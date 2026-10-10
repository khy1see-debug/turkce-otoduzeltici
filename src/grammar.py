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
from src.dictionary import is_valid_word
from src.deasciifier import deasciify_word
from src.harmony import fix_question_particle, get_genitive_suffix
from src.slang import expand_slang
from src.syntax import fix_word_order

QUESTION_PARTICLES = {"mi", "mı", "mu", "mü", "misin", "mısın", "musun", "müsün", "miyiz", "mıyız"}
CONJUNCTION_PARTICLES = {"de", "da"}

# Karşıtlık ve sıralama bağlaçları (öncesinde virgül konulması gereken durumlar)
CLAUSE_CONNECTORS = {"ama", "fakat", "ancak", "lakin", "çünkü", "halbuki", "oysa", "oysaki"}

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
    raw_text = raw_text.strip()
    if not raw_text:
        return ""

    tokens = raw_text.split()
    processed_words: List[str] = []
    punctuation_after: List[str] = []
    punctuation_before: List[str] = []

    for token_index, token in enumerate(tokens):
        clean_token = re.sub(r'[^\wçğıöşüÇĞİÖŞÜ]', '', token).lower()
        if not clean_token:
            if processed_words and re.fullmatch(r'[.,!?;:…]+[)\]}\"\'”’»]*', token):
                punctuation_after[-1] += token
            continue

        prefix = token[:len(token) - len(token.lstrip("([{\"'“‘«"))]
        suffix_match = re.search(r'[.,!?;:…]+[)\]}\"\'”’»]*$', token)
        suffix = suffix_match.group(0) if suffix_match else ""
        # Bilinen kısaltmaları ve bilinmeyen büyük harfli adları otomatik
        # yazım düzeltmesine sokma.
        preserve_token = (
            token.isupper() and len(clean_token) > 1
        ) or (
            token_index > 0
            and token[:1].isupper()
        )
        if preserve_token:
            processed_words.append(token)
            punctuation_after.append("")
            punctuation_before.append("")
            continue

        # 1. Aşama: Chat Kısaltması Kontrolü (slm -> selam, knk -> kanka vb.)
        slang_expanded = expand_slang(clean_token)
        if slang_expanded:
            expanded_words = slang_expanded.split()
            processed_words.extend(expanded_words)
            punctuation_before.extend([""] * len(expanded_words))
            punctuation_after.extend([""] * (len(expanded_words) - 1) + [suffix])
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
        if segmented:
            punctuation_before[len(processed_words) - len(segmented)] = prefix

    if not processed_words:
        return ""

    # -de / -da bağlacı ayrımı:
    final_tokens: List[str] = []
    final_before: List[str] = []
    final_after: List[str] = []
    for i, w in enumerate(processed_words):
        if w.lower() == "bende":
            final_tokens.extend(["ben", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
        elif w.lower() == "sende":
            final_tokens.extend(["sen", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
        elif w.lower() == "bizde":
            final_tokens.extend(["biz", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
        elif w.lower() == "sizde":
            final_tokens.extend(["siz", "de"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
        elif w.lower() == "ondada":
            final_tokens.extend(["onda", "da"])
            final_before.extend([punctuation_before[i], ""])
            final_after.extend(["", punctuation_after[i]])
        else:
            final_tokens.append(w)
            final_before.append(punctuation_before[i])
            final_after.append(punctuation_after[i])

    processed_words = final_tokens
    punctuation_before = final_before
    punctuation_after = final_after

    # İyelik ve Tamlayan (Genitive Case) İlişkisi:
    has_possessive = any(w.lower() in POSSESSIVE_NOUNS for w in processed_words[1:])
    if has_possessive and len(processed_words) > 1:
        first = processed_words[0].lower()
        if first not in {"bu", "şu", "o", "ben", "sen", "biz", "siz", "her", "bir", "ne", "nasıl"}:
            suffix = get_genitive_suffix(processed_words[0])
            processed_words[0] = processed_words[0] + suffix

    # Soru eki ünlü uyumu düzeltmesi (-mi/-mı/-mu/-mü)
    for i in range(1, len(processed_words)):
        w = processed_words[i].lower()
        if w in {"mi", "mı", "mu", "mü"}:
            prev = processed_words[i - 1]
            processed_words[i] = fix_question_particle(prev, w)

    # Devrik Cümle Düzeltmesi (Yüklemi/Fiili sona taşıma):
    reordered_words = fix_word_order(processed_words[:])
    if reordered_words != processed_words:
        punctuation_before = punctuation_before[1:] + punctuation_before[:1]
        punctuation_after = punctuation_after[1:] + punctuation_after[:1]
    processed_words = reordered_words

    # Cümle başı büyük harf (Türkçe İ / I kuralı)
    first_word = processed_words[0]
    if first_word.isupper():
        pass
    elif first_word.startswith("i"):
        processed_words[0] = "İ" + first_word[1:]
    elif first_word.startswith("ı"):
        processed_words[0] = "I" + first_word[1:]
    else:
        processed_words[0] = first_word.capitalize()

    # Soru tespiti
    is_question = False
    for word in processed_words:
        if word.lower() in QUESTION_PARTICLES or word.lower() in {"neden", "niçin", "nerede", "kim", "nasıl", "hangi", "kaç"}:
            is_question = True
            break

    # Bağlaçlardan önce otomatik virgül koyma
    reconstructed: List[str] = []
    for i, word in enumerate(processed_words):
        if i > 0 and word.lower() in CLAUSE_CONNECTORS:
            if reconstructed and not reconstructed[-1].endswith(","):
                reconstructed[-1] = reconstructed[-1] + ","
        reconstructed.append(word)

    rendered_words = []
    for i, word in enumerate(reconstructed):
        rendered_words.append(
            punctuation_before[i] + word + punctuation_after[i]
        )
    sentence = " ".join(rendered_words)

    # Var olan cümle sonu işaretini, kapanış tırnaklarının önünde koru.
    closing_match = re.search(r'[)\]}"\'”’»]+$', sentence)
    closing = closing_match.group(0) if closing_match else ""
    sentence_body = sentence[:-len(closing)] if closing else sentence
    if not sentence_body.endswith((".", "?", "!", "…")):
        if is_question:
            sentence_body += "?"
        else:
            sentence_body += "."
    sentence = sentence_body + closing

    return sentence
