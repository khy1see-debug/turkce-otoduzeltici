"""
Türkçe Dilbilgisi, Ek Ayrımı, Noktalama ve İki Aşamalı Düzeltici.
Hibrit Mimari:
1. De-asciifier + Segmenter + Speller (Bitişik kelimeleri, harf hatalarını ve Türkçe karakterleri çözer)
2. İyelik & Tamlayan Tespiti (Örnek: 'reis yetkisi oldu' -> 'Reis'in yetkisi oldu')
3. Ünlü Uyumu Motoru (-mi/-mı/-mu/-mü tam uyumu)
4. Akıllı Noktalama & Bağlaç Motoru (Virgül, soru işareti, büyük harf, -de/-da)
"""

import re
from typing import List
from src.segmenter import segment_text
from src.speller import correct_word
from src.deasciifier import deasciify_word
from src.harmony import fix_question_particle, get_genitive_suffix

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
    1. Bitişik kelimeleri ayırır (sendemigeliyorusn -> sen de mi geliyorsun).
    2. Türkçe harfleri tamamlar (ogrenci -> öğrenci, agac -> ağaç).
    3. Harf hatalarını 1.17M Türkçe sözlükle düzeltir.
    4. Tamlayan eklerini bağlar (Reis yetkisi -> Reis'in yetkisi).
    5. Soru eklerini ünlü uyumuna göre hizalar (değil mi, oldu mu).
    6. Cümle başı büyük harf yapar.
    7. Cümle içi ve sonu noktalama işaretlerini (., ?, !, ,) akıllıca yerleştirir.
    """
    raw_text = raw_text.strip()
    if not raw_text:
        return ""

    tokens = raw_text.split()
    processed_words: List[str] = []

    for token in tokens:
        # Noktalama işaretlerinden arındırarak işle
        clean_token = re.sub(r'[^\wçğıöşüÇĞİÖŞÜ]', '', token)
        if len(clean_token) > 4:
            segmented = segment_text(clean_token)
            processed_words.extend(segmented)
        elif clean_token:
            deasc = deasciify_word(clean_token)
            corrected = correct_word(deasc)
            processed_words.append(corrected)

    if not processed_words:
        return ""

    # 1. -de / -da bağlacı ayrımı:
    final_tokens: List[str] = []
    for i, w in enumerate(processed_words):
        if w.lower() == "bende":
            final_tokens.extend(["ben", "de"])
        elif w.lower() == "sende":
            final_tokens.extend(["sen", "de"])
        elif w.lower() == "bizde":
            final_tokens.extend(["biz", "de"])
        elif w.lower() == "sizde":
            final_tokens.extend(["siz", "de"])
        elif w.lower() == "ondada":
            final_tokens.extend(["onda", "da"])
        else:
            final_tokens.append(w)

    processed_words = final_tokens

    # 2. İyelik ve Tamlayan (Genitive Case) İlişkisi:
    # Eğer cümlede bir iyelik eki ('yetkisi') varsa ve baştaki kelime özne/isim ise ('reis'),
    # özneye kesme işaretiyle tamlayan eki ekle ('Reis'in').
    has_possessive = any(w.lower() in POSSESSIVE_NOUNS for w in processed_words[1:])
    if has_possessive and len(processed_words) > 1:
        first = processed_words[0].lower()
        if first not in {"bu", "şu", "o", "ben", "sen", "biz", "siz", "her", "bir", "ne", "nasıl"}:
            suffix = get_genitive_suffix(processed_words[0])
            processed_words[0] = processed_words[0] + suffix

    # 3. Soru eki ünlü uyumu düzeltmesi (-mi/-mı/-mu/-mü)
    for i in range(1, len(processed_words)):
        w = processed_words[i].lower()
        if w in {"mi", "mı", "mu", "mü"}:
            prev = processed_words[i - 1]
            processed_words[i] = fix_question_particle(prev, w)

    # 4. Cümle başı büyük harf (Türkçe İ / I kuralı)
    first_word = processed_words[0]
    if first_word.startswith("i"):
        processed_words[0] = "İ" + first_word[1:]
    elif first_word.startswith("ı"):
        processed_words[0] = "I" + first_word[1:]
    else:
        processed_words[0] = first_word.capitalize()

    # 5. Soru tespiti
    is_question = False
    for word in processed_words:
        if word.lower() in QUESTION_PARTICLES or word.lower() in {"neden", "niçin", "nerede", "kim", "nasıl", "hangi", "kaç"}:
            is_question = True
            break

    # 6. Bağlaçlardan önce otomatik virgül koyma
    reconstructed: List[str] = []
    for i, word in enumerate(processed_words):
        if i > 0 and word.lower() in CLAUSE_CONNECTORS:
            if reconstructed and not reconstructed[-1].endswith(","):
                reconstructed[-1] = reconstructed[-1] + ","
        reconstructed.append(word)

    sentence = " ".join(reconstructed)

    # 7. Cümle sonu noktalama
    if not sentence.endswith((".", "?", "!")):
        if is_question:
            sentence += "?"
        else:
            sentence += "."

    return sentence
