"""
AI Cache Module
===============
AI yanıtlarını SQLite'da saklar.
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AICache:
    """
    AI analiz sonuçlarını cache'leyen sınıf.
    
    SQLite veritabanı kullanarak paket analizlerini saklar.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Cache'i başlat.
        
        Args:
            cache_dir: Cache dizini (None ise varsayılan kullanılır)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".adbui" / "cache"
        else:
            cache_dir = Path(cache_dir)
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "ai_cache.db"
        
        self._init_db()
    
    def _init_db(self):
        """Veritabanını oluştur."""
        with sqlite3.connect(self.db_path) as conn:
            # Performans ve eşzamanlılık için WAL modu
            conn.execute("PRAGMA journal_mode=WAL;")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    package_name TEXT PRIMARY KEY,
                    analysis_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON analysis_cache(created_at)
            """)
            conn.commit()
    
    def get(self, package_name: str):
        """
        Cache'den analiz al.
        
        Args:
            package_name: Paket adı
            
        Returns:
            AIAnalysis veya None
        """
        # Gecikmeli import (circular import önlemi)
        from .analyzer import AIAnalysis
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT analysis_json, created_at 
                FROM analysis_cache 
                WHERE package_name = ?
                """,
                (package_name,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            analysis_json, created_at = row
            
            # Erişim zamanını güncelle
            conn.execute(
                "UPDATE analysis_cache SET accessed_at = ? WHERE package_name = ?",
                (datetime.now().isoformat(), package_name)
            )
            conn.commit()
            
            # JSON'dan AIAnalysis oluştur
            try:
                data = json.loads(analysis_json)
                return AIAnalysis(**data)
            except Exception as e:
                logger.error(f"Cache parse hatası: {e}")
                return None
    
    def set(self, package_name: str, analysis) -> bool:
        """
        Analizi cache'e kaydet.
        
        Args:
            package_name: Paket adı
            analysis: AIAnalysis objesi
            
        Returns:
            bool: Başarılı mı?
        """
        try:
            analysis_dict = {
                'description': analysis.description,
                'safety_score': analysis.safety_score,
                'safe_to_remove': analysis.safe_to_remove,
                'removal_impact': analysis.removal_impact,
                'alternative_action': analysis.alternative_action,
                'recommendation': analysis.recommendation,
            }
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO analysis_cache 
                    (package_name, analysis_json, created_at, accessed_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        package_name,
                        json.dumps(analysis_dict, ensure_ascii=False),
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                conn.commit()
            
            logger.debug(f"Cache'e kaydedildi: {package_name}")
            return True
            
        except Exception as e:
            logger.error(f"Cache kayıt hatası: {e}")
            return False
    
    def delete(self, package_name: str) -> bool:
        """Cache'den sil."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM analysis_cache WHERE package_name = ?",
                    (package_name,)
                )
                conn.commit()
            return True
        except Exception:
            return False
    
    def clear(self) -> bool:
        """Tüm cache'i temizle."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM analysis_cache")
                conn.commit()
            logger.info("Cache temizlendi")
            return True
        except Exception as e:
            logger.error(f"Cache temizleme hatası: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Cache istatistiklerini al."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM analysis_cache")
            total = cursor.fetchone()[0]
            
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM analysis_cache 
                WHERE created_at > ?
                """,
                ((datetime.now() - timedelta(days=7)).isoformat(),)
            )
            recent = cursor.fetchone()[0]
        
        return {
            'total_entries': total,
            'recent_entries': recent,
            'db_path': str(self.db_path)
        }
