"""
Türkçe Harf Normalizasyonu ve De-asciifier Modülü.
Kullanıcı İngilizce klavye (c, g, i, o, s, u) yazsa bile
otomatik olarak doğru Türkçe harflere (ç, ğ, ı, ö, ş, ü) dönüştürür.
"""

from src.dictionary import is_valid_word, get_word_prob
from src.turkish_case import turkish_lower

# ASCII karakterlerin Türkçe olası alternatifleri
ASCII_TO_TURKISH = {
    'c': ['c', 'ç'],
    'g': ['g', 'ğ'],
    'i': ['i', 'ı', 'î'],
    'o': ['o', 'ö'],
    's': ['s', 'ş'],
    'u': ['u', 'ü']
}

def deasciify_word(word: str) -> str:
    """
    ASCII karakterlerle yazılmış tek bir kelimeyi (örn: 'ogrencilerin' -> 'öğrencilerin', 'goz' -> 'göz')
    en yüksek olasılıklı Türkçe haline çevirir.
    """
    word_lower = turkish_lower(word)
    
    # 1. Kelime zaten Türkçe sözlükte tam olarak varsa ve özel durum değilse kontrol et
    # Ancak içinde c, g, o, s, u olup da Türkçe karakterlisi daha yüksek frekanslı olabilir
    # (Örn: 'goz' sözlükte yok ama 'göz' var, 'yas' var ama 'yaş' daha yaygın olabilir)
    # Kelimedeki her pozisyon için varyasyonları üret (maksimum 128 kombinasyon)
    indices = [idx for idx, ch in enumerate(word_lower) if ch in ASCII_TO_TURKISH]
    if not indices or len(indices) > 5:
        # Çok fazla varyasyon varsa direkt sözlük ve speller'a bırak
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
        return max(valid_candidates, key=get_word_prob)

    return word_lower
