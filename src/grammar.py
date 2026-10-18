"""
Türkçe Dilbilgisi, Ek Ayrımı, Noktalama, Kod Koruması ve Kural Açıklamalı Akıllı Motor.

Gerçekleştirim ``src/_pipeline`` paketine taşınmış boru-hatlı aşamalardan oluşur.
Bu modül geriye dönük uyumluluk için ``fix_sentence`` ve ``analyze_sentence``
giriş noktalarını yeniden dışa aktarır.
"""

from __future__ import annotations

from src._pipeline.stages import (
    analyze_sentence,
    fix_sentence,
)

__all__ = ["analyze_sentence", "fix_sentence"]
