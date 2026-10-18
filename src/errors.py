"""
Düzeltme motoru için türetilmiş özel istisnalar.

* ``CorrectionError``: motor genelinde hata taban sınıfı.
* ``PolicyError``: ağ/aı politica dışı bir işlem istendiğinde.
* ``NetworkError``: ağ erişimi gerektiren işlem başarısız olduğunda.
* ``AIError``: AI sağlayıcısından geçersiz / halüsinasyon yanıt geldiğinde.
"""

from __future__ import annotations


class CorrectionError(Exception):
    """Düzeltme motoru temel hata sınıfı."""


class PolicyError(CorrectionError):
    """Ağ / AI / çeviri politikası nedeniyle işlem engellendi."""


class NetworkError(CorrectionError):
    """Ağ erişimi gerektiren bir işlem başarısız oldu (bağlantı, zaman aşımı, DNS vb.)."""


class AIError(CorrectionError):
    """AI yanıtı geçersiz, boş veya halüsinasyon içerdiği tespit edildi."""
