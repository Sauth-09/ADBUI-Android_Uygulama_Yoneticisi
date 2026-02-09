"""
Settings Dialog
================
Uygulama ayarları diyaloğu.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QTabWidget, QWidget, QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt
import logging

from ...utils.config import get_config

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """
    Ayarlar diyaloğu.
    
    API anahtarları, güvenlik ve UI ayarlarını yönetir.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("⚙️ Ayarlar")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        self.config = get_config()
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """UI oluştur."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Tab widget
        tabs = QTabWidget()
        
        # AI Ayarları
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        
        ai_group = QGroupBox("OpenAI API")
        ai_form = QFormLayout(ai_group)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("sk-...")
        ai_form.addRow("API Anahtarı:", self.api_key_input)
        
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("gpt-3.5-turbo")
        ai_form.addRow("Model:", self.model_input)
        
        self.ai_enabled = QCheckBox("AI özelliklerini etkinleştir")
        ai_form.addRow("", self.ai_enabled)
        
        ai_layout.addWidget(ai_group)
        
        # Cache ayarları
        cache_group = QGroupBox("Cache")
        cache_form = QFormLayout(cache_group)
        
        self.cache_enabled = QCheckBox("Cache'i etkinleştir")
        cache_form.addRow("", self.cache_enabled)
        
        self.cache_ttl = QSpinBox()
        self.cache_ttl.setRange(1, 365)
        self.cache_ttl.setSuffix(" gün")
        cache_form.addRow("Geçerlilik süresi:", self.cache_ttl)
        
        ai_layout.addWidget(cache_group)
        ai_layout.addStretch()
        
        tabs.addTab(ai_tab, "🤖 AI")
        
        # Güvenlik Ayarları
        security_tab = QWidget()
        security_layout = QVBoxLayout(security_tab)
        
        security_group = QGroupBox("Güvenlik")
        security_form = QFormLayout(security_group)
        
        self.confirm_critical = QCheckBox("Kritik işlemler için onay iste")
        security_form.addRow("", self.confirm_critical)
        
        self.show_system = QCheckBox("Sistem paketlerini göster")
        security_form.addRow("", self.show_system)
        
        self.enable_dangerous = QCheckBox("Tehlikeli işlemleri etkinleştir")
        self.enable_dangerous.setStyleSheet("color: #dc3545;")
        security_form.addRow("", self.enable_dangerous)
        
        warning = QLabel(
            "⚠️ Tehlikeli işlemler, kritik sistem paketlerinin\n"
            "kaldırılmasına izin verir. Dikkatli kullanın!"
        )
        warning.setStyleSheet("color: #ffc107; font-size: 11px;")
        security_form.addRow("", warning)
        
        security_layout.addWidget(security_group)
        
        # ADB ayarları
        adb_group = QGroupBox("ADB")
        adb_form = QFormLayout(adb_group)
        
        self.adb_path = QLineEdit()
        self.adb_path.setPlaceholderText("Otomatik tespit")
        adb_form.addRow("ADB Yolu:", self.adb_path)
        
        self.command_timeout = QSpinBox()
        self.command_timeout.setRange(5, 120)
        self.command_timeout.setSuffix(" saniye")
        adb_form.addRow("Komut timeout:", self.command_timeout)
        
        self.auto_detect = QCheckBox("Cihazları otomatik algıla")
        adb_form.addRow("", self.auto_detect)
        
        security_layout.addWidget(adb_group)
        security_layout.addStretch()
        
        tabs.addTab(security_tab, "🔒 Güvenlik")
        
        layout.addWidget(tabs)
        
        # Butonlar
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        save_btn = QPushButton("Kaydet")
        save_btn.setObjectName("successButton")
        save_btn.clicked.connect(self._save_settings)
        buttons.addWidget(save_btn)
        
        layout.addLayout(buttons)
    
    def _load_settings(self):
        """Mevcut ayarları yükle."""
        config = self.config.config
        
        self.api_key_input.setText(config.openai_api_key)
        self.model_input.setText(config.ai_model)
        self.ai_enabled.setChecked(config.ai_enabled)
        
        self.cache_enabled.setChecked(config.cache_enabled)
        self.cache_ttl.setValue(config.cache_ttl_days)
        
        self.confirm_critical.setChecked(config.confirm_critical_actions)
        self.show_system.setChecked(config.show_system_packages)
        self.enable_dangerous.setChecked(config.enable_dangerous_operations)
        
        self.adb_path.setText(config.adb_path)
        self.command_timeout.setValue(config.command_timeout)
        self.auto_detect.setChecked(config.auto_detect_device)
    
    def _save_settings(self):
        """Ayarları kaydet."""
        config = self.config.config
        
        config.openai_api_key = self.api_key_input.text().strip()
        config.ai_model = self.model_input.text().strip() or "gpt-3.5-turbo"
        config.ai_enabled = self.ai_enabled.isChecked()
        
        config.cache_enabled = self.cache_enabled.isChecked()
        config.cache_ttl_days = self.cache_ttl.value()
        
        config.confirm_critical_actions = self.confirm_critical.isChecked()
        config.show_system_packages = self.show_system.isChecked()
        config.enable_dangerous_operations = self.enable_dangerous.isChecked()
        
        config.adb_path = self.adb_path.text().strip()
        config.command_timeout = self.command_timeout.value()
        config.auto_detect_device = self.auto_detect.isChecked()
        
        if self.config.save():
            logger.info("Ayarlar kaydedildi")
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Ayarlar kaydedilemedi!")
