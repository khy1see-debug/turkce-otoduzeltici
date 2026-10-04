"""
Ultra-Hafif Yerel AI Düzeltici Motoru (0-Token, Çevrimdışı, RTX Optimize).
Sadece istendiğinde yüklenir ve işlem bittiğinde VRAM'i tamamen serbest bırakır.
Noktalama, harf hataları, devrik cümleler ve bağlaçları mükemmel seviyede düzeltir.
"""

import os
import sys
from typing import Optional

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "qwen2.5-0.5b-instruct-q4_k_m.gguf")

def fix_with_ai(raw_text: str) -> Optional[str]:
    """
    Yerel GGUF modeli ile metni düzeltir.
    Ekran kartını boşta tutmaz; sadece işlem anında çağrılır ve çıkar.
    """
    if not os.path.exists(MODEL_PATH):
        return None

    try:
        from llama_cpp import Llama
    except ImportError:
        return None

    # Ultra hafif ve hızlı yükleme: n_gpu_layers=-1 (varsa GPU'ya atar), n_ctx=512 (küçük bağlam = sıfır RAM yükü)
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=512,
        n_gpu_layers=35,
        verbose=False
    )

    system_prompt = (
        "Sen uzman bir Türkçe editörüsün. Görevin kullanıcının yazdığı bozuk, bitişik veya imla/noktalama hatası "
        "içeren Türkçe metni düzeltmektir. Sadece ve sadece düzeltilmiş nihai Türkçe cümleyi yaz. "
        "Açıklama, selamlama veya başka hiçbir metin ekleme."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Düzelt: {raw_text}"}
    ]

    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=128,
        temperature=0.1
    )

    del llm  # Belleği hemen serbest bırak

    content = response["choices"][0]["message"]["content"].strip()
    # Tırnak işaretlerini veya ek boşlukları temizle
    content = content.strip('"\'`')
    return content
