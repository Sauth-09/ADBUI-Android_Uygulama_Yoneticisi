"""
Known Apps Widget
=================
Bilinen (bloatware) uygulamaları listeleyen ve işlem yapılmasını sağlayan arayüz.
"""

from typing import List, Optional
import threading
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QBrush

from ...core.package_manager import Package
from ...core.known_apps import KnownAppsManager, KnownApp
import logging

logger = logging.getLogger(__name__)

class KnownAppsWidget(QWidget):
    """
    Bilinen uygulamalar listesi widget'ı.
    """
    
    refresh_requested = Signal()  # Listeyi yenileme isteği
    action_requested = Signal(str, str)  # action (uninstall/disable), package_name
    
    def __init__(self, manager: KnownAppsManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._installed_packages: List[Package] = []
        
        self._setup_ui()
        
        # Başlangıçta verileri yükle (yerel)
        self.manager.load_local_cache()
        self._refresh_list()
    
    def _setup_ui(self):
        """UI oluştur."""
        layout = QVBoxLayout(self)
        
        # Üst Bar
        top_layout = QHBoxLayout()
        
        self.status_label = QLabel("Durum: Hazır")
        top_layout.addWidget(self.status_label)
        
        top_layout.addStretch()
        
        self.refresh_btn = QPushButton("☁️ Listeyi Güncelle")
        self.refresh_btn.setToolTip("İnternetten güncel listeyi çek")
        self.refresh_btn.clicked.connect(self._fetch_update)
        top_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(top_layout)
        
        # Arama
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Listede ara...")
        self.search_input.textChanged.connect(self._filter_list)
        layout.addWidget(self.search_input)
        
        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Durum", "Uygulama", "Paket Adı", "Risk", "İşlem"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Uygulama adı esnek
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # Bilgi Notu
        info_label = QLabel("Not: Bu liste topluluk tarafından oluşturulmuştur. Kaldırmadan önce araştırmanız önerilir.")
        info_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(info_label)
        
    def set_installed_packages(self, packages: List[Package]):
        """Yüklü paket listesini güncelle."""
        self._installed_packages = packages
        self._refresh_list()
        
    def _fetch_update(self):
        """Listeyi güncelle (Thread ile)."""
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("Güncelleniyor...")
        
        def run():
            success = self.manager.fetch_remote_list()
            # UI thread'de sonucu işlememiz gerekmez çünkü _refresh_list
            # local cache'i veya memory'dekini okur.
            # Ancak UI güncellemesi main thread'de olmalı.
            pass # Burası sadece işi yapar, sinyalle UI güncellenmeli ama basitlik için şimdilik:
            
        # Basit threading yerine, işlem bitince manual refresh çağıracağız
        # Ama önce main_window'da thread yapısını düzgün kurmak lazım.
        # Şimdilik basic thread:
        threading.Thread(target=self._run_fetch, daemon=True).start()

    def _run_fetch(self):
        success = self.manager.fetch_remote_list()
        # UI güncellemeleri için signal kullanmalıyız ama
        # QWidget içinde custom signal tanımlayıp ona emit edebiliriz
        # ya da invokeMethod.
        # Basit çözüm (PySide6'da thread güvenliği için):
        from PySide6.QtCore import QMetaObject, Q_ARG
        QMetaObject.invokeMethod(self, "_on_fetch_finished", Qt.QueuedConnection, Q_ARG(bool, success))

    @Slot(bool)
    def _on_fetch_finished(self, success: bool):
        self.refresh_btn.setEnabled(True)
        if success:
            self.status_label.setText("Liste güncellendi.")
            self._refresh_list()
        else:
            self.status_label.setText("Güncelleme başarısız!")
            
    def _refresh_list(self):
        """Tabloyu yenile."""
        search_text = self.search_input.text().lower()
        known_apps = self.manager.get_all_apps()
        
        # Yüklü paketlerin isimlerini set yap (hızlı arama için)
        installed_map = {p.name: p for p in self._installed_packages}
        
        self.table.setRowCount(0)
        
        for app in known_apps:
            # Filtreleme
            if search_text and (search_text not in app.name.lower() and search_text not in app.package.lower()):
                continue
            
            # Yüklü mü?
            is_installed = app.package in installed_map
            package_info = installed_map.get(app.package)
            
            # Sadece yüklü olanları göster opsiyonu eklenebilir
            # Şimdilik hepsini gösteriyoruz ama yüklü olanları öne alabiliriz
            # veya işaretleyebiliriz.
            
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 1. Durum
            status_item = QTableWidgetItem()
            if is_installed:
                if package_info and not package_info.is_enabled:
                    status_item.setText("Devre Dışı")
                    status_item.setForeground(QBrush(QColor("orange")))
                else:
                    status_item.setText("Yüklü")
                    status_item.setForeground(QBrush(QColor("green")))
            else:
                status_item.setText("Yok")
                status_item.setForeground(QBrush(QColor("gray")))
            self.table.setItem(row, 0, status_item)
            
            # 2. İsim ve Açıklama
            name_item = QTableWidgetItem(f"{app.name}")
            name_item.setToolTip(app.description)
            self.table.setItem(row, 1, name_item)
            
            # 3. Paket
            pkg_item = QTableWidgetItem(app.package)
            self.table.setItem(row, 2, pkg_item)
            
            # 4. Risk
            risk_item = QTableWidgetItem(app.risk)
            if app.risk == "Safe":
                risk_item.setForeground(QBrush(QColor("green")))
            elif app.risk == "Caution":
                 risk_item.setForeground(QBrush(QColor("orange")))
            self.table.setItem(row, 3, risk_item)
            
            # 5. İşlem Butonu
            if is_installed:
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                action_btn = QPushButton(app.recommendation) # Remove / Disable
                # Stil
                if app.recommendation == "Remove":
                    action_btn.setStyleSheet("background-color: #d9534f; color: white;")
                elif app.recommendation == "Disable":
                    action_btn.setStyleSheet("background-color: #f0ad4e; color: black;")
                
                # Lambda closure sorunu için (app=app)
                action_btn.clicked.connect(lambda checked, a=app: self._on_action_clicked(a))
                
                btn_layout.addWidget(action_btn)
                self.table.setCellWidget(row, 4, btn_widget)
            else:
                self.table.setItem(row, 4, QTableWidgetItem("-"))

    def _on_action_clicked(self, app: KnownApp):
        """İşlem butonuna tıklandı."""
        action = "uninstall" if app.recommendation == "Remove" else "disable"
        self.action_requested.emit(action, app.package)
    
    def _filter_list(self, text):
        self._refresh_list()
