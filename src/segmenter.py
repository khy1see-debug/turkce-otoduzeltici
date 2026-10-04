"""
Bitişik yazılmış Türkçe metinleri ayırma modülü (Word Segmentation / Viterbi).
63.000+ kelimelik sözlük tabanlı.
"""

from typing import List, Tuple
from src.dictionary import is_valid_word, get_word_prob
from src.speller import correct_word

MAX_WORD_LEN = 20

def segment_text(text: str) -> List[str]:
    """
    Dinamik programlama (Viterbi) ile bitişik yazılmış metni kelimelere ayırır ve düzeltir.
    """
    clean_text = text.lower().strip()
    n = len(clean_text)
    if n == 0:
        return []

    # Faz 1: Doğrudan sözlükte var olan kelimelerle Viterbi dene
    best_cost = [float('-inf')] * (n + 1)
    best_cost[0] = 0.0
    best_match = [None] * (n + 1)

    for i in range(n):
        if best_cost[i] == float('-inf'):
            continue
        max_j = min(n + 1, i + MAX_WORD_LEN + 1)
        for j in range(i + 1, max_j):
            chunk = clean_text[i:j]
            if is_valid_word(chunk):
                cost = best_cost[i] + get_word_prob(chunk)
                if cost > best_cost[j]:
                    best_cost[j] = cost
                    best_match[j] = (i, chunk)

    # Eğer doğrudan sözlükle sona ulaşıldıysa
    if best_cost[n] > float('-inf'):
        words = []
        idx = n
        while idx > 0:
            prev_idx, word = best_match[idx]
            words.insert(0, word)
            idx = prev_idx
        return words

    # Faz 2: Sona ulaşılamadıysa (harf hatası var), aday parçaları düzeltmeyle dene
    best_cost = [float('-inf')] * (n + 1)
    best_cost[0] = 0.0
    best_match = [None] * (n + 1)

    for i in range(n):
        if best_cost[i] == float('-inf'):
            continue
        max_j = min(n + 1, i + MAX_WORD_LEN + 1)
        for j in range(i + 1, max_j):
            chunk = clean_text[i:j]
            if is_valid_word(chunk):
                # Sözlükte olan tam parçalara öncelik
                cost = best_cost[i] + get_word_prob(chunk) + 5.0
                if cost > best_cost[j]:
                    best_cost[j] = cost
                    best_match[j] = (i, chunk)
            else:
                if len(chunk) >= 4 or j == n:
                    corrected = correct_word(chunk)
                    if is_valid_word(corrected) and corrected != chunk:
                        cost = best_cost[i] + get_word_prob(corrected)
                        if cost > best_cost[j]:
                            best_cost[j] = cost
                            best_match[j] = (i, corrected)

    words = []
    idx = n
    while idx > 0:
        match = best_match[idx]
        if match is None:
            words.insert(0, clean_text[:idx])
            break
        prev_idx, word = match
        words.insert(0, word)
        idx = prev_idx

    return [correct_word(w) for w in words]
