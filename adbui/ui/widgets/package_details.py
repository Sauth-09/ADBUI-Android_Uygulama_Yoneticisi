"""
Package Details Widget
======================
Orta panel - Paket detayları ve işlem butonları.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QComboBox, QFrame,
    QGridLayout
)
from PySide6.QtCore import Signal
import logging

from ...core.package_manager import Package, PackageCategory

logger = logging.getLogger(__name__)


class PackageDetailsWidget(QWidget):
    """
    Paket detayları widget'ı.
    
    Seçili paketin bilgilerini ve işlem butonlarını gösterir.
    """
    
    action_requested = Signal(str, object)  # action, package
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._current_package: Optional[Package] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Başlık
        title = QLabel("📋 Paket Detayları")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px;")
        layout.addWidget(title)
        
        # Paket bilgi alanı
        self.info_group = QGroupBox("Bilgiler")
        info_layout = QGridLayout(self.info_group)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setVerticalSpacing(4)
        info_layout.setHorizontalSpacing(8)
        
        # Paket adı
        info_layout.addWidget(QLabel("Paket:"), 0, 0)
        self.name_label = QLabel("-")
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("font-weight: bold; color: #667eea;")
        info_layout.addWidget(self.name_label, 0, 1)
        
        # Kategori
        info_layout.addWidget(QLabel("Kategori:"), 1, 0)
        self.category_label = QLabel("-")
        info_layout.addWidget(self.category_label, 1, 1)
        
        # Durum
        info_layout.addWidget(QLabel("Durum:"), 2, 0)
        self.status_label = QLabel("-")
        info_layout.addWidget(self.status_label, 2, 1)
        
        # Üretici
        info_layout.addWidget(QLabel("Üretici:"), 3, 0)
        self.vendor_label = QLabel("-")
        info_layout.addWidget(self.vendor_label, 3, 1)
        
        layout.addWidget(self.info_group)
        
        # İşlem butonları
        actions_group = QGroupBox("İşlemler")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setContentsMargins(8, 12, 8, 12)
        actions_layout.setSpacing(8)
        
        # Ana işlemler
        main_actions = QHBoxLayout()
        main_actions.setSpacing(8)
        
        self.uninstall_btn = QPushButton("🗑️ Kaldır")
        self.uninstall_btn.setObjectName("dangerButton")
        self.uninstall_btn.clicked.connect(self._on_uninstall)
        main_actions.addWidget(self.uninstall_btn)
        
        self.freeze_btn = QPushButton("❄️ Dondur")
        self.freeze_btn.setObjectName("warningButton")
        self.freeze_btn.clicked.connect(self._on_freeze)
        main_actions.addWidget(self.freeze_btn)
        
        self.enable_btn = QPushButton("✅ Etkinleştir")
        self.enable_btn.setObjectName("successButton")
        self.enable_btn.clicked.connect(self._on_enable)
        main_actions.addWidget(self.enable_btn)
        
        actions_layout.addLayout(main_actions)
        
        # Ayırıcı
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #2d2d44;")
        actions_layout.addWidget(separator)
        
        # AppOps
        appops_layout = QHBoxLayout()
        appops_layout.addWidget(QLabel("AppOps:"))
        
        self.appops_combo = QComboBox()
        self.appops_combo.addItem("Seçin...", None)
        self.appops_combo.addItem("Arka Planda Çalışma (Background) - İzin Ver", "RUN_IN_BACKGROUND:allow")
        self.appops_combo.addItem("Arka Planda Çalışma (Background) - Engelle", "RUN_IN_BACKGROUND:deny")
        self.appops_combo.addItem("Uyanık Tut (Wake Lock) - İzin Ver", "WAKE_LOCK:allow")
        self.appops_combo.addItem("Uyanık Tut (Wake Lock) - Engelle", "WAKE_LOCK:deny")
        self.appops_combo.currentIndexChanged.connect(self._on_appops_changed)
        appops_layout.addWidget(self.appops_combo)
        
        appops_layout.addStretch()
        actions_layout.addLayout(appops_layout)
        
        # Standby Bucket
        bucket_layout = QHBoxLayout()
        bucket_layout.addWidget(QLabel("Standby:"))
        
        self.bucket_combo = QComboBox()
        self.bucket_combo.addItem("Seçin...", None)
        self.bucket_combo.addItem("🟢 Active", "active")
        self.bucket_combo.addItem("🟡 Working Set", "working_set")
        self.bucket_combo.addItem("🟠 Frequent", "frequent")
        self.bucket_combo.addItem("🔴 Rare", "rare")
        self.bucket_combo.addItem("⛔ Restricted", "restricted")
        self.bucket_combo.currentIndexChanged.connect(self._on_bucket_changed)
        bucket_layout.addWidget(self.bucket_combo)
        
        bucket_layout.addStretch()
        actions_layout.addLayout(bucket_layout)
        
        layout.addWidget(actions_group)
        
        # Uyarı alanı
        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("""
            QLabel {
                background-color: #3d1f1f;
                color: #ff6b6b;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #5c3030;
            }
        """)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)
        
        layout.addStretch()
        
        # Başlangıçta butonları devre dışı bırak
        self._set_actions_enabled(False)
    
    def set_package(self, package: Optional[Package]):
        """Paketi ayarla."""
        self._current_package = package
        
        if not package:
            self._clear()
            return
        
        # Bilgileri güncelle
        self.name_label.setText(package.name)
        
        category_text = {
            PackageCategory.SYSTEM: "⚙️ Sistem",
            PackageCategory.USER: "📱 Kullanıcı",
            PackageCategory.DISABLED: "❄️ Devre Dışı",
        }.get(package.category, "❓ Bilinmiyor")
        self.category_label.setText(category_text)
        
        status_text = "✅ Aktif" if package.is_enabled else "❄️ Dondurulmuş"
        self.status_label.setText(status_text)
        
        self.vendor_label.setText(package.vendor or "-")
        
        # Butonları ayarla
        self._set_actions_enabled(True)
        
        # Kritik paket kontrolü
        if package.is_critical:
            self.uninstall_btn.setEnabled(False)
            self.warning_label.setText(
                "⚠️ Bu kritik bir sistem paketidir.\n"
                "Kaldırılması cihazınızın çalışmasını engelleyebilir."
            )
            self.warning_label.show()
        else:
            self.warning_label.hide()
        
        # Dondur/Etkinleştir butonlarını ayarla
        if package.is_enabled:
            self.freeze_btn.show()
            self.enable_btn.hide()
        else:
            self.freeze_btn.hide()
            self.enable_btn.show()
        
        # Dropdown'ları sıfırla
        self.appops_combo.setCurrentIndex(0)
        self.bucket_combo.setCurrentIndex(0)
    
    def _clear(self):
        """Alanları temizle."""
        self.name_label.setText("-")
        self.category_label.setText("-")
        self.status_label.setText("-")
        self.vendor_label.setText("-")
        self.warning_label.hide()
        self._set_actions_enabled(False)
    
    def clear(self):
        """Paket bilgilerini temizle (public)."""
        self._current_package = None
        self._clear()
    
    def _set_actions_enabled(self, enabled: bool):
        """İşlem butonlarını etkinleştir/devre dışı bırak."""
        self.uninstall_btn.setEnabled(enabled)
        self.freeze_btn.setEnabled(enabled)
        self.enable_btn.setEnabled(enabled)
        self.appops_combo.setEnabled(enabled)
        self.bucket_combo.setEnabled(enabled)
    
    def _on_uninstall(self):
        """Kaldır butonu tıklandı."""
        if self._current_package:
            self.action_requested.emit("uninstall", self._current_package)
    
    def _on_freeze(self):
        """Dondur butonu tıklandı."""
        if self._current_package:
            self.action_requested.emit("disable", self._current_package)
    
    def _on_enable(self):
        """Etkinleştir butonu tıklandı."""
        if self._current_package:
            self.action_requested.emit("enable", self._current_package)
    
    def _on_appops_changed(self, index: int):
        """AppOps seçimi değişti."""
        value = self.appops_combo.currentData()
        if value and self._current_package:
            operation, mode = value.split(":")
            self.action_requested.emit(f"appops:{operation}:{mode}", self._current_package)
            self.appops_combo.setCurrentIndex(0)
    
    def _on_bucket_changed(self, index: int):
        """Standby bucket seçimi değişti."""
        value = self.bucket_combo.currentData()
        if value and self._current_package:
            self.action_requested.emit(f"bucket:{value}", self._current_package)
            self.bucket_combo.setCurrentIndex(0)
