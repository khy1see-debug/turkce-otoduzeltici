"""
Türkçe Devrik Cümle Düzeltici (Word Order Normalizer).
Örnek:
  "gördüm seni dün sokakta" -> "seni dün sokakta gördüm"
  "geldim eve biraz önce" -> "eve biraz önce geldim"
"""

import re
from typing import List

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
    'evet', 'hayır', 'tamam', 'peki', 'aynen', 'falan', 'falansal'
}

def is_finite_verb(word: str) -> bool:
    """Kelimenin çekimli bir fiil olup olmadığını tespit eder."""
    w = word.lower().strip(",.?!")
    if w in NON_VERBS or len(w) <= 2:
        return False
    return bool(COMBINED_VERB_REGEX.match(w))

def fix_word_order(tokens: List[str]) -> List[str]:
    """
    Eğer yüklem/fiil cümlenin en başında veya ortasında kalmışsa
    ve cümle açık bir devrik cümle ise fiili cümlenin en sonuna taşır.
    """
    if len(tokens) <= 2:
        return tokens

    # Eğer son kelime zaten fiil veya soru eki ise dokunma
    last_w = tokens[-1].lower()
    if last_w in {"mi", "mı", "mu", "mü"} or is_finite_verb(last_w):
        return tokens

    # Cümlenin ilk kelimesi fiil mi? (Örn: "Gördüm seni dün sokakta")
    if is_finite_verb(tokens[0]):
        verb = tokens.pop(0)
        tokens.append(verb)
        return tokens

    return tokens
