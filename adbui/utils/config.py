"""
Utils - Config Module
=====================
Uygulama konfigürasyon yönetimi.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Uygulama konfigürasyonu."""
    
    # AI Ayarları
    openai_api_key: str = ""
    ai_model: str = "gpt-3.5-turbo"
    ai_enabled: bool = True
    
    # UI Ayarları
    theme: str = "dark"
    language: str = "tr"
    window_width: int = 1400
    window_height: int = 900
    
    # ADB Ayarları
    adb_path: str = ""
    auto_detect_device: bool = True
    command_timeout: int = 30
    
    # Güvenlik Ayarları
    confirm_critical_actions: bool = True
    show_system_packages: bool = True
    enable_dangerous_operations: bool = False
    
    # Cache Ayarları
    cache_enabled: bool = True
    cache_ttl_days: int = 30


class ConfigManager:
    """
    Konfigürasyon yöneticisi.
    
    JSON dosyasında ayarları saklar ve yönetir.
    """
    
    DEFAULT_CONFIG_DIR = Path.home() / ".adbui"
    CONFIG_FILENAME = "config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        ConfigManager'ı başlat.
        
        Args:
            config_path: Konfigürasyon dosyası yolu
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self.DEFAULT_CONFIG_DIR / self.CONFIG_FILENAME
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load()
    
    @property
    def config(self) -> AppConfig:
        """Mevcut konfigürasyon."""
        return self._config
    
    def _load(self) -> AppConfig:
        """Konfigürasyonu dosyadan yükle."""
        if not self.config_path.exists():
            logger.info("Konfigürasyon dosyası bulunamadı, varsayılan oluşturuluyor")
            config = AppConfig()
            self._save(config)
            return config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Sadece tanımlı alanları kullan
            valid_fields = {f.name for f in AppConfig.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in data.items() if k in valid_fields}
            
            return AppConfig(**filtered_data)
            
        except Exception as e:
            logger.error(f"Konfigürasyon yükleme hatası: {e}")
            return AppConfig()
    
    def _save(self, config: AppConfig) -> bool:
        """Konfigürasyonu dosyaya kaydet."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Konfigürasyon kaydetme hatası: {e}")
            return False
    
    def save(self) -> bool:
        """Mevcut konfigürasyonu kaydet."""
        return self._save(self._config)
    
    def reload(self):
        """Konfigürasyonu yeniden yükle."""
        self._config = self._load()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Konfigürasyon değeri al."""
        return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Konfigürasyon değeri ayarla.
        
        Args:
            key: Ayar adı
            value: Yeni değer
            
        Returns:
            bool: Başarılı mı?
        """
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            return self.save()
        else:
            logger.warning(f"Bilinmeyen konfigürasyon anahtarı: {key}")
            return False
    
    def reset(self) -> AppConfig:
        """Varsayılan ayarlara dön."""
        self._config = AppConfig()
        self.save()
        return self._config


# Global config instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Global konfigürasyon yöneticisini al."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
