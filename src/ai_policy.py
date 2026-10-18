"""
Ağ / AI / çeviri / web-fallback politikası.

Varsayılan davranış ``LOCAL_ONLY``dır: yerel düzeltme motoru hiçbir API
anahtarı ve ağ erişimine ihtiyaç duymamalı. İsteğe bağlı özellikler
``settings.json`` üzerindeki ``network_policy`` anahtarıyla açılır.
"""

from __future__ import annotations

from enum import Enum


class NetworkPolicy(Enum):
    LOCAL_ONLY = "local_only"
    AI_OPTIONAL = "ai_optional"
    TRANSLATION_OPTIONAL = "translation_optional"
    WEB_FALLBACK_OPTIONAL = "web_fallback_optional"


DEFAULT_POLICY = NetworkPolicy.LOCAL_ONLY


def policy_from_settings(settings: dict) -> NetworkPolicy:
    """Ayarlar sözlüğünden ``NetworkPolicy`` çözer; bilinmeyen değerde local-only döner."""
    raw = settings.get("network_policy", DEFAULT_POLICY.value)
    if isinstance(raw, NetworkPolicy):
        return raw
    try:
        return NetworkPolicy(raw)
    except (ValueError, TypeError):
        return DEFAULT_POLICY


def ai_allowed(policy: NetworkPolicy) -> bool:
    """AI düzeltme (Groq / Gemini / NVIDIA / yerel GGUF) izni."""
    return policy in (
        NetworkPolicy.AI_OPTIONAL,
        NetworkPolicy.WEB_FALLBACK_OPTIONAL,
    )


def translation_allowed(policy: NetworkPolicy) -> bool:
    """Çeviri izni (AI veya web tabanlı)."""
    return policy in (
        NetworkPolicy.TRANSLATION_OPTIONAL,
        NetworkPolicy.WEB_FALLBACK_OPTIONAL,
    )


def web_fallback_allowed(policy: NetworkPolicy) -> bool:
    """Sıfır maliyetli web fallback (Google Translate / Wikipedia) izni."""
    return policy == NetworkPolicy.WEB_FALLBACK_OPTIONAL
