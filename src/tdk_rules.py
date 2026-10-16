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
    "pc", "gpu", "cpu", "ram", "ssd", "usb", "dc", "tr", "ai", "llm"
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
    "yavaşca": "yavaşça", "türkce": "türkçe", "türkcede": "türkçede",
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


def apply_tdk_rules(text: str) -> str:
    """
    Tüm TDK kurallarını (özel isimler, kısaltmalar, Fıstıkçı Şahap, konuşma dili, sayı/saat)
    sırayla metne uygular.
    """
    # 1. Saat ve sayı kuralları
    text = fix_time_and_number_grammar(text)
    # 2. Özel isimler ve kısaltmalarda kesme işareti
    text = fix_proper_nouns_and_acronyms(text)
    # 3. Ünsüz benzeşmesi ve konuşma dili daralmaları
    text = fix_consonant_and_colloquial(text)
    return text
