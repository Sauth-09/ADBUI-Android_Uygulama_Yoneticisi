"""
Known Apps Manager
==================
Bilinen (bloatware/kaldırılabilir) uygulamalar listesini yönetir.
GitHub veya başka bir uzak kaynaktan JSON formatında liste çeker.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

from ..utils.config import get_config

# Varsayılan Veri Kaynağı
DEFAULT_SOURCE_URL = "https://raw.githubusercontent.com/Sauth-09/ADBUI-Android_Uygulama_Yoneticisi/main/apps.json" 

@dataclass
class KnownApp:
    """Bilinen bir uygulama tanımı."""
    package: str
    name: str
    description: str
    risk: str  # Safe, Caution, Unsafe
    recommendation: str  # Remove, Disable, Keep
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KnownApp':
        return cls(
            package=data.get('package', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            risk=data.get('risk', 'Unknown'),
            recommendation=data.get('recommendation', 'Unknown')
        )

class KnownAppsManager:
    """Bilinen uygulamaları yöneten sınıf."""
    
    def __init__(self):
        # Config'den URL'yi al, yoksa varsayılanı kullan
        self.source_url = get_config().get('known_apps_url', DEFAULT_SOURCE_URL)
        self._apps: Dict[str, KnownApp] = {}
        self._cache_file = Path("known_apps_cache.json")
    
    def fetch_remote_list(self) -> bool:
        """
        Uzak sunucudan listeyi çeker.
        Başarılı olursa True, değilse False döner.
        """
        try:
            logger.info(f"Liste güncelleniyor: {self.source_url}")
            with urllib.request.urlopen(self.source_url, timeout=10) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    data = json.loads(content)
                    self._parse_and_update(data)
                    self._save_cache(content)
                    return True
                else:
                    logger.error(f"Sunucu hatası: {response.status}")
                    return False
        except urllib.error.URLError as e:
            logger.warning(f"Bağlantı hatası: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"JSON hatası: {e}")
            return False
        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")
            return False
            
    def load_local_cache(self) -> bool:
        """Yerel önbelleği yükler."""
        if not self._cache_file.exists():
            # Cache yoksa varsayılan/gömülü veriyi yükle (opsiyonel)
            self._apps = self._get_hardcoded_defaults()
            return False
            
        try:
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._parse_and_update(data)
            logger.info("Yerel önbellek yüklendi")
            return True
        except Exception as e:
            logger.error(f"Önbellek yükleme hatası: {e}")
            return False
            
    def _parse_and_update(self, data: List[Dict]):
        """JSON verisini parse et ve listeyi güncelle."""
        if not isinstance(data, list):
            logger.error("Veri formatı hatalı: Liste bekleniyor")
            return
            
        self._apps = {}
        for item in data:
            app = KnownApp.from_dict(item)
            if app.package:
                self._apps[app.package] = app
                
        logger.info(f"{len(self._apps)} bilinen uygulama yüklendi")

    def _save_cache(self, content: str):
        """Veriyi önbelleğe kaydeder."""
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Önbellek kayıt hatası: {e}")

    def get_app(self, package_name: str) -> Optional[KnownApp]:
        """Paket adına göre bilinen uygulamayı getirir."""
        return self._apps.get(package_name)
        
    def get_all_apps(self) -> List[KnownApp]:
        """Tüm bilinen uygulamaları getirir."""
        return list(self._apps.values())

    def _get_hardcoded_defaults(self) -> Dict[str, KnownApp]:
        """İnternet yoksa ve cache yoksa kullanılacak varsayılan liste."""
        defaults = [
            {
                "package": "com.miui.daemon",
                "name": "MIUI Daemon",
                "description": "Xiaomi veri toplama ve analiz servisi.",
                "risk": "Safe",
                "recommendation": "Remove"
            },
            {
                "package": "com.miui.analytics",
                "name": "MIUI Analytics",
                "description": "Xiaomi analitik ve reklam servisi.",
                "risk": "Safe",
                "recommendation": "Remove"
            },
            {
                "package": "com.miui.msa.global",
                "name": "MSA (MIUI System Ads)",
                "description": "Xiaomi sistem reklam servisi.",
                "risk": "Safe",
                "recommendation": "Remove"
            },
             {
                "package": "com.google.android.apps.tachyon",
                "name": "Google Duo / Meet",
                "description": "Google görüntülü görüşme uygulaması.",
                "risk": "Safe",
                "recommendation": "Disable"
            },
            {
                "package": "com.google.android.videos",
                "name": "Google TV",
                "description": "Google film ve dizi kiralama servisi.",
                "risk": "Safe",
                "recommendation": "Remove"
            }
        ]
        
        apps = {}
        for item in defaults:
            app = KnownApp.from_dict(item)
            apps[app.package] = app
        return apps
