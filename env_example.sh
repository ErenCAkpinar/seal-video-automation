# ========================================
# SEAL Video Automation - Environment Variables
# ========================================

# Temel AI Model Ayarları
# ========================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TEMPERATURE=0.7
OLLAMA_MAX_TOKENS=2000

# Text-to-Speech (ElevenLabs)
# ========================================
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID_EN=21m00Tcm4TlvDq8ikWAM  # Rachel (English)
ELEVENLABS_VOICE_ID_DE=pNInz6obpgDQGcFmaJgB  # Adam (German)
ELEVENLABS_VOICE_ID_KO=Xb7hH8MSUJpSbSDYk0k2  # Alice (Korean)
ELEVENLABS_VOICE_ID_ZH=pMsXgVXv3BLzUgSXRplE  # Serena (Chinese)

# YouTube API
# ========================================
YOUTUBE_API_KEY=your_youtube_api_key_here
YOUTUBE_CHANNEL_ID=your_youtube_channel_id
YOUTUBE_CLIENT_SECRETS_FILE=client_secrets.json
YOUTUBE_UPLOAD_SCOPE=https://www.googleapis.com/auth/youtube.upload

# TikTok API (3rd party)
# ========================================
TIKTOK_API_KEY=your_tiktok_api_key
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token

# Trend Analysis APIs
# ========================================
GOOGLE_TRENDS_API_KEY=your_google_trends_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=TrendBot/1.0

# Affiliate Marketing
# ========================================
AMAZON_AFFILIATE_TAG=your_amazon_associate_tag
CLICKBANK_AFFILIATE_ID=your_clickbank_id
COMMISSION_JUNCTION_API_KEY=your_cj_api_key

# Database and Storage
# ========================================
CHROMA_PERSIST_DIRECTORY=./data/vector_db
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./data/seal_automation.db

# Cloud Storage (Optional)
# ========================================
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=your_s3_bucket_name
AWS_REGION=us-east-1

# Google Cloud Storage (Optional)
# ========================================
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCS_BUCKET_NAME=your_gcs_bucket

# Content Generation Settings
# ========================================
DAILY_VIDEO_COUNT=3
MAX_VIDEO_DURATION=60
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,de,ko,zh
VIDEO_QUALITY=high
INCLUDE_WATERMARK=true

# Automation Schedule
# ========================================
AUTO_GENERATION_ENABLED=true
GENERATION_SCHEDULE=0 8 * * *  # Daily at 8 AM
FEEDBACK_COLLECTION_DELAY=7200  # 2 hours in seconds
FINE_TUNE_SCHEDULE=0 2 1 * *   # Monthly at 2 AM on 1st

# Notification Settings
# ========================================
SLACK_WEBHOOK_URL=your_slack_webhook_url
DISCORD_WEBHOOK_URL=your_discord_webhook_url
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_email_app_password
NOTIFICATION_EMAIL=admin@yoursite.com

# API Rate Limiting
# ========================================
ELEVENLABS_RATE_LIMIT=100  # requests per minute
YOUTUBE_RATE_LIMIT=10000   # requests per day
REDDIT_RATE_LIMIT=60       # requests per minute

# Fine-tuning Settings
# ========================================
FINE_TUNE_ENABLED=true
FINE_TUNE_MIN_FEEDBACK=50
FINE_TUNE_LEARNING_RATE=0.0001
LORA_RANK=16
LORA_ALPHA=32

# Monitoring and Logging
# ========================================
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn_here
PROMETHEUS_PORT=8001
GRAFANA_ADMIN_PASSWORD=admin123

# Development Settings
# ========================================
DEBUG=false
TEST_MODE=false
MOCK_APIS=false
DEVELOPMENT_MODE=false

# Content Filtering
# ========================================
CONTENT_FILTER_ENABLED=true
PROFANITY_FILTER=true
SPAM_DETECTION=true
MINIMUM_QUALITY_SCORE=0.7

# Social Media Automation
# ========================================
AUTO_UPLOAD_YOUTUBE=true
AUTO_UPLOAD_TIKTOK=true
AUTO_UPLOAD_INSTAGRAM=false
AUTO_SCHEDULE_POSTS=true

# Backup and Recovery
# ========================================
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 3 * * *  # Daily at 3 AM
BACKUP_RETENTION_DAYS=30
BACKUP_LOCATION=./backups

# Performance Settings
# ========================================
MAX_CONCURRENT_VIDEOS=2
PARALLEL_UPLOADS=3
GPU_ENABLED=false
CPU_THREADS=4

# Web Interface
# ========================================
WEB_HOST=0.0.0.0
WEB_PORT=8000
GRADIO_PORT=7860
STREAMLIT_PORT=8501

# Security
# ========================================
SECRET_KEY=your_secret_key_here_change_this
API_TOKEN_EXPIRY=3600  # 1 hour
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Analytics and Metrics
# ========================================
GOOGLE_ANALYTICS_ID=your_ga_id
TRACK_USER_BEHAVIOR=true
COLLECT_PERFORMANCE_METRICS=true

# Experimental Features
# ========================================
ENABLE_VOICE_CLONING=false
ENABLE_VIDEO_EFFECTS=false
ENABLE_AI_THUMBNAILS=true
ENABLE_TREND_PREDICTION=true

# Custom Model Paths (Optional)
# ========================================
CUSTOM_OLLAMA_MODEL_PATH=./models/custom_mistral
FINE_TUNED_MODEL_PATH=./models/fine_tuned
EMBEDDING_MODEL_PATH=./models/embeddings

# Webhook URLs for External Integration
# ========================================
ZAPIER_WEBHOOK_URL=your_zapier_webhook_url
MAKE_WEBHOOK_URL=your_make_webhook_url
IFTTT_WEBHOOK_KEY=your_ifttt_key

# Proxy Settings (if needed)
# ========================================
HTTP_PROXY=
HTTPS_PROXY=
NO_PROXY=localhost,127.0.0.1

# ========================================
# Notes:
# 1. Bu dosyayı .env olarak kopyalayın
# 2. Tüm placeholder değerleri gerçek API anahtarlarınızla değiştirin
# 3. .env dosyasını asla git'e commit etmeyin
# 4. Üretim ortamında güçlü şifreler kullanın
# ========================================