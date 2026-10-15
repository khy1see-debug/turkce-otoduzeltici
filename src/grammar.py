"""
Türkçe Dilbilgisi, Ek Ayrımı, Noktalama, Kod Koruması ve Kural Açıklamalı Akıllı Motor.
Hibrit Mimari:
1. Markdown ve Kod Blokları Koruması (```...``` ve `...` bloklarına dokunulmaz)
2. Chat Kısaltmaları & TDK Yaygın Hatalar (slm -> selam, knk -> kanka, herkez -> herkes, iyiki -> iyi ki)
3. Harf Uzatması Temizleyici (geliyoruuuum -> geliyorum, çoooook -> çok)
4. De-asciifier + Segmenter + Speller (Bitişik kelimeleri, harf hatalarını ve Türkçe karakterleri çözer)
5. Bağlaç & Soru Eki Ayrımı (sendemigeliyorusn -> Sen de mi geliyorsun?, geliyormusun -> Geliyor musun?)
6. Büyük ve Küçük Ünlü Uyumu Motoru (değil mi, oldu mu, bakar mısınız)
7. TDK Noktalama & İmla Standartları (Büyük harf, soru işareti, bağlaç kuralları)
8. Ayrıntılı Kural Açıklamaları (LanguageTool / Grammarly tarzı açıklama ve analiz)
"""

import re
import time
from typing import List, Dict, Any, Tuple
from src.segmenter import segment_text
from src.speller import correct_word
from src.dictionary import refresh_personal_dictionary
from src.deasciifier import deasciify_word
from src.harmony import fix_question_particle, get_genitive_suffix
from src.slang import expand_slang, normalize_elongation, TDK_COMMON_MISSPELLINGS
from src.syntax import fix_word_order
from src.turkish_case import turkish_lower, turkish_upper, turkish_capitalize
from src.tdk_rules import apply_tdk_rules

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

ATTACHED_QUESTION_REGEX = re.compile(
    r"^([a-zçğıöşü]{3,})(m[ıiuü](?:sin|sınız|siniz|sun|sunuz|sün|sünüz|yız|yiz|yuz|yüz|yım|yim|yum|yüm|di|dı|du|dü|miş|mış|muş|müş)?)$",
    re.IGNORECASE
)

QUESTION_FALSE_POSITIVES = {
    "kamu", "cami", "semi", "namu", "samu", "timu", "armi", "humi", "rumi"
}

PROTECTED_TOKEN = re.compile(
    r"(?:https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.\w+|[@#][\wçğıöşüÇĞİÖŞÜ_]+|__CODE_BLOCK_\d+__)",
    re.IGNORECASE,
)
PROTECTED_EMOTICONS = {":)", ":-)", ":(", ":-(", ":D", ":-D", ";)", ";-)", "<3", ":P", ":-P", ":3"}
PROTECTED_ABBREVIATIONS = {
    "km", "cm", "mm", "m", "kg", "mg", "g", "l", "ml", "lt",
    "sn", "dk", "tl", "kb", "mb", "gb", "tb", "hz", "khz", "mhz", "ghz",
    "vs", "vb",
}

POSSESSIVE_NOUNS = {
    "yetkisi", "arabası", "telefonu", "evi", "parası", "fikri", "hakkı",
    "işi", "çocuğu", "annesi", "babası", "kardeşi", "arkadaşı", "hatası", "suçu"
}


def _extract_code_blocks(text: str) -> Tuple[str, List[str]]:
    """Markdown kod bloklarını ve inline kodları koruma altına alır."""
    blocks: List[str] = []
    def repl(m: re.Match) -> str:
        idx = len(blocks)
        blocks.append(m.group(0))
        return f"__CODE_BLOCK_{idx}__"

    masked = re.sub(r"(```[\s\S]*?```|`[^`\n]+`)", repl, text)
    return masked, blocks


def _restore_code_blocks(text: str, blocks: List[str]) -> str:
    """Koruma altına alınan kod bloklarını geri yükler."""
    for idx, block in enumerate(blocks):
        text = text.replace(f"__CODE_BLOCK_{idx}__", block)
    return text


def analyze_sentence(raw_text: str) -> Dict[str, Any]:
    """
    Metni analiz eder, düzeltir ve her bir düzeltmenin nedenini (TDK kuralı, bağlaç,
    deasciifier vb.) detaylı bir liste halinde döner.
    """
    t0 = time.time()
    if not raw_text.strip():
        return {
            "original": raw_text,
            "corrected": "",
            "changes": [],
            "stats": {"word_count": 0, "char_count": 0, "changes_count": 0, "time_ms": 0.0}
        }

    # 1. Kod bloklarını maskele
    masked_text, code_blocks = _extract_code_blocks(raw_text)

    # 1.1. TDK Kuralları (Özel İsimler, Kısaltmalar, Fıstıkçı Şahap, Sayı/Saat İmlası)
    tdk_normalized = apply_tdk_rules(masked_text)
    if tdk_normalized != masked_text:
        masked_text = tdk_normalized

    if refresh_personal_dictionary():
        correct_word.cache_clear()

    original_text = masked_text
    leading_length = len(masked_text) - len(masked_text.lstrip())
    trailing_length = len(masked_text) - len(masked_text.rstrip())
    leading = re.sub(r" {2,}", " ", masked_text[:leading_length])
    trailing = (
        re.sub(r" {2,}", " ", masked_text[len(masked_text) - trailing_length:])
        if trailing_length else ""
    )
    content_end = len(masked_text) - trailing_length if trailing_length else len(masked_text)
    masked_text = masked_text[leading_length:content_end]

    token_matches = list(re.finditer(r"\S+", masked_text))
    tokens = [match.group(0) for match in token_matches]
    spaces_before = [
        re.sub(
            r" {2,}",
            " ",
            masked_text[token_matches[i - 1].end() if i else 0:match.start()],
        )
        for i, match in enumerate(token_matches)
    ]
    processed_words: List[str] = []
    punctuation_after: List[str] = []
    punctuation_before: List[str] = []
    whitespace_before: List[str] = []
    changes: List[Dict[str, str]] = []

    for token_index, token in enumerate(tokens):
        # Kod bloğu yer tutucusu ise doğrudan koru
        if "__CODE_BLOCK_" in token:
            processed_words.append(token)
            punctuation_after.append("")
            punctuation_before.append("")
            whitespace_before.append(spaces_before[token_index])
            continue

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

        # 0. Harf uzatması normalizasyonu (örn: geliyoruuuum -> geliyorum)
        normalized_elong = normalize_elongation(clean_token)
        if normalized_elong != clean_token:
            changes.append({
                "original": clean_token,
                "corrected": normalized_elong,
                "rule": "Harf Uzatması: Aşırı tekrar eden harfler standart Türkçeye indirgendi.",
                "type": "elongation"
            })
            clean_token = normalized_elong

        # 1. Chat Kısaltması ve TDK Yaygın Hatalar Kontrolü
        slang_expanded = expand_slang(clean_token)
        if slang_expanded:
            rule_text = "TDK Yazım Kuralı: Yaygın yazım hatası düzeltildi." if clean_token in TDK_COMMON_MISSPELLINGS else "Chat Kısaltması: Günlük konuşma kısaltması standart Türkçeye açıldı."
            changes.append({
                "original": token_core,
                "corrected": slang_expanded,
                "rule": rule_text,
                "type": "slang_or_tdk"
            })
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

        # 1.5. Bitişik soru eki ayrımı (geliyormusun -> geliyor musun)
        attached_match = ATTACHED_QUESTION_REGEX.match(clean_token)
        if attached_match and clean_token not in QUESTION_FALSE_POSITIVES:
            stem, q_particle = attached_match.group(1), attached_match.group(2)
            stem_fixed = correct_word(deasciify_word(stem))
            q_fixed = fix_question_particle(stem_fixed, q_particle)
            q_words = [stem_fixed, q_fixed]
            changes.append({
                "original": token_core,
                "corrected": f"{stem_fixed} {q_fixed}",
                "rule": "TDK Soru Eki Kuralı: Soru eki olan '-mi' daima kendinden önceki sözcükten ayrı yazılır.",
                "type": "question_suffix"
            })
            processed_words.extend(q_words)
            punctuation_before.extend([""] * len(q_words))
            punctuation_after.extend(["", suffix])
            whitespace_before.extend([spaces_before[token_index], " "])
            if prefix:
                punctuation_before[len(processed_words) - 2] = prefix
            continue

        # 2. Segmenter veya tek kelime düzeltici
        if len(clean_token) > 4:
            segmented = segment_text(clean_token)
            if len(segmented) > 1:
                changes.append({
                    "original": token_core,
                    "corrected": " ".join(segmented),
                    "rule": "Bitişik Kelime Ayrımı: Bitişik yazılmış sözcükler sözlük ve frekans tablosuyla ayrıldı.",
                    "type": "segmentation"
                })
            elif segmented and segmented[0] != clean_token:
                changes.append({
                    "original": token_core,
                    "corrected": segmented[0],
                    "rule": "İmla Düzeltme: Harf hatası ve Türkçe karakterler düzeltildi.",
                    "type": "spelling"
                })
            processed_words.extend(segmented)
        else:
            deasc = deasciify_word(clean_token)
            corrected = correct_word(deasc)
            if corrected != clean_token:
                changes.append({
                    "original": token_core,
                    "corrected": corrected,
                    "rule": "İmla & De-asciifier: Doğru Türkçe harfler tamamlandı.",
                    "type": "spelling"
                })
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
        return {
            "original": raw_text,
            "corrected": _restore_code_blocks(original_text, code_blocks),
            "changes": [],
            "stats": {"word_count": 0, "char_count": 0, "changes_count": 0, "time_ms": 0.0}
        }

    # -de / -da bağlacı ayrımı:
    final_tokens: List[str] = []
    final_before: List[str] = []
    final_after: List[str] = []
    final_whitespace: List[str] = []
    conjunction_map = {
        "bende": ("ben", "de"),
        "sende": ("sen", "de"),
        "bizde": ("biz", "de"),
        "sizde": ("siz", "de"),
        "ondada": ("onda", "da"),
        "buda": ("bu", "da"),
        "şuda": ("şu", "da"),
    }
    for i, w in enumerate(processed_words):
        w_lower = turkish_lower(w)
        if w_lower in conjunction_map:
            p1, p2 = conjunction_map[w_lower]
            changes.append({
                "original": w,
                "corrected": f"{p1} {p2}",
                "rule": "TDK Bağlaç Kuralı: Bağlaç olan 'de/da' ayrı yazılır ve asla 'te/ta' biçiminde yazılmaz.",
                "type": "conjunction"
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

    # Soru eki ünlü uyumu düzeltmesi
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
                    "type": "vowel_harmony"
                })
            processed_words[i] = (
                turkish_upper(corrected_particle)
                if processed_words[i].isupper()
                else corrected_particle
            )

    # Devrik Cümle Düzeltmesi (Güvenli kontrol)
    reordered_words = fix_word_order(processed_words[:])
    if reordered_words != processed_words:
        moved_before = punctuation_before.pop(0)
        moved_after = punctuation_after.pop(0)
        punctuation_before.append(moved_before)
        punctuation_after.append(moved_after)
        whitespace_before = [""] + [" "] * (len(reordered_words) - 1)
        processed_words = reordered_words

    # Cümle başı büyük harf
    first_word = processed_words[0]
    if not (PROTECTED_TOKEN.fullmatch(first_word) or first_word.isupper()):
        processed_words[0] = turkish_capitalize(first_word)

    # Soru tespiti
    is_question = False
    for word in processed_words:
        w_low = turkish_lower(word)
        if w_low in QUESTION_PARTICLES or w_low in {"neden", "niçin", "nerede", "kim", "nasıl", "hangi", "kaç", "ne zaman", "kimin", "nereye"}:
            is_question = True
            break

    # Bağlaçlardan önce virgül (CLAUSE_CONNECTORS)
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

    # Cümle sonu noktalamasından sonra gelen cümlelerin ilk harfini büyüt
    def capitalize_turkish(letter: str) -> str:
        return turkish_upper(letter)

    sentence = re.sub(
        r"([.!?…][ \t]+|\n[ \t\n]*)([a-zçğıöşü])",
        lambda match: match.group(1) + capitalize_turkish(match.group(2)),
        sentence,
    )

    final_result = leading + sentence + trailing
    # Kod bloklarını geri yükle
    final_result = _restore_code_blocks(final_result, code_blocks)

    elapsed_ms = (time.time() - t0) * 1000

    return {
        "original": raw_text,
        "corrected": final_result,
        "changes": changes,
        "stats": {
            "word_count": len(final_result.split()),
            "char_count": len(final_result),
            "changes_count": len(changes),
            "time_ms": round(elapsed_ms, 2)
        }
    }


def fix_sentence(raw_text: str) -> str:
    """
    Kullanıcının girdiği ham metni tam Türkçe gramer kurallarıyla düzeltir.
    Geriye sadece nihai düzeltilmiş metin döner.
    """
    analysis = analyze_sentence(raw_text)
    return analysis["corrected"]
