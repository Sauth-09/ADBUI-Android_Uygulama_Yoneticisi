"""
AI Analyzer Module
==================
OpenAI API entegrasyonu ile paket analizi.
"""

import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# OpenAI paketi opsiyonel
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai paketi yüklü değil. AI özellikleri devre dışı.")


@dataclass
class AIAnalysis:
    """AI paket analizi sonucu."""
    description: str  # Paketin ne işe yaradığı
    safety_score: int  # 1-10 arası güvenlik skoru
    safe_to_remove: bool  # Kaldırılması güvenli mi?
    removal_impact: str  # Kaldırılırsa ne olur?
    alternative_action: str  # Alternatif öneri
    recommendation: str  # Genel öneri
    is_cached: bool = False  # Cache'den mi geldi?


class PackageAnalyzer:
    """
    Yapay zeka tabanlı paket analizci.
    
    OpenAI API kullanarak paketler hakkında bilgi sağlar.
    """
    
    # Sistem prompt'u
    SYSTEM_PROMPT = """Sen bir Android uzmanısın. Kullanıcının verdiği Android paket adını analiz et.
    
Yanıtını aşağıdaki JSON formatında ver:
{
    "description": "Paketin ne işe yaradığı (Türkçe, 1-2 cümle)",
    "safety_score": 1-10 arası güvenlik skoru (10=çok güvenli),
    "safe_to_remove": true/false,
    "removal_impact": "Kaldırılırsa ne olur? (Türkçe)",
    "alternative_action": "Alternatif öneri: freeze/appops/none (Türkçe açıklama)",
    "recommendation": "Genel öneri (Türkçe)"
}

Kurallar:
- Sistem kritik paketleri (systemui, settings, phone) için safe_to_remove: false
- Bloatware için safe_to_remove: true
- Bilinmeyen paketler için ihtiyatlı ol
- Her zaman geçerli JSON döndür"""

    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        cache_manager = None
    ):
        """
        Analyzer'ı başlat.
        
        Args:
            api_key: OpenAI API anahtarı
            model: Kullanılacak model
            cache_manager: Cache yöneticisi (opsiyonel)
        """
        self.api_key = api_key
        self.model = model
        self.cache = cache_manager
        self._client = None
        
        if api_key and OPENAI_AVAILABLE:
            self._client = openai.OpenAI(api_key=api_key)
    
    @property
    def is_available(self) -> bool:
        """AI hizmeti kullanılabilir mi?"""
        return self._client is not None
    
    def set_api_key(self, api_key: str):
        """API anahtarını ayarla."""
        self.api_key = api_key
        if OPENAI_AVAILABLE:
            self._client = openai.OpenAI(api_key=api_key)
    
    def analyze(self, package_name: str) -> Optional[AIAnalysis]:
        """
        Paketi analiz et.
        
        Args:
            package_name: Analiz edilecek paket adı
            
        Returns:
            AIAnalysis: Analiz sonucu veya None
        """
        # Önce cache'e bak
        if self.cache:
            cached = self.cache.get(package_name)
            if cached:
                logger.debug(f"Cache'den alındı: {package_name}")
                cached.is_cached = True
                return cached
        
        # AI kullanılabilir değilse None dön
        if not self.is_available:
            logger.warning("AI hizmeti kullanılamıyor")
            return None
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Paket: {package_name}"}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # JSON parse et
            analysis = self._parse_response(content)
            
            if analysis and self.cache:
                self.cache.set(package_name, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI analizi başarısız ({package_name}): {e}")
            return None
    
    def _parse_response(self, content: str) -> Optional[AIAnalysis]:
        """API yanıtını parse et."""
        try:
            # JSON bloğunu bul
            content = content.strip()
            if content.startswith('```'):
                # Markdown code block içinde olabilir
                lines = content.split('\n')
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith('```'):
                        in_block = not in_block
                        continue
                    if in_block or not line.startswith('```'):
                        json_lines.append(line)
                content = '\n'.join(json_lines)
            
            data = json.loads(content)
            
            return AIAnalysis(
                description=data.get('description', 'Açıklama yok'),
                safety_score=int(data.get('safety_score', 5)),
                safe_to_remove=bool(data.get('safe_to_remove', False)),
                removal_impact=data.get('removal_impact', 'Bilinmiyor'),
                alternative_action=data.get('alternative_action', 'Yok'),
                recommendation=data.get('recommendation', 'Dikkatli olun')
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse hatası: {e}")
            return None
    
    def analyze_batch(
        self, 
        package_names: list, 
        progress_callback=None
    ) -> Dict[str, AIAnalysis]:
        """
        Birden fazla paketi analiz et.
        
        Args:
            package_names: Paket adları listesi
            progress_callback: İlerleme callback fonksiyonu
            
        Returns:
            Dict[str, AIAnalysis]: Paket adı -> Analiz sonucu
        """
        results = {}
        total = len(package_names)
        
        for i, name in enumerate(package_names):
            analysis = self.analyze(name)
            if analysis:
                results[name] = analysis
            
            if progress_callback:
                progress_callback(i + 1, total, name)
        
        return results
