"""
Türkçe Temel Sözlük ve Frekans Tablosu (0-token, offline).
En sık kullanılan Türkçe kelimeler, soru ekleri ve fiil çekimleri.
"""

from collections import Counter
import math

# Temel ve sık kullanılan Türkçe kelimeler (frekans ağırlıklı)
BASE_TURKISH_WORDS = {
    # Zamirler & Bağlaçlar & Edatlar & Soru
    "sen": 15000, "ben": 16000, "o": 14000, "biz": 12000, "siz": 11000, "onlar": 9000,
    "de": 25000, "da": 26000, "mi": 20000, "mı": 21000, "mu": 12000, "mü": 11000,
    "ve": 35000, "ile": 18000, "ama": 15000, "fakat": 8000, "ancak": 9000, "çünkü": 11000,
    "için": 22000, "gibi": 17000, "kadar": 16000, "diye": 14000, "ise": 13000, "bu": 30000, "şu": 15000,
    "ne": 20000, "nasıl": 16000, "neden": 13000, "niçin": 8000, "nerede": 12000, "kim": 14000,
    "çok": 22000, "daha": 19000, "en": 18000, "var": 21000, "yok": 19000, "evet": 14000, "hayır": 12000,
    "iyi": 15000, "güzel": 14000, "kötü": 9000, "tamam": 13000, "peki": 10000, "olur": 12000,

    # Fiiller ve Çekimleri (özellikle kullanıcı senaryoları)
    "geliyorsun": 12000, "geliyorum": 13000, "geliyor": 14000, "geldin": 11000, "geldi": 12000, "gel": 10000,
    "gidiyorsun": 11000, "gidiyorum": 12000, "gidiyor": 13000, "gittin": 10000, "gitti": 11000, "git": 10000,
    "yapıyorsun": 12000, "yapıyorum": 13000, "yapıyor": 14000, "yaptın": 11000, "yaptı": 12000, "yap": 11000,
    "ediyorsun": 11000, "ediyorum": 12000, "ediyor": 13000, "ettin": 9000, "etti": 10000, "et": 10000,
    "biliyorsun": 11000, "biliyorum": 13000, "biliyor": 12000, "bildin": 8000, "bildi": 9000, "bil": 9000,
    "istiyorsun": 10000, "istiyorum": 12000, "istiyor": 13000, "istedin": 7000, "istedi": 8000,
    "seviyorsun": 9000, "seviyorum": 11000, "seviyor": 10000, "sevdin": 7000, "sevdi": 8000,
    "görüyorsun": 9000, "görüyorum": 10000, "görüyor": 11000, "gördün": 8000, "gördü": 9000,
    "anlıyorsun": 9000, "anlıyorum": 10000, "anlıyor": 10000, "anladın": 8000, "anladı": 8000,
    "okuyorsun": 8000, "okuyorum": 9000, "okuyor": 9000, "okudun": 7000, "okudu": 8000,
    "yazıyorsun": 9000, "yazıyorum": 10000, "yazıyor": 10000, "yazdın": 8000, "yazdı": 8000,

    # Zaman & Günlük Yaşam & İsimler
    "bugün": 14000, "yarın": 12000, "dün": 11000, "şimdi": 16000, "sonra": 14000, "önce": 13000,
    "zaman": 15000, "saat": 12000, "gün": 14000, "hafta": 10000, "ay": 11000, "yıl": 13000,
    "akşam": 11000, "sabah": 11000, "öğle": 8000, "gece": 10000,
    "ev": 13000, "iş": 14000, "okul": 11000, "yol": 11000, "araba": 9000, "kitap": 10000,
    "merhaba": 12000, "selam": 11000, "nasılsın": 10000, "iyiyim": 10000, "teşekkürler": 9000, "sağol": 8000,
    "görüşürüz": 9000, "hoşça": 8000, "kal": 8000,
    "bir": 38000, "iki": 14000, "üç": 12000, "dört": 9000, "beş": 9000, "on": 11000,
    "her": 17000, "şey": 23000, "herkes": 12000, "hiç": 14000, "kimse": 11000, "biri": 12000
}

TOTAL_WORDS = sum(BASE_TURKISH_WORDS.values())

def get_word_prob(word: str) -> float:
    """Kelimenin log-olasılığını döner (unseen smoothing ile)."""
    count = BASE_TURKISH_WORDS.get(word.lower(), 0)
    if count > 0:
        return math.log(count / TOTAL_WORDS)
    # Bilinmeyen kelimeler için uzunluğa göre ceza (penalty)
    return math.log(10 / (TOTAL_WORDS * (10 ** len(word))))
