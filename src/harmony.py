"""
Türkçe Büyük ve Küçük Ünlü Uyumu (Vowel Harmony) ve Ek Türetici.
- Soru ekleri (-mi, -mı, -mu, -mü)
- İyelik ve Tamlayan ekleri (-in, -ın, -un, -ün / 'in, 'ın vb.)
"""

FRONT_UNROUNDED = {'e', 'i'}     # -> mi, in
BACK_UNROUNDED = {'a', 'ı'}      # -> mı, ın
BACK_ROUNDED = {'o', 'u'}        # -> mu, un
FRONT_ROUNDED = {'ö', 'ü'}       # -> mü, ün

ALL_VOWELS = set("aeıioöuü")

def get_last_vowel(word: str) -> str:
    """Kelimenin son ünlüsünü döner."""
    for ch in reversed(word.lower()):
        if ch in ALL_VOWELS:
            return ch
    return 'e'

def get_genitive_suffix(word: str) -> str:
    """Kelimenin son ünlüsüne göre tamlayan ekini döner ('in, 'ın, 'un, 'ün)."""
    last_v = get_last_vowel(word)
    # Eğer kelime ünlü ile bitiyorsa kaynaştırma harfi 'n' gelir ('nin, 'nın vb.)
    ends_with_vowel = word[-1].lower() in ALL_VOWELS if word else False
    
    if last_v in FRONT_UNROUNDED:
        return "'nin" if ends_with_vowel else "'in"
    elif last_v in BACK_UNROUNDED:
        return "'nın" if ends_with_vowel else "'ın"
    elif last_v in BACK_ROUNDED:
        return "'nun" if ends_with_vowel else "'un"
    elif last_v in FRONT_ROUNDED:
        return "'nün" if ends_with_vowel else "'ün"
    return "'in"

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
