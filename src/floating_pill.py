"""
Yüzen Hızlı Düzeltme ve Çeviri Balonu (Floating Pill Widget — Grammarly / DeepL Modu).
Kullanıcı herhangi bir uygulamada (Tarayıcı, Discord, WhatsApp, Word, Notepad, Kod Editörü)
fareyle bir metin seçtiğinde imlecin hemen üstünde odak çalmadan (WS_EX_NOACTIVATE) belirir.
Tek tıkla '✨ Düzelt' veya '🌍 Çevir' işlemi uygular.
"""

import sys
import time
import ctypes
from ctypes import wintypes
from typing import Callable, Optional, Tuple

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFrame,
    QLabel,
    QApplication,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QCursor


PILL_STYLE = """
QFrame#pillContainer {
    background-color: rgba(15, 23, 42, 0.95);
    border: 1px solid rgba(56, 189, 248, 0.32);
    border-radius: 16px;
}
QFrame#resultCard {
    background-color: rgba(15, 23, 42, 0.97);
    border: 1px solid rgba(16, 185, 129, 0.45);
    border-radius: 12px;
    padding: 4px;
}
QLabel#resultTitle {
    color: #38bdf8;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 11px;
    font-weight: bold;
    background: transparent;
}
QLabel#resultBody {
    color: #f8fafc;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
    font-weight: 500;
    background: transparent;
    padding: 2px 4px;
}
QLabel#brandBadge {
    color: #f8fafc;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 12px;
    font-weight: bold;
    padding-left: 5px;
    padding-right: 3px;
    background: transparent;
}
QPushButton#fixBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e11d48, stop:1 #be123c);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    padding: 5px 11px;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#fixBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f43f5e, stop:1 #e11d48);
    border: 1px solid #fda4af;
}
QPushButton#fixBtn:pressed {
    background: #9f1239;
}
QPushButton#transBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0369a1);
    color: #ffffff;
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 10px;
    padding: 5px 11px;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#transBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #0284c7);
    color: #ffffff;
    border: 1px solid #7dd3fc;
}
QPushButton#transBtn:pressed {
    background: #075985;
}
QPushButton#ruBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #dc2626);
    color: #ffffff;
    border: 1px solid rgba(147, 197, 253, 0.35);
    border-radius: 10px;
    padding: 5px 11px;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#ruBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #ef4444);
    color: #ffffff;
    border: 1px solid #93c5fd;
}
QPushButton#ruBtn:pressed {
    background: #1e40af;
}
QPushButton#targetBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #047857);
    color: #ffffff;
    border: 1px solid rgba(52, 211, 153, 0.35);
    border-radius: 10px;
    padding: 5px 10px;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#targetBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
    color: #ffffff;
    border: 1px solid #6ee7b7;
}
QPushButton#targetBtn:pressed {
    background: #064e3b;
}
QPushButton#infoBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #b45309);
    color: #ffffff;
    border: 1px solid rgba(251, 191, 36, 0.35);
    border-radius: 10px;
    padding: 5px 11px;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#infoBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f59e0b, stop:1 #d97706);
    color: #ffffff;
    border: 1px solid #fde68a;
}
QPushButton#infoBtn:pressed {
    background: #92400e;
}
QPushButton#toneBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #6d28d9);
    color: #ffffff;
    border: 1px solid rgba(167, 139, 250, 0.35);
    border-radius: 10px;
    padding: 5px 11px;
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#toneBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #7c3aed);
    color: #ffffff;
    border: 1px solid #c4b5fd;
}
QPushButton#toneBtn:pressed {
    background: #5b21b6;
}
QPushButton#closeBtn {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 9px;
    padding: 3px 6px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#closeBtn:hover {
    background-color: rgba(239, 68, 68, 0.28);
    color: #f87171;
}
"""


class FloatingCorrectionPill(QWidget):
    """
    Odak çalmayan (Non-Activating) Yüzen Hızlı Düzeltme & Çeviri Balonu.
    Seçili metni bozmaz, hedef pencerenin odağını kaybettirmez.
    """
    result_ready_signal = pyqtSignal(str, str)

    def __init__(
        self,
        on_correct: Callable[[], None],
        on_translate: Callable[[], None],
        on_translate_ru: Optional[Callable[[], None]] = None,
        on_translate_target: Optional[Callable[[], None]] = None,
        on_select_target_lang: Optional[Callable[[str], None]] = None,
        on_info: Optional[Callable[[], None]] = None,
        on_tone: Optional[Callable[[], None]] = None,
        is_active_fn: Optional[Callable[[], bool]] = None,
        enabled: bool = True,
        target_lang: str = "de",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._on_correct = on_correct
        self._on_translate = on_translate
        self._on_translate_ru = on_translate_ru
        self._on_translate_target = on_translate_target
        self._on_select_target_lang = on_select_target_lang
        self._on_info = on_info
        self._on_tone = on_tone
        self._is_active_fn = is_active_fn or (lambda: True)
        self.enabled = enabled
        self._target_lang = target_lang
        self._last_result_text = ""

        # Hedef pencere ve fare seçim durumu
        self._target_hwnd: int = 0
        self._was_lbutton_down: bool = False
        self._drag_start_pos: Tuple[int, int] = (0, 0)
        self._drag_start_time: float = 0.0
        self._drag_start_hwnd: int = 0
        self._drag_start_rect: Optional[Tuple[int, int, int, int]] = None
        self._last_click_time: float = 0.0
        self._last_click_pos: Tuple[int, int] = (0, 0)
        self._shown_at: float = 0.0

        self._setup_window()
        self._setup_ui()
        self.result_ready_signal.connect(self._display_result_card_on_main_thread)

        # Otomatik gizleme zamanlayıcısı (4.5 saniye hareketsizlikte kaybolur)
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide_pill)

        # Hafif Win32 fare seçim dinleyicisi (30ms, <%0.01 CPU, tamamen ana GUI thread'inde)
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_mouse_selection)
        if sys.platform == "win32":
            self._poll_timer.start(30)

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(PILL_STYLE)

    def _apply_win32_noactivate(self):
        """Windows API düzeyinde WS_EX_NOACTIVATE uygular; tıklanınca hedef uygulamanın odağı gitmez."""
        if sys.platform != "win32":
            return
        try:
            import ctypes.wintypes
            user32 = ctypes.windll.user32
            hwnd = ctypes.wintypes.HWND(int(self.winId()))
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_TOPMOST = 0x00000008

            # 64-bit ve 32-bit güvenli SetWindowLong / GetWindowLong
            get_window_long = getattr(user32, "GetWindowLongPtrW", getattr(user32, "GetWindowLongW", None))
            set_window_long = getattr(user32, "SetWindowLongPtrW", getattr(user32, "SetWindowLongW", None))

            if get_window_long and set_window_long:
                ptr_type = ctypes.c_ssize_t if hasattr(user32, "GetWindowLongPtrW") else ctypes.c_long
                get_window_long.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
                get_window_long.restype = ptr_type
                set_window_long.argtypes = [ctypes.wintypes.HWND, ctypes.c_int, ptr_type]
                set_window_long.restype = ptr_type

                style = get_window_long(hwnd, GWL_EXSTYLE)
                set_window_long(
                    hwnd,
                    GWL_EXSTYLE,
                    style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST,
                )
        except Exception:
            pass

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(4)

        self.container = QFrame(self)
        self.container.setObjectName("pillContainer")
        self.container.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Yumuşak gölge efekti
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.container.setGraphicsEffect(shadow)

        pill_layout = QHBoxLayout(self.container)
        pill_layout.setContentsMargins(7, 4, 5, 4)
        pill_layout.setSpacing(5)

        self.brand_lbl = QLabel("🇹🇷")
        self.brand_lbl.setObjectName("brandBadge")
        self.brand_lbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        pill_layout.addWidget(self.brand_lbl)

        self.fix_btn = QPushButton("✨ Düzelt")
        self.fix_btn.setObjectName("fixBtn")
        self.fix_btn.setCursor( QCursor(Qt.CursorShape.PointingHandCursor) )
        self.fix_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.fix_btn.setToolTip("Seçili metni anında düzelt veya gelen yabancı mesajı Türkçeye çevir (Alt+Q)")
        self.fix_btn.clicked.connect(self._trigger_correct)
        pill_layout.addWidget(self.fix_btn)

        self.trans_btn = QPushButton("🌍 Çevir")
        self.trans_btn.setObjectName("transBtn")
        self.trans_btn.setCursor( QCursor(Qt.CursorShape.PointingHandCursor) )
        self.trans_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.trans_btn.setToolTip("Hangi dilde olursa olsun Türkçeye çevir / Türkçe ise İngilizceye çevir (Alt+W)")
        self.trans_btn.clicked.connect(self._trigger_translate)
        pill_layout.addWidget(self.trans_btn)

        self.ru_btn = QPushButton("🇷🇺 Rusça")
        self.ru_btn.setObjectName("ruBtn")
        self.ru_btn.setCursor( QCursor(Qt.CursorShape.PointingHandCursor) )
        self.ru_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.ru_btn.setToolTip("Seçili metni TR ⇄ RU (Rusça) çevir (Alt+R)")
        self.ru_btn.clicked.connect(self._trigger_translate_ru)
        pill_layout.addWidget(self.ru_btn)

        self.target_btn = QPushButton(f"🌐 {self._target_lang.upper()} ▾")
        self.target_btn.setObjectName("targetBtn")
        self.target_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.target_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.target_btn.setToolTip("Seçili hedef dile çevir (Alt+T). Tıklayarak hedef dili değiştirebilir veya çevirebilirsiniz.")
        self.target_btn.clicked.connect(self._handle_target_btn_click)
        pill_layout.addWidget(self.target_btn)

        self.info_btn = QPushButton("💡 Cevapla")
        self.info_btn.setObjectName("infoBtn")
        self.info_btn.setCursor( QCursor(Qt.CursorShape.PointingHandCursor) )
        self.info_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.info_btn.setToolTip("Bu soruya arkadaş ağzıyla anında cevap üret (Alt+E)")
        self.info_btn.clicked.connect(self._trigger_info)
        pill_layout.addWidget(self.info_btn)

        self.tone_btn = QPushButton("👔 Tonla")
        self.tone_btn.setObjectName("toneBtn")
        self.tone_btn.setCursor( QCursor(Qt.CursorShape.PointingHandCursor) )
        self.tone_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tone_btn.setToolTip("Seçili metni resmi/kurumsal iş diline çevir")
        self.tone_btn.clicked.connect(self._trigger_tone)
        pill_layout.addWidget(self.tone_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setCursor( QCursor(Qt.CursorShape.PointingHandCursor) )
        self.close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_btn.setToolTip("Gizle")
        self.close_btn.clicked.connect(self.hide_pill)
        pill_layout.addWidget(self.close_btn)

        outer_layout.addWidget(self.container)

        # Gelen Yabancı Mesaj Çeviri / Sonuç Kartı (Salt okunur Discord/Web ekranlarında anında okuma için)
        self.result_card = QFrame(self)
        self.result_card.setObjectName("resultCard")
        self.result_card.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        result_layout = QVBoxLayout(self.result_card)
        result_layout.setContentsMargins(8, 6, 8, 6)
        result_layout.setSpacing(3)

        top_res_bar = QHBoxLayout()
        self.result_title_lbl = QLabel("🌍 Çeviri Sonucu")
        self.result_title_lbl.setObjectName("resultTitle")
        top_res_bar.addWidget(self.result_title_lbl)
        top_res_bar.addStretch()

        self.copy_res_btn = QPushButton("📋 Kopyala")
        self.copy_res_btn.setObjectName("transBtn")
        self.copy_res_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_res_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.copy_res_btn.clicked.connect(self._copy_result_text)
        top_res_bar.addWidget(self.copy_res_btn)
        result_layout.addLayout(top_res_bar)

        self.result_body_lbl = QLabel("")
        self.result_body_lbl.setObjectName("resultBody")
        self.result_body_lbl.setWordWrap(True)
        self.result_body_lbl.setMaximumWidth(420)
        result_layout.addWidget(self.result_body_lbl)

        self.result_card.hide()
        outer_layout.addWidget(self.result_card)
        self.adjustSize()

    def _copy_result_text(self):
        if self._last_result_text:
            QApplication.clipboard().setText(self._last_result_text)
            self.copy_res_btn.setText("✅ Kopyalandı")
            QTimer.singleShot(1200, lambda: self.copy_res_btn.setText("📋 Kopyala"))

    def show_result_card(self, title: str, result_text: str):
        """Arka plan iş parçacıklarından güvenli şekilde yüzen çeviri/sonuç kartını açar."""
        if result_text and result_text.strip():
            self.result_ready_signal.emit(title, result_text.strip())

    def _display_result_card_on_main_thread(self, title: str, result_text: str):
        self._last_result_text = result_text
        self.result_title_lbl.setText(title)
        display_txt = result_text if len(result_text) <= 280 else result_text[:277] + "..."
        self.result_body_lbl.setText(display_txt)
        self.result_card.show()
        self.adjustSize()

        # İmlecin yanında göster
        pt = QCursor.pos()
        screen_x, screen_y = pt.x(), pt.y()
        w = self.width() or 320
        h = self.height() or 95
        pos_x = screen_x - int(w * 0.35)
        pos_y = screen_y - h - 14

        screen = QApplication.screenAt(pt) or QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            pos_x = max(geom.left() + 6, min(pos_x, geom.right() - w - 6))
            if pos_y < geom.top() + 6:
                pos_y = screen_y + 22
            pos_y = max(geom.top() + 6, min(pos_y, geom.bottom() - h - 6))

        self.move(pos_x, pos_y)
        self.show()
        self.raise_()
        self._apply_win32_noactivate()
        self._shown_at = time.time()
        self._auto_hide_timer.start(8000)

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)
        if not self.enabled and self.isVisible():
            self.hide_pill()

    def show_at(self, screen_x: int, screen_y: int, target_hwnd: int):
        """Balonu imlecin hemen üstünde ekran sınırlarını taşmadan gösterir."""
        if not self.enabled or not self._is_active_fn():
            return

        self.result_card.hide()
        self._target_hwnd = target_hwnd
        self.adjustSize()
        w = self.width() or 185
        h = self.height() or 42

        # İmlecin hafif sağ-üstünde konumlandır
        pos_x = screen_x - int(w * 0.35)
        pos_y = screen_y - h - 12

        # Ekran sınırlarını kontrol et
        screen = QApplication.screenAt(QPoint(screen_x, screen_y)) or QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            pos_x = max(geom.left() + 6, min(pos_x, geom.right() - w - 6))
            if pos_y < geom.top() + 6:
                pos_y = screen_y + 20  # Üstte yer yoksa imlecin altında göster
            # Alt kenar taşmasını önle (görev çubuğuna çarpmasın)
            pos_y = max(geom.top() + 6, min(pos_y, geom.bottom() - h - 6))

        self.move(pos_x, pos_y)
        self.show()
        self.raise_()
        self._apply_win32_noactivate()
        self._shown_at = time.time()
        self._auto_hide_timer.start(4500)

    def hide_pill(self):
        self._auto_hide_timer.stop()
        self.result_card.hide()
        if self.isVisible():
            self.hide()

    def _restore_target_focus(self):
        """Hedef uygulamanın pencere odağını korur."""
        if sys.platform == "win32" and self._target_hwnd:
            try:
                import ctypes.wintypes
                user32 = ctypes.windll.user32
                user32.GetForegroundWindow.restype = ctypes.wintypes.HWND
                user32.SetForegroundWindow.argtypes = [ctypes.wintypes.HWND]
                fg = user32.GetForegroundWindow()
                if fg != self._target_hwnd:
                    user32.SetForegroundWindow(ctypes.wintypes.HWND(self._target_hwnd))
                    time.sleep(0.015)
            except Exception:
                pass

    def _trigger_correct(self):
        import threading
        self.hide_pill()
        self._restore_target_focus()
        threading.Thread(target=self._on_correct, daemon=True).start()

    def _trigger_translate(self):
        import threading
        self.hide_pill()
        self._restore_target_focus()
        threading.Thread(target=self._on_translate, daemon=True).start()

    def _trigger_translate_ru(self):
        if not self._on_translate_ru:
            return
        import threading
        self.hide_pill()
        self._restore_target_focus()
        threading.Thread(target=self._on_translate_ru, daemon=True).start()

    def update_target_lang(self, lang_code: str):
        self._target_lang = lang_code
        if hasattr(self, "target_btn"):
            self.target_btn.setText(f"🌐 {lang_code.upper()} ▾")

    def _trigger_translate_target(self):
        if not getattr(self, "_on_translate_target", None):
            return
        import threading
        self.hide_pill()
        self._restore_target_focus()
        threading.Thread(target=self._on_translate_target, daemon=True).start()

    def _handle_target_btn_click(self):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        from src.settings_manager import SUPPORTED_TRANSLATE_LANGS

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 11px;
            }
            QMenu::item {
                padding: 6px 14px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: #059669;
                color: #ffffff;
            }
        """)

        cur_name = SUPPORTED_TRANSLATE_LANGS.get(self._target_lang, self._target_lang.upper())
        quick_act = QAction(f"🚀 Şimdi Çevir ➜ {cur_name} (Alt+T)", menu)
        quick_act.triggered.connect(self._trigger_translate_target)
        menu.addAction(quick_act)
        menu.addSeparator()

        for code, name in SUPPORTED_TRANSLATE_LANGS.items():
            check_mark = " ✓" if code == self._target_lang else ""
            act = QAction(f"{name}{check_mark}", menu)
            def _choose_and_translate(checked=False, c=code):
                self.update_target_lang(c)
                if getattr(self, "_on_select_target_lang", None):
                    try:
                        self._on_select_target_lang(c)
                    except Exception:
                        pass
                self._trigger_translate_target()
            act.triggered.connect(_choose_and_translate)
            menu.addAction(act)

        menu.exec(QCursor.pos())

    def _trigger_info(self):
        if not self._on_info:
            return
        import threading
        self.hide_pill()
        self._restore_target_focus()
        threading.Thread(target=self._on_info, daemon=True).start()

    def _trigger_tone(self):
        if not self._on_tone:
            return
        import threading
        self.hide_pill()
        self._restore_target_focus()
        threading.Thread(target=self._on_tone, daemon=True).start()

    @staticmethod
    def _get_window_rect(hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        if sys.platform != "win32" or not hwnd:
            return None
        try:
            rect = wintypes.RECT()
            if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return (rect.left, rect.top, rect.right, rect.bottom)
        except Exception:
            pass
        return None

    def _poll_mouse_selection(self):
        """
        Fare ile metin seçimini (sürükleyerek seçme veya çift tıklama) sıfır pano kirliliğiyle algılar.
        """
        if sys.platform != "win32":
            return
        if not self.enabled or not self._is_active_fn():
            if self.isVisible():
                self.hide_pill()
            return

        try:
            user32 = ctypes.windll.user32
            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            cur_x, cur_y = pt.x, pt.y

            # Fare balonun üzerindeyse otomatik kapanma süresini uzat
            if self.isVisible() and self.geometry().contains(cur_x, cur_y):
                self._auto_hide_timer.start(2500)
                self._was_lbutton_down = bool(user32.GetAsyncKeyState(0x01) & 0x8000)
                return

            # Kullanıcı ESC veya yazı tuşuna bastıysa balonu gizle
            if self.isVisible() and (time.time() - self._shown_at) > 0.25:
                for vk in (0x1B, 0x08, 0x0D):  # ESC, Backspace, Enter
                    if user32.GetAsyncKeyState(vk) & 0x8000:
                        self.hide_pill()
                        break

            lbutton_down = bool(user32.GetAsyncKeyState(0x01) & 0x8000)
            now = time.time()

            # 1. Sol tık basıldı (Mouse Down)
            if lbutton_down and not self._was_lbutton_down:
                if self.isVisible():
                    self.hide_pill()
                fg_hwnd = user32.GetForegroundWindow()
                self._drag_start_pos = (cur_x, cur_y)
                self._drag_start_time = now
                self._drag_start_hwnd = fg_hwnd
                self._drag_start_rect = self._get_window_rect(fg_hwnd)

            # 2. Sol tık bırakıldı (Mouse Up)
            elif not lbutton_down and self._was_lbutton_down:
                fg_hwnd = user32.GetForegroundWindow()
                my_hwnd = int(self.winId()) if self.isVisible() else 0

                if fg_hwnd and fg_hwnd != my_hwnd and fg_hwnd == self._drag_start_hwnd:
                    end_rect = self._get_window_rect(fg_hwnd)
                    # Pencere taşınmamış/boyutlandırılmamış olmalı
                    if self._drag_start_rect and end_rect == self._drag_start_rect:
                        left, top, right, bottom = end_rect
                        # Başlık çubuğu (üst 38px) veya sağ kaydırma çubuğu (sağ 24px) değilse
                        in_client_area = (
                            (cur_y - top) > 38
                            and (right - cur_x) > 24
                            and (bottom - cur_y) > 16
                        )
                        if in_client_area:
                            dx = abs(cur_x - self._drag_start_pos[0])
                            dy = abs(cur_y - self._drag_start_pos[1])
                            dt = now - self._drag_start_time

                            # A) Yatay/paragraf metin sürükleme seçimi
                            is_drag_select = (
                                dx >= 22
                                and dy < 350
                                and not (dy > dx * 2.5)
                                and 0.07 <= dt <= 6.0
                            )

                            # B) Kelime üzerine çift tıklama seçimi
                            click_dist = abs(cur_x - self._last_click_pos[0]) + abs(cur_y - self._last_click_pos[1])
                            is_double_click = (
                                dx <= 6
                                and dy <= 6
                                and (now - self._last_click_time) <= 0.35
                                and click_dist <= 8
                            )

                            if is_drag_select or is_double_click:
                                self.show_at(cur_x, cur_y, fg_hwnd)

                            if dx <= 6 and dy <= 6:
                                self._last_click_time = now
                                self._last_click_pos = (cur_x, cur_y)

            self._was_lbutton_down = lbutton_down
        except Exception:
            pass
