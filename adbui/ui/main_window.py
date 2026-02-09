"""
Main Window
===========
ADBUI ana penceresi - 3 panelli modern UI.
"""

import sys
from typing import Optional, List
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QToolBar, QStatusBar, QComboBox,
    QPushButton, QLabel, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QTimer
from PySide6.QtGui import QAction, QIcon
import logging

from .widgets.package_list import PackageListWidget
from .widgets.package_details import PackageDetailsWidget
from .widgets.ai_panel import AIPanelWidget
from .widgets.log_panel import LogPanelWidget
from .dialogs.settings_dialog import SettingsDialog

from ..core.adb_service import ADBService
from ..core.device_manager import DeviceManager, Device
from ..core.package_manager import PackageManager, Package
from ..ai.analyzer import PackageAnalyzer
from ..ai.cache import AICache
from ..utils.config import get_config
from ..utils.logger import log_emitter

logger = logging.getLogger(__name__)


class PackageLoaderThread(QThread):
    """Paketleri arka planda yükleyen thread."""
    
    packages_loaded = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, package_manager: PackageManager):
        super().__init__()
        self.package_manager = package_manager
    
    def run(self):
        try:
            packages = self.package_manager.get_all_packages()
            self.packages_loaded.emit(packages)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    """
    ADBUI Ana Penceresi.
    
    3 panelli düzen:
    - Sol: Paket listesi
    - Orta: Paket detayları
    - Sağ: AI önerisi
    - Alt: Log paneli
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("ADBUI - Android Debloat ve Kontrol Aracı")
        self.setMinimumSize(1200, 800)
        
        # Thread referansları
        self._loader_thread: Optional[PackageLoaderThread] = None
        self._device_timer = QTimer(self)
        self._device_timer.timeout.connect(self._check_devices_periodically)
        
        # Servisleri başlat
        self._init_services()
        
        # UI oluştur
        self._setup_ui()
        self._setup_toolbar()
        self._setup_statusbar()
        self._load_stylesheet()
        
        # Log emitter'a bağlan
        log_emitter.connect(self._on_log_message)
        
        # Cihazları yükle ve izlemeye başla
        self._refresh_devices()
        
        # Otomatik algılama aktifse timer'ı başlat
        if get_config().get('auto_detect_device', True):
            self._device_timer.start(2000)  # 2 saniyede bir kontrol et
    
    def _init_services(self):
        """Servisleri başlat."""
        config = get_config()
        
        try:
            self.adb_service = ADBService()
            self.device_manager = DeviceManager(self.adb_service)
            self.package_manager = PackageManager(self.adb_service)
            
            # AI servisi
            cache = AICache() if config.get('cache_enabled') else None
            self.ai_analyzer = PackageAnalyzer(
                api_key=config.get('openai_api_key'),
                cache_manager=cache
            )
            
            self._current_device: Optional[Device] = None
            self._packages: List[Package] = []
            self._selected_package: Optional[Package] = None
            
        except FileNotFoundError as e:
            QMessageBox.critical(
                self,
                "ADB Bulunamadı",
                f"adb.exe dosyası bulunamadı.\n\n"
                f"Lütfen uygulamayı platform-tools klasöründen çalıştırın.\n\n"
                f"Hata: {e}"
            )
            sys.exit(1)
    
    def _setup_ui(self):
        """Ana UI yapısını oluştur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Ana splitter (dikey - üst/alt)
        main_splitter = QSplitter(Qt.Vertical)
        
        # Üst bölüm splitter (yatay - sol/orta/sağ)
        top_splitter = QSplitter(Qt.Horizontal)
        
        # Sol panel - Paket listesi
        self.package_list = PackageListWidget()
        self.package_list.package_selected.connect(self._on_package_selected)
        top_splitter.addWidget(self.package_list)
        
        # Orta panel - Paket detayları
        self.package_details = PackageDetailsWidget()
        self.package_details.action_requested.connect(self._on_action_requested)
        top_splitter.addWidget(self.package_details)
        
        # Sağ panel - AI önerisi
        self.ai_panel = AIPanelWidget()
        top_splitter.addWidget(self.ai_panel)
        
        # Splitter oranları
        top_splitter.setSizes([300, 500, 400])
        
        main_splitter.addWidget(top_splitter)
        
        # Alt panel - Log
        self.log_panel = LogPanelWidget()
        main_splitter.addWidget(self.log_panel)
        
        # Ana splitter oranları
        main_splitter.setSizes([600, 200])
        
        main_layout.addWidget(main_splitter)
    
    def _setup_toolbar(self):
        """Toolbar oluştur."""
        toolbar = QToolBar("Ana Araç Çubuğu")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Cihaz seçici
        toolbar.addWidget(QLabel("  Cihaz: "))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(250)
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        toolbar.addWidget(self.device_combo)
        
        toolbar.addSeparator()
        
        # Yenile butonu
        refresh_action = QAction("🔄 Cihazları Yenile", self)
        refresh_action.setToolTip("Cihaz listesini yenile")
        refresh_action.triggered.connect(self._refresh_devices)
        toolbar.addAction(refresh_action)
        
        # Paketleri Yükle butonu
        self.load_packages_btn = QPushButton("📦 Uygulamaları Göster")
        self.load_packages_btn.setToolTip("Seçili cihazdaki uygulamaları listele")
        self.load_packages_btn.clicked.connect(self._refresh_packages)
        self.load_packages_btn.setEnabled(False)  # Cihaz seçilene kadar devre dışı
        toolbar.addWidget(self.load_packages_btn)
        
        toolbar.addSeparator()
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(
            spacer.sizePolicy().horizontalPolicy(),
            spacer.sizePolicy().verticalPolicy()
        )
        spacer.setMinimumWidth(20)
        toolbar.addWidget(spacer)
        
        # Ayarlar
        settings_action = QAction("⚙️ Ayarlar", self)
        settings_action.triggered.connect(self._show_settings)
        toolbar.addAction(settings_action)
    
    def _setup_statusbar(self):
        """Durum çubuğu oluştur."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.status_label = QLabel("Hazır")
        self.statusbar.addWidget(self.status_label)
        
        self.package_count_label = QLabel("")
        self.statusbar.addPermanentWidget(self.package_count_label)
    
    def _load_stylesheet(self):
        """Koyu tema stilini yükle."""
        style = """
        QMainWindow {
            background-color: #1a1a2e;
        }
        
        QWidget {
            background-color: #16213e;
            color: #e8e8e8;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        
        QToolBar {
            background-color: #0f0f23;
            border: none;
            padding: 8px;
            spacing: 10px;
        }
        
        QToolBar QLabel {
            color: #a0a0a0;
        }
        
        QPushButton {
            background-color: #4a4e69;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #6c757d;
        }
        
        QPushButton:pressed {
            background-color: #545b62;
        }
        
        QPushButton:disabled {
            background-color: #3d3d3d;
            color: #6c6c6c;
        }
        
        QPushButton#dangerButton {
            background-color: #dc3545;
        }
        
        QPushButton#dangerButton:hover {
            background-color: #c82333;
        }
        
        QPushButton#successButton {
            background-color: #28a745;
        }
        
        QPushButton#successButton:hover {
            background-color: #218838;
        }
        
        QPushButton#warningButton {
            background-color: #ffc107;
            color: #212529;
        }
        
        QComboBox {
            background-color: #2d2d44;
            border: 1px solid #4a4e69;
            border-radius: 6px;
            padding: 6px 12px;
            min-width: 150px;
        }
        
        QComboBox:hover {
            border-color: #6c757d;
        }
        
        QComboBox::drop-down {
            border: none;
            padding-right: 10px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #2d2d44;
            border: 1px solid #4a4e69;
            selection-background-color: #4a4e69;
        }
        
        QLineEdit {
            background-color: #2d2d44;
            border: 1px solid #4a4e69;
            border-radius: 6px;
            padding: 8px 12px;
        }
        
        QLineEdit:focus {
            border-color: #667eea;
        }
        
        QListWidget {
            background-color: #1a1a2e;
            border: 1px solid #2d2d44;
            border-radius: 8px;
            padding: 4px;
        }
        
        QListWidget::item {
            padding: 8px 12px;
            border-radius: 4px;
            margin: 2px 0;
        }
        
        QListWidget::item:selected {
            background-color: #4a4e69;
        }
        
        QListWidget::item:hover {
            background-color: #2d2d44;
        }
        
        QTextEdit {
            background-color: #0f0f23;
            border: 1px solid #2d2d44;
            border-radius: 8px;
            padding: 8px;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        
        QGroupBox {
            border: 1px solid #2d2d44;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: bold;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
        }
        
        QSplitter::handle {
            background-color: #2d2d44;
        }
        
        QSplitter::handle:horizontal {
            width: 2px;
        }
        
        QSplitter::handle:vertical {
            height: 2px;
        }
        
        QStatusBar {
            background-color: #0f0f23;
            color: #a0a0a0;
        }
        
        QScrollBar:vertical {
            background-color: #1a1a2e;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #4a4e69;
            border-radius: 6px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #6c757d;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        
        QCheckBox {
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid #4a4e69;
        }
        
        QCheckBox::indicator:checked {
            background-color: #667eea;
            border-color: #667eea;
        }
        """
        
        self.setStyleSheet(style)
    
    def _refresh_devices(self):
        """Cihaz listesini yenile."""
        # Önce mevcut seçimi kaydet
        old_serial = self._current_device.serial if self._current_device else None
        
        self.device_combo.clear()
        devices = self.device_manager.get_devices()
        
        if not devices:
            self.device_combo.addItem("Cihaz bulunamadı", None)
            self.status_label.setText("Cihaz bağlı değil")
            self.load_packages_btn.setEnabled(False)
            self._clear_packages()  # Paketleri temizle
            return
        
        # Cihazları combo'ya ekle
        selected_index = 0
        for i, device in enumerate(devices):
            if device.is_ready:
                self.device_combo.addItem(device.display_name, device)
                if device.serial == old_serial:
                    selected_index = i
            else:
                status_text = ""
                if device.status.value == "unauthorized":
                    status_text = " ⚠️ (Yetkilendirilmemiş)"
                else:
                    status_text = f" ({device.status.value})"
                self.device_combo.addItem(
                    f"{device.display_name}{status_text}",
                    device
                )
        
        # Eğer önceki cihaz hala varsa onu seç, yoksa ilkini seç
        self.device_combo.setCurrentIndex(selected_index)
    
    def _clear_packages(self):
        """Paket listesini temizle."""
        self._packages = []
        self.package_list.set_packages([])
        self.package_details.clear()
        self.ai_panel.clear()
        self.package_count_label.setText("")
        self._selected_package = None
    
    def _refresh_packages(self):
        """Paket listesini yenile."""
        if not self._current_device:
            return
        
        self.status_label.setText("Paketler yükleniyor...")
        self.package_manager.set_device(self._current_device.serial)
        
        # Varsaki thread çalışıyorsa durdur
        if self._loader_thread is not None:
            if self._loader_thread.isRunning():
                self._loader_thread.terminate()  # Zorla durdur
                self._loader_thread.wait()       # Bitmesini bekle
            self._loader_thread = None           # Referansı temizle
        
        # Thread ile yükle
        self._loader_thread = PackageLoaderThread(self.package_manager)
        self._loader_thread.packages_loaded.connect(self._on_packages_loaded)
        self._loader_thread.error_occurred.connect(self._on_load_error)
        # deleteLater KULLANMA! Python tarafında referans kalıyor, C++ siliyor -> Crash.
        # self._loader_thread.finished.connect(self._loader_thread.deleteLater)
        self._loader_thread.start()
        
    def _check_devices_periodically(self):
        """Periyodik olarak cihazları kontrol et."""
        # Eğer dropdown açık değilse güncelle (kullanıcı seçim yaparken engelleme)
        if not self.device_combo.view().isVisible():
             # Sadece sayı veya durum değiştiyse tam yenileme yap
             # Şimdilik basitçe her seferinde kontrol ediyoruz
             # İleride optimizasyon yapılabilir
             
             # Mevcut cihaz listesini al
             current_devices = self.device_manager.get_devices()
             
             # Combobox'taki cihaz sayısıyla karşılaştır
             # (Tam doğru değil ama pratik bir kontrol)
             # "Cihaz bulunamadı" maddesi varsa count 1 olur ama data None'dır
             combo_count = self.device_combo.count()
             combo_has_none = False
             if combo_count > 0 and self.device_combo.itemData(0) is None:
                 combo_has_none = True
                 
             real_device_count = 0 if combo_has_none else combo_count
             
             # Değişiklik varsa yenile
             if len(current_devices) != real_device_count:
                 logger.debug("Cihaz değişikliği algılandı, yenileniyor...")
                 self._refresh_devices()
             else:
                 # Sayı aynı olsa bile seri numaraları veya durumları değişmiş olabilir
                 # Basitlik için şimdilik sadece sayıya bakıyoruz
                 # Veya mevcut seçili cihazın durumu değişti mi?
                 if self._current_device:
                     for d in current_devices:
                         if d.serial == self._current_device.serial and d.status != self._current_device.status:
                             logger.info(f"Cihaz durumu değişti: {d.status.value}")
                             self._refresh_devices()
                             break
    
    def _refresh_all(self):
        """Tüm verileri yenile."""
        self._refresh_devices()
        if self._current_device:
            self._refresh_packages()
    
    @Slot(int)
    def _on_device_changed(self, index: int):
        """Cihaz seçimi değişti."""
        device = self.device_combo.currentData()
        
        if device and device.is_ready:
            self._current_device = device
            self.device_manager.current_device = device
            self.status_label.setText(f"Bağlı: {device.display_name}")
            self.load_packages_btn.setEnabled(True)
            logger.info(f"Cihaz seçildi: {device.display_name}")
            
            # Cihaz değiştiyse paketleri temizle (karışıklığı önle)
            self._clear_packages()
        else:
            self._current_device = None
            self.load_packages_btn.setEnabled(False)
            self._clear_packages()  # Paketleri temizle
            
            if device and not device.is_ready:
                QMessageBox.warning(
                    self,
                    "Cihaz Hazır Değil",
                    f"Seçilen cihaz kullanılamıyor.\n\n"
                    f"Durum: {device.status.value}\n\n"
                    f"Lütfen cihazınızda USB hata ayıklamayı etkinleştirin "
                    f"ve bu bilgisayarı yetkilendirin."
                )
    
    @Slot(list)
    def _on_packages_loaded(self, packages: List[Package]):
        """Paketler yüklendi."""
        self._packages = packages
        self.package_list.set_packages(packages)
        
        count = len(packages)
        self.package_count_label.setText(f"{count} paket")
        self.status_label.setText("Hazır")
        
        logger.info(f"{count} paket yüklendi")
    
    @Slot(str)
    def _on_load_error(self, error: str):
        """Yükleme hatası."""
        self.status_label.setText("Hata!")
        logger.error(f"Paket yükleme hatası: {error}")
        QMessageBox.critical(self, "Hata", f"Paketler yüklenemedi:\n{error}")
    
    @Slot(object)
    def _on_package_selected(self, package: Package):
        """Paket seçildi."""
        self._selected_package = package
        self.package_details.set_package(package)
        
        # AI analizi başlat
        if self.ai_analyzer.is_available:
            self.ai_panel.set_loading(True)
            analysis = self.ai_analyzer.analyze(package.name)
            self.ai_panel.set_analysis(analysis)
        else:
            self.ai_panel.set_unavailable()
    
    @Slot(str, object)
    def _on_action_requested(self, action: str, package: Package):
        """Paket işlemi istendi."""
        if not package:
            return
        
        if action == "uninstall":
            self._confirm_and_uninstall(package)
        elif action == "disable":
            self._disable_package(package)
        elif action == "enable":
            self._enable_package(package)
        elif action.startswith("appops:"):
            parts = action.split(":")
            if len(parts) == 3:
                self._set_appops(package, parts[1], parts[2])
        elif action.startswith("bucket:"):
            bucket = action.split(":")[1]
            self._set_standby_bucket(package, bucket)
    
    def _confirm_and_uninstall(self, package: Package):
        """Onay al ve kaldır."""
        if package.is_critical:
            QMessageBox.warning(
                self,
                "Kritik Paket",
                f"'{package.name}' kritik bir sistem paketidir.\n\n"
                f"Bu paketi kaldırmak cihazınızın çalışmasını engelleyebilir.\n"
                f"İşlem iptal edildi."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Onay",
            f"'{package.name}' paketini kaldırmak istediğinize emin misiniz?\n\n"
            f"Bu işlem kullanıcı 0 için paketi kaldıracaktır.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.package_manager.uninstall(package.name)
            if success:
                logger.info(f"Paket kaldırıldı: {package.name}")
                self._refresh_packages()
            else:
                QMessageBox.critical(
                    self,
                    "Hata",
                    f"Paket kaldırılamadı: {package.name}"
                )
    
    def _disable_package(self, package: Package):
        """Paketi dondur."""
        success = self.package_manager.disable(package.name)
        if success:
            logger.info(f"Paket donduruldu: {package.name}")
            self._refresh_packages()
        else:
            QMessageBox.critical(self, "Hata", "Paket dondurulamadı")
    
    def _enable_package(self, package: Package):
        """Paketi etkinleştir."""
        success = self.package_manager.enable(package.name)
        if success:
            logger.info(f"Paket etkinleştirildi: {package.name}")
            self._refresh_packages()
        else:
            QMessageBox.critical(self, "Hata", "Paket etkinleştirilemedi")
    
    def _set_appops(self, package: Package, operation: str, mode: str):
        """AppOps ayarla."""
        success = self.package_manager.set_appops(package.name, operation, mode)
        if success:
            logger.info(f"AppOps ayarlandı: {package.name} {operation}={mode}")
    
    def _set_standby_bucket(self, package: Package, bucket: str):
        """Standby bucket ayarla."""
        from ..core.package_manager import StandbyBucket
        try:
            bucket_enum = StandbyBucket(bucket)
            success = self.package_manager.set_standby_bucket(package.name, bucket_enum)
            if success:
                logger.info(f"Standby bucket ayarlandı: {package.name} -> {bucket}")
        except ValueError:
            logger.error(f"Geçersiz bucket: {bucket}")
    
    def _show_settings(self):
        """Ayarlar dialogunu göster."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Ayarlar değiştiyse AI'ı güncelle
            config = get_config()
            self.ai_analyzer.set_api_key(config.get('openai_api_key'))
    
    def _on_log_message(self, message: str, level: str):
        """Log mesajı geldi."""
        self.log_panel.append_log(message, level)
    
    def closeEvent(self, event):
        """Pencere kapatılıyor."""
        logger.info("Uygulama kapatılıyor")
        
        # Timer'ı durdur
        if self._device_timer.isActive():
            self._device_timer.stop()
        
        # Thread'i temizle (C++ objesi silinmiş olabilir)
        try:
            if self._loader_thread is not None and self._loader_thread.isRunning():
                self._loader_thread.quit()
                self._loader_thread.wait(1000)
                if self._loader_thread.isRunning():
                    self._loader_thread.terminate()
        except RuntimeError:
            pass  # C++ object already deleted
        
        event.accept()
