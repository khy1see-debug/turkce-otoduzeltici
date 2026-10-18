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

def test_transposition_typos():
    """Hızlı yazımda oluşan harf yer değişimleri (naıslsınız -> nasılsınız)."""
    assert correct_word("naıslsınız") == "nasılsınız"
    assert correct_word("naısl") == "nasıl"
    assert correct_word("naıslsın") == "nasılsın"
    assert fix_sentence("gunaydın naıslsınız") == "Günaydın, nasılsınız?"
    assert fix_sentence("Günaydın naıslsınız") == "Günaydın, nasılsınız?"

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

def test_elongation_reduction():
    assert fix_sentence("geliyoruuuum") == "Geliyorum."
    assert fix_sentence("guuuuuuuuzel") == "Güzel."
    assert fix_sentence("lütfeeeen") == "Lütfen."

def test_tdk_misspellings_correction():
    assert fix_sentence("orjinal labaratuvar") == "Orijinal laboratuvar."
    assert fix_sentence("yalnış ve yanlız") == "Yanlış ve yalnız."
    assert fix_sentence("tabiki de gelirim") == "Tabii ki de gelirim."
    assert fix_sentence("iyiki varsın") == "İyi ki varsın."

def test_asciifier_and_deasciifier():
    from src.deasciifier import asciify_text, deasciify_text
    assert asciify_text("Öğrenciler şampiyon oldu.") == "Ogrenciler sampiyon oldu."
    assert deasciify_text("ogrenci goz sevinc") == "öğrenci göz sevinç"

def test_code_block_protection():
    raw = "burada kod: `git commit -m \"fix\"` ve sendemigeliyorusn"
    res = fix_sentence(raw)
    assert '`git commit -m "fix"`' in res
    assert "sen de mi geliyorsun" in res

def test_analyze_sentence():
    from src.grammar import analyze_sentence
    analysis = analyze_sentence("herkez birşey biliyo")
    assert analysis["corrected"] == "Herkes bir şey biliyor."
    assert len(analysis["changes"]) >= 2
    assert any("TDK" in c["rule"] or "Chat" in c["rule"] for c in analysis["changes"])

def test_tdk_proper_nouns_and_acronyms():
    from src.tdk_rules import apply_tdk_rules
    # Özel isimler ve kesme işareti
    assert "Ankara'da" in apply_tdk_rules("ankarada yasiyorum")
    assert "Ahmet'e" in apply_tdk_rules("ahmete verdim")
    # TDK Kısaltma kuralı ('K' harfi 'ke' okunur)
    assert "TDK'ye" in apply_tdk_rules("TDKya basvurduk")
    assert "SGK'ye" in apply_tdk_rules("SGKya gittim")

def test_tdk_consonant_assimilation():
    from src.tdk_rules import apply_tdk_rules
    # Fıstıkçı Şahap sertleşmesi
    assert "kitapçı" in apply_tdk_rules("kitapcı")
    assert "ağaçta" in apply_tdk_rules("ağaçda")
    assert "sokakta" in apply_tdk_rules("sokakda")
    assert "yaptı" in apply_tdk_rules("yapdı")

def test_tdk_colloquial_reduction():
    from src.tdk_rules import apply_tdk_rules
    assert "yapacak" in apply_tdk_rules("yapıcak")
    assert "yapacağım" in apply_tdk_rules("yapıcam")
    assert "biliyor" in apply_tdk_rules("biliyo")
    assert "geliyorum" in apply_tdk_rules("geliyom")

def test_tdk_time_and_number_grammar():
    from src.tdk_rules import apply_tdk_rules
    # Saat başlarında dakikaya değil saate göre ek: 14.00'te
    assert "14.00'te" in apply_tdk_rules("14:00 da")
    # Dakikalı saatler
    assert "14.30'da" in apply_tdk_rules("14:30 da")
    # Yıl ve sayılar
    assert "2026'da" in apply_tdk_rules("2026 de")
    assert "1923'te" in apply_tdk_rules("1923 de")


def test_homonyms_and_root_loanwords_not_corrupted():
    """Cins isim eş seslileri (abi, canı, denize, yağmurda, orduda) ve alıntı kökler (takdir, mahcup) bozulmamalı."""
    assert fix_sentence("abi naber") == "Abi naber?"
    assert fix_sentence("canı sıkıldı") == "Canı sıkıldı."
    assert fix_sentence("denize gittik") == "Denize gittik."
    assert fix_sentence("yağmurda ıslandık") == "Yağmurda ıslandık."
    assert fix_sentence("orduda görev yaptı") == "Orduda görev yaptı."
    assert fix_sentence("takdir ettim mahcup oldum") == "Takdir ettim mahcup oldum."
    assert fix_sentence("bugün işi bitirdim") == "Bugün işi bitirdim."


def test_tdk_sound_changes_and_compounds():
    """Ünlü düşmesi, ünsüz yumuşaması, birleşik fiiller ve tipografi testleri."""
    from src.tdk_rules import apply_tdk_rules
    # Ünlü Düşmesi
    assert "aklıma" in apply_tdk_rules("akılıma gelmedi") or "aklı" in apply_tdk_rules("onun akılı")
    assert "ağzı" in apply_tdk_rules("onun ağızı açık kaldı")
    assert "fikri" in apply_tdk_rules("onun fikiri güzel")
    assert "şehrin" in apply_tdk_rules("bu şehirin havası")

    # Ünsüz Yumuşaması
    assert "kitabı" in apply_tdk_rules("bu kitapı oku")
    assert "çocuğu" in apply_tdk_rules("küçük çocuku gördüm")
    assert "sokağa" in apply_tdk_rules("sokaka çıktım")

    # Bitişik Birleşik Fiiller (Ses olayı olanlar bitişik)
    assert "kayboldu" in apply_tdk_rules("anahtar kayıp oldu")
    assert "hissediyorum" in apply_tdk_rules("bunu his ediyorum")
    assert "affetti" in apply_tdk_rules("öğretmen onu af etti")
    assert "sabret" in apply_tdk_rules("biraz sabır et")

    # Üleştirme Sayıları (TDK kuralı: 2'şer değil ikişer)
    assert "ikişer" in apply_tdk_rules("öğrenciler 2'şer sıra oldu")
    assert "beşer" in apply_tdk_rules("herkese 5'er elma")

    # Tipografi ve Yüzde Temizliği
    assert apply_tdk_rules("merhaba , dünya") == "merhaba, dünya"
    assert "%50" in apply_tdk_rules("indirim oranı % 50 oldu")



def test_devrik_and_colloquial_complex_sentences():
    """Devrik cümleler, -icek/-yom daralmaları, kısaltma ekleri ve bitişik 'banasun' ayrımı."""
    assert fix_sentence("Oturuyorum yemek yedim siz") == "Oturuyorum yemek yedim, siz?"
    assert fix_sentence("deniyom bakalim pcden") == "Deniyorum bakalım PC'den."
    assert fix_sentence(
        "yaptığı projeyi bastan sona gözden geçir ve düzelticekleri düzelt geliştir ve banasun"
    ) == "Yaptığı projeyi baştan sona gözden geçir ve düzeltecekleri düzelt geliştir ve bana sun."

def test_advanced_grammar_and_punctuation():
    """Gelişmiş harf düzeltme, bağlaçlar, hitap virgülü, ikilemeler ve soru işareti testleri."""
    assert fix_sentence("merhaba nasılsın") == "Merhaba, nasılsın?"
    assert fix_sentence("selam naber") == "Selam, naber?"
    assert fix_sentence("neredesin") == "Neredesin?"
    assert fix_sentence("ne zaman geliyorsun") == "Ne zaman geliyorsun?"
    assert fix_sentence("bende geliyorum") == "Ben de geliyorum."
    assert fix_sentence("iyiki varsın") == "İyi ki varsın."
    assert fix_sentence("artarda goller attık") == "Art arda goller attık."
    assert fix_sentence("benn ve senn") == "Ben ve sen."
    assert fix_sentence("çooook güzel") == "Çok güzel."
    assert fix_sentence("gıdıyorum") == "Gidiyorum."


def test_real_world_chat_and_complex_user_sentences():
    """Gerçek kullanıcı mesajlarındaki ekliyelim/birde/herseyi/sanrıım/mesala/yazıyorya düzeltmeleri."""
    assert fix_sentence("Birde rusça çevirme tuşu Ekliyelim") == "Bir de Rusça çevirme tuşu ekleyelim."
    assert (
        fix_sentence("bu çevirme tr eng onların bunların herseyi düzelt geliştir. bazınbuglar var sanrıım")
        == "Bu çevirme TR ENG onların bunların her şeyi düzelt geliştir. Bazı buglar var sanırım."
    )
    assert (
        fix_sentence(
            "Ve birde mesala biri bana bisi yazıyorya hangi dil olursa olsun otomatik çevirebilirmiyiz ama ondan önce bu düzeltme olayını çok iyi yapmalıyız"
        )
        == "Ve bir de mesela biri bana bir şey yazıyor ya hangi dil olursa olsun otomatik çevirebilir miyiz, ama ondan önce bu düzeltme olayını çok iyi yapmalıyız."
    )
    assert fix_sentence("eklerizde") == "Ekleriz de."
    assert fix_sentence("yaparızda") == "Yaparız da."
    assert fix_sentence("giderizde") == "Gideriz de."
    assert fix_sentence("bunu gelitşir") == "Bunu geliştir."
    assert (
        fix_sentence("hayır onu eklerizde önce şimdi ben baska bir dil yani rusça ve englsihce olmıyna bir dili hangi tusla sevçicem")
        == "Hayır onu ekleriz de önce şimdi ben başka bir dil yani Rusça ve İngilizce olmayan bir dili hangi tuşla seçeceğim?"
    )
    assert fix_sentence("isviççe ekle") == "İsveççe ekle."
    assert fix_sentence("isveçce konuşuyor") == "İsveççe konuşuyor."
    assert fix_sentence("isviççe öğrenmek istiyorum") == "İsveççe öğrenmek istiyorum."
