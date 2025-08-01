#!/usr/bin/env python3
"""
Script Generator - Ollama + LangChain ile AI destekli video senaryosu üretimi
RAG (Retrieval Augmented Generation) ve SEAL feedback sistemi dahil
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# LangChain imports
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, DirectoryLoader

logger = logging.getLogger(__name__)

class ScriptGenerator:
    """AI destekli video script üretimi sınıfı"""
    
    def __init__(self):
        # Ollama model ayarları
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model_name = os.getenv('OLLAMA_MODEL', 'mistral')
        
        # LLM'i başlat
        self.llm = Ollama(
            base_url=self.ollama_base_url,
            model=self.model_name,
            temperature=0.7
        )
        
        # RAG için embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Vector database
        self.vector_db_path = "data/vector_db"
        self.vector_db = None
        
        # Knowledge base'i yükle
        self._initialize_knowledge_base()
        
        # Dil-spesifik ayarlar
        self.language_configs = {
            'en': {
                'voice_style': 'professional',
                'max_length': 150,  # kelime
                'hook_examples': ["Did you know that...", "Here's something crazy...", "What if I told you..."]
            },
            'de': {
                'voice_style': 'formal',
                'max_length': 140,
                'hook_examples': ["Wussten Sie, dass...", "Hier ist etwas Verrücktes...", "Was wäre, wenn..."]
            },
            'ko': {
                'voice_style': 'friendly',
                'max_length': 120,
                'hook_examples': ["알고 계셨나요?", "이건 정말 놀라운데요", "만약 제가 말씀드린다면"]
            },
            'zh': {
                'voice_style': 'energetic',
                'max_length': 130,
                'hook_examples': ["你知道吗", "这很疯狂", "如果我告诉你"]
            }
        }
    
    def _initialize_knowledge_base(self):
        """Knowledge base'i hazırla (RAG için)"""
        try:
            knowledge_base_dir = Path("data/knowledge_base")
            
            if knowledge_base_dir.exists() and any(knowledge_base_dir.iterdir()):
                # Mevcut dosyaları yükle
                loader = DirectoryLoader(
                    str(knowledge_base_dir), 
                    glob="*.txt",
                    loader_cls=TextLoader
                )
                documents = loader.load()
                
                # Text splitter
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50
                )
                splits = text_splitter.split_documents(documents)
                
                # Vector database oluştur
                self.vector_db = Chroma.from_documents(
                    documents=splits,
                    embedding=self.embeddings,
                    persist_directory=self.vector_db_path
                )
                
                logger.info(f"Knowledge base yüklendi: {len(splits)} chunk")
            else:
                # İlk çalıştırma için örnek veriler oluştur
                self._create_initial_knowledge_base()
                
        except Exception as e:
            logger.error(f"Knowledge base hatası: {e}")
            self.vector_db = None
    
    def _create_initial_knowledge_base(self):
        """İlk çalıştırma için örnek knowledge base oluştur"""
        knowledge_base_dir = Path("data/knowledge_base")
        knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Örnek içerik dosyaları
        sample_contents = {
            "finance_tips.txt": """
How to Make Money Online in 2025:
1. Start with affiliate marketing - promote products you believe in
2. Create digital products like courses or ebooks
3. Use AI tools to automate content creation
4. Invest in index funds for long-term growth
5. Build multiple income streams

Investment Basics:
- Dollar-cost averaging reduces risk
- Diversification is key to portfolio health
- Emergency fund should be 3-6 months expenses
- High-yield savings accounts for short-term goals
- Consider low-cost index funds for beginners
            """,
            
            "ai_automation.txt": """
AI Automation Tools for 2025:
1. ChatGPT for content writing and coding
2. Midjourney for image generation
3. ElevenLabs for voice synthesis
4. Make.com for workflow automation
5. Zapier for app integrations

YouTube Automation with AI:
- Use AI for script writing
- Generate thumbnails with AI
- Automate video editing with tools like Pictory
- Schedule uploads with Buffer or Hootsuite
- Analyze performance with TubeBuddy
            """,
            
            "productivity_hacks.txt": """
Productivity Tips That Actually Work:
1. Time blocking - schedule specific times for tasks
2. The 2-minute rule - do it now if it takes less than 2 minutes
3. Batch similar tasks together
4. Use the Pomodoro Technique for focus
5. Eliminate distractions during deep work

Excel Automation:
- Use VLOOKUP for data matching
- Conditional formatting for visual cues
- Pivot tables for data analysis
- Macros for repetitive tasks
- Power Query for data transformation
            """
        }
        
        for filename, content in sample_contents.items():
            file_path = knowledge_base_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        logger.info("Örnek knowledge base oluşturuldu")
        
        # Vector DB'yi yeniden başlat
        self._initialize_knowledge_base()
    
    async def generate_script(self, topic: str, language: str = 'en', 
                            category: str = 'general', trend_data: Dict = None) -> Dict[str, Any]:
        """Ana script üretim fonksiyonu"""
        
        logger.info(f"Script üretiliyor: {topic} ({language})")
        
        # Dil konfigürasyonu
        lang_config = self.language_configs.get(language, self.language_configs['en'])
        
        # RAG ile ilgili bilgileri al
        context = self._get_relevant_context(topic, category)
        
        # Script prompt'unu hazırla
        prompt = self._create_script_prompt(
            topic=topic, 
            language=language, 
            category=category, 
            context=context,
            lang_config=lang_config,
            trend_data=trend_data
        )
        
        # LLM'den script oluştur
        script_content = await self._generate_with_llm(prompt)
        
        # Script'i yapılandır
        structured_script = self._structure_script(script_content, lang_config)
        
        # Metadata ekle
        script_data = {
            'topic': topic,
            'language': language,
            'category': category,
            'content': structured_script['content'],
            'hook': structured_script['hook'],
            'main_points': structured_script['main_points'],
            'cta': structured_script['cta'],
            'title': structured_script['title'],
            'description': structured_script['description'],
            'tags': structured_script['tags'],
            'voice_style': lang_config['voice_style'],
            'estimated_duration': self._estimate_duration(structured_script['content']),
            'created_at': datetime.now().isoformat(),
            'context_used': context[:200] + "..." if context else None
        }
        
        # Script'i kaydet
        self._save_script(script_data)
        
        return script_data
    
    def _get_relevant_context(self, topic: str, category: str) -> str:
        """RAG ile ilgili bilgileri getir"""
        if not self.vector_db:
            return ""
        
        try:
            # Topic + category ile arama
            query = f"{topic} {category}"
            relevant_docs = self.vector_db.similarity_search(query, k=3)
            
            context = "\n".join([doc.page_content for doc in relevant_docs])
            return context
            
        except Exception as e:
            logger.error(f"RAG context hatası: {e}")
            return ""
    
    def _create_script_prompt(self, topic: str, language: str, category: str, 
                            context: str, lang_config: Dict, trend_data: Dict = None) -> str:
        """LLM için prompt oluştur"""
        
        # Trend bilgisi varsa ekle
        trend_info = ""
        if trend_data:
            trend_info = f"This topic is currently trending with {trend_data.get('search_volume', 'high')} search volume."
        
        # Kategori-spesifik talimatlar
        category_instructions = {
            'finance': "Focus on practical money-making strategies. Include specific numbers and examples. Mention both opportunities and risks.",
            'tech': "Explain technical concepts in simple terms. Include step-by-step guidance and common mistakes to avoid.",
            'education': "Make it educational but engaging. Use examples and analogies. Provide actionable takeaways.",
            'lifestyle': "Keep it motivational and relatable. Include personal anecdotes and practical tips.",
            'entertainment': "Make it engaging and fun. Use storytelling and humor where appropriate."
        }
        
        category_instruction = category_instructions.get(category, "Keep it informative and engaging.")
        
        # Ana prompt
        prompt = f"""
Create a compelling {lang_config['max_length']}-word video script about: "{topic}"

Language: {language}
Category: {category}
Voice Style: {lang_config['voice_style']}

{trend_info}

CONTEXT (use this information to make the script more accurate and detailed):
{context}

REQUIREMENTS:
1. {category_instruction}
2. Start with a strong hook from these examples: {', '.join(lang_config['hook_examples'])}
3. Structure: Hook → Main Content → Call to Action
4. Make it perfect for YouTube Shorts (60 seconds max)
5. Include 3-5 specific, actionable points
6. End with a compelling call to action
7. Write in {language} language
8. Use simple, conversational language
9. Include numbers and specifics when possible
10. Make it engaging and retention-focused

IMPORTANT: 
- Focus on value and actionable advice
- Avoid fluff and filler words
- Make every sentence count
- Create curiosity and engagement
- Include a reason why viewers should watch till the end

Please provide the script in this format:
TITLE: [Compelling title for the video]
HOOK: [First 5-10 seconds to grab attention]
MAIN_CONTENT: [Core content with 3-5 key points]
CTA: [Call to action]
DESCRIPTION: [YouTube description]
TAGS: [5-8 relevant tags]
"""
        
        return prompt
    
    async def _generate_with_llm(self, prompt: str) -> str:
        """LLM ile text üret"""
        try:
            # LangChain chain oluştur
            prompt_template = PromptTemplate(
                input_variables=["prompt"],
                template="{prompt}"
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            
            # Generate
            response = await chain.arun(prompt=prompt)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"LLM generation hatası: {e}")
            raise
    
    def _structure_script(self, raw_content: str, lang_config: Dict) -> Dict[str, str]:
        """Ham LLM çıktısını yapılandır"""
        
        # Default values
        structured = {
            'title': 'Generated Video',
            'hook': 'Welcome to this video!',
            'main_points': [],
            'content': raw_content,
            'cta': 'Thanks for watching!',
            'description': 'AI generated content',
            'tags': ['ai', 'automation', 'tips']
        }
        
        try:
            # Parse structured output
            lines = raw_content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith('TITLE:'):
                    structured['title'] = line.replace('TITLE:', '').strip()
                elif line.startswith('HOOK:'):
                    structured['hook'] = line.replace('HOOK:', '').strip()
                elif line.startswith('MAIN_CONTENT:'):
                    current_section = 'main_content'
                    structured['main_content'] = line.replace('MAIN_CONTENT:', '').strip()
                elif line.startswith('CTA:'):
                    structured['cta'] = line.replace('CTA:', '').strip()
                    current_section = None
                elif line.startswith('DESCRIPTION:'):
                    structured['description'] = line.replace('DESCRIPTION:', '').strip()
                elif line.startswith('TAGS:'):
                    tags_text = line.replace('TAGS:', '').strip()
                    structured['tags'] = [tag.strip() for tag in tags_text.split(',')]
                elif current_section == 'main_content' and line:
                    if structured['main_content']:
                        structured['main_content'] += ' ' + line
                    else:
                        structured['main_content'] = line
            
            # Ana content'i oluştur
            full_content = f"{structured['hook']} {structured.get('main_content', '')} {structured['cta']}"
            structured['content'] = full_content.strip()
            
            # Main points'i çıkar
            main_content = structured.get('main_content', '')
            if main_content:
                # Numaralı listeler veya bullet pointleri bul
                import re
                points = re.findall(r'(?:\d+\.|\-|\•)\s*([^.!?]+[.!?])', main_content)
                structured['main_points'] = [point.strip() for point in points]
            
        except Exception as e:
            logger.warning(f"Script structuring hatası: {e}")
            # Raw content'i kullan
            structured['content'] = raw_content
        
        return structured
    
    def _estimate_duration(self, content: str) -> int:
        """İçerik süresini tahmin et (saniye)"""
        # Ortalama 150 kelime/dakika konuşma hızı
        word_count = len(content.split())
        duration_seconds = (word_count / 150) * 60
        return int(duration_seconds)
    
    def _save_script(self, script_data: Dict[str, Any]):
        """Script'i dosyaya kaydet"""
        try:
            scripts_dir = Path("output/scripts")
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"script_{script_data['language']}_{timestamp}.json"
            
            filepath = scripts_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Script kaydedildi: {filepath}")
            
        except Exception as e:
            logger.error(f"Script kaydetme hatası: {e}")
    
    def add_to_knowledge_base(self, content: str, category: str):
        """Knowledge base'e yeni içerik ekle (SEAL öğrenme için)"""
        try:
            knowledge_base_dir = Path("data/knowledge_base")
            knowledge_base_dir.mkdir(parents=True, exist_ok=True)
            
            # Kategoriyi dosya adına ekle
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{category}_{timestamp}.txt"
            
            filepath = knowledge_base_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Vector DB'yi güncelle
            self._initialize_knowledge_base()
            
            logger.info(f"Knowledge base güncellendi: {filename}")
            
        except Exception as e:
            logger.error(f"Knowledge base güncelleme hatası: {e}")

# Test fonksiyonu
async def test_script_generator():
    """Script generator test"""
    generator = ScriptGenerator()
    
    script = await generator.generate_script(
        topic="How to make money with AI in 2025",
        language="en",
        category="finance"
    )
    
    print("=== OLUŞTURULAN SCRİPT ===")
    print(f"Başlık: {script['title']}")
    print(f"Dil: {script['language']}")
    print(f"Kategori: {script['category']}")
    print(f"Süre: {script['estimated_duration']} saniye")
    print(f"\nHook: {script['hook']}")
    print(f"\nAna İçerik: {script['content'][:200]}...")
    print(f"\nCTA: {script['cta']}")
    print(f"\nEtiketler: {', '.join(script['tags'])}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_script_generator())