"""
Damerau-Levenshtein tabanlı ve Türkçe karakter destekli Yazım Düzeltici (Speller).
Harf yer değişimi (transposition) ve aynı harfin çift yazılması (klavye kayması) önceliklidir.
"""

from typing import List, Tuple, Set
from src.dictionary import is_valid_word, get_word_prob

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
    Tek bir kelimeyi 1.17M Türkçe kelime arasından en yüksek frekanslı haline düzeltir.
    Harf yer değişimine (transposition: kanak -> kanka) ve aynı harf tekrarına özel öncelik verir.
    """
    word_clean = word.lower()
    
    # 1. Kelime zaten geçerliyse doğrudan dön
    if is_valid_word(word_clean):
        return word_clean

    # Öncelikli 1.A: Harf yer değişimi (Transposition) kontrolü: kanak -> kanka
    splits = [(word_clean[:i], word_clean[i:]) for i in range(len(word_clean) + 1)]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    trans_valid = [w for w in transposes if is_valid_word(w)]
    if trans_valid:
        return max(trans_valid, key=get_word_prob)

    # Öncelikli 1.B: Tekrar eden/fazla harf silme: gdidiyor -> gidiyor
    deletes = [L + R[1:] for L, R in splits if R]
    del_valid = [w for w in deletes if is_valid_word(w)]
    if del_valid:
        return max(del_valid, key=get_word_prob)

    # 1.C: Diğer 1-mesafe adayları
    candidates1 = [w for w in edits1(word_clean) if is_valid_word(w)]
    if candidates1:
        return max(candidates1, key=get_word_prob)

    if max_distance >= 2:
        # 2. İki adım mesafedeki adaylar
        candidates2 = [
            w for w in edits2(word_clean) 
            if is_valid_word(w) and abs(len(w) - len(word_clean)) <= 1
        ]
        if candidates2:
            return max(candidates2, key=get_word_prob)

    return word_clean
