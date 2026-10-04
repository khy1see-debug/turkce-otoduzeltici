"""
Türkçe Büyük ve Küçük Ünlü Uyumu (Vowel Harmony) ve Soru Eki Düzeltici.
-mi, -mı, -mu, -mü eklerini kendisinden önceki kelimenin son ünlüsüne göre tam uyumlu hale getirir.
"""

FRONT_UNROUNDED = {'e', 'i'}     # -> mi
BACK_UNROUNDED = {'a', 'ı'}      # -> mı
BACK_ROUNDED = {'o', 'u'}        # -> mu
FRONT_ROUNDED = {'ö', 'ü'}       # -> mü

ALL_VOWELS = set("aeıioöuü")

def get_last_vowel(word: str) -> str:
    """Kelimenin son ünlüsünü döner."""
    for ch in reversed(word.lower()):
        if ch in ALL_VOWELS:
            return ch
    return 'e'

def fix_question_particle(prev_word: str, particle: str) -> str:
    """
    Soru ekini önceki kelimenin son seslisine göre büyük ünlü uyumuyla düzeltir:
    değil -> değil mi
    yaptın -> yaptın mı
    oldu -> oldu mu
    gördün -> gördün mü
    """
    p = particle.lower()
    if p not in {"mi", "mı", "mu", "mü"}:
        return particle

    last_v = get_last_vowel(prev_word)

    if last_v in FRONT_UNROUNDED:
        return "mi"
    elif last_v in BACK_UNROUNDED:
        return "mı"
    elif last_v in BACK_ROUNDED:
        return "mu"
    elif last_v in FRONT_ROUNDED:
        return "mü"
    return "mi"
