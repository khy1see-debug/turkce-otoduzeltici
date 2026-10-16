"""
Türkçe Otomatik Düzeltici - Birleşik Windows Masaüstü Başlatıcısı.
Çift tıklandığında: GUI Stüdyosu + Sistem Tepsisi (Alt+Q) + Ctrl+Z izleyicisi başlar.
Argüman verildiğinde: CLI veya Web arayüzü moduna geçer.
"""
import sys
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Safe logging for PyInstaller --windowed mode
log_dir = os.path.expanduser(r"~\AppData\Roaming\turkce-otoduzeltici")
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "app.log")

class SafeLogWriter:
    def __init__(self, filepath, fallback=None):
        self.filepath = filepath
        self.fallback = fallback

    def write(self, s):
        if self.fallback:
            try:
                self.fallback.write(s)
            except Exception:
                pass
        try:
            with open(self.filepath, "a", encoding="utf-8", errors="replace") as f:
                f.write(s)
        except Exception:
            pass

    def flush(self):
        if self.fallback and hasattr(self.fallback, "flush"):
            try:
                self.fallback.flush()
            except Exception:
                pass

sys.stdout = SafeLogWriter(log_path, sys.stdout)
sys.stderr = SafeLogWriter(log_path, sys.stderr)

def excepthook(exc_type, exc_value, exc_tb):
    import traceback
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"[KRİTİK HATA] {tb}", file=sys.stderr)

sys.excepthook = excepthook
import threading
threading.excepthook = lambda args: excepthook(args.exc_type, args.exc_value, args.exc_traceback)

_single_instance_mutex = None

def ensure_single_instance():
    """Win32 Named Mutex ile uygulamanın tek bir örneğinin çalışmasını sağlar."""
    global _single_instance_mutex
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex_name = "Global\\TurkceOtomatikDuzeltici_App_Mutex_v1"
        _single_instance_mutex = kernel32.CreateMutexW(None, False, mutex_name)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            print("[!] Halihazırda çalışan bir Türkçe Otomatik Düzeltici kopyası mevcut. Çıkılıyor.")
            sys.exit(0)
        return True
    except Exception:
        return True

def run():
    # Argüman kontrolü (CLI / Web / Parametreler)
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-psn"):
        from src.cli import main as cli_main
        cli_main()
    else:
        # Masaüstü GUI & Sistem Tepsisi Modu: Eski kopyaları temizle ve başlat
        ensure_single_instance()
        from src.app_tray import main as tray_main
        tray_main()

if __name__ == "__main__":
    run()
