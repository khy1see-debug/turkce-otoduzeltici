"""
System Tray Application for Turkish Auto-Corrector.
Provides a background service with global hotkey correction (default Alt+Q),
clipboard preservation, undo detection (Ctrl+Z), and tray menu.
"""
import sys
import os
import time
import pyperclip
import keyboard
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt

# Import managers
from src import settings_manager
from src import self_learning
from src.grammar import fix_sentence
from src.dictionary import refresh_personal_dictionary, _resolved_personal_dict_path
from src.statistics_manager import StatisticsManager
from src.notifications import NotificationManager

# Global flag to enable/disable correction
correction_active = True

# Global variable to track recent corrections for undo detection
_last_correction_time = 0.0
_last_correction_original = ""
_last_correction_corrected = ""

# Preload dictionaries on startup
refresh_personal_dictionary(force=True)

# Initialize managers
_stats_manager = StatisticsManager()
_notification_manager = NotificationManager()


def handle_ctrl_z():
    """Handle Ctrl+Z key press to undo recent correction."""
    global _last_correction_time, _last_correction_original, _last_correction_corrected

    current_time = time.time()
    if _last_correction_time > 0 and (current_time - _last_correction_time) <= 2.5:
        if _last_correction_original and _last_correction_corrected:
            self_learning.record_rejection(_last_correction_corrected)
            _notification_manager.show_notification(
                "↩️ Düzeltme Geri Alındı",
                f"'{_last_correction_corrected}' ➜ '{_last_correction_original}'"
            )

        _last_correction_time = 0.0
        _last_correction_original = ""
        _last_correction_corrected = ""
        return True

    return False


def setup_undo_detection():
    """Set up global Ctrl+Z hook for undo detection."""
    try:
        keyboard.add_hotkey('ctrl+z', handle_ctrl_z)
    except Exception as e:
        print(f"Undo hook notice: {e}")


def create_icon_image() -> QIcon:
    """Load icon from file or generate a beautiful modern 64x64 icon."""
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        return QIcon(icon_path)

    # 64x64 modern kırmızı-beyaz yuvarlatılmış Türkçe Otodüzeltici ikonu
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Arka plan yuvarlak daire (Türk bayrağı kırmızısı)
    p.setBrush(QColor(227, 10, 23))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(2, 2, 60, 60, 16, 16)

    # Beyaz şık "TR" yazısı
    p.setPen(QColor(255, 255, 255))
    font = QFont("Segoe UI", 22, QFont.Weight.Bold)
    p.setFont(font)
    p.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "TR")
    p.end()

    try:
        pixmap.save(icon_path, "ICO")
    except Exception:
        pass

    return QIcon(pixmap)


def correct_selected_text():
    """Get selected text, correct it, and replace the selection."""
    global correction_active, _last_correction_time, _last_correction_original, _last_correction_corrected
    if not correction_active:
        return

    # Panonun mevcut içeriğini yedekle
    try:
        original_clipboard = pyperclip.paste()
    except Exception:
        original_clipboard = ""

    try:
        # Seçili metni panoya kopyala (Ctrl+C)
        keyboard.send('ctrl+c')
        time.sleep(0.08)
        selected_text = pyperclip.paste()

        if not selected_text or not selected_text.strip():
            return

        # Metni akıllı dilbilgisi motoru ile düzelt
        corrected_text = fix_sentence(selected_text)

        if corrected_text != selected_text:
            # Düzeltilmiş metni panoya koyup yapıştır (Ctrl+V)
            pyperclip.copy(corrected_text)
            time.sleep(0.05)
            keyboard.send('ctrl+v')

            # Geri alma takibi için kaydet
            _last_correction_time = time.time()
            _last_correction_original = selected_text
            _last_correction_corrected = corrected_text

            # İstatistik ve Öz-öğrenmeye kaydet
            _stats_manager.record_correction(selected_text, corrected_text)
            self_learning.record_correction(selected_text, corrected_text)

            # Bildirim ve ses
            settings = settings_manager.load_settings()
            if settings.get("sound_toggle", True):
                _notification_manager.play_sound()

            _notification_manager.show_notification(
                "✨ Metin Düzeltildi",
                f"{selected_text} ➜ {corrected_text}"
            )

            # Bir süre sonra orijinal panoyu geri yükle
            time.sleep(0.15)
            if original_clipboard:
                pyperclip.copy(original_clipboard)
    except Exception as e:
        print(f"Düzeltme hatası: {e}")
        if original_clipboard:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass


class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app_icon = create_icon_image()
        self.setIcon(self.app_icon)
        self.setToolTip("Türkçe Otomatik Düzeltici (0-Token)")

        _notification_manager.set_tray_icon(self)

        self.menu = QMenu()
        self.setup_menu()
        self.setContextMenu(self.menu)
        self.activated.connect(self.on_tray_activated)

        # Ayarları yükle ve kısayolu kaydet
        self.settings = settings_manager.load_settings()
        self.current_hotkey = self.settings.get("hotkey", "alt+q")
        self.register_hotkey(self.current_hotkey)
        self.main_window = None

    def setup_menu(self):
        # Düzeltme Stüdyosu & Ayarlar
        self.show_settings_action = QAction("✨ Düzeltme Stüdyosu & Ayarlar", self)
        self.show_settings_action.triggered.connect(self.show_settings_window)
        self.menu.addAction(self.show_settings_action)

        # Kişisel Sözlük
        self.personal_dict_action = QAction("📖 Kişisel Sözlüğü Aç", self)
        self.personal_dict_action.triggered.connect(self.show_personal_dictionary)
        self.menu.addAction(self.personal_dict_action)

        self.menu.addSeparator()

        # Düzeltmeyi Durdur/Başlat
        self.toggle_correction_action = QAction("⏸️ Kısayolu Durdur", self)
        self.toggle_correction_action.setCheckable(True)
        self.toggle_correction_action.setChecked(True)
        self.toggle_correction_action.triggered.connect(self.toggle_correction)
        self.menu.addAction(self.toggle_correction_action)

        self.menu.addSeparator()

        # Çıkış
        self.exit_action = QAction("❌ Çıkış", self)
        self.exit_action.triggered.connect(self.exit_application)
        self.menu.addAction(self.exit_action)

    def show_settings_window(self):
        """Düzeltme Stüdyosu ve Ayarlar Penceresini Aç."""
        from src.main_window import MainWindow
        if self.main_window is None:
            self.main_window = MainWindow(tray_icon=self)
        self.main_window.show()
        self.main_window.activateWindow()
        self.main_window.raise_()

    def show_personal_dictionary(self):
        """Kişisel sözlük dosyasını varsayılan editörde aç."""
        try:
            dict_path = _resolved_personal_dict_path()
            os.makedirs(os.path.dirname(dict_path), exist_ok=True)
            if not os.path.exists(dict_path):
                open(dict_path, 'a', encoding='utf-8').close()
            if sys.platform == "win32":
                os.system(f'notepad "{dict_path}"')
            else:
                os.system(f'xdg-open "{dict_path}"')
        except Exception as e:
            print(f"Kişisel sözlük açılamadı: {e}")

    def toggle_correction(self, checked):
        """Düzeltme kısayolunu aktif/pasif yap."""
        global correction_active
        correction_active = checked
        self.toggle_correction_action.setText("⏸️ Kısayolu Durdur" if correction_active else "▶️ Kısayolu Başlat")
        _notification_manager.show_notification(
            "Türkçe Otomatik Düzeltici",
            "Otomatik düzeltme aktif." if correction_active else "Otomatik düzeltme duraklatıldı."
        )

    def exit_application(self):
        """Uygulamayı tamamen kapat."""
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        QApplication.quit()

    def on_tray_activated(self, reason):
        """Tepsi ikonuna tıklandığında pencereyi aç."""
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.show_settings_window()

    def register_hotkey(self, hotkey_str: str):
        """Global kısayol tuşunu sisteme bağla."""
        try:
            keyboard.remove_hotkey(self.current_hotkey)
        except Exception:
            pass

        try:
            keyboard.add_hotkey(hotkey_str, correct_selected_text)
            self.current_hotkey = hotkey_str
            print(f"Global kısayol kaydedildi: {hotkey_str}")
        except Exception as e:
            print(f"Kısayol kaydetme hatası '{hotkey_str}': {e}")

    def update_hotkey(self, new_hotkey: str):
        """Kısayol değiştirildiğinde güncelle."""
        if new_hotkey != self.current_hotkey:
            self.register_hotkey(new_hotkey)
            self.settings["hotkey"] = new_hotkey
            settings_manager.save_settings(self.settings)


def main():
    """Tepsi uygulamasını başlat."""
    setup_undo_detection()

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray_icon = SystemTrayApp()
    tray_icon.show()

    _notification_manager.show_notification(
        "🇹🇷 Türkçe Otomatik Düzeltici",
        f"Çalışıyor! Herhangi bir metni seçip {tray_icon.current_hotkey.upper()} tuşuna basın."
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()