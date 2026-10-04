"""
Türkçe Dilbilgisi, Ek Ayrımı ve Noktalama Düzenleyici.
- Soru ekleri (-mi, -mı, -mu, -mü) ayrımı
- Bağlaç olan -de/-da ayrımı
- Cümle başı büyük harf ve sonuna uygun noktalama işareti (? veya .)
"""

from typing import List
from src.segmenter import segment_text
from src.speller import correct_word

QUESTION_PARTICLES = {"mi", "mı", "mu", "mü"}

def fix_sentence(raw_text: str) -> str:
    """
    Kullanıcının girdiği ham metni (örn: 'sendemigeliyorusn') alır:
    1. Kelimelere ayırır ve yazım yanlışlarını düzeltir.
    2. Soru eki ve bağlaçları kurallara uygun hizalar.
    3. Cümle başı büyük harf yapar.
    4. Soru içeriyorsa '?' değilse '.' ekler.
    """
    raw_text = raw_text.strip()
    if not raw_text:
        return ""

    # Eğer metin zaten boşluk içeriyorsa parça parça segmenter'dan geçir
    tokens = raw_text.split()
    processed_words: List[str] = []

    for token in tokens:
        # Eğer tek parça uzun ve bitişikse segment et
        if len(token) > 4:
            segmented = segment_text(token)
            processed_words.extend(segmented)
        else:
            processed_words.append(correct_word(token))

    if not processed_words:
        return ""

    # Türkçe özel kural: Baş harfi büyüt
    first_word = processed_words[0]
    if first_word.startswith("i"):
        processed_words[0] = "İ" + first_word[1:]
    elif first_word.startswith("ı"):
        processed_words[0] = "I" + first_word[1:]
    else:
        processed_words[0] = first_word.capitalize()

    # Soru eki kontrolü
    is_question = False
    for word in processed_words:
        if word.lower() in QUESTION_PARTICLES:
            is_question = True
            break

    # Cümleyi oluştur
    sentence = " ".join(processed_words)

    # Sonuna noktalama işareti ekle (eğer zaten yoksa)
    if not sentence.endswith((".", "?", "!")):
        if is_question:
            sentence += "?"
        else:
            sentence += "."

    return sentence
