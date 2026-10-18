"""
TDK İmla Kuralları, Ses Olayları ve Biçimlendirme Motoru (0-Token, Offline).
1. Özel İsimler ve Kısaltmalarda Kesme İşareti (') ve Büyük Harf Kuralı.
2. Ünsüz Benzeşmesi (Fıstıkçı Şahap: kitapcı -> kitapçı, ağaçda -> ağaçta).
3. Konuşma Dili Daralma Düzeltmesi (yapıcak -> yapacak, biliyo -> biliyor).
4. Saat, Sayı ve Tarih İmlası (14:00'da -> 14.00'te, 2026 de -> 2026'da).
"""

import re
from src.turkish_case import turkish_lower, turkish_capitalize

# ==============================================================================
# 1. ÖZEL İSİMLER VE KISALTMALAR (TDK KESME İŞARETİ KURALI)
# ==============================================================================

# Türkiye'nin 81 ili
TURKISH_CITIES = {
    "adana", "adıyaman", "afyonkarahisar", "ağrı", "amasya", "ankara", "antalya",
    "artvin", "aydın", "balıkesir", "bilecik", "bingöl", "bitlis", "bolu", "burdur",
    "bursa", "çanakkale", "çankırı", "çorum", "denizli", "diyarbakır", "edirne",
    "elazığ", "erzincan", "erzurum", "eskişehir", "gaziantep", "giresun", "gümüşhane",
    "hakkari", "hatay", "isparta", "mersin", "istanbul", "izmir", "kars", "kastamonu",
    "kayseri", "kırklareli", "kırşehir", "kocaeli", "konya", "kütahya", "malatya",
    "manisa", "kahramanmaraş", "mardin", "muğla", "muş", "nevşehir", "niğde", "ordu",
    "rize", "sakarya", "samsun", "siirt", "sinop", "sivas", "tekirdağ", "tokat",
    "trabzon", "tunceli", "şanlıurfa", "uşak", "van", "yozgat", "zonguldak", "aksaray",
    "bayburt", "karaman", "kırıkkale", "batman", "şırnak", "bartın", "ardahan",
    "iğdır", "yalova", "karabük", "kilis", "osmaniye", "düzce"
}

# Yaygın kişi adları ve ülkeler
COMMON_PROPER_NOUNS = {
    "ahmet", "mehmet", "ali", "ayşe", "fatma", "mustafa", "enes", "can", "zeynep",
    "elif", "emre", "burak", "ceren", "merve", "yusuf", "ibrahim", "ömer", "deniz",
    "cem", "berk", "selin", "yağmur", "gizem", "kerem", "ece", "kemal", "atatürk",
    "türkiye", "almanya", "fransa", "ingiltere", "amerika", "italya", "rusya", "japonya"
}

ALL_PROPER_STEMS = TURKISH_CITIES | COMMON_PROPER_NOUNS

# TDK Yaygın Kısaltmaları ve Ek Kuralları
# Kural: Kısaltmalarda 'K' harfi 'ka' değil 'ke' okunur (TDK'ye, SGK'ye).
ACRONYM_SUFFIX_CORRECTIONS = {
    "TDK'ya": "TDK'ye",
    "TDK'nin": "TDK'nin",
    "SGK'ya": "SGK'ye",
    "SSK'ya": "SSK'ye",
    "MEB'a": "MEB'e",
    "TBMM'ya": "TBMM'ye",
    "TÜBİTAK'e": "TÜBİTAK'a",
    "RTÜK'a": "RTÜK'e",
    "YÖK'e": "YÖK'e",
    "THY'ya": "THY'ye"
}

TECH_ACRONYMS = {
    "pc", "gpu", "cpu", "ram", "ssd", "usb", "dc", "tr", "eng", "ai", "llm"
}

LANGUAGE_NORMALIZATION_MAP = {
    "türkçe": "Türkçe", "turkce": "Türkçe", "türkce": "Türkçe",
    "ingilizce": "İngilizce",
    "rusça": "Rusça", "rusca": "Rusça",
    "almanca": "Almanca",
    "fransızca": "Fransızca", "fransizca": "Fransızca",
    "ispanyolca": "İspanyolca",
    "italyanca": "İtalyanca",
    "arapça": "Arapça", "arapca": "Arapça",
    "japonca": "Japonca",
    "çince": "Çince", "cince": "Çince",
    "korece": "Korece",
    "portekizce": "Portekizce",
    "yunanca": "Yunanca",
    "farsça": "Farsça", "farsca": "Farsça",
    "isveççe": "İsveççe", "isveçce": "İsveççe", "isvecce": "İsveççe", "isviççe": "İsveççe", "isvicce": "İsveççe",
}

KNOWN_ACRONYMS = {
    "tdk", "sgk", "ssk", "meb", "tbmm", "tübitak", "rtük", "yök", "thy", "abd", "ab", "chp", "akp", "mhp"
} | TECH_ACRONYMS

# ==============================================================================
# 2. ÜNSÜZ BENZEŞMESİ (FISTIKÇI ŞAHAP) VE EK SERTLEŞMESİ
# ==============================================================================

VOICELESS_CONSONANTS = set("pçtkfhşs")  # Fıstıkçı Şahap

# Sert ünsüzle biten kelimelerden sonra gelen eklerin sertleşmesi
CONSONANT_ASSIMILATION_SUFFIXES = [
    (r'([pçtkfhşs])(da|de)\b', r'\1te'),     # da/de -> ta/te (ünlü uyumu aşağıda rafine edilir)
    (r'([pçtkfhşs])(dan|den)\b', r'\1ten'),  # dan/den -> tan/ten
    (r'([pçtkfhşs])(cı|ci|cu|cü)\b', r'\1çi'), # cı/ci -> çı/çi
]

# Konuşma dilindeki daralmaların standart yazı diline çevrilmesi
COLLOQUIAL_REDUCTIONS = {
    # Gelecek zaman (-ecek / -acak) daralmaları
    "yapıcak": "yapacak", "yapıcam": "yapacağım", "yapıcaz": "yapacağız",
    "edicem": "edeceğim", "edicez": "edeceğiz", "edicek": "edecek",
    "gidicem": "gideceğim", "gidicez": "gideceğiz", "gidicek": "gidecek",
    "gelicem": "geleceğim", "gelicez": "geleceğiz", "gelicek": "gelecek",
    "alıcam": "alacağım", "alıcaz": "alacağız", "alıcak": "alacak",
    "vericem": "vereceğim", "vericez": "vereceğiz", "vericek": "verecek",
    "bakıcam": "bakacağım", "bakıcaz": "bakacağız", "bakıcak": "bakacak",
    "olucam": "olacağım", "olucaz": "olacağız", "olucak": "olacak",
    "gelmiycem": "gelmeyeceğim", "gelmiycek": "gelmeyecek", "gelmiycez": "gelmeyeceğiz",
    "yapmıycak": "yapmayacak", "yapmıycaz": "yapmayacağız", "yapmıycam": "yapmayacağım",
    "etmiycem": "etmeyeceğim", "etmiycek": "etmeyecek", "etmiycez": "etmeyeceğiz",
    
    # Şimdiki zaman (-iyor) konuşma dili son harf düşmesi ve şahıs daralmaları
    "biliyo": "biliyor", "geliyo": "geliyor", "gidiyo": "gidiyor",
    "bakıyo": "bakıyor", "yapıyo": "yapıyor", "oluyo": "oluyor",
    "seviyo": "seviyor", "diyo": "diyor", "istiyo": "istiyor",
    "bilmiyo": "bilmiyor", "gelmiyo": "gelmiyor", "yapmıyo": "yapmıyor",
    "etmiyo": "etmiyor", "istemiyo": "istemiyor", "görmüyo": "görmüyor",
    "duymuyo": "duymuyor", "almıyo": "almıyor", "vermiyo": "vermiyor",
    "yapıyom": "yapıyorum", "yapıyon": "yapıyorsun", "yapıyoz": "yapıyoruz",
    "geliyom": "geliyorum", "geliyon": "geliyorsun", "geliyoz": "geliyoruz",
    "gidiyom": "gidiyorum", "gidiyon": "gidiyorsun", "gidiyoz": "gidiyoruz",
    "biliyom": "biliyorum", "biliyon": "biliyorsun", "biliyoz": "biliyoruz",
    "bakıyom": "bakıyorum", "bakıyon": "bakıyorsun", "bakıyoz": "bakıyoruz",
    "istiyom": "istiyorum", "istiyon": "istiyorsun", "istiyoz": "istiyoruz",
    "diyom": "diyorum", "diyon": "diyorsun", "diyoz": "diyoruz",
    "oluyom": "oluyorum", "oluyon": "oluyorsun", "oluyoz": "oluyoruz",
    "seviyom": "seviyorum", "seviyon": "seviyorsun", "seviyoz": "seviyoruz",
    "bilmiyom": "bilmiyorum", "gelmiyom": "gelmiyorum", "yapmıyom": "yapmıyorum",

    # Sık rastlanan ünsüz benzeşmesi hataları
    "kitapcı": "kitapçı", "kitapda": "kitapta", "kitapdan": "kitaptan",
    "ağaçda": "ağaçta", "ağaçdan": "ağaçtan", "sokakda": "sokakta",
    "sokakdan": "sokaktan", "sınıfda": "sınıfta", "sınıfdan": "sınıftan",
    "yavaşca": "yavaşça", "türkce": "Türkçe", "türkcede": "Türkçede",
    "aşcı": "aşçı", "aşcılık": "aşçılık", "çiftci": "çiftçi",
    "simitci": "simitçi", "balıkcı": "balıkçı", "işci": "işçi",
    "saatci": "saatçi", "sabahdan": "sabahtan", "yapdı": "yaptı",
    "gitdi": "gitti", "bakdı": "baktı", "açdı": "açtı", "içdi": "içti"
}

# ==============================================================================
# 3. SAYI, SAAT VE TARİH İMLASI
# ==============================================================================

# Saat başlarında dakikaya değil saate göre ek kuralı (14:00'da -> 14.00'te)
HOUR_ZERO_SUFFIX = {
    0: "da",   # 00.00'da
    1: "de",   # 01.00'de
    2: "de",   # 02.00'de
    3: "te",   # 03.00'te
    4: "te",   # 04.00'te
    5: "te",   # 05.00'te
    6: "da",   # 06.00'da
    7: "de",   # 07.00'de
    8: "de",   # 08.00'de
    9: "da",   # 09.00'da
    10: "da",  # 10.00'da
    11: "de",  # 11.00'de
    12: "de",  # 12.00'de
    13: "te",  # 13.00'te
    14: "te",  # 14.00'te
    15: "te",  # 15.00'te
    16: "da",  # 16.00'da
    17: "de",  # 17.00'de
    18: "de",  # 18.00'de
    19: "da",  # 19.00'da
    20: "de",  # 20.00'de
    21: "de",  # 21.00'de
    22: "de",  # 22.00'de
    23: "te"   # 23.00'te
}

# Tekil rakamların son basamak okunuşuna göre ekleri
DIGIT_LOCATIVE_SUFFIX = {
    '0': "da",  # sıfır-da
    '1': "de",  # bir-de
    '2': "de",  # iki-de
    '3': "te",  # üç-te
    '4': "te",  # dört-te
    '5': "te",  # beş-te
    '6': "da",  # altı-da
    '7': "de",  # yedi-de
    '8': "de",  # sekiz-de
    '9': "da"   # dokuz-da
}


def fix_proper_nouns_and_acronyms(text: str) -> str:
    """
    Özel isimlere ve kısaltmalara gelen ekleri kesme işaretiyle ayırır ve büyük harf kuralını uygular.
    Örn: 'ankarada' -> 'Ankara\'da', 'ahmete' -> 'Ahmet\'e', 'TDKya' -> 'TDK\'ye'.
    """
    words = text.split(" ")
    result_words = []

    # İyelik ve durum ekleri
    case_suffixes = [
        ("da", "de", "ta", "te"),
        ("dan", "den", "tan", "ten"),
        ("a", "e", "ya", "ye"),
        ("ı", "i", "u", "ü", "yı", "yi", "yu", "yü"),
        ("ın", "in", "un", "ün", "nın", "nin", "nun", "nün"),
    ]

    all_suffixes_flat = set()
    for grp in case_suffixes:
        all_suffixes_flat.update(grp)

    for word in words:
        clean_word = word.strip(".,!?:;\"'()[]{}")
        punc_suffix = word[len(clean_word):] if len(clean_word) < len(word) else ""
        lower_clean = turkish_lower(clean_word)

        # 0. Dil isimleri kontrolü (TDK: Dil adları büyük harfle başlar ve yapım eki olduğu için kesme işaretiyle ayrılmaz)
        lang_handled = False
        for lang_key, lang_proper in LANGUAGE_NORMALIZATION_MAP.items():
            if lower_clean == lang_key:
                result_words.append(lang_proper + punc_suffix)
                lang_handled = True
                break
            elif lower_clean.startswith(lang_key) and lower_clean[len(lang_key):] in all_suffixes_flat:
                suffix = lower_clean[len(lang_key):]
                result_words.append(f"{lang_proper}{suffix}{punc_suffix}")
                lang_handled = True
                break
        if lang_handled:
            continue

        # 1. Kısaltma kontrolü (Örn: TDK'ya -> TDK'ye veya TDKya -> TDK'ye)
        handled = False
        for wrong_acr, right_acr in ACRONYM_SUFFIX_CORRECTIONS.items():
            if clean_word.upper() == wrong_acr.replace("'", "").upper() or clean_word == wrong_acr:
                result_words.append(right_acr + punc_suffix)
                handled = True
                break
        if handled:
            continue

        # 1.B: Tek başına teknik kısaltma (örn: pc -> PC, gpu -> GPU, tr -> TR)
        if lower_clean in TECH_ACRONYMS:
            result_words.append(lower_clean.upper() + punc_suffix)
            continue

        # 1.C: Büyük ya da küçük harfle yazılmış kısaltmaya ek gelmişse (örn: pcden -> PC'den, MEBe -> MEB'e, trde -> TR'de)
        if "'" in clean_word:
            result_words.append(word)
            continue

        acr_handled = False
        for acr in KNOWN_ACRONYMS:
            if lower_clean.startswith(acr) and len(lower_clean) > len(acr):
                # 'ab' ve 'ai' gibi 2 harfli kısaltmalar küçük yazıldığında ('abi', 'ait', 'aile') özel kısaltma sayılmaz
                if acr in {"ab", "ai"} and not clean_word[:2].isupper():
                    continue
                suffix = lower_clean[len(acr):]
                # 2 harfli kısaltmalarda tek harfli ünlü eki ('abi' -> 'ab'+'i') ayrılmaz
                if len(acr) <= 2 and len(suffix) < 2:
                    continue
                if suffix in all_suffixes_flat:
                    stem = acr.upper()
                    # Son harfe ve ünlü uyumuna göre ek düzeltmesi
                    if stem.endswith("K") and suffix in {"a", "ya", "da"}:
                        suffix = "ye" if suffix in {"a", "ya"} else "de"
                    elif stem in {"PC", "DC", "TR", "AI", "CPU", "GPU"} and suffix in {"da", "dan"}:
                        suffix = "de" if suffix == "da" else "den"
                    result_words.append(f"{stem}'{suffix}{punc_suffix}")
                    acr_handled = True
                    break
        if acr_handled:
            continue

        # 2. Özel isim tespiti (Örn: ankarada, ahmete, mustafanın)
        # Cins isimlerle eş sesli olan özel isimler ('can', 'deniz', 'yağmur', 'ordu', 'ağrı' vb.) küçük harfle yazılmışsa cins isimdir
        common_noun_homonyms = {
            "can", "deniz", "yağmur", "gizem", "ağrı", "ordu", "aydın", "muş", "van", "batman"
        }
        for stem in ALL_PROPER_STEMS:
            if lower_clean.startswith(stem) and len(lower_clean) > len(stem):
                if stem in common_noun_homonyms and not (clean_word and clean_word[0].isupper()):
                    continue
                suffix = lower_clean[len(stem):]
                if suffix in all_suffixes_flat:
                    # Doğru büyük harfli kök
                    cap_stem = turkish_capitalize(stem)
                    result_words.append(f"{cap_stem}'{suffix}{punc_suffix}")
                    handled = True
                    break

        if not handled:
            result_words.append(word)

    return " ".join(result_words)


def fix_consonant_and_colloquial(text: str) -> str:
    """
    Ünsüz benzeşmesi (Fıstıkçı Şahap) ve konuşma dili daralmalarını düzeltir.
    Örn: 'kitapcı' -> 'kitapçı', 'yapıcak' -> 'yapacak', 'biliyo' -> 'biliyor'.
    """
    words = text.split(" ")
    result_words = []

    for word in words:
        clean_word = word.strip(".,!?:;\"'()[]{}")
        punc_suffix = word[len(clean_word):] if len(clean_word) < len(word) else ""
        lower_clean = turkish_lower(clean_word)

        # Doğrudan eşleşme kontrolü
        if lower_clean in COLLOQUIAL_REDUCTIONS:
            replacement = COLLOQUIAL_REDUCTIONS[lower_clean]
            # İlk harf büyükse koru
            if clean_word and clean_word[0].isupper():
                replacement = turkish_capitalize(replacement)
            result_words.append(replacement + punc_suffix)
            continue

        # Fıstıkçı Şahap: yalnızca kelime sonundaki ek sınırlarında (-da/-de, -dan/-den, -dı/-di, -cı/-ci) uygula
        # ('takdir', 'tasdik', 'mahcup', 'mescit', 'akdeniz' gibi kelime köklerini bozmaz)
        consonant_fixed = lower_clean
        consonant_fixed = re.sub(
            r'^([a-zçğıöşü]{2,}[pçtkfhşs])c(ı|i|u|ü|ılık|ilik|uluk|ülük)$',
            r'\1ç\2',
            consonant_fixed,
        )
        consonant_fixed = re.sub(
            r'^([a-zçğıöşü]{2,}[pçtkfhşs])d(a|e|an|en|ı|i|u|ü|ım|im|um|üm|ın|in|un|ün|ık|ik|uk|ük)$',
            r'\1t\2',
            consonant_fixed,
        )
        if consonant_fixed != lower_clean:
            if clean_word and clean_word[0].isupper():
                consonant_fixed = turkish_capitalize(consonant_fixed)
            result_words.append(consonant_fixed + punc_suffix)
            continue

        result_words.append(word)

    return " ".join(result_words)


def fix_time_and_number_grammar(text: str) -> str:
    """
    TDK Saat, Sayı ve Tarih kurallarını uygular:
    - 14:00 da / 14:00'da -> 14.00'te
    - 14:30 da / 14:30'da -> 14.30'da
    - 14:30 -> 14.30 (iki nokta yerine tek nokta)
    - 2026 de / 2026'de -> 2026'da
    - 1923 de / 1923'de -> 1923'te
    """
    # 1. Saat formatı ve ek düzeltmesi (Örn: 14:00'da, 14:00 da, 14:30 da, 14.00 da)
    def hour_replacer(match):
        hour = int(match.group(1))
        minute = int(match.group(2))
        suffix = match.group(3) if match.lastindex >= 3 and match.group(3) else ""

        # TDK kuralı: dijital saat arasına tek nokta konur
        time_str = f"{hour:02d}.{minute:02d}"

        if not suffix:
            return time_str

        # Sıfırlı saatlerde ek saate göre gelir: 14.00'te (on dörtte)
        if minute == 0 and hour in HOUR_ZERO_SUFFIX:
            correct_suffix = HOUR_ZERO_SUFFIX[hour]
        else:
            # Dakikanın son rakamına göre ek
            last_digit = str(minute)[-1]
            correct_suffix = DIGIT_LOCATIVE_SUFFIX.get(last_digit, "de")

        return f"{time_str}'{correct_suffix}"

    # Regex: 14:00'da | 14:00 da | 14.00 da | 14:30'de vb.
    pattern_time = r'\b([0-1]?[0-9]|2[0-3])[:.]([0-5][0-9])(?:\s*[\'’\s]?\s*(da|de|ta|te))\b'
    text = re.sub(pattern_time, hour_replacer, text, flags=re.IGNORECASE)

    # İki noktalı tekil saatleri tek noktaya çevir: 14:30 -> 14.30
    text = re.sub(r'\b([0-1]?[0-9]|2[0-3]):([0-5][0-9])\b', r'\1.\2', text)

    # 2. Yıl / Sayı ek sertleşmesi ve uyumu (Örn: 2026 de -> 2026'da, 1923 de -> 1923'te)
    def number_replacer(match):
        num_str = match.group(1)
        last_digit = num_str[-1]

        # Özel yıl sonları (Örn: 70 -> yetmişte, 80 -> seksende)
        if len(num_str) >= 2 and num_str.endswith("70"):
            correct_suffix = "te"
        elif len(num_str) >= 2 and num_str.endswith("80"):
            correct_suffix = "de"
        elif len(num_str) >= 2 and num_str.endswith("90"):
            correct_suffix = "da"
        elif len(num_str) >= 2 and num_str.endswith("00"):
            correct_suffix = "de"  # yüz-de / bin-de
        else:
            correct_suffix = DIGIT_LOCATIVE_SUFFIX.get(last_digit, "de")

        return f"{num_str}'{correct_suffix}"

    pattern_num = r'(?<!\.)\b(\d{1,4})\s*[\'’\s]?\s*(da|de|ta|te)\b'
    text = re.sub(pattern_num, number_replacer, text, flags=re.IGNORECASE)

    return text


# ==============================================================================
# 4. ÜNLÜ DÜŞMESİ, ÜNSÜZ YUMUŞAMASI VE BİTİŞİK BİRLEŞİK FİİLLER (TDK)
# ==============================================================================

# Ünlü Düşmesi (Ses Düşmesi) Haritası
VOWEL_ELISION_MAP = {
    # Ağız
    "ağızı": "ağzı", "ağızım": "ağzım", "ağızın": "ağzın", "ağıza": "ağza", "ağızda": "ağızda",
    # Akıl
    "akılı": "aklı", "akılım": "aklım", "akılın": "aklın", "akıla": "akla",
    # Fikir
    "fikiri": "fikri", "fikirim": "fikrim", "fikirin": "fikrin", "fikire": "fikre",
    # Şehir
    "şehiri": "şehri", "şehire": "şehre", "şehirim": "şehrim", "şehirin": "şehrin",
    # Ömür
    "ömürü": "ömrü", "ömürüm": "ömrüm", "ömürün": "ömrün", "ömüre": "ömre",
    # Burun
    "burunu": "burnu", "burunum": "burnum", "burunun": "burnun", "buruna": "burna",
    # Alın
    "alını": "alnı", "alınım": "alnım", "alının": "alnının", "alına": "alna",
    # Boyun
    "boyunu": "boynu", "boyunum": "boynum", "boyunun": "boynun", "boyuna": "boynuna",
    # Omuz
    "omuzu": "omzu", "omuzum": "omzum", "omuzun": "omzun", "omuza": "omza",
    # Göğüs
    "göğüsü": "göğsü", "göğüsüm": "göğsüm", "göğüsün": "göğsün", "göğüse": "göğse",
    # Karın
    "karını": "karnı", "karınım": "karnım", "karının": "karnın", "karına": "karna",
    # Gönül
    "gönülü": "gönlü", "gönülüm": "gönlüm", "gönülün": "gönlün", "gönüle": "gönle",
    # İsim
    "isimi": "ismi", "isimim": "ismim", "isimin": "ismin", "isime": "isme",
    # Resim
    "resimi": "resmi", "resimim": "resmim", "resimin": "resmin", "resime": "resme",
    # Vakit
    "vakiti": "vakti", "vakitimiz": "vaktimiz", "vakite": "vakte",
    # Sabır
    "sabırı": "sabrı", "sabırım": "sabrım", "sabıra": "sabra",
    # Kayıp
    "kayıpı": "kaybı", "kayıpa": "kayba",
    # Ne için / Ne asıl birleşmesi
    "ne için": "niçin", "ne asıl": "nasıl"
}

# Ünsüz Yumuşaması Haritası (p, ç, t, k -> b, c, d, ğ/g)
CONSONANT_SOFTENING_MAP = {
    # Kitap
    "kitapı": "kitabı", "kitapım": "kitabım", "kitapın": "kitabın", "kitapa": "kitaba",
    # Çiçek
    "çiçeki": "çiçeği", "çiçeke": "çiçeğe", "çiçekim": "çiçeğim", "çiçekin": "çiçeğin",
    # Çocuk
    "çocuku": "çocuğu", "çocuka": "çocuğa", "çocukun": "çocuğun", "çocukumuz": "çocuğumuz",
    # Sokak
    "sokakı": "sokağı", "sokaka": "sokağa",
    # Ağaç
    "ağaçı": "ağacı", "ağaça": "ağaca", "ağaçın": "ağacın",
    # İlaç
    "ilaçı": "ilacı", "ilaça": "ilaca", "ilaçım": "ilacım", "ilaçın": "ilacın",
    # Ayak
    "ayakı": "ayağı", "ayaka": "ayağa", "ayakım": "ayağım", "ayakın": "ayağın",
    # Kalp
    "kalpi": "kalbi", "kalpim": "kalbim", "kalpin": "kalbin", "kalpe": "kalbe",
    # Dert
    "derti": "derdi", "dertim": "derdim", "derte": "derde", "dertin": "derdin",
    # Renk
    "renki": "rengi", "renke": "renge", "renkim": "rengim",
    # Mutfak
    "mutfakı": "mutfağı", "mutfaka": "mutfağa",
    # Ekmek
    "ekmeki": "ekmeği", "ekmeke": "ekmeğe",
    # Bebek
    "bebeki": "bebeği", "bebeke": "bebeğe", "bebekim": "bebeğim", "bebekin": "bebeğin"
}

# Bitişik Yazılan Birleşik Fiiller (Ses düşmesi veya türemesi olanlar bitişik yazılır)
COMPOUND_VERBS_MAP = {
    # Kayıp olmak / etmek
    "kayıp olmak": "kaybolmak", "kayıp oldu": "kayboldu", "kayıp olmuş": "kaybolmuş",
    "kayıp olur": "kaybolur", "kayıp oluyor": "kayboluyor", "kayıp ol": "kaybol",
    "kayıp etmek": "kaybetmek", "kayıp etti": "kaybetti", "kayıp etmiş": "kaybetmiş",
    "kayıp eder": "kaybeder", "kayıp ediyor": "kaybediyor", "kayıp et": "kaybet",
    # His etmek
    "his etmek": "hissetmek", "his etti": "hissetti", "his etmiş": "hissetmiş",
    "his eder": "hisseder", "his ediyor": "hissediyor", "his et": "hisset",
    "his ediyorum": "hissediyorum", "his ediyorsun": "hissediyorsun", "his ediyoruz": "hissediyoruz",
    # Af etmek
    "af etmek": "affetmek", "af etti": "affetti", "af etmiş": "affetmiş",
    "af eder": "affeder", "af ediyor": "affediyor", "af et": "affet",
    "af edersiniz": "affedersiniz", "af edersin": "affedersin",
    # Sabır etmek
    "sabır etmek": "sabretmek", "sabır etti": "sabretti", "sabır etmiş": "sabretmiş",
    "sabır eder": "sabreder", "sabır ediyor": "sabrediyor", "sabır et": "sabret",
    # Şükür etmek
    "şükür etmek": "şükretmek", "şükür etti": "şükretti", "şükür etmiş": "şükretmiş",
    "şükür eder": "şükreder", "şükür ediyor": "şükrediyor", "şükür et": "şükret",
    # Emir etmek
    "emir etmek": "emretmek", "emir etti": "emretti", "emir etmiş": "emretmiş",
    "emir eder": "emreder", "emir ediyor": "emrediyor", "emir et": "emret",
    # Hapis olmak / etmek
    "hapis olmak": "hapsolmak", "hapis oldu": "hapsoldu",
    "hapis etmek": "hapsetmek", "hapis etti": "hapsetti",
    # Zan etmek
    "zan etmek": "zannetmek", "zan etti": "zannetti", "zan etmiş": "zannetmiş",
    "zan eder": "zanneder", "zan ediyor": "zannediyor", "zan ediyorum": "zannediyorum",
    # Hall olmak / etmek
    "hal olmak": "hallolmak", "hal oldu": "halloldu", "hal olur": "hallolur",
    "hal etmek": "halletmek", "hal etti": "halletti", "hal eder": "halleder", "hallet": "hallet",
    # Red etmek
    "red etmek": "reddetmek", "red etti": "reddetti", "red etmiş": "reddetmiş",
    "red eder": "reddeder", "red ediyor": "reddediyor",
    # Terk etmek / Park etmek / Fark etmek (Bunlar TDK gereği AYRI yazılır)
    "terketmek": "terk etmek", "terketti": "terk etti",
    "farketmek": "fark etmek", "farketti": "fark etti", "farketmez": "fark etmez",
    "parketmek": "park etmek", "parketti": "park etti",
    "arzetmek": "arz etmek", "arzederim": "arz ederim",
    "sağol": "sağ ol", "sağolun": "sağ olun", "hoşçakal": "hoşça kal", "hoşgeldiniz": "hoş geldiniz"
}

# Üleştirme sayıları rakamla değil yazıyla yazılır (TDK kuralı: 2'şer değil ikişer)
DISTRIBUTIVE_NUMERALS = {
    "1'er": "birer", "1'erli": "birerli",
    "2'şer": "ikişer", "2'şerli": "ikişerli",
    "3'er": "üçer", "3'erli": "üçerli",
    "4'er": "dörder", "4'erli": "dörderli",
    "5'er": "beşer", "5'erli": "beşerli",
    "6'şar": "altışar", "6'şarlı": "altışarlı",
    "7'şer": "yedişer", "7'şerli": "yedişerli",
    "8'er": "sekizer", "8'erli": "sekizerli",
    "9'ar": "dokuzar", "9'arlı": "dokuzarlı",
    "10'ar": "onar", "10'arlı": "onarlı",
    "20'şer": "yirmişer", "50'şer": "ellişer", "100'er": "yüzer"
}


def fix_sound_changes_and_compounds(text: str) -> str:
    """
    Ünlü düşmesi, ünsüz yumuşaması ve bitişik/ayrı birleşik fiil kurallarını uygular.
    """
    # 1. Çok kelimeli birleşik fiiller ve kalıplar (Örn: 'kayıp oldu' -> 'kayboldu', 'his ediyorum' -> 'hissediyorum')
    for wrong_phr, right_phr in COMPOUND_VERBS_MAP.items():
        # Kelime sınırlarına duyarlı regex değişimi
        pattern = rf'(?<!\w){re.escape(wrong_phr)}(?!\w)'
        text = re.sub(pattern, right_phr, text, flags=re.IGNORECASE)

    # 2. Üleştirme sayıları (2'şer -> ikişer, 5'er -> beşer)
    for wrong_num, right_num in DISTRIBUTIVE_NUMERALS.items():
        pattern = rf'(?<!\w){re.escape(wrong_num)}(?!\w)'
        text = re.sub(pattern, right_num, text, flags=re.IGNORECASE)

    # 3. Tek kelimelik ses olayları (ünlü düşmesi & ünsüz yumuşaması)
    words = text.split(" ")
    result_words = []

    for word in words:
        clean_word = word.strip(".,!?:;\"'()[]{}")
        punc_prefix = word[:len(word) - len(word.lstrip(".,!?:;\"'()[]{}"))]
        punc_suffix = word[len(punc_prefix) + len(clean_word):]
        lower_clean = turkish_lower(clean_word)

        replacement = None
        # Ünlü düşmesi kontrolü
        if lower_clean in VOWEL_ELISION_MAP:
            replacement = VOWEL_ELISION_MAP[lower_clean]
        # Ünsüz yumuşaması kontrolü
        elif lower_clean in CONSONANT_SOFTENING_MAP:
            replacement = CONSONANT_SOFTENING_MAP[lower_clean]

        if replacement:
            if clean_word and clean_word[0].isupper():
                replacement = turkish_capitalize(replacement)
            result_words.append(f"{punc_prefix}{replacement}{punc_suffix}")
        else:
            result_words.append(word)

    return " ".join(result_words)


def fix_typography_and_spacing(text: str) -> str:
    """
    Tipografi, noktalama ve boşluk kurallarını TDK standardına göre temizler:
    - Noktalama işaretlerinden önceki gereksiz boşlukları temizler ('merhaba , dünya' -> 'merhaba, dünya')
    - Emojileri ve gülen yüzleri (':)', ':D', ';)') bozmaz
    - Yüzde işaretinin sayıdan önce ve boşluksuz yazılması ('% 50' / '50 %' -> '%50')
    """
    # Noktalama öncesi boşluk temizliği:
    # Yalnızca virgül, noktalı virgül, soru işareti, ünlem ve ardında boşluk/son gelen noktalar
    # Gülen yüzlerdeki ':)', ':D', ';)' ifadelerini bozmamak için iki nokta (:) hariç tutulur veya ardı kontrol edilir
    text = re.sub(r'\s+([,;?!…])', r'\1', text)
    # Nokta öncesi boşluk (ardında boşluk veya satır sonu varsa)
    text = re.sub(r'\s+(\.)(?=\s|$)', r'\1', text)

    # TDK Türkçe Yüzde İmlası: Sayıdan önce ve bitişik yazılır (%20, %50)
    # Örn: "% 50" -> "%50"
    text = re.sub(r'%\s+(\d+)', r'%\1', text)
    # Örn: "50 %" veya "50%" -> "%50"
    text = re.sub(r'\b(\d+)\s*%', r'%\1', text)

    return text



def apply_tdk_rules(text: str) -> str:
    """
    Tüm TDK kurallarını (özel isimler, kısaltmalar, Fıstıkçı Şahap, konuşma dili,
    sayı/saat, ses olayları, birleşik fiiller ve tipografi) sırayla metne uygular.
    """
    # 1. Tipografi ve boşluk temizliği
    text = fix_typography_and_spacing(text)
    # 2. Saat ve sayı kuralları
    text = fix_time_and_number_grammar(text)
    # 3. Özel isimler ve kısaltmalarda kesme işareti
    text = fix_proper_nouns_and_acronyms(text)
    # 4. Ünsüz benzeşmesi ve konuşma dili daralmaları
    text = fix_consonant_and_colloquial(text)
    # 5. Ünlü düşmesi, ünsüz yumuşaması ve birleşik fiiller
    text = fix_sound_changes_and_compounds(text)
    return text
