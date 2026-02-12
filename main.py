#!/usr/bin/env python3
"""
ADBUI - Android Debloat ve Kontrol Aracı
========================================

Ana uygulama giriş noktası.

Kullanım:
    python main.py

Gereksinimler:
    - Python 3.9+
    - PySide6
    - openai (opsiyonel, AI özellikleri için)
"""

import sys
import os
from pathlib import Path

# Proje kök dizinini path'e ekle
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from adbui.ui.main_window import MainWindow
from adbui.utils.logger import setup_logging
from adbui.utils.config import get_config


def main():
    """Uygulamayı başlat."""
    # Log sistemini başlat
    setup_logging()
    
    # Global Exception Handler (Kritik hataları yakala)
    def excepthook(exc_type, exc_value, exc_traceback):
        import logging
        logging.getLogger("root").critical(
            "Beklenmeyen Hata (Uncaught Exception):", 
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = excepthook
    
    # Konfigürasyonu yükle
    config = get_config()
    
    # High DPI desteği
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Uygulama oluştur
    app = QApplication(sys.argv)
    app.setApplicationName("ADBUI")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ADBUI")
    
    from PySide6.QtWidgets import QSplashScreen
    from PySide6.QtGui import QPixmap

    # İkonu ayarla
    icon_path = PROJECT_ROOT / "logo.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Splash Screen (Açılış Ekranı)
    splash = None
    if icon_path.exists():
        pixmap = QPixmap(str(icon_path))
        # Logoyu biraz büyüt
        pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
        splash.showMessage("Yükleniyor...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        splash.show()
        app.processEvents()

    # Font ayarla
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Ana pencereyi oluştur ve göster
    window = MainWindow()
    window.resize(
        config.get('window_width', 1400),
        config.get('window_height', 900)
    )
    window.show()
    
    if splash:
        splash.finish(window)
    
    # Uygulama döngüsü
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
