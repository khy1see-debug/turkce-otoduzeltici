"""
Türkçe Chat Kısaltmaları ve Günlük Konuşma Genişletici (Slang Expander).
Örnek:
  slm -> selam
  knk -> kanka
  nbr -> naber
  tsk / tskler -> teşekkürler
  eyw / eyv -> eyvallah
  hg / hb -> hoş geldin / hoş bulduk
  gelcenmi -> gelecek misin
"""

from typing import Optional

CHAT_SLANG_MAP = {
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
    "gelcenmi": "gelecek misin",
    "geliyonmu": "geliyor musun",
    "gidiyonmu": "gidiyor musun",
    "yapiyonmu": "yapıyor musun",
    "napion": "ne yapıyorsun",
    "napiyon": "ne yapıyorsun",
    "napıyosun": "ne yapıyorsun"
}

def expand_slang(token: str) -> Optional[str]:
    """Kısaltma veya chat argo kelimesini tam Türkçe karşılığına açar."""
    return CHAT_SLANG_MAP.get(token.lower())
