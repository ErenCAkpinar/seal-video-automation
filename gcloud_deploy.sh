#!/bin/bash

# ========================================
# SEAL Video Automation - Google Cloud Deploy Script
# ========================================

set -e  # Exit on any error

# Renkli output için
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Konfigürasyon
PROJECT_ID=${1:-"seal-video-automation"}
REGION=${2:-"us-central1"}
ZONE=${3:-"us-central1-a"}
MACHINE_TYPE=${4:-"n1-standard-4"}
DISK_SIZE=${5:-"50GB"}

echo -e "${BLUE}=== SEAL Video Automation - Google Cloud Deploy ===${NC}"
echo -e "${YELLOW}Project ID: $PROJECT_ID${NC}"
echo -e "${YELLOW}Region: $REGION${NC}"
echo -e "${YELLOW}Zone: $ZONE${NC}"
echo -e "${YELLOW}Machine Type: $MACHINE_TYPE${NC}"

# Fonksiyonlar
print_step() {
    echo -e "\n${GREEN}[STEP] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

check_prerequisites() {
    print_step "Ön koşullar kontrol ediliyor..."
    
    # gcloud CLI kontrolü
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI kurulu değil. Lütfen kurulum yapın:"
        echo "curl https://sdk.cloud.google.com | bash"
        exit 1
    fi
    
    # Docker kontrolü
    if ! command -v docker &> /dev/null; then
        print_error "Docker kurulu değil. Lütfen kurulum yapın."
        exit 1
    fi
    
    # .env dosyası kontrolü
    if [ ! -f ".env" ]; then
        print_warning ".env dosyası bulunamadı. .env.example'dan oluşturuluyor..."
        cp .env.example .env
        echo -e "${YELLOW}Lütfen .env dosyasını API anahtarlarınızla güncelleyin!${NC}"
        read -p "Devam etmek için Enter'a basın..."
    fi
    
    echo -e "${GREEN}✓ Ön koşullar tamam${NC}"
}

setup_gcloud_project() {
    print_step "Google Cloud projesi hazırlanıyor..."
    
    # Mevcut projeyi kontrol et
    if ! gcloud projects describe $PROJECT_ID &>/dev/null; then
        echo -e "${YELLOW}Proje bulunamadı. Yeni proje oluşturuluyor...${NC}"
        gcloud projects create $PROJECT_ID --name="SEAL Video Automation"
    fi
    
    # Projeyi aktif et
    gcloud config set project $PROJECT_ID
    
    # Gerekli API'leri etkinleştir
    print_step "Gerekli API'ler etkinleştiriliyor..."
    gcloud services enable compute.googleapis.com
    gcloud services enable cloudfunctions.googleapis.com
    gcloud services enable storage.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com
    gcloud services enable scheduler.googleapis.com
    
    echo -e "${GREEN}✓ Google Cloud projesi hazır${NC}"
}

create_storage_bucket() {
    print_step "Storage bucket oluşturuluyor..."
    
    BUCKET_NAME="${PROJECT_ID}-storage"
    
    if ! gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
        gsutil mb -l $REGION gs://$BUCKET_NAME
        
        # Bucket politikaları
        gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME/public/
        
        echo -e "${GREEN}✓ Storage bucket oluşturuldu: gs://$BUCKET_NAME${NC}"
    else
        echo -e "${GREEN}✓ Storage bucket zaten mevcut${NC}"
    fi
    
    # .env dosyasına bucket adını ekle
    if ! grep -q "GCS_BUCKET_NAME" .env; then
        echo "GCS_BUCKET_NAME=$BUCKET_NAME" >> .env
    fi
}

store_secrets() {
    print_step "API anahtarları Secret Manager'a kaydediliyor..."
    
    # .env dosyasından secret'ları oku ve kaydet
    while IFS= read -r line; do
        if [[ $line =~ ^[A-Z_]+=.+ ]]; then
            key=$(echo $line | cut -d'=' -f1)
            value=$(echo $line | cut -d'=' -f2-)
            
            # Boş değerleri atla
            if [ "$value" != "your_" ] && [ ! -z "$value" ]; then
                echo "Creating secret: $key"
                echo -n "$value" | gcloud secrets create $key --data-file=- --replication-policy="automatic" || true
            fi
        fi
    done < .env
    
    echo -e "${GREEN}✓ Secrets kaydedildi${NC}"
}

create_vm_instance() {
    print_step "Compute Engine VM oluşturuluyor..."
    
    VM_NAME="seal-automation-vm"
    
    # VM zaten var mı kontrol et
    if gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
        print_warning "VM zaten mevcut. Yeniden oluşturmak istiyor musunuz? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
        else
            echo -e "${GREEN}✓ Mevcut VM kullanılıyor${NC}"
            return
        fi
    fi
    
    # Startup script oluştur
    cat > startup-script.sh << 'EOF'
#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose git python3-pip nginx

# Docker'ı başlat
systemctl start docker
systemctl enable docker

# Kullanıcıyı docker grubuna ekle
usermod -aG docker $USER

# SEAL automation'u klonla
cd /opt
git clone https://github.com/your-username/seal-video-automation.git
cd seal-video-automation

# Secrets'ları VM'e indir (bu kısım otomatik çalışmayacak, manuel yapılmalı)
# gcloud secrets versions access latest --secret="ELEVENLABS_API_KEY" > /tmp/secrets

# Docker compose ile başlat
docker-compose up -d

# Nginx proxy konfigürasyonu
cat > /etc/nginx/sites-available/seal-automation << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /gradio/ {
        proxy_pass http://localhost:7860/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
NGINX_EOF

ln -s /etc/nginx/sites-available/seal-automation /etc/nginx/sites-enabled/
systemctl restart nginx
EOF
    
    # VM oluştur
    gcloud compute instances create $VM_NAME \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --boot-disk-size=$DISK_SIZE \
        --boot-disk-type=pd-standard \
        --image-family=ubuntu-2004-lts \
        --image-project=ubuntu-os-cloud \
        --metadata-from-file startup-script=startup-script.sh \
        --tags=http-server,https-server \
        --scopes=cloud-platform
    
    # Firewall kuralları
    gcloud compute firewall-rules create allow-seal-automation \
        --allow tcp:80,tcp:443,tcp:8000,tcp:7860 \
        --source-ranges 0.0.0.0/0 \
        --target-tags http-server,https-server || true
    
    # External IP al
    EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
    
    echo -e "${GREEN}✓ VM oluşturuldu${NC}"
    echo -e "${BLUE}VM Adı: $VM_NAME${NC}"
    echo -e "${BLUE}External IP: $EXTERNAL_IP${NC}"
    echo -e "${BLUE}Web Interface: http://$EXTERNAL_IP${NC}"
    echo -e "${BLUE}Gradio Dashboard: http://$EXTERNAL_IP/gradio${NC}"
    
    # Cleanup
    rm startup-script.sh
}

deploy_cloud_functions() {
    print_step "Cloud Functions deploy ediliyor..."
    
    # Trend analyzer function
    mkdir -p cloud-functions/trend-analyzer
    
    cat > cloud-functions/trend-analyzer/main.py << 'PYTHON_EOF'
import functions_framework
import requests
import json
import os

@functions_framework.http
def main(request):
    """Trend analizi ve otomatik video üretimi tetikleyicisi"""
    
    # VM'deki ana uygulamaya istek gönder
    vm_ip = os.environ.get('VM_INTERNAL_IP', 'localhost')
    
    try:
        response = requests.post(
            f'http://{vm_ip}:8000/api/generate-trending-videos',
            json={'count': 3},
            timeout=30
        )
        
        if response.status_code == 200:
            return {'status': 'success', 'message': 'Trend analysis triggered'}
        else:
            return {'status': 'error', 'message': f'API error: {response.status_code}'}
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
PYTHON_EOF

    cat > cloud-functions/trend-analyzer/requirements.txt << 'REQ_EOF'
functions-framework==3.*
requests==2.31.0
REQ_EOF

    # Function deploy
    gcloud functions deploy trend-analyzer \
        --gen2 \
        --runtime=python311 \
        --region=$REGION \
        --source=cloud-functions/trend-analyzer \
        --entry-point=main \
        --trigger-http \
        --allow-unauthenticated \
        --set-env-vars VM_INTERNAL_IP=$EXTERNAL_IP
    
    echo -e "${GREEN}✓ Cloud Functions deploy edildi${NC}"
}

setup_scheduler() {
    print_step "Cloud Scheduler kurulumu..."
    
    # Günlük video üretimi için scheduler
    gcloud scheduler jobs create http daily-video-generation \
        --schedule="0 8 * * *" \
        --uri="https://$REGION-$PROJECT_ID.cloudfunctions.net/trend-analyzer" \
        --http-method=POST \
        --location=$REGION || true
    
    # Haftalık fine-tune için scheduler
    gcloud scheduler jobs create http weekly-fine-tune \
        --schedule="0 2 * * 0" \
        --uri="http://$EXTERNAL_IP:8000/api/fine-tune" \
        --http-method=POST \
        --location=$REGION || true
    
    echo -e "${GREEN}✓ Scheduler kuruldu${NC}"
}

setup_monitoring() {
    print_step "Monitoring kurulumu..."
    
    # Alerting policy oluştur
    cat > alerting-policy.json << 'JSON_EOF'
{
  "displayName": "SEAL Automation VM Down",
  "conditions": [
    {
      "displayName": "VM Instance Down",
      "conditionThreshold": {
        "filter": "resource.type=\"gce_instance\" resource.label.instance_id=\"${VM_NAME}\"",
        "comparison": "COMPARISON_EQUAL",
        "thresholdValue": 0,
        "duration": "300s",
        "aggregations": [
          {
            "alignmentPeriod": "60s",
            "perSeriesAligner": "ALIGN_MEAN"
          }
        ]
      }
    }
  ],
  "enabled": true
}
JSON_EOF

    gcloud alpha monitoring policies create --policy-from-file=alerting-policy.json || true
    
    rm alerting-policy.json
    
    echo -e "${GREEN}✓ Monitoring kuruldu${NC}"
}

final_setup() {
    print_step "Final kurulum adımları..."
    
    echo -e "\n${BLUE}=== KURULUM TAMAMLANDI ===${NC}"
    echo -e "${GREEN}✓ Google Cloud projesi oluşturuldu${NC}"
    echo -e "${GREEN}✓ VM instance çalışıyor${NC}"
    echo -e "${GREEN}✓ Storage bucket hazır${NC}"
    echo -e "${GREEN}✓ Secrets kaydedildi${NC}"
    echo -e "${GREEN}✓ Cloud Functions deploy edildi${NC}"
    echo -e "${GREEN}✓ Scheduler ayarlandı${NC}"
    
    echo -e "\n${YELLOW}ÖNEMLİ NOTLAR:${NC}"
    echo -e "1. VM'e SSH ile bağlanın ve .env dosyasını düzenleyin:"
    echo -e "   ${BLUE}gcloud compute ssh $VM_NAME --zone=$ZONE${NC}"
    echo -e "2. Web arayüzü: ${BLUE}http://$EXTERNAL_IP${NC}"
    echo -e "3. Gradio dashboard: ${BLUE}http://$EXTERNAL_IP/gradio${NC}"
    echo -e "4. Logs: ${BLUE}gcloud compute instances get-serial-port-output $VM_NAME --zone=$ZONE${NC}"
    
    echo -e "\n${YELLOW}MANUEL ADIMLAR:${NC}"
    echo -e "1. VM'de API anahtarlarını ayarlayın"
    echo -e "2. Ollama modelini indirin: ${BLUE}docker exec seal-ollama ollama pull mistral${NC}"
    echo -e "3. Test video oluşturun: ${BLUE}curl http://$EXTERNAL_IP:8000/api/test${NC}"
    
    # SSH connection helper script
    cat > connect-vm.sh << 'SSH_EOF'
#!/bin/bash
echo "VM'e bağlanılıyor..."
gcloud compute ssh seal-automation-vm --zone=us-central1-a --project=$PROJECT_ID

# VM içinde çalıştırılacak komutlar:
echo "=== VM içinde çalıştırın ==="
echo "cd /opt/seal-video-automation"
echo "sudo docker-compose logs -f"
echo "sudo docker exec -it seal-ollama ollama pull mistral"
SSH_EOF

    chmod +x connect-vm.sh
    
    echo -e "\n${GREEN}VM'e bağlanmak için: ${BLUE}./connect-vm.sh${NC}"
}

# Ana fonksiyon
main() {
    echo -e "${BLUE}SEAL Video Automation Google Cloud Deploy başlatılıyor...${NC}"
    
    check_prerequisites
    setup_gcloud_project
    create_storage_bucket
    store_secrets
    create_vm_instance
    deploy_cloud_functions
    setup_scheduler
    setup_monitoring
    final_setup
    
    echo -e "\n${GREEN}🎉 Deploy tamamlandı!${NC}"
}

# Script çalıştırma
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi