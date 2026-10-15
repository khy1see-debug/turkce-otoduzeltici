"""
Windows Standalone Executable (.exe) Derleme Scripti.
PyInstaller kullanarak projeyi tek tıkla çalışan taşınabilir bir .exe dosyasına dönüştürür.
Kullanım:
  uv run --with pyinstaller python build_windows.py
"""

import os
import subprocess
import sys

# Windows konsolunda UnicodeEncodeError (cp1254) önlemi
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def build():
    print("=" * 65)
    print("[*] Turkce Otomatik Duzeltici - Windows .exe Derleyici")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "src", "icon.ico")
    data_path = os.path.join(base_dir, "src", "data", "turkish_words.txt.gz")

    if not os.path.exists(data_path):
        print(f"Hata: Sözlük dosyası bulunamadı: {data_path}")
        return 1

    target_name = "turkce-otoduzeltici"
    candidates = ["turkce-otoduzeltici", "turkce-otoduzeltici-v2", "turkce-otoduzeltici-v3"]
    for cand in candidates:
        exe_f = os.path.join(base_dir, "dist", f"{cand}.exe")
        if os.path.exists(exe_f):
            try:
                with open(exe_f, "a+b"):
                    pass
                target_name = cand
                break
            except OSError:
                continue
        else:
            target_name = cand
            break

    print(f"[*] Hedef Çıktı Dosyası: {target_name}.exe")

    # Spec dosyasını temizle
    for s_name in ["turkce-otoduzeltici.spec", "turkce-otoduzeltici-v2.spec", "turkce-otoduzeltici-v3.spec"]:
        s_path = os.path.join(base_dir, s_name)
        if os.path.exists(s_path):
            try:
                os.remove(s_path)
            except OSError:
                pass

    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        f"--name={target_name}",
        "--windowed",       # Konsol penceresini gizle (GUI & Tray için)
        "--onefile",        # Tek tıkla çalışan bağımsız tek dosya
        "--noconfirm",
        "--clean",
        f"--add-data={data_path};src/data",
        f"--add-data={icon_path};src",
        "--hidden-import=keyboard",
        "--hidden-import=pyperclip",
        "--hidden-import=wordfreq",
        "--hidden-import=regex",
        "--hidden-import=PyQt6",
        "--collect-all=src",
        "--collect-all=wordfreq",
        "--collect-all=regex",
        os.path.join(base_dir, "src", "desktop_entry.py")
    ]

    if os.path.exists(icon_path):
        pyinstaller_cmd.insert(4, f"--icon={icon_path}")

    print("PyInstaller çalıştırılıyor (bu işlem 1-2 dakika sürebilir)...")
    print(" ".join(pyinstaller_cmd))

    ret = subprocess.call(pyinstaller_cmd)
    if ret == 0:
        exe_path = os.path.join(base_dir, "dist", f"{target_name}.exe")
        print("\n" + "=" * 65)
        print("[+] Derleme Basarili!")
        print(f"[>] Calistirilabilir EXE: {exe_path}")
        print("=" * 65)
    else:
        print("\n[-] Derleme sirasinda bir hata olustu.")
    return ret

if __name__ == "__main__":
    sys.exit(build())
