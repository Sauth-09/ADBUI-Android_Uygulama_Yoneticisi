"""
Permissions Dialog
==================
Paket izinlerini yöneten dialog penceresi.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QCheckBox, QWidget, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont

from ...core.package_manager import PackageManager
from ...data.permissions import get_permission_description

class PermissionLoaderThread(QThread):
    """İzinleri arka planda yükleyen thread."""
    loaded = Signal(list)
    
    def __init__(self, pm, package_name):
        super().__init__()
        self.pm = pm
        self.package_name = package_name
        
    def run(self):
        perms = self.pm.get_permissions(self.package_name)
        self.loaded.emit(perms)


class PermissionsDialog(QDialog):
    """
    İzin yönetim penceresi.
    """
    
    def __init__(self, package_manager: PackageManager, package_name: str, parent=None):
        super().__init__(parent)
        self.pm = package_manager
        self.package_name = package_name
        
        self.setWindowTitle(f"İzin Yöneticisi: {package_name}")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        
        # Stil
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                color: #e8e8e8;
            }
            QTableWidget {
                background-color: #16213e;
                gridline-color: #2d2d44;
                border: 1px solid #2d2d44;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #0f0f23;
                color: #a0a0a0;
                padding: 8px;
                border: none;
            }
            QTableWidgetItem {
                padding: 10px;
            }
            QLabel {
                color: #e8e8e8;
            }
        """)
        
        self._setup_ui()
        self._load_permissions()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Info
        info_header = QLabel(f"🛡️ {self.package_name}")
        info_header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(info_header)
        
        info_label = QLabel(
            "⚠️ Not: Sadece 'Runtime' (Çalışma Zamanı) izinleri açılıp kapatılabilir.\n"
            "Diğer izinler (Install-time) bilgilendirme amaçlıdır ve değiştirilemez."
        )
        info_label.setStyleSheet("color: #ffc107; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["İzin", "Açıklama", "Durum"])
        
        # Tablo ayarları
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("alternate-background-color: #1a1a2e;")
        
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.table)
        
        # Loading
        self.loading_label = QLabel("İzinler yükleniyor...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.loading_label)
        self.loading_label.hide()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4e69;
                color: white; border: none; padding: 8px 16px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #6c757d; }
        """)
        refresh_btn.clicked.connect(self._load_permissions)
        btn_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet("""
             QPushButton {
                background-color: #2d2d44;
                color: white; border: none; padding: 8px 16px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #3d3d5c; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
    def _load_permissions(self):
        self.table.setRowCount(0)
        self.table.hide()
        self.loading_label.show()
        
        self.loader = PermissionLoaderThread(self.pm, self.package_name)
        self.loader.loaded.connect(self._on_loaded)
        self.loader.start()
        
    def _on_loaded(self, permissions):
        self.loading_label.hide()
        self.table.show()
        self.table.setRowCount(len(permissions))
        
        if not permissions:
            self.table.setRowCount(1)
            self.table.setItem(0, 1, QTableWidgetItem("İzin bulunamadı."))
            return
            
        font_bold = QFont()
        font_bold.setBold(True)
        
        for i, perm in enumerate(permissions):
            name = perm['name']
            granted = perm['granted']
            desc = get_permission_description(name)
            
            # Name
            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemIsEnabled) # Sadece okunabilir
            name_item.setToolTip(name)
            self.table.setItem(i, 0, name_item)
            
            # Desc
            desc_item = QTableWidgetItem(desc)
            desc_item.setFlags(Qt.ItemIsEnabled)
            desc_item.setFont(font_bold)
            desc_item.setToolTip(desc)
            self.table.setItem(i, 1, desc_item)
            
            changeable = perm.get('changeable', False)
            
            # Checkbox Widget
            widget = QWidget()
            chk = QCheckBox()
            chk.setChecked(granted)
            
            if changeable:
                 chk.setStyleSheet("""
                    QCheckBox::indicator { width: 20px; height: 20px; }
                 """)
                 chk.setCursor(Qt.PointingHandCursor)
                 # Lambda içinde default argümanlar
                 chk.clicked.connect(lambda checked, n=name, c=chk: self._toggle_permission(n, checked, c))

            else:
                 chk.setEnabled(False)
                 chk.setStyleSheet("""
                    QCheckBox::indicator { width: 20px; height: 20px; background-color: #3d3d3d; border: 1px solid #555; }
                 """)
                 chk.setToolTip("Bu izin sistem tarafından kilitlidir (Install-time).")
            
            layout = QHBoxLayout(widget)
            layout.addWidget(chk)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0,0,0,0)
            
            self.table.setCellWidget(i, 2, widget)
            
            self.table.setRowHeight(i, 45)
            
    def _toggle_permission(self, name, checked, checkbox):
        """İzni aç/kapat."""
        
        # Kullanıcıya beklemesini hissettir
        checkbox.setEnabled(False)
        self.setCursor(Qt.WaitCursor)
        
        success = False
        try:
            if checked:
                success = self.pm.grant_permission(self.package_name, name)
            else:
                success = self.pm.revoke_permission(self.package_name, name)
        except Exception as e:
            pass
            
        checkbox.setEnabled(True)
        self.setCursor(Qt.ArrowCursor)
            
        if not success:
            # Başarısız olursa eski haline getir (sinyal tetiklemeden)
            checkbox.blockSignals(True)
            checkbox.setChecked(not checked) # Revert
            checkbox.blockSignals(False)
            
            QMessageBox.warning(
                self, 
                "İşlem Başarısız", 
                f"'{name}' izni değiştirilemedi.\n\n"
                "Bu izin sistem tarafından kilitli olabilir veya root yetkisi gerektirebilir.\n"
                "Normal (Install-time) izinler değiştirilemez."
            )
