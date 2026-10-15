"""
Windows Başlangıcında Otomatik Başlatma (Autostart - Registry Entegrasyonu).
Windows Kayıt Defteri (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run)
üzerinden uygulamanın sistem açılışında otomatik başlamasını yönetir.
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "TurkceOtoduzeltici"


def get_application_path() -> str:
    """Çalışan uygulamanın tam dosya yolunu döner (EXE veya Python betiği)."""
    if getattr(sys, "frozen", False):
        return sys.executable
    
    # Geliştirme ortamında dist/turkce-otoduzeltici.exe varsa onu tercih et
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dist_exe = os.path.join(base_dir, "dist", "turkce-otoduzeltici.exe")
    if os.path.exists(dist_exe):
        return dist_exe

    return os.path.abspath(sys.argv[0])


def set_autostart(enabled: bool, custom_exe_path: str = None) -> bool:
    """
    Windows başlangıcında otomatik başlatmayı açar veya kapatır.
    """
    if sys.platform != "win32":
        return False

    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )

        if enabled:
            exe_path = custom_exe_path or get_application_path()
            # Tırnak içine alarak boşluklu yollarda sorunsuz çalışmasını sağla
            cmd_value = f'"{exe_path}"'
            winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd_value)
            logger.info("Autostart etkinleştirildi: %s", cmd_value)
        else:
            try:
                winreg.DeleteValue(key, APP_REG_NAME)
                logger.info("Autostart devre dışı bırakıldı.")
            except FileNotFoundError:
                pass

        winreg.CloseKey(key)
        return True
    except Exception as e:
        logger.warning("Windows autostart ayarı güncellenemedi: %s", e)
        return False


def is_autostart_enabled() -> bool:
    """Uygulamanın Windows başlangıcında açılıp açılmayacağını kontrol eder."""
    if sys.platform != "win32":
        return False

    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_KEY_PATH,
            0,
            winreg.KEY_READ
        )
        _, _ = winreg.QueryValueEx(key, APP_REG_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
