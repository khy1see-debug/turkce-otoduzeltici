"""
Türkçe Dilbilgisi, Ek Ayrımı, Noktalama ve İki Aşamalı Düzeltici.
Hibrit Mimari:
1. Chat Kısaltmaları & Argo Açıcı (slm -> selam, knk -> kanka, tsk -> teşekkürler)
2. De-asciifier + Segmenter + Speller (Bitişik kelimeleri, harf hatalarını ve Türkçe karakterleri çözer)
3. İyelik & Tamlayan Tespiti (Örnek: 'reis yetkisi oldu' -> 'Reis'in yetkisi oldu')
4. Ünlü Uyumu Motoru (-mi/-mı/-mu/-mü tam uyumu)
5. Akıllı Noktalama & Bağlaç Motoru (Virgül, soru işareti, büyük harf, -de/-da)
"""

import re
from typing import List
from src.segmenter import segment_text
from src.speller import correct_word
from src.dictionary import refresh_personal_dictionary
from src.deasciifier import deasciify_word
from src.harmony import fix_question_particle, get_genitive_suffix
from src.slang import expand_slang
from src.syntax import fix_word_order
from src.turkish_case import turkish_lower, turkish_upper, turkish_capitalize

QUESTION_PARTICLES = {
    "mi", "mı", "mu", "mü",
    "misin", "mısın", "musun", "müsün",
    "miyiz", "mıyız", "muyuz", "müyüz",
    "misiniz", "mısınız", "musunuz", "müsünüz",
    "miyim", "mıyım", "muyum", "müyüm",
}
CONJUNCTION_PARTICLES = {"de", "da"}

# Karşıtlık ve sıralama bağlaçları (öncesinde virgül konulması gereken durumlar)
CLAUSE_CONNECTORS = {"ama", "fakat", "ancak", "lakin", "çünkü", "halbuki", "oysa", "oysaki"}

# These tokens are identifiers or user-authored literals, not prose to normalize.
PROTECTED_TOKEN = re.compile(
    r"(?:https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.\w+|[@#][\wçğıöşüÇĞİÖŞÜ_]+)",
    re.IGNORECASE,
)
PROTECTED_EMOTICONS = {":)", ":-)", ":(", ":-(", ":D", ":-D", ";)", ";-)", "<3"}
PROTECTED_ABBREVIATIONS = {
    "km", "cm", "mm", "m", "kg", "mg", "g", "l", "ml", "lt",
    "sn", "dk", "tl", "kb", "mb", "gb", "tb", "hz", "khz", "mhz", "ghz",
    "vs", "vb",
}

# Sık kullanılan 3. tekil iyelik eki almış isimler (tamlayan gerektiren durumlar)
POSSESSIVE_NOUNS = {
    "yetkisi", "arabası", "telefonu", "evi", "parası", "fikri", "hakkı",
    "işi", "çocuğu", "annesi", "babası", "kardeşi", "arkadaşı", "hatası", "suçu"
}

def fix_sentence(raw_text: str) -> str:
    """
    Kullanıcının girdiği ham metni alır:
    1. Chat kısaltmalarını açar (slm -> selam, tşk -> teşekkürler).
    2. Bitişik kelimeleri ayırır (sendemigeliyorusn -> sen de mi geliyorsun).
    3. Türkçe harfleri tamamlar (ogrenci -> öğrenci, agac -> ağaç).
    4. Harf hatalarını 1.17M Türkçe sözlükle düzeltir.
    5. Tamlayan eklerini bağlar (Reis yetkisi -> Reis'in yetkisi).
    6. Soru eklerini ünlü uyumuna göre hizalar (değil mi, oldu mu).
    7. Cümle başı büyük harf yapar.
    8. Cümle içi ve sonu noktalama işaretlerini (., ?, !, ,) akıllıca yerleştirir.
    """
    if not raw_text.strip():
        return ""

    if refresh_personal_dictionary():
        correct_word.cache_clear()

    original_text = raw_text
    leading_length = len(raw_text) - len(raw_text.lstrip())
    trailing_length = len(raw_text) - len(raw_text.rstrip())
    leading = re.sub(r" {2,}", " ", raw_text[:leading_length])
    trailing = (
        re.sub(r" {2,}", " ", raw_text[len(raw_text) - trailing_length:])
        if trailing_length else ""
    )
    content_end = len(raw_text) - trailing_length if trailing_length else len(raw_text)
    raw_text = raw_text[leading_length:content_end]

    token_matches = list(re.finditer(r"\S+", raw_text))
    tokens = [match.group(0) for match in token_matches]
    spaces_before = [
        re.sub(
            r" {2,}",
            " ",
            raw_text[token_matches[i - 1].end() if i else 0:match.start()],
        )
        for i, match in enumerate(token_matches)
    ]
    processed_words: List[str] = []
    punctuation_after: List[str] = []
    punctuation_before: List[str] = []
    whitespace_before: List[str] = []

    for token_index, token in enumerate(tokens):
        clean_token = turkish_lower(re.sub(r'[^\wçğıöşüÇĞİÖŞÜ]', '', token))
        if not clean_token:
            if token in PROTECTED_EMOTICONS or re.search(r"[^\w\s.,!?;:…()\[\]{}\"'“”‘’«»]", token):
                processed_words.append(token)
                punctuation_after.append("")
                punctuation_before.append("")
                whitespace_before.append(spaces_before[token_index])
                continue
            if processed_words and re.fullmatch(r'[.,!?;:…]+[)\]}\"\'”’»]*', token):
                punctuation_after[-1] += token
            continue

        prefix = token[:len(token) - len(token.lstrip("([{\"'“‘«"))]
        suffix_match = re.search(r'[.,!?;:…]+[)\]}\"\'”’»]*$', token)
        suffix = suffix_match.group(0) if suffix_match else ""
        core_end = len(token) - len(suffix) if suffix else len(token)
        token_core = token[len(prefix):core_end]
        has_internal_symbol = bool(
            re.search(r"[^\wçğıöşüÇĞİÖŞÜ'’]", token_core)
        )
        # Bilinen kısaltmaları ve bilinmeyen büyük harfli adları otomatik
        # yazım düzeltmesine sokma. URL, e-posta ve sosyal medya belirteçleri
        # de doğal dil düzeltmesinden aynen korunur.
        preserve_token = (
            token.isupper() and len(clean_token) > 1
        ) or (
            token_index > 0
            and token[:1].isupper()
        ) or "'" in token_core or "’" in token_core or bool(
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

        # 1. Aşama: Chat Kısaltması Kontrolü (slm -> selam, knk -> kanka vb.)
        slang_expanded = expand_slang(clean_token)
        if slang_expanded:
            expanded_words = slang_expanded.split()
            processed_words.extend(expanded_words)
            punctuation_before.extend([""] * len(expanded_words))
            punctuation_after.extend([""] * (len(expanded_words) - 1) + [suffix])
            whitespace_before.extend(
                [spaces_before[token_index]] + [" "] * (len(expanded_words) - 1)
            )
            continue

        # 2. Aşama: Segmenter veya tek kelime düzeltici
        if len(clean_token) > 4:
            segmented = segment_text(clean_token)
            processed_words.extend(segmented)
        else:
            deasc = deasciify_word(clean_token)
            corrected = correct_word(deasc)
            processed_words.append(corrected)
            segmented = [corrected]
        punctuation_before.extend([""] * len(segmented))
        punctuation_after.extend([""] * (len(segmented) - 1) + [suffix])
        whitespace_before.extend(
            [spaces_before[token_index]] + [" "] * (len(segmented) - 1)
        )
        if segmented:
            punctuation_before[len(processed_words) - len(segmented)] = prefix

    if not processed_words:
        return original_text

    # -de / -da bağlacı ayrımı:
    final_tokens: List[str] = []
    final_before: List[str] = []
    final_after: List[str] = []
    final_whitespace: List[str] = []
    for i, w in enumerate(processed_words):
        if turkish_lower(w) == "bende":
            final_tokens.extend(["ben", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif turkish_lower(w) == "sende":
            final_tokens.extend(["sen", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif turkish_lower(w) == "bizde":
            final_tokens.extend(["biz", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif turkish_lower(w) == "sizde":
            final_tokens.extend(["siz", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif turkish_lower(w) == "ondada":
            final_tokens.extend(["onda", "da"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        else:
            final_tokens.append(w)
            final_before.append(punctuation_before[i])
            final_after.append(punctuation_after[i])
            final_whitespace.append(whitespace_before[i])

    processed_words = final_tokens
    punctuation_before = final_before
    punctuation_after = final_after
    whitespace_before = final_whitespace

    # İyelik ve Tamlayan (Genitive Case) İlişkisi:
    has_possessive = any(turkish_lower(w) in POSSESSIVE_NOUNS for w in processed_words[1:])
    if has_possessive and len(processed_words) > 1:
        first = turkish_lower(processed_words[0])
        if first not in {"bu", "şu", "o", "ben", "sen", "biz", "siz", "her", "bir", "ne", "nasıl"}:
            suffix = get_genitive_suffix(processed_words[0])
            processed_words[0] = processed_words[0] + suffix

    # Soru eki ünlü uyumu düzeltmesi (-mi/-mı/-mu/-mü)
    for i in range(1, len(processed_words)):
        w = turkish_lower(processed_words[i])
        if w in {"mi", "mı", "mu", "mü"}:
            prev = processed_words[i - 1]
            corrected_particle = fix_question_particle(prev, w)
            processed_words[i] = (
                turkish_upper(corrected_particle)
                if processed_words[i].isupper()
                else corrected_particle
            )

    # Devrik Cümle Düzeltmesi (Yüklemi/Fiili sona taşıma):
    reordered_words = fix_word_order(processed_words[:])
    if reordered_words != processed_words:
        punctuation_before = punctuation_before[1:] + punctuation_before[:1]
        punctuation_after = punctuation_after[1:] + punctuation_after[:1]
        whitespace_before = [""] + [" "] * (len(reordered_words) - 1)
    processed_words = reordered_words

    # Cümle başı büyük harf (Türkçe İ / I kuralı)
    first_word = processed_words[0]
    if PROTECTED_TOKEN.fullmatch(first_word) or first_word.isupper():
        pass
    else:
        processed_words[0] = turkish_capitalize(first_word)

    # Soru tespiti
    is_question = False
    for word in processed_words:
        if turkish_lower(word) in QUESTION_PARTICLES or turkish_lower(word) in {"neden", "niçin", "nerede", "kim", "nasıl", "hangi", "kaç"}:
            is_question = True
            break

    # Bağlaçlardan önce otomatik virgül koyma
    reconstructed: List[str] = []
    for i, word in enumerate(processed_words):
        if i > 0 and turkish_lower(word) in CLAUSE_CONNECTORS:
            if reconstructed and not reconstructed[-1].endswith(","):
                reconstructed[-1] = reconstructed[-1] + ","
        reconstructed.append(word)

    rendered_words = []
    for i, word in enumerate(reconstructed):
        rendered_words.append(
            punctuation_before[i] + word + punctuation_after[i]
        )
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

    # Var olan cümle sonu işaretini, kapanış tırnaklarının önünde koru.
    closing_match = re.search(r'[)\]}"\'”’»]+$', sentence)
    closing = closing_match.group(0) if closing_match else ""
    sentence_body = sentence[:-len(closing)] if closing else sentence
    standalone_identifier = (
        len(processed_words) == 1
        and bool(PROTECTED_TOKEN.fullmatch(processed_words[0]))
    )
    if (
        not sentence_body.endswith((".", "?", "!", "…"))
        and not emoticon_tail
        and not standalone_identifier
    ):
        if is_question:
            sentence_body += "?"
        else:
            sentence_body += "."
    sentence = sentence_body + closing + emoticon_tail

    # Cümle sonu noktalamasından sonra gelen cümlelerin ilk harfini de büyüt.
    def capitalize_turkish(letter: str) -> str:
        return turkish_upper(letter)

    sentence = re.sub(
        r"([.!?…][ \t]+|\n[ \t\n]*)([a-zçğıöşü])",
        lambda match: match.group(1) + capitalize_turkish(match.group(2)),
        sentence,
    )

    return leading + sentence + trailing
