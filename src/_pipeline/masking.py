"""
Markdown kod bloklarını ve korunacak tanımlayıcıları (URL, e-posta, mention, hashtag)
koruma-altına almayı sağlar.

Korunan parçalar ``__CODE_BLOCK_<n>__`` şeklinde maskeleyip, işlem sonrasında
``restore_code_blocks`` ile geri yüklenir. Kod blokları asla imla/kural motoruna
verilmez.
"""

from __future__ import annotations

import re
from typing import List, Tuple

PROTECTED_TOKEN = re.compile(
    r"(?:https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.\w+|[@#][\wçğıöşüÇĞİÖŞÜ_]+|__CODE_BLOCK_\d+__)",
    re.IGNORECASE,
)

PROTECTED_EMOTICONS = {
    ":)", ":-)", ":(", ":-(", ":D", ":-D", ";)", ";-)", "<3", ":P", ":-P", ":3",
}


def extract_code_blocks(text: str) -> Tuple[str, List[str]]:
    """Markdown kod bloklarını ve inline kodları koruma-altına alır.

    ``(```...``` veya `...` blokları ``__CODE_BLOCK_0__`` gibi yer tutucu ile
    değiştirilir; orijinal bloklar sırayla ``blocks`` listesinde saklanır.
    """
    blocks: List[str] = []

    def repl(m: re.Match) -> str:
        idx = len(blocks)
        blocks.append(m.group(0))
        return f"__CODE_BLOCK_{idx}__"

    masked = re.sub(r"(```[\s\S]*?```|`[^`\n]+`)", repl, text)
    return masked, blocks


def restore_code_blocks(text: str, blocks: List[str]) -> str:
    """Koruma-altına alınan kod bloklarını orijinal haliyle geri yükler."""
    for idx, block in enumerate(blocks):
        text = text.replace(f"__CODE_BLOCK_{idx}__", block)
    return text
