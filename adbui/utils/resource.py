"""
Resource Utils
==============
Kaynak dosyalarının yollarını yöneten yardımcı modül.
Hem geliştirme ortamında hem de PyInstaller ile derlenmiş (frozen)
ortamda doğru dosya yollarını bulmayı sağlar.
"""

import sys
import os
from pathlib import Path

def get_resource_path(relative_path: str) -> str:
    """
    Kaynak dosyasının mutlak yolunu döndürür.
    
    Args:
        relative_path: Proje kök dizinine göre göreceli yol (örn: 'adbui/assets/icon.png')
        
    Returns:
        str: Dosyanın mutlak yolu (Forward slash ile)
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller ile çalışıyor (Tek dosya veya Klasör)
        base_path = Path(sys._MEIPASS)
    else:
        # Normal Python ile çalışıyor
        # Bu dosya: adbui/utils/resource.py
        # Proje kökü: adbui/utils/../../ -> platform-tools/
        base_path = Path(__file__).parent.parent.parent.absolute()
    
    # Yolu birleştir
    full_path = base_path / relative_path
    
    # Qt Stylesheet için forward slash kullan (Windows'ta bile)
    return str(full_path).replace("\\", "/")
