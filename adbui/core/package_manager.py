"""
Package Manager Module
======================
Android paket yönetimi - listeleme, kaldırma, dondurma işlemleri.
"""

import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from .adb_service import ADBService

logger = logging.getLogger(__name__)


class PackageCategory(Enum):
    """Paket kategorisi."""
    SYSTEM = "system"
    USER = "user"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class StandbyBucket(Enum):
    """Standby bucket seviyeleri."""
    ACTIVE = "active"
    WORKING_SET = "working_set"
    FREQUENT = "frequent"
    RARE = "rare"
    RESTRICTED = "restricted"


@dataclass
class AppOpsState:
    """AppOps izin durumu."""
    run_in_background: Optional[str] = None  # allow/deny
    wake_lock: Optional[str] = None  # allow/deny


@dataclass
class Package:
    """Android paketi."""
    name: str
    category: PackageCategory = PackageCategory.UNKNOWN
    is_enabled: bool = True
    is_critical: bool = False
    version_name: Optional[str] = None
    version_code: Optional[int] = None
    install_time: Optional[str] = None
    appops: AppOpsState = field(default_factory=AppOpsState)
    standby_bucket: Optional[StandbyBucket] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    
    @property
    def display_name(self) -> str:
        """Kısa görüntüleme adı."""
        # com.samsung.android.app.tips -> tips
        parts = self.name.split('.')
        return parts[-1] if parts else self.name
    
    @property
    def vendor(self) -> Optional[str]:
        """Paket üreticisi (com.samsung -> Samsung)."""
        parts = self.name.split('.')
        if len(parts) >= 2:
            vendor = parts[1].lower()
            vendor_map = {
                'samsung': 'Samsung',
                'google': 'Google',
                'android': 'Android',
                'huawei': 'Huawei',
                'xiaomi': 'Xiaomi',
                'miui': 'MIUI',
                'oppo': 'OPPO',
                'vivo': 'Vivo',
                'oneplus': 'OnePlus',
                'facebook': 'Facebook',
                'meta': 'Meta',
                'microsoft': 'Microsoft',
            }
            return vendor_map.get(vendor, vendor.capitalize())
        return None


class PackageManager:
    """
    Paket yönetim sınıfı.
    
    Android cihazlardaki paketleri listeler ve yönetir.
    """
    
    # Kritik sistem paketleri - kaldırılmamalı
    CRITICAL_PACKAGES = {
        'com.android.systemui',
        'com.android.settings',
        'com.android.phone',
        'com.android.launcher',
        'com.android.launcher3',
        'com.android.vending',  # Play Store
        'com.google.android.gms',  # Google Play Services
        'com.android.providers.settings',
        'com.android.providers.contacts',
        'com.android.providers.telephony',
        'com.android.inputmethod.latin',
        'com.android.packageinstaller',
        'com.android.shell',
        'android',
    }
    
    def __init__(self, adb_service: ADBService, device_serial: Optional[str] = None):
        """
        PackageManager'ı başlat.
        
        Args:
            adb_service: ADB servis instance'ı
            device_serial: Hedef cihaz seri numarası
        """
        self.adb = adb_service
        self.device_serial = device_serial
    
    def set_device(self, serial: str):
        """Hedef cihazı ayarla."""
        self.device_serial = serial
    
    def get_all_packages(self) -> List[Package]:
        """Tüm paketleri al (sistem + kullanıcı + devre dışı)."""
        packages: Dict[str, Package] = {}
        
        # Sistem paketleri
        system_packages = self._get_packages_by_flag("-s")
        for name in system_packages:
            packages[name] = Package(
                name=name,
                category=PackageCategory.SYSTEM,
                is_critical=name in self.CRITICAL_PACKAGES
            )
        
        # Kullanıcı paketleri (3rd party)
        user_packages = self._get_packages_by_flag("-3")
        for name in user_packages:
            packages[name] = Package(
                name=name,
                category=PackageCategory.USER
            )
        
        # Devre dışı paketler
        disabled_packages = self._get_packages_by_flag("-d")
        for name in disabled_packages:
            if name in packages:
                packages[name].is_enabled = False
                packages[name].category = PackageCategory.DISABLED
            else:
                packages[name] = Package(
                    name=name,
                    category=PackageCategory.DISABLED,
                    is_enabled=False
                )
        
        result = list(packages.values())
        logger.info(f"Toplam {len(result)} paket bulundu")
        return result
    
    def _get_packages_by_flag(self, flag: str) -> List[str]:
        """Belirli bir flag ile paket listesi al."""
        result = self.adb.shell(
            f"pm list packages {flag}",
            device_serial=self.device_serial
        )
        
        if not result.success:
            logger.error(f"Paket listesi alınamadı ({flag}): {result.stderr}")
            return []
        
        packages = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith('package:'):
                packages.append(line[8:])  # 'package:' prefix'ini kaldır
        
        return packages
    
    def uninstall(self, package_name: str, user_id: int = 0) -> bool:
        """
        Paketi kullanıcı için kaldır.
        
        Args:
            package_name: Paket adı
            user_id: Kullanıcı ID (varsayılan 0)
            
        Returns:
            bool: İşlem başarılı mı?
        """
        if package_name in self.CRITICAL_PACKAGES:
            logger.warning(f"Kritik paket kaldırılamaz: {package_name}")
            return False
        
        result = self.adb.shell(
            f"pm uninstall --user {user_id} {package_name}",
            device_serial=self.device_serial
        )
        
        success = result.success and "Success" in result.stdout
        if success:
            logger.info(f"Paket kaldırıldı: {package_name}")
        else:
            logger.error(f"Paket kaldırılamadı: {package_name} - {result.stderr}")
        
        return success
    
    def disable(self, package_name: str, user_id: int = 0) -> bool:
        """
        Paketi devre dışı bırak (dondur).
        
        Args:
            package_name: Paket adı
            user_id: Kullanıcı ID
            
        Returns:
            bool: İşlem başarılı mı?
        """
        result = self.adb.shell(
            f"pm disable-user --user {user_id} {package_name}",
            device_serial=self.device_serial
        )
        
        success = result.success and "disabled" in result.stdout.lower()
        if success:
            logger.info(f"Paket donduruldu: {package_name}")
        else:
            logger.error(f"Paket dondurulamadı: {package_name} - {result.stderr}")
        
        return success
    
    def enable(self, package_name: str) -> bool:
        """
        Paketi etkinleştir.
        
        Args:
            package_name: Paket adı
            
        Returns:
            bool: İşlem başarılı mı?
        """
        result = self.adb.shell(
            f"pm enable {package_name}",
            device_serial=self.device_serial
        )
        
        success = result.success and "enabled" in result.stdout.lower()
        if success:
            logger.info(f"Paket etkinleştirildi: {package_name}")
        else:
            logger.error(f"Paket etkinleştirilemedi: {package_name} - {result.stderr}")
        
        return success
    
    def set_appops(
        self, 
        package_name: str, 
        operation: str, 
        mode: str
    ) -> bool:
        """
        AppOps izni ayarla.
        
        Args:
            package_name: Paket adı
            operation: İzin adı (RUN_IN_BACKGROUND, WAKE_LOCK, vb.)
            mode: İzin modu (allow, deny, ignore, default)
            
        Returns:
            bool: İşlem başarılı mı?
        """
        result = self.adb.shell(
            f"appops set {package_name} {operation} {mode}",
            device_serial=self.device_serial
        )
        
        if result.success:
            logger.info(f"AppOps ayarlandı: {package_name} {operation}={mode}")
        else:
            logger.error(f"AppOps ayarlanamadı: {result.stderr}")
        
        return result.success
    
    def set_standby_bucket(
        self, 
        package_name: str, 
        bucket: StandbyBucket
    ) -> bool:
        """
        Standby bucket ayarla.
        
        Args:
            package_name: Paket adı
            bucket: Hedef bucket
            
        Returns:
            bool: İşlem başarılı mı?
        """
        result = self.adb.shell(
            f"am set-standby-bucket {package_name} {bucket.value}",
            device_serial=self.device_serial
        )
        
        if result.success:
            logger.info(f"Standby bucket ayarlandı: {package_name} -> {bucket.value}")
        else:
            logger.error(f"Standby bucket ayarlanamadı: {result.stderr}")
        
        return result.success
    
    def get_package_info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """
        Paket detay bilgilerini al.
        
        Args:
            package_name: Paket adı
            
        Returns:
            Dict: Paket bilgileri veya None
        """
        result = self.adb.shell(
            f"dumpsys package {package_name}",
            device_serial=self.device_serial,
            timeout=10
        )
        
        if not result.success:
            return None
        
        info = {
            'name': package_name,
            'raw_info': result.stdout
        }
        
        # Version bilgisini parse et
        version_match = re.search(r'versionName=([^\s]+)', result.stdout)
        if version_match:
            info['version_name'] = version_match.group(1)
        
        code_match = re.search(r'versionCode=(\d+)', result.stdout)
        if code_match:
            info['version_code'] = int(code_match.group(1))
        
        return info
    
    def get_advanced_details(self, package_name: str) -> Dict[str, str]:
        """
        Paket hakkında gelişmiş detayları al (AppOps, Standby, WakeLock, Versiyon, Tarih).
        """
        details = {
            "run_in_background": "Yükleniyor...",
            "wake_lock": "Yükleniyor...",
            "standby_bucket": "Yükleniyor...",
            "version": "Yükleniyor...",
            "install_time": "Yükleniyor..."
        }
        
        try:
            # 1. RUN_IN_BACKGROUND
            res = self.adb.shell(f"cmd appops get {package_name} RUN_IN_BACKGROUND", device_serial=self.device_serial)
            if res.success:
                stdout = res.stdout.lower()
                if "allow" in stdout: details["run_in_background"] = "✅ İzin Verildi"
                elif "ignore" in stdout: details["run_in_background"] = "⚠️ Yoksay (Ignore)"
                elif "deny" in stdout: details["run_in_background"] = "⛔ Engellendi"
                else: details["run_in_background"] = "❓ Bilinmiyor"
            
            # 2. WAKE_LOCK
            res = self.adb.shell(f"cmd appops get {package_name} WAKE_LOCK", device_serial=self.device_serial)
            if res.success:
                stdout = res.stdout.lower()
                if "allow" in stdout: details["wake_lock"] = "✅ İzin Verildi"
                elif "ignore" in stdout: details["wake_lock"] = "⚠️ Yoksay (Ignore)"
                elif "deny" in stdout: details["wake_lock"] = "⛔ Engellendi"
                else: details["wake_lock"] = "❓ Bilinmiyor"
                
            # 3. STANDBY BUCKET
            res = self.adb.shell(f"am get-standby-bucket {package_name}", device_serial=self.device_serial)
            if res.success:
                bucket_code = res.stdout.strip()
                bucket_map = {
                    "5": "💎 Muaf (Exempted)",
                    "10": "🟢 Aktif (Active)",
                    "20": "🟡 Çalışma Grubu (Working)",
                    "30": "🟠 Sık (Frequent)",
                    "40": "🔴 Nadir (Rare)",
                    "45": "⛔ Kısıtlı (Restricted)",
                    "50": "❄️ Hiç (Never)"
                }
                details["standby_bucket"] = bucket_map.get(bucket_code, f"Bilinmiyor ({bucket_code})")
            
            # 4. Versiyon ve Yükleme Zamanı (Dumpsys)
            res = self.adb.shell(f"dumpsys package {package_name}", device_serial=self.device_serial)
            if res.success:
                import re
                v_match = re.search(r"versionName=([^\r\n]+)", res.stdout)
                if v_match: details["version"] = v_match.group(1)
                
                t_match = re.search(r"firstInstallTime=([^\r\n]+)", res.stdout)
                if t_match: details["install_time"] = t_match.group(1)
                
        except Exception as e:
            logger.error(f"Gelişmiş detay hatası: {e}")
            
        return details
