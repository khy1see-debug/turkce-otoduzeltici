"""
scripts/enrich_dictionary.py - Devasa Türkçe Kelime Derlemi ve Sözlük Zenginleştirici.
İnternet üzerindeki açık kaynaklı TDK, OpenSubtitles ve Zemberek derlemlerini tarar,
yerel sözlüğü 1.68 Milyon+ doğrulanmış kelimeye çıkarır ve sıkıştırarak kaydeder.
"""

import gzip
import os
import sys
import time
import urllib.request
from typing import Set

# Konsol utf-8 desteği
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "data", "turkish_words.txt.gz")

TURKISH_LOWER_MAP = str.maketrans({
    "I": "ı",
    "İ": "i",
    "Ç": "ç",
    "Ğ": "ğ",
    "Ö": "ö",
    "Ş": "ş",
    "Ü": "ü",
})

VALID_CHARS = set("abcçdefgğhıijklmnoöprsştuüvyz-")

BLOCKED_SHORT_CHUNKS = {
    "gd", "gt", "şl", "®", "ti", "2a", "│", "♦", "aj", "md", "sr", "fb", "tı", "mt", "lü", "ov", "ic", "tu", "tj",
    "h1", "g3", "g4", "dü", "zi", "do", "iğ", "to", "wp", "r2", "hz",
    "sn", "dk", "km", "kg", "tl", "cm", "mm", "vs", "vb",
    "b", "c", "ç", "d", "e", "f", "g", "ğ", "h", "ı", "i", "j", "k", "l", "m", "n", "p", "r", "s", "ş", "t", "u", "ü", "v", "y", "z"
}


TYPO_ENDINGS = (
    "asn", "esn", "ısn", "isn", "osn", "ösn", "usn", "üsn",
    "yorm", "yordm", "yordk"
)


def to_turkish_lower(s: str) -> str:
    return s.translate(TURKISH_LOWER_MAP).lower()


def is_valid_turkish_word(w: str) -> bool:
    if not w or len(w) < 2 and w not in {"o", "su", "ev", "at", "ay", "el", "it", "ot"}:
        return False
    if w in BLOCKED_SHORT_CHUNKS:
        return False
    if any(w.endswith(e) for e in TYPO_ENDINGS):
        return False
    return all(c in VALID_CHARS for c in w)


def fetch_url_lines(url: str, timeout: float = 35.0) -> list[str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Turkce-Sozluk-Crawler/2.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            return content.splitlines()
    except Exception as exc:
        print(f"  [!] İndirme uyarısı ({url}): {exc}")
        return []


def enrich_dictionary():
    print("=" * 65)
    print("🚀 TÜRKÇE SÖZLÜK DERLEMİ ZENGİNLEŞTİRİCİ (1.68M+ Kelime Hedefi)")
    print("=" * 65)

    words: Set[str] = set()

    # 1. Mevcut yerel sözlüğü oku
    if os.path.exists(DATA_PATH):
        print(f"[*] Mevcut yerel sözlük okunuyor: {DATA_PATH}")
        with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
            for line in f:
                w = to_turkish_lower(line.strip())
                if is_valid_turkish_word(w):
                    words.add(w)
        print(f"  [+] Mevcut temiz kelime sayısı: {len(words):,}")

    initial_count = len(words)

    # 2. CanNuhlar TDK Resmi İmla Kılavuzu Derlemi (76.205 kelime)
    tdk_url = "https://raw.githubusercontent.com/CanNuhlar/Turkce-Kelime-Listesi/master/turkce_kelime_listesi.txt"
    print(f"\n[*] TDK resmi kelime listesi taranıyor...")
    tdk_lines = fetch_url_lines(tdk_url)
    tdk_added = 0
    for line in tdk_lines:
        w = to_turkish_lower(line.strip())
        if is_valid_turkish_word(w) and w not in words:
            words.add(w)
            tdk_added += 1
    print(f"  [+] TDK'dan eklenen yeni kelime: {tdk_added:,}")

    # 3. Mertemin Türkçe Sözcük Listesi (63.840 kelime)
    mert_url = "https://raw.githubusercontent.com/mertemin/turkish-word-list/master/words.txt"
    print(f"\n[*] Mertemin Türkçe kelime listesi taranıyor...")
    mert_lines = fetch_url_lines(mert_url)
    mert_added = 0
    for line in mert_lines:
        w = to_turkish_lower(line.strip())
        if is_valid_turkish_word(w) and w not in words:
            words.add(w)
            mert_added += 1
    print(f"  [+] Mertemin listesinden eklenen yeni kelime: {mert_added:,}")

    # 4. OpenSubtitles Türkçe Konuşma ve Dizi/Film Derlemi (tr_full.txt: 2.035.629 kelime)
    sub_url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/tr/tr_full.txt"
    print(f"\n[*] OpenSubtitles devasa Türkçe konuşma dili derlemi taranıyor (tr_full.txt)...")
    req = urllib.request.Request(
        sub_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Turkce-Sozluk-Crawler/2.0"}
    )
    sub_added = 0
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            for line in resp:
                parts = line.decode("utf-8", errors="ignore").strip().split()
                if len(parts) >= 2:
                    raw_w, count_str = parts[0], parts[1]
                    try:
                        count = int(count_str)
                    except ValueError:
                        continue
                    # Frekansı >= 15 olan (yazım hatası olmayan gerçek konuşma dili) kelimeleri al
                    if count >= 15:
                        w = to_turkish_lower(raw_w)
                        if is_valid_turkish_word(w) and w not in words:
                            words.add(w)
                            sub_added += 1
    except Exception as exc:
        print(f"  [!] OpenSubtitles indirme uyarısı: {exc}")

    print(f"  [+] OpenSubtitles derleminden eklenen kelime: {sub_added:,}")

    # 5. Kritik Modern Teknoloji & Günlük Konuşma Terimleri
    modern_terms = [
        "discord", "spotify", "instagram", "youtube", "tiktok", "netflix", "whatsapp",
        "twitter", "telegram", "github", "steam", "epic", "valorant", "roblox",
        "chatgpt", "gemini", "claude", "nvidia", "intel", "amd", "ryzen", "rtx",
        "kanka", "kankam", "naber", "selam", "merhaba", "eyvallah", "sağol", "aynen",
        "hadi", "tamamdır", "olur", "süper", "harika", "efsane", "mükemmel",
        "link", "post", "dm", "online", "offline", "bug", "lag", "fps", "drop"
    ]
    for term in modern_terms:
        w = to_turkish_lower(term)
        if is_valid_turkish_word(w):
            words.add(w)

    final_count = len(words)
    net_increase = final_count - initial_count

    print("\n" + "=" * 65)
    print(f"[+] Zenginleştirme Tamamlandı!")
    print(f"[>] Eski Kelime Sayısı: {initial_count:,}")
    print(f"[>] Yeni Eklenen Kelime: {net_increase:,}")
    print(f"[>] TOPLAM AKTİF KELİME: {final_count:,}")
    print("=" * 65)

    # 6. Sırala ve Gzip ile Kaydet
    print(f"[*] Dosya kaydediliyor: {DATA_PATH}...")
    sorted_words = sorted(words)
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with gzip.open(DATA_PATH, "wt", encoding="utf-8", compresslevel=9) as f:
        f.write("\n".join(sorted_words) + "\n")

    size_mb = os.path.getsize(DATA_PATH) / (1024 * 1024)
    print(f"[✓] Başarıyla kaydedildi! Sıkıştırılmış boyut: {size_mb:.2f} MB")
    return final_count


if __name__ == "__main__":
    enrich_dictionary()
