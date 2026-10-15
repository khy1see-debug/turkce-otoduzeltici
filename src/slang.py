"""
Türkçe Chat Kısaltmaları, TDK Sık Yapılan Hatalar ve Harf Uzatması Düzeltici (Slang & Elongation Expander).
Discord, Instagram, WhatsApp ve oyun sohbetlerinde sıkça geçen kısaltmaları,
TDK resmi yazım kurallarına aykırı yaygın hataları ve uzatılmış harfleri standart Türkçeye dönüştürür.
"""

import re
from typing import Optional
from src.turkish_case import turkish_lower
from src.dictionary import is_valid_word
from src.deasciifier import deasciify_word

# TDK Resmi Yazım Kılavuzu: En Sık Yapılan Yazım Hataları ve Doğruları
TDK_COMMON_MISSPELLINGS = {
    "herkez": "herkes",
    "yalnış": "yanlış",
    "yanlız": "yalnız",
    "traş": "tıraş",
    "orjinal": "orijinal",
    "labaratuvar": "laboratuvar",
    "klavuz": "kılavuz",
    "insiyatif": "inisiyatif",
    "süpriz": "sürpriz",
    "supriz": "sürpriz",
    "eksoz": "egzoz",
    "egzos": "egzoz",
    "egzoz": "egzoz",
    "şarz": "şarj",
    "sarz": "şarj",
    "dinazor": "dinozor",
    "ahçı": "aşçı",
    "ahcilik": "aşçılık",
    "karnıbahar": "karnabahar",
    "kravat": "kravat",
    "rastlantı": "rastlantı",
    "rasgele": "rastgele",
    "ayrıyeten": "ayrıca",
    "tesbit": "tespit",
    "doküman": "doküman",
    "döküman": "doküman",
    "unvan": "unvan",
    "ünvan": "unvan",
    "muhattap": "muhatap",
    "mütahhit": "müteahhit",
    "müsade": "müsaade",
    "tabiki": "tabii ki",
    "tabikide": "tabii ki de",
    "iyiki": "iyi ki",
    "demekki": "demek ki",
    "oyleki": "öyle ki",
    "öyleki": "öyle ki",
    "kaldıki": "kaldı ki",
    "bilmemki": "bilmem ki",
    "anladımki": "anladım ki",
    "yeterki": "yeter ki",
    "farketmez": "fark etmez",
    "farketmek": "fark etmek",
    "terketmek": "terk etmek",
    "terketti": "terk etti",
    "kaybolmak": "kaybolmak",
    "arzetmek": "arz etmek",
    "haketmek": "hak etmek",
    "hakketmek": "hak etmek",
    "saatlerolsun": "sıhhatler olsun",
    "sağol": "sağ ol",
    "sagol": "sağ ol",
    "hoşçakal": "hoşça kal",
    "hoscakal": "hoşça kal",
    "hoşgeldin": "hoş geldin",
    "hosgeldin": "hoş geldin",
    "hoşbulduk": "hoş bulduk",
    "hosbulduk": "hoş bulduk",
    "pekçok": "pek çok",
    "pekaz": "pek az",
    "herbiri": "her biri",
    "hergün": "her gün",
    "hiçkimse": "hiç kimse",
    "hickimse": "hiç kimse",
    "yüzyüze": "yüz yüze",
    "ardıardına": "ardı ardına",
    "peşisıra": "peşi sıra",
    "yanısıra": "yanı sıra",
}

CHAT_SLANG_MAP = {
    # --- "Şey" İfadeleri (TDK: daima ayrı) ---
    "hersey": "her şey",
    "herşey": "her şey",
    "bişey": "bir şey",
    "bisey": "bir şey",
    "birsey": "bir şey",
    "birşey": "bir şey",
    "hiçbirşey": "hiçbir şey",
    "hicbirsey": "hiçbir şey",
    "bisi": "bir şey",
    "bişi": "bir şey",
    "coksey": "çok şey",
    "çokşey": "çok şey",
    "hicbisi": "hiçbir şey",
    "hiçbişi": "hiçbir şey",
    "hicbir": "hiçbir",
    "hicbi": "hiçbir",
    "hiçbi": "hiçbir",

    # --- Günlük Konuşma, Kalıplar ve Soru İfadeleri ---
    "bune": "bu ne",
    "şune": "şu ne",
    "sune": "şu ne",
    "one": "o ne",
    "noluor": "ne oluyor",
    "noluyo": "ne oluyor",
    "noluyor": "ne oluyor",
    "noldu": "ne oldu",
    "nolcak": "ne olacak",
    "nolucak": "ne olacak",
    "niden": "neden",
    "niye": "niye",

    # --- Konum & Bulunma Bildiren Günlük Kelimeler ---
    "içerdeyim": "içerideyim",
    "icerdeyim": "içerideyim",
    "içerde": "içeride",
    "icerde": "içeride",
    "dışardayım": "dışarıdayım",
    "disardayim": "dışarıdayım",
    "dışarda": "dışarıda",
    "disarda": "dışarıda",
    "yukardayım": "yukarıdayım",
    "yukardayim": "yukarıdayım",
    "yukarda": "yukarıda",
    "aşağdayım": "aşağıdayım",
    "aşağda": "aşağıda",
    "asagida": "aşağıda",
    "burdayım": "buradayım",
    "burdayim": "buradayım",
    "burda": "burada",
    "şurdayım": "şuradayım",
    "surdayim": "şuradayım",
    "şurda": "şurada",
    "surda": "şurada",
    "ordayım": "oradayım",
    "ordayim": "oradayım",
    "orda": "orada",

    # --- Doldurma Kelimeleri (fln, falan, vb) ---
    "fln": "falan",
    "flan": "falan",
    "flnsal": "falansal",
    "falansal": "falansal",
    "filan": "falan",
    "aynn": "aynen",
    "ayn": "aynen",

    # --- Selamlaşma & Vedalaşma & Nezaket ---
    "slm": "selam",
    "mrb": "merhaba",
    "meraba": "merhaba",
    "nbr": "naber",
    "knk": "kanka",
    "kank": "kanka",
    "krdş": "kardeş",
    "krds": "kardeş",
    "tsk": "teşekkürler",
    "tşk": "teşekkürler",
    "tskler": "teşekkürler",
    "tşkler": "teşekkürler",
    "thx": "teşekkürler",
    "eyw": "eyvallah",
    "eyv": "eyvallah",
    "hg": "hoş geldin",
    "hb": "hoş bulduk",
    "kib": "kendine iyi bak",
    "a.s": "aleyküm selam",
    "as": "aleyküm selam",
    "s.a": "selamün aleyküm",
    "sa": "selamün aleyküm",
    "bb": "bay bay",
    "by": "bay bay",
    "bye": "bay bay",
    "byebye": "bay bay",
    "tmm": "tamam",
    "tm": "tamam",
    "ok": "tamam",
    "oki": "tamam",
    "oke": "tamam",
    "okey": "tamam",
    "peki": "peki",
    "rica": "rica ederim",
    "ö.d": "önemli değil",
    "od": "önemli değil",
    "hyr": "hayır",
    "evt": "evet",
    "nys": "neyse",
    "snrm": "sanırım",
    "glba": "galiba",
    "bence": "bence",
    "sence": "sence",
    "acaba": "acaba",
    "tabi": "tabii",

    # --- Sık Kullanılan Fiil / Eylem Kısaltmaları ---
    "napion": "ne yapıyorsun",
    "napiyon": "ne yapıyorsun",
    "napıyon": "ne yapıyorsun",
    "napıyosun": "ne yapıyorsun",
    "napiyosun": "ne yapıyorsun",
    "naptin": "ne yaptın",
    "naptın": "ne yaptın",
    "naptiniz": "ne yaptınız",
    "naptınız": "ne yaptınız",
    "napim": "ne yapayım",
    "napayım": "ne yapayım",
    "napcan": "ne yapacaksın",
    "napıcaksın": "ne yapacaksın",
    "napicaksin": "ne yapacaksın",
    "napıonuz": "ne yapıyorsunuz",
    "napiyonuz": "ne yapıyorsunuz",
    "gelcenmi": "gelecek misin",
    "geliyonmu": "geliyor musun",
    "gidiyonmu": "gidiyor musun",
    "geliyomusun": "geliyor musun",
    "gidiyomusun": "gidiyor musun",
    "geliyormusun": "geliyor musun",
    "gidiyormusun": "gidiyor musun",
    "iyimisin": "iyi misin",
    "iyimisiniz": "iyi misiniz",
    "yapiyonmu": "yapıyor musun",
    "yapıyonmu": "yapıyor musun",
    "girekmi": "girelim mi",
    "girelimmi": "girelim mi",
    "oynakmi": "oynayalım mı",
    "oynayalimmi": "oynayalım mı",
    "atakmi": "atalım mı",
    "atalimmi": "atalım mı",
    "gidelimmi": "gidelim mi",
    "yapalimmi": "yapalım mı",
    "gelekmi": "gelelim mi",
    "yayindamisin": "yayında mısın",
    "yayındamısın": "yayında mısın",
    "oyundamisin": "oyunda mısın",
    "oyundamısın": "oyunda mısın",
    "dcydemisin": "dc'de misin",
    "dcdemisin": "dc'de misin",
    "burdamisin": "burada mısın",
    "burdamısın": "burada mısın",
    "ordamisin": "orada mısın",
    "ordamısın": "orada mısın",
    "evdemisin": "evde misin",
    "uyudunmu": "uyudun mu",
    "yattinmi": "yattın mı",
    "yattınmı": "yattın mı",
    "kalktinmi": "kalktın mı",
    "kalktınmı": "kalktın mı",
    "yazamiom": "yazamıyorum",
    "yazamıyom": "yazamıyorum",
    "yapamiom": "yapamıyorum",
    "yapamıyom": "yapamıyorum",
    "gidemiom": "gidemiyorum",
    "gidemiyom": "gidemiyorum",
    "gelemiom": "gelemiyorum",
    "gelemiyom": "gelemiyorum",
    "bilmiom": "bilmiyorum",
    "bilmiyom": "bilmiyorum",
    "istemiom": "istemiyorum",
    "anlamiom": "anlamıyorum",
    "anlamıyom": "anlamıyorum",
    "gorüşürüz": "görüşürüz",
    "gorusuruz": "görüşürüz",
    "geliyom": "geliyorum",
    "gidiyom": "gidiyorum",
    "geliyo": "geliyor",
    "gidiyo": "gidiyor",
    "yapıyo": "yapıyor",
    "yapiyo": "yapıyor",
    "oluyo": "oluyor",
    "biliyo": "biliyor",
    "bakiom": "bakıyorum",
    "bakıyom": "bakıyorum",
    "bekliom": "bekliyorum",
    "bekliyom": "bekliyorum",
    "özledim": "özledim",
    "ozledim": "özledim",

    # --- Zaman & Bağlaç Kısaltmaları ---
    "zmn": "zaman",
    "nezaman": "ne zaman",
    "simdi": "şimdi",
    "sora": "sonra",
    "soraan": "sonradan",
    "azora": "az sonra",
    "bida": "bir daha",
    "bidaha": "bir daha",
    "tekra": "tekrar"
}

# Birleşik haritası
ALL_EXPANSIONS = {**CHAT_SLANG_MAP, **TDK_COMMON_MISSPELLINGS}


def normalize_elongation(word: str) -> str:
    """
    Kelimedeki aşırı harf tekrarlarını (uzatmaları) temizler.
    Örnek:
      'geliyoruuuum' -> 'geliyorum'
      'coooooolll' -> 'cool'
      'guuuuuuuuzel' -> 'güzel'
      'lütfeeeen' -> 'lütfen'
      'merhabalarrrr' -> 'merhabalar'
    """
    clean_w = turkish_lower(word)
    # Eğer 3 veya daha fazla ardışık aynı harf yoksa dokunma
    if not re.search(r'(.)\1{2,}', clean_w):
        return word

    # 1. 3+ tekrar eden tüm harfleri tek veya çift harfe indirge
    # Örn: 'geliyoruuuum' -> 'geliyorum', 'cooooool' -> 'cool'
    # Önce tek harfe indirgeyip sözlük kontrolü yap
    single_reduced = re.sub(r'(.)\1{2,}', r'\1', clean_w)
    deasc_single = deasciify_word(single_reduced)
    if is_valid_word(deasc_single):
        return deasc_single
    if is_valid_word(single_reduced):
        return single_reduced

    # Çift harfe indirge (Örn: 'cooooool' -> 'cool', 'hakkkkı' -> 'hakkı')
    double_reduced = re.sub(r'(.)\1{2,}', r'\1\1', clean_w)
    deasc_double = deasciify_word(double_reduced)
    if is_valid_word(deasc_double):
        return deasc_double
    if is_valid_word(double_reduced):
        return double_reduced

    return single_reduced


def expand_slang(token: str) -> Optional[str]:
    """Kısaltma, TDK yaygın hatası veya chat argo kelimesini tam Türkçe karşılığına açar."""
    w = turkish_lower(token)
    if w in ALL_EXPANSIONS:
        return ALL_EXPANSIONS[w]

    # Uzatma kontrolü (geliyoruuuum vb.)
    normalized = normalize_elongation(w)
    if normalized != w:
        if normalized in ALL_EXPANSIONS:
            return ALL_EXPANSIONS[normalized]
        if is_valid_word(normalized):
            return normalized

    return None
