"""
Settings Dialog
================
Uygulama ayarları diyaloğu.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QCheckBox, QSpinBox, QComboBox,
    QTabWidget, QWidget, QLabel, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt
import logging

from pathlib import Path
from ...utils.config import get_config
from ...ai.cache import AICache

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
        
        ai_group = QGroupBox("Google Gemini API")
        ai_form = QFormLayout(ai_group)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("AIza...")
        ai_form.addRow("API Anahtarı:", self.api_key_input)
        
        # Model seçici (dropdown)
        self.model_combo = QComboBox()
        self.model_combo.addItem("gemini-2.5-flash (Önerilen)", "gemini-2.5-flash")
        self.model_combo.addItem("gemini-2.5-flash-lite (Hızlı)", "gemini-2.5-flash-lite")
        self.model_combo.addItem("gemini-flash-latest (En Güncel)", "gemini-flash-latest")
        ai_form.addRow("Model:", self.model_combo)
        
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
        
        # Bakım ve Temizlik
        maint_group = QGroupBox("Bakım ve Temizlik")
        maint_layout = QHBoxLayout(maint_group)
        
        self.clear_logs_btn = QPushButton("Logları Temizle")
        self.clear_logs_btn.setToolTip("Uygulama log dosyalarını temizler.")
        self.clear_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.clear_logs_btn.clicked.connect(self._clear_logs)
        
        self.clear_db_btn = QPushButton("Veritabanını Sıfırla")
        self.clear_db_btn.setToolTip("Tüm AI analiz geçmişini siler. Dikkat!")
        self.clear_db_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.clear_db_btn.clicked.connect(self._clear_db)
        
        maint_layout.addWidget(self.clear_logs_btn)
        
        self.open_logs_btn = QPushButton("Log Klasörünü Aç")
        self.open_logs_btn.setToolTip("Hata loglarını incelemek için klasörü açar.")
        self.open_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        self.open_logs_btn.clicked.connect(self._open_logs)
        maint_layout.addWidget(self.open_logs_btn)
        
        maint_layout.addWidget(self.clear_db_btn)
        
        ai_layout.addWidget(maint_group)
        
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
        # Model combo'da doğru modeli seç
        model_index = self.model_combo.findData(config.ai_model)
        if model_index >= 0:
            self.model_combo.setCurrentIndex(model_index)
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
        config.ai_model = self.model_combo.currentData() or "gemini-2.5-flash"
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
            
    def _clear_db(self):
        """Veritabanını temizle."""
        reply = QMessageBox.question(
            self, "Onay", 
            "Tüm AI analiz veritabanı silinecek.\nBu işlem geri alınamaz.\nDevam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Cache temizle
                cache = AICache()
                cache.clear()
                QMessageBox.information(self, "Başarılı", "Veritabanı temizlendi.")
            except Exception as e:
                logger.error(f"Veritabanı silinemedi: {e}")
                QMessageBox.critical(self, "Hata", f"Veritabanı temizlenemedi:\n{e}")
    
    
    def _clear_logs(self):
        """Log temizliği."""
        reply = QMessageBox.question(
            self, "Onay", 
            "Geçmiş log dosyaları silinecek.\n"
            "(Aktif oturumun log dosyası silinemez)\n\n"
            "Devam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                log_dir = Path.home() / ".adbui" / "logs"
                deleted_count = 0
                skipped_count = 0
                
                if log_dir.exists():
                    for log_file in log_dir.glob("*.log"):
                        try:
                            log_file.unlink()
                            deleted_count += 1
                        except PermissionError:
                             # Windows'ta açık dosyalar silinemez
                            skipped_count += 1
                        except Exception as e:
                            logger.error(f"Dosya silme hatası ({log_file}): {e}")
                            skipped_count += 1
                    
                    msg = f"{deleted_count} eski log dosyası silindi."
                    if skipped_count > 0:
                        msg += f"\n({skipped_count} aktif dosya korundu)"
                        
                    QMessageBox.information(self, "İşlem Tamamlandı", msg)
                else:
                    QMessageBox.information(self, "Bilgi", "Log klasörü bulunamadı.")
            except Exception as e:
                logger.error(f"Log temizleme hatası: {e}")
                QMessageBox.critical(self, "Hata", f"Loglar temizlenemedi:\n{e}")
                
    def _open_logs(self):
        """Log klasörünü aç."""
        try:
            log_dir = Path.home() / ".adbui" / "logs"
            if not log_dir.exists():
                log_dir.mkdir(parents=True, exist_ok=True)
                
            import os
            # Windows için klasör aç
            os.startfile(log_dir)
        except Exception as e:
            logger.error(f"Log klasörü açılamadı: {e}")
            QMessageBox.critical(self, "Hata", f"Log klasörü açılamadı:\n{e}")
