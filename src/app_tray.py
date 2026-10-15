"""
System Tray Application for Turkish Auto-Corrector.
Provides a background service with global hotkey correction (default Alt+Q),
clipboard preservation, undo detection (Ctrl+Z), and tray menu.
"""
import sys
import os
import time
import threading
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


def _send_win32_key_combination(ctrl_key: str):
    """Windows'ta basılı olabilecek Alt/Shift tuşlarını serbest bırakarak güvenli Ctrl+C veya Ctrl+V gönderir."""
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # 1. Alt, Ctrl, Shift tuşlarını serbest bırak (KEYUP = 2)
            user32.keybd_event(0x12, 0, 2, 0)  # VK_MENU (Alt)
            user32.keybd_event(0x11, 0, 2, 0)  # VK_CONTROL
            user32.keybd_event(0x10, 0, 2, 0)  # VK_SHIFT
            time.sleep(0.04)

            # 2. Ctrl + key gönder
            vk_code = 0x43 if ctrl_key.lower() == 'c' else 0x56  # 0x43 = 'C', 0x56 = 'V'
            user32.keybd_event(0x11, 0, 0, 0)  # Ctrl DOWN
            user32.keybd_event(vk_code, 0, 0, 0)  # Key DOWN
            time.sleep(0.03)
            user32.keybd_event(vk_code, 0, 2, 0)  # Key UP
            user32.keybd_event(0x11, 0, 2, 0)  # Ctrl UP
            return
        except Exception:
            pass

    # Fallback to keyboard module
    try:
        keyboard.release('alt')
        time.sleep(0.04)
        keyboard.send(f'ctrl+{ctrl_key}')
    except Exception:
        pass


def correct_selected_text():
    """Seçili metni kopyalar, otomatik stil ve imlayla düzeltip yerine yapıştırır."""
    global correction_active, _last_correction_time, _last_correction_original, _last_correction_corrected
    if not correction_active:
        return

    # Panonun mevcut içeriğini yedekle
    try:
        original_clipboard = pyperclip.paste()
    except Exception:
        original_clipboard = ""

    try:
        # Önce panoyu temizle ki yeni kopyalanan metni kesin ayırt edebilelim
        try:
            pyperclip.copy("")
        except Exception:
            pass

        # Seçili metni panoya kopyala (Alt tuşunu serbest bırakıp Ctrl+C gönder)
        _send_win32_key_combination('c')

        selected_text = ""
        # Pano güncellenene kadar maksimum 300ms bekle (Chrome/Word/Discord gecikmesi)
        for _ in range(6):
            time.sleep(0.05)
            try:
                t = pyperclip.paste()
                if t and t.strip():
                    selected_text = t
                    break
            except Exception:
                pass

        if not selected_text or not selected_text.strip():
            # Kullanıcı metin seçmemişse orijinal panoyu geri yükle
            if original_clipboard:
                pyperclip.copy(original_clipboard)
            return

        # Akıllı Harf & İmla Tespiti (Auto-Detect + Opsiyonel NVIDIA AI)
        settings = settings_manager.load_settings()
        used_ai = False
        corrected_text = None

        if settings.get("use_ai_in_tray", False):
            try:
                from src.ai_engine import fix_with_ai
                ai_res = fix_with_ai(selected_text)
                if ai_res and ai_res.strip():
                    corrected_text = ai_res.strip()
                    used_ai = True
            except Exception:
                corrected_text = None

        if not corrected_text:
            is_all_caps = selected_text.isupper() and len([c for c in selected_text if c.isalpha()]) > 2
            corrected_text = fix_sentence(selected_text)
            if is_all_caps:
                from src.turkish_case import turkish_upper
                corrected_text = turkish_upper(corrected_text)

        if corrected_text != selected_text:
            # Düzeltilmiş metni panoya koyup yapıştır (Ctrl+V)
            pyperclip.copy(corrected_text)
            time.sleep(0.05)
            _send_win32_key_combination('v')

            # Geri alma takibi için kaydet
            _last_correction_time = time.time()
            _last_correction_original = selected_text
            _last_correction_corrected = corrected_text

            # İstatistik ve Öz-öğrenmeye kaydet (güvenli blok)
            try:
                _stats_manager.record_correction(selected_text, corrected_text)
                self_learning.record_correction(selected_text, corrected_text)
            except Exception:
                pass

            # Bildirim ve ses
            settings = settings_manager.load_settings()
            if settings.get("sound_toggle", True):
                _notification_manager.play_sound("success")

            title = "✨ Metin Düzeltildi (NVIDIA AI)" if used_ai else "✨ Metin Düzeltildi"
            _notification_manager.show_notification(
                title,
                f"{selected_text} ➜ {corrected_text}"
            )

            # Hedef uygulamanın yapıştırmayı tamamlaması için bekle, ardından panoyu geri yükle
            time.sleep(0.3)
            if original_clipboard:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
        else:
            settings = settings_manager.load_settings()
            if settings.get("sound_toggle", True):
                _notification_manager.play_sound("info")
            _notification_manager.show_notification(
                "✓ İmla Doğru",
                f"'{selected_text}' imlasında hata bulunamadı.",
                duration_sec=2
            )
            if original_clipboard:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
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


def _start_background_web_api():
    """Tarayıcı eklentisi ve harici araçlar için yerel REST API'yi arka planda başlatır."""
    try:
        from http.server import HTTPServer
        from src.web import CorrectionApiHandler
        server = HTTPServer(("127.0.0.1", 8765), CorrectionApiHandler)
        server.serve_forever()
    except Exception:
        pass


def main():
    """Tepsi uygulamasını başlat."""
    setup_undo_detection()

    # Tarayıcı eklentisi için yerel REST API'yi arka plan daemon thread'i olarak başlat
    threading.Thread(target=_start_background_web_api, daemon=True).start()

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray_icon = SystemTrayApp()
    tray_icon.show()
    tray_icon.show_settings_window()

    _notification_manager.show_notification(
        "🇹🇷 Türkçe Otomatik Düzeltici",
        f"Çalışıyor! Herhangi bir metni seçip {tray_icon.current_hotkey.upper()} tuşuna basın."
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()