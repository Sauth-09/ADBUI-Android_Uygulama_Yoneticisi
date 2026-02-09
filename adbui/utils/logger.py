"""
Utils - Logger Module
=====================
Uygulama genelinde kullanılan log sistemi.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from logging.handlers import RotatingFileHandler


class LogEmitter:
    """
    Log mesajlarını UI'a iletmek için sinyal benzeri yapı.
    
    PySide6 Signal olmadan çalışabilmek için basit callback sistemi.
    """
    
    def __init__(self):
        self._callbacks = []
    
    def connect(self, callback):
        """Callback ekle."""
        self._callbacks.append(callback)
    
    def disconnect(self, callback):
        """Callback kaldır."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def emit(self, message: str, level: str):
        """Mesajı tüm callback'lere ilet."""
        for callback in self._callbacks:
            try:
                callback(message, level)
            except Exception:
                pass


# Global log emitter instance
log_emitter = LogEmitter()


class UILogHandler(logging.Handler):
    """Log mesajlarını UI'a ileten handler."""
    
    def __init__(self):
        super().__init__()
        self.setFormatter(logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%H:%M:%S'
        ))
    
    def emit(self, record):
        try:
            message = self.format(record)
            log_emitter.emit(message, record.levelname)
        except Exception:
            self.handleError(record)


def setup_logging(
    log_dir: Optional[str] = None,
    level: int = logging.INFO,
    enable_file: bool = True,
    enable_ui: bool = True
) -> logging.Logger:
    """
    Uygulama log sistemini yapılandır.
    
    Args:
        log_dir: Log dosyası dizini
        level: Log seviyesi
        enable_file: Dosyaya yazma aktif mi?
        enable_ui: UI handler aktif mi?
        
    Returns:
        Logger: Root logger
    """
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Mevcut handler'ları temizle
    logger.handlers.clear()
    
    # Format
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    # File handler
    if enable_file:
        if log_dir is None:
            log_dir = Path.home() / ".adbui" / "logs"
        else:
            log_dir = Path(log_dir)
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"adbui_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # UI handler
    if enable_ui:
        ui_handler = UILogHandler()
        ui_handler.setLevel(logging.INFO)
        logger.addHandler(ui_handler)
    
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info("="*40)
    logger.info(f"OTURUM BAŞLATILDI: {start_time}")
    logger.info("="*40)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Modül için logger al."""
    return logging.getLogger(name)
