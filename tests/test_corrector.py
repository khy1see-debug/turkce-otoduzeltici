from src.grammar import fix_sentence
from src.speller import correct_word
from src.deasciifier import deasciify_word
from src.harmony import fix_question_particle
from src.turkish_case import turkish_lower, turkish_upper

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

def test_turkish_dotted_and_dotless_i_case_mapping():
    assert turkish_lower("I İ") == "ı i"
    assert turkish_upper("i ı") == "İ I"
    assert fix_question_particle("KAPI", "Mİ") == "mı"
    assert fix_sentence("BU GÜZEL Mİ") == "BU GÜZEL Mİ?"

def test_full_complex_sentence():
    """Uzun, karmaşık, bağlaçlı ve virgüllü cümle testi."""
    raw = "ogrencileringozlerindensevincokunuyorducunkuokullaracildi"
    expected = "Öğrencilerin gözlerinden sevinç okunuyordu, çünkü okullar açıldı."
    assert fix_sentence(raw) == expected

def test_protected_identifiers_are_not_spell_corrected():
    """URLs, emails, mentions and hashtags should survive prose correction."""
    raw = "site https://ornek.com/kayit, mail ad.soyad@example.com @kullanici #OtoDuzeltici"
    expected = "Site https://ornek.com/kayit, mail ad.soyad@example.com @kullanici #OtoDuzeltici."
    assert fix_sentence(raw) == expected

def test_links_at_sentence_start_keep_their_case():
    url = "https://ornek.com/foo?x=1&y=2"
    assert fix_sentence(url) == url
    assert fix_sentence("@kullanici") == "@kullanici"

def test_second_sentence_starts_with_turkish_capital_letter():
    assert fix_sentence("Merhaba dünya. bugün hava güzel") == "Merhaba dünya. Bugün hava güzel."
    assert fix_sentence("Tamamdır. istanbul'a gidiyorum") == "Tamamdır. İstanbul'a gidiyorum."

def test_symbols_and_emoticons_are_preserved():
    assert fix_sentence("2+2=4 ve C++ öğreniyorum") == "2+2=4 ve C++ öğreniyorum."
    assert fix_sentence("Merhaba :) nasılsın?") == "Merhaba :) nasılsın?"
    assert fix_sentence("Merhaba :)") == "Merhaba :)"

def test_numbers_units_and_punctuation_only_input_are_preserved():
    assert fix_sentence("Bugün 10 km yürüdüm") == "Bugün 10 km yürüdüm."
    assert fix_sentence("Versiyon v1.2.3 çıktı") == "Versiyon v1.2.3 çıktı."
    assert fix_sentence("...") == "..."

def test_redundant_spaces_collapse_and_tabs_line_breaks_are_preserved():
    assert fix_sentence("merhaba   dünya") == "Merhaba dünya."
    assert fix_sentence("merhaba\t\tdünya\nbugün") == "Merhaba\t\tdünya\nBugün."
    assert fix_sentence("sendemigeliyorusn") == "Sen de mi geliyorsun?"
    assert fix_sentence("\n  merhaba dünya  \n") == "\n Merhaba dünya. \n"

def test_common_turkish_spelling_and_chat_typos():
    assert fix_sentence("herkez birşey biliyo") == "Herkes bir şey biliyor."
    assert fix_sentence("geliyomusun") == "Geliyor musun?"
    assert fix_sentence("iyimisin") == "İyi misin?"
    assert fix_sentence("hiçbirşey anlamadım") == "Hiçbir şey anlamadım."

def test_question_suffix_written_attached_is_separated():
    assert fix_sentence("geliyormusun") == "Geliyor musun?"
    assert fix_sentence("iyimisiniz") == "İyi misiniz?"
