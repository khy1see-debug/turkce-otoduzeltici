"""
Türkçe Dilbilgisi, Ek Ayrımı, Noktalama ve İki Aşamalı Düzeltici.
Hibrit Mimari:
1. Chat Kısaltmaları & TDK Yaygın Hatalar (slm -> selam, knk -> kanka, herkez -> herkes, iyiki -> iyi ki)
2. Harf Uzatması Temizleyici (geliyoruuuum -> geliyorum, çoooook -> çok)
3. De-asciifier + Segmenter + Speller (Bitişik kelimeleri, harf hatalarını ve Türkçe karakterleri çözer)
4. Bağlaç & Soru Eki Ayrımı (sendemigeliyorusn -> Sen de mi geliyorsun?, geliyormusun -> Geliyor musun?)
5. Büyük ve Küçük Ünlü Uyumu Motoru (değil mi, oldu mu, bakar mısınız)
6. TDK Noktalama & İmla Standartları (Büyük harf, soru işareti, bağlaç kuralları)
"""

import re
from typing import List
from src.segmenter import segment_text
from src.speller import correct_word
from src.dictionary import refresh_personal_dictionary
from src.deasciifier import deasciify_word
from src.harmony import fix_question_particle, get_genitive_suffix
from src.slang import expand_slang, normalize_elongation
from src.syntax import fix_word_order
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

# Verbe bitişik yazılan soru eklerini yakalama regexi
# Örn: geliyormusun -> geliyor + musun, gordunmu -> gördün + mü
ATTACHED_QUESTION_REGEX = re.compile(
    r"^([a-zçğıöşü]{3,})(m[ıiuü](?:sin|sınız|siniz|sun|sunuz|sün|sünüz|yız|yiz|yuz|yüz|yım|yim|yum|yüm|di|dı|du|dü|miş|mış|muş|müş)?)$",
    re.IGNORECASE
)

# Soru eki zannedilmemesi gereken isim/kökler
QUESTION_FALSE_POSITIVES = {
    "kamu", "cami", "semi", "namu", "samu", "timu", "armi", "humi", "rumi"
}

# Bu belirteçler internet adresi, e-posta veya korunan etiketlerdir
PROTECTED_TOKEN = re.compile(
    r"(?:https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.\w+|[@#][\wçğıöşüÇĞİÖŞÜ_]+)",
    re.IGNORECASE,
)
PROTECTED_EMOTICONS = {":)", ":-)", ":(", ":-(", ":D", ":-D", ";)", ";-)", "<3", ":P", ":-P", ":3"}
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
    1. Chat kısaltmalarını ve TDK hatalarını açar (slm -> selam, herkez -> herkes, tşk -> teşekkürler).
    2. Aşırı harf uzatmalarını temizler (geliyoruuuum -> geliyorum, çoooook -> çok).
    3. Bitişik yazılmış kelimeleri ayırır (sendemigeliyorusn -> sen de mi geliyorsun).
    4. Türkçe harfleri deasciifier ile tamamlar (ogrenci -> öğrenci, agac -> ağaç).
    5. Harf hatalarını 1.17M Türkçe sözlükle düzeltir.
    6. Bitişik soru eklerini ayırır (geliyormusun -> geliyor musun).
    7. Soru eklerini ünlü uyumuna göre hizalar (değil mi, oldu mu, bakar mısınız).
    8. Cümle başı büyük harf yapar (Türkçe İ / I kurallarıyla).
    9. Cümle içi ve sonu noktalama işaretlerini akıllıca yerleştirir.
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

        # 0. Aşama: Harf uzatması normalizasyonu (örn: geliyoruuuum -> geliyorum, çoooook -> çok)
        clean_token = normalize_elongation(clean_token)

        # 1. Aşama: Chat Kısaltması ve TDK Yaygın Hatalar Kontrolü (slm -> selam, herkez -> herkes)
        slang_expanded = expand_slang(clean_token)
        if slang_expanded:
            expanded_words = slang_expanded.split()
            processed_words.extend(expanded_words)
            punctuation_before.extend([""] * len(expanded_words))
            punctuation_after.extend([""] * (len(expanded_words) - 1) + [suffix])
            whitespace_before.extend(
                [spaces_before[token_index]] + [" "] * (len(expanded_words) - 1)
            )
            if expanded_words and prefix:
                punctuation_before[len(processed_words) - len(expanded_words)] = prefix
            continue

        # 1.5. Bitişik soru eki ayrımı kontrolü (geliyormusun -> geliyor musun, bakar mısın)
        attached_match = ATTACHED_QUESTION_REGEX.match(clean_token)
        if attached_match and clean_token not in QUESTION_FALSE_POSITIVES:
            stem, q_particle = attached_match.group(1), attached_match.group(2)
            # Kök deasciify ve speller'dan geçsin
            stem_fixed = correct_word(deasciify_word(stem))
            q_fixed = fix_question_particle(stem_fixed, q_particle)
            q_words = [stem_fixed, q_fixed]
            processed_words.extend(q_words)
            punctuation_before.extend([""] * len(q_words))
            punctuation_after.extend(["", suffix])
            whitespace_before.extend([spaces_before[token_index], " "])
            if prefix:
                punctuation_before[len(processed_words) - 2] = prefix
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
        if segmented and prefix:
            punctuation_before[len(processed_words) - len(segmented)] = prefix

    if not processed_words:
        return original_text

    # -de / -da bağlacı ayrımı:
    # TDK: Kişi zamirlerinde ve belirli bağlaçlarda "de/da" daima ayrı yazılır
    final_tokens: List[str] = []
    final_before: List[str] = []
    final_after: List[str] = []
    final_whitespace: List[str] = []
    for i, w in enumerate(processed_words):
        w_lower = turkish_lower(w)
        if w_lower == "bende":
            final_tokens.extend(["ben", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif w_lower == "sende":
            final_tokens.extend(["sen", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif w_lower == "bizde":
            final_tokens.extend(["biz", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif w_lower == "sizde":
            final_tokens.extend(["siz", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif w_lower == "ondada":
            final_tokens.extend(["onda", "da"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif w_lower == "buda":
            final_tokens.extend(["bu", "da"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
            final_whitespace.extend([whitespace_before[i], " "])
        elif w_lower == "şuda":
            final_tokens.extend(["şu", "da"])
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

    # Soru eki ünlü uyumu düzeltmesi (-mi/-mı/-mu/-mü, -misin, -musun vb.)
    for i in range(1, len(processed_words)):
        w = turkish_lower(processed_words[i])
        if w in QUESTION_PARTICLES:
            prev = processed_words[i - 1]
            corrected_particle = fix_question_particle(prev, w)
            processed_words[i] = (
                turkish_upper(corrected_particle)
                if processed_words[i].isupper()
                else corrected_particle
            )

    # Devrik Cümle Düzeltmesi (Yüklemi/Fiili sona taşıma - güvenli kontrol):
    reordered_words = fix_word_order(processed_words[:])
    if reordered_words != processed_words:
        # Fiil sona taşındı, noktalama ve boşluk dizilimini güvenli güncelle
        moved_before = punctuation_before.pop(0)
        moved_after = punctuation_after.pop(0)
        punctuation_before.append(moved_before)
        punctuation_after.append(moved_after)
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
        w_low = turkish_lower(word)
        if w_low in QUESTION_PARTICLES or w_low in {"neden", "niçin", "nerede", "kim", "nasıl", "hangi", "kaç", "ne zaman", "kimin", "nereye"}:
            is_question = True
            break

    CLAUSE_CONNECTORS = {"ama", "fakat", "ancak", "lakin", "çünkü", "halbuki", "oysa", "oysaki"}
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
