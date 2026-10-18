"""
Harf uzatması temizliği, chat kısaltması/TDK yaygın hata açılması ve bitişik
ek (-ya, -mi) ayrımı.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from src.deasciifier import deasciify_word
from src.slang import (
    TDK_COMMON_MISSPELLINGS,
    expand_slang,
    normalize_elongation,
)
from src.dictionary import is_valid_word

ATTACHED_QUESTION_REGEX = re.compile(
    r"^([a-zçğıöşü]{3,})(m[ıiuü](?:sin|sınız|siniz|sun|sunuz|sün|sünüz|yız|yiz|yuz|yüz|yım|yim|yum|yüm|di|dı|du|dü|miş|mış|muş|müş)?)$",
    re.IGNORECASE,
)

ATTACHED_YA_REGEX = re.compile(
    r"^([a-zçğıöşü]{2,}(?:yor|yorsun|yorum|yoruz|yorsunuz|dım|dim|dum|düm|tım|tim|tum|tüm|dın|din|dun|dün|tın|tin|tun|tün|dı|di|du|dü|tı|ti|tu|tü|mış|miş|muş|müş|acak|ecek))(ya)$",
    re.IGNORECASE,
)

QUESTION_FALSE_POSITIVES = {
    "kamu", "cami", "semi", "namu", "samu", "timu", "armi", "humi", "rumi"
}


def normalize_elongation_token(clean_token: str) -> Tuple[str, Optional[dict]]:
    """Aşırı tekrar eden harfleri standart haline indirir.

    Dönüş: (normalized_token, change_dict_or_None).
    """
    normalized = normalize_elongation(clean_token)
    if normalized != clean_token:
        return normalized, {
            "original": clean_token,
            "corrected": normalized,
            "rule": "Harf Uzatması: Aşırı tekrar eden harfler standart Türkçeye indirgendi.",
            "type": "elongation",
        }
    return clean_token, None


def expand_slang_token(clean_token: str, token_core: str) -> Tuple[Optional[str], Optional[dict], Optional[List[str]]]:
    """Chat kısaltması veya TDK yaygın hatasını açar.

    Dönüş: (expanded_text, change_dict_or_None, expanded_words_or_None).
    """
    slang_expanded = expand_slang(clean_token)
    if not slang_expanded:
        return None, None, None
    rule_text = (
        "TDK Yazım Kuralı: Yaygın yazım hatası düzeltildi."
        if clean_token in TDK_COMMON_MISSPELLINGS
        else "Chat Kısaltması: Günlük konuşma kısaltması standart Türkçeye açıldı."
    )
    change = {
        "original": token_core,
        "corrected": slang_expanded,
        "rule": rule_text,
        "type": "slang_or_tdk",
    }
    expanded_words = slang_expanded.split()
    return slang_expanded, change, expanded_words


def split_attached_ya(clean_token: str, token_core: str, prefix: str, spaces_before_token: str) -> Tuple[Optional[List[str]], Optional[dict], Optional[List[str]], Optional[List[str]], Optional[List[str]]]:
    """Bitişik yazılmış '-ya' ünlem/pekiştirme ekini ayırır (yazıyorya -> yazıyor ya).

    Dönüş: (words, change_dict, punctuation_before, punctuation_after, whitespace_before) veya (None, ...).
    """
    attached_ya = ATTACHED_YA_REGEX.match(clean_token)
    if not attached_ya:
        return None, None, None, None, None
    stem_ya = attached_ya.group(1)
    stem_ya_fixed = expand_slang(stem_ya) or correct_word_via_deasc(stem_ya)
    if not is_valid_word(stem_ya_fixed):
        return None, None, None, None, None
    ya_words = [stem_ya_fixed, "ya"]
    change = {
        "original": token_core,
        "corrected": f"{stem_ya_fixed} ya",
        "rule": "TDK Bağlaç/Ünlem Kuralı: Fiilden sonra gelen 'ya' pekiştirme sözcüğü ayrı yazılır.",
        "type": "conjunction",
    }
    punctuation_before = [""] * len(ya_words)
    punctuation_after = ["", ""]
    whitespace_before = [spaces_before_token, " "]
    if prefix:
        punctuation_before[len(ya_words) - 2] = prefix
    return ya_words, change, punctuation_before, punctuation_after, whitespace_before


def split_attached_question(clean_token: str, token_core: str, prefix: str, spaces_before_token: str) -> Tuple[Optional[List[str]], Optional[dict], Optional[List[str]], Optional[List[str]], Optional[List[str]]]:
    """Bitişik yazılmış soru ekini ayırır (geliyormusun -> geliyor musun).

    Dönüş: (words, change_dict, punctuation_before, punctuation_after, whitespace_before) veya (None, ...).
    """
    attached_match = ATTACHED_QUESTION_REGEX.match(clean_token)
    if not attached_match or clean_token in QUESTION_FALSE_POSITIVES:
        return None, None, None, None, None
    stem, q_particle = attached_match.group(1), attached_match.group(2)
    stem_fixed = correct_word_via_deasc(stem)
    q_fixed = fix_question_particle(stem_fixed, q_particle)
    q_words = [stem_fixed, q_fixed]
    change = {
        "original": token_core,
        "corrected": f"{stem_fixed} {q_fixed}",
        "rule": "TDK Soru Eki Kuralı: Soru eki olan '-mi' daima kendinden önceki sözcükten ayrı yazılır.",
        "type": "question_suffix",
    }
    punctuation_before = [""] * len(q_words)
    punctuation_after = ["", ""]
    whitespace_before = [spaces_before_token, " "]
    if prefix:
        punctuation_before[len(q_words) - 2] = prefix
    return q_words, change, punctuation_before, punctuation_after, whitespace_before


def correct_word_via_deasc(word: str) -> str:
    """De-asciify + imla düzeltme zinciri (speller.modülüne proxy)."""
    from src.speller import correct_word
    return correct_word(deasciify_word(word))


def fix_question_particle(prev_word: str, particle: str) -> str:
    """Soru ekini önceki kelimenin son seslisine göre büyük/küçük ünlü uyumuyla düzeltir."""
    from src.harmony import fix_question_particle as _fix
    return _fix(prev_word, particle)
