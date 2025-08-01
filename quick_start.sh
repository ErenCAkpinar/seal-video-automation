#!/bin/bash

# ========================================
# SEAL Video Automation - Quick Start Script
# ========================================

set -e

# Renkler
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Banner
print_banner() {
    echo -e "${PURPLE}"
    echo "  ╔═══════════════════════════════════════════════════════════════╗"
    echo "  ║                                                               ║"
    echo "  ║         🚀 SEAL VIDEO AUTOMATION SYSTEM 🚀                   ║"
    echo "  ║                                                               ║"
    echo "  ║    Self-Evolving AI Layer for Automated Video Generation     ║"
    echo "  ║                                                               ║"
    echo "  ╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${GREEN}[STEP] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

check_system() {
    print_step "Sistem kontrolleri yapılıyor..."
    
    # OS Detection
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_info "Linux sistemi algılandı"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_info "macOS sistemi algılandı"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        print_info "Windows sistemi algılandı"
    else
        print_error "Desteklenmeyen işletim sistemi: $OSTYPE"
        exit 1
    fi
    
    # Python kontrolü
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python $PYTHON_VERSION bulundu"
        
        # Python version check (minimum 3.9)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
            print_info "✓ Python versiyonu uygun"
        else
            print_error "Python 3.9+ gerekli. Mevcut: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python3 bulunamadı. Lütfen Python 3.9+ kurun."
        exit 1
    fi
    
    # Git kontrolü
    if ! command -v git &> /dev/null; then
        print_error "Git bulunamadı. Lütfen Git'i kurun."
        exit 1
    fi
    
    print_info "✓ Sistem kontrolleri başarılı"
}

install_dependencies() {
    print_step "Sistem bağımlılıkları kuruluyor..."
    
    case $OS in
        "linux")
            # Ubuntu/Debian
            if command -v apt-get &> /dev/null; then
                print_info "APT paket yöneticisi kullanılıyor..."
                sudo apt-get update
                sudo apt-get install -y ffmpeg python3-pip python3-venv curl wget
                
            # CentOS/RHEL/Fedora
            elif command -v yum &> /dev/null; then
                print_info "YUM paket yöneticisi kullanılıyor..."
                sudo yum install -y ffmpeg python3-pip curl wget
                
            # Arch Linux
            elif command -v pacman &> /dev/null; then
                print_info "Pacman paket yöneticisi kullanılıyor..."
                sudo pacman -S --noconfirm ffmpeg python-pip curl wget
            fi
            ;;
            
        "macos")
            # Homebrew kontrolü
            if ! command -v brew &> /dev/null; then
                print_info "Homebrew kuruluyor..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            print_info "Homebrew ile bağımlılıklar kuruluyor..."
            brew install ffmpeg python@3.11
            ;;
            
        "windows")
            print_warning "Windows için manual kurulum gerekli:"
            print_info "1. FFmpeg'i indirin: https://ffmpeg.org/download.html"
            print_info "2. PATH'e ekleyin"
            print_info "3. Python 3.9+ kurulu olduğundan emin olun"
            read -p "Kurulum tamamlandı mı? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
    
    print_info "✓ Sistem bağımlılıkları kuruldu"
}

setup_python_environment() {
    print_step "Python sanal ortamı oluşturuluyor..."
    
    # Sanal ortam oluştur
    python3 -m venv venv
    
    # Sanal ortamı aktifleştir
    source venv/bin/activate
    
    # Pip upgrade
    pip install --upgrade pip
    
    print_info "✓ Python sanal ortamı hazır"
}

install_python_packages() {
    print_step "Python paketleri kuruluyor..."
    
    # Sanal ortamın aktif olduğundan emin ol
    source venv/bin/activate
    
    # Requirements'ı kur
    print_info "Temel paketler kuruluyor..."
    pip install -r requirements.txt
    
    # Spacy model indir
    print_info "Spacy language model indiriliyor..."
    python -m spacy download en_core_web_sm || print_warning "Spacy model indirilemedi, daha sonra deneyin"
    
    print_info "✓ Python paketleri kuruldu"
}

setup_ollama() {
    print_step "Ollama kurulumu kontrol ediliyor..."
    
    if ! command -v ollama &> /dev/null; then
        print_info "Ollama kuruluyor..."
        
        case $OS in
            "linux"|"macos")
                curl -fsSL https://ollama.ai/install.sh | sh
                ;;
            "windows")
                print_warning "Windows için Ollama'yı manuel indirin: https://ollama.ai"
                read -p "Ollama kuruldu mu? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    print_error "Ollama kurulumu gerekli"
                    exit 1
                fi
                ;;
        esac
    else
        print_info "✓ Ollama zaten kurulu"
    fi
    
    # Ollama servisini başlat
    print_info "Ollama servisi başlatılıyor..."
    ollama serve > /dev/null 2>&1 &
    
    # Biraz bekle
    sleep 3
    
    # Mistral modelini indir
    print_info "Mistral modeli indiriliyor (bu biraz zaman alabilir)..."
    ollama pull mistral
    
    print_info "✓ Ollama kurulumu tamamlandı"
}

setup_configuration() {
    print_step "Konfigürasyon dosyaları hazırlanıyor..."
    
    # .env dosyası oluştur
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_info ".env dosyası oluşturuldu"
    else
        print_info ".env dosyası zaten mevcut"
    fi