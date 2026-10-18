"""
Notifications module for turkce-otoduzeltici.
Handles Windows notifications, tray messages, and sound feedback safely across all environments.
"""

try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False


try:
    from PyQt6.QtCore import QObject, pyqtSignal
    class _NotificationBridge(QObject):
        notify_signal = pyqtSignal(str, str, int)
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False


class NotificationManager:
    def __init__(self, tray_icon=None):
        self.tray_icon = tray_icon
        self._bridge = None
        if QT_AVAILABLE:
            try:
                self._bridge = _NotificationBridge()
                self._bridge.notify_signal.connect(self._on_notify_qt)
            except Exception:
                self._bridge = None

    def set_tray_icon(self, tray_icon):
        """Set or update the system tray icon reference."""
        self.tray_icon = tray_icon

    def _on_notify_qt(self, title: str, message: str, duration_ms: int):
        """Thread-safe slot running exclusively on Qt main GUI event loop."""
        if self.tray_icon and hasattr(self.tray_icon, "showMessage"):
            try:
                from PyQt6.QtWidgets import QSystemTrayIcon
                self.tray_icon.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.MessageIcon.Information,
                    duration_ms
                )
            except Exception as e:
                print(f"Tray notification error: {e}")

    def show_notification(self, title: str, message: str, duration_sec: int = 4):
        """
        Show a desktop toast / balloon notification.
        Uses Qt signal to safely dispatch to main thread if available.
        """
        duration_ms = int(duration_sec * 1000)
        if self._bridge is not None:
            try:
                self._bridge.notify_signal.emit(title, message, duration_ms)
                return
            except Exception:
                pass

        # Direct fallback
        if self.tray_icon and hasattr(self.tray_icon, "showMessage"):
            try:
                from PyQt6.QtWidgets import QSystemTrayIcon
                self.tray_icon.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.MessageIcon.Information,
                    duration_ms
                )
                return
            except Exception as e:
                print(f"Tray notification error: {e}")

        # 2. Windows console fallback
        print(f"[Bildirim] {title}: {message}")

    def play_sound(self, sound_type: str = "success"):
        """Play a subtle system notification sound if sound is enabled."""
        if not SOUND_AVAILABLE:
            return
        try:
            if sound_type == "success":
                # Başarılı düzeltme: Yumuşak yükselen bildirim (1000Hz 60ms + 1400Hz 80ms)
                winsound.Beep(1000, 60)
                winsound.Beep(1400, 80)
            else:
                # Zaten doğru / bilgi: Tek hafif tık (1200Hz 50ms)
                winsound.Beep(1200, 50)
        except Exception:
            pass