"""
Damerau-Levenshtein tabanlı ve Türkçe karakter destekli Yazım Düzeltici (Speller).
63.000+ kelimelik sözlük üzerinden hızlı filtreleme ve düzeltme.
"""

from typing import List, Tuple, Set
from src.dictionary import is_valid_word, get_word_prob, ALL_TURKISH_WORDS

TURKISH_ALPHABET = "abcçdefgğhıijklmnoöprsştuüvyz"

def edits1(word: str) -> set:
    """Tek karakterlik düzenleme mesafesindeki tüm varyasyonlar."""
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in TURKISH_ALPHABET]
    inserts = [L + c + R for L, R in splits for c in TURKISH_ALPHABET]
    return set(deletes + transposes + replaces + inserts)

def edits2(word: str) -> set:
    """İki karakterlik düzenleme mesafesi."""
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if len(e2) >= 2)

def correct_word(word: str, max_distance: int = 2) -> str:
    """
    Tek bir kelimeyi 63.000+ Türkçe kelime arasından en yüksek frekanslı haline düzeltir.
    """
    word_clean = word.lower()
    
    # 1. Kelime zaten geçerliyse doğrudan dön
    if is_valid_word(word_clean):
        return word_clean

    # Çok kısa kelimelerde (<=3 harf) kelime yozlaşmasını önle
    if len(word_clean) <= 3:
        candidates1 = [w for w in edits1(word_clean) if is_valid_word(w) and len(w) == len(word_clean)]
        if candidates1:
            return max(candidates1, key=get_word_prob)
        return word_clean

    # 2. 1-adım mesafedeki bilinen kelimeler
    candidates1 = [w for w in edits1(word_clean) if is_valid_word(w)]
    if candidates1:
        return max(candidates1, key=get_word_prob)

    if max_distance >= 2:
        # 3. 2-adım mesafedeki bilinen kelimeler
        candidates2 = [
            w for w in edits2(word_clean) 
            if is_valid_word(w) and abs(len(w) - len(word_clean)) <= 1
        ]
        if candidates2:
            return max(candidates2, key=get_word_prob)

    return word_clean
