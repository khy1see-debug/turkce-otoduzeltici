"""
Windows Standalone Executable (.exe) Derleme Scripti.
PyInstaller kullanarak projeyi tek tıkla çalışan taşınabilir bir .exe dosyasına dönüştürür.
Kullanım:
  uv run --with pyinstaller python build_windows.py
"""

import os
import subprocess
import sys

def build():
    print("=" * 65)
    print("🇹🇷 Türkçe Otomatik Düzeltici - Windows .exe Derleyici")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "src", "icon.ico")
    data_path = os.path.join(base_dir, "src", "data", "turkish_words.txt.gz")

    if not os.path.exists(data_path):
        print(f"Hata: Sözlük dosyası bulunamadı: {data_path}")
        return 1

    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=turkce-otoduzeltici",
        "--windowed",  # Konsol penceresini gizle (GUI & Tray için)
        "--onedir",    # Hızlı açılış için onedir veya --onefile
        "--noconfirm",
        f"--add-data={data_path};src/data",
        os.path.join(base_dir, "src", "main_window.py")
    ]

    if os.path.exists(icon_path):
        pyinstaller_cmd.insert(4, f"--icon={icon_path}")

    print("PyInstaller çalıştırılıyor...")
    print(" ".join(pyinstaller_cmd))

    ret = subprocess.call(pyinstaller_cmd)
    if ret == 0:
        print("\n✅ Başarılı! Çıktı klasörü: dist/turkce-otoduzeltici")
    else:
        print("\n❌ Derleme sırasında bir hata oluştu.")
    return ret

if __name__ == "__main__":
    sys.exit(build())
