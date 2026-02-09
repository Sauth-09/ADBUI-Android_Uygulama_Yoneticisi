<<<<<<< HEAD
# ADBUI - Android Debloat ve Kontrol Aracı

## Gereksinimler

```
PySide6>=6.5.0
openai>=1.0.0
```

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

```bash
cd platform-tools
python main.py
```

## Özellikler

- 📱 USB ile bağlı Android cihazları otomatik algılar
- 📦 Sistem, kullanıcı ve devre dışı paketleri listeler
- 🗑️ Paket kaldırma (user 0)
- ❄️ Paket dondurma/etkinleştirme
- ⚙️ AppOps yönetimi (arka plan, wake lock)
- 💤 Standby Bucket ayarları
- 🤖 AI tabanlı paket analizi (OpenAI)
- 🎨 Modern koyu tema arayüz

## Yapı

```
platform-tools/
├── adb.exe            # Android Platform Tools
├── main.py            # Giriş noktası
├── requirements.txt   # Bağımlılıklar
└── adbui/             # Ana paket
    ├── core/          # ADB servisleri
    ├── ui/            # PySide6 arayüz
    ├── ai/            # OpenAI entegrasyonu
    ├── models/        # Veri modelleri
    ├── utils/         # Yardımcı araçlar
    └── data/          # Cache ve veri
```

## Lisans

MIT License
=======
# ADBUI-Ak-ll-Uygulama-Y-neticisi
android adb ile normalde kaldırılamayan uygulamaları kaldır, arka planı kısıtla,dondur, hengi sistem uygulamasının ne işe yaradığını öğren.
>>>>>>> a4aa34683d58fc8b669dfdb4a76231492555bcdb
