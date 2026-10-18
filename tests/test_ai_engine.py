"""
Unit tests for NVIDIA AI engine and LLM fallback logic.
"""

import pytest
from unittest.mock import MagicMock, patch
from src import ai_engine


def test_get_nvidia_api_key_explicit():
    assert ai_engine.get_nvidia_api_key("nvapi-test123") == "nvapi-test123"


def test_get_nvidia_api_key_env(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-env-key")
    assert ai_engine.get_nvidia_api_key() == "nvapi-env-key"


def test_test_nvidia_connection_empty():
    ok, msg, latency = ai_engine.test_nvidia_connection("")
    assert not ok
    assert "boş" in msg.lower()


def test_test_nvidia_connection_mocked():
    fake_response = MagicMock()
    fake_response.status = 200
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        ok, msg, latency = ai_engine.test_nvidia_connection("nvapi-valid", "meta/llama-3.2-11b-vision-instruct")
        assert ok
        assert "başarılı" in msg.lower()


def test_call_nvidia_nim_success():
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b'''{
        "choices": [
            {
                "message": {
                    "content": "Bug\xc3\xbcn hava \xc3\xa7ok g\xc3\xbczel."
                }
            }
        ]
    }'''

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        result = ai_engine.call_nvidia_nim(
            "bugun hava cok guzel",
            api_key="nvapi-dummy",
            model="meta/llama-3.3-70b-instruct"
        )
        assert result == "Bugün hava çok güzel."


def test_call_nvidia_nim_failure_fallback():
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        with pytest.raises(ai_engine.NetworkError):
            ai_engine.call_nvidia_nim("test", api_key="nvapi-dummy")


def test_fix_with_ai_fallback():
    # API anahtarı ve yerel model yokken, AI izni varsa fix_with_ai graceful None döner
    monkeypatch_settings = {
        "network_policy": "ai_optional",
        "ai_provider": "auto",
    }
    with patch.object(ai_engine.settings_manager, "load_settings", lambda: dict(monkeypatch_settings)):
        with patch.dict("os.environ", {}, clear=True):
            res = ai_engine.fix_with_ai("sendemigeliyorusn", api_key=None)
            assert res is None


def test_translate_with_ai_mocked(monkeypatch):
    monkeypatch.setattr(
        ai_engine.settings_manager,
        "load_settings",
        lambda: {"network_policy": "translation_optional", "ai_provider": "auto"},
    )
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b'''{
        "choices": [
            {
                "message": {
                    "content": "Good morning my friend."
                }
            }
        ]
    }'''

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        result = ai_engine.translate_with_ai(
            "gunaydin arkadasim",
            target_lang="en",
            api_key="nvapi-dummy"
        )
        assert result == "Good morning my friend."


def test_translate_with_ai_swedish_mocked(monkeypatch):
    monkeypatch.setattr(
        ai_engine.settings_manager,
        "load_settings",
        lambda: {"network_policy": "translation_optional", "ai_provider": "auto"},
    )
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b'''{
        "choices": [
            {
                "message": {
                    "content": "God morgon min v\xc3\xa4n."
                }
            }
        ]
    }'''

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        result = ai_engine.translate_with_ai(
            "gunaydin arkadasim",
            target_lang="sv",
            api_key="nvapi-dummy"
        )
        assert result == "God morgon min vän."



def test_translate_with_ai_fallback_no_key(monkeypatch):
    monkeypatch.setattr(
        ai_engine.settings_manager,
        "load_settings",
        lambda: {"network_policy": "translation_optional", "ai_provider": "auto"},
    )
    with patch.dict("os.environ", {}, clear=True):
        res = ai_engine.translate_with_ai("test", api_key=None)
        assert res is None


def test_get_gemini_api_key_explicit():
    assert ai_engine.get_gemini_api_key("AIzaSyTest123") == "AIzaSyTest123"


def test_get_gemini_api_key_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyEnvKey")
    assert ai_engine.get_gemini_api_key() == "AIzaSyEnvKey"


def test_test_gemini_connection_empty():
    ok, msg, latency = ai_engine.test_gemini_connection("")
    assert not ok
    assert "boş" in msg.lower()


def test_test_gemini_connection_mocked():
    fake_response = MagicMock()
    fake_response.status = 200
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        ok, msg, latency = ai_engine.test_gemini_connection("AIzaSyValid", "gemini-3.5-flash-lite")
        assert ok
        assert "başarılı" in msg.lower()


def test_call_gemini_api_success():
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b'''{
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "Yar\xc4\xb1n sabah bulu\xc5\x9fal\xc4\xb1m m\xc4\xb1?"
                        }
                    ]
                }
            }
        ]
    }'''

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        result = ai_engine.call_gemini_api(
            "yarin sabah bulusalimmi",
            api_key="AIzaSyDummy",
            model="gemini-3.5-flash-lite"
        )
        assert result == "Yarın sabah buluşalım mı?"


def test_call_gemini_api_failure():
    with patch("urllib.request.urlopen", side_effect=Exception("Timeout")):
        with pytest.raises(ai_engine.NetworkError):
            ai_engine.call_gemini_api("test", api_key="AIzaSyDummy")


def test_is_ai_hallucination_triggers():
    hallucinated_text = (
        "Alt + W tuş kombinasyonu ile Windows'un 'Gizli Komutlar' menüsüne erişmek mümkün. "
        "Bu menüde, 'Alt + W' tuş kombinasyonunu kullanarak 'Kanka' kelimesini arattığınızda, "
        "bu kelimeyi temizlemek için bir çeviriye ihtiyacınız olduğunu belirtiyor."
    )
    assert ai_engine.is_ai_hallucination("kanka", hallucinated_text, mode="correction") is True
    assert ai_engine.is_ai_hallucination("test", "Nasıl yardımcı olabilirim?", mode="correction") is True
    assert ai_engine.is_ai_hallucination("nasil bir ceviriyie ihtiyaciniz var", "What kind of translation do you need?", mode="translation") is False


def test_is_ai_hallucination_word_explosion():
    # 2-word input should not produce 30-word essay
    long_response = " ".join(["kelime"] * 35)
    assert ai_engine.is_ai_hallucination("merhaba dünya", long_response, mode="correction") is True


def test_is_ai_hallucination_paragraphs_and_bullets():
    single_line_in = "slm knk"
    bullet_response = "- Selam\n- Kanka\n- Naber"
    assert ai_engine.is_ai_hallucination(single_line_in, bullet_response, mode="correction") is True

    paragraph_response = "Selam kanka.\n\nİşte metniniz hazır.\n\nBaşka bir isteğiniz var mı?"
    assert ai_engine.is_ai_hallucination(single_line_in, paragraph_response, mode="correction") is True


def test_is_ai_hallucination_valid_correction():
    assert ai_engine.is_ai_hallucination("sendemigeliyorsun", "Sen de mi geliyorsun?", mode="correction") is False
    assert ai_engine.is_ai_hallucination("good morning", "Günaydın.", mode="translation") is False


def test_fix_with_ai_blocks_hallucination():
    hallucinated = "Alt + W tuş kombinasyonu ile Windows'un 'Gizli Komutlar' menüsüne erişmek mümkün."
    with patch.object(
        ai_engine.settings_manager, "load_settings", lambda: {"network_policy": "ai_optional", "ai_provider": "gemini"}
    ):
        with patch("src.ai_engine.call_gemini_api", return_value=hallucinated):
            with patch("src.ai_engine.get_gemini_api_key", return_value="fake_key"):
                res = ai_engine.fix_with_ai("kanka", provider="gemini")
                assert res is None


def test_translate_with_ai_blocks_hallucination(monkeypatch):
    monkeypatch.setattr(
        ai_engine.settings_manager,
        "load_settings",
        lambda: {"network_policy": "translation_optional", "ai_provider": "auto"},
    )
    conversational = "Nasıl yardımcı olabilirim? Hangi dilden hangi dile çeviri yapmak istiyorsunuz?"
    with patch("src.ai_engine.call_gemini_api", return_value=conversational):
        with patch("src.ai_engine.get_gemini_api_key", return_value="fake_key"):
            res = ai_engine.translate_with_ai("yardım", provider="gemini")
            assert res is None


def test_detect_source_language():
    # Türkçe örnekler
    assert ai_engine.detect_source_language("ne yapıyorsun") == "tr"
    assert ai_engine.detect_source_language("günaydın") == "tr"
    assert ai_engine.detect_source_language("nasilsin iyi misin") == "tr"
    assert ai_engine.detect_source_language("bugun hava cok guzel") == "tr"
    assert ai_engine.detect_source_language("ben geliyorum") == "tr"
    assert ai_engine.detect_source_language("sen de gel") == "tr"

    # İngilizce ve Yabancı Dil örnekler
    assert ai_engine.detect_source_language("What are you doing?") == "en"
    assert ai_engine.detect_source_language("Good morning my friend") == "en"
    assert ai_engine.detect_source_language("Good morning") == "en"
    assert ai_engine.detect_source_language("Cancel") == "en"
    assert ai_engine.detect_source_language("Settings") == "en"
    assert ai_engine.detect_source_language("Download application") == "en"
    assert ai_engine.detect_source_language("Save changes") == "en"
    assert ai_engine.detect_source_language("Bonjour tout le monde") == "en"
    assert ai_engine.detect_source_language("Guten Morgen") == "en"
    assert ai_engine.detect_source_language("Hola amigo") == "en"


def test_free_web_translate_mocked(monkeypatch):
    monkeypatch.setattr(
        ai_engine.settings_manager,
        "load_settings",
        lambda: {"network_policy": "web_fallback_optional", "ai_provider": "auto"},
    )
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b'[[["Ayarlar ve bildirimler","Settings and notifications",null,null,1]],null,"en"]'

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        res = ai_engine.free_web_translate("Settings and notifications", target_lang="tr")
        assert res == "Ayarlar ve bildirimler"


def test_free_wiki_summary_mocked(monkeypatch):
    monkeypatch.setattr(
        ai_engine.settings_manager,
        "load_settings",
        lambda: {"network_policy": "web_fallback_optional", "ai_provider": "auto"},
    )
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b'{"extract": "K\xc3\xb6pek, k\xc3\xb6pekgiller familyas\xc4\xb1na ait evcil bir memelidir. 400\'den fazla \xc4\xb1rk\xc4\xb1 vard\xc4\xb1r."}'

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        res = ai_engine.free_wiki_summary("köpekler hakkında bilgi ver")
        assert "Köpek" in res
        assert "memelidir" in res


def test_generate_knowledge_mocked(monkeypatch):
    monkeypatch.setattr(
        ai_engine.settings_manager,
        "load_settings",
        lambda: {"network_policy": "web_fallback_optional", "ai_provider": "auto"},
    )
    with patch("src.ai_engine.call_nvidia_nim", return_value="Köpekler son derece sadık ve zeki evcil hayvanlardır. İnsanlarla binlerce yıldır birlikte yaşarlar."):
        with patch("src.ai_engine.get_nvidia_api_key", return_value="fake_nv_key"):
            res = ai_engine.generate_knowledge("köpekler", provider="nvidia")
            assert res is not None
            assert "Köpekler" in res


def test_is_ai_hallucination_knowledge():
    valid = "Köpekler yaklaşık 15.000 yıl önce evcilleştirilen ilk canlılardandır. Koku alma duyuları çok gelişmiştir."
    assert ai_engine.is_ai_hallucination("köpekler", valid, mode="knowledge") is False

    too_long = " ".join(["bilgi"] * 140)
    assert ai_engine.is_ai_hallucination("köpekler", too_long, mode="knowledge") is True

    too_short = "köpek"
    assert ai_engine.is_ai_hallucination("köpekler", too_short, mode="knowledge") is True


def test_get_groq_api_key_explicit():
    assert ai_engine.get_groq_api_key("gsk_test123") == "gsk_test123"


def test_get_groq_api_key_env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_env_key")
    assert ai_engine.get_groq_api_key() == "gsk_env_key"


def test_test_groq_connection_empty():
    ok, msg, latency = ai_engine.test_groq_connection("")
    assert not ok
    assert "boş" in msg.lower()


def test_test_groq_connection_mocked():
    fake_response = MagicMock()
    fake_response.status = 200
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        ok, msg, latency = ai_engine.test_groq_connection("gsk_valid", "llama-3.3-70b-versatile")
        assert ok
        assert "başarılı" in msg.lower()


def test_call_groq_api_success():
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b'''{
        "choices": [
            {
                "message": {
                    "content": "Bug\xc3\xbcn hava \xc3\xa7ok g\xc3\xbczel."
                }
            }
        ]
    }'''

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        result = ai_engine.call_groq_api(
            "bugun hava cok guzel",
            api_key="gsk_dummy",
            model="llama-3.3-70b-versatile"
        )
        assert result == "Bugün hava çok güzel."


def test_call_groq_api_failure():
    with patch("urllib.request.urlopen", side_effect=Exception("Groq network error")):
        with pytest.raises(ai_engine.NetworkError):
            ai_engine.call_groq_api("test", api_key="gsk_dummy")


def test_is_russian_text():
    assert ai_engine.is_russian_text("Привет, как дела?") is True
    assert ai_engine.is_russian_text("не парься бро") is True
    assert ai_engine.is_russian_text("merhaba kanka nasılsın") is False
    assert ai_engine.is_russian_text("hello world") is False


def test_translate_with_ai_russian(monkeypatch):
    monkeypatch.setattr(
        ai_engine.settings_manager,
        "load_settings",
        lambda: {"network_policy": "translation_optional", "ai_provider": "auto"},
    )
    with patch("src.ai_engine.call_groq_api", return_value="Привет, бро!") as mock_groq:
        res = ai_engine.translate_with_ai("selam kanka", target_lang="auto_ru", api_key="gsk_test", provider="groq")
        assert res == "Привет, бро!"
        assert mock_groq.called


def test_detect_source_language_turkish_chat_edge_cases():
    # Previously misclassified as English due to 'at', 'an', 'in', 'on' stopwords
    assert ai_engine.detect_source_language("bana mesaj at") == "tr"
    assert ai_engine.detect_source_language("link at") == "tr"
    assert ai_engine.detect_source_language("ss at knk") == "tr"
    assert ai_engine.detect_source_language("su an oyundayim") == "tr"
    assert ai_engine.detect_source_language("asagi in") == "tr"
    assert ai_engine.detect_source_language("on dakika bekle") == "tr"
    assert ai_engine.detect_source_language("napiyon") == "tr"
    assert ai_engine.detect_source_language("geliyorum") == "tr"


def test_clean_llm_output_strips_think_and_prefixes():
    raw = "<think>\nFirst, let's analyze the Turkish phrase...\n</think>\nTranslation: \"Send me a message.\""
    assert ai_engine._clean_llm_output(raw) == "Send me a message."


def test_is_valid_translation_output():
    # Russian target must contain Cyrillic
    assert ai_engine.is_valid_translation_output("selam kanka", "Привет, бро!", "ru") is True
    assert ai_engine.is_valid_translation_output("selam kanka", "Selam kanka.", "ru") is False
    # English target must not contain Turkish-specific characters or echo Turkish input
    assert ai_engine.is_valid_translation_output("bana mesaj at", "Send me a message.", "en") is True
    assert ai_engine.is_valid_translation_output("bana mesaj at", "Bana mesaj at.", "en") is False
    assert ai_engine.is_valid_translation_output("tesekkurler", "Teşekkürler.", "en") is False
    # Turkish target must not contain Cyrillic
    assert ai_engine.is_valid_translation_output("Привет", "Merhaba", "tr") is True
    assert ai_engine.is_valid_translation_output("Привет", "Привет", "tr") is False


def test_is_definitely_foreign_text_multilang():
    # Foreign languages should be detected
    assert ai_engine.is_definitely_foreign_text("Hello bro, how are you doing today?") is True
    assert ai_engine.is_definitely_foreign_text("Привет, как дела брат?") is True
    assert ai_engine.is_definitely_foreign_text("Hallo, wie geht es dir heute?") is True
    assert ai_engine.is_definitely_foreign_text("Bonjour, comment ça va mon ami ?") is True
    assert ai_engine.is_definitely_foreign_text("Hola amigo, ¿cómo estás?") is True
    assert ai_engine.is_definitely_foreign_text("مرحبا كيف حالك اليوم") is True
    assert ai_engine.is_definitely_foreign_text("こんにちは、元気ですか？") is True
    assert ai_engine.is_definitely_foreign_text("你好，今天怎么样？") is True
    assert ai_engine.is_definitely_foreign_text("안녕하세요 오늘 어때요") is True

    # Turkish and de-asciified Turkish chat must NOT be flagged as foreign
    assert ai_engine.is_definitely_foreign_text("sendemigeliyorusn") is False
    assert ai_engine.is_definitely_foreign_text("bana mesaj at knk") is False
    assert ai_engine.is_definitely_foreign_text("Birde rusça çevirme tuşu Ekliyelim") is False
    assert ai_engine.is_definitely_foreign_text("ogrencileringozlerindensevincokunuyordu") is False


def test_is_valid_turkish_correction_guard():
    assert ai_engine._is_valid_turkish_correction("Sen de mi geliyorsun?", "Sen de mi geliyorsun?") is True
    # Rejects AI rejoining separated 'de' particle
    assert ai_engine._is_valid_turkish_correction("Sen de mi geliyorsun?", "Sende mi geliyorsun?") is False
    # Rejects code blocks
    assert ai_engine._is_valid_turkish_correction("merhaba", "```python\nprint('merhaba')\n```") is False


def test_translate_with_ai_custom_languages(monkeypatch):
    monkeypatch.setattr(
        ai_engine.settings_manager,
        "load_settings",
        lambda: {"network_policy": "translation_optional", "ai_provider": "auto"},
    )
    with patch("src.ai_engine.call_groq_api", return_value="Hallo mein Freund!") as mock_groq:
        res = ai_engine.translate_with_ai("merhaba arkadaşım", target_lang="de", api_key="gsk_dummy", provider="groq")
        assert res == "Hallo mein Freund!"
        assert mock_groq.called
        call_args = mock_groq.call_args
        assert "German" in call_args.kwargs.get("sys_prompt", "")


def test_fix_with_ai_raises_policy_error_when_local_only():
    # Varsayılan politika local_only olduğu sürece AI düzeltme engellenmeli.
    with pytest.raises(ai_engine.PolicyError):
        ai_engine.fix_with_ai("sendemigeliyorusn", api_key=None)
