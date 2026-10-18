"""
System Tray Application for Turkish Auto-Corrector.
Provides a background service with global hotkey correction (default Alt+Q),
clipboard preservation, undo detection (Ctrl+Z), and tray menu.
"""
import sys
import os
import time
import threading
from typing import Optional
import pyperclip
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QTimer

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

# Yüzen balon örneği (SystemTrayApp oluşturulunca atanır); arka plan çeviri thread'leri sonuç kartı için kullanır
_floating_pill = None


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
                        hid = msg.wParam
                        # Türkçe Q Klavye AltGr (@ ve €) Koruma Filtresi:
                        # AltGr tuşu Windows tarafından VK_RMENU (0xA5) + VK_CONTROL (0x11) olarak iletilir.
                        # Kullanıcı AltGr + Q (@) veya AltGr + E (€) yapıyorsa, bunu kısayol olarak yutma!
                        is_rmenu = bool(user32.GetAsyncKeyState(0xA5) & 0x8000)
                        vk = (msg.lParam >> 16) & 0xFFFF
                        if is_rmenu:
                            if vk == 0x51:  # 'Q' -> '@'
                                user32.keybd_event(0, ord('@'), 0x0004, 0)
                                user32.keybd_event(0, ord('@'), 0x0006, 0)
                                continue
                            elif vk == 0x45:  # 'E' -> '€'
                                user32.keybd_event(0, ord('€'), 0x0004, 0)
                                user32.keybd_event(0, ord('€'), 0x0006, 0)
                                continue

                        target_cb = callbacks.get(hid)
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


def _release_and_mask_modifiers(extra_vks=(0x51, 0x57, 0x45, 0x52, 0x54), max_wait_sec=0.35):
    """
    Fiziksel tuşların (Alt, Ctrl, Shift, Q, W, E, R, T) bırakılmasını bekler
    ve Windows'un Menü Çubuğunu (Menu Bar / Focus Steal) tetiklemesini 0xFF maskeleme tuşuyla engeller.
    """
    if sys.platform != "win32":
        return
    import ctypes
    user32 = ctypes.windll.user32
    start = time.time()
    # 1. Kullanıcının parmaklarını tuşlardan kaldırmasını bekle (en fazla max_wait_sec)
    while (time.time() - start) < max_wait_sec:
        alt_down = bool(user32.GetAsyncKeyState(0x12) & 0x8000)
        ctrl_down = bool(user32.GetAsyncKeyState(0x11) & 0x8000)
        shift_down = bool(user32.GetAsyncKeyState(0x10) & 0x8000)
        any_extra = any(bool(user32.GetAsyncKeyState(vk) & 0x8000) for vk in extra_vks)
        if not (alt_down or ctrl_down or shift_down or any_extra):
            break
        time.sleep(0.01)

    # 2. Donanım düzeyinde tüm niteleyicileri (modifiers) serbest bırak
    user32.keybd_event(0x12, 0, 2, 0)  # Alt UP
    user32.keybd_event(0x11, 0, 2, 0)  # Ctrl UP
    user32.keybd_event(0x10, 0, 2, 0)  # Shift UP
    for vk in extra_vks:
        user32.keybd_event(vk, 0, 2, 0)

    # 3. Windows Menü Çubuğu (Menu Bar / Focus Steal) maskesi!
    # Alt tuşu tek başına bırakıldığında Windows pencerenin Dosya/Düzen menüsüne odaklanır.
    # 0xFF (tanımsız sanal tuş) gönderilerek menü çubuğunun odağı çalması %100 engellenir.
    user32.keybd_event(0xFF, 0, 0, 0)
    user32.keybd_event(0xFF, 0, 2, 0)
    time.sleep(0.015)


def _send_win32_key_combination(ctrl_key: str):
    """Windows'ta basılı olabilecek tuşları serbest bırakarak donanım tarama kodlarıyla (ScanCode) güvenli Ctrl+C veya Ctrl+V gönderir."""
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            # 1. Alt, Ctrl, Shift ve harf tuşlarını temizle
            _release_and_mask_modifiers(max_wait_sec=0.2)

            # 2. Donanım ScanCode ile Ctrl + key gönder
            vk_code = 0x43 if ctrl_key.lower() == 'c' else 0x56  # 0x43 = 'C', 0x56 = 'V'
            ctrl_scan = user32.MapVirtualKeyW(0x11, 0)
            key_scan = user32.MapVirtualKeyW(vk_code, 0)
            user32.keybd_event(0x11, ctrl_scan, 0, 0)  # Ctrl DOWN
            time.sleep(0.02)
            user32.keybd_event(vk_code, key_scan, 0, 0)  # Key DOWN
            time.sleep(0.025)
            user32.keybd_event(vk_code, key_scan, 2, 0)  # Key UP
            time.sleep(0.015)
            user32.keybd_event(0x11, ctrl_scan, 2, 0)  # Ctrl UP
            time.sleep(0.015)
        except Exception as e:
            print(f"Key send error: {e}")
        finally:
            try:
                user32.keybd_event(0x11, 0, 2, 0)  # Ctrl UP
                user32.keybd_event(0x12, 0, 2, 0)  # Alt UP
                user32.keybd_event(0x10, 0, 2, 0)  # Shift UP
                user32.keybd_event(0xFF, 0, 0, 0)
                user32.keybd_event(0xFF, 0, 2, 0)
            except Exception:
                pass


def _ensure_foreground_hwnd(target_hwnd: int):
    """İşlem sırasında hedef pencere odağı kaybolduysa yapıştırma öncesinde odağı geri kazandırır."""
    if sys.platform == "win32" and target_hwnd:
        try:
            import ctypes
            user32 = ctypes.windll.user32
            fg = user32.GetForegroundWindow()
            if fg and fg != target_hwnd:
                user32.SetForegroundWindow(target_hwnd)
                time.sleep(0.025)
        except Exception:
            pass


SENTINEL_CLIPBOARD = "\x00__TURKCE_COPY_SENTINEL__\x00"


def _capture_active_text(sentinel=SENTINEL_CLIPBOARD) -> tuple[str, str]:
    """
    Seçili metni yakalar. Kullanıcı fare ile metin seçmemişse,
    akıllı otomasyon ile imlecin solundaki satırı (Shift+Home) otomatik seçip yakalar.
    (orijinal_pano, yakalanan_metin) döner.
    """
    _release_and_mask_modifiers()

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
    for _ in range(10):
        time.sleep(0.02)
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
            _release_and_mask_modifiers(max_wait_sec=0.15)

            shift_scan = user32.MapVirtualKeyW(0x10, 0)
            home_scan = user32.MapVirtualKeyW(0x24, 0)
            # Shift + Home (imleçten satır başına kadar seç)
            user32.keybd_event(0x10, shift_scan, 0, 0)  # Shift DOWN
            time.sleep(0.015)
            user32.keybd_event(0x24, home_scan, 1, 0)  # Home DOWN
            time.sleep(0.02)
            user32.keybd_event(0x24, home_scan, 3, 0)  # Home UP
            time.sleep(0.015)
            user32.keybd_event(0x10, shift_scan, 2, 0)  # Shift UP
            time.sleep(0.02)

            _send_win32_key_combination('c')
            for _ in range(10):
                time.sleep(0.02)
                t = pyperclip.paste()
                if t != sentinel and t.strip():
                    captured = t
                    break
        except Exception:
            pass
        finally:
            _release_and_mask_modifiers(max_wait_sec=0.1)

    return orig, captured


def correct_selected_text():
    """Seçili metni (veya o anki satırı) kopyalar; yabancı dilde gelen mesaj ise Türkçeye çevirir, Türkçe ise TDK + AI ile düzeltir."""
    global correction_active, _last_correction_time, _last_correction_original, _last_correction_corrected
    if not correction_active:
        return

    target_hwnd = 0
    if sys.platform == "win32":
        try:
            import ctypes
            target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            pass

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
        from src.ai_engine import (
            is_definitely_foreign_text,
            translate_with_ai,
            free_web_translate,
            is_valid_translation_output,
            fix_with_ai,
        )
        settings = settings_manager.load_settings()

        # 0. Birisi yabancı dilde (İngilizce, Rusça, Almanca, Fransızca, İspanyolca, Arapça, Japonca vb.)
        # mesaj yazdığında ve kullanıcı seçip Alt+Q / Düzelt yaptığında otomatik Türkçeye çevir!
        if is_definitely_foreign_text(clean_stripped):
            translated_tr = translate_with_ai(clean_stripped, target_lang="tr")
            if not translated_tr or not translated_tr.strip() or not is_valid_translation_output(clean_stripped, translated_tr, "tr"):
                translated_tr = free_web_translate(clean_stripped, target_lang="tr")
            if translated_tr and translated_tr.strip():
                translated_tr = translated_tr.strip()
                _ensure_foreground_hwnd(target_hwnd)
                pyperclip.copy(translated_tr)
                time.sleep(0.04)
                _send_win32_key_combination('v')

                if _floating_pill is not None:
                    _floating_pill.show_result_card("🌍 Yabancı Mesaj ➜ Türkçe", translated_tr)

                if settings.get("sound_toggle", True):
                    _notification_manager.play_sound("success")
                _notification_manager.show_notification(
                    "🌍 Yabancı Mesaj ➜ Türkçe",
                    f"{clean_stripped} ➜ {translated_tr}"
                )
                time.sleep(0.38)
                if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                    try:
                        pyperclip.copy(original_clipboard)
                    except Exception:
                        pass
                return

        # 1. Önce yerel deterministik motoru çalıştır (~2ms: TDK, bitişik kelime, argo, devrik koruma)
        is_all_caps = selected_text.isupper() and len([c for c in selected_text if c.isalpha()]) > 2
        local_corrected = fix_sentence(selected_text)
        if is_all_caps:
            from src.turkish_case import turkish_upper
            local_corrected = turkish_upper(local_corrected)

        used_ai = False
        corrected_text = local_corrected

        # 2. Hibrit Yapay Zeka Cilalama (Varsayılan açık: yerel TDK çıktısını Gemini/Groq ile bağlamsal olarak mükemmelleştirir)
        from src.ai_engine import NetworkError, PolicyError
        from src.ai_policy import ai_allowed, policy_from_settings

        policy = policy_from_settings(settings)
        ai_enabled = settings.get("use_ai_in_tray", True) and ai_allowed(policy)
        if ai_enabled:
            try:
                ai_res = fix_with_ai(local_corrected)
                if ai_res and ai_res.strip():
                    corrected_text = ai_res.strip()
                    if is_all_caps:
                        from src.turkish_case import turkish_upper
                        corrected_text = turkish_upper(corrected_text)
                    used_ai = True
            except PolicyError:
                corrected_text = local_corrected
            except NetworkError as exc:
                _notification_manager.show_notification(
                    "⚠️ AI Hizmetine Bağlanılamadı",
                    f"Yerel motorla düzeltme devam ediyor: {exc}",
                )
                corrected_text = local_corrected

        # Sonucu Yapıştır
        if corrected_text != selected_text:
            _ensure_foreground_hwnd(target_hwnd)
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

            title = "✨ Metin Düzeltildi (TDK + AI)" if used_ai else "✨ Metin Düzeltildi"
            _notification_manager.show_notification(
                title,
                f"{selected_text} ➜ {corrected_text}"
            )

            # Electron/Discord/Tarayıcı IPC pano okuması tamamlanana kadar bekle (380ms)
            time.sleep(0.38)
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
    """Seçili metni (veya panodaki gelen mesajı) hangi dilde olursa olsun Türkçeye, Türkçe ise İngilizceye çevirir."""
    global correction_active
    if not correction_active:
        return

    target_hwnd = 0
    if sys.platform == "win32":
        try:
            import ctypes
            target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            pass

    original_clipboard, selected_text = _capture_active_text()
    is_clipboard_fallback = False
    if not selected_text or not selected_text.strip():
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD and original_clipboard.strip():
            selected_text = original_clipboard.strip()
            is_clipboard_fallback = True
        else:
            _notification_manager.show_notification(
                "⚠️ Metin Bulunamadı",
                "Lütfen çevirmek istediğiniz metni seçin veya kopyalayıp (Ctrl+C) Alt+W yapın."
            )
            return

    try:
        from src.ai_engine import translate_with_ai, free_web_translate, detect_source_language, is_valid_translation_output
        src_lang = detect_source_language(selected_text)
        target_lang = "en" if src_lang == "tr" else "tr"

        translated = translate_with_ai(selected_text, target_lang=target_lang)
        if not translated or not translated.strip() or not is_valid_translation_output(selected_text, translated, target_lang):
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
        if not is_clipboard_fallback:
            _ensure_foreground_hwnd(target_hwnd)
            pyperclip.copy(translated)
            time.sleep(0.04)
            _send_win32_key_combination('v')
        else:
            pyperclip.copy(translated)

        settings = settings_manager.load_settings()
        if settings.get("sound_toggle", True):
            _notification_manager.play_sound("success")

        direction_title = "🌍 Türkçe ➜ İngilizce" if target_lang == "en" else "🌍 Yabancı Mesaj ➜ Türkçe"
        if _floating_pill is not None:
            _floating_pill.show_result_card(direction_title, translated)

        _notification_manager.show_notification(
            direction_title,
            f"{selected_text} ➜ {translated}"
        )

        # Electron/Discord/Tarayıcı IPC pano okuması tamamlanana kadar bekle (380ms)
        if not is_clipboard_fallback:
            time.sleep(0.38)
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


def translate_selected_text_russian():
    """Seçili metni (veya o anki satırı / panoyu) AI ile çift yönlü TR ⇄ RU (Rusça) çevirir."""
    global correction_active
    if not correction_active:
        return

    target_hwnd = 0
    if sys.platform == "win32":
        try:
            import ctypes
            target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            pass

    original_clipboard, selected_text = _capture_active_text()
    is_clipboard_fallback = False
    if not selected_text or not selected_text.strip():
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD and original_clipboard.strip():
            selected_text = original_clipboard.strip()
            is_clipboard_fallback = True
        else:
            _notification_manager.show_notification(
                "⚠️ Metin Bulunamadı",
                "Lütfen Rusçaya/Türkçeye çevirmek istediğiniz metni seçin veya kopyalayıp Alt+R yapın."
            )
            return

    try:
        from src.ai_engine import translate_with_ai, free_web_translate, is_russian_text, is_valid_translation_output
        target_lang = "tr" if is_russian_text(selected_text) else "ru"

        translated = translate_with_ai(selected_text, target_lang=target_lang)
        if not translated or not translated.strip() or not is_valid_translation_output(selected_text, translated, target_lang):
            translated = free_web_translate(selected_text, target_lang=target_lang)

        if not translated or not translated.strip():
            _notification_manager.show_notification(
                "⚠️ Rusça Çeviri Başarısız",
                "Çeviri servisi yanıt vermedi."
            )
            if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
            return

        translated = translated.strip()
        if not is_clipboard_fallback:
            _ensure_foreground_hwnd(target_hwnd)
            pyperclip.copy(translated)
            time.sleep(0.04)
            _send_win32_key_combination('v')
        else:
            pyperclip.copy(translated)

        settings = settings_manager.load_settings()
        if settings.get("sound_toggle", True):
            _notification_manager.play_sound("success")

        direction_title = "🇷🇺 Türkçe ➜ Rusça" if target_lang == "ru" else "🇷🇺 Rusça ➜ Türkçe"
        if _floating_pill is not None:
            _floating_pill.show_result_card(direction_title, translated)

        _notification_manager.show_notification(
            direction_title,
            f"{selected_text} ➜ {translated}"
        )

        # Electron/Discord/Tarayıcı IPC pano okuması tamamlanana kadar bekle (380ms)
        if not is_clipboard_fallback:
            time.sleep(0.38)
            if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
    except Exception as e:
        print(f"Rusça çeviri hatası: {e}")
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass

def translate_selected_text_target_language(pre_captured=None, custom_target: Optional[str] = None):
    """
    Seçili metni kullanıcının seçtiği hedef dile (Almanca, Fransızca, İspanyolca, Arapça, Japonca vb.)
    veya yabancı dilde gelen mesajı otomatik Türkçeye çevirir (Alt+T).
    """
    global correction_active
    if not correction_active:
        return

    target_hwnd = 0
    if sys.platform == "win32":
        try:
            import ctypes
            target_hwnd = ctypes.windll.user32.GetForegroundWindow()
        except Exception:
            pass

    original_clipboard, selected_text = _capture_active_text()
    is_clipboard_fallback = False
    if not selected_text or not selected_text.strip():
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD and original_clipboard.strip():
            selected_text = original_clipboard.strip()
            is_clipboard_fallback = True
        else:
            _notification_manager.show_notification(
                "⚠️ Metin Bulunamadı",
                "Lütfen çevirmek istediğiniz metni seçin veya kopyalayıp Alt+T yapın."
            )
            return

    try:
        from src.ai_engine import (
            translate_with_ai,
            free_web_translate,
            detect_source_language,
            is_definitely_foreign_text,
            is_valid_translation_output
        )
        from src.settings_manager import SUPPORTED_TRANSLATE_LANGS

        settings = settings_manager.load_settings()
        chosen_lang = custom_target or settings.get("target_translate_lang", "de")
        lang_display = SUPPORTED_TRANSLATE_LANGS.get(chosen_lang, chosen_lang.upper())

        is_foreign = is_definitely_foreign_text(selected_text) or (detect_source_language(selected_text) != "tr")
        target_lang = "tr" if is_foreign else chosen_lang

        translated = translate_with_ai(selected_text, target_lang=target_lang)
        if not translated or not translated.strip() or not is_valid_translation_output(selected_text, translated, target_lang):
            translated = free_web_translate(selected_text, target_lang=target_lang)

        if not translated or not translated.strip():
            _notification_manager.show_notification(
                f"⚠️ {lang_display} Çeviri Başarısız",
                "Çeviri servisi yanıt vermedi."
            )
            if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
            return

        translated = translated.strip()
        if not is_clipboard_fallback:
            _ensure_foreground_hwnd(target_hwnd)
            pyperclip.copy(translated)
            time.sleep(0.04)
            _send_win32_key_combination('v')
        else:
            pyperclip.copy(translated)

        settings = settings_manager.load_settings()
        if settings.get("sound_toggle", True):
            _notification_manager.play_sound("success")

        direction_title = f"🌐 Türkçe ➜ {lang_display}" if target_lang != "tr" else f"🌐 {lang_display} ➜ Türkçe"
        if _floating_pill is not None:
            _floating_pill.show_result_card(direction_title, translated)

        _notification_manager.show_notification(
            direction_title,
            f"{selected_text} ➜ {translated}"
        )

        if not is_clipboard_fallback:
            time.sleep(0.38)
            if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
    except Exception as e:
        print(f"Hedef dil çeviri hatası: {e}")
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


def change_text_tone(tone: str = "formal"):
    """Seçili metnin üslubunu (resmi, samimi, özet) yapay zeka ile dönüştürür."""
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
            "Lütfen tonunu değiştirmek istediğiniz metni seçin."
        )
        return

    try:
        from src.ai_engine import rewrite_tone
        transformed = rewrite_tone(selected_text, tone=tone)
        if not transformed or not transformed.strip():
            _notification_manager.show_notification(
                "⚠️ Dönüştürülemedi",
                "Metin tonu dönüştürülürken yapay zeka yanıt veremedi."
            )
            if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass
            return

        res = transformed.strip()
        pyperclip.copy(res)
        time.sleep(0.04)
        _send_win32_key_combination('v')

        settings = settings_manager.load_settings()
        if settings.get("sound_toggle", True):
            _notification_manager.play_sound("success")

        tone_names = {"formal": "👔 Resmi / Kurumsal", "casual": "🤝 Samimi / Arkadaşça", "concise": "🎯 Kısa & Öz"}
        _notification_manager.show_notification(
            f"✨ Ton Değiştirildi ({tone_names.get(tone, tone)})",
            f"{selected_text[:50]}... ➜ {res[:50]}..."
        )

        time.sleep(0.08)
        if original_clipboard and original_clipboard != SENTINEL_CLIPBOARD:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass
    except Exception as e:
        print(f"Ton değiştirme hatası: {e}")
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
        self.setToolTip("Türkçe Otomatik Düzeltici (Alt+Q: Düzelt | Alt+W: EN Çevir | Alt+R: RU Çevir | Alt+E: Bilgi)")

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
            on_translate_ru=translate_selected_text_russian,
            on_translate_target=translate_selected_text_target_language,
            on_select_target_lang=self.set_target_translate_language,
            on_info=generate_knowledge_for_selected_text,
            on_tone=lambda: change_text_tone("formal"),
            is_active_fn=lambda: correction_active,
            enabled=self.settings.get("floating_pill_enabled", True),
            target_lang=self.settings.get("target_translate_lang", "de"),
        )
        global _floating_pill
        _floating_pill = self.floating_pill

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
        self.toggle_ai_action = QAction("🤖 Yapay Zeka Modu (Groq / Gemini / NVIDIA)", self)
        self.toggle_ai_action.setCheckable(True)
        self.toggle_ai_action.setChecked(is_ai_on)
        self.toggle_ai_action.triggered.connect(self.toggle_ai_mode)
        self.menu.addAction(self.toggle_ai_action)

        # Akıllı Çeviri Kısayol Bilgisi / Tetikleyici (TR ⇄ EN)
        self.translate_action = QAction("🌍 İngilizce Çeviri (Alt+W - TR ⇄ EN)", self)
        self.translate_action.triggered.connect(lambda: threading.Thread(target=translate_selected_text, daemon=True).start())
        self.menu.addAction(self.translate_action)

        # Rusça Çeviri Kısayol Bilgisi / Tetikleyici (TR ⇄ RU)
        self.translate_ru_action = QAction("🇷🇺 Rusça Çeviri (Alt+R - TR ⇄ RU)", self)
        self.translate_ru_action.triggered.connect(lambda: threading.Thread(target=translate_selected_text_russian, daemon=True).start())
        self.menu.addAction(self.translate_ru_action)

        # Çok Dilli Hedef Çeviri (Alt+T) & Dil Seçici Menüsü
        from src.settings_manager import SUPPORTED_TRANSLATE_LANGS
        cur_target = self.settings.get("target_translate_lang", "de")
        cur_target_name = SUPPORTED_TRANSLATE_LANGS.get(cur_target, cur_target.upper())

        self.target_lang_menu = QMenu(f"🌐 Hedef Çeviri (Alt+T: {cur_target_name})", self.menu)
        self.target_quick_action = QAction(f"🚀 Şimdi Çevir ➜ {cur_target_name} (Alt+T)", self.target_lang_menu)
        self.target_quick_action.triggered.connect(lambda: threading.Thread(target=translate_selected_text_target_language, daemon=True).start())
        self.target_lang_menu.addAction(self.target_quick_action)
        self.target_lang_menu.addSeparator()

        self.lang_actions = {}
        for code, name in SUPPORTED_TRANSLATE_LANGS.items():
            act = QAction(name, self.target_lang_menu)
            act.setCheckable(True)
            act.setChecked(code == cur_target)
            act.triggered.connect(lambda checked, c=code: self.set_target_translate_language(c))
            self.target_lang_menu.addAction(act)
            self.lang_actions[code] = act
        self.menu.addMenu(self.target_lang_menu)

        # Anında Bilgi / Cevapla Kısayol Bilgisi / Tetikleyici
        self.knowledge_action = QAction("💡 Anında Bilgi / Cevapla (Alt+E)", self)
        self.knowledge_action.triggered.connect(lambda: threading.Thread(target=generate_knowledge_for_selected_text, daemon=True).start())
        self.menu.addAction(self.knowledge_action)

        # Yazı Tonu Dönüştürücü (Kurumsal / Samimi / Kısa)
        self.tone_action = QAction("👔 Kurumsal / Resmi Dile Çevir", self)
        self.tone_action.triggered.connect(lambda: threading.Thread(target=lambda: change_text_tone("formal"), daemon=True).start())
        self.menu.addAction(self.tone_action)

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
        """Düzeltme Stüdyosu ve Ayarlar Penceresini Aç ve her koşulda en öne getir."""
        from src.main_window import MainWindow
        if self.main_window is None:
            self.main_window = MainWindow(tray_icon=self)

        self.main_window.setWindowState(
            (self.main_window.windowState() & ~Qt.WindowState.WindowMinimized)
            | Qt.WindowState.WindowActive
        )
        self.main_window.showNormal()
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        if sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                hwnd = int(self.main_window.winId())
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.ShowWindow(hwnd, 5)  # SW_SHOW

                fg_hwnd = user32.GetForegroundWindow()
                fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0
                cur_tid = kernel32.GetCurrentThreadId()
                attached = False
                if fg_tid and cur_tid and fg_tid != cur_tid:
                    attached = bool(user32.AttachThreadInput(fg_tid, cur_tid, True))

                user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # HWND_TOPMOST
                user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # HWND_NOTOPMOST
                user32.SetForegroundWindow(hwnd)
                user32.BringWindowToTop(hwnd)
                user32.SetFocus(hwnd)

                if attached:
                    user32.AttachThreadInput(fg_tid, cur_tid, False)
            except Exception:
                pass


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
        try:
            self.hide()
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
                (1003, "alt+e", generate_knowledge_for_selected_text),
                (1004, "alt+r", translate_selected_text_russian),
                (1005, "alt+t", translate_selected_text_target_language),
            ]
            self._win32_hotkey_thread = Win32GlobalHotkeyThread(mappings)
            self._win32_hotkey_thread.start()
            print(f"[+] Win32 Donanım Kısayolları Devrede: {hotkey_str} (Düzeltme), Alt+W (EN), Alt+R (RU), Alt+T (Hedef Dil), Alt+E (Bilgi)")

        self.current_hotkey = hotkey_str

    def set_target_translate_language(self, lang_code: str):
        self.settings = settings_manager.load_settings()
        self.settings["target_translate_lang"] = lang_code
        settings_manager.save_settings(self.settings)
        from src.settings_manager import SUPPORTED_TRANSLATE_LANGS
        lang_name = SUPPORTED_TRANSLATE_LANGS.get(lang_code, lang_code)
        if hasattr(self, "lang_actions"):
            for c, act in self.lang_actions.items():
                act.setChecked(c == lang_code)
        if hasattr(self, "target_lang_menu"):
            self.target_lang_menu.setTitle(f"🌐 Hedef Çeviri (Alt+T: {lang_name})")
        if hasattr(self, "target_quick_action"):
            self.target_quick_action.setText(f"🚀 Şimdi Çevir ➜ {lang_name} (Alt+T)")
        if getattr(self, "floating_pill", None):
            self.floating_pill.update_target_lang(lang_code)
        _notification_manager.show_notification(
            "🌐 Hedef Dil Güncellendi",
            f"Alt+T kısayolu artık {lang_name} diline çevirecek."
        )

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
    QTimer.singleShot(300, tray_icon.show_settings_window)

    # REST API üzerinden /show çağrıldığında Qt ana thread'ine güvenli sinyal (pyqtSignal) gönder
    try:
        from src.web import CorrectionApiHandler
        from PyQt6.QtCore import QObject, pyqtSignal

        class _WindowShowBridge(QObject):
            trigger = pyqtSignal()

        _show_bridge = _WindowShowBridge()
        _show_bridge.trigger.connect(tray_icon.show_settings_window)
        tray_icon._show_bridge = _show_bridge
        CorrectionApiHandler.show_window_callback = _show_bridge.trigger.emit
    except Exception:
        pass

    _notification_manager.show_notification(
        "🇹🇷 Türkçe Otomatik Düzeltici",
        f"Çalışıyor! Düzeltme: {tray_icon.current_hotkey.upper()} | EN: ALT+W | RU: ALT+R | Bilgi: ALT+E"
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()