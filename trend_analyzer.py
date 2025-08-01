#!/usr/bin/env python3
"""
Trend Analyzer - Google Trends, YouTube, Reddit API'leri ile trend analizi
"""

import os
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import requests
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)

@dataclass
class TrendTopic:
    """Trend konusu veri sınıfı"""
    title: str
    category: str
    search_volume: int
    growth_rate: float
    region: str
    related_keywords: List[str]
    content_suggestions: List[str]
    source: str  # 'google_trends', 'youtube', 'reddit'
    confidence_score: float

class TrendAnalyzer:
    """Trend analizi ve konu önerisi sınıfı"""
    
    def __init__(self):
        self.google_trends = TrendReq(hl='en-US', tz=360)
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        
        # Hedef kategoriler
        self.target_categories = {
            'finance': ['money', 'investing', 'crypto', 'stocks', 'business'],
            'tech': ['ai', 'programming', 'technology', 'software', 'automation'],
            'education': ['learning', 'tips', 'tutorial', 'how to', 'guide'],
            'lifestyle': ['productivity', 'motivation', 'success', 'mindset'],
            'entertainment': ['funny', 'viral', 'trending', 'meme', 'story']
        }
        
        # Video formatları için anahtar kelimeler
        self.video_formats = {
            'how_to': ['how to', 'tutorial', 'guide', 'step by step'],
            'tips': ['tips', 'tricks', 'hacks', 'secrets'],
            'list': ['best', 'top', 'worst', '5 ways', '10 things'],
            'story': ['story', 'experience', 'journey', 'case study'],
            'controversial': ['truth about', 'reality of', 'nobody tells you']
        }
    
    async def get_trending_topics(self, count: int = 5) -> List[TrendTopic]:
        """Ana trend analizi fonksiyonu"""
        logger.info(f"Trend analizi başlatılıyor - {count} konu için")
        
        all_trends = []
        
        # Paralel olarak farklı kaynaklardan trend topla
        tasks = [
            self._get_google_trends(),
            self._get_youtube_trends(),
            self._get_reddit_trends()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_trends.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Trend kaynağında hata: {result}")
        
        # Trendleri skorla ve sırala
        scored_trends = self._score_and_rank_trends(all_trends)
        
        # En iyi trendleri döndür
        return scored_trends[:count]
    
    async def _get_google_trends(self) -> List[TrendTopic]:
        """Google Trends'den popüler konuları al"""
        try:
            trends = []
            
            # Günlük trendler
            daily_trends = self.google_trends.trending_searches(pn='united_states')
            
            for trend in daily_trends.head(10).values:
                topic_name = trend[0]
                
                # Kategori belirle
                category = self._categorize_topic(topic_name)
                
                # Video formatı öner
                video_format = self._suggest_video_format(topic_name, category)
                
                trends.append(TrendTopic(
                    title=self._format_topic_for_video(topic_name, video_format),
                    category=category,
                    search_volume=1000,  # Google Trends exact volume vermiyor
                    growth_rate=0.8,
                    region='US',
                    related_keywords=[topic_name],
                    content_suggestions=self._generate_content_suggestions(topic_name, category),
                    source='google_trends',
                    confidence_score=0.7
                ))
            
            logger.info(f"Google Trends'den {len(trends)} konu alındı")
            return trends
            
        except Exception as e:
            logger.error(f"Google Trends hatası: {e}")
            return []
    
    async def _get_youtube_trends(self) -> List[TrendTopic]:
        """YouTube trending videolarından konu çıkar"""
        if not self.youtube_api_key:
            logger.warning("YouTube API key bulunamadı")
            return []