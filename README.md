# 🇹🇷 Çevrimdışı Türkçe Otomatik Düzeltici (0-Token)

Bitişik yazılan (örn: `sendemigeliyorusn`), imla, harf ve bağlaç hataları barındıran Türkçe metinleri **çevrimdışı (offline)** ve **sıfır (0) token maliyetiyle** otomatik düzelten, modern stüdyo arayüzüne ve sistem tepsisi (system tray) kısayoluna sahip akıllı doğal dil işleme platformu.

---

## ⚡ Özellikler

- **0 Token Maliyeti & Gizlilik:** Herhangi bir bulut servisi veya LLM API'si çağırmaz, tamamen yerel CPU üzerinde, verileriniz dışarı çıkmadan anında çalışır.
- **✨ Gelişmiş Düzeltme & Çevirme Stüdyosu (GUI):** Çift panelli modern masaüstü arayüzü (Giriş / Düzeltilmiş Çıktı, canlı diff vurgulama, örnek metinler, harf sayacı ve tek tıkla kopyalama).
- **⌨️ Global Kısayol Tuşu & Sistem Tepsisi (Tray):** Herhangi bir programda (Discord, WhatsApp, Word, Tarayıcı vb.) bir metni fareyle seçip **`Alt+Q`** tuşuna bastığınızda seçili metni anında panoda düzeltip yerine yapıştırır.
- **↩️ Geri Alma & Öz-Öğrenme (Self-Learning):** Düzeltilen metin sonrasında `Ctrl+Z` basıldığında bunu ret olarak kaydeder; kabul edilen kelimeleri ise SQLite veritabanında öğrenerek kişisel sözlüğe katar.
- **🔤 De-asciifier & Asciifier:** 
  - İngilizce klavye harflerini (`c, g, i, o, s, u`) Türkçeleştirir (`ç, ğ, ı, ö, ş, ü`).
  - Türkçe harfleri standart ASCII'ye dönüştürme (Asciifier) modu.
- **📚 TDK Resmi İmla & Sık Yapılan Hatalar Kılavuzu:**
  - `herkez` $\rightarrow$ `herkes`, `yalnış` $\rightarrow$ `yanlış`, `orjinal` $\rightarrow$ `orijinal`, `süpriz` $\rightarrow$ `sürpriz`, `labaratuvar` $\rightarrow$ `laboratuvar`, `tabiki` $\rightarrow$ `tabii ki`, `iyiki` $\rightarrow$ `iyi ki`
- **🧩 Bitişik Kelime Ayrımı (Word Segmentation):** `sendemigeliyorusn` $\rightarrow$ `Sen de mi geliyorsun?`
- **🔗 Dilbilgisi, Bağlaç ve Soru Ekleri:**
  - Bağlaç olan *-de / -da* ayrımı (`sen de`, `o da`, `Ali de`, `biz de`)
  - Bitişik yazılan soru eklerini ayırma ve ünlü uyumu (`geliyormusun` $\rightarrow$ `geliyor musun?`, `bakarmısınız` $\rightarrow$ `bakar mısınız?`)
  - Bağlaç olan *-ki* ayrımı (`demek ki`, `öyle ki`, `iyi ki`)
- **🧹 Harf Uzatmalarını Temizleme (Elongation Reduction):** `geliyoruuuum` $\rightarrow$ `geliyorum`, `çooooook` $\rightarrow$ `çok`, `lütfeeeen` $\rightarrow$ `lütfen`
- **💬 Chat Argosu ve Kısaltmaları:** `slm` $\rightarrow$ `selam`, `nbr` $\rightarrow$ `naber`, `knk` $\rightarrow$ `kanka`, `tşk` $\rightarrow$ `teşekkürler`

---

## 🚀 Hızlı Başlangıç

### 1. Kurulum

```bash
# uv ile bağımlılıkları yükleyin
uv sync

# Veya pip ile kurun
pip install .
```

### 2. Kullanım Modları

#### 🖥️ 1. Görsel Düzeltme Stüdyosu (Modern GUI):
```bash
python -m src.cli --gui
# veya
turkce-duzelt-gui
```

#### 🛡️ 2. Sistem Tepsisi & Arka Plan Kısayolu (Alt+Q):
```bash
python -m src.cli --tray
# veya
turkce-duzelt-tray
```
> Arka planda sessizce çalışır. Herhangi bir uygulamada metni seçip `Alt+Q` tuşuna basın, anında düzeltilsin! Beğenmezseniz 2 saniye içinde `Ctrl+Z` yaparak geri alabilirsiniz.

#### 💻 3. Komut Satırından Hızlı Kullanım:
```bash
# Tek seferlik düzeltme
python -m src.cli "sendemigeliyorusn"
# Çıktı: Sen de mi geliyorsun?

# Canlı terminal interaktif modu
python -m src.cli -i

# Sadece de-asciifier (ASCII -> Türkçe)
python -m src.cli --deasciify "ogrencileringozlerindensevincokunuyordu"

# Sadece asciifier (Türkçe -> ASCII)
python -m src.cli --asciify "Öğrenciler şampiyon oldu"
```

#### 🐍 4. Python Kütüphanesi Olarak Kullanım:
```python
from src.grammar import fix_sentence
from src.deasciifier import deasciify_text, asciify_text

# Tam akıllı düzeltme
print(fix_sentence("sendemigeliyorusn"))
# Çıktı: "Sen de mi geliyorsun?"

print(fix_sentence("herkez birşey biliyo ama yanlız kaldım"))
# Çıktı: "Herkes bir şey biliyor, ama yalnız kaldım."

# De-asciifier
print(deasciify_text("ogrenci goz sevinc"))
# Çıktı: "öğrenci göz sevinç"

# Asciifier
print(asciify_text("Öğrenciler Türkçe konuşuyor"))
# Çıktı: "Ogrenciler Turkce konusuyor"
```

---

## 📖 Kişisel Sözlük ve Öz-Öğrenme

Kişisel sözlüğünüze özel terimler (oyun adları, yazılım kütüphaneleri, kişi adları) ekleyebilir veya sistemin kendi öğrendiklerini yönetebilirsiniz:

```bash
turkce-duzelt --add-word Valorant
turkce-duzelt --remove-word Valorant
turkce-duzelt --list-words
```

---

## 🧪 Testler

Test paketini çalıştırmak için:

```bash
uv run --with pytest pytest
uv run --with ruff ruff check src tests
```

---

## 📜 Lisans

MIT License — Açık kaynaklı ve ücretsiz.
