"""
Düzeltme boru hattının ana organtörü.

``analyze_sentence``, ``grammar.py``'deki eski tek-blok mantığını aşağıdaki
sıralı aşamalara bölerek yeniden oluşturur:

1. Kod bloğu maskesi
2. TDK ön-normalizasyonu (apply_tdk_rules)
3. Tokenizasyon (whitespace/noktalama/önek-sonek korumalı)
4. Başlık/koruma geçişleri
5. Harf uzatması normalizasyonu
6. Slang / TDK yaygın hata açılması
7. Bitişik '-ya' ayrımı
8. Bitişik soru eki ayrımı
9. De-asciifier + imla + segmenter zinciri
10. '-de / -da / -ki' bağlaç ayrımı
11. Soru eki ünlü uyumu
12. Devrik cümle kontrolü (şu an düzenlemez)
13. Cümle başı büyük harfi
14. Hitap virgülü
15. Soru tespiti
16. Bağlaktan önce virgül
17. Nihai render + cümle-sonu noktalaması
18. Kod bloğu geri yükleme

Public giriş noktaları: ``analyze_sentence(text)`` ve ``fix_sentence(text)``.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List

from src.dictionary import is_valid_word, refresh_personal_dictionary
from src.speller import correct_word
from src.tdk_rules import apply_tdk_rules
from src.turkish_case import turkish_lower

from .conjunctions import split_conjunctions
from .masking import extract_code_blocks, restore_code_blocks, PROTECTED_TOKEN, PROTECTED_EMOTICONS
from .normalization import (
    normalize_elongation_token,
    expand_slang_token,
    split_attached_ya,
    split_attached_question,
    ATTACHED_QUESTION_REGEX,
    ATTACHED_YA_REGEX,
)
from .rendering import (
    apply_vowel_harmony,
    apply_word_order,
    apply_sentence_capitalization,
    apply_greeting_comma,
    detect_question,
    apply_clause_commas,
    render_sentence,
    apply_sentence_ending,
    capitalize_after_sentence_end,
)
from .spelling import correct_word_chain
from .tokenize import split_leading_trailing, tokenize_with_spaces, split_prefix_suffix, clean_token

PROTECTED_ABBREVIATIONS = {
    "km", "cm", "mm", "m", "kg", "mg", "g", "l", "ml", "lt",
    "sn", "dk", "tl", "kb", "mb", "gb", "tb", "hz", "khz", "mhz", "ghz",
    "vs", "vb",
}


def analyze_sentence(raw_text: str) -> Dict[str, Any]:
    """
    Metni analiz eder, düzeltir ve her bir düzeltmenin nedenini (TDK kuralı, bağlaç,
    deasciifier vb.) detaylı bir liste halinde döner.

    Çıktı şeması:
        {
            "original": str,
            "corrected": str,
            "changes": [{"original", "corrected", "rule", "type"}, ...],
            "stats": {"word_count", "char_count", "changes_count", "time_ms"}
        }
    """
    t0 = time.time()
    if not raw_text.strip():
        return {
            "original": raw_text,
            "corrected": "",
            "changes": [],
            "stats": {"word_count": 0, "char_count": 0, "changes_count": 0, "time_ms": 0.0},
        }

    # 1. Kod bloklarını maskele
    masked_text, code_blocks = extract_code_blocks(raw_text)

    # 2. TDK Kuralları (Özel İsimler, Kısaltmalar, Sayı/Saat İmlası)
    tdk_normalized = apply_tdk_rules(masked_text)
    if tdk_normalized != masked_text:
        masked_text = tdk_normalized

    if refresh_personal_dictionary():
        correct_word.cache_clear()

    original_text = masked_text
    leading, content, trailing = split_leading_trailing(masked_text)

    tokens, spaces_before = tokenize_with_spaces(content)
    processed_words: List[str] = []
    punctuation_after: List[str] = []
    punctuation_before: List[str] = []
    whitespace_before: List[str] = []
    changes: List[dict] = []

    for token_index, token in enumerate(tokens):
        # Kod bloğu yer tutucusu ise doğrudan koru
        if "__CODE_BLOCK_" in token:
            processed_words.append(token)
            punctuation_after.append("")
            punctuation_before.append("")
            whitespace_before.append(spaces_before[token_index])
            continue

        clean_tok = clean_token(token)
        if not clean_tok:
            if token in PROTECTED_EMOTICONS or re.search(
                r"[^\w\s.,!?;:…()\[\]{}\"'“”‘’«»]", token
            ):
                processed_words.append(token)
                punctuation_after.append("")
                punctuation_before.append("")
                whitespace_before.append(spaces_before[token_index])
                continue
            if processed_words and re.fullmatch(r"[.,!?;:…]+[)\]}\"\'”’»]*", token):
                punctuation_after[-1] += token
            continue

        prefix, token_core, suffix = split_prefix_suffix(token)
        has_internal_symbol = bool(
            re.search(r"[^\wçğıöşüÇĞİÖŞÜ'’]", token_core)
        )

        # Cümle ortasında büyük harfle başlayan kelimenin özel isim olup olmadığını denetle
        is_mid_sentence_proper = False
        if token_index > 0 and token[:1].isupper() and not token.isupper():
            prev_ended_sentence = bool(
                punctuation_after and any(p in punctuation_after[-1] for p in ".!?…")
            ) or ("\n" in spaces_before[token_index])
            if not prev_ended_sentence:
                if (
                    not expand_slang_token(clean_tok, token_core)[0]
                    and not ATTACHED_QUESTION_REGEX.match(clean_tok)
                    and not ATTACHED_YA_REGEX.match(clean_tok)
                    and (is_valid_word(clean_tok) or len(clean_tok) <= 4)
                ):
                    is_mid_sentence_proper = True

        preserve_token = (
            token.isupper() and len(clean_tok) > 1
        ) or is_mid_sentence_proper or "'" in token_core or "’" in token_core or bool(
            token_core and PROTECTED_TOKEN.fullmatch(token_core)
        ) or has_internal_symbol or bool(
            token_core and turkish_lower(token_core) in PROTECTED_ABBREVIATIONS
        ) or any(char.isdigit() for char in token_core)
        if preserve_token:
            processed_words.append(token)
            punctuation_after.append("")
            punctuation_before.append("")
            whitespace_before.append(spaces_before[token_index])
            continue

        # 5. Harf uzatması normalizasyonu
        normalized_elong, elong_change = normalize_elongation_token(clean_tok)
        if elong_change:
            changes.append(elong_change)
            clean_tok = normalized_elong

        # 6. Chat Kısaltması ve TDK Yaygın Hatalar
        slang_text, slang_change, expanded_words = expand_slang_token(clean_tok, token_core)
        if slang_change:
            changes.append(slang_change)
            processed_words.extend(expanded_words)
            punctuation_before.extend([""] * len(expanded_words))
            punctuation_after.extend([""] * (len(expanded_words) - 1) + [suffix])
            whitespace_before.extend(
                [spaces_before[token_index]] + [" "] * (len(expanded_words) - 1)
            )
            if expanded_words and prefix:
                punctuation_before[len(processed_words) - len(expanded_words)] = prefix
            continue

        # 7. Bitişik '-ya' ayrımı
        ya_words, ya_change, ya_before, ya_after, ya_ws = split_attached_ya(
            clean_tok, token_core, prefix, spaces_before[token_index]
        )
        if ya_change:
            changes.append(ya_change)
            processed_words.extend(ya_words)
            punctuation_before.extend(ya_before)
            punctuation_after.extend(ya_after)
            whitespace_before.extend(ya_ws)
            continue

        # 8. Bitişik soru eki ayrımı
        q_words, q_change, q_before, q_after, q_ws = split_attached_question(
            clean_tok, token_core, prefix, spaces_before[token_index]
        )
        if q_change:
            changes.append(q_change)
            processed_words.extend(q_words)
            punctuation_before.extend(q_before)
            punctuation_after.extend(q_after)
            whitespace_before.extend(q_ws)
            continue

        # 9. Kelime geçerlilik ve imla düzeltmesi
        segmented, spell_changes = correct_word_chain(clean_tok, token_core)
        changes.extend(spell_changes)
        processed_words.extend(segmented)
        punctuation_before.extend([""] * len(segmented))
        punctuation_after.extend([""] * (len(segmented) - 1) + [suffix])
        whitespace_before.extend(
            [spaces_before[token_index]] + [" "] * (len(segmented) - 1)
        )
        if segmented and prefix:
            punctuation_before[len(processed_words) - len(segmented)] = prefix

    if not processed_words:
        return {
            "original": raw_text,
            "corrected": restore_code_blocks(original_text, code_blocks),
            "changes": [],
            "stats": {"word_count": 0, "char_count": 0, "changes_count": 0, "time_ms": 0.0},
        }

    # 10. -de / -da bağlacı ayrımı
    (
        processed_words,
        punctuation_before,
        punctuation_after,
        whitespace_before,
        conj_changes,
    ) = split_conjunctions(
        processed_words, punctuation_before, punctuation_after, whitespace_before
    )
    changes.extend(conj_changes)

    # 11. Soru eki ünlü uyumu düzeltmesi
    processed_words, changes = apply_vowel_harmony(processed_words, changes)

    # 12. Devrik Cümle Düzeltmesi (şu anki uygulama sıralamayı korur)
    (
        processed_words,
        punctuation_before,
        punctuation_after,
        whitespace_before,
    ) = apply_word_order(
        processed_words, punctuation_before, punctuation_after, whitespace_before
    )

    # 13. Cümle başı büyük harf
    processed_words = apply_sentence_capitalization(
        processed_words, punctuation_before, PROTECTED_TOKEN
    )

    # 14. Hitap / Selamlaşma sonrası virgül kuralı
    punctuation_after = apply_greeting_comma(processed_words, punctuation_after)

    # 15. Soru tespiti
    is_question, punctuation_after = detect_question(
        processed_words, punctuation_after
    )

    # 16. Bağlaçlardan önce virgül (CLAUSE_CONNECTORS)
    reconstructed: List[str] = []
    reconstructed = apply_clause_commas(processed_words, reconstructed)

    # 17. Render + cümle-sonu noktalaması
    (
        sentence,
        sentence_body,
        closing,
        emoticon_tail,
        standalone_identifier,
    ) = render_sentence(
        reconstructed,
        punctuation_before,
        punctuation_after,
        whitespace_before,
        processed_words,
        PROTECTED_TOKEN,
        PROTECTED_EMOTICONS,
    )
    sentence_body = apply_sentence_ending(
        sentence_body,
        closing,
        emoticon_tail,
        is_question,
        standalone_identifier,
    )
    sentence = sentence_body + closing + emoticon_tail

    # 18. Cümle sonu noktalamasından sonra gelen cümlelerin ilk harfini büyüt
    sentence = capitalize_after_sentence_end(sentence)

    final_result = leading + sentence + trailing
    final_result = restore_code_blocks(final_result, code_blocks)

    elapsed_ms = (time.time() - t0) * 1000

    return {
        "original": raw_text,
        "corrected": final_result,
        "changes": changes,
        "stats": {
            "word_count": len(final_result.split()),
            "char_count": len(final_result),
            "changes_count": len(changes),
            "time_ms": round(elapsed_ms, 2),
        },
    }


def fix_sentence(raw_text: str) -> str:
    """Kullanıcının girdiği ham metni düzeltip nihai metni döner."""
    analysis = analyze_sentence(raw_text)
    return analysis["corrected"]
