#!/usr/bin/env python3
"""
Voiceover Generator - ElevenLabs API ile çoklu dil seslendirme
"""

import os
import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class VoiceoverGenerator:
    """ElevenLabs API ile çoklu dil seslendirme sınıfı"""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.api_base = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            logger.warning("ElevenLabs API key bulunamadı")
        
        # Dil-spesifik ses konfigürasyonları
        self.voice_configs = {
            'en': {
                'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Rachel - Professional
                'model_id': 'eleven_multilingual_v2',
                'stability': 0.5,
                'similarity_boost': 0.8,
                'style': 0.0,
                'use_speaker_boost': True
            },
            'de': {
                'voice_id': 'pNInz6obpgDQGcFmaJgB',  # Adam - German
                'model_id': 'eleven_multilingual_v2',
                'stability': 0.6,
                'similarity_boost': 0.7,
                'style': 0.1,
                'use_speaker_boost': True
            },
            'ko': {
                'voice_id': 'Xb7hH8MSUJpSbSDYk0k2',  # Alice - Multilingual
                'model_id': 'eleven_multilingual_v2',
                'stability': 0.4,
                'similarity_boost': 0.9,
                'style': 0.2,
                'use_speaker_boost': True
            },
            'zh': {
                'voice_id': 'pMsXgVXv3BLzUgSXRplE',  # Serena - Multilingual
                'model_id': 'eleven_multilingual_v2',
                'stability': 0.5,
                'similarity_boost': 0.8,
                'style': 0.1,
                'use_speaker_boost': True
            }
        }
        
        # Voice style presets
        self.style_presets = {
            'professional': {'stability': 0.6, 'similarity_boost': 0.8, 'style': 0.0},
            'energetic': {'stability': 0.4, 'similarity_boost': 0.9, 'style': 0.3},
            'calm': {'stability': 0.8, 'similarity_boost': 0.6, 'style': 0.1},
            'friendly': {'stability': 0.5, 'similarity_boost': 0.7, 'style': 0.2},
            'formal': {'stability': 0.7, 'similarity_boost': 0.8, 'style': 0.0}
        }
        
        # Output klasörü
        self.output_dir = Path("output/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_voiceover(self, text: str, language: str = 'en', 
                              voice_style: str = 'professional', 
                              custom_voice_id: str = None) -> str:
        """Ana seslendirme oluşturma fonksiyonu"""
        
        logger.info(f"Seslendirme oluşturuluyor ({language}): {len(text)} karakter")
        
        if not self.api_key:
            logger.error("ElevenLabs API key bulunamadı")
            return await self._create_fallback_audio(text, language)
        
        try:
            # Voice konfigürasyonu
            voice_config = self.voice_configs.get(language, self.voice_configs['en'])
            
            # Custom voice varsa kullan
            if custom_voice_id:
                voice_config['voice_id'] = custom_voice_id
            
            # Style preset uygula
            if voice_style in self.style_presets:
                style_settings = self.style_presets[voice_style]
                voice_config.update(style_settings)
            
            # Uzun metinleri böl
            text_chunks = self._split_text_for_tts(text)
            audio_files = []
            
            for i, chunk in enumerate(text_chunks):
                audio_file = await self._generate_audio_chunk(
                    chunk, voice_config, language, i
                )
                if audio_file:
                    audio_files.append(audio_file)
            
            # Ses dosyalarını birleştir
            if len(audio_files) > 1:
                final_audio = await self._merge_audio_files(audio_files, language)
            else:
                final_audio = audio_files[0] if audio_files else None
            
            if final_audio:
                logger.info(f"Seslendirme oluşturuldu: {final_audio}")
                return str(final_audio)
            else:
                logger.error("Ses oluşturulamadı")
                return await self._create_fallback_audio(text, language)
                
        except Exception as e:
            logger.error(f"Seslendirme hatası: {e}")
            return await self._create_fallback_audio(text, language)
    
    def _split_text_for_tts(self, text: str, max_chars: int = 2500) -> list:
        """Metni TTS için uygun parçalara böl"""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence + '. ') <= max_chars:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _generate_audio_chunk(self, text: str, voice_config: Dict, 
                                  language: str, chunk_index: int) -> Optional[Path]:
        """Tek bir metin parçası için ses üret"""
        
        try:
            url = f"{self.api_base}/text-to-speech/{voice_config['voice_id']}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            payload = {
                "text": text,
                "model_id": voice_config['model_id'],
                "voice_settings": {
                    "stability": voice_config['stability'],
                    "similarity_boost": voice_config['similarity_boost'],
                    "style": voice_config.get('style', 0.0),
                    "use_speaker_boost": voice_config.get('use_speaker_boost', True)
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        # Dosya adı oluştur
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"voice_{language}_{timestamp}_chunk{chunk_index}.mp3"
                        filepath = self.output_dir / filename
                        
                        # Ses dosyasını kaydet
                        audio_data = await response.read()
                        with open(filepath, 'wb') as f:
                            f.write(audio_data)
                        
                        logger.info(f"Ses parçası oluşturuldu: {filename}")
                        return filepath
                    else:
                        error_text = await response.text()
                        logger.error(f"ElevenLabs API hatası: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ses chunk oluşturma hatası: {e}")
            return None
    
    async def _merge_audio_files(self, audio_files: list, language: str) -> Optional[Path]:
        """Ses dosyalarını birleştir"""
        try:
            import subprocess
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"voice_{language}_{timestamp}_final.mp3"
            output_path = self.output_dir / output_filename
            
            # FFmpeg ile birleştir
            file_list_path = self.output_dir / f"filelist_{timestamp}.txt"
            
            with open(file_list_path, 'w') as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file.absolute()}'\n")
            
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', str(file_list_path),
                '-c', 'copy',
                str(output_path),
                '-y'  # Overwrite output file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Geçici dosyaları temizle
                file_list_path.unlink()
                for audio_file in audio_files:
                    audio_file.unlink()
                
                logger.info(f"Ses dosyaları birleştirildi: {output_filename}")
                return output_path
            else:
                logger.error(f"FFmpeg hatası: {result.stderr}")
                return audio_files[0]  # İlk dosyayı döndür
                
        except Exception as e:
            logger.error(f"Ses birleştirme hatası: {e}")
            return audio_files[0] if audio_files else None
    
    async def _create_fallback_audio(self, text: str, language: str) -> str:
        """Fallback ses oluştur (TTS hatası durumunda)"""
        try:
            # gTTS ile basit TTS (yedek çözüm)
            from gtts import gTTS
            import io
            
            # Dil kodlarını gTTS formatına çevir
            gtts_lang_map = {
                'en': 'en',
                'de': 'de',
                'ko': 'ko',
                'zh': 'zh'
            }
            
            gtts_lang = gtts_lang_map.get(language, 'en')
            
            # gTTS ile ses oluştur
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voice_fallback_{language}_{timestamp}.mp3"
            filepath = self.output_dir / filename
            
            tts.save(str(filepath))
            
            logger.info(f"Fallback ses oluşturuldu: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Fallback TTS hatası: {e}")
            
            # Son çare: sessiz ses dosyası oluştur
            return await self._create_silent_audio(language)
    
    async def _create_silent_audio(self, language: str) -> str:
        """Sessiz ses dosyası oluştur (son çare)"""
        try:
            import subprocess
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"voice_silent_{language}_{timestamp}.mp3"
            filepath = self.output_dir / filename
            
            # 30 saniye sessiz audio
            cmd = [
                'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-t', '30', '-c:a', 'mp3', str(filepath), '-y'
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            logger.warning(f"Sessiz ses dosyası oluşturuldu: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Sessiz ses oluşturma hatası: {e}")
            return ""
    
    async def get_available_voices(self, language: str = None) -> Dict[str, Any]:
        """Mevcut sesleri listele"""
        if not self.api_key:
            return {}
        
        try:
            url = f"{self.api_base}/voices"
            headers = {"xi-api-key": self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        voices = {}
                        
                        for voice in data.get('voices', []):
                            voice_info = {
                                'name': voice['name'],
                                'voice_id': voice['voice_id'],
                                'category': voice.get('category', 'unknown'),
                                'description': voice.get('description', ''),
                                'preview_url': voice.get('preview_url', ''),
                                'labels': voice.get('labels', {})
                            }
                            
                            # Dil filtresi
                            if language:
                                voice_labels = voice.get('labels', {})
                                if language in str(voice_labels).lower():
                                    voices[voice['voice_id']] = voice_info
                            else:
                                voices[voice['voice_id']] = voice_info
                        
                        return voices
                    else:
                        logger.error(f"Voices API hatası: {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"Voices listesi hatası: {e}")
            return {}
    
    def get_voice_config(self, language: str) -> Dict[str, Any]:
        """Dil için ses konfigürasyonunu döndür"""
        return self.voice_configs.get(language, self.voice_configs['en'])
    
    def update_voice_config(self, language: str, config: Dict[str, Any]):
        """Ses konfigürasyonunu güncelle (SEAL öğrenme için)"""
        if language in self.voice_configs:
            self.voice_configs[language].update(config)
            logger.info(f"Voice config güncellendi ({language}): {config}")
        else:
            self.voice_configs[language] = config
            logger.info(f"Yeni voice config eklendi ({language}): {config}")

# Test fonksiyonu
async def test_voiceover():
    """Voiceover test"""
    generator = VoiceoverGenerator()
    
    test_text = "Hello! This is a test of the AI voice generation system. It supports multiple languages and voice styles."
    
    # İngilizce test
    audio_path = await generator.create_voiceover(
        text=test_text,
        language='en',
        voice_style='professional'
    )
    
    print(f"Ses dosyası oluşturuldu: {audio_path}")
    
    # Mevcut sesleri listele
    voices = await generator.get_available_voices()
    print(f"\nMevcut ses sayısı: {len(voices)}")

if __name__ == "__main__":
    asyncio.run(test_voiceover())