"""
Extra Features Dialog
=====================
Ekstra özellikler menüsü.
Şimdilik sadece Private DNS (Reklam Engelleyici) içerir.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

from ...core.adb_service import ADBService
import logging

logger = logging.getLogger(__name__)

class ExtraFeaturesDialog(QDialog):
    """Diğer Özellikler Penceresi."""
    
    def __init__(self, adb_service: ADBService, device_serial: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠️ Diğer Özellikler")
        self.resize(500, 300)
        
        self.adb_service = adb_service
        self.device_serial = device_serial
        
        if not self.device_serial:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir cihaz seçin.")
            self.close()
            return
            
        self._setup_ui()
        self._refresh_status()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # --- DNS AdBlock Section ---
        dns_group = QGroupBox("🚫 Reklam Engelleyici (Private DNS)")
        dns_layout = QVBoxLayout(dns_group)
        
        # Açıklama
        desc = QLabel(
            "Sistem genelinde reklamları engellemek için Android'in Private DNS özelliğini kullanır.\n"
            "Bu özellik trafiğinizi <b>dns.adguard-dns.com</b> üzerinden geçirerek reklamları filtrefeler.\n"
            "<i>(Android 9 ve üzeri gerektirir)</i>"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #a0a0a0; margin-bottom: 10px;")
        dns_layout.addWidget(desc)
        
        # Durum Göstergesi
        status_container = QHBoxLayout()
        status_label = QLabel("Şu anki Durum:")
        status_label.setStyleSheet("font-weight: bold;")
        self.dns_status_text = QLabel("Yükleniyor...")
        status_container.addWidget(status_label)
        status_container.addWidget(self.dns_status_text)
        status_container.addStretch()
        dns_layout.addLayout(status_container)
        
        # Butonlar
        btn_layout = QHBoxLayout()
        
        self.enable_dns_btn = QPushButton("✅ Etkinleştir (AdGuard)")
        self.enable_dns_btn.setToolTip("dns.adguard-dns.com sunucusunu ayarlar.")
        self.enable_dns_btn.clicked.connect(self._enable_adblock)
        btn_layout.addWidget(self.enable_dns_btn)
        
        self.disable_dns_btn = QPushButton("❌ Devre Dışı Bırak")
        self.disable_dns_btn.setToolTip("Private DNS özelliğini kapatır.")
        self.disable_dns_btn.clicked.connect(self._disable_dns)
        btn_layout.addWidget(self.disable_dns_btn)
        
        dns_layout.addLayout(btn_layout)
        layout.addWidget(dns_group)
        
        layout.addStretch()
        
        # Kapat Butonu
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignRight)

    def _refresh_status(self):
        """Mevcut DNS durumunu kontrol et."""
        try:
            status = self.adb_service.get_private_dns(self.device_serial)
            mode = status.get('mode', 'unknown')
            hostname = status.get('hostname', '')
            
            if mode == 'hostname' and 'adguard' in hostname:
                self.dns_status_text.setText(f"✅ Aktif ({hostname})")
                self.dns_status_text.setStyleSheet("color: #4cd964; font-weight: bold;")
            elif mode == 'off':
                self.dns_status_text.setText("❌ Kapalı")
                self.dns_status_text.setStyleSheet("color: #ff3b30; font-weight: bold;")
            else:
                self.dns_status_text.setText(f"⚠️ {mode} ({hostname})")
                self.dns_status_text.setStyleSheet("color: #ffcc00; font-weight: bold;")
                
        except Exception as e:
            self.dns_status_text.setText("Hata oluştu")
            logger.error(f"DNS durumu alınamadı: {e}")

    def _enable_adblock(self):
        """AdGuard DNS'i aktif et."""
        try:
            success = self.adb_service.set_private_dns(self.device_serial, "dns.adguard-dns.com")
            if success:
                QMessageBox.information(self, "Başarılı", "Reklam engelleyici aktif edildi!\nEtkisini görmek için Wifi/Mobil veriyi kapatıp açmanız gerekebilir.")
                self._refresh_status()
            else:
                QMessageBox.critical(self, "Hata", "DNS ayarlanamadı. Cihazın Android 9+ olduğundan emin olun.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İşlem başarısız: {e}")

    def _disable_dns(self):
        """DNS'i kapat."""
        try:
            success = self.adb_service.disable_private_dns(self.device_serial)
            if success:
                QMessageBox.information(self, "Başarılı", "Private DNS kapatıldı.")
                self._refresh_status()
            else:
                QMessageBox.critical(self, "Hata", "DNS kapatılamadı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İşlem başarısız: {e}")
