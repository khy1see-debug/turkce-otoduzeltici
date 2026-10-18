"""
Whitespace, noktalama ve önek/sonek korumalı kelime-tokenizasyonu.

Orijinal metindeki boşluk miktarı, kelime başındaki parantez/tırnak önekleri ve
kelime sonundaki noktalama sonekleri ayrı tutulur; boru hattı boyunca
yeniden birleştirilebilir hale getirilir.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from src.turkish_case import turkish_lower


def split_leading_trailing(text: str) -> Tuple[str, str, str]:
    """Baştaki ve sondaki boşlukları ayırır; (leading, content, trailing) döner."""
    leading_length = len(text) - len(text.lstrip())
    trailing_length = len(text) - len(text.rstrip())
    leading = re.sub(r" {2,}", " ", text[:leading_length])
    trailing = re.sub(r" {2,}", " ", text[len(text) - trailing_length:]) if trailing_length else ""
    content_end = len(text) - trailing_length if trailing_length else len(text)
    content = text[leading_length:content_end]
    return leading, content, trailing


def tokenize_with_spaces(text: str) -> Tuple[List[str], List[str]]:
    """Metni boşluklarla ayrılmış tokenlara ve her tokenin önündeki boşluğa ayırır.

    Dönüş: (tokens, spaces_before). ``spaces_before[i]``, ``tokens[i]``'den önce
    gelen boşluktır (iki veya daha fazla boşluk tek boşluğa indirgenir).
    """
    token_matches = list(re.finditer(r"\S+", text))
    tokens = [match.group(0) for match in token_matches]
    spaces_before = [
        re.sub(r" {2,}", " ", text[token_matches[i - 1].end() if i else 0:match.start()])
        for i, match in enumerate(token_matches)
    ]
    return tokens, spaces_before


def split_prefix_suffix(token: str) -> Tuple[str, str, str]:
    """Tokeni (prefix, core, suffix) olarak böler.

    prefix: kelime başındaki parantez/köşeli ayraç/tırnak karakterleri.
    suffix: kelime sonundaki noktalama karakterleri (ve kapanış parantezleri).
    core: kalan ortadaki içerik.
    """
    prefix = re.match(r"^([([{\"'“«]*)", token).group(1)
    suffix_match = re.search(r"[.,!?;:…]+[)\]}\"\'”’»]*$", token)
    suffix = suffix_match.group(0) if suffix_match else ""
    core_end = len(token) - len(suffix) if suffix else len(token)
    core = token[len(prefix):core_end]
    return prefix, core, suffix


def clean_token(core: str) -> str:
    """Kernelleştirilmiş (sadece Türkçe harf içeren) küçük harfli token."""
    return turkish_lower(re.sub(r"[^\wçğıöşüÇĞİÖŞÜ]", "", core))
