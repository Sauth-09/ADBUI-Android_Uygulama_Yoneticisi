"""
Package List Widget
===================
Sol panel - Paket listesi, arama ve filtreleme.
"""

from typing import List, Optional
import webbrowser
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QCheckBox, QLabel,
    QFrame, QMenu, QApplication
)
from PySide6.QtGui import QAction, QCursor
from PySide6.QtCore import Qt, Signal
import logging

from ...core.package_manager import Package, PackageCategory

logger = logging.getLogger(__name__)


class PackageListWidget(QWidget):
    """
    Paket listesi widget'ı.
    
    Arama, filtreleme ve paket seçimi özellikleri içerir.
    """
    
    package_selected = Signal(object)  # Package objesi
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._packages: List[Package] = []
        self._filtered_packages: List[Package] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Başlık
        title = QLabel("📦 Paketler")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        layout.addWidget(title)
        
        # Arama kutusu
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Paket ara...")
        self.search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_input)
        
        # Filtreler
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(12)
        
        self.filter_system = QCheckBox("Sistem")
        self.filter_system.setChecked(True)
        self.filter_system.stateChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.filter_system)
        
        self.filter_user = QCheckBox("Kullanıcı")
        self.filter_user.setChecked(True)
        self.filter_user.stateChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.filter_user)
        
        self.filter_disabled = QCheckBox("Devre Dışı")
        self.filter_disabled.setChecked(True)
        self.filter_disabled.stateChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.filter_disabled)
        
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        # Liste
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)
        
        # Sayaç
        self.count_label = QLabel("0 paket")
        self.count_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.count_label)
    
    def set_packages(self, packages: List[Package]):
        """Paket listesini ayarla."""
        self._packages = packages
        self._apply_filters()
    
    def _apply_filters(self):
        """Filtreleri uygula."""
        search_text = self.search_input.text().lower()
        
        self._filtered_packages = []
        
        for package in self._packages:
            # Kategori filtresi
            if package.category == PackageCategory.SYSTEM and not self.filter_system.isChecked():
                continue
            if package.category == PackageCategory.USER and not self.filter_user.isChecked():
                continue
            if package.category == PackageCategory.DISABLED and not self.filter_disabled.isChecked():
                continue
            
            # Arama filtresi
            if search_text and search_text not in package.name.lower():
                continue
            
            self._filtered_packages.append(package)
        
        self._update_list()
    
    def _update_list(self):
        """Liste widget'ını güncelle."""
        self.list_widget.clear()
        
        for package in self._filtered_packages:
            item = QListWidgetItem()
            
            # İkon belirle
            if package.is_critical:
                icon = "🔒"
            elif package.category == PackageCategory.SYSTEM:
                icon = "⚙️"
            elif package.category == PackageCategory.DISABLED:
                icon = "❄️"
            else:
                icon = "📱"
            
            # Vendor bilgisi
            vendor_text = f" [{package.vendor}]" if package.vendor else ""
            
            item.setText(f"{icon} {package.name}{vendor_text}")
            item.setData(Qt.UserRole, package)
            
            # Kritik paketleri vurgula
            if package.is_critical:
                item.setForeground(Qt.red)
            elif not package.is_enabled:
                item.setForeground(Qt.gray)
            
            self.list_widget.addItem(item)
        
        self.count_label.setText(f"{len(self._filtered_packages)} paket")
    
    def _on_search_changed(self, text: str):
        """Arama metni değişti."""
        self._apply_filters()
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Liste öğesi tıklandı."""
        package = item.data(Qt.UserRole)
        if package:
            self.package_selected.emit(package)
    
    def _show_context_menu(self, pos):
        """Sağ tık menüsü göster."""
        item = self.list_widget.itemAt(pos)
        if not item:
            return
            
        package = item.data(Qt.UserRole)
        if not package:
            return
            
        menu = QMenu(self)
        
        # Kopyala
        copy_action = QAction("📋 Paket Adını Kopyala", self)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(package.name))
        menu.addAction(copy_action)
        
        # Ara
        search_action = QAction("🔍 Google'da Ara", self)
        search_action.triggered.connect(lambda: webbrowser.open(f"https://www.google.com/search?q={package.name} android package"))
        menu.addAction(search_action)
        
        menu.exec(QCursor.pos())

    def get_selected_package(self) -> Optional[Package]:
        """Seçili paketi al."""
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None
