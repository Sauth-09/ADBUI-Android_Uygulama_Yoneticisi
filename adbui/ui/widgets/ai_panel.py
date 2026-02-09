"""
AI Panel Widget
===============
Sağ panel - AI paket analizi ve önerileri.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QProgressBar
)
from PySide6.QtCore import Qt
import logging

from ...ai.analyzer import AIAnalysis

logger = logging.getLogger(__name__)


class AIPanelWidget(QWidget):
    """
    AI öneri paneli widget'ı.
    
    Seçili paketin AI analizini gösterir.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Başlık
        header_layout = QVBoxLayout()
        
        title = QLabel("🤖 AI Önerisi")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        header_layout.addWidget(title)
        
        self.cache_badge = QLabel("📦 Cache")
        self.cache_badge.setStyleSheet("""
            QLabel {
                background-color: #28a745;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 10px;
            }
        """)
        self.cache_badge.hide()
        header_layout.addWidget(self.cache_badge)
        
        layout.addLayout(header_layout)
        
        # Loading indicator
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        
        self.loading_label = QLabel("AI analizi yapılıyor...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(self.loading_label)
        
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)  # Indeterminate
        self.loading_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2d2d44;
                border-radius: 4px;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #667eea;
                border-radius: 4px;
            }
        """)
        loading_layout.addWidget(self.loading_bar)
        
        self.loading_widget.hide()
        layout.addWidget(self.loading_widget)
        
        # İçerik alanı
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        
        # Açıklama
        self.description_frame = self._create_section("📝 Açıklama", "#667eea")
        self.description_label = QLabel("-")
        self.description_label.setWordWrap(True)
        self.description_frame.layout().addWidget(self.description_label)
        content_layout.addWidget(self.description_frame)
        
        # Güvenlik skoru
        self.safety_frame = self._create_section("🛡️ Güvenlik", "#28a745")
        safety_inner = QVBoxLayout()
        
        self.safety_score_label = QLabel("-")
        self.safety_score_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        safety_inner.addWidget(self.safety_score_label)
        
        self.safety_bar = QProgressBar()
        self.safety_bar.setRange(0, 10)
        self.safety_bar.setTextVisible(False)
        self.safety_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2d2d44;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                border-radius: 4px;
            }
        """)
        safety_inner.addWidget(self.safety_bar)
        
        self.safety_frame.layout().addLayout(safety_inner)
        content_layout.addWidget(self.safety_frame)
        
        # Kaldırma etkisi
        self.impact_frame = self._create_section("⚠️ Kaldırılırsa", "#ffc107")
        self.impact_label = QLabel("-")
        self.impact_label.setWordWrap(True)
        self.impact_frame.layout().addWidget(self.impact_label)
        content_layout.addWidget(self.impact_frame)
        
        # Alternatif öneri
        self.alternative_frame = self._create_section("💡 Alternatif", "#17a2b8")
        self.alternative_label = QLabel("-")
        self.alternative_label.setWordWrap(True)
        self.alternative_frame.layout().addWidget(self.alternative_label)
        content_layout.addWidget(self.alternative_frame)
        
        # Genel öneri
        self.recommendation_frame = self._create_section("📌 Öneri", "#6c757d")
        self.recommendation_label = QLabel("-")
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("font-weight: bold;")
        self.recommendation_frame.layout().addWidget(self.recommendation_label)
        content_layout.addWidget(self.recommendation_frame)
        
        layout.addWidget(self.content_widget)
        
        # Kullanılamıyor mesajı
        self.unavailable_widget = QWidget()
        unavailable_layout = QVBoxLayout(self.unavailable_widget)
        
        unavailable_icon = QLabel("🔒")
        unavailable_icon.setStyleSheet("font-size: 48px;")
        unavailable_icon.setAlignment(Qt.AlignCenter)
        unavailable_layout.addWidget(unavailable_icon)
        
        unavailable_text = QLabel(
            "AI özelliği kullanılamıyor.\n\n"
            "Ayarlar menüsünden OpenAI API\n"
            "anahtarınızı girin."
        )
        unavailable_text.setAlignment(Qt.AlignCenter)
        unavailable_text.setStyleSheet("color: #888;")
        unavailable_layout.addWidget(unavailable_text)
        
        self.unavailable_widget.hide()
        layout.addWidget(self.unavailable_widget)
        
        layout.addStretch()
        
        # Placeholder durumu
        self._show_placeholder()
    
    def _create_section(self, title: str, color: str) -> QFrame:
        """Bölüm frame'i oluştur."""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1a2e;
                border-left: 3px solid {color};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        return frame
    
    def _show_placeholder(self):
        """Placeholder göster."""
        self.content_widget.hide()
        self.loading_widget.hide()
        self.unavailable_widget.hide()
        self.cache_badge.hide()
    
    def set_loading(self, loading: bool):
        """Yükleme durumunu ayarla."""
        if loading:
            self.content_widget.hide()
            self.unavailable_widget.hide()
            self.loading_widget.show()
            self.cache_badge.hide()
        else:
            self.loading_widget.hide()
    
    def set_analysis(self, analysis: Optional[AIAnalysis]):
        """Analiz sonucunu göster."""
        self.loading_widget.hide()
        self.unavailable_widget.hide()
        
        if not analysis:
            self._show_placeholder()
            return
        
        self.content_widget.show()
        
        # Cache badge
        if analysis.is_cached:
            self.cache_badge.show()
        else:
            self.cache_badge.hide()
        
        # Açıklama
        self.description_label.setText(analysis.description)
        
        # Güvenlik skoru
        score = analysis.safety_score
        self.safety_score_label.setText(f"{score}/10")
        self.safety_bar.setValue(score)
        
        # Skor rengini ayarla
        if score >= 7:
            color = "#28a745"
        elif score >= 4:
            color = "#ffc107"
        else:
            color = "#dc3545"
        
        self.safety_score_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        self.safety_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #2d2d44;
                border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        
        # Kaldırma etkisi
        self.impact_label.setText(analysis.removal_impact)
        
        # Alternatif
        self.alternative_label.setText(analysis.alternative_action)
        
        # Öneri
        self.recommendation_label.setText(analysis.recommendation)
        
        # Güvenli değilse öneri vurgula
        if not analysis.safe_to_remove:
            self.recommendation_frame.setStyleSheet("""
                QFrame {
                    background-color: #3d1f1f;
                    border-left: 3px solid #dc3545;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        else:
            self.recommendation_frame.setStyleSheet("""
                QFrame {
                    background-color: #1a1a2e;
                    border-left: 3px solid #28a745;
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
    
    def set_unavailable(self):
        """AI kullanılamıyor durumunu göster."""
        self.content_widget.hide()
        self.loading_widget.hide()
        self.cache_badge.hide()
        self.unavailable_widget.show()
