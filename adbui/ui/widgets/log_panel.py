"""
Log Panel Widget
================
Alt panel - Canlı log çıktısı.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QColor
import logging

logger = logging.getLogger(__name__)


class LogPanelWidget(QWidget):
    """
    Log paneli widget'ı.
    
    Uygulama loglarını canlı olarak gösterir.
    """
    
    # Log seviyesi renkleri
    LEVEL_COLORS = {
        'DEBUG': '#6c757d',
        'INFO': '#17a2b8',
        'WARNING': '#ffc107',
        'ERROR': '#dc3545',
        'CRITICAL': '#ff0000',
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(4)
        
        # Başlık ve butonlar
        header = QHBoxLayout()
        
        title = QLabel("📝 Log")
        title.setStyleSheet("font-weight: bold;")
        header.addWidget(title)
        
        header.addStretch()
        
        clear_btn = QPushButton("Temizle")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self._clear_logs)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # Log alanı
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0f0f23;
                color: #e8e8e8;
                border: 1px solid #2d2d44;
                border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_text)
    
    def append_log(self, message: str, level: str = "INFO"):
        """
        Log mesajı ekle.
        
        Args:
            message: Log mesajı
            level: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        color = self.LEVEL_COLORS.get(level, '#e8e8e8')
        
        # HTML formatında ekle
        html = f'<span style="color: {color};">{message}</span><br>'
        
        # Cursor'u sona taşı ve ekle
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        self.log_text.insertHtml(html)
        
        # Otomatik scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _clear_logs(self):
        """Logları temizle."""
        self.log_text.clear()
        self.append_log("Log temizlendi", "INFO")
