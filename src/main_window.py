"""
Türkçe Otomatik Düzeltici - Modern Görsel Arayüz (Studio UI).
Çift panelli canlı düzeltme, TDK kuralları, deasciifier, asciifier,
harf dönüşümleri, diff görünümü, kullanım istatistikleri ve ayarlar içerir.
"""

import sys
import os
import time
from difflib import ndiff
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget, QKeySequenceEdit,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QGroupBox, QFormLayout, QComboBox, QSplitter, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QKeySequence, QIcon

# Import managers and engine
from src import settings_manager
from src import statistics_manager
from src import notifications
from src import self_learning
from src.grammar import fix_sentence
from src.deasciifier import deasciify_text, asciify_text
from src.turkish_case import turkish_lower, turkish_upper, turkish_capitalize
from src.dictionary import (
    list_personal_words,
    add_personal_word,
    remove_personal_word
)
from src.autostart import set_autostart, is_autostart_enabled
from src.ai_engine import fix_with_ai, test_nvidia_connection, AVAILABLE_MODELS

SAMPLE_TEXTS = [
    ("Örnek 1: Bitişik ve Hatalı Kelimeler", "sendemigeliyorusn yarinaksam toplanalimmi"),
    ("Örnek 2: De-asciifier (İngilizce Harfler)", "ogrencileringozlerindensevincokunuyorducunkuokullaracildi"),
    ("Örnek 3: Chat Argosu ve Kısaltmalar", "slm knk nbr bugun dcydemisin oyun alakmi"),
    ("Örnek 4: Harf Uzatmaları", "çoooook tesekkurler lütfeeeen geliyoruuuum"),
    ("Örnek 5: TDK Yaygın Hataları", "herkez birşey biliyo ama yanlız kaldım orjinal labaratuvar")
]

DARK_STYLE = """
QMainWindow {
    background-color: #0f172a;
    color: #f8fafc;
}
QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f172a;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #1e293b;
    color: #94a3b8;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QGroupBox {
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: bold;
    color: #38bdf8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QTextEdit, QLineEdit, QListWidget, QTableWidget {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
    selection-background-color: #2563eb;
}
QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #38bdf8;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    border: none;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QPushButton#actionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #7c3aed);
    color: white;
    font-size: 14px;
    padding: 10px 24px;
    border-radius: 8px;
}
QPushButton#secondaryBtn {
    background-color: #334155;
    color: #e2e8f0;
}
QPushButton#secondaryBtn:hover {
    background-color: #475569;
}
QComboBox {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
}
QCheckBox {
    color: #e2e8f0;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background: #1e293b;
}
QCheckBox::indicator:checked {
    background: #2563eb;
    border-color: #38bdf8;
}
QHeaderView::section {
    background-color: #334155;
    color: #f8fafc;
    padding: 6px;
    border: none;
    font-weight: bold;
}
"""

LIGHT_STYLE = """
QMainWindow {
    background-color: #f8fafc;
    color: #0f172a;
}
QTabWidget::pane {
    border: 1px solid #cbd5e1;
    background-color: #ffffff;
    border-radius: 8px;
}
QTabBar::tab {
    background-color: #e2e8f0;
    color: #475569;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background-color: #2563eb;
    color: #ffffff;
}
QGroupBox {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: bold;
    color: #0284c7;
}
QTextEdit, QLineEdit, QListWidget, QTableWidget {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    border: none;
}
QPushButton#secondaryBtn {
    background-color: #e2e8f0;
    color: #1e293b;
}
"""


class MainWindow(QMainWindow):
    def __init__(self, tray_icon=None):
        super().__init__()
        self.tray_icon = tray_icon
        self.setWindowTitle("🇹🇷 Türkçe Otomatik Düzeltici — Gelişmiş Stüdyo & NVIDIA AI")
        self.setMinimumSize(QSize(900, 620))

        # İkon yükle
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Yöneticileri başlat
        self.settings = settings_manager.load_settings()
        self.stats_manager = statistics_manager.StatisticsManager()
        self.notification_manager = notifications.NotificationManager(tray_icon=self.tray_icon)

        # Canlı düzeltme debounce zamanlayıcısı
        self.live_timer = QTimer(self)
        self.live_timer.setSingleShot(True)
        self.live_timer.timeout.connect(self.perform_live_correction)

        # Arayüzü kur
        self.setup_ui()
        self.apply_theme(self.settings.get("theme", "dark"))
        self.load_settings_into_ui()
        self.update_dashboard()

        # İstatistik güncelleme timer'ı
        self.dashboard_timer = QTimer(self)
        self.dashboard_timer.timeout.connect(self.update_dashboard)
        self.dashboard_timer.start(5000)

    def apply_theme(self, theme_name: str):
        if theme_name == "light":
            self.setStyleSheet(LIGHT_STYLE)
        else:
            self.setStyleSheet(DARK_STYLE)

    def setup_ui(self):
        """Ana sekmeleri oluştur."""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 1. Sekme: Düzeltme & Çevirme Stüdyosu
        self.studio_tab = QWidget()
        self.setup_studio_tab()
        self.tabs.addTab(self.studio_tab, "✨ Düzeltme & Çevirme Stüdyosu")

        # 2. Sekme: Kullanım İstatistikleri & Tasarruf Paneli
        self.dashboard_tab = QWidget()
        self.setup_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "📊 İstatistikler & Tasarruf")

        # 3. Sekme: Kişisel Sözlük & Öz-Öğrenme
        self.dict_tab = QWidget()
        self.setup_dict_tab()
        self.tabs.addTab(self.dict_tab, "📖 Kişisel Sözlük & Öz-Öğrenme")

        # 4. Sekme: Ayarlar
        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "⚙️ Ayarlar & Kısayollar")

    # ==================== 1. STÜDYO SEKMESİ ====================
    def setup_studio_tab(self):
        main_layout = QVBoxLayout(self.studio_tab)
        main_layout.setSpacing(10)

        # Üst Araç Çubuğu
        top_bar = QHBoxLayout()

        # Mod Seçici
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "🤖 Otomatik Akıllı Algılama (Stil, Harf Düzeni ve İmlayı Kendi Anlar)",
            "✨ Yapay Zeka ile Düzelt (NVIDIA NIM / Llama 3.2)",
            "🇹🇷 Tam Akıllı Düzeltme (TDK + Segmenter + İmla + Noktalama)",
            "🔤 De-asciifier (ASCII ➜ Türkçe Harfler: c,g,i,o,s,u ➜ ç,ğ,ı,ö,ş,ü)",
            "🌐 Asciifier (Türkçe ➜ ASCII: ç,ğ,ı,ö,ş,ü ➜ c,g,i,o,s,u)",
            "🔠 Cümle Düzeni (İlk harfler büyük)",
            "🔠 TÜMÜ BÜYÜK HARF",
            "🔡 tümü küçük harf",
            "🔠 Baş Harfleri Büyüt (Başlık Düzeni)"
        ])
        top_bar.addWidget(QLabel("Dönüşüm Modu:"))
        top_bar.addWidget(self.mode_combo, stretch=2)

        # Örnek Metinler
        self.sample_combo = QComboBox()
        self.sample_combo.addItem("💡 Örnek Metin Seç...")
        for title, _ in SAMPLE_TEXTS:
            self.sample_combo.addItem(title)
        self.sample_combo.currentIndexChanged.connect(self.load_sample_text)
        top_bar.addWidget(self.sample_combo, stretch=1)

        # Canlı Düzeltme Toggle
        self.live_check = QCheckBox("⚡ Canlı Düzelt (Yazdıkça)")
        self.live_check.setChecked(False)
        top_bar.addWidget(self.live_check)

        main_layout.addLayout(top_bar)

        # Çift Panelli Editör Alanı (Giriş / Çıkış)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sol Panel (Giriş)
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)

        input_header = QHBoxLayout()
        input_header.addWidget(QLabel("<b>Giriş Metni:</b>"))
        self.input_stats_label = QLabel("0 karakter | 0 kelime")
        self.input_stats_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        input_header.addStretch()
        input_header.addWidget(self.input_stats_label)

        self.clear_btn = QPushButton("🗑️ Temizle")
        self.clear_btn.setObjectName("secondaryBtn")
        self.clear_btn.clicked.connect(self.clear_text)
        input_header.addWidget(self.clear_btn)

        input_layout.addLayout(input_header)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Düzeltilecek veya çevrilecek Türkçe metni buraya yazın veya yapıştırın...\n(Örn: sendemigeliyorusn bugun hava cok guzel)")
        self.input_edit.textChanged.connect(self.on_input_text_changed)
        input_layout.addWidget(self.input_edit)

        splitter.addWidget(input_widget)

        # Sağ Panel (Çıktı)
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_layout.setContentsMargins(0, 0, 0, 0)

        output_header = QHBoxLayout()
        output_header.addWidget(QLabel("<b>Düzeltilmiş / Çevrilmiş Sonuç:</b>"))
        self.output_stats_label = QLabel("0 karakter | 0 kelime")
        self.output_stats_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        output_header.addStretch()
        output_header.addWidget(self.output_stats_label)

        self.diff_check = QCheckBox("🔍 Farkları Göster (Diff)")
        self.diff_check.toggled.connect(self.toggle_diff_view)
        output_header.addWidget(self.diff_check)

        self.copy_btn = QPushButton("📋 Kopyala")
        self.copy_btn.clicked.connect(self.copy_output)
        output_header.addWidget(self.copy_btn)

        output_layout.addLayout(output_header)

        self.output_edit = QTextEdit()
        self.output_edit.setPlaceholderText("Düzeltilmiş sonuç burada görünecektir.")
        output_layout.addWidget(self.output_edit)

        splitter.addWidget(output_widget)
        main_layout.addWidget(splitter, stretch=1)

        # Alt Buton & Bilgi Çubuğu
        bottom_bar = QHBoxLayout()

        self.status_msg_label = QLabel("Hazır. Çevrimdışı ve 0-Token yerel motor devrede.")
        self.status_msg_label.setStyleSheet("color: #10b981; font-weight: 500;")
        bottom_bar.addWidget(self.status_msg_label)

        bottom_bar.addStretch()

        self.correct_btn = QPushButton("✨ Şimdi Düzelt")
        self.correct_btn.setObjectName("actionBtn")
        self.correct_btn.clicked.connect(self.perform_manual_correction)
        bottom_bar.addWidget(self.correct_btn)

        main_layout.addLayout(bottom_bar)

    def on_input_text_changed(self):
        text = self.input_edit.toPlainText()
        chars = len(text)
        words = len(text.split())
        self.input_stats_label.setText(f"{chars} karakter | {words} kelime")

        if self.live_check.isChecked():
            self.live_timer.start(250)

    def load_sample_text(self, index: int):
        if index > 0 and index <= len(SAMPLE_TEXTS):
            _, text = SAMPLE_TEXTS[index - 1]
            self.input_edit.setPlainText(text)
            self.perform_manual_correction()

    def clear_text(self):
        self.input_edit.clear()
        self.output_edit.clear()
        self.status_msg_label.setText("Temizlendi.")

    def copy_output(self):
        text = self.output_edit.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.copy_btn.setText("✅ Kopyalandı!")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("📋 Kopyala"))

    def perform_live_correction(self):
        self.apply_transformation(record_stats=False)

    def perform_manual_correction(self):
        self.apply_transformation(record_stats=True)

    def apply_transformation(self, record_stats: bool = True):
        try:
            raw_text = self.input_edit.toPlainText().strip()
            if not raw_text:
                self.output_edit.clear()
                return

            mode_idx = self.mode_combo.currentIndex()
            t0 = time.time()

            engine_label = "Yerel Motor"
            if mode_idx == 0:
                # 🤖 Otomatik Akıllı Algılama
                is_all_caps = raw_text.isupper() and len([c for c in raw_text if c.isalpha()]) > 2
                result = fix_sentence(raw_text)
                if is_all_caps:
                    result = turkish_upper(result)
                engine_label = "Akıllı İmla & Yerel Motor"
            elif mode_idx == 1:
                # ✨ Yapay Zeka ile Düzelt (NVIDIA NIM)
                ai_res = fix_with_ai(raw_text)
                if ai_res and ai_res.strip():
                    result = ai_res.strip()
                    engine_label = "NVIDIA NIM AI (Llama 3.2)"
                else:
                    # Geri düşüş
                    result = fix_sentence(raw_text)
                    engine_label = "Yerel Motor (NVIDIA API Anahtarı Yok / Bağlantı Hatası)"
            elif mode_idx == 2:
                # Tam Akıllı Düzeltme
                result = fix_sentence(raw_text)
                engine_label = "TDK & Dilbilgisi Motoru"
            elif mode_idx == 3:
                # De-asciifier
                result = deasciify_text(raw_text)
                engine_label = "De-asciifier"
            elif mode_idx == 4:
                # Asciifier
                result = asciify_text(raw_text)
                engine_label = "Asciifier"
            elif mode_idx == 5:
                # Cümle Düzeni
                sentences = raw_text.split(".")
                result = ". ".join(turkish_capitalize(s.strip()) for s in sentences if s.strip())
                if raw_text.endswith("."):
                    result += "."
                engine_label = "Cümle Düzeni"
            elif mode_idx == 6:
                # TÜMÜ BÜYÜK
                result = turkish_upper(raw_text)
                engine_label = "Büyük Harf"
            elif mode_idx == 7:
                # tümü küçük
                result = turkish_lower(raw_text)
                engine_label = "Küçük Harf"
            elif mode_idx == 8:
                # Baş Harfleri Büyüt
                result = " ".join(turkish_capitalize(w) for w in raw_text.split())
                engine_label = "Başlık Düzeni"
            else:
                result = fix_sentence(raw_text)

            elapsed_ms = (time.time() - t0) * 1000

            # Diff görünümü veya düz metin
            if self.diff_check.isChecked():
                self.render_diff(raw_text, result)
            else:
                self.output_edit.setPlainText(result)

            chars = len(result)
            words = len(result.split())
            self.output_stats_label.setText(f"{chars} karakter | {words} kelime")
            self.status_msg_label.setText(f"İşlem tamamlandı ({elapsed_ms:.1f} ms) — [{engine_label}]")
            self.status_msg_label.setStyleSheet("color: #10b981; font-weight: 500;")

            # İstatistik kaydı (güvenli blok, hata arayüzü çökertemez)
            if record_stats and raw_text != result:
                try:
                    self.stats_manager.record_correction(raw_text, result)
                    self.update_dashboard()
                except Exception as stat_err:
                    print(f"İstatistik güncelleme uyarısı: {stat_err}")
        except Exception as e:
            self.status_msg_label.setText(f"İşlem Hatası: {e}")
            self.status_msg_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            print(f"Arayüz düzeltme hatası: {e}")

    def toggle_diff_view(self, checked: bool):
        raw = self.input_edit.toPlainText()
        out = self.output_edit.toPlainText()
        if checked and raw and out:
            self.render_diff(raw, out)
        elif not checked and out:
            # Düz metne geri dön
            self.output_edit.setPlainText(out)

    def render_diff(self, original: str, corrected: str):
        """Orijinal ve düzeltilmiş arasındaki farkları renkli HTML olarak gösterir."""
        orig_words = original.split()
        corr_words = corrected.split()

        diff = list(ndiff(orig_words, corr_words))
        html_parts = []
        for token in diff:
            code = token[0]
            word = token[2:]
            if code == " ":
                html_parts.append(f"<span style='color:#e2e8f0;'>{word}</span>")
            elif code == "-":
                html_parts.append(f"<span style='color:#ef4444; text-decoration: line-through; background-color: rgba(239, 68, 68, 0.15); padding: 2px 4px; border-radius: 4px;'>{word}</span>")
            elif code == "+":
                html_parts.append(f"<span style='color:#10b981; font-weight: bold; background-color: rgba(16, 185, 129, 0.15); padding: 2px 4px; border-radius: 4px;'>{word}</span>")

        self.output_edit.setHtml(" ".join(html_parts))

    # ==================== 2. İSTATİSTİKLER SEKMESİ ====================
    def setup_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)

        stats_group = QGroupBox("Kullanım & Tasarruf Göstergeleri")
        stats_layout = QVBoxLayout()

        cards_layout = QHBoxLayout()
        self.total_card = QLabel("Toplam Düzeltilen Kelime:\n0")
        self.total_card.setStyleSheet("background: #1e293b; padding: 15px; border-radius: 8px; font-size: 14px; font-weight: bold; color: #38bdf8;")
        self.time_card = QLabel("Tasarruf Edilen Süre:\n0 saniye")
        self.time_card.setStyleSheet("background: #1e293b; padding: 15px; border-radius: 8px; font-size: 14px; font-weight: bold; color: #10b981;")

        cards_layout.addWidget(self.total_card)
        cards_layout.addWidget(self.time_card)
        stats_layout.addLayout(cards_layout)

        # En Sık Düzeltilen Hatalar Tablosu
        stats_layout.addWidget(QLabel("<b>En Sık Düzeltilen Kelimeler:</b>"))
        self.top_table = QTableWidget()
        self.top_table.setColumnCount(3)
        self.top_table.setHorizontalHeaderLabels(["Hatalı Kelime", "Düzeltilmiş Hali", "Düzeltme Sayısı"])
        self.top_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.top_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.top_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        stats_layout.addWidget(self.top_table)

        self.reset_btn = QPushButton("🗑️ İstatistikleri Sıfırla")
        self.reset_btn.setObjectName("secondaryBtn")
        self.reset_btn.clicked.connect(self.reset_statistics)
        stats_layout.addWidget(self.reset_btn, alignment=Qt.AlignmentFlag.AlignRight)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

    def update_dashboard(self):
        total = self.stats_manager.get_total_corrections()
        self.total_card.setText(f"Toplam Düzeltilen Kelime:\n{total}")

        time_saved = self.stats_manager.get_time_saved_formatted()
        self.time_card.setText(f"Tasarruf Edilen Süre:\n{time_saved}")

        top_corrections = self.stats_manager.get_top_corrections(10)
        self.top_table.setRowCount(len(top_corrections))
        for row, (orig, corr, freq) in enumerate(top_corrections):
            self.top_table.setItem(row, 0, QTableWidgetItem(orig))
            self.top_table.setItem(row, 1, QTableWidgetItem(corr))
            self.top_table.setItem(row, 2, QTableWidgetItem(str(freq)))

        # Öz-Öğrenme Listesini Güncelle
        try:
            learned_words = self_learning.get_learned_words()
            self.learned_count_label.setText(f"Sistemin Kendi Öğrendiği Kelimeler ({len(learned_words)}):")
            self.learned_list.clear()
            for w in learned_words:
                self.learned_list.addItem(w)
        except Exception:
            pass

    def reset_statistics(self):
        reply = QMessageBox.question(
            self, "Onay",
            "Tüm kullanım istatistiklerini silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.stats_manager.clear_statistics()
            self.update_dashboard()
            QMessageBox.information(self, "Bilgi", "İstatistikler sıfırlandı.")

    # ==================== 3. KİŞİSEL SÖZLÜK SEKMESİ ====================
    def setup_dict_tab(self):
        layout = QVBoxLayout(self.dict_tab)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sol: Kullanıcı Kişisel Sözlüğü
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("<b>Kullanıcı Tanımlı Özel Kelimeler:</b>"))

        self.dict_list = QListWidget()
        left_layout.addWidget(self.dict_list)

        add_bar = QHBoxLayout()
        self.new_word_edit = QLineEdit()
        self.new_word_edit.setPlaceholderText("Özel kelime ekle (örn: Valorant, Enes)...")
        self.new_word_edit.returnPressed.connect(self.add_word_action)
        self.add_word_btn = QPushButton("➕ Ekle")
        self.add_word_btn.clicked.connect(self.add_word_action)
        add_bar.addWidget(self.new_word_edit)
        add_bar.addWidget(self.add_word_btn)
        left_layout.addLayout(add_bar)

        self.delete_word_btn = QPushButton("🗑️ Seçili Kelimeyi Kaldır")
        self.delete_word_btn.setObjectName("secondaryBtn")
        self.delete_word_btn.clicked.connect(self.delete_word_action)
        left_layout.addWidget(self.delete_word_btn)

        splitter.addWidget(left_widget)

        # Sağ: Otomatik Öğrenilen Kelimeler
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.learned_count_label = QLabel("<b>Sistemin Kendi Öğrendiği Kelimeler (0):</b>")
        right_layout.addWidget(self.learned_count_label)

        self.learned_list = QListWidget()
        right_layout.addWidget(self.learned_list)

        info_lbl = QLabel("Öz-öğrenme motoru, kullanıcının düzelttiği ve geri almadığı (Ctrl+Z basılmayan) kelimeleri otomatik öğrenir.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        right_layout.addWidget(info_lbl)

        splitter.addWidget(right_widget)
        layout.addWidget(splitter)

        self.refresh_personal_dict_list()

    def refresh_personal_dict_list(self):
        self.dict_list.clear()
        for w in list_personal_words():
            self.dict_list.addItem(w)

    def add_word_action(self):
        w = self.new_word_edit.text().strip()
        if not w:
            return
        try:
            if add_personal_word(w):
                self.refresh_personal_dict_list()
                self.new_word_edit.clear()
            else:
                QMessageBox.information(self, "Bilgi", f"'{w}' zaten sözlükte mevcut.")
        except ValueError as exc:
            QMessageBox.warning(self, "Hata", str(exc))

    def delete_word_action(self):
        item = self.dict_list.currentItem()
        if not item:
            return
        w = item.text()
        if remove_personal_word(w):
            self.refresh_personal_dict_list()

    # ==================== 4. AYARLAR SEKMESİ ====================
    def setup_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)

        # Kısayol Tuşu
        hotkey_group = QGroupBox("Global Kısayol Tuşu")
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel("Metin Seçildiğinde Tetiklenecek Kısayol:"))
        self.hotkey_edit = QKeySequenceEdit()
        hotkey_layout.addWidget(self.hotkey_edit)
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)

        # Genel Seçenekler
        opt_group = QGroupBox("Davranış & Arayüz Seçenekleri")
        opt_layout = QFormLayout()

        self.startup_check = QCheckBox("Windows Başlangıcında Otomatik Başlat")
        self.sound_check = QCheckBox("Düzeltme Yapıldığında Ses Efekti Çal")
        self.slang_check = QCheckBox("Chat Kısaltmalarını Aç (slm -> selam, tşk -> teşekkürler)")
        self.elongation_check = QCheckBox("Aşırı Harf Uzatmalarını Temizle (geliyoruuuum -> geliyorum)")

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Koyu Tema (Dark Mode)", "Açık Tema (Light Mode)"])

        opt_layout.addRow(self.startup_check)
        opt_layout.addRow(self.sound_check)
        opt_layout.addRow(self.slang_check)
        opt_layout.addRow(self.elongation_check)
        opt_layout.addRow("Görsel Tema:", self.theme_combo)

        opt_group.setLayout(opt_layout)
        layout.addWidget(opt_group)

        # NVIDIA AI Yapılandırması
        ai_group = QGroupBox("✨ Yapay Zeka Desteği (NVIDIA NIM / Ücretsiz API)")
        ai_layout = QFormLayout()

        ai_info = QLabel("build.nvidia.com üzerinden aldığınız ücretsiz API anahtarı (nvapi-...) ile Llama 3.3 70B gibi dev modellerle bağlamsal düzeltme yapabilirsiniz. Boş bırakılırsa sistem 0 gecikmeli yerel motorla çalışır.")
        ai_info.setWordWrap(True)
        ai_info.setStyleSheet("color: #94a3b8; font-size: 11px; margin-bottom: 4px;")
        ai_layout.addRow(ai_info)

        key_box = QHBoxLayout()
        self.ai_key_edit = QLineEdit()
        self.ai_key_edit.setPlaceholderText("nvapi-...")
        self.ai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_key_toggle_btn = QPushButton("👁️ Göster")
        self.ai_key_toggle_btn.setObjectName("secondaryBtn")
        self.ai_key_toggle_btn.clicked.connect(self.toggle_ai_key_visibility)
        key_box.addWidget(self.ai_key_edit)
        key_box.addWidget(self.ai_key_toggle_btn)
        ai_layout.addRow("NVIDIA API Anahtarı:", key_box)

        self.ai_model_combo = QComboBox()
        for model_id, model_label in AVAILABLE_MODELS:
            self.ai_model_combo.addItem(model_label, model_id)
        ai_layout.addRow("AI Modeli:", self.ai_model_combo)

        self.ai_tray_check = QCheckBox("Alt+Q kısayolunda öncelikli olarak NVIDIA AI motorunu kullan")
        ai_layout.addRow(self.ai_tray_check)

        test_box = QHBoxLayout()
        self.test_ai_btn = QPushButton("🔌 API Bağlantısını Test Et")
        self.test_ai_btn.setObjectName("secondaryBtn")
        self.test_ai_btn.clicked.connect(self.test_ai_action)
        self.ai_test_result_label = QLabel("")
        self.ai_test_result_label.setStyleSheet("font-size: 11px;")
        test_box.addWidget(self.test_ai_btn)
        test_box.addWidget(self.ai_test_result_label)
        test_box.addStretch()
        ai_layout.addRow(test_box)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # Kaydet Butonu
        self.save_btn = QPushButton("💾 Ayarları Kaydet ve Uygula")
        self.save_btn.setObjectName("actionBtn")
        self.save_btn.clicked.connect(self.save_settings_action)
        layout.addWidget(self.save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addStretch()

    def toggle_ai_key_visibility(self):
        if self.ai_key_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.ai_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.ai_key_toggle_btn.setText("🔒 Gizle")
        else:
            self.ai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.ai_key_toggle_btn.setText("👁️ Göster")

    def test_ai_action(self):
        key = self.ai_key_edit.text().strip()
        if not key:
            self.ai_test_result_label.setText("❌ Lütfen önce bir API anahtarı girin.")
            self.ai_test_result_label.setStyleSheet("color: #ef4444; font-size: 11px;")
            return

        model_id = self.ai_model_combo.currentData() or "meta/llama-3.3-70b-instruct"
        self.ai_test_result_label.setText("⏳ Bağlantı test ediliyor...")
        self.ai_test_result_label.setStyleSheet("color: #38bdf8; font-size: 11px;")
        QApplication.processEvents()

        ok, msg, latency = test_nvidia_connection(key, model_id)
        if ok:
            self.ai_test_result_label.setText(f"✅ {msg} ({latency} ms)")
            self.ai_test_result_label.setStyleSheet("color: #10b981; font-size: 11px; font-weight: bold;")
        else:
            self.ai_test_result_label.setText(f"❌ {msg}")
            self.ai_test_result_label.setStyleSheet("color: #ef4444; font-size: 11px;")

    def load_settings_into_ui(self):
        self.hotkey_edit.setKeySequence(QKeySequence(self.settings.get("hotkey", "alt+q")))
        reg_autostart = is_autostart_enabled() if sys.platform == "win32" else self.settings.get("startup_toggle", False)
        self.startup_check.setChecked(reg_autostart)
        self.sound_check.setChecked(self.settings.get("sound_toggle", True))
        self.slang_check.setChecked(self.settings.get("slang_expansion", True))
        self.elongation_check.setChecked(self.settings.get("elongation_cleanup", True))
        current_theme = self.settings.get("theme", "dark")
        self.theme_combo.setCurrentIndex(0 if current_theme == "dark" else 1)

        # AI Ayarları Yükle
        self.ai_key_edit.setText(self.settings.get("nvidia_api_key", ""))
        saved_model = self.settings.get("ai_model", "meta/llama-3.3-70b-instruct")
        idx = self.ai_model_combo.findData(saved_model)
        if idx >= 0:
            self.ai_model_combo.setCurrentIndex(idx)
        self.ai_tray_check.setChecked(self.settings.get("use_ai_in_tray", False))

    def save_settings_action(self):
        hotkey_str = self.hotkey_edit.keySequence().toString(QKeySequence.SequenceFormat.NativeText).lower()
        if not hotkey_str:
            hotkey_str = "alt+q"

        theme = "dark" if self.theme_combo.currentIndex() == 0 else "light"
        startup_enabled = self.startup_check.isChecked()

        new_settings = {
            "hotkey": hotkey_str,
            "startup_toggle": startup_enabled,
            "sound_toggle": self.sound_check.isChecked(),
            "slang_expansion": self.slang_check.isChecked(),
            "elongation_cleanup": self.elongation_check.isChecked(),
            "contextual_correction": True,
            "theme": theme,
            "nvidia_api_key": self.ai_key_edit.text().strip(),
            "ai_model": self.ai_model_combo.currentData() or "meta/llama-3.3-70b-instruct",
            "use_ai_in_tray": self.ai_tray_check.isChecked()
        }

        settings_manager.save_settings(new_settings)
        self.settings = new_settings
        self.apply_theme(theme)

        # Windows Başlangıcında Otomatik Başlatma Registry Güncellemesi
        if sys.platform == "win32":
            set_autostart(startup_enabled)

        # Tepsi ikonundaki kısayolu güncelle
        if self.tray_icon and hasattr(self.tray_icon, "update_hotkey"):
            self.tray_icon.update_hotkey(hotkey_str)

        QMessageBox.information(self, "Başarılı", "Ayarlar başarıyla kaydedildi.")

    def closeEvent(self, event):
        """Pencere kapatıldığında arka planda tepside kalması için gizle."""
        if self.tray_icon and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            self.notification_manager.show_notification(
                "Türkçe Otomatik Düzeltici",
                "Uygulama arka planda sistem tepsisinde çalışmaya devam ediyor."
            )
        else:
            event.accept()


def main():
    def qt_excepthook(exc_type, exc_value, exc_tb):
        import traceback
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"Arayüz Hatası:\n{tb}", file=sys.stderr)

    sys.excepthook = qt_excepthook

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()