"""
Kelime geçerlilik ve imla düzeltmesi zinciri:
de-asciifier → doğruluk kontrolü → speller (1-adım mesafe) → segmenter.
"""

from __future__ import annotations

from typing import List, Tuple

from src.deasciifier import deasciify_word
from src.dictionary import is_valid_word
from src.segmenter import segment_text
from src.speller import correct_word


def correct_word_chain(clean_token: str, token_core: str) -> Tuple[List[str], List[dict]]:
    """Tek bir temiz tokeni düzeltip parçalar.

    Dönüş: (segmented_words, changes).
    """
    changes: List[dict] = []
    deasc = deasciify_word(clean_token)
    if is_valid_word(deasc) or is_valid_word(clean_token):
        final_w = deasc if is_valid_word(deasc) else clean_token
        if final_w != clean_token:
            changes.append({
                "original": token_core,
                "corrected": final_w,
                "rule": "İmla & De-asciifier: Doğru Türkçe harfler tamamlandı.",
                "type": "spelling",
            })
        return [final_w], changes

    cand = correct_word(deasc)
    if is_valid_word(cand) and cand != clean_token:
        changes.append({
            "original": token_core,
            "corrected": cand,
            "rule": "İmla Düzeltme: Harf hatası ve Türkçe karakterler düzeltildi.",
            "type": "spelling",
        })
        return [cand], changes

    if len(clean_token) > 4:
        segmented = segment_text(clean_token)
        if len(segmented) > 1:
            changes.append({
                "original": token_core,
                "corrected": " ".join(segmented),
                "rule": "Bitişik Kelime Ayrımı: Bitişik yazılmış sözcükler sözlük ve frekans tablosuyla ayrıldı.",
                "type": "segmentation",
            })
        elif segmented and segmented[0] != clean_token:
            changes.append({
                "original": token_core,
                "corrected": segmented[0],
                "rule": "İmla Düzeltme: Harf hatası ve Türkçe karakterler düzeltildi.",
                "type": "spelling",
            })
        return segmented, changes

    return [cand], changes
