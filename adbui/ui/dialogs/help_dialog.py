"""
Help Dialog
===========
Uygulama yardım, kullanım kılavuzu ve hakkında bilgileri içeren diyalog.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QStackedWidget, QTextBrowser, QPushButton,
    QLabel, QWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont

class HelpDialog(QDialog):
    """Yardım ve Hakkında penceresi."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yardım ve Hakkında")
        self.resize(800, 600)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """UI bileşenlerini oluştur."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sol Menü (Navigasyon)
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d44;
                border: none;
                color: #e8e8e8;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #3d3d5c;
            }
            QListWidget::item:selected {
                background-color: #4a4e69;
                color: white;
                border-left: 4px solid #667eea;
            }
            QListWidget::item:hover {
                background-color: #3d3d5c;
            }
        """)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        layout.addWidget(self.nav_list)
        
        # Sağ İçerik Alanı
        content_container = QWidget()
        content_container.setStyleSheet("background-color: #1a1a2e; color: #e8e8e8;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)
        
        # Kapat butonu (Alt kısım)
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a4e69;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a5e7d;
            }
        """)
        close_btn.clicked.connect(self.accept)
        content_layout.addWidget(close_btn, 0, Qt.AlignRight)
        
        layout.addWidget(content_container)
        
        # İçerikleri Yükle
        self._load_pages()
        
        # İlk sayfayı seç
        self.nav_list.setCurrentRow(0)

    def _load_pages(self):
        """Sayfaları oluştur ve ekle."""
        pages = [
            ("🚀 Başlangıç", self._get_getting_started_content()),
            ("📱 Kullanım Kılavuzu", self._get_usage_content()),
            ("🤖 AI Analizi", self._get_ai_content()),
            ("🛠️ Sorun Giderme", self._get_troubleshooting_content()),
            ("ℹ️ Hakkında", self._get_about_content()),
        ]
        
        for title, content in pages:
            # Liste öğesi ekle
            item = QListWidgetItem(title)
            self.nav_list.addItem(item)
            
            # İçerik sayfası ekle
            browser = QTextBrowser()
            browser.setOpenExternalLinks(True)
            browser.setStyleSheet("""
                QTextBrowser {
                    background-color: transparent;
                    border: none;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                }
            """)
            browser.setHtml(content)
            self.content_stack.addWidget(browser)
            
    def _on_nav_changed(self, index):
        """Navigasyon değiştiğinde sayfayı değiştir."""
        self.content_stack.setCurrentIndex(index)

    # --- İÇERİK ANLATIMLARI ---
    
    def _get_getting_started_content(self):
        return """
        <h2 style="color: #667eea;">🚀 Başlangıç Rehberi</h2>
        <p>ADBUI aracını kullanabilmek için Android cihazınızda bazı ayarları yapmanız gerekmektedir.</p>
        
        <h3 style="color: #4a90e2;">1. Geliştirici Seçeneklerini Açma</h3>
        <p>Bu menü varsayılan olarak gizlidir. Açmak için:</p>
        <ol>
            <li>Ayarlar > <b>Telefon Hakkında</b> menüsüne gidin.</li>
            <li><b>Derleme Numarası</b> (veya MIUI Sürümü) üzerine art arda <b>7 kez</b> dokunun.</li>
            <li>"Artık bir geliştiricisiniz!" uyarısını göreceksiniz.</li>
        </ol>
        
        <h3 style="color: #4a90e2;">2. USB Hata Ayıklamayı Açma</h3>
        <p>Cihazınızın bilgisayardan kontrol edilebilmesi için gereklidir:</p>
        <ol>
            <li>Ayarlar > <b>Sistem</b> > <b>Geliştirici Seçenekleri</b> menüsüne girin.</li>
            <li>Listeden <b>USB Hata Ayıklama</b> seçeneğini bulup açın.</li>
            <li>Xiaomi cihazlar için ayrıca <b>USB Hata Ayıklama (Güvenlik Ayarları)</b> seçeneğini de açmanız gerekir.</li>
        </ol>
        
        <h3 style="color: #4a90e2;">3. Bağlantı</h3>
        <p>Cihazınızı USB kablosu ile bilgisayara bağlayın. Telefon ekranında <b>"Bu bilgisayara güvenilsin mi?"</b> uyarısı çıkarsa <b>"Her zaman izin ver"</b>i işaretleyip onaylayın.</p>
        """

    def _get_usage_content(self):
        return """
        <h2 style="color: #667eea;">📱 Kullanım Kılavuzu</h2>
        
        <h3 style="color: #4a90e2;">Paket Listesi (Sol Panel)</h3>
        <p>Tüm yüklü uygulamaları burada görebilirsiniz.</p>
        <ul>
            <li><b>Filtreler:</b> Sistem, Kullanıcı veya Devre Dışı uygulamaları filtreleyebilirsiniz.</li>
            <li><b>Arama:</b> Uygulama adı veya paket ismiyle arama yapabilirsiniz.</li>
            <li><b>Bilinen Uygulamalar Sekmesi:</b> Sık karşılaşılan gereksiz (bloatware) uygulamaları listeler.</li>
        </ul>
        
        <h3 style="color: #4a90e2;">Paket Detayları (Orta Panel)</h3>
        <p>Bir uygulamaya tıkladığınızda detayları ve işlem butonları açılır:</p>
        <ul>
            <li><b>Kaldır:</b> Uygulamayı kalıcı olarak siler (Dikkatli olun!).</li>
            <li><b>Devre Dışı Bırak:</b> Uygulamayı dondurur, silmez. En güvenli yöntemdir.</li>
            <li><b>Dışa Aktar (APK):</b> Uygulamanın setup dosyasını bilgisayara kaydeder.</li>
            <li><b>Verileri Temizle:</b> Uygulamanın sıfırlanmasını sağlar.</li>
        </ul>
        """

    def _get_ai_content(self):
        return """
        <h2 style="color: #667eea;">🤖 AI Analizi (Google Gemini)</h2>
        <p>ADBUI, yapay zeka desteği ile paketlerin ne işe yaradığını analiz eder.</p>
        
        <ul>
            <li><b>Nasıl Çalışır?</b> Paket ismini Google Gemini yapay zekasına sorarak güvenilirlik analizi yapar.</li>
            <li><b>Güvenlik Skoru:</b> 1-10 arasında bir puan verir. 10 puan, silinmesi güvenli demektir.</li>
            <li><b>Önbellek (Cache):</b> Sorgulanan paketler kaydedilir, sonraki sefer internet gerekmeden anında gösterilir.</li>
        </ul>
        
        <p><i>Not: Yapay zeka tavsiyedir, kesin yargı değildir. Sistem bileşenlerini silerken dikkatli olun.</i></p>
        """

    def _get_troubleshooting_content(self):
        return """
        <h2 style="color: #667eea;">🛠️ Sorun Giderme</h2>
        
        <h3>Cihaz Görünmüyor?</h3>
        <ul>
            <li>USB kablosunu kontrol edin, Mümkünse orijinal kablo kullanın.</li>
            <li>Farklı bir USB portu deneyin.</li>
            <li>Bilgisayarınızda <b>ADB Sürücülerinin (Drivers)</b> yüklü olduğundan emin olun.</li>
        </ul>
        
        <h3>Yetki Hatası (Unauthorized)?</h3>
        <p>Telefon ekranına bakın, USB hata ayıklama onayı bekliyor olabilir.</p>
        """

    def _get_about_content(self):
        return """
        <center>
            <h1 style="color: #667eea; font-size: 24px;">ADBUI</h1>
            <p style="font-size: 16px;">Android Debloat ve Yönetim Aracı</p>
            <p style="color: #4a90e2; font-weight: bold; font-size: 18px;">Sürüm v1.0</p>
            <hr style="border: 1px solid #3d3d5c; width: 50%;">
            <p>Geliştirici: <b>Sauth-09</b></p>
            <p>Bu yazılım açık kaynak kodludur ve MIT lisansı ile dağıtılmaktadır.</p>
            <br>
            <p style="color: #888;">© 2026 ADBUI Team</p>
        </center>
        """
