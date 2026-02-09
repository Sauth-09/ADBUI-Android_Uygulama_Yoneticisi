"""
Device Manager Module
=====================
Android cihaz tespiti ve yönetimi.
"""

import re
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from .adb_service import ADBService

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    """Cihaz bağlantı durumu."""
    ONLINE = "device"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    UNKNOWN = "unknown"


@dataclass
class Device:
    """Android cihaz bilgisi."""
    serial: str
    status: DeviceStatus
    model: Optional[str] = None
    product: Optional[str] = None
    transport_id: Optional[str] = None
    android_version: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """Kullanıcı dostu cihaz adı."""
        if self.model:
            return f"{self.model} ({self.serial})"
        return self.serial
    
    @property
    def is_ready(self) -> bool:
        """Cihazın kullanıma hazır olup olmadığı."""
        return self.status == DeviceStatus.ONLINE


class DeviceManager:
    """
    Cihaz yönetim sınıfı.
    
    Bağlı Android cihazları tespit eder ve yönetir.
    """
    
    def __init__(self, adb_service: ADBService):
        """
        DeviceManager'ı başlat.
        
        Args:
            adb_service: ADB servis instance'ı
        """
        self.adb = adb_service
        self._current_device: Optional[Device] = None
    
    @property
    def current_device(self) -> Optional[Device]:
        """Şu an seçili cihaz."""
        return self._current_device
    
    @current_device.setter
    def current_device(self, device: Optional[Device]):
        """Cihaz seç."""
        self._current_device = device
        if device:
            logger.info(f"Cihaz seçildi: {device.display_name}")
    
    def get_devices(self) -> List[Device]:
        """
        Bağlı cihazları listele.
        
        Returns:
            List[Device]: Bağlı cihaz listesi
        """
        result = self.adb.get_devices_raw()
        
        if not result.success:
            logger.error(f"Cihaz listesi alınamadı: {result.stderr}")
            return []
        
        devices = []
        lines = result.stdout.split('\n')
        
        # İlk satır "List of devices attached" header'ı
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            device = self._parse_device_line(line)
            if device:
                # Cihaz ready ise ek bilgileri al
                if device.is_ready:
                    device = self._enrich_device_info(device)
                devices.append(device)
        
        logger.info(f"{len(devices)} cihaz bulundu")
        return devices
    
    def _parse_device_line(self, line: str) -> Optional[Device]:
        """
        'adb devices -l' çıktısından cihaz bilgisi parse et.
        
        Örnek çıktı:
        RFXXXXXXX device product:dreamltexx model:SM_G950F transport_id:1
        """
        # Temel pattern: serial status [ek bilgiler]
        parts = line.split()
        if len(parts) < 2:
            return None
        
        serial = parts[0]
        status_str = parts[1]
        
        # Status'u enum'a çevir
        try:
            status = DeviceStatus(status_str)
        except ValueError:
            status = DeviceStatus.UNKNOWN
        
        device = Device(serial=serial, status=status)
        
        # Ek bilgileri parse et
        for part in parts[2:]:
            if ':' in part:
                key, value = part.split(':', 1)
                if key == 'model':
                    device.model = value.replace('_', ' ')
                elif key == 'product':
                    device.product = value
                elif key == 'transport_id':
                    device.transport_id = value
        
        return device
    
    def _enrich_device_info(self, device: Device) -> Device:
        """Cihaza ek bilgiler ekle (Android versiyon vs.)."""
        # Android versiyonunu al
        result = self.adb.shell(
            "getprop ro.build.version.release",
            device_serial=device.serial
        )
        if result.success:
            device.android_version = result.stdout.strip()
        
        # Model bilgisi yoksa getprop ile al
        if not device.model:
            result = self.adb.shell(
                "getprop ro.product.model",
                device_serial=device.serial
            )
            if result.success:
                device.model = result.stdout.strip()
        
        return device
    
    def refresh(self) -> List[Device]:
        """Cihaz listesini yenile."""
        return self.get_devices()
    
    def wait_for_device(self, timeout: int = 30) -> bool:
        """
        Cihaz bağlanana kadar bekle.
        
        Args:
            timeout: Maksimum bekleme süresi (saniye)
            
        Returns:
            bool: Cihaz bulundu mu?
        """
        result = self.adb.execute(["wait-for-device"], timeout=timeout)
        return result.success
