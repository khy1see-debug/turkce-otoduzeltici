"""
Damerau-Levenshtein tabanlı ve Türkçe karakter destekli Yazım Düzeltici (Speller).
"""

from typing import List, Tuple, Set
from src.dictionary import BASE_TURKISH_WORDS, TOTAL_WORDS

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
    Tek bir kelimeyi en yüksek olasılıklı Türkçe haline düzeltir.
    Önemli: Çok kısa kelimeleri (<=3 harf) bambaşka kelimelere dönüştürmez!
    """
    word_clean = word.lower()
    
    # 1. Kelime zaten sözlükte varsa doğrudan dön
    if word_clean in BASE_TURKISH_WORDS:
        return word_clean

    # Çok kısa kelimelerde sadece 1 mesafeye izin ver (kelime yozlaşmasını önlemek için)
    if len(word_clean) <= 3:
        candidates1 = [w for w in edits1(word_clean) if w in BASE_TURKISH_WORDS and len(w) == len(word_clean)]
        if candidates1:
            return max(candidates1, key=lambda w: BASE_TURKISH_WORDS[w])
        return word_clean

    # 2. 1-adım mesafedeki bilinen kelimeler
    candidates1 = [w for w in edits1(word_clean) if w in BASE_TURKISH_WORDS]
    if candidates1:
        return max(candidates1, key=lambda w: BASE_TURKISH_WORDS[w])

    if max_distance >= 2:
        # 3. 2-adım mesafedeki bilinen kelimeler (uzunluk farkı en fazla 1 olmalı)
        candidates2 = [
            w for w in edits2(word_clean) 
            if w in BASE_TURKISH_WORDS and abs(len(w) - len(word_clean)) <= 1
        ]
        if candidates2:
            return max(candidates2, key=lambda w: BASE_TURKISH_WORDS[w])

    # Düzeltilemezse orijinali koru
    return word_clean
