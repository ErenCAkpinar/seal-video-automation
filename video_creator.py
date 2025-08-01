#!/usr/bin/env python3
"""
Video Creator - FFmpeg ile otomatik video oluşturma, altyazı ekleme ve şablon sistemi
"""

import os
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
import random
import requests
from PIL import Image, ImageDraw, ImageFont
import textwrap

logger = logging.getLogger(__name__)

class VideoCreator:
    """Otomatik video oluşturma sınıfı"""
    
    def __init__(self):
        self.output_dir = Path("output/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.templates_dir = Path("templates")
        self.backgrounds_dir = self.templates_dir / "video_backgrounds"
        self.fonts_dir = self.templates_dir / "fonts"
        
        # Klasörleri oluştur
        self.backgrounds_dir.mkdir(parents=True, exist_ok=True)
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        
        # Video ayarları
        self.video_settings = {
            'width': 1080,
            'height': 1920,  # 9:16 aspect ratio (Shorts/Reels)
            'fps': 30,
            'duration': 60,  # max 60 saniye
            'bitrate': '2M',
            'audio_bitrate': '128k'
        }
        
        # Kategori-spesifik stil ayarları
        self.category_styles = {
            'finance': {
                'colors': ['#1a5f3f', '#2d8a5f', '#0a4d3a'],
                'font_color': '#ffffff',
                'background_type': 'gradient',
                'animation_style': 'slide'
            },
            'tech': {
                'colors': ['#1e3a8a', '#3b82f6', '#1e40af'],
                'font_color': '#ffffff',
                'background_type': 'particles',
                'animation_style': 'fade'
            },
            'education': {
                'colors': ['#7c2d12', '#ea580c', '#9a3412'],
                'font_color': '#ffffff',
                'background_type': 'minimal',
                'animation_style': 'zoom'
            },
            'lifestyle': {
                'colors': ['#581c87', '#a855f7', '#7c3aed'],
                'font_color': '#ffffff',
                'background_type': 'geometric',
                'animation_style': 'slide'
            },
            'general': {
                'colors': ['#374151', '#6b7280', '#4b5563'],
                'font_color': '#ffffff',
                'background_type': 'gradient',
                'animation_style': 'fade'
            }
        }
        
        # Altyazı ayarları
        self.subtitle_settings = {
            'en': {'font_size': 48, 'line_height': 1.2, 'max_chars_per_line': 25},
            'de': {'font_size': 44, 'line_height': 1.3, 'max_chars_per_line': 22},
            'ko': {'font_size': 52, 'line_height': 1.1, 'max_chars_per_line': 20},
            'zh': {'font_size': 50, 'line_height': 1.1, 'max_chars_per_line': 18}
        }
        
        # İlk çalıştırmada gerekli dosyaları indir
        asyncio.create_task(self._initialize_assets())
    
    async def _initialize_assets(self):
        """Gerekli asset'leri indir ve hazırla"""
        try:
            # Font dosyalarını indir
            await self._download_fonts()
            
            # Örnek arka plan görsellerini indir
            await self._download_stock_backgrounds()
            
            logger.info("Video assets hazırlandı")
            
        except Exception as e:
            logger.error(f"Asset hazırlama hatası: {e}")
    
    async def _download_fonts(self):
        """Font dosyalarını indir"""
        fonts = {
            'Roboto-Bold.ttf': 'https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf',
            'OpenSans-Bold.ttf': 'https://github.com/google/fonts/raw/main/apache/opensans/OpenSans-Bold.ttf',
            'Montserrat-Bold.ttf': 'https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf'
        }
        
        for font_name, font_url in fonts.items():
            font_path = self.fonts_dir / font_name
            
            if not font_path.exists():
                try:
                    response = requests.get(font_url, timeout=30)
                    if response.status_code == 200:
                        with open(font_path, 'wb') as f:
                            f.write(response.content)
                        logger.info(f"Font indirildi: {font_name}")
                except Exception as e:
                    logger.warning(f"Font indirme hatası ({font_name}): {e}")
    
    async def _download_stock_backgrounds(self):
        """Stok arka plan görsellerini indir"""
        # Basit gradient ve solid color arka planları oluştur
        backgrounds = [
            {'name': 'gradient_blue', 'colors': ['#1e3a8a', '#3b82f6']},
            {'name': 'gradient_green', 'colors': ['#1a5f3f', '#2d8a5f']},
            {'name': 'gradient_purple', 'colors': ['#581c87', '#a855f7']},
            {'name': 'gradient_orange', 'colors': ['#7c2d12', '#ea580c']},
            {'name': 'solid_dark', 'colors': ['#1f2937']},
        ]
        
        for bg in backgrounds:
            bg_path = self.backgrounds_dir / f"{bg['name']}.png"
            
            if not bg_path.exists():
                try:
                    await self._create_gradient_background(
                        bg['colors'], 
                        str(bg_path),
                        self.video_settings['width'],
                        self.video_settings['height']
                    )
                    logger.info(f"Arka plan oluşturuldu: {bg['name']}")
                except Exception as e:
                    logger.warning(f"Arka plan oluşturma hatası ({bg['name']}): {e}")
    
    async def _create_gradient_background(self, colors: List[str], output_path: str, width: int, height: int):
        """Gradient arka plan oluştur"""
        try:
            from PIL import Image, ImageDraw
            
            # Görüntü oluştur
            img = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(img)
            
            if len(colors) == 1:
                # Solid color
                draw.rectangle([0, 0, width, height], fill=colors[0])
            else:
                # Gradient effect (basit implementasyon)
                for y in range(height):
                    # Gradient hesaplama
                    ratio = y / height
                    
                    # İki renk arası interpolasyon
                    r1, g1, b1 = self._hex_to_rgb(colors[0])
                    r2, g2, b2 = self._hex_to_rgb(colors[1])
                    
                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)
                    
                    draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # Kaydet
            img.save(output_path)
            
        except Exception as e:
            logger.error(f"Gradient oluşturma hatası: {e}")
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Hex rengi RGB'ye çevir"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    async def create_video(self, script_data: Dict[str, Any], audio_path: str, 
                          language: str = 'en', category: str = 'general') -> str:
        """Ana video oluşturma fonksiyonu"""
        
        logger.info(f"Video oluşturuluyor ({language}): {script_data.get('title', 'Untitled')}")
        
        try:
            # Stil ayarlarını al
            style = self.category_styles.get(category, self.category_styles['general'])
            
            # Arka plan seç
            background_path = await self._select_background(category, style)
            
            # Altyazı dosyası oluştur
            subtitle_path = await self._create_subtitle_file(
                script_data['content'], 
                language,
                script_data.get('estimated_duration', 60)
            )
            
            # Video oluştur
            video_path = await self._create_video_with_ffmpeg(
                background_path=background_path,
                audio_path=audio_path,
                subtitle_path=subtitle_path,
                script_data=script_data,
                language=language,
                style=style
            )
            
            logger.info(f"Video oluşturuldu: {video_path}")
            return video_path
            
        except Exception as e:
            logger.error(f"Video oluşturma hatası: {e}")
            raise
    
    async def _select_background(self, category: str, style: Dict) -> str:
        """Kategoriye uygun arka plan seç"""
        try:
            # Kategori renk temasına uygun arka plan
            if category == 'finance':
                bg_name = 'gradient_green.png'
            elif category == 'tech':
                bg_name = 'gradient_blue.png'
            elif category == 'education':
                bg_name = 'gradient_orange.png'
            elif category == 'lifestyle':
                bg_name = 'gradient_purple.png'
            else:
                bg_name = 'solid_dark.png'
            
            bg_path = self.backgrounds_dir / bg_name
            
            if bg_path.exists():
                return str(bg_path)
            else:
                # Fallback: solid dark background oluştur
                fallback_path = self.backgrounds_dir / 'fallback_dark.png'
                await self._create_gradient_background(
                    ['#1f2937'], 
                    str(fallback_path),
                    self.video_settings['width'],
                    self.video_settings['height']
                )
                return str(fallback_path)
                
        except Exception as e:
            logger.error(f"Arka plan seçim hatası: {e}")
            return ""
    
    async def _create_subtitle_file(self, content: str, language: str, duration: int) -> str:
        """SRT altyazı dosyası oluştur"""
        try:
            subtitle_settings = self.subtitle_settings.get(language, self.subtitle_settings['en'])
            
            # Metni satırlara böl
            lines = self._split_text_for_subtitles(content, subtitle_settings['max_chars_per_line'])
            
            # Timing hesapla
            time_per_line = duration / len(lines) if lines else 1
            
            # SRT formatında dosya oluştur
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            subtitle_filename = f"subtitles_{language}_{timestamp}.srt"
            subtitle_path = self.output_dir / subtitle_filename
            
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                for i, line in enumerate(lines):
                    start_time = i * time_per_line
                    end_time = (i + 1) * time_per_line
                    
                    start_srt = self._seconds_to_srt_time(start_time)
                    end_srt = self._seconds_to_srt_time(end_time)
                    
                    f.write(f"{i + 1}\n")
                    f.write(f"{start_srt} --> {end_srt}\n")
                    f.write(f"{line}\n\n")
            
            logger.info(f"Altyazı dosyası oluşturuldu: {subtitle_filename}")
            return str(subtitle_path)
            
        except Exception as e:
            logger.error(f"Altyazı oluşturma hatası: {e}")
            return ""
    
    def _split_text_for_subtitles(self, text: str, max_chars_per_line: int) -> List[str]:
        """Metni altyazı için uygun satırlara böl"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_chars_per_line:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Saniyeyi SRT zaman formatına çevir"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    async def _create_video_with_ffmpeg(self, background_path: str, audio_path: str,
                                       subtitle_path: str, script_data: Dict,
                                       language: str, style: Dict) -> str:
        """FFmpeg ile video oluştur"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"video_{language}_{timestamp}.mp4"
            output_path = self.output_dir / output_filename
            
            # Font seç
            font_path = self._select_font()
            
            # FFmpeg komutu oluştur
            cmd = [
                'ffmpeg',
                '-loop', '1',
                '-i', background_path,  # Arka plan
                '-i', audio_path,       # Ses dosyası
                '-vf', self._create_video_filter(subtitle_path, font_path, style, language),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:v', self.video_settings['bitrate'],
                '-b:a', self.video_settings['audio_bitrate'],
                '-r', str(self.video_settings['fps']),
                '-shortest',  # En kısa input kadar sürer
                '-y',  # Overwrite
                str(output_path)
            ]
            
            # FFmpeg çalıştır
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Video başarıyla oluşturuldu: {output_filename}")
                
                # Geçici dosyaları temizle
                if subtitle_path and Path(subtitle_path).exists():
                    Path(subtitle_path).unlink()
                
                return str(output_path)
            else:
                logger.error(f"FFmpeg hatası: {result.stderr}")
                raise Exception(f"Video oluşturma başarısız: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout - video oluşturma çok uzun sürdü")
            raise Exception("Video oluşturma timeout")
        except Exception as e:
            logger.error(f"Video oluşturma hatası: {e}")
            raise
    
    def _select_font(self) -> str:
        """En uygun fontu seç"""
        preferred_fonts = ['Montserrat-Bold.ttf', 'Roboto-Bold.ttf', 'OpenSans-Bold.ttf']
        
        for font in preferred_fonts:
            font_path = self.fonts_dir / font
            if font_path.exists():
                return str(font_path)
        
        # Sistem fontunu kullan (fallback)
        return "/System/Library/Fonts/Helvetica.ttc"  # macOS
        # return "C:/Windows/Fonts/arial.ttf"  # Windows
        # return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Linux
    
    def _create_video_filter(self, subtitle_path: str, font_path: str, 
                           style: Dict, language: str) -> str:
        """FFmpeg video filter oluştur"""
        
        subtitle_settings = self.subtitle_settings.get(language, self.subtitle_settings['en'])
        
        # Temel ölçeklendirme
        filter_parts = [
            f"scale={self.video_settings['width']}:{self.video_settings['height']}"
        ]
        
        # Altyazı filtresi
        if subtitle_path and Path(subtitle_path).exists():
            # SRT altyazı stili
            subtitle_filter = (
                f"subtitles='{subtitle_path}'"
                f":force_style='FontName={Path(font_path).stem},"
                f"FontSize={subtitle_settings['font_size']},"
                f"PrimaryColour=&H{style['font_color'].lstrip('#').upper()},"
                f"Alignment=2,"  # Center alignment
                f"MarginV=150'"
            )
            filter_parts.append(subtitle_filter)
        
        # Filtreleri birleştir
        return ",".join(filter_parts)
    
    async def create_thumbnail(self, script_data: Dict, video_path: str, 
                              category: str = 'general') -> str:
        """Video için thumbnail oluştur"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            thumbnail_filename = f"thumbnail_{timestamp}.jpg"
            thumbnail_path = self.output_dir / thumbnail_filename
            
            # Video'nun ilk frame'ini al
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', '00:00:02',  # 2. saniyeden frame al
                '-vframes', '1',
                '-y',
                str(thumbnail_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Thumbnail oluşturuldu: {thumbnail_filename}")
                return str(thumbnail_path)
            else:
                logger.error(f"Thumbnail oluşturma hatası: {result.stderr}")
                return ""
                
        except Exception as e:
            logger.error(f"Thumbnail hatası: {e}")
            return ""
    
    async def add_watermark(self, video_path: str, watermark_text: str = None) -> str:
        """Videoya watermark ekle"""
        try:
            if not watermark_text:
                watermark_text = "AI Generated"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"watermarked_{timestamp}.mp4"
            output_path = self.output_dir / output_filename
            
            # Watermark filtresi
            watermark_filter = (
                f"drawtext=text='{watermark_text}'"
                f":fontcolor=white@0.5"
                f":fontsize=24"
                f":x=w-tw-10"
                f":y=h-th-10"
            )
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', watermark_filter,
                '-c:a', 'copy',
                '-y',
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Watermark eklendi: {output_filename}")
                return str(output_path)
            else:
                logger.error(f"Watermark hatası: {result.stderr}")
                return video_path
                
        except Exception as e:
            logger.error(f"Watermark ekleme hatası: {e}")
            return video_path

# Test fonksiyonu
async def test_video_creator():
    """Video creator test"""
    creator = VideoCreator()
    
    # Test script data
    script_data = {
        'title': 'Test Video',
        'content': 'This is a test video content. It will be converted to speech and then to video with subtitles.',
        'category': 'tech',
        'estimated_duration': 15
    }
    
    # Fake audio file (test için)
    audio_path = "test_audio.mp3"  # Bu dosyanın var olduğunu varsay
    
    if Path(audio_path).exists():
        video_path = await creator.create_video(
            script_data=script_data,
            audio_path=audio_path,
            language='en',
            category='tech'
        )
        
        print(f"Test video oluşturuldu: {video_path}")
    else:
        print("Test için audio dosyası bulunamadı")

if __name__ == "__main__":
    asyncio.run(test_video_creator())