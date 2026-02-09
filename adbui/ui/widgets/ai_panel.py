"""
AI Panel Widget
===============
Sağ panel - AI paket analizi ve önerileri.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QScrollArea, QPushButton
)
from PySide6.QtCore import Qt, Signal
import logging

from ...ai.analyzer import AIAnalysis

logger = logging.getLogger(__name__)


class AIPanelWidget(QWidget):
    """
    AI öneri paneli widget'ı.
    
    Seçili paketin AI analizini gösterir.
    """
    
    refresh_requested = Signal(str)  # package_name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_package: Optional[str] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Başlık
        header = QHBoxLayout()
        
        title = QLabel("🤖 AI Analizi")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 4px;")
        header.addWidget(title)
        
        header.addStretch()
        
        self.cache_badge = QLabel("📦 Önbellek")
        self.cache_badge.setStyleSheet("""
            QLabel {
                background-color: #28a745;
                color: white;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        self.cache_badge.hide()
        header.addWidget(self.cache_badge)
        
        header.addStretch()

        # İlerleme Label (Yeni)
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #00bcd4; font-weight: bold; font-size: 12px;")
        self.progress_label.hide()
        header.addWidget(self.progress_label)
        
        header.addStretch()
        
        # Güncelle butonu
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("AI analizini yeniden yap")
        self.refresh_btn.setFixedSize(28, 28)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d5c;
                border: none;
                border-radius: 14px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4d4d6c;
            }
            QPushButton:pressed {
                background-color: #2d2d4c;
            }
        """)
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        self.refresh_btn.hide()  # Paket seçilene kadar gizli
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        # Loading indicator
        self.loading_widget = QWidget()
        loading_layout = QVBoxLayout(self.loading_widget)
        loading_layout.setAlignment(Qt.AlignCenter)
        
        loading_icon = QLabel("⏳")
        loading_icon.setStyleSheet("font-size: 36px;")
        loading_icon.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(loading_icon)
        
        self.loading_label = QLabel("AI analizi yapılıyor...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #888; font-size: 13px;")
        loading_layout.addWidget(self.loading_label)
        
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)  # Indeterminate
        self.loading_bar.setFixedWidth(200)
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
        loading_layout.addWidget(self.loading_bar, alignment=Qt.AlignCenter)
        
        self.loading_widget.hide()
        layout.addWidget(self.loading_widget)
        
        # İçerik alanı
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)
        
        # ===== SONUÇ KARTI (Ultra Kompakt) =====
        self.result_card = QFrame()
        self.result_card.setStyleSheet("""
            QFrame {
                background-color: #1e3a5f;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        result_layout = QVBoxLayout(self.result_card)
        result_layout.setSpacing(4)
        result_layout.setContentsMargins(6, 6, 6, 6)
        
        # Üst kısım: İkon + Başlık + Skor
        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        
        self.result_icon = QLabel("✅")
        self.result_icon.setStyleSheet("font-size: 20px;")
        top_row.addWidget(self.result_icon)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        
        self.result_title = QLabel("Kaldırılabilir")
        self.result_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #28a745;")
        title_layout.addWidget(self.result_title)
        
        self.result_subtitle = QLabel("Güvenli işlem")
        self.result_subtitle.setStyleSheet("font-size: 10px; color: #ccc;")
        title_layout.addWidget(self.result_subtitle)
        
        top_row.addLayout(title_layout)
        top_row.addStretch()
        
        # Skor
        score_container = QWidget()
        score_container.setStyleSheet("background-color: rgba(0,0,0,0.2); border-radius: 4px;")
        score_layout = QHBoxLayout(score_container) # Yan yana olsun
        score_layout.setContentsMargins(6, 2, 6, 2)
        score_layout.setSpacing(4)
        
        self.safety_score_label = QLabel("10")
        self.safety_score_label.setAlignment(Qt.AlignCenter)
        self.safety_score_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #28a745;")
        score_layout.addWidget(self.safety_score_label)
        
        score_max = QLabel("/10")
        score_max.setAlignment(Qt.AlignCenter)
        score_max.setStyleSheet("font-size: 10px; color: #aaa; margin-top: 4px;")
        score_layout.addWidget(score_max)
        
        top_row.addWidget(score_container)
        
        result_layout.addLayout(top_row)
        
        # Güvenlik çubuğu
        self.safety_bar = QProgressBar()
        self.safety_bar.setRange(0, 10)
        self.safety_bar.setTextVisible(False)
        self.safety_bar.setFixedHeight(4)
        self.safety_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2d2d44;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 2px;
            }
        """)
        result_layout.addWidget(self.safety_bar)
        
        content_layout.addWidget(self.result_card)
        
        # ===== AÇIKLAMA =====
        desc_section = self._create_info_section("📝 Bu uygulama ne işe yarar?")
        self.description_label = desc_section[1]
        content_layout.addWidget(desc_section[0])
        
        # ===== KALDIRILIRSA NE OLUR =====
        impact_section = self._create_info_section("⚠️ Kaldırılırsa ne olur?")
        self.impact_label = impact_section[1]
        content_layout.addWidget(impact_section[0])
        
        # ===== ALTERNATİF ÖNERİ =====
        alt_section = self._create_info_section("💡 Alternatif öneri")
        self.alternative_label = alt_section[1]
        content_layout.addWidget(alt_section[0])
        
        # ===== SONUÇ ÖNERİSİ =====
        self.recommendation_frame = QFrame()
        self.recommendation_frame.setStyleSheet("""
            QFrame {
                background-color: #1a2e1a;
                border: 1px solid #28a745;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        rec_layout = QVBoxLayout(self.recommendation_frame)
        rec_layout.setSpacing(4)
        
        rec_title = QLabel("📌 Sonuç")
        rec_title.setStyleSheet("font-size: 12px; color: #28a745; font-weight: bold;")
        rec_layout.addWidget(rec_title)
        
        self.recommendation_label = QLabel("-")
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #fff;")
        rec_layout.addWidget(self.recommendation_label)
        
        content_layout.addWidget(self.recommendation_frame)
        
        content_layout.addStretch()
        
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # Kullanılamıyor mesajı
        self.unavailable_widget = QWidget()
        unavailable_layout = QVBoxLayout(self.unavailable_widget)
        unavailable_layout.setAlignment(Qt.AlignCenter)
        
        unavailable_icon = QLabel("🔒")
        unavailable_icon.setStyleSheet("font-size: 48px;")
        unavailable_icon.setAlignment(Qt.AlignCenter)
        unavailable_layout.addWidget(unavailable_icon)
        
        unavailable_text = QLabel(
            "AI özelliği kullanılamıyor.\n\n"
            "Ayarlar menüsünden Google Gemini\n"
            "API anahtarınızı girin."
        )
        unavailable_text.setAlignment(Qt.AlignCenter)
        unavailable_text.setStyleSheet("color: #888; font-size: 13px;")
        unavailable_layout.addWidget(unavailable_text)
        
        self.unavailable_widget.hide()
        layout.addWidget(self.unavailable_widget)
        
        # Placeholder durumu
        self._show_placeholder()
    
    def _create_info_section(self, title: str):
        """Bilgi bölümü oluştur."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #888; font-weight: bold;")
        layout.addWidget(title_label)
        
        content_label = QLabel("-")
        content_label.setWordWrap(True)
        content_label.setStyleSheet("font-size: 13px; color: #e8e8e8; line-height: 1.4;")
        layout.addWidget(content_label)
        
        return (frame, content_label)
    
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
            self.refresh_btn.hide()
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
        
        self.refresh_btn.show()
        
        # Cache badge
        is_cached = analysis.is_cached
        text = "Veritabanından (Cache)" if is_cached else "Canlı Analiz"
        color = "#6c757d" if is_cached else "#28a745"
        
        self.cache_badge.setText(text)
        self.cache_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        self.cache_badge.show()
        
        # Güvenlik skoru ve sonuç kartı
        score = analysis.safety_score
        self.safety_score_label.setText(str(score))
        self.safety_bar.setValue(score)
        
        # Skora göre renk ve mesaj ayarla
        if score >= 7:
            color = "#28a745"
            bg_color = "#1e3a5f"
            border_color = "#28a745" # Sınır rengini skora göre değiştirmiyoruz, arka plan koyu kalsın
            icon = "✅"
            title = "Kaldırılabilir"
            subtitle = "Güvenli işlem"
        elif score >= 4:
            color = "#ffc107"
            bg_color = "#1e3a5f"
            border_color = "#ffc107"
            icon = "⚠️"
            title = "Dikkatli Olun"
            subtitle = "Riskleri değerlendirin"
        else:
            color = "#dc3545"
            bg_color = "#1e3a5f"
            border_color = "#dc3545"
            icon = "❌"
            title = "Kaldırmayın"
            subtitle = "Sistem için kritik"
        
        self.result_icon.setText(icon)
        self.result_title.setText(title)
        self.result_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        self.result_subtitle.setText(subtitle)
        self.safety_score_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        
        # Arka plan rengini sabit tutuyoruz, sadece border değişebilir veya sabit kalabilir
        # Kompakt görünümde çok fazla renk karmaşası olmasın
        self.result_card.setStyleSheet("""
            QFrame {
                background-color: #1e3a5f;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        
        self.safety_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #2d2d44;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)
        
        # Açıklama
        self.description_label.setText(analysis.description)
        
        # Kaldırma etkisi
        self.impact_label.setText(analysis.removal_impact)
        
        # Alternatif
        self.alternative_label.setText(analysis.alternative_action)
        
        # Öneri
        self.recommendation_label.setText(analysis.recommendation)
        
        # Öneri kutusunun rengini ayarla (Border kullanarak vurgula)
        rec_bg = "#1a2e1a" if score >= 7 else ("#2e2a1a" if score >= 4 else "#2e1a1a")
        
        self.recommendation_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {rec_bg};
                border: 1px solid {color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
    
    def set_unavailable(self):
        """AI kullanılamıyor durumunu göster."""
        self.content_widget.hide()
        self.loading_widget.hide()
        self.cache_badge.hide()
        self.unavailable_widget.show()
        self.refresh_btn.hide()
    
    def clear(self):
        """Paneli temizle (public)."""
        self._show_placeholder()
    
    def _on_refresh_clicked(self):
        """Yenile butonuna tıklandı."""
        if self.current_package:
            self.refresh_requested.emit(self.current_package)

    def update_progress(self, text: str, is_error: bool = False):
        """İlerleme durumunu güncelle (text, error)."""
        self.progress_label.setText(text)
        self.progress_label.show()
        
        if is_error:
            self.progress_label.setStyleSheet("color: #dc3545; font-weight: bold; font-size: 12px;")
        else:
            self.progress_label.setStyleSheet("color: #00bcd4; font-weight: bold; font-size: 12px;")
