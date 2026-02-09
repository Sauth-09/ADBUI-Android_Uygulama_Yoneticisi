"""
Background Analyzer
====================
Arka planda toplu paket analizi yapar.
"""

import time
import logging
from typing import List
from PySide6.QtCore import QThread, Signal

from .analyzer import PackageAnalyzer, AIAnalysis
from .cache import AICache
from ..core.package_manager import Package

logger = logging.getLogger(__name__)


class BackgroundAnalyzerThread(QThread):
    """
    Arka planda paket analizi yapan thread.
    
    Paketleri 10'arlı gruplar halinde analiz eder.
    Her analiz tamamlandığında sinyal gönderir.
    """
    
    # Sinyaller
    progress_updated = Signal(int, int)  # current, total
    package_analyzed = Signal(str, object)  # package_name, AIAnalysis
    batch_completed = Signal(int)  # completed_count
    all_completed = Signal(int)  # total_analyzed
    error_occurred = Signal(str)  # error message
    
    def __init__(self, packages: List[Package], analyzer: PackageAnalyzer, 
                 cache: AICache, batch_size: int = 10, parent=None):
        super().__init__(parent)
        
        self.packages = packages
        self.analyzer = analyzer
        self.cache = cache
        self.batch_size = batch_size
        self._stop_requested = False
    
    def run(self):
        """Thread ana fonksiyonu."""
        total = len(self.packages)
        analyzed = 0
        skipped = 0
        
        logger.info(f"Arka plan analizi başladı: {total} paket")
        
        # Cache'de olmayan paketleri filtrele
        packages_to_analyze = []
        for pkg in self.packages:
            cached = self.cache.get(pkg.name)
            if cached:
                skipped += 1
            else:
                packages_to_analyze.append(pkg)
        
        logger.info(f"{skipped} paket cache'den alındı, {len(packages_to_analyze)} paket analiz edilecek")
        
        # Batch'ler halinde işle
        for i in range(0, len(packages_to_analyze), self.batch_size):
            if self._stop_requested:
                logger.info("Arka plan analizi durduruldu")
                break
            
            batch = packages_to_analyze[i:i + self.batch_size]
            batch_names = [pkg.name for pkg in batch]
            
            try:
                # Toplu AI analizi yap (Tek istek = 10 paket)
                results = self.analyzer.analyze_multiple(batch_names)
                
                if results:
                    batch_success_count = 0
                    for pkg in batch:
                        if pkg.name in results:
                            analysis = results[pkg.name]
                            batch_success_count += 1
                            analyzed += 1
                            self.package_analyzed.emit(pkg.name, analysis)
                    
                    # Sonuç boşsa ve durdurulmadıysa rate limit olabilir
                    if batch_success_count == 0 and not self._stop_requested:
                        logger.warning("Batch analizi boş döndü, rate limit olabilir. 30sn bekleniyor...")
                        self.error_occurred.emit("AI Kotası aşıldı, 30sn bekleniyor...")
                        time.sleep(30)
                else:
                    if not self._stop_requested:
                         logger.warning("Batch analizi boş döndü. Rate limit olabilir.")
                         self.error_occurred.emit("AI Kotası aşıldı, 30sn bekleniyor...")
                         time.sleep(30)

                # Progress güncelle
                self.progress_updated.emit(analyzed + skipped, total)
                
                # Batch tamamlandı
                self.batch_completed.emit(analyzed)
                
            except Exception as e:
                logger.error(f"Batch analiz hatası: {e}")
                self.error_occurred.emit(str(e))
            
            # Rate limit koruması (5 RPM = 12sn/istek)
            # Güvenli olması için 15 saniye bekleyelim
            if not self._stop_requested and i + self.batch_size < len(packages_to_analyze):
                time.sleep(15)
        
        self.all_completed.emit(analyzed)
        logger.info(f"Arka plan analizi tamamlandı: {analyzed} yeni, {skipped} cache'den")
    
    def stop(self):
        """Thread'i durdur."""
        self._stop_requested = True
