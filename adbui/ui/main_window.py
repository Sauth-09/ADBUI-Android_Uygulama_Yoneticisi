"""
Main Window
===========
ADBUI ana penceresi - 3 panelli modern UI.
"""

import sys
import threading
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
from .dialogs.permissions_dialog import PermissionsDialog

from ..core.adb_service import ADBService
from ..core.device_manager import DeviceManager, Device
from ..core.package_manager import PackageManager, Package, PackageCategory
from ..ai.analyzer import PackageAnalyzer
from ..ai.cache import AICache
from ..ai.background_analyzer import BackgroundAnalyzerThread
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
    
    refresh_finished = Signal(object)
    advanced_info_loaded = Signal(dict)
    log_received = Signal(str, str)  # Thread-safe log sinyali
    
    def __init__(self):
        super().__init__()
        
        # Sinyal bağlantıları
        self.refresh_finished.connect(self._on_ai_refresh_done)
        
        self.setWindowTitle("ADBUI - Android Debloat ve Kontrol Aracı")
        self.setMinimumSize(1000, 700) # 1366x768 ekranlar için optimize edildi
        
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
        
        # Sinyal bağlantıları (UI Bileşenleri oluşturulduktan sonra)
        self.advanced_info_loaded.connect(self.package_details.update_advanced_info)
        
        # Log sistemini bağla (Thread-Safe)
        self._init_logging_signals()
        
        # Cihazları yükle ve izlemeye başla
        self._refresh_devices()
        
        # Otomatik algılama aktifse timer'ı başlat
        if get_config().get('auto_detect_device', True):
            self._device_timer.start(2000)  # 2 saniyede bir kontrol et
    
    def _init_logging_signals(self):
        """Log sinyallerini bağla (Thread-Safe UI Updates)."""
        # Log emitter'dan gelen sinyali yakala
        log_emitter.connect(self.log_received.emit)
        
        # Sinyali slot'a bağla (Otomatik QueuedConnection)
        self.log_received.connect(self._on_log_message)

    def _init_services(self):
        """Servisleri başlat."""
        config = get_config()
        
        try:
            self.adb_service = ADBService()
            self.device_manager = DeviceManager(self.adb_service)
            self.package_manager = PackageManager(self.adb_service)
            
            # AI servisi
            self.ai_cache = AICache() if config.get('cache_enabled', True) else AICache()  # Her zaman cache kullan
            self.ai_analyzer = PackageAnalyzer(
                api_key=config.get('openai_api_key'),
                cache_manager=self.ai_cache
            )
            
            self._current_device: Optional[Device] = None
            self._packages: List[Package] = []
            self._selected_package: Optional[Package] = None
            self._background_analyzer: Optional[BackgroundAnalyzerThread] = None
            
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
        self.ai_panel.refresh_requested.connect(self._force_ai_refresh)
        top_splitter.addWidget(self.ai_panel)
        
        # Splitter oranları
        top_splitter.setSizes([280, 420, 300])
        
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
            background-color: transparent;
            border: 2px solid #667eea;
            image: url(adbui/assets/check.svg);
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
        
        # Arka planda AI analizini başlat
        self._start_background_analysis(packages)
    
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
        self.ai_panel.current_package = package.name
        
        # Gelişmiş detayları arka planda yükle
        self.package_details.update_advanced_info({}) # Temizle
        
        def load_details():
            try:
                if self.package_manager:
                    details = self.package_manager.get_advanced_details(package.name)
                    self.advanced_info_loaded.emit(details)
            except Exception as e:
                logger.error(f"Detay yükleme hatası: {e}")
        
        threading.Thread(target=load_details, daemon=True).start()
        
        # Önce cache'e bak
        if self.ai_cache:
            cached_analysis = self.ai_cache.get(package.name)
            if cached_analysis:
                # Cache'den direkt göster (hızlı!)
                self.ai_panel.set_analysis(cached_analysis)
                return
        
        # Cache'de yok, AI analizi başlat (arka plan işlemi devam ediyorsa bekleyecek)
        # Cache'de yok, AI analizi başlat (arka plan işlemi devam ediyorsa bekleyecek)
        if self.ai_analyzer.is_available:
            self.ai_panel.set_loading(True)
            
            # Asenkron çağrı (Thread ile) - UI donmasını önler
            def run():
                try:
                    analysis = self.ai_analyzer.analyze(package.name)
                    self.refresh_finished.emit(analysis)
                except Exception as e:
                    logger.error(f"Manuel analiz hatası: {e}")
                    self.refresh_finished.emit(None)
            
            threading.Thread(target=run, daemon=True).start()
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
        elif action == "permissions":
            self._show_permissions_dialog(package)
        elif action.startswith("appops:"):
            parts = action.split(":")
            if len(parts) == 3:
                self._set_appops(package, parts[1], parts[2])
        elif action.startswith("bucket:"):
            bucket = action.split(":")[1]
            self._set_standby_bucket(package, bucket)
    
    def _confirm_and_uninstall(self, package: Package):
        """Onay al ve kaldır."""
        if package.is_critical and package.category == PackageCategory.SYSTEM:
            QMessageBox.warning(
                self,
                "Kritik Paket",
                f"'{package.name}' kritik bir sistem paketidir.\n\n"
                f"Bu paketi kaldırmak cihazınızın çalışmasını engelleyebilir.\n"
                f"İşlem iptal edildi."
            )
            return

        # Mesaj içeriği (Sistem ve Kullanıcı ayrımı)
        title = "Kaldırma Onayı"
        if package.category == PackageCategory.SYSTEM:
            msg = (
                f"'{package.name}' sistem paketini kaldırmak istediğinize emin misiniz?\n\n"
                f"Bu işlem paketi 'User 0' (ana kullanıcı) için kaldıracaktır.\n"
                f"Sistem dosyası silinmez (root olmadan silinemez).\n\n"
                f"Geri yüklemek için:\n"
                f"pm install-existing {package.name}"
            )
        else:
             # Kullanıcı uygulaması
            msg = (
                f"'{package.name}' uygulamasını KALDIRMAK istediğinize emin misiniz?\n\n"
                f"Bu işlem uygulamayı ve tüm verilerini cihazdan TAMAMEN SİLECEKTİR.\n"
                f"(Geri yüklemek için Play Store veya APK ile tekrar kurmanız gerekir.)"
            )
        
        reply = QMessageBox.question(
            self,
            title,
            msg,
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
            self._refresh_packages()
        else:
            QMessageBox.critical(self, "Hata", "Paket dondurulamadı")
    
    def _enable_package(self, package: Package):
        """Paketi etkinleştir."""
        success = self.package_manager.enable(package.name)
        if success:
            self._refresh_packages()
        else:
            QMessageBox.critical(self, "Hata", "Paket etkinleştirilemedi")
    
    def _set_appops(self, package: Package, operation: str, mode: str):
        """AppOps ayarla."""
        self.package_manager.set_appops(package.name, operation, mode)
    
    def _set_standby_bucket(self, package: Package, bucket: str):
        """Standby bucket ayarla."""
        from ..core.package_manager import StandbyBucket
        try:
            bucket_enum = StandbyBucket(bucket)
            self.package_manager.set_standby_bucket(package.name, bucket_enum)
        except ValueError:
            logger.error(f"Geçersiz bucket: {bucket}")
    
    def _show_settings(self):
        """Ayarlar dialogunu göster."""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Ayarlar değiştiyse AI'ı güncelle
            config = get_config()
            self.ai_analyzer.set_api_key(config.get('openai_api_key'))
    def _show_permissions_dialog(self, package: Package):
        """İzinler dialogunu göster."""
        dialog = PermissionsDialog(self.package_manager, package.name, self)
        dialog.exec()
    
    def _on_log_message(self, message: str, level: str):
        """Log mesajı geldi."""
        self.log_panel.append_log(message, level)
    
    # ===== ARKA PLAN ANALİZİ =====
    
    def _start_background_analysis(self, packages: List[Package]):
        """Arka planda AI analizini başlat."""
        if not self.ai_analyzer.is_available:
            logger.warning("AI analizi kullanılamıyor, arka plan analizi atlanıyor")
            return
        
        # Önceki thread varsa durdur
        if self._background_analyzer and self._background_analyzer.isRunning():
            self._background_analyzer.stop()
            self._background_analyzer.wait(2000)
        
        # Yeni thread oluştur
        self._background_analyzer = BackgroundAnalyzerThread(
            packages=packages,
            analyzer=self.ai_analyzer,
            cache=self.ai_cache,
            batch_size=20
        )
        
        # Sinyalleri bağla
        self._background_analyzer.progress_updated.connect(self._on_background_progress)
        self._background_analyzer.package_analyzed.connect(self._on_background_package_analyzed)
        self._background_analyzer.all_completed.connect(self._on_background_completed)
        self._background_analyzer.error_occurred.connect(self._on_background_error)
        
        # Başlat
        self.ai_panel.update_progress(f"AI Analizi Başlıyor... (0/{len(packages)})")
        self._background_analyzer.start()
        logger.info("Arka plan AI analizi başlatıldı")
    
    @Slot(int, int)
    def _on_background_progress(self, current: int, total: int):
        """Arka plan analizi ilerleme durumu."""
        self.ai_panel.update_progress(f"AI Analizi: {current}/{total}")
        # self.status_label.setText(f"AI Analizi: {current}/{total}") # Artık gerek yok
    
    @Slot(str, object)
    def _on_background_package_analyzed(self, package_name: str, analysis):
        """Bir paket arka planda analiz edildi."""
        # Eğer şu an bu paket seçiliyse, paneli güncelle
        if self._selected_package and self._selected_package.name == package_name:
            self.ai_panel.set_analysis(analysis)
    
    @Slot(int)
    def _on_background_completed(self, total_analyzed: int):
        """Arka plan analizi tamamlandı."""
        self.status_label.setText("Hazır")
        self.ai_panel.update_progress("AI: Tamamlandı ✅")
        
        # 5 saniye sonra AI label'ı temizle (istenirse)
        # QTimer.singleShot(5000, lambda: self.ai_panel.update_progress(""))
        
        logger.info(f"Arka plan AI analizi tamamlandı: {total_analyzed} paket analiz edildi")
    
    @Slot(str)
    def _on_background_error(self, error: str):
        """Arka plan analiz hatası."""
        logger.error(f"Arka plan analiz hatası: {error}")
        
        if "Kota" in error or "RESOURCE_EXHAUSTED" in str(error):
            self.status_label.setText("🛑 AI Analizi Durduruldu (Kota)")
            self.ai_panel.update_progress("⚠️ AI Kotası Doldu", is_error=True)
        else:
            self.status_label.setText(f"AI Hatası")
            self.ai_panel.update_progress(f"AI Hatası: {str(error)[:20]}...", is_error=True)
    
    @Slot(str)
    def _force_ai_refresh(self, package_name: str):
        """AI analizini zorla yenile."""
        logger.info(f"AI analizi yenileniyor: {package_name}")
        self.ai_panel.set_loading(True)
        
        # Cache'den sil
        if self.ai_cache:
            self.ai_cache.delete(package_name)
            
        def run():
            if self.ai_analyzer:
                # Cache silindiği için API'ye gidecek
                try:
                    analysis = self.ai_analyzer.analyze(package_name)
                    self.refresh_finished.emit(analysis)
                except Exception as e:
                    logger.error(f"Yenileme hatası: {e}")
                    self.refresh_finished.emit(None)
                
        threading.Thread(target=run, daemon=True).start()

    @Slot(object)
    def _on_ai_refresh_done(self, analysis):
        """Yenileme tamamlandı."""
        self.ai_panel.set_analysis(analysis)
    
    def closeEvent(self, event):
        """Pencere kapatılıyor."""
        logger.info("Uygulama kapatılıyor")
        
        # Timer'ı durdur
        if self._device_timer.isActive():
            self._device_timer.stop()
        
        # Background analyzer'ı durdur
        try:
            if self._background_analyzer and self._background_analyzer.isRunning():
                self._background_analyzer.stop()
                self._background_analyzer.wait(2000)
        except RuntimeError:
            pass
        
        # Loader thread'i temizle (C++ objesi silinmiş olabilir)
        try:
            if self._loader_thread is not None and self._loader_thread.isRunning():
                self._loader_thread.quit()
                self._loader_thread.wait(1000)
                if self._loader_thread.isRunning():
                    self._loader_thread.terminate()
        except RuntimeError:
            pass  # C++ object already deleted
        
        event.accept()
