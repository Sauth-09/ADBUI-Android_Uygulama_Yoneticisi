"""
AI Analyzer Module
==================
Google Gemini API entegrasyonu ile paket analizi.
Yeni google-genai paketi kullanılıyor.
"""

import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Google GenAI paketi (Lazy import yapılacak)
GEMINI_AVAILABLE = None  # İlk kullanımda kontrol edilecek


# Kullanılabilir modeller
AVAILABLE_MODELS = [
    "gemini-2.5-flash",        # En yeni, dengeli
    "gemini-2.5-flash-lite",   # Hafif ve hızlı
    "gemini-flash-latest",     # En güncel flash
]

DEFAULT_MODEL = "gemini-2.5-flash"


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
    
    Google Gemini API kullanarak paketler hakkında bilgi sağlar.
    """
    
    # Sistem prompt'u
    SYSTEM_PROMPT = """Sen bir Android uzmanısın. Kullanıcının verdiği Android paket adını analiz et.
    
Yanıtını aşağıdaki JSON formatında ver:
{
    "description": "Paketin ne işe yaradığı (Türkçe, 1-2 cümle)",
    "safety_score": 1-10 arası güvenlik skoru (10=çok güvenli kaldırılabilir),
    "safe_to_remove": true/false,
    "removal_impact": "Kaldırılırsa ne olur? (Türkçe)",
    "alternative_action": "Alternatif öneri: freeze/appops/none (Türkçe açıklama)",
    "recommendation": "Genel öneri (Türkçe)"
}

Kurallar:
- Sistem kritik paketleri (systemui, settings, phone, launcher) için safe_to_remove: false ve safety_score: 1-3
- Bloatware ve gereksiz uygulamalar için safe_to_remove: true ve safety_score: 8-10
- Bilinmeyen paketler için ihtiyatlı ol, safety_score: 5
- Her zaman geçerli JSON döndür, başka bir şey yazma"""

    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        cache_manager = None
    ):
        """
        Analyzer'ı başlat.
        
        Args:
            api_key: Google Gemini API anahtarı
            model: Kullanılacak model
            cache_manager: Cache yöneticisi (opsiyonel)
        """
        self.api_key = api_key
        self.model_name = model
        self.cache = cache_manager
        self._client = None
        
        if api_key:
            self._configure_gemini(api_key)
    
    def _configure_gemini(self, api_key: str):
        """Gemini API'yi yapılandır."""
        global GEMINI_AVAILABLE
        
        try:
            # Lazy import
            from google import genai
            GEMINI_AVAILABLE = True
            
            self._client = genai.Client(api_key=api_key)
            logger.info(f"Gemini API yapılandırıldı: {self.model_name}")
        except ImportError:
            GEMINI_AVAILABLE = False
            logger.warning("google-genai paketi yüklü değil. AI özellikleri devre dışı.")
            self._client = None
        except Exception as e:
            logger.error(f"Gemini yapılandırma hatası: {e}")
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """AI hizmeti kullanılabilir mi?"""
        return self._client is not None
    
    def set_api_key(self, api_key: str):
        """API anahtarını ayarla."""
        self.api_key = api_key
        # API key varsa yapılandırmayı dene (bu modülü de yükler)
        if api_key:
            self._configure_gemini(api_key)
    
    def set_model(self, model: str):
        """Modeli değiştir."""
        self.model_name = model
        logger.info(f"Model değiştirildi: {model}")
    
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
            # Prompt oluştur
            prompt = f"{self.SYSTEM_PROMPT}\n\nPaket: {package_name}"
            
            # Gemini'ye gönder (yeni basit API)
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            
            content = response.text
            
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
            
            # Markdown code block içinde olabilir
            if '```' in content:
                lines = content.split('\n')
                json_lines = []
                in_block = False
                for line in lines:
                    if line.strip().startswith('```'):
                        in_block = not in_block
                        continue
                    if in_block:
                        json_lines.append(line)
                content = '\n'.join(json_lines)
            
            # JSON'u bul (süslü parantezler arası)
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                content = content[start:end]
            
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
            logger.error(f"JSON parse hatası: {e}\nİçerik: {content[:200]}")
            return None
    
    
    def analyze_multiple(self, package_names: list) -> Dict[str, AIAnalysis]:
        """
        Birden fazla paketi tek bir API isteği ile analiz et (Batch Prompt).
        
        Args:
            package_names: Paket adları listesi
            
        Returns:
            Dict[str, AIAnalysis]: Paket adı -> Analiz sonucu
        """
        # AI kullanılabilir değilse boş dön
        if not self.is_available or not package_names:
            return {}
            
        # Zaten cache'de olanları ele
        results = {}
        packages_to_ask = []
        
        if self.cache:
            for pkg in package_names:
                cached = self.cache.get(pkg)
                if cached:
                    results[pkg] = cached
                    cached.is_cached = True
                else:
                    packages_to_ask.append(pkg)
        else:
            packages_to_ask = package_names
            
        if not packages_to_ask:
            return results
            
        try:
            # Batch prompt oluştur
            pkg_list_str = "\n".join([f"- {pkg}" for pkg in packages_to_ask])
            
            prompt = f"""{self.SYSTEM_PROMPT}

Aşağıdaki paketleri analiz et. Yanıtını bir JSON Listesi olarak ver.
Örnek:
[
  {{ "package": "com.ornek.paket", "description": "...", "safety_score": 5, ... }},
  {{ "package": "com.diger.paket", ... }}
]

Analiz edilecek paketler:
{pkg_list_str}"""
            
            # Gemini'ye gönder
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            
            content = response.text
            
            # JSON parse et
            batch_results = self._parse_batch_response(content)
            
            # Cache'e kaydet ve results'a ekle
            for pkg_name, analysis in batch_results.items():
                if self.cache:
                    self.cache.set(pkg_name, analysis)
                results[pkg_name] = analysis
                
            return results
            
        except Exception as e:
            logger.error(f"Toplu AI analizi başarısız: {e}")
            raise e

    def _parse_batch_response(self, content: str) -> Dict[str, AIAnalysis]:
        """Batch API yanıtını parse et."""
        results = {}
        raw_content = content
        
        try:
            # JSON temizle
            content = content.strip()
            
            # Markdown block temizliği
            if '```' in content:
                lines = content.split('\n')
                json_lines = []
                in_block = False
                found_block = False
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('```'):
                        in_block = not in_block
                        continue
                    if in_block:
                        json_lines.append(line)
                        found_block = True
                
                if found_block:
                    content = '\n'.join(json_lines)
            
            # JSON Array bul ([...])
            start = content.find('[')
            end = content.rfind(']') + 1
            
            if start == -1 or end <= start:
                logger.warning(f"Batch yanıtta JSON listesi ([...]) bulunamadı. Raw: {raw_content[:200]}")
                return {}
            
            content = content[start:end]
            
            try:
                data_list = json.loads(content)
            except json.JSONDecodeError as je:
                logger.error(f"JSON Decode hatası: {je}")
                return {}
            
            if not isinstance(data_list, list):
                logger.warning(f"API yanıtı liste değil: {type(data_list)}")
                return {}
            
            for item in data_list:
                pkg_name = item.get('package')
                if not pkg_name:
                    continue
                    
                analysis = AIAnalysis(
                    description=item.get('description', 'Açıklama yok'),
                    safety_score=int(item.get('safety_score', 5)),
                    safe_to_remove=bool(item.get('safe_to_remove', False)),
                    removal_impact=item.get('removal_impact', 'Bilinmiyor'),
                    alternative_action=item.get('alternative_action', 'Yok'),
                    recommendation=item.get('recommendation', 'Dikkatli olun')
                )
                results[pkg_name] = analysis
                
            return results
            
        except Exception as e:
            logger.error(f"Batch JSON genel hata: {e}")
            logger.debug(f"Hatalı İçerik: {raw_content}")
            return {}

    def analyze_batch(
        self, 
        package_names: list, 
        progress_callback=None
    ) -> Dict[str, AIAnalysis]:
        """
        Birden fazla paketi analiz et (Eski metod).
        
        Args:
            package_names: Paket adları listesi
            progress_callback: İlerleme callback fonksiyonu
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
