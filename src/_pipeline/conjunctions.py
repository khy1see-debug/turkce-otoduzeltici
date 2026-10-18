"""
Bağlaç olan *-de / -da* ve *-ki* ayrımı (örn: bende -> ben de, iyiki -> iyi ki).
"""

from __future__ import annotations

from typing import List, Tuple

from src.turkish_case import turkish_lower

CONJUNCTION_MAP = {
    "bende": ("ben", "de"),
    "sende": ("sen", "de"),
    "bizde": ("biz", "de"),
    "sizde": ("siz", "de"),
    "ondada": ("onda", "da"),
    "buda": ("bu", "da"),
    "şuda": ("şu", "da"),
    "oda": ("o", "da"),
    "onada": ("ona", "da"),
    "banada": ("bana", "da"),
    "sanada": ("sana", "da"),
    "bizede": ("bize", "de"),
    "sizede": ("size", "de"),
    "onlarada": ("onlara", "da"),
    "onlarda": ("onlar", "da"),
    "burayada": ("buraya", "da"),
    "şurayada": ("şuraya", "da"),
    "orayada": ("oraya", "da"),
    "bendede": ("bende", "de"),
    "sendede": ("sende", "de"),
    "bizdede": ("bizde", "de"),
    "sizdede": ("sizde", "de"),
    "evdede": ("evde", "de"),
    "iştede": ("işte", "de"),
    "öyleki": ("öyle", "ki"),
    "demekki": ("demek", "ki"),
    "iyiki": ("iyi", "ki"),
    "kaldıki": ("kaldı", "ki"),
    "şöyleki": ("şöyle", "ki"),
    "yeterki": ("yeter", "ki"),
    "bilmemki": ("bilmem", "ki"),
    "anladımki": ("anladım", "ki"),
    "gördümki": ("gördüm", "ki"),
}


def split_conjunctions(
    processed_words: List[str],
    punctuation_before: List[str],
    punctuation_after: List[str],
    whitespace_before: List[str],
) -> Tuple[List[str], List[str], List[str], List[str], List[dict]]:
    """Bağlaçlı tekil kelimeleri iki kelimeye ayırır.

    Dönüş: (final_tokens, final_before, final_after, final_whitespace, changes).
    """
    final_tokens: List[str] = []
    final_before: List[str] = []
    final_after: List[str] = []
    final_whitespace: List[str] = []
    changes: List[dict] = []

    for i, w in enumerate(processed_words):
        w_lower = turkish_lower(w)
        if w_lower in CONJUNCTION_MAP:
            p1, p2 = CONJUNCTION_MAP[w_lower]
            changes.append({
                "original": w,
                "corrected": f"{p1} {p2}",
                "rule": "TDK Bağlaç Kuralı: Bağlaç olan 'de/da' ve 'ki' ayrı yazılır.",
                "type": "conjunction",
            })
            final_tokens.extend([p1, p2])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        else:
            final_tokens.append(w)
            final_before.append(punctuation_before[i])
            final_after.append(punctuation_after[i])
            final_whitespace.append(whitespace_before[i])

    return final_tokens, final_before, final_after, final_whitespace, changes
