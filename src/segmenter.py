"""
Bitişik yazılmış Türkçe metinleri ayırma modülü (Word Segmentation / Viterbi).
1.17M kelimelik sözlük tabanlı, Deasciifier ve Harf Düzeltme entegreli.
Kısa anlamsız parçalanmalar (kan + ak) yerine doğru kelimeleri (kanka) önceliklendirir.
"""

from typing import List, Tuple
from src.dictionary import is_valid_word, get_word_prob, CRITICAL_GRAMMAR_WORDS
from src.speller import correct_word
from src.deasciifier import deasciify_word

MAX_WORD_LEN = 22

def segment_text(text: str) -> List[str]:
    """
    Dinamik programlama (Viterbi) ile bitişik yazılmış metni kelimelere ayırır ve düzeltir.
    Kısa bağlaçlar ve soru ekleri (de, da, mi, mı) korunurken, anlamsız 2 harfli bölmeler cezalandırılır.
    """
    clean_text = text.lower().strip()
    n = len(clean_text)
    if n == 0:
        return []

    best_cost = [float('-inf')] * (n + 1)
    best_cost[0] = 0.0
    best_match = [None] * (n + 1)

    for i in range(n):
        if best_cost[i] == float('-inf'):
            continue
        max_j = min(n + 1, i + MAX_WORD_LEN + 1)
        for j in range(i + 1, max_j):
            chunk = clean_text[i:j]
            deasc = deasciify_word(chunk)
            
            # 1. Tam geçerli kelime
            target_word = deasc if is_valid_word(deasc) else (chunk if is_valid_word(chunk) else None)
            
            if target_word:
                # Eğer kelime de, da, mi, mı gibi kritik gramer kelimesi ise ekstra ceza verme
                if target_word in CRITICAL_GRAMMAR_WORDS or target_word in {"su", "ev", "at", "ay", "el", "it", "ot"}:
                    penalty = 0.0
                elif len(target_word) <= 2:
                    penalty = -5.0  # Anlamsız 2 harfli parçalama cezası
                else:
                    penalty = 0.0
                
                cost = best_cost[i] + get_word_prob(target_word) + penalty
                if cost > best_cost[j]:
                    best_cost[j] = cost
                    best_match[j] = (i, target_word)
            else:
                # 2. Harf hatası düzeltme (örn: kanak -> kanka, geliyorusn -> geliyorsun)
                if len(chunk) >= 4 or j == n:
                    corrected = correct_word(chunk)
                    if is_valid_word(corrected) and corrected != chunk:
                        # Düzeltme maliyeti
                        cost = best_cost[i] + get_word_prob(corrected) - 2.0
                        if cost > best_cost[j]:
                            best_cost[j] = cost
                            best_match[j] = (i, corrected)

    # Geriye doğru yolu çıkar
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

    return [deasciify_word(correct_word(w)) for w in words]
