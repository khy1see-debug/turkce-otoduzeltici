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


def _parse_hotkey_string(hotkey_str: str) -> tuple[int, int]:
    """Kısayol metnini (örn: 'alt+q', 'ctrl+alt+q') Win32 modifiers ve sanal tuş koduna çevirir."""
    parts = [p.strip().lower() for p in hotkey_str.split('+')]
    mods = 0x4000  # MOD_NOREPEAT (tuşa basılı tutunca ardışık tetiklemeyi önler)
    vk = 0
    for p in parts:
        if p in ('alt', 'menu'):
            mods |= 0x0001
        elif p in ('ctrl', 'control'):
            mods |= 0x0002
        elif p in ('shift',):
            mods |= 0x0004
        elif p in ('win', 'windows'):
            mods |= 0x0008
        elif len(p) == 1:
            vk = ord(p.upper())
        elif p.startswith('f') and p[1:].isdigit():
            vk = 0x6F + int(p[1:])
        elif p == 'space':
            vk = 0x20
    if vk == 0:
        vk = 0x51  # Varsayılan: 'Q'
    if mods == 0x4000:
        mods |= 0x0001  # Varsayılan: ALT
    return mods, vk


class Win32GlobalHotkeyThread(threading.Thread):
    """
    Windows işletim sisteminde donanım düzeyinde güvenilir global kısayol dinleyicisi.
    Windows API 'RegisterHotKey' kullanır; birden fazla kısayolu (Düzeltme: Alt+Q, Çeviri: Alt+W)
    aynı donanım mesaj döngüsünde güvenle dinler.
    """
    def __init__(self, *args):
        super().__init__(daemon=True)
        # hotkey_mappings: [(id, hotkey_str, callback), ...]
        if len(args) == 1 and isinstance(args[0], list):
            self.hotkey_mappings = args[0]
        elif len(args) == 2:
            self.hotkey_mappings = [(1001, args[0], args[1])]
        else:
            self.hotkey_mappings = []
        self.stop_event = threading.Event()
        self.registered_ids = []

    def run(self):
        if sys.platform != "win32":
            return
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        callbacks = {}
        for hid, hstr, cb in self.hotkey_mappings:
            mods, vk = _parse_hotkey_string(hstr)
            reg = bool(user32.RegisterHotKey(None, hid, mods, vk))
            if not reg:
                reg = bool(user32.RegisterHotKey(None, hid, mods & ~0x4000, vk))
            if reg:
                self.registered_ids.append(hid)
                callbacks[hid] = cb
                print(f"[+] Win32 Donanım Kısayolu Devrede: {hstr} (ID: {hid})")
            else:
                print(f"Win32 RegisterHotKey kaydedilemedi: {hstr} (ID: {hid})", file=sys.stderr)

        msg = wintypes.MSG()
        try:
            while not self.stop_event.is_set():
                if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE = 1
                    if msg.message == 0x0312:  # WM_HOTKEY
                        target_cb = callbacks.get(msg.wParam)
                        if target_cb:
                            threading.Thread(target=target_cb, daemon=True).start()
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    # Akıllı Ctrl+Z (Undo) geri alma tespiti: Kullanıcı düzeltmeyi geri alırsa öğrenme motoru ret kaydeder
                    global _last_correction_time, _last_correction_corrected
                    if _last_correction_time > 0 and (time.time() - _last_correction_time) < 4.0:
                        ctrl_pressed = bool(user32.GetAsyncKeyState(0x11) & 0x8000)
                        z_pressed = bool(user32.GetAsyncKeyState(0x5A) & 0x8000)
                        if ctrl_pressed and z_pressed:
                            rejected = _last_correction_corrected
                            _last_correction_time = 0.0
                            try:
                                from src import self_learning
                                threading.Thread(target=self_learning.record_rejection, args=(rejected,), daemon=True).start()
                            except Exception:
                                pass
                    time.sleep(0.015)
        finally:
            for hid in self.registered_ids:
                user32.UnregisterHotKey(None, hid)

    def stop(self):
        self.stop_event.set()


def _send_win32_key_combination(ctrl_key: str):
    """Windows'ta basılı olabilecek tuşları serbest bırakarak güvenli Ctrl+C veya Ctrl+V gönderir."""
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # 1. Alt, Ctrl, Shift, Q tuşlarını donanım düzeyinde serbest bırak
            user32.keybd_event(0x12, 0, 2, 0)  # VK_MENU (Alt) UP
            user32.keybd_event(0x51, 0, 2, 0)  # 'Q' UP
            user32.keybd_event(0x11, 0, 2, 0)  # VK_CONTROL UP
            user32.keybd_event(0x10, 0, 2, 0)  # VK_SHIFT UP
            time.sleep(0.02)

            # 2. Ctrl + key gönder
            vk_code = 0x43 if ctrl_key.lower() == 'c' else 0x56  # 0x43 = 'C', 0x56 = 'V'
            user32.keybd_event(0x11, 0, 0, 0)  # Ctrl DOWN
            time.sleep(0.02)
            user32.keybd_event(vk_code, 0, 0, 0)  # Key DOWN
            time.sleep(0.03)
            user32.keybd_event(vk_code, 0, 2, 0)  # Key UP
            time.sleep(0.02)
            user32.keybd_event(0x11, 0, 2, 0)  # Ctrl UP
        except Exception as e:
            print(f"Key send error: {e}")


SENTINEL_CLIPBOARD = "\x00__TURKCE_COPY_SENTINEL__\x00"


def _capture_active_text(sentinel=SENTINEL_CLIPBOARD) -> tuple[str, str]:
    """
    Seçili metni yakalar. Kullanıcı fare ile metin seçmemişse,
    akıllı otomasyon ile imlecin solundaki satırı (Shift+Home) otomatik seçip yakalar.
    (orijinal_pano, yakalanan_metin) döner.
    """
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # Parmaklar Alt/Ctrl/Q/W tuşlarından çekilene kadar bekle (hızlı yoklama)
            for _ in range(8):
                alt_down = bool(user32.GetAsyncKeyState(0x12) & 0x8000)
                q_down = bool(user32.GetAsyncKeyState(0x51) & 0x8000)
                w_down = bool(user32.GetAsyncKeyState(0x57) & 0x8000)
                if not alt_down and not q_down and not w_down:
                    break
                time.sleep(0.012)
            # Tuşları donanım düzeyinde serbest bırak
            user32.keybd_event(0x12, 0, 2, 0)  # Alt UP
            user32.keybd_event(0x51, 0, 2, 0)  # Q UP
            user32.keybd_event(0x57, 0, 2, 0)  # W UP
            user32.keybd_event(0x11, 0, 2, 0)  # Ctrl UP
            user32.keybd_event(0x10, 0, 2, 0)  # Shift UP
            time.sleep(0.01)
        except Exception:
            pass

    try:
        orig = pyperclip.paste()
    except Exception:
        orig = ""

    try:
        pyperclip.copy(sentinel)
    except Exception:
        pass

    # 1. Standart Ctrl+C kopyalama denemesi
    _send_win32_key_combination('c')
    captured = ""
    for _ in range(7):
        time.sleep(0.015)
        try:
            t = pyperclip.paste()
            if t != sentinel and t.strip():
                captured = t
                break
        except Exception:
            pass

    # 2. Akıllı Satır Otomasyonu (Fareyle seçilmediyse imleçten satır başına kadar otomatik seç)
    if not captured and sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # Shift + Home (imleçten satır başına kadar seç)
            user32.keybd_event(0x10, 0, 0, 0)  # Shift DOWN
            time.sleep(0.01)
            user32.keybd_event(0x24, 0, 1, 0)  # Home DOWN
            time.sleep(0.015)
            user32.keybd_event(0x24, 0, 3, 0)  # Home UP
            time.sleep(0.01)
            user32.keybd_event(0x10, 0, 2, 0)  # Shift UP
            time.sleep(0.015)

            _send_win32_key_combination('c')
            for _ in range(6):
                time.sleep(0.015)
                t = pyperclip.paste()
                if t != sentinel and t.strip():
                    captured = t
                    break
        except Exception:
            pass

    return orig, captured


def correct_selected_text():
    """Seçili metni (veya o anki satırı) kopyalar, otomatik imla ve LLM ile düzeltip yerine yapıştırır."""
    global correction_active, _last_correction_time, _last_correction_original, _last_correction_corrected
    if not correction_active:
        return

    original_clipboard, selected_text = _capture_active_text()
    if not selected_text or not selected_text.strip():
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass
        _notification_manager.show_notification(
            "⚠️ Metin Bulunamadı",
            "Lütfen düzeltmek istediğiniz metni seçin veya imleci satır sonuna getirin."
        )
        return

    # Eğer kullanıcı metnin başına ? veya /bilgi koyduysa doğrudan anında bilgi motoruna yönlendir
    clean_stripped = selected_text.strip()
    if clean_stripped.startswith(("?", "/bilgi", "/ai", "/cevap")):
        generate_knowledge_for_selected_text(pre_captured=(original_clipboard, selected_text))
        return

    try:
        # 1. Önce yerel deterministik motoru çalıştır (~2ms: TDK, bitişik kelime, argo, devrik koruma)
        settings = settings_manager.load_settings()
        is_all_caps = selected_text.isupper() and len([c for c in selected_text if c.isalpha()]) > 2
        local_corrected = fix_sentence(selected_text)
        if is_all_caps:
            from src.turkish_case import turkish_upper
            local_corrected = turkish_upper(local_corrected)

        used_ai = False
        corrected_text = local_corrected

        # 2. Kullanıcı özellikle Tray'de AI aktif ettiyse yerel çıktıyı AI ile cilala
        if settings.get("use_ai_in_tray", False):
            try:
                from src.ai_engine import fix_with_ai
                ai_res = fix_with_ai(local_corrected)
                if ai_res and ai_res.strip():
                    corrected_text = ai_res.strip()
                    used_ai = True
            except Exception:
                corrected_text = local_corrected

        # Sonucu Yapıştır
        if corrected_text != selected_text:
            pyperclip.copy(corrected_text)
            time.sleep(0.04)
            _send_win32_key_combination('v')

            _last_correction_time = time.time()
            _last_correction_original = selected_text
            _last_correction_corrected = corrected_text

            try:
                _stats_manager.record_correction(selected_text, corrected_text)
                self_learning.record_correction(selected_text, corrected_text)
            except Exception:
                pass

            if settings.get("sound_toggle", True):
                _notification_manager.play_sound("success")

            title = "✨ Metin Düzeltildi (Yapay Zeka)" if used_ai else "✨ Metin Düzeltildi"
            _notification_manager.show_notification(
                title,
                f"{selected_text} ➜ {corrected_text}"
            )

            time.sleep(0.08)
            if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
        else:
            if settings.get("sound_toggle", True):
                _notification_manager.play_sound("info")
            _notification_manager.show_notification(
                "✓ İmla Doğru",
                f"'{selected_text}' üzerinde düzeltme gerekmedi."
            )
            if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
    except Exception as e:
        print(f"Düzeltme hatası: {e}")
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass


def translate_selected_text():
    """Seçili metni (veya o anki satırı) kopyalar, NVIDIA AI ile TR ⇄ EN çevirip yerine yapıştırır."""
    global correction_active
    if not correction_active:
        return

    original_clipboard, selected_text = _capture_active_text()
    if not selected_text or not selected_text.strip():
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass
        _notification_manager.show_notification(
            "⚠️ Metin Bulunamadı",
            "Lütfen çevirmek istediğiniz metni seçin veya imleci satır sonuna getirin."
        )
        return

    try:
        from src.ai_engine import translate_with_ai, free_web_translate, detect_source_language
        src_lang = detect_source_language(selected_text)
        target_lang = "en" if src_lang == "tr" else "tr"

        translated = translate_with_ai(selected_text, target_lang=target_lang)
        if not translated or not translated.strip():
            # Yedek: Hızlı ve kesintisiz web çevirisi
            translated = free_web_translate(selected_text, target_lang=target_lang)

        if not translated or not translated.strip():
            _notification_manager.show_notification(
                "⚠️ Çeviri Başarısız",
                "Çeviri servisi yanıt vermedi veya metin güvenlik denetiminden geçemedi."
            )
            if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
            return

        translated = translated.strip()
        pyperclip.copy(translated)
        time.sleep(0.04)
        _send_win32_key_combination('v')

        settings = settings_manager.load_settings()
        if settings.get("sound_toggle", True):
            _notification_manager.play_sound("success")

        direction_title = "🌍 Türkçe ➜ İngilizce" if target_lang == "en" else "🌍 Yabancı Dil ➜ Türkçe"
        _notification_manager.show_notification(
            direction_title,
            f"{selected_text} ➜ {translated}"
        )

        time.sleep(0.08)
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass
    except Exception as e:
        print(f"Çeviri hatası: {e}")
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass


def generate_knowledge_for_selected_text(pre_captured=None):
    """Seçili metni (veya o anki satırı ya da panodaki soruyu) kopyalar, AI ile arkadaş ağzından anında cevap üretip kutuya yapıştırır (Ghost Copilot)."""
    global correction_active
    if not correction_active:
        return

    if pre_captured:
        original_clipboard, selected_text = pre_captured
    else:
        original_clipboard, selected_text = _capture_active_text()

    # Eğer metin kutusunda yazı yoksa, panodaki en son kopyalanmış soruya bak (Ctrl+C & Alt+E akışı)
    is_clipboard_source = False
    target_query = selected_text

    if not target_query or not target_query.strip():
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD and original_clipboard.strip():
            target_query = original_clipboard.strip()
            is_clipboard_source = True

    if not target_query or not target_query.strip():
        _notification_manager.show_notification(
            "⚠️ Soru/Konu Bulunamadı",
            "Bir soru yazın, metin seçin veya arkadaşınızın sorusunu kopyalayıp (Ctrl+C) Alt+E yapın."
        )
        return

    try:
        from src.ai_engine import generate_knowledge
        info_res = generate_knowledge(target_query)

        if not info_res or not info_res.strip():
            _notification_manager.show_notification(
                "⚠️ Cevap Üretilemedi",
                "Yapay zeka yanıt veremedi veya konu hakkında yanıt bulunamadı."
            )
            if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
            return

        info_text = info_res.strip()
        pyperclip.copy(info_text)
        time.sleep(0.04)
        _send_win32_key_combination('v')

        settings = settings_manager.load_settings()
        if settings.get("sound_toggle", True):
            _notification_manager.play_sound("success")

        preview = info_text[:80] + "..." if len(info_text) > 80 else info_text
        title = "💡 Arkadaş Cevabı Yapıştırıldı" if is_clipboard_source else "💡 Anında Soru Yanıtı"
        _notification_manager.show_notification(
            title,
            preview
        )

        time.sleep(0.08)
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass
    except Exception as e:
        print(f"Bilgi üretme hatası: {e}")
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass


class SystemTrayApp(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.app_icon = create_icon_image()
        self.setIcon(self.app_icon)
        self.setToolTip("Türkçe Otomatik Düzeltici (Alt+Q: Düzelt | Alt+W: Çevir | Alt+E: Bilgi)")

        _notification_manager.set_tray_icon(self)

        # Ayarları yükle
        self.settings = settings_manager.load_settings()
        self.current_hotkey = self.settings.get("hotkey", "alt+q")
        self._win32_hotkey_thread = None
        self.main_window = None

        # Yüzen Düzeltme Balonu (Grammarly Modu)
        from src.floating_pill import FloatingCorrectionPill
        self.floating_pill = FloatingCorrectionPill(
            on_correct=correct_selected_text,
            on_translate=translate_selected_text,
            on_info=generate_knowledge_for_selected_text,
            is_active_fn=lambda: correction_active,
            enabled=self.settings.get("floating_pill_enabled", True),
        )

        self.menu = QMenu()
        self.setup_menu()
        self.setContextMenu(self.menu)
        self.activated.connect(self.on_tray_activated)

        # Donanım kısayolunu sisteme kaydet
        self.register_hotkey(self.current_hotkey)

    def setup_menu(self):
        # Düzeltme Stüdyosu & Ayarlar
        self.show_settings_action = QAction("✨ Düzeltme Stüdyosu & Ayarlar", self)
        self.show_settings_action.triggered.connect(self.show_settings_window)
        self.menu.addAction(self.show_settings_action)

        # Kişisel Sözlük
        self.personal_dict_action = QAction("📖 Kişisel Sözlüğü Aç", self)
        self.personal_dict_action.triggered.connect(self.show_personal_dictionary)
        self.menu.addAction(self.personal_dict_action)

        # Yüzen Düzeltme Balonu Aç/Kapat
        is_pill_on = self.settings.get("floating_pill_enabled", True)
        self.toggle_pill_action = QAction("🪄 Yüzen Düzeltme Balonu (Seçimde Göster)", self)
        self.toggle_pill_action.setCheckable(True)
        self.toggle_pill_action.setChecked(is_pill_on)
        self.toggle_pill_action.triggered.connect(self.toggle_floating_pill)
        self.menu.addAction(self.toggle_pill_action)

        # AI Modu Aç/Kapat (Hızlı Geçiş)
        is_ai_on = self.settings.get("use_ai_in_tray", False)
        self.toggle_ai_action = QAction("🤖 Yapay Zeka Modu (Gemini / NVIDIA)", self)
        self.toggle_ai_action.setCheckable(True)
        self.toggle_ai_action.setChecked(is_ai_on)
        self.toggle_ai_action.triggered.connect(self.toggle_ai_mode)
        self.menu.addAction(self.toggle_ai_action)

        # Akıllı Çeviri Kısayol Bilgisi / Tetikleyici
        self.translate_action = QAction("🌍 Akıllı Çeviri (Alt+W - TR ⇄ EN)", self)
        self.translate_action.triggered.connect(lambda: threading.Thread(target=translate_selected_text, daemon=True).start())
        self.menu.addAction(self.translate_action)

        # Anında Bilgi / Cevapla Kısayol Bilgisi / Tetikleyici
        self.knowledge_action = QAction("💡 Anında Bilgi / Cevapla (Alt+E)", self)
        self.knowledge_action.triggered.connect(lambda: threading.Thread(target=generate_knowledge_for_selected_text, daemon=True).start())
        self.menu.addAction(self.knowledge_action)

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

    def toggle_floating_pill(self, checked):
        """Yüzen Düzeltme Balonunu (Floating Pill) aç/kapat."""
        self.settings = settings_manager.load_settings()
        self.settings["floating_pill_enabled"] = checked
        settings_manager.save_settings(self.settings)

        if getattr(self, "floating_pill", None):
            self.floating_pill.set_enabled(checked)

        if self.main_window and hasattr(self.main_window, "floating_pill_check"):
            self.main_window.floating_pill_check.setChecked(checked)

        if hasattr(self, "toggle_pill_action") and self.toggle_pill_action.isChecked() != checked:
            self.toggle_pill_action.setChecked(checked)

        _notification_manager.show_notification(
            "🪄 Yüzen Düzeltme Balonu",
            "Seçim baloncuğu aktif edildi." if checked else "Seçim baloncuğu devre dışı bırakıldı."
        )

    def toggle_ai_mode(self, checked):
        """Kısayollar için AI modunu doğrudan tepsi menüsünden aç/kapat."""
        self.settings = settings_manager.load_settings()
        self.settings["use_ai_in_tray"] = checked
        settings_manager.save_settings(self.settings)

        # Stüdyo açık ise ayarlar penceresindeki kutucuğu da senkronize et
        if self.main_window and hasattr(self.main_window, "ai_tray_check"):
            self.main_window.ai_tray_check.setChecked(checked)

        if hasattr(self, "toggle_ai_action") and self.toggle_ai_action.isChecked() != checked:
            self.toggle_ai_action.setChecked(checked)

        if checked:
            prov = self.settings.get("ai_provider", "auto").upper()
            _notification_manager.show_notification(
                "🤖 Yapay Zeka Modu Devrede",
                f"Kısayollar artık derin dil modelini ({prov}) kullanacak."
            )
        else:
            _notification_manager.show_notification(
                "⚡ Çevrimdışı 0-Token Modu",
                "Kısayollar 1.68M+ kelimelik yerel Türkçe sözlük motoruna geçti."
            )

    def exit_application(self):
        """Uygulamayı tamamen kapat."""
        if getattr(self, "floating_pill", None):
            try:
                self.floating_pill.hide_pill()
                self.floating_pill.close()
            except Exception:
                pass
        if getattr(self, "_win32_hotkey_thread", None):
            try:
                self._win32_hotkey_thread.stop()
            except Exception:
                pass
        QApplication.quit()

    def on_tray_activated(self, reason):
        """Tepsi ikonuna tıklandığında pencereyi aç."""
        if reason in (QSystemTrayIcon.ActivationReason.DoubleClick, QSystemTrayIcon.ActivationReason.Trigger):
            self.show_settings_window()

    def register_hotkey(self, hotkey_str: str):
        """Global kısayol tuşlarını sisteme bağla (Win32 Donanım API - 100% Kararlı)."""
        if sys.platform == "win32":
            if getattr(self, "_win32_hotkey_thread", None):
                try:
                    self._win32_hotkey_thread.stop()
                except Exception:
                    pass
                self._win32_hotkey_thread = None
            mappings = [
                (1001, hotkey_str, correct_selected_text),
                (1002, "alt+w", translate_selected_text),
                (1003, "alt+e", generate_knowledge_for_selected_text)
            ]
            self._win32_hotkey_thread = Win32GlobalHotkeyThread(mappings)
            self._win32_hotkey_thread.start()
            print(f"[+] Win32 Donanım Kısayolları Devrede: {hotkey_str} (Düzeltme), Alt+W (Çeviri), Alt+E (Bilgi)")

        self.current_hotkey = hotkey_str

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
        f"Çalışıyor! Düzeltme: {tray_icon.current_hotkey.upper()} | Çeviri: ALT+W | Bilgi: ALT+E"
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()