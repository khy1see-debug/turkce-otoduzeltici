"""
Türkçe Chat Kısaltmaları ve Günlük Konuşma Genişletici (Slang Expander).
Örnek:
  fln / falan -> falan
  flnsal -> falansal
  vb -> ve benzeri
  vs -> ve benzeri
  slm -> selam
  knk -> kanka
  nbr -> naber
  tsk / tskler -> teşekkürler
  eyw / eyv -> eyvallah
"""

from typing import Optional

CHAT_SLANG_MAP = {
    # Günlük Konuşma Doldurma Kelimeleri (fln, falan, vb)
    "bune": "bu ne",
    "şune": "şu ne",
    "one": "o ne",
    "içerdeyim": "içerideyim",
    "icerdeyim": "içerideyim",
    "dışardayım": "dışarıdayım",
    "disardayim": "dışarıdayım",
    "yukardayım": "yukarıdayım",
    "aşağdayım": "aşağıdayım",
    "burdayım": "buradayım",
    "şurdayım": "şuradayım",
    "fln": "falan",
    "flan": "falan",
    "flnsal": "falansal",
    "falansal": "falansal",
    "vb": "ve benzeri",
    "vs": "ve benzeri",
    "v.b": "ve benzeri",
    "v.s": "ve benzeri",
    "filan": "falan",

    # Selamlaşma & Vedalaşma
    "slm": "selam",
    "mrb": "merhaba",
    "nbr": "naber",
    "knk": "kanka",
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
    "aynn": "aynen",
    "aynen": "aynen",
    "bb": "bay bay",
    "by": "bay bay",
    "bye": "bay bay",
    "tmm": "tamam",
    "tm": "tamam",
    "ok": "tamam",
    "oki": "tamam",
    "rica": "rica ederim",
    "ö.d": "önemli değil",
    "od": "önemli değil",
    "hyr": "hayır",
    "evt": "evet",
    "nys": "neyse",
    "snrm": "sanırım",
    "bence": "bence",

    # Fiil Kısaltmaları (gelcenmi, gidiyonmu vb.)
    "gelcenmi": "gelecek misin",
    "geliyonmu": "geliyor musun",
    "gidiyonmu": "gidiyor musun",
    "yapiyonmu": "yapıyor musun",
    "napion": "ne yapıyorsun",
    "napiyon": "ne yapıyorsun",
    "napıyosun": "ne yapıyorsun",
    "yazamiom": "yazamıyorum",
    "yapamiom": "yapamıyorum",
    "gidemiom": "gidemiyorum",
    "gelemiom": "gelemiyorum"
}

def expand_slang(token: str) -> Optional[str]:
    """Kısaltma veya chat argo kelimesini tam Türkçe karşılığına açar."""
    return CHAT_SLANG_MAP.get(token.lower())
