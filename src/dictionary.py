"""
1.170.000+ Kelimelik Devasa Türkçe Sözlük ve Frekans Tablosu (0-Token, Offline).
Zemberek çekimleri, TDK resmi sözlüğü ve wordfreq frekansları birleştirildi.
"""

import os
import math
import pickle
from functools import lru_cache
from typing import Set
from wordfreq import word_frequency

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "turkish_words_huge.pkl")

# Tek harfli veya anlamsız kısaltmaların kelime parçalama sırasında suistimal edilmesini önleme
BLOCKED_SHORT_CHUNKS = {
    "sn", "dk", "km", "kg", "tl", "cm", "mm", "vs", "vb",
    "b", "c", "ç", "d", "e", "f", "g", "ğ", "h", "ı", "i", "j", "k", "l", "m", "n", "p", "r", "s", "ş", "t", "u", "ü", "v", "y", "z"
}

# 1.170.000+ kelimelik devasa sözlük seti
ALL_TURKISH_WORDS: Set[str] = set()

if os.path.exists(DATA_PATH):
    try:
        with open(DATA_PATH, "rb") as f:
            ALL_TURKISH_WORDS = pickle.load(f) - BLOCKED_SHORT_CHUNKS
    except Exception as e:
        print(f"Uyarı: Devasa sözlük yüklenirken hata oluştu: {e}")

ALL_TURKISH_WORDS.add("o")  # 'o' zamir olarak geçerlidir

# Kritik dilbilgisi bağlaç ve soru ekleri taban puanları
CRITICAL_GRAMMAR_WORDS = {
    "de": 0.025, "da": 0.026,
    "mi": 0.020, "mı": 0.021, "mu": 0.012, "mü": 0.011,
    "sen": 0.015, "ben": 0.016, "biz": 0.012, "siz": 0.011, "o": 0.020,
    "ve": 0.035, "ne": 0.020, "bu": 0.030, "şu": 0.015
}

def is_valid_word(word: str) -> bool:
    """Kelimenin 1.17M Türkçe kelime havuzunda olup olmadığını O(1) hızla kontrol eder."""
    w = word.lower()
    return w in ALL_TURKISH_WORDS or w in CRITICAL_GRAMMAR_WORDS

@lru_cache(maxsize=100000)
def get_word_prob(word: str) -> float:
    """
    Kelimenin log-olasılığını döner.
    Uzun kelimelere doğal öncelik vermek için uzunluk katsayısı eklenir (kelimeleri gereksiz bölmeyi önler).
    """
    w = word.lower()
    if w in CRITICAL_GRAMMAR_WORDS:
        freq = CRITICAL_GRAMMAR_WORDS[w]
    else:
        freq = word_frequency(w, "tr")
    
    if freq > 0:
        return math.log(freq) + (len(w) * 0.4)
    
    # Kelime sözlükte var ama wordfreq'te yoksa (çekimli kelime vs.)
    if w in ALL_TURKISH_WORDS:
        # Orta düzey frekans ver (-12.0)
        return -12.0 + (len(w) * 0.4)
    
    # Bilinmeyen kelimeler için uzunluğa göre ceza
    return -25.0 - (2.0 * len(word))
