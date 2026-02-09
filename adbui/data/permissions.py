"""
Android İzin Tanımları
======================
Sık kullanılan Android izinleri ve açıklamaları.
"""

PERMISSION_DESCRIPTIONS = {
    # Ağ ve İnternet
    "android.permission.INTERNET": "Tam İnternet Erişimi",
    "android.permission.ACCESS_NETWORK_STATE": "Ağ Bağlantılarını Görüntüleme",
    "android.permission.ACCESS_WIFI_STATE": "Wi-Fi Bağlantılarını Görüntüleme",
    "android.permission.CHANGE_WIFI_STATE": "Wi-Fi Durumunu Değiştirme",
    "android.permission.BLUETOOTH": "Bluetooth Cihazlarla Eşleşme",
    "android.permission.BLUETOOTH_ADMIN": "Bluetooth Ayarlarına Erişim",
    
    # Konum
    "android.permission.ACCESS_FINE_LOCATION": "Hassas Konum (GPS)",
    "android.permission.ACCESS_COARSE_LOCATION": "Yaklaşık Konum (Ağ)",
    "android.permission.ACCESS_BACKGROUND_LOCATION": "Arka Planda Konum Erişimi",
    
    # Kamera ve Mikrofon
    "android.permission.CAMERA": "Kamera Kullanımı",
    "android.permission.RECORD_AUDIO": "Ses Kaydetme (Mikrofon)",
    
    # Depolama
    "android.permission.READ_EXTERNAL_STORAGE": "Depolamayı Okuma",
    "android.permission.WRITE_EXTERNAL_STORAGE": "Depolamaya Yazma",
    "android.permission.MANAGE_EXTERNAL_STORAGE": "Tüm Dosyalara Erişim",
    "android.permission.READ_MEDIA_IMAGES": "Fotoğraf ve Videolara Erişim",
    "android.permission.READ_MEDIA_VIDEO": "Videolara Erişim",
    "android.permission.READ_MEDIA_AUDIO": "Ses Dosyalarına Erişim",
    
    # Kişiler ve Takvim
    "android.permission.READ_CONTACTS": "Kişileri Okuma",
    "android.permission.WRITE_CONTACTS": "Kişileri Düzenleme",
    "android.permission.READ_CALENDAR": "Takvim Etkinliklerini Okuma",
    "android.permission.WRITE_CALENDAR": "Takvim Etkinlikleri Ekleme",
    "android.permission.READ_CALL_LOG": "Arama Kayıtlarını Okuma",
    "android.permission.WRITE_CALL_LOG": "Arama Kayıtlarını Düzenleme",
    
    # Telefon ve SMS
    "android.permission.CALL_PHONE": "Telefon Araması Yapma",
    "android.permission.READ_PHONE_STATE": "Telefon Durumunu ve Kimliğini Okuma",
    "android.permission.SEND_SMS": "SMS Gönderme",
    "android.permission.READ_SMS": "SMS Okuma",
    "android.permission.RECEIVE_SMS": "SMS Alma",
    "android.permission.RECEIVE_MMS": "MMS Alma",
    
    # Sistem
    "android.permission.WAKE_LOCK": "Cihazın Uykuya Geçmesini Önleme",
    "android.permission.RECEIVE_BOOT_COMPLETED": "Başlangıçta Çalışma",
    "android.permission.FOREGROUND_SERVICE": "Ön Plan Hizmeti Çalıştırma",
    "android.permission.SYSTEM_ALERT_WINDOW": "Diğer Uygulamaların Üzerinde Görüntüleme",
    "android.permission.WRITE_SETTINGS": "Sistem Ayarlarını Değiştirme",
    "android.permission.KILL_BACKGROUND_PROCESSES": "Arka Plan İşlemlerini Kapatma",
    "android.permission.POST_NOTIFICATIONS": "Bildirim Gönderme",
    
    # Diğer
    "android.permission.VIBRATE": "Titreşim Kontrolü",
    "android.permission.FLASHLIGHT": "Feneri Açma/Kapama",
    "android.permission.NFC": "NFC İletişimi",
    "com.android.vending.BILLING": "Google Play Ödeme Hizmeti",
    "com.google.android.c2dm.permission.RECEIVE": "Bulut Bildirimleri Alma (FCM)",
}

# İzin -> AppOps eşleşmesi (Legacy uygulamalar için)
PERMISSION_TO_APPOPS = {
    # Konum
    "android.permission.ACCESS_FINE_LOCATION": "FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION": "COARSE_LOCATION",
    "android.permission.ACCESS_BACKGROUND_LOCATION": "FINE_LOCATION", # Genellikle FINE ile aynı gruptadır
    
    # Kamera / Mikrofon
    "android.permission.CAMERA": "CAMERA",
    "android.permission.RECORD_AUDIO": "RECORD_AUDIO",
    
    # Depolama (API < 30)
    "android.permission.READ_EXTERNAL_STORAGE": "READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE": "WRITE_EXTERNAL_STORAGE",
    
    # Medya (API >= 33)
    "android.permission.READ_MEDIA_IMAGES": "READ_MEDIA_IMAGES",
    "android.permission.READ_MEDIA_VIDEO": "READ_MEDIA_VIDEO",
    "android.permission.READ_MEDIA_AUDIO": "READ_MEDIA_AUDIO",
    
    # Kişiler
    "android.permission.READ_CONTACTS": "READ_CONTACTS",
    "android.permission.WRITE_CONTACTS": "WRITE_CONTACTS",
    
    # Takvim
    "android.permission.READ_CALENDAR": "READ_CALENDAR",
    "android.permission.WRITE_CALENDAR": "WRITE_CALENDAR",
    
    # Arama Kayıtları
    "android.permission.READ_CALL_LOG": "READ_CALL_LOG",
    "android.permission.WRITE_CALL_LOG": "WRITE_CALL_LOG",
    
    # Telefon
    "android.permission.CALL_PHONE": "CALL_PHONE",
    "android.permission.READ_PHONE_STATE": "READ_PHONE_STATE",
    
    # SMS
    "android.permission.SEND_SMS": "SEND_SMS",
    "android.permission.READ_SMS": "READ_SMS",
    "android.permission.RECEIVE_SMS": "RECEIVE_SMS",
    "android.permission.RECEIVE_MMS": "RECEIVE_MMS",
    
    # Diğer
    "android.permission.SYSTEM_ALERT_WINDOW": "SYSTEM_ALERT_WINDOW",
    "android.permission.WRITE_SETTINGS": "WRITE_SETTINGS",
    "android.permission.POST_NOTIFICATIONS": "POST_NOTIFICATION",
}

def get_permission_description(permission_name: str) -> str:
    """İzin adından açıklamasını döndürür."""
    return PERMISSION_DESCRIPTIONS.get(permission_name, permission_name)

def get_appops_for_permission(permission_name: str) -> str:
    """İzin adına karşılık gelen AppOps operasyonunu döndürür."""
    return PERMISSION_TO_APPOPS.get(permission_name)
