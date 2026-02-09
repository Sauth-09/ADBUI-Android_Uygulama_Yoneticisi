"""
ADB Service Module
==================
ADB executable ile iletişim kuran temel servis sınıfı.
Tüm ADB komutlarını subprocess üzerinden çalıştırır.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ADBResult:
    """ADB komut sonucu."""
    success: bool
    stdout: str
    stderr: str
    return_code: int


class ADBService:
    """
    ADB komutlarını çalıştıran servis sınıfı.
    
    Bu sınıf, proje klasöründeki adb.exe dosyasını kullanarak
    Android cihazlarla iletişim kurar.
    """
    
    def __init__(self, adb_path: Optional[str] = None):
        """
        ADB servisini başlat.
        
        Args:
            adb_path: ADB executable yolu. None ise otomatik tespit edilir.
        """
        self.adb_path = adb_path or self._find_adb()
        if not self.adb_path or not os.path.exists(self.adb_path):
            raise FileNotFoundError(
                "adb.exe bulunamadı. Lütfen platform-tools klasörünü kontrol edin."
            )
        logger.info(f"ADB yolu: {self.adb_path}")
    
    def _find_adb(self) -> Optional[str]:
        """Proje klasöründe adb.exe'yi bul."""
        # Önce çalışma dizininde ara
        possible_paths = [
            Path.cwd() / "adb.exe",
            Path(__file__).parent.parent.parent / "adb.exe",
        ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def execute(
        self, 
        args: List[str], 
        device_serial: Optional[str] = None,
        timeout: int = 30
    ) -> ADBResult:
        """
        ADB komutu çalıştır.
        
        Args:
            args: ADB komut argümanları (adb hariç)
            device_serial: Hedef cihaz seri numarası
            timeout: Komut timeout süresi (saniye)
            
        Returns:
            ADBResult: Komut sonucu
        """
        cmd = [self.adb_path]
        
        # Cihaz belirtilmişse -s parametresi ekle
        if device_serial:
            cmd.extend(["-s", device_serial])
        
        cmd.extend(args)
        
        logger.debug(f"ADB komutu: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            return ADBResult(
                success=result.returncode == 0,
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                return_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            logger.error(f"ADB komutu zaman aşımına uğradı: {' '.join(cmd)}")
            return ADBResult(
                success=False,
                stdout="",
                stderr="Komut zaman aşımına uğradı",
                return_code=-1
            )
        except Exception as e:
            logger.error(f"ADB komutu başarısız: {e}")
            return ADBResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1
            )
    
    def shell(
        self, 
        command: str, 
        device_serial: Optional[str] = None,
        timeout: int = 30
    ) -> ADBResult:
        """
        ADB shell komutu çalıştır.
        
        Args:
            command: Shell komutu
            device_serial: Hedef cihaz seri numarası
            timeout: Komut timeout süresi
            
        Returns:
            ADBResult: Komut sonucu
        """
        return self.execute(["shell", command], device_serial, timeout)
    
    def start_server(self) -> ADBResult:
        """ADB server'ı başlat."""
        return self.execute(["start-server"])
    
    def kill_server(self) -> ADBResult:
        """ADB server'ı durdur."""
        return self.execute(["kill-server"])
    
    def get_devices_raw(self) -> ADBResult:
        """Bağlı cihazların ham listesini al."""
        return self.execute(["devices", "-l"])
