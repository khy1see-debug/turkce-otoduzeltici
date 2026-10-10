# 🇹🇷 Çevrimdışı Türkçe Otomatik Düzeltici (0-Token)

Bitişik yazılan (örn: `sendemigeliyorusn`), imla ve harf hataları barındıran Türkçe metinleri **çevrimdışı (offline)** ve **sıfır (0) token maliyetiyle** otomatik düzelten Python tabanlı akıllı doğal dil işleme kütüphanesi ve CLI aracı.

---

## ⚡ Özellikler
- **0 Token Maliyeti:** Herhangi bir API (OpenAI, Gemini vb.) çağırmaz, tamamen yerel CPU üzerinde çalışır.
- **Bitişik Kelime Ayrımı (Word Segmentation):** `sendemigeliyorusn` $\rightarrow$ `Sen de mi geliyorsun?`
- **İmla ve Harf Hatası Düzeltme:** Damerau-Levenshtein tabanlı Türkçe harf mesafesi ve frekans sözlüğü.
- **Dilbilgisi ve Noktalama:** 
  - Bağlaç olan *-de / -da* ayrımı
  - Soru eki *-mi / -mı / -mu / -mü* ayrımı
  - Cümle başı büyük harf ve uygun noktalama (`.` veya `?`) ekleme.
- **İnteraktif CLI:** Terminalden anlık interaktif kullanım modu.

---

## 🚀 Hızlı Başlangıç

### 1. Kurulum
```bash
# uv ile kullanıcı hesabına komut olarak kurun
uv tool install .
```

Alternatif olarak sanal ortamda `python -m pip install .` kullanabilirsiniz.
Kişisel kelimelerinizi `~/.config/turkce-otoduzeltici/kisisel_sozluk.txt`
dosyasına her satıra bir kelime gelecek şekilde ekleyin. Bu dosya yerel kalır.

### 2. Kullanım

#### Komut Satırından Tek Seferlik Düzeltme:
```bash
python3 -m src.cli "sendemigeliyorusn"
# Çıktı: Sen de mi geliyorsun?
```

#### Canlı / İnteraktif Terminal Modu:
```bash
python3 -m src.cli -i
```

#### Python Kodu İçinde Kullanım:
```python
from src.grammar import fix_sentence

print(fix_sentence("sendemigeliyorusn"))
# Çıktı: "Sen de mi geliyorsun?"

print(fix_sentence("bugunhavacokguzel"))
# Çıktı: "Bugün hava çok güzel."
```

Kurulumdan sonra Python'dan içe aktarım için aynı `src.grammar` modülünü kullanın.

---

## 🧪 Testler
```bash
PYTHONPATH=. pytest tests/
```
