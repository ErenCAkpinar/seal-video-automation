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
        
        try:
            trends = []
            
            # YouTube API'den trending videolar
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'snippet,statistics',
                'chart': 'mostPopular',
                'regionCode': 'US',
                'videoCategoryId': '22',  # People & Blogs
                'maxResults': 20,
                'key': self.youtube_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for video in data.get('items', []):
                            title = video['snippet']['title']
                            view_count = int(video['statistics'].get('viewCount', 0))
                            
                            # Çok popüler videolardan ilham al
                            if view_count > 100000:
                                category = self._categorize_topic(title)
                                video_format = self._suggest_video_format(title, category)
                                
                                # Başlığı kendi formatımıza çevir
                                new_title = self._format_topic_for_video(title, video_format)
                                
                                trends.append(TrendTopic(
                                    title=new_title,
                                    category=category,
                                    search_volume=view_count // 1000,  # Basitleştirilmiş
                                    growth_rate=0.6,
                                    region='US',
                                    related_keywords=self._extract_keywords(title),
                                    content_suggestions=self._generate_content_suggestions(title, category),
                                    source='youtube',
                                    confidence_score=0.8
                                ))
            
            logger.info(f"YouTube'dan {len(trends)} konu alındı")
            return trends
            
        except Exception as e:
            logger.error(f"YouTube Trends hatası: {e}")
            return []
    
    async def _get_reddit_trends(self) -> List[TrendTopic]:
        """Reddit'den trending konuları al"""
        try:
            trends = []
            
            # Popüler subreddit'ler
            subreddits = ['entrepreneur', 'investing', 'technology', 'LifeProTips', 
                         'personalfinance', 'Python', 'artificial', 'Futurology']
            
            async with aiohttp.ClientSession() as session:
                for subreddit in subreddits:
                    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                    
                    try:
                        async with session.get(url, headers={'User-Agent': 'TrendBot 1.0'}) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                for post in data['data']['children']:
                                    post_data = post['data']
                                    title = post_data['title']
                                    score = post_data['score']
                                    
                                    if score > 100:  # Popüler postlar
                                        category = self._categorize_topic(title)
                                        video_format = self._suggest_video_format(title, category)
                                        
                                        new_title = self._format_topic_for_video(title, video_format)
                                        
                                        trends.append(TrendTopic(
                                            title=new_title,
                                            category=category,
                                            search_volume=score,
                                            growth_rate=0.5,
                                            region='Global',
                                            related_keywords=self._extract_keywords(title),
                                            content_suggestions=self._generate_content_suggestions(title, category),
                                            source='reddit',
                                            confidence_score=0.6
                                        ))
                    
                    except Exception as e:
                        logger.warning(f"Reddit subreddit hatası ({subreddit}): {e}")
                        continue
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
            
            logger.info(f"Reddit'den {len(trends)} konu alındı")
            return trends
            
        except Exception as e:
            logger.error(f"Reddit Trends hatası: {e}")
            return []
    
    def _categorize_topic(self, topic: str) -> str:
        """Konuyu kategorilere ayır"""
        topic_lower = topic.lower()
        
        for category, keywords in self.target_categories.items():
            for keyword in keywords:
                if keyword in topic_lower:
                    return category
        
        return 'general'
    
    def _suggest_video_format(self, topic: str, category: str) -> str:
        """Video formatı öner"""
        topic_lower = topic.lower()
        
        # Format anahtar kelimelerine göre belirle
        for format_type, keywords in self.video_formats.items():
            for keyword in keywords:
                if keyword in topic_lower:
                    return format_type
        
        # Kategoriye göre varsayılan format
        if category == 'finance':
            return 'tips'
        elif category == 'tech':
            return 'how_to'
        elif category == 'education':
            return 'list'
        else:
            return 'story'
    
    def _format_topic_for_video(self, original_topic: str, video_format: str) -> str:
        """Konuyu video formatına göre yeniden formatla"""
        
        # Format şablonları
        format_templates = {
            'how_to': [
                "How to {topic} in 2025",
                "Complete Guide to {topic}",
                "Step by Step {topic} Tutorial"
            ],
            'tips': [
                "5 {topic} Tips That Actually Work",
                "Secret {topic} Tricks Nobody Tells You",
                "{topic} Hacks That Will Change Your Life"
            ],
            'list': [
                "Top 5 {topic} Methods",
                "Best {topic} Strategies for Beginners",
                "5 Ways to Master {topic}"
            ],
            'story': [
                "My {topic} Journey: What I Learned",
                "The Truth About {topic}",
                "What Nobody Tells You About {topic}"
            ],
            'controversial': [
                "The Dark Side of {topic}",
                "Why {topic} is Overrated",
                "{topic}: Scam or Legit?"
            ]
        }
        
        templates = format_templates.get(video_format, format_templates['tips'])
        template = templates[0]  # İlk şablonu kullan
        
        # Konuyu temizle ve şablona yerleştir
        clean_topic = self._clean_topic(original_topic)
        return template.format(topic=clean_topic)
    
    def _clean_topic(self, topic: str) -> str:
        """Konu metnini temizle"""
        # Gereksiz kelimeleri kaldır
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = topic.split()
        cleaned_words = [word for word in words if word.lower() not in stop_words]
        
        # İlk 3-4 kelimeyi al
        return ' '.join(cleaned_words[:4])
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Metinden anahtar kelimeleri çıkar"""
        # Basit keyword extraction
        words = text.lower().split()
        keywords = [word for word in words if len(word) > 3]
        return keywords[:5]  # İlk 5 kelime
    
    def _generate_content_suggestions(self, topic: str, category: str) -> List[str]:
        """İçerik önerileri oluştur"""
        suggestions = []
        
        if category == 'finance':
            suggestions = [
                "Start with basic concepts",
                "Include real examples",
                "Mention risks and benefits",
                "Add actionable steps",
                "Include success stories"
            ]
        elif category == 'tech':
            suggestions = [
                "Explain in simple terms",
                "Show practical examples",
                "Include code snippets if relevant",
                "Mention common mistakes",
                "Provide resources for learning"
            ]
        elif category == 'education':
            suggestions = [
                "Break down into steps",
                "Use visual examples",
                "Include practice exercises",
                "Mention common pitfalls",
                "Provide additional resources"
            ]
        else:
            suggestions = [
                "Keep it engaging",
                "Use storytelling",
                "Include personal examples",
                "Make it relatable",
                "Add call to action"
            ]
        
        return suggestions
    
    def _score_and_rank_trends(self, trends: List[TrendTopic]) -> List[TrendTopic]:
        """Trendleri skorla ve sırala"""
        
        for trend in trends:
            # Temel skor hesaplama
            base_score = trend.confidence_score
            
            # Kategori bonusu
            category_bonus = {
                'finance': 1.3,
                'tech': 1.2,
                'education': 1.1,
                'lifestyle': 0.9,
                'entertainment': 0.8
            }
            base_score *= category_bonus.get(trend.category, 1.0)
            
            # Kaynak bonusu
            source_bonus = {
                'youtube': 1.2,
                'google_trends': 1.1,
                'reddit': 0.9
            }
            base_score *= source_bonus.get(trend.source, 1.0)
            
            # Search volume bonusu
            if trend.search_volume > 1000:
                base_score *= 1.2
            elif trend.search_volume > 500:
                base_score *= 1.1
            
            # Final skoru güncelle
            trend.confidence_score = min(base_score, 1.0)
        
        # Skoruna göre sırala
        return sorted(trends, key=lambda x: x.confidence_score, reverse=True)
    
    def save_trends_to_file(self, trends: List[TrendTopic], filename: str = None):
        """Trendleri dosyaya kaydet"""
        if filename is None:
            filename = f"data/trends/trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        trends_data = []
        for trend in trends:
            trends_data.append({
                'title': trend.title,
                'category': trend.category,
                'search_volume': trend.search_volume,
                'growth_rate': trend.growth_rate,
                'region': trend.region,
                'related_keywords': trend.related_keywords,
                'content_suggestions': trend.content_suggestions,
                'source': trend.source,
                'confidence_score': trend.confidence_score,
                'created_at': datetime.now().isoformat()
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(trends_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Trendler kaydedildi: {filename}")

# Test fonksiyonu
async def test_trend_analyzer():
    """Trend analyzer test"""
    analyzer = TrendAnalyzer()
    trends = await analyzer.get_trending_topics(5)
    
    print("=== TREND ANALİZİ SONUÇLARI ===")
    for i, trend in enumerate(trends, 1):
        print(f"\n{i}. {trend.title}")
        print(f"   Kategori: {trend.category}")
        print(f"   Kaynak: {trend.source}")
        print(f"   Skor: {trend.confidence_score:.2f}")
        print(f"   Anahtar kelimeler: {', '.join(trend.related_keywords[:3])}")

if __name__ == "__main__":
    asyncio.run(test_trend_analyzer())