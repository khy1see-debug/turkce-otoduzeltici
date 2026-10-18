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
    "mesala": "mesela",
    "sanrıım": "sanırım",
    "sanrım": "sanırım",
    "sanırm": "sanırım",
    "sanirim": "sanırım",
    "birde": "bir de",
    "hemde": "hem de",
    "yada": "ya da",
    "ekliyelim": "ekleyelim",
    "ekliyebilir": "ekleyebilir",
    "başlıyalım": "başlayalım",
    "bekliyelim": "bekleyelim",
    "söyliyelim": "söyleyelim",
    "izliyelim": "izleyelim",
    "dinliyelim": "dinleyelim",
    "anlıyamadım": "anlayamadım",
    "olmıyan": "olmayan",
    "olmıyna": "olmayan",
    "olmıycak": "olmayacak",
    "olmıyacak": "olmayacak",
    "secicem": "seçeceğim",
    "seçicem": "seçeceğim",
    "sevçicem": "seçeceğim",
    "secicez": "seçeceğiz",
    "seçicez": "seçeceğiz",
    "sevçicez": "seçeceğiz",
    "englsihce": "İngilizce",
    "englıshce": "İngilizce",
    "inglizce": "İngilizce",
    "gelitşir": "geliştir",
    "baska": "başka",
    "isviççe": "İsveççe",
    "isvicce": "İsveççe",
    "isveçce": "İsveççe",
    "isvecce": "İsveççe",
}

CHAT_SLANG_MAP = {
    # --- "Şey" İfadeleri (TDK: daima ayrı) ---
    "hersey": "her şey",
    "herşey": "her şey",
    "herseyi": "her şeyi",
    "herşeyi": "her şeyi",
    "herseyin": "her şeyin",
    "herşeyin": "her şeyin",
    "herseye": "her şeye",
    "herşeye": "her şeye",
    "herseyde": "her şeyde",
    "herşeyde": "her şeyde",
    "herseyden": "her şeyden",
    "herşeyden": "her şeyden",
    "herseyle": "her şeyle",
    "herşeyle": "her şeyle",
    "bişey": "bir şey",
    "bisey": "bir şey",
    "birsey": "bir şey",
    "birşey": "bir şey",
    "birseyi": "bir şeyi",
    "birşeyi": "bir şeyi",
    "biseyi": "bir şeyi",
    "bişeyi": "bir şeyi",
    "birseyin": "bir şeyin",
    "birşeyin": "bir şeyin",
    "biseyin": "bir şeyin",
    "bişeyin": "bir şeyin",
    "birseye": "bir şeye",
    "birşeye": "bir şeye",
    "biseye": "bir şeye",
    "bişeye": "bir şeye",
    "birseyde": "bir şeyde",
    "birşeyde": "bir şeyde",
    "birseyden": "bir şeyden",
    "birşeyden": "bir şeyden",
    "birşeyler": "bir şeyler",
    "birşeyleri": "bir şeyleri",
    "bişeyler": "bir şeyler",
    "biseyler": "bir şeyler",
    "birseyler": "bir şeyler",
    "hiçbirşey": "hiçbir şey",
    "hicbirsey": "hiçbir şey",
    "hiçbirşeyi": "hiçbir şeyi",
    "hicbirseyi": "hiçbir şeyi",
    "hiçbirşeyin": "hiçbir şeyin",
    "hicbirseyin": "hiçbir şeyin",
    "bisi": "bir şey",
    "bişi": "bir şey",
    "bisiler": "bir şeyler",
    "bişiler": "bir şeyler",
    "bisiyi": "bir şeyi",
    "bişiyi": "bir şeyi",
    "coksey": "çok şey",
    "çokşey": "çok şey",
    "cokseyi": "çok şeyi",
    "çokşeyi": "çok şeyi",
    "hicbisi": "hiçbir şey",
    "hiçbişi": "hiçbir şey",
    "hicbir": "hiçbir",
    "hicbi": "hiçbir",
    "hiçbi": "hiçbir",

    # --- Günlük Konuşma, Kalıplar ve Soru İfadeleri ---
    "naısl": "nasıl",
    "naıslsın": "nasılsın",
    "naıslsınız": "nasılsınız",
    "nsaıl": "nasıl",
    "naslsn": "nasılsın",
    "naslsnz": "nasılsınız",
    "nasılsnz": "nasılsınız",
    "gıdıyor": "gidiyor",
    "gıdıyorum": "gidiyorum",
    "gıdıyorsun": "gidiyorsun",
    "gıdıyoruz": "gidiyoruz",
    "gıdıyorsunuz": "gidiyorsunuz",
    "bılmıyorum": "bilmiyorum",
    "bılmıyor": "bilmiyor",
    "bılmıyorsun": "bilmiyorsun",
    "yaprken": "yaparken",
    "geliyorsn": "geliyorsun",
    "gidiyorsn": "gidiyorsun",
    "tmmdır": "tamamdır",
    "tmdır": "tamamdır",
    "skntı": "sıkıntı",
    "sknti": "sıkıntı",
    "sıkntı": "sıkıntı",
    "ztn": "zaten",
    "bgn": "bugün",
    "yrn": "yarın",
    "artarda": "art arda",
    "yanyana": "yan yana",
    "elele": "el ele",
    "yuzyuze": "yüz yüze",
    "pespese": "peş peşe",
    "peşpeşe": "peş peşe",
    "basbasa": "baş başa",
    "başbaşa": "baş başa",
    "icice": "iç içe",
    "içiçe": "iç içe",
    "gozgoze": "göz göze",
    "gözgöze": "göz göze",
    "dizdize": "diz dize",
    "gundengune": "günden güne",
    "gündengüne": "günden güne",
    "adımadım": "adım adım",
    "şöyleki": "şöyle ki",
    "gördümki": "gördüm ki",
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

    # --- Kullanıcı Günlük & Sohbet Kalıpları ---
    "vesallam": "vesselam",
    "vessellam": "vesselam",
    "ries": "reis",
    "övelimmi": "övelim mi",
    "ovelimmi": "övelim mi",
    "anlamıyyer": "anlamıyor",
    "anlamiyyer": "anlamıyor",
    "çıldıryporum": "çıldırıyorum",
    "cildiryporum": "çıldırıyorum",
    "hayırlıolsunikkan": "hayırlı olsun ikkan",
    "hayirliolsunikkan": "hayırlı olsun ikkan",
    "patlatıcağz": "patlatacağız",
    "patlaticagz": "patlatacağız",

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


def expand_colloquial_verb(token: str) -> Optional[str]:
    """
    Günlük konuşma ve mesajlaşma dilindeki kestirme fiil eklerini
    standart Türkçe fiil çekimlerine dönüştürür.
    Örnekler:
      deniyom / denıyorm -> deniyorum
      yapıyorsn -> yapıyorsun
      deniyon -> deniyorsun
      yapıyo -> yapıyor
      yapcam -> yapacağım
      gelcem -> geleceğim
    """
    clean_w = turkish_lower(token)
    if is_valid_word(clean_w):
        return None

    # -yorsn -> -yorsun (örn: yapıyorsn, geliyorsn)
    m = re.match(r"^([a-zçğıöşü]{2,})yorsn$", clean_w)
    if m:
        cand = deasciify_word(m.group(1) + "yorsun")
        if is_valid_word(cand):
            return cand

    # -yorm / -yom / -yım -> -yorum (örn: deniyom, denıyorm, bakıyom, gidiyom)
    m = re.match(r"^([a-zçğıöşü]{2,})(?:yorm|yom|yım)$", clean_w)
    if m:
        base = deasciify_word(m.group(1) + "yorum")
        for cand in [base, base.replace('ı', 'i'), base.replace('i', 'ı')]:
            if is_valid_word(cand):
                return cand

    # -yon -> -yorsun (örn: deniyon, bakıyon, geliyon)
    m = re.match(r"^([a-zçğıöşü]{2,})yon$", clean_w)
    if m:
        cand = deasciify_word(m.group(1) + "yorsun")
        if is_valid_word(cand):
            return cand

    # -yo -> -yor (örn: geliyo, gidiyo, bakıyo)
    m = re.match(r"^([a-zçğıöşü]{2,})yo$", clean_w)
    if m:
        cand = deasciify_word(m.group(1) + "yor")
        if is_valid_word(cand):
            return cand

    # -yoz -> -yoruz (örn: geliyoz, gidiyoz)
    m = re.match(r"^([a-zçğıöşü]{2,})yoz$", clean_w)
    if m:
        cand = deasciify_word(m.group(1) + "yoruz")
        if is_valid_word(cand):
            return cand

    # -yonuz -> -yorsunuz (örn: geliyonuz, gidiyonuz)
    m = re.match(r"^([a-zçğıöşü]{2,})yonuz$", clean_w)
    if m:
        cand = deasciify_word(m.group(1) + "yorsunuz")
        if is_valid_word(cand):
            return cand

    # -cam / -cem -> -acağım / -eceğim (örn: yapcam -> yapacağım, gelcem -> geleceğim)
    m = re.match(r"^([a-zçğıöşü]{2,})(cam|cem)$", clean_w)
    if m:
        stem, suffix = m.group(1), m.group(2)
        cand = deasciify_word(stem + ("acağım" if suffix == "cam" else "eceğim"))
        if is_valid_word(cand):
            return cand

    # -cak / -cek -> -acak / -ecek (örn: yapcak -> yapacak, gelcek -> gelecek)
    m = re.match(r"^([a-zçğıöşü]{2,})(cak|cek)$", clean_w)
    if m:
        stem, suffix = m.group(1), m.group(2)
        cand = deasciify_word(stem + ("acak" if suffix == "cak" else "ecek"))
        if is_valid_word(cand):
            return cand

    # -icek / -ıcak / -ücek / -ucak ve gereksiz daralma (-iyelim / -ıyalım / -iyemedi / -ıyamadı)
    for narrow, wide in [
        ("icem", "eceğim"), ("ıcam", "acağım"), ("ucam", "acağım"), ("ücem", "eceğim"),
        ("icez", "eceğiz"), ("ıcaz", "acağız"), ("ucaz", "acağız"), ("ücez", "eceğiz"),
        ("icek", "ecek"), ("ıcak", "acak"), ("ucak", "acak"), ("ücek", "ecek"),
        ("iceğ", "eceğ"), ("ıcağ", "acağ"), ("ucağ", "acağ"), ("üceğ", "eceğ"),
        ("iyelim", "eyelim"), ("ıyalım", "ayalım"), ("iyeyim", "eyeyim"), ("ıyayım", "ayayım"),
        ("iyebilir", "eyebilir"), ("ıyabilir", "ayabilir"), ("iyemedi", "eyemedi"), ("ıyamadı", "ayamadı"),
    ]:
        if narrow in clean_w and not clean_w.startswith(("diye", "yiye")):
            cand = deasciify_word(clean_w.replace(narrow, wide, 1))
            if is_valid_word(cand):
                return cand

    return None


ATTACHED_VERBAL_DE_REGEX = re.compile(
    r"^([a-zçğıöşü]{2,}(?:riz|rız|ruz|rüz|iriz|ırız|uruz|ürüz|eriz|arız|sak|sek|sam|sem|dık|dik|duk|dük|tık|tik|tuk|tük|yoruz|yorsunuz|acağız|eceğiz|alım|elim))(da|de|ta|te)$",
    re.IGNORECASE
)


def expand_slang(token: str) -> Optional[str]:
    """Kısaltma, TDK yaygın hatası veya chat argo kelimesini tam Türkçe karşılığına açar."""
    w = turkish_lower(token)
    if w in ALL_EXPANSIONS:
        return ALL_EXPANSIONS[w]

    # Fiil çekiminden sonra bitişik yazılmış bağlaç 'de/da' kontrolü (örn: eklerizde -> ekleriz de, yaparızda -> yaparız da)
    m_vde = ATTACHED_VERBAL_DE_REGEX.match(w)
    if m_vde:
        stem_raw = m_vde.group(1)
        deasc_stem = deasciify_word(stem_raw)
        canonical_stem = deasc_stem if is_valid_word(deasc_stem) else stem_raw
        if is_valid_word(canonical_stem):
            vowels = [c for c in canonical_stem if c in "aıoueöiü"]
            de_norm = "da" if vowels and vowels[-1] in "aıou" else "de"
            return f"{canonical_stem} {de_norm}"

    # Bitişik yazılmış her+şey / bir+şey / hiçbir+şey çekimli halleri (örn: herşeyimiz -> her şeyimiz)
    m_sey = re.match(r"^(her|hiçbir|hicbir|bir|bi|çok|cok)(?:şey|sey)([a-zçğıöşü]*)$", w)
    if m_sey:
        prefix_part, suffix_part = m_sey.group(1), m_sey.group(2)
        prefix_map = {"her": "her", "hiçbir": "hiçbir", "hicbir": "hiçbir", "bir": "bir", "bi": "bir", "çok": "çok", "cok": "çok"}
        sey_word = deasciify_word("şey" + suffix_part) if suffix_part else "şey"
        if is_valid_word(sey_word):
            return f"{prefix_map[prefix_part]} {sey_word}"

    # Günlük fiil çekim normalizasyonu
    verb_cand = expand_colloquial_verb(w)
    if verb_cand:
        return verb_cand

    # Uzatma kontrolü (geliyoruuuum vb.)
    normalized = normalize_elongation(w)
    if normalized != w:
        if normalized in ALL_EXPANSIONS:
            return ALL_EXPANSIONS[normalized]
        verb_norm = expand_colloquial_verb(normalized)
        if verb_norm:
            return verb_norm
        if is_valid_word(normalized):
            return normalized

    return None

