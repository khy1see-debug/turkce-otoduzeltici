"""
1.170.000+ Kelimelik Devasa Türkçe Sözlük ve Frekans Tablosu (0-Token, Offline).
Zemberek çekimleri, TDK resmi sözlüğü ve günlük konuşma dili ağırlıkları birleştirildi.
"""

import os
import math
import gzip
from functools import lru_cache
from typing import Set
from wordfreq import word_frequency

from src.loanwords import COMMON_ENGLISH_TERMS

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "turkish_words.txt.gz")

# Tek harfli, iki harfli anlamsız kısaltmalar veya segmenter'ı bozan yabancı karakterler
BLOCKED_SHORT_CHUNKS = {
    "gd", "gt", "şl", "®", "ti", "2a", "│", "♦", "aj", "md", "sr", "fb", "tı", "mt", "lü", "ov", "ic", "tu", "tj",
    "h1", "g3", "g4", "dü", "zi", "do", "iğ", "to", "wp", "r2", "hz",
    "sn", "dk", "km", "kg", "tl", "cm", "mm", "vs", "vb",
    "ticarici", "disarici", "dışarıcı",
    "b", "c", "ç", "d", "e", "f", "g", "ğ", "h", "ı", "i", "j", "k", "l", "m", "n", "p", "r", "s", "ş", "t", "u", "ü", "v", "y", "z"
}

ALL_TURKISH_WORDS: Set[str] = set()

if os.path.exists(DATA_PATH):
    try:
        with gzip.open(DATA_PATH, "rt", encoding="utf-8") as f:
            ALL_TURKISH_WORDS = {line.rstrip("\n") for line in f if line.strip()} - BLOCKED_SHORT_CHUNKS
    except Exception as e:
        print(f"Uyarı: Devasa sözlük yüklenirken hata oluştu: {e}")

# İngilizce teknoloji/oyun terimleri ve temel Türkçe kısa kelimeler
ALL_TURKISH_WORDS.update(COMMON_ENGLISH_TERMS)

# Kişisel Sözlük / Discord kelimeleri yükleme
CONFIG_DIR = os.environ.get(
    "XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config")
)
PERSONAL_DICT_PATH = os.path.join(CONFIG_DIR, "turkce-otoduzeltici", "kisisel_sozluk.txt")
REPOSITORY_PERSONAL_DICT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "kisisel_sozluk.txt"
)
if not os.path.exists(PERSONAL_DICT_PATH):
    PERSONAL_DICT_PATH = REPOSITORY_PERSONAL_DICT_PATH
PERSONAL_WORDS: Set[str] = set()
if os.path.exists(PERSONAL_DICT_PATH):
    try:
        with open(PERSONAL_DICT_PATH, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w and not w.startswith("#"):
                    PERSONAL_WORDS.add(w)
                    ALL_TURKISH_WORDS.add(w)
    except Exception as e:
        print(f"Kişisel sözlük okuma hatası: {e}")

ALL_TURKISH_WORDS.add("o")
ALL_TURKISH_WORDS.add("su")
ALL_TURKISH_WORDS.add("ev")
ALL_TURKISH_WORDS.add("at")
ALL_TURKISH_WORDS.add("ay")
ALL_TURKISH_WORDS.add("el")
ALL_TURKISH_WORDS.add("it")
ALL_TURKISH_WORDS.add("ot")

# Günlük konuşma dili, argo ve sıkça kullanılan kritik kelimeler için yüksek öncelik
HIGH_PRIORITY_COLLOQUIAL = {
    "naber": 0.015, "kanka": 0.020, "selam": 0.018, "merhaba": 0.020, "nasılsın": 0.015,
    "gidiyor": 0.025, "geliyor": 0.025, "gidiyorsun": 0.020, "geliyorsun": 0.020,
    "nasıl": 0.030, "neden": 0.020, "niye": 0.015, "iyiyim": 0.015, "güzel": 0.020,
    "discord": 0.020, "premium": 0.020, "spotify": 0.018, "instagram": 0.020,
    "youtube": 0.020, "steam": 0.018, "online": 0.018, "link": 0.020, "chat": 0.018
}

# Kritik dilbilgisi bağlaç ve soru ekleri taban puanları
CRITICAL_GRAMMAR_WORDS = {
    "de": 0.030, "da": 0.030,
    "mi": 0.025, "mı": 0.025, "mu": 0.015, "mü": 0.015,
    "sen": 0.020, "ben": 0.020, "biz": 0.015, "siz": 0.015, "o": 0.025,
    "ve": 0.040, "ne": 0.025, "bu": 0.035, "şu": 0.020
}

def is_valid_word(word: str) -> bool:
    """Kelimenin Türkçe sözlükte olup olmadığını O(1) hızla kontrol eder."""
    w = word.lower()
    if w in BLOCKED_SHORT_CHUNKS:
        return False
    return w in ALL_TURKISH_WORDS or w in CRITICAL_GRAMMAR_WORDS or w in HIGH_PRIORITY_COLLOQUIAL

@lru_cache(maxsize=100000)
def get_word_prob(word: str) -> float:
    """Kelimenin log-olasılığını döner."""
    w = word.lower()
    if w in BLOCKED_SHORT_CHUNKS:
        return -50.0

    if w in PERSONAL_WORDS:
        return math.log(0.040) + (len(w) * 0.4)

    if w in HIGH_PRIORITY_COLLOQUIAL:
        return math.log(HIGH_PRIORITY_COLLOQUIAL[w]) + (len(w) * 0.4)
    if w in CRITICAL_GRAMMAR_WORDS:
        return math.log(CRITICAL_GRAMMAR_WORDS[w]) + (len(w) * 0.4)

    freq = word_frequency(w, "tr")
    if freq > 0:
        return math.log(freq) + (len(w) * 0.4)
    
    if w in ALL_TURKISH_WORDS:
        return -12.0 + (len(w) * 0.4)
    
    return -25.0 - (2.0 * len(word))
