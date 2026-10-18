"""
Nihai dönüşüm katmanı: ünlü uyumu, cümle-büyük-harfi, hitap virgülü,
soru tespiti, bağlaktan önce virgül ve kelimelerin tekrarıyla metin biçimi.
"""

from __future__ import annotations

import re
from typing import List, Set, Tuple

from src.harmony import fix_question_particle
from src.syntax import fix_word_order, is_finite_verb
from src.turkish_case import turkish_lower, turkish_upper, turkish_capitalize

QUESTION_PARTICLES = {
    "mi", "mı", "mu", "mü",
    "misin", "mısın", "musun", "müsün",
    "miyiz", "mıyız", "muyuz", "müyüz",
    "misiniz", "mısınız", "musunuz", "müsünüz",
    "miyim", "mıyım", "muyum", "müyüm",
    "miydi", "mıydı", "muydu", "müydü",
    "miymiş", "mıymış", "muymuş", "müymüş",
    "midir", "mıdır", "mudur", "müdür",
}

QUESTION_WORDS = {
    "nasıl", "nasılsın", "nasılsınız", "nasıldı", "nasılmış",
    "nerede", "nereden", "nereye", "neredesin", "neredesiniz", "neredeydin", "neredeydiniz", "neresi", "neresinde",
    "kim", "kimi", "kime", "kimin", "kiminle", "kimsin", "kimsiniz", "kimdi", "kimmiş", "kimler",
    "ne", "neden", "niye", "niçin", "naber", "naaber", "neydi", "neymiş", "neler", "neyi", "neye", "neyin", "nesi", "nesin",
    "kaç", "kaça", "kaçta", "kaçtan", "kaçıncı", "kaççar", "kaçtı", "kaçtır",
    "hangi", "hangisi", "hangileri", "hangisine", "hangisinde", "hangisinden",
}

CONTRAST_CONJUNCTIONS = {"ama", "fakat", "ancak", "lakin"}
CLAUSE_CONNECTORS = {"ama", "fakat", "ancak", "lakin", "çünkü", "halbuki", "oysa", "oysaki"}
GREETING_WORDS = {"merhaba", "günaydın", "selam", "tünaydın", "selamlar", "hey", "efendim"}
FOLLOW_UP_GREETING_INDICATORS = {
    "nasılsın", "nasılsınız", "naber", "ne", "nasıl", "neredesin", "neredesiniz",
    "kimsin", "kimsiniz", "nereden", "nereye", "neden", "niye", "sen", "siz",
}


def apply_vowel_harmony(
    processed_words: List[str], changes: List[dict]
) -> Tuple[List[str], List[dict]]:
    """Soru ekini önceki kelimenin son seslisine göre büyük/küçük ünlü uyumuna girer."""
    for i in range(1, len(processed_words)):
        w = turkish_lower(processed_words[i])
        if w in QUESTION_PARTICLES:
            prev = processed_words[i - 1]
            corrected_particle = fix_question_particle(prev, w)
            if corrected_particle != w:
                changes.append({
                    "original": w,
                    "corrected": corrected_particle,
                    "rule": "TDK Ünlü Uyumu: Soru eki kendinden önceki kelimenin son ünlüsüne göre büyük/küçük ünlü uyumuna girer.",
                    "type": "vowel_harmony",
                })
            processed_words[i] = (
                turkish_upper(corrected_particle)
                if processed_words[i].isupper()
                else corrected_particle
            )
    return processed_words, changes


def apply_word_order(
    processed_words: List[str],
    punctuation_before: List[str],
    punctuation_after: List[str],
    whitespace_before: List[str],
) -> Tuple[List[str], List[str], List[str], List[str]]:
    """Devrik cümle düzeltmesi (şu anki uygulama sıralamayı korur)."""
    reordered_words = fix_word_order(processed_words[:])
    if reordered_words != processed_words:
        moved_before = punctuation_before.pop(0)
        moved_after = punctuation_after.pop(0)
        punctuation_before.append(moved_before)
        punctuation_after.append(moved_after)
        whitespace_before = [""] + [" "] * (len(reordered_words) - 1)
        processed_words = reordered_words
    return processed_words, punctuation_before, punctuation_after, whitespace_before


def apply_sentence_capitalization(
    processed_words: List[str],
    punctuation_before: List[str],
    PROTECTED_TOKEN,
) -> List[str]:
    """Cümle başındaki kelimeyi büyük harfe çevirir (korunan token ise dokunmaz)."""
    if not processed_words:
        return processed_words
    first_word = processed_words[0]
    if not (PROTECTED_TOKEN.fullmatch(first_word) or first_word.isupper()):
        processed_words[0] = turkish_capitalize(first_word)
    return processed_words


def apply_greeting_comma(
    processed_words: List[str],
    punctuation_after: List[str],
) -> List[str]:
    """Selamlaşmadan sonraki soru/çeşitre öncesine virgül ekler (Günaydın, nasılsın?)."""
    if len(processed_words) >= 2 and not punctuation_after[0]:
        if (
            turkish_lower(processed_words[0]) in GREETING_WORDS
            and turkish_lower(processed_words[1]) in FOLLOW_UP_GREETING_INDICATORS
        ):
            punctuation_after[0] = ","
    return punctuation_after


def detect_question(
    processed_words: List[str],
    punctuation_after: List[str],
) -> Tuple[bool, List[str]]:
    """Cümlenin soru cümlesi olup olmadığını tespit eder ve virgül ekler (ya sen vb.)."""
    words_lower = [turkish_lower(w) for w in processed_words]
    contrast_indices = [idx for idx, wl in enumerate(words_lower) if wl in CONTRAST_CONJUNCTIONS]
    check_slice = words_lower[contrast_indices[-1] + 1:] if contrast_indices else words_lower

    is_question = False
    for idx_w, w_low in enumerate(check_slice):
        if w_low in QUESTION_PARTICLES:
            is_question = True
            break
        if w_low in QUESTION_WORDS:
            tail_window = " ".join(check_slice[idx_w:idx_w + 5])
            if "olursa olsun" in tail_window:
                continue
            is_question = True
            break

    if not is_question and len(check_slice) >= 2:
        for q_i in range(len(check_slice) - 1):
            bigram = f"{check_slice[q_i]} {check_slice[q_i + 1]}"
            if bigram in {"ne zaman", "ne kadar", "ne haber", "kaç para", "kaç tane", "kaç kişi"}:
                tail_window = " ".join(check_slice[q_i:q_i + 5])
                if "olursa olsun" not in tail_window:
                    is_question = True
                    break

    if (
        len(processed_words) >= 2
        and turkish_lower(processed_words[-1]) in {"siz", "sen"}
    ):
        prev_low = turkish_lower(processed_words[-2])
        if prev_low in {"ya", "peki"} or any(is_finite_verb(w) for w in processed_words[:-1]):
            is_question = True
            if not punctuation_after[-2]:
                punctuation_after[-2] = ","

    if words_lower.count("ne") >= 2:
        is_question = False

    return is_question, punctuation_after


def apply_clause_commas(
    processed_words: List[str],
    reconstructed: List[str],
) -> List[str]:
    """Bağlaçlardan önce virgül ekler (ama, fakat, çünkü vb.)."""
    for i, word in enumerate(processed_words):
        if i > 0 and turkish_lower(word) in CLAUSE_CONNECTORS:
            if reconstructed and not reconstructed[-1].endswith(","):
                reconstructed[-1] = reconstructed[-1] + ","
        reconstructed.append(word)
    return reconstructed


def render_sentence(
    reconstructed: List[str],
    punctuation_before: List[str],
    punctuation_after: List[str],
    whitespace_before: List[str],
    processed_words: List[str],
    PROTECTED_TOKEN,
    PROTECTED_EMOTICONS: Set[str],
) -> Tuple[str, bool, str, str]:
    """Kelimeleri noktalama/boşlukla birleştirir; emoticon, kapanış parantezi,
    cümle-sonu noktalaması ve büyük harf uygular.

    Dönüş: (sentence, is_question, closing, emoticon_tail).
    """
    rendered_words = []
    for i, word in enumerate(reconstructed):
        rendered_words.append(punctuation_before[i] + word + punctuation_after[i])
    sentence = "".join(
        whitespace_before[i] + rendered_words[i]
        for i in range(len(rendered_words))
    )

    emoticons = "|".join(
        re.escape(value) for value in sorted(PROTECTED_EMOTICONS, key=len, reverse=True)
    )
    emoticon_match = re.search(rf"\s*(?:{emoticons})$", sentence)
    emoticon_tail = sentence[emoticon_match.start():] if emoticon_match else ""
    if emoticon_match:
        sentence = sentence[:emoticon_match.start()]

    closing_match = re.search(r'[)\]}"\'”’»]+$', sentence)
    closing = closing_match.group(0) if closing_match else ""
    sentence_body = sentence[:-len(closing)] if closing else sentence
    standalone_identifier = (
        len(processed_words) == 1
        and bool(PROTECTED_TOKEN.fullmatch(processed_words[0]))
    )

    return sentence, sentence_body, closing, emoticon_tail, standalone_identifier


def apply_sentence_ending(
    sentence_body: str,
    closing: str,
    emoticon_tail: str,
    is_question: bool,
    standalone_identifier: bool,
) -> str:
    """Cümle sonuna . veya ? ekler (zaten bitişik noktalama varsa dokunmaz)."""
    if (
        not sentence_body.endswith((".", "?", "!", "…"))
        and not emoticon_tail
        and not standalone_identifier
    ):
        if is_question:
            sentence_body += "?"
        else:
            sentence_body += "."
    return sentence_body


def capitalize_after_sentence_end(sentence: str) -> str:
    """Noktalama işaretinden sonra gelen cümlelerin ilk harfini büyütür."""

    def capitalize_turkish(letter: str) -> str:
        return turkish_upper(letter)

    return re.sub(
        r"([.!?…][ \t]+|\n[ \t\n]*)([a-zçğıöşü])",
        lambda match: match.group(1) + capitalize_turkish(match.group(2)),
        sentence,
    )
