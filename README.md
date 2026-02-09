# ADBUI - Android Debloat ve Kontrol Aracı

Profesyonel Android uygulama yönetim aracı. ADB kullanarak normalde kaldırılamayan uygulamaları kaldır, arka planı kısıtla, dondur ve her sistem uygulamasının ne işe yaradığını öğren.

## Özellikler

- 📱 USB ile bağlı Android cihazları otomatik algılar
- 📦 Sistem, kullanıcı ve devre dışı paketleri listeler
- 🗑️ Paket kaldırma (user 0)
- ❄️ Paket dondurma/etkinleştirme
- ⚙️ AppOps yönetimi (arka plan, wake lock)
- 💤 Standby Bucket ayarları
- 🤖 AI tabanlı paket analizi (Google Gemini - Ücretsiz)
- 🎨 Modern koyu tema arayüz

## Kurulum

```bash
pip install -r requirements.txt
```

## Kullanım

```bash
cd platform-tools
python main.py
```

## Yapı

```
platform-tools/
├── adb.exe            # Android Platform Tools
├── main.py            # Giriş noktası
├── requirements.txt   # Bağımlılıklar
└── adbui/             # Ana paket
    ├── core/          # ADB servisleri
    ├── ui/            # PySide6 arayüz
    ├── ai/            # Google Gemini entegrasyonu
    ├── models/        # Veri modelleri
    ├── utils/         # Yardımcı araçlar
    └── data/          # Cache ve veri
```

## AI Özellikleri

**Google Gemini API (Ücretsiz)** kullanarak her paket için:
- Paketin ne işe yaradığını açıklar
- Kaldırmanın güvenli olup olmadığını belirtir
- Kaldırılırsa olası etkileri anlatır
- Alternatif yöntemler önerir (dondurma, appops)

API anahtarı almak için: [Google AI Studio](https://aistudio.google.com/apikey)

## Lisans

MIT License
