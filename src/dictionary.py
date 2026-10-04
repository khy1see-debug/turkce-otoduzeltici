"""
Kapsamlı Türkçe Sözlük ve Frekans Tablosu (0-token, offline).
63.000+ gerçek Türkçe kelime haznesi ve kısaltma/harf koruma kuralları.
"""

import math
from typing import Optional
from wordfreq import word_frequency, iter_wordlist

# Tek harfli veya anlamsız kısaltmaların kelime parçalama sırasında suistimal edilmesini önleme
BLOCKED_SHORT_CHUNKS = {
    "sn", "dk", "km", "kg", "tl", "cm", "mm", "vs", "vb",
    "b", "c", "ç", "d", "e", "f", "g", "ğ", "h", "ı", "i", "j", "k", "l", "m", "n", "p", "r", "s", "ş", "t", "u", "ü", "v", "y", "z"
}

# 63.000+ kelimelik tam Türkçe sözlük seti
ALL_TURKISH_WORDS = set(iter_wordlist("tr")) - BLOCKED_SHORT_CHUNKS
ALL_TURKISH_WORDS.add("o")  # 'o' zamir olarak geçerlidir

# Soru ekleri ve bağlaçlar gibi kritik kısa kelimelerin frekans taban puanları
CRITICAL_GRAMMAR_WORDS = {
    "de": 0.025, "da": 0.026,
    "mi": 0.020, "mı": 0.021, "mu": 0.012, "mü": 0.011,
    "sen": 0.015, "ben": 0.016, "biz": 0.012, "siz": 0.011, "o": 0.020,
    "ve": 0.035, "ne": 0.020, "bu": 0.030, "şu": 0.015
}

def is_valid_word(word: str) -> bool:
    """Kelimenin Türkçe sözlükte olup olmadığını O(1) hızla kontrol eder."""
    w = word.lower()
    return w in ALL_TURKISH_WORDS or w in CRITICAL_GRAMMAR_WORDS

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
        # Kelime uzunluğuna göre küçük bir log-bonus (daha uzun kelimeleri tercih eder)
        return math.log(freq) + (len(w) * 0.4)
    
    # Bilinmeyen kelimeler için uzunluğa göre ceza
    return -25.0 - (2.0 * len(word))
