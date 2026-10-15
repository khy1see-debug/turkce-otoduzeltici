"""
Notifications module for turkce-otoduzeltici.
Handles Windows notifications, tray messages, and sound feedback safely across all environments.
"""

import sys

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False


class NotificationManager:
    def __init__(self, tray_icon=None):
        self.tray_icon = tray_icon

    def set_tray_icon(self, tray_icon):
        """Set or update the system tray icon reference."""
        self.tray_icon = tray_icon

    def show_notification(self, title: str, message: str, duration_sec: int = 4):
        """
        Show a desktop toast / balloon notification.
        Uses PyQt6 tray icon if available, otherwise falls back gracefully.
        """
        # 1. PyQt6 QSystemTrayIcon (en kararlı ve sorunsuz yöntem)
        if self.tray_icon and hasattr(self.tray_icon, "showMessage"):
            try:
                from PyQt6.QtWidgets import QSystemTrayIcon
                self.tray_icon.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.MessageIcon.Information,
                    int(duration_sec * 1000)
                )
                return
            except Exception as e:
                print(f"Tray notification error: {e}")

        # 2. Windows PowerShell / BurntToast fallback
        if sys.platform == "win32":
            try:
                # Kısa console log
                print(f"[Bildirim] {title}: {message}")
            except Exception:
                pass
        else:
            print(f"[Bildirim] {title}: {message}")

    def play_sound(self):
        """Play a subtle system notification sound if sound is enabled."""
        if not SOUND_AVAILABLE:
            return
        try:
            # Yumuşak sistem bildirimi sesi (1200 Hz, 80ms)
            winsound.Beep(1200, 80)
        except Exception:
            pass