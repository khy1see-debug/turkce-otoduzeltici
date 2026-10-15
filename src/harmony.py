"""
Türkçe Büyük ve Küçük Ünlü Uyumu (Vowel Harmony) ve Ek Türetici.
- Soru ekleri (-mi, -mı, -mu, -mü, -misin, -musun, -miyiz vb.)
- İyelik ve Tamlayan ekleri (-in, -ın, -un, -ün / 'in, 'ın vb.)
"""

from src.turkish_case import turkish_lower

FRONT_UNROUNDED = {'e', 'i'}     # -> mi, in
BACK_UNROUNDED = {'a', 'ı'}      # -> mı, ın
BACK_ROUNDED = {'o', 'u'}        # -> mu, un
FRONT_ROUNDED = {'ö', 'ü'}       # -> mü, ün

ALL_VOWELS = set("aeıioöuü")

# Soru eki kök ve şahıs kalıpları
QUESTION_PARTICLE_FORMS = {
    # Tekil / Çoğul Şahıs & Zaman varyasyonları
    "mi": ("mi", "mı", "mu", "mü"),
    "mı": ("mi", "mı", "mu", "mü"),
    "mu": ("mi", "mı", "mu", "mü"),
    "mü": ("mi", "mı", "mu", "mü"),
    "misin": ("misin", "mısın", "musun", "müsün"),
    "mısın": ("misin", "mısın", "musun", "müsün"),
    "musun": ("misin", "mısın", "musun", "müsün"),
    "müsün": ("misin", "mısın", "musun", "müsün"),
    "miyiz": ("miyiz", "mıyız", "muyuz", "müyüz"),
    "mıyız": ("miyiz", "mıyız", "muyuz", "müyüz"),
    "muyuz": ("miyiz", "mıyız", "muyuz", "müyüz"),
    "müyüz": ("miyiz", "mıyız", "muyuz", "müyüz"),
    "misiniz": ("misiniz", "mısınız", "musunuz", "müsünüz"),
    "mısınız": ("misiniz", "mısınız", "musunuz", "müsünüz"),
    "musunuz": ("misiniz", "mısınız", "musunuz", "müsünüz"),
    "müsünüz": ("misiniz", "mısınız", "musunuz", "müsünüz"),
    "miyim": ("miyim", "mıyım", "muyum", "müyüm"),
    "mıyım": ("miyim", "mıyım", "muyum", "müyüm"),
    "muyum": ("miyim", "mıyım", "muyum", "müyüm"),
    "müyüm": ("miyim", "mıyım", "muyum", "müyüm"),
    "miydi": ("miydi", "mıydı", "muydu", "müydü"),
    "mıydı": ("miydi", "mıydı", "muydu", "müydü"),
    "muydu": ("miydi", "mıydı", "muydu", "müydü"),
    "müydü": ("miydi", "mıydı", "muydu", "müydü"),
    "miymiş": ("miymiş", "mıymış", "muymuş", "müymüş"),
    "mıymış": ("miymiş", "mıymış", "muymuş", "müymüş"),
    "muymuş": ("miymiş", "mıymış", "muymuş", "müymüş"),
    "müymüş": ("miymiş", "mıymış", "muymuş", "müymüş"),
    "midir": ("midir", "mıdır", "mudur", "müdür"),
    "mıdır": ("midir", "mıdır", "mudur", "müdür"),
    "mudur": ("midir", "mıdır", "mudur", "müdür"),
    "müdür": ("midir", "mıdır", "mudur", "müdür"),
    "miydik": ("miydik", "mıydık", "muyduk", "müydük"),
    "mıydık": ("miydik", "mıydık", "muyduk", "müydük"),
    "muyduk": ("miydik", "mıydık", "muyduk", "müydük"),
    "müydük": ("miydik", "mıydık", "muyduk", "müydük"),
    "miydiniz": ("miydiniz", "mıydınız", "muydunuz", "müydünüz"),
    "mıydınız": ("miydiniz", "mıydınız", "muydunuz", "müydünüz"),
    "muydunuz": ("miydiniz", "mıydınız", "muydunuz", "müydünüz"),
    "müydünüz": ("miydiniz", "mıydınız", "muydunuz", "müydünüz"),
    "miler": ("miler", "mılar", "mular", "müler"),
    "mılar": ("miler", "mılar", "mular", "müler"),
}

def get_last_vowel(word: str) -> str:
    """Kelimenin son ünlüsünü döner."""
    for ch in reversed(turkish_lower(word)):
        if ch in ALL_VOWELS:
            return ch
    return 'e'

def get_genitive_suffix(word: str) -> str:
    """Kelimenin son ünlüsüne göre tamlayan ekini döner ('in, 'ın, 'un, 'ün)."""
    last_v = get_last_vowel(word)
    ends_with_vowel = turkish_lower(word[-1]) in ALL_VOWELS if word else False
    
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
    Soru ekini önceki kelimenin son seslisine göre büyük ve küçük ünlü uyumuyla düzeltir:
    değil -> değil mi
    yaptın -> yaptın mı
    oldu -> oldu mu
    gördün -> gördün mü
    geliyor -> geliyor musun
    bakar -> bakar mısınız
    """
    p = turkish_lower(particle)
    if p not in QUESTION_PARTICLE_FORMS:
        return particle

    forms = QUESTION_PARTICLE_FORMS[p]
    last_v = get_last_vowel(prev_word)

    if last_v in FRONT_UNROUNDED:
        return forms[0]  # -i
    elif last_v in BACK_UNROUNDED:
        return forms[1]  # -ı
    elif last_v in BACK_ROUNDED:
        return forms[2]  # -u
    elif last_v in FRONT_ROUNDED:
        return forms[3]  # -ü
    return forms[0]
