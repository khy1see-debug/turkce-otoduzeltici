"""
Damerau-Levenshtein tabanlı ve Türkçe karakter destekli Yazım Düzeltici (Speller).
Harf yer değişimi, harf/hece tekrarı temizliği ve deasciifier ile ultra hızlı çalışır.
"""

import re
from functools import lru_cache
from src.dictionary import is_valid_word, get_word_prob
from src.deasciifier import deasciify_word
from src.turkish_case import turkish_lower

TURKISH_ALPHABET = "abcçdefgğhıijklmnoöprsştuüvyz"

def edits1(word: str) -> set:
    """Tek karakterlik düzenleme mesafesindeki tüm varyasyonlar."""
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in TURKISH_ALPHABET]
    inserts = [L + c + R for L, R in splits for c in TURKISH_ALPHABET]
    return set(deletes + transposes + replaces + inserts)

@lru_cache(maxsize=50000)
def correct_word(word: str, max_distance: int = 1) -> str:
    """
    Tek bir kelimeyi 1.17M Türkçe kelime arasından en yüksek frekanslı haline düzeltir.
    Hızlı ve optimize: Harf yer değişimi, hece tekrarı ve 1-adım mesafeyi anında çözer.
    """
    word_clean = turkish_lower(word)
    if len(word_clean) > 24:
        return word_clean
    
    # 1. Kelime zaten geçerliyse doğrudan dön
    deasc = deasciify_word(word_clean)
    if is_valid_word(deasc):
        return deasc
    if is_valid_word(word_clean):
        return word_clean

    # 1.A: Tekrarlayan hece temizliği (örn: cikalalim -> cikalim -> çıkalım)
    syllable_dedup = re.sub(r'([a-zçğıöşü]{2,3})\1+', r'\1', word_clean)
    if syllable_dedup != word_clean:
        d_cand = deasciify_word(syllable_dedup)
        if is_valid_word(d_cand):
            return d_cand
        if is_valid_word(syllable_dedup):
            return syllable_dedup

    # 1.B: Tüm 1-adım düzenleme adayları (O(1) sözlük kontrolü + hızlı deasciify)
    cands1 = edits1(word_clean)
    valid_cands1 = {c for c in cands1 if is_valid_word(c)}

    splits = [(word_clean[:i], word_clean[i:]) for i in range(len(word_clean) + 1)]
    fast_edits = (
        [L + R[1:] for L, R in splits if R]
        + [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    )
    for c in fast_edits:
        d = deasciify_word(c, max_indices=5)
        if is_valid_word(d):
            valid_cands1.add(d)

    if not valid_cands1:
        vowel_inserts = [L + v + R for L, R in splits for v in "aeıioöuü"]
        for c in vowel_inserts:
            d = deasciify_word(c, max_indices=5)
            if is_valid_word(d):
                valid_cands1.add(d)

    if valid_cands1:
        return max(valid_cands1, key=get_word_prob)

    # 1.E: Uzun kelimelerde 2-mesafe aramayı gereksiz CPU yükü olmaması için sadece son çare olarak sınırla
    if max_distance >= 2 and len(word_clean) <= 8:
        # 2 harf mesafesi
        for e1 in edits1(word_clean):
            for e2 in edits1(e1):
                if is_valid_word(e2):
                    return e2

    return word_clean
