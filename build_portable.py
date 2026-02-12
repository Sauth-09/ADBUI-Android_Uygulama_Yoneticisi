
import os
import shutil
import subprocess
import sys
from pathlib import Path

def build():
    print("🚀 ADBUI Derleme İşlemi Başlatılıyor...")
    
    # Bağımlılıkları kontrol et
    try:
        import PyInstaller
    except ImportError:
        print("📦 PyInstaller bulunamadı, yükleniyor...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 1. Ortamı Hazırla
    build_dir = Path("build_dist")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()

    # 2. PyInstaller SPEC Dosyası İçeriği
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Dahil edilecek dosyalar (Binaries ve Datas)
added_files = [
    ('adbui/assets/*', 'adbui/assets'),
    ('logo.ico', '.'),
]

added_binaries = [
    ('adb.exe', '.'),
    ('AdbWinApi.dll', '.'),
    ('AdbWinUsbApi.dll', '.'),
    ('libwinpthread-1.dll', '.'),
    ('sqlite3.exe', '.'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=added_binaries,
    datas=added_files,
    hiddenimports=['adbui', 'google-genai'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# PORTABLE (KLASÖRLÜ) VERSİYON
exe_dir = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ADBUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',
)
coll = COLLECT(
    exe_dir,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ADBUI_Portable_v2',
)

# KURULUM / STANDALONE (TEK EXE) VERSİYON - Şimdilik devre dışı (Hız ve test amaçlı)
# exe_single = EXE(
#     pyz,
#     a.scripts,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     [],
#     name='ADBUI_Setup',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     runtime_tmpdir=None,
#     console=False,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
# )
"""
    
    spec_file = Path("adbui.spec")
    spec_file.write_text(spec_content, encoding="utf-8")

    # 3. PyInstaller'ı Çalıştır
    print("🔨 PyInstaller çalıştırılıyor (Bu işlem birkaç dakika sürebilir)...")
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "--noconfirm", "adbui.spec"])

    print("\n✅ Derleme Tamamlandı!")
    print(f"📂 Portable Klasör: {Path('dist/ADBUI_Portable_v2').absolute()}")
    # print(f"📄 Tek EXE (Kurulum): {Path('dist/ADBUI_Setup.exe').absolute()}")

if __name__ == "__main__":
    build()
