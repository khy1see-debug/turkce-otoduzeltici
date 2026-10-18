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

def check_already_running_and_show():
    """Eğer uygulama arka planda zaten açıksa, REST API ile penceresini öne getirir ve True döner."""
    import urllib.request
    try:
        req = urllib.request.Request("http://127.0.0.1:8765/api/show", headers={"User-Agent": "Launcher"})
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            if resp.status == 200:
                print("[+] Mevcut uygulama penceresi öne getirildi.")
                return True
    except Exception:
        pass
    return False

def _ensure_interactive_default_desktop():
    """
    Eğer uygulama bir arka plan terminalinden / sandbox masaüstünden (örn: exebox)
    başlatıldıysa, pencerelerin kullanıcının gerçek ekranında (WinSta0\\Default)
    görünmesi için kendisini Default masaüstünde yeniden başlatır veya bağlar.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        cur_tid = kernel32.GetCurrentThreadId()
        h_desk = user32.GetThreadDesktop(cur_tid)
        buf = ctypes.create_unicode_buffer(256)
        user32.GetUserObjectInformationW(h_desk, 2, buf, 512, None)
        desk_name = buf.value

        if desk_name and desk_name.lower() != "default":
            # Önce mevcut thread'i doğrudan Default masaüstüne bağlamayı dene
            h_default = user32.OpenDesktopW("Default", 0, False, 0x10000000)  # GENERIC_ALL
            if h_default:
                if user32.SetThreadDesktop(h_default):
                    return
                # Eğer thread zaten hook/pencere açtıysa CreateProcessW ile lpDesktop='WinSta0\\Default' olarak başlat
                class STARTUPINFOW(ctypes.Structure):
                    _fields_ = [
                        ("cb", wintypes.DWORD),
                        ("lpReserved", wintypes.LPWSTR),
                        ("lpDesktop", wintypes.LPWSTR),
                        ("lpTitle", wintypes.LPWSTR),
                        ("dwX", wintypes.DWORD),
                        ("dwY", wintypes.DWORD),
                        ("dwXSize", wintypes.DWORD),
                        ("dwYSize", wintypes.DWORD),
                        ("dwXCountChars", wintypes.DWORD),
                        ("dwYCountChars", wintypes.DWORD),
                        ("dwFillAttribute", wintypes.DWORD),
                        ("dwFlags", wintypes.DWORD),
                        ("wShowWindow", wintypes.WORD),
                        ("cbReserved2", wintypes.WORD),
                        ("lpReserved2", ctypes.POINTER(wintypes.BYTE)),
                        ("hStdInput", wintypes.HANDLE),
                        ("hStdOutput", wintypes.HANDLE),
                        ("hStdError", wintypes.HANDLE),
                    ]

                class PROCESS_INFORMATION(ctypes.Structure):
                    _fields_ = [
                        ("hProcess", wintypes.HANDLE),
                        ("hThread", wintypes.HANDLE),
                        ("dwProcessId", wintypes.DWORD),
                        ("dwThreadId", wintypes.DWORD),
                    ]

                si = STARTUPINFOW()
                si.cb = ctypes.sizeof(STARTUPINFOW)
                si.lpDesktop = "WinSta0\\Default"
                pi = PROCESS_INFORMATION()
                ctypes.windll.kernel32.GetCommandLineW.restype = wintypes.LPWSTR
                cmd_str = ctypes.windll.kernel32.GetCommandLineW()
                if kernel32.CreateProcessW(
                    None, cmd_str, None, None, False, 0x00000010, None, None, ctypes.byref(si), ctypes.byref(pi)
                ):
                    sys.exit(0)
    except Exception:
        pass


def run():
    # Argüman kontrolü (CLI / Web / Parametreler)
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-psn"):
        from src.cli import main as cli_main
        cli_main()
    else:
        _ensure_interactive_default_desktop()
        # Masaüstü GUI & Sistem Tepsisi Modu: Zaten açıksa öne getir, yoksa başlat
        if check_already_running_and_show():
            sys.exit(0)
        from src.app_tray import main as tray_main
        tray_main()

if __name__ == "__main__":
    run()
