import pytest
from src.grammar import fix_sentence
from src.segmenter import segment_text
from src.speller import correct_word
from src.deasciifier import deasciify_word
from src.harmony import fix_question_particle

def test_target_example():
    """Kullanıcının verdiği temel örnek senaryo."""
    raw = "sendemigeliyorusn"
    expected = "Sen de mi geliyorsun?"
    assert fix_sentence(raw) == expected

def test_separated_words_with_typo():
    """Ayrık yazılmış ama harf hatası içeren örnekler."""
    assert correct_word("geliyorusn") == "geliyorsun"
    assert correct_word("gidiyorusn") == "gidiyorsun"

def test_deasciifier():
    """İngilizce harflerin Türkçeleştirilmesi."""
    assert deasciify_word("ogrenci") == "öğrenci"
    assert deasciify_word("goz") == "göz"
    assert deasciify_word("sevinc") == "sevinç"

def test_vowel_harmony():
    """Büyük ünlü uyumu ile soru eki düzeltmesi."""
    assert fix_question_particle("değil", "mı") == "mi"
    assert fix_question_particle("oldu", "mi") == "mu"
    assert fix_question_particle("gördün", "mi") == "mü"

def test_full_complex_sentence():
    """Uzun, karmaşık, bağlaçlı ve virgüllü cümle testi."""
    raw = "ogrencileringozlerindensevincokunuyorducunkuokullaracildi"
    expected = "Öğrencilerin gözlerinden sevinç okunuyordu, çünkü okullar açıldı."
    assert fix_sentence(raw) == expected
