"""
Yapay Zeka Destekli Türkçe Düzeltme Motoru (NVIDIA NIM & Yerel LLM Desteği).
NVIDIA API Catalog (build.nvidia.com) üzerinden ücretsiz sağlanan API anahtarı (nvapi-...)
ile Llama-3.3 70B, Mixtral veya Nemotron gibi devasa yapay zeka modellerini çağırır.
İnternet veya API anahtarı olmadığında sıfır maliyetli yerel çevrimdışı motora geri düşer.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Optional, Tuple

from src import settings_manager

DEFAULT_NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"

AVAILABLE_MODELS = [
    ("meta/llama-3.3-70b-instruct", "Llama 3.3 70B (Önerilen - En Yüksek İmla ve Anlam Kalitesi)"),
    ("meta/llama-3.1-8b-instruct", "Llama 3.1 8B (Ultra Hızlı ve Hafif)"),
    ("mistralai/mixtral-8x7b-instruct-v0.1", "Mixtral 8x7B (Çok Dilli Güçlü Model)"),
    ("nvidia/llama-3.1-nemotron-70b-instruct", "Nemotron 70B (NVIDIA İnce Ayarlı)"),
    ("deepseek-ai/deepseek-r1", "DeepSeek R1 (Derin Muhakeme & Düzeltme)"),
]

SYSTEM_PROMPT = (
    "Sen profesyonel bir Türkçe dilbilgisi, imla ve anlam editörüsün. "
    "Sana verilen Türkçe metindeki yazım yanlışlarını, bitişik/ayrık yazılan bağlaçları (de/da, ki), "
    "eksik harfleri, devrik cümleleri ve noktalama işaretlerini TDK kurallarına göre düzelt. "
    "Metnin orijinal anlamını ve üslubunu kesinlikle bozma. "
    "Cevap olarak YALNIZCA düzeltilmiş Türkçe metni ver. "
    "Asla açıklama, selamlama, önsöz, tırnak işareti veya ek not yazma."
)


def get_nvidia_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """NVIDIA API anahtarını öncelik sırasına göre bulur."""
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    env_key = os.environ.get("NVIDIA_API_KEY") or os.environ.get("NV_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()

    try:
        settings = settings_manager.load_settings()
        cfg_key = settings.get("nvidia_api_key", "").strip()
        if cfg_key:
            return cfg_key
    except Exception:
        pass

    return None


def call_nvidia_nim(
    text: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout: float = 8.0,
    base_url: str = DEFAULT_NVIDIA_URL,
) -> Optional[str]:
    """
    NVIDIA NIM API kullanarak metni düzeltir.
    Standart kütüphane (urllib) kullanır, harici paket bağımlılığı gerektirmez.
    """
    key = get_nvidia_api_key(api_key)
    if not key:
        return None

    if not model:
        try:
            settings = settings_manager.load_settings()
            model = settings.get("ai_model", DEFAULT_MODEL)
        except Exception:
            model = DEFAULT_MODEL

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "top_p": 0.7,
        "max_tokens": 1024,
        "stream": False,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Turkce-Otoduzeltici/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                body = response.read().decode("utf-8")
                res_json = json.loads(body)
                content = res_json["choices"][0]["message"]["content"].strip()
                # Olası tırnak işaretlerini veya markdown kod bloklarını temizle
                if content.startswith("```") and content.endswith("```"):
                    content = content.strip("`").strip()
                    if content.startswith("plaintext") or content.startswith("markdown"):
                        content = content.split("\n", 1)[-1]
                content = content.strip('"\'`')
                return content
    except Exception as exc:
        print(f"[!] NVIDIA API Çağrı Hatası: {exc}", file=sys.stderr)
        return None

    return None


def test_nvidia_connection(
    api_key: str,
    model: Optional[str] = None,
    timeout: float = 6.0,
) -> Tuple[bool, str, float]:
    """
    Girilen NVIDIA API anahtarını ve bağlantısını test eder.
    (başarılı_mı, mesaj, yanıt_süresi_ms) döner.
    """
    key = api_key.strip() if api_key else ""
    if not key:
        return False, "API anahtarı boş bırakılamaz.", 0.0

    target_model = model or DEFAULT_MODEL
    t0 = time.time()
    res = call_nvidia_nim("Merhaba dünya nasılsın", api_key=key, model=target_model, timeout=timeout)
    latency_ms = round((time.time() - t0) * 1000, 1)

    if res:
        return True, f"Bağlantı başarılı! Model: {target_model}", latency_ms
    else:
        return False, "Bağlantı kurulamadı. API anahtarınızı veya internet bağlantınızı kontrol edin.", latency_ms


def fix_with_ai(
    raw_text: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> Optional[str]:
    """
    Yapay zeka ile metni düzeltir.
    Önce NVIDIA NIM API'yi dener; anahtar yoksa veya başarısız olursa yerel GGUF'a bakar.
    """
    if not raw_text or not raw_text.strip():
        return raw_text

    # 1. NVIDIA NIM API Denemesi
    res = call_nvidia_nim(raw_text, api_key=api_key, model=model)
    if res:
        return res

    # 2. Yerel GGUF Modeli Denemesi (İsteğe bağlı çevrimdışı llama_cpp)
    local_model_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "models",
        "qwen2.5-0.5b-instruct-q4_k_m.gguf",
    )
    if os.path.exists(local_model_path):
        try:
            from llama_cpp import Llama

            llm = Llama(
                model_path=local_model_path,
                n_ctx=512,
                n_gpu_layers=35,
                verbose=False,
            )
            response = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Düzelt: {raw_text}"},
                ],
                max_tokens=256,
                temperature=0.1,
            )
            del llm
            content = response["choices"][0]["message"]["content"].strip().strip('"\'`')
            return content
        except Exception:
            pass

    return None
