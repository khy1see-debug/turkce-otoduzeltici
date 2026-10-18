"""
Türkçe Harf Normalizasyonu, De-asciifier ve Asciifier Modülü.
Kullanıcı İngilizce klavye (c, g, i, o, s, u) yazsa bile
otomatik olarak doğru Türkçe harflere (ç, ğ, ı, ö, ş, ü) dönüştürür.
Ayrıca tersine çevirme (Asciifier) ve tam metin desteği sunar.
"""

from functools import lru_cache
from src.dictionary import is_valid_word, get_word_prob
from src.turkish_case import turkish_lower, turkish_upper

# ASCII karakterlerin Türkçe olası alternatifleri
ASCII_TO_TURKISH = {
    'c': ['c', 'ç'],
    'g': ['g', 'ğ'],
    'i': ['i', 'ı'],
    'o': ['o', 'ö'],
    's': ['s', 'ş'],
    'u': ['u', 'ü']
}

TURKISH_TO_ASCII = {
    'ç': 'c', 'Ç': 'C',
    'ğ': 'g', 'Ğ': 'G',
    'ı': 'i', 'I': 'I',
    'İ': 'I', 'i': 'i',
    'ö': 'o', 'Ö': 'O',
    'ş': 's', 'Ş': 'S',
    'ü': 'u', 'Ü': 'U',
    'â': 'a', 'Â': 'A',
    'î': 'i', 'Î': 'I',
    'û': 'u', 'Û': 'U'
}


def asciify_text(text: str) -> str:
    """
    Türkçe karakterleri standart ASCII karakterlerine dönüştürür.
    Örnek: 'Öğrenciler şampiyon oldu.' -> 'Ogrenciler sampiyon oldu.'
    """
    return "".join(TURKISH_TO_ASCII.get(ch, ch) for ch in text)


@lru_cache(maxsize=100000)
def deasciify_word(word: str, max_indices: int = 6) -> str:
    """
    ASCII karakterlerle yazılmış tek bir kelimeyi (örn: 'ogrencilerin' -> 'öğrencilerin', 'goz' -> 'göz')
    en yüksek olasılıklı Türkçe haline çevirir.
    Ultra hızlı O(1) varyasyon arama kullanır.
    """
    if not word:
        return word

    word_lower = turkish_lower(word)
    from src.loanwords import COMMON_ENGLISH_TERMS
    if word_lower in COMMON_ENGLISH_TERMS:
        return word

    # Değiştirilebilir karakter indeksleri
    indices = [idx for idx, ch in enumerate(word_lower) if ch in ASCII_TO_TURKISH]
    if not indices or len(indices) > max_indices:
        # Çok fazla şüpheli harf genelde bitişik bölünmemiş tümcedir
        return word_lower

    current_pool = [list(word_lower)]
    for idx in indices:
        orig_char = word_lower[idx]
        replacements = ASCII_TO_TURKISH[orig_char]
        new_pool = []
        for p in current_pool:
            for r in replacements:
                variant = list(p)
                variant[idx] = r
                new_pool.append(variant)
        current_pool = new_pool

    valid_candidates = []
    for p in current_pool:
        w_candidate = "".join(p)
        if is_valid_word(w_candidate):
            valid_candidates.append(w_candidate)

    if valid_candidates:
        best_cand = max(valid_candidates, key=get_word_prob)
        return _preserve_case_pattern(word, best_cand)

    return word_lower


def deasciify_text(text: str) -> str:
    """
    Tüm bir metindeki kelimeleri deasciify eder, noktalama ve boşlukları korur.
    """
    import re
    def replace_token(match: re.Match) -> str:
        word = match.group(0)
        return deasciify_word(word)

    return re.sub(r'[a-zA-ZçğıöşüÇĞİÖŞÜ]+', replace_token, text)


def _preserve_case_pattern(original: str, converted: str) -> str:
    """Orijinal kelimenin büyük/küçük harf desenini korur."""
    if original.isupper():
        return turkish_upper(converted)
    if original and original[0].isupper():
        from src.turkish_case import turkish_capitalize
        return turkish_capitalize(converted)
    return converted
