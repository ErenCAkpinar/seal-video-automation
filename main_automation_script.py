#!/usr/bin/env python3
"""
SEAL Video Automation System - Ana Çalıştırma Scripti
Bu script tüm otomasyon sürecini koordine eder.
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Core modülleri import et
from core.trend_analyzer import TrendAnalyzer
from core.generate_script import ScriptGenerator
from core.voiceover import VoiceoverGenerator
from core.create_video import VideoCreator
from core.upload import VideoUploader
from core.affiliate_manager import AffiliateManager
from core.feedback_collector import FeedbackCollector

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SEALVideoAutomation:
    """Ana otomasyon sınıfı"""
    
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
        self.script_generator = ScriptGenerator()
        self.voiceover_generator = VoiceoverGenerator()
        self.video_creator = VideoCreator()
        self.uploader = VideoUploader()
        self.affiliate_manager = AffiliateManager()
        self.feedback_collector = FeedbackCollector()
        
        # Output klasörlerini oluştur
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "videos").mkdir(exist_ok=True)
        (self.output_dir / "audio").mkdir(exist_ok=True)
        (self.output_dir / "scripts").mkdir(exist_ok=True)
    
    async def generate_trending_content(self, count: int = 1):
        """Trend analizi yaparak içerik üret"""
        logger.info(f"Trend analizi başlatılıyor - {count} video için")
        
        # Trending konuları al
        trending_topics = await self.trend_analyzer.get_trending_topics(count)
        
        results = []
        for topic in trending_topics:
            try:
                result = await self.create_video_content(
                    topic=topic['title'],
                    category=topic.get('category', 'general'),
                    trend_data=topic
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Video oluşturma hatası ({topic['title']}): {e}")
                continue
        
        return results
    
    async def create_video_content(self, topic: str, category: str = "general", 
                                  languages: list = None, include_affiliates: bool = True,
                                  trend_data: dict = None):
        """Tek bir video içeriği oluştur"""
        
        if languages is None:
            languages = ["en"]  # Varsayılan İngilizce
        
        logger.info(f"Video içeriği oluşturuluyor: {topic}")
        
        results = {}
        
        for lang in languages:
            try:
                # 1. Script oluştur
                logger.info(f"Script oluşturuluyor ({lang}): {topic}")
                script_data = await self.script_generator.generate_script(
                    topic=topic,
                    language=lang,
                    category=category,
                    trend_data=trend_data
                )
                
                # 2. Affiliate linkler ekle
                if include_affiliates:
                    script_data = self.affiliate_manager.add_affiliate_content(
                        script_data, category
                    )
                
                # 3. Seslendirme oluştur
                logger.info(f"Seslendirme oluşturuluyor ({lang})")
                audio_path = await self.voiceover_generator.create_voiceover(
                    text=script_data['content'],
                    language=lang,
                    voice_style=script_data.get('voice_style', 'professional')
                )
                
                # 4. Video oluştur
                logger.info(f"Video oluşturuluyor ({lang})")
                video_path = await self.video_creator.create_video(
                    script_data=script_data,
                    audio_path=audio_path,
                    language=lang,
                    category=category
                )
                
                # 5. Video yükle
                logger.info(f"Video yükleniyor ({lang})")
                upload_results = await self.uploader.upload_video(
                    video_path=video_path,
                    script_data=script_data,
                    language=lang
                )
                
                results[lang] = {
                    'script': script_data,
                    'audio_path': audio_path,
                    'video_path': video_path,
                    'upload_results': upload_results,
                    'created_at': datetime.now().isoformat()
                }
                
                logger.info(f"Video başarıyla oluşturuldu ve yüklendi ({lang}): {topic}")
                
            except Exception as e:
                logger.error(f"Hata ({lang}): {topic} - {e}")
                results[lang] = {'error': str(e)}
        
        return results
    
    async def run_automation_cycle(self):
        """Tam otomasyon döngüsü çalıştır"""
        logger.info("Otomasyon döngüsü başlatılıyor")
        
        try:
            # Günlük video sayısını belirle
            daily_video_count = int(os.getenv('DAILY_VIDEO_COUNT', 3))
            
            # Trending içerik üret
            results = await self.generate_trending_content(daily_video_count)
            
            # Sonuçları logla
            logger.info(f"Otomasyon döngüsü tamamlandı: {len(results)} video işlendi")
            
            # Feedback toplamayı başlat (asenkron)
            asyncio.create_task(self.collect_feedback_for_videos(results))
            
            return results
            
        except Exception as e:
            logger.error(f"Otomasyon döngüsü hatası: {e}")
            raise
    
    async def collect_feedback_for_videos(self, results: list):
        """Videolar için feedback topla (SEAL learning için)"""
        logger.info("Feedback toplama başlatılıyor")
        
        # 2 saat bekle, sonra metrics topla
        await asyncio.sleep(7200)  # 2 saat
        
        for result in results:
            try:
                for lang, data in result.items():
                    if 'upload_results' in data:
                        await self.feedback_collector.collect_video_metrics(
                            data['upload_results'], 
                            data['script']
                        )
            except Exception as e:
                logger.error(f"Feedback toplama hatası: {e}")

async def main():
    """Ana fonksiyon"""
    parser = argparse.ArgumentParser(description="SEAL Video Automation System")
    
    parser.add_argument('--topic', type=str, help='Belirli bir konu için video üret')
    parser.add_argument('--languages', type=str, default='en', 
                       help='Diller (virgülle ayrılmış): en,de,ko,zh')
    parser.add_argument('--count', type=int, default=1, 
                       help='Üretilecek video sayısı (trend tabanlı)')
    parser.add_argument('--include-affiliates', action='store_true', 
                       help='Affiliate linkleri dahil et')
    parser.add_argument('--test-mode', action='store_true', 
                       help='Test modu (upload yapmaz)')
    parser.add_argument('--auto-mode', action='store_true', 
                       help='Tam otomatik mod (günlük döngü)')
    
    args = parser.parse_args()
    
    # Sistem başlatma
    automation = SEALVideoAutomation()
    
    # Test modu ayarla
    if args.test_mode:
        os.environ['TEST_MODE'] = 'true'
        logger.info("TEST MODU - Videolar yüklenmeyecek")
    
    try:
        if args.auto_mode:
            # Otomatik mod - sürekli çalışır
            logger.info("Otomatik mod başlatıldı - CTRL+C ile durdurun")
            while True:
                await automation.run_automation_cycle()
                # 24 saat bekle
                await asyncio.sleep(86400)
                
        elif args.topic:
            # Manuel konu
            languages = args.languages.split(',')
            result = await automation.create_video_content(
                topic=args.topic,
                languages=languages,
                include_affiliates=args.include_affiliates
            )
            print(f"Video oluşturuldu: {result}")
            
        else:
            # Trend tabanlı
            results = await automation.generate_trending_content(args.count)
            print(f"{len(results)} trend tabanlı video oluşturuldu")
            
    except KeyboardInterrupt:
        logger.info("Kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"Kritik hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Event loop oluştur ve çalıştır
    if sys.platform == 'win32':
        # Windows için
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())