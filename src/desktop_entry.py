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

def excepthook(exc_type, exc_value, exc_tb):
    import traceback
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"Kritik Hata:\n{tb}", file=sys.stderr)

sys.excepthook = excepthook

def run():
    # Argüman kontrolü (CLI / Web / Parametreler)
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-psn"):
        from src.cli import main as cli_main
        cli_main()
    else:
        # Masaüstü GUI & Sistem Tepsisi Modu
        from src.app_tray import main as tray_main
        tray_main()

if __name__ == "__main__":
    run()
