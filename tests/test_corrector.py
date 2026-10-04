import pytest
from src.grammar import fix_sentence
from src.segmenter import segment_text
from src.speller import correct_word

def test_target_example():
    """Kullanıcının verdiği temel örnek senaryo."""
    raw = "sendemigeliyorusn"
    expected = "Sen de mi geliyorsun?"
    assert fix_sentence(raw) == expected

def test_separated_words_with_typo():
    """Ayrık yazılmış ama harf hatası içeren örnekler."""
    assert correct_word("geliyorusn") == "geliyorsun"
    assert correct_word("gidiyorusn") == "gidiyorsun"

def test_segmentation_clean():
    """Temiz bitişik kelime ayrımı."""
    assert segment_text("bugunhavacokguzel") == ["bugün", "hava", "çok", "güzel"] or \
           segment_text("sendemi") == ["sen", "de", "mi"]

def test_question_punctuation():
    """Soru işareti ve nokta mantığı."""
    assert fix_sentence("sendemi") == "Sen de mi?"
    assert fix_sentence("beniyiyim") == "Ben iyiyim."

def test_casing():
    """Cümle başı büyük harf testi."""
    assert fix_sentence("senigordum").startswith("S")
