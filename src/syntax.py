"""
Türkçe Devrik Cümle İnceleyici ve Düzeltici (Word Order Normalizer).
Açık ve devrik kuralsız fiil yerleşimlerini cümlenin sonuna taşır.
Soru cümlelerini, ünlemleri ve şiirsel/özgün anlatımları bozmaz.
"""

import re
from typing import List
from src.turkish_case import turkish_lower

# Türkçe fiil zaman ve şahıs ekleri regexi
TENSE_PERSON_PATTERNS = [
    # Şimdiki zaman: -iyor, -ıyor, -üyor, -uyor + şahıs
    r'^[a-zçğıöşü]{2,}(iyor|ıyor|uyor|üyor)(um|sun|uz|sunuz|lar)?$',
    # Görülen geçmiş zaman: -di, -dı, -du, -dü, -ti, -tı, -tu, -tü + şahıs
    r'^[a-zçğıöşü]{2,}(di|dı|du|dü|ti|tı|tu|tü)(m|n|k|niz|ler|lar)?$',
    # Gelecek zaman: -ecek, -acak + şahıs
    r'^[a-zçğıöşü]{2,}(eceğ|acağ)(im|ım|iz|ız)$',
    r'^[a-zçğıöşü]{2,}(ecek|acak)(sin|sınız|siniz|ler|lar)?$',
    # Geniş zaman: -ir, -ır, -ur, -ür, -er, -ar
    r'^[a-zçğıöşü]{2,}(er|ar|ir|ır|ur|ür)(im|sin|iz|siniz|ler|lar)?$',
    # Duyulan geçmiş: -miş, -mış, -muş, -müş
    r'^[a-zçğıöşü]{2,}(miş|mış|muş|müş)(im|sin|iz|siniz|ler|lar)?$'
]

COMBINED_VERB_REGEX = re.compile('|'.join(TENSE_PERSON_PATTERNS))

NON_VERBS = {
    'dün', 'gün', 'bin', 'on', 'son', 'ten', 'sen', 'ben', 'siz', 'biz',
    'demir', 'fikir', 'kedi', 'bilgisayar', 'şehir', 'iyi', 'güzel', 'var', 'yok',
    'bugün', 'yarın', 'şimdi', 'sonra', 'önce', 'akşam', 'sabah', 'gece',
    'evet', 'hayır', 'tamam', 'peki', 'aynen', 'falan', 'falansal', 'neden', 'niçin',
    'nasıl', 'nerede', 'kim', 'hangi', 'kaç'
}

def is_finite_verb(word: str) -> bool:
    """Kelimenin çekimli bir fiil olup olmadığını tespit eder."""
    w = turkish_lower(word).strip(",.?!:;\"'")
    if w in NON_VERBS or len(w) <= 2:
        return False
    return bool(COMBINED_VERB_REGEX.match(w))

def fix_word_order(tokens: List[str]) -> List[str]:
    """
    Eğer yüklem/fiil cümlenin en başında kalmışsa ve cümle açık bir düz devrik cümle ise
    fiili cümlenin sonuna taşır.
    Soru cümlelerinde, emir kiplerinde veya 2 kelimelik ifadelerde dokunmaz.
    """
    if len(tokens) <= 2:
        return tokens

    # Soru cümlelerinde devriklik düzeltilmez (örn: "Gördün mü onu dün?")
    lower_tokens = [turkish_lower(t.strip(",.?!:;\"'")) for t in tokens]
    if any(t in {"mi", "mı", "mu", "mü", "misin", "mısın", "musun", "müsün", "neden", "niye", "nasıl", "kim", "nerede"} for t in lower_tokens):
        return tokens

    # Eğer son kelime zaten fiil ise dokunma
    last_w = lower_tokens[-1]
    if is_finite_verb(last_w):
        return tokens

    # Cümlenin ilk kelimesi çekimli bir fiil mi? (Örn: "Gördüm seni dün sokakta" -> "seni dün sokakta gördüm")
    if is_finite_verb(lower_tokens[0]):
        verb = tokens.pop(0)
        # Fiil cümlenin sonuna taşınırken küçük harfe indirgenmeli (cümle başı büyüteç kuralı yeni ilk kelimeye uygulanacak)
        tokens.append(turkish_lower(verb))
        return tokens

    return tokens
