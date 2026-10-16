"""
Unit tests for NVIDIA AI engine and LLM fallback logic.
"""

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
        result = ai_engine.call_nvidia_nim("test", api_key="nvapi-dummy")
        assert result is None


def test_fix_with_ai_fallback():
    # Without any API key and without local model, fix_with_ai should return None gracefully
    with patch.dict("os.environ", {}, clear=True):
        res = ai_engine.fix_with_ai("sendemigeliyorusn", api_key=None)
        # Should gracefully return None without raising an exception
        assert res is None or isinstance(res, str)


def test_translate_with_ai_mocked():
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


def test_translate_with_ai_fallback_no_key():
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
        result = ai_engine.call_gemini_api("test", api_key="AIzaSyDummy")
        assert result is None


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
    with patch("src.ai_engine.call_gemini_api", return_value=hallucinated):
        with patch("src.ai_engine.get_gemini_api_key", return_value="fake_key"):
            res = ai_engine.fix_with_ai("kanka", provider="gemini")
            assert res is None


def test_translate_with_ai_blocks_hallucination():
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


def test_free_web_translate_mocked():
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.read.return_value = b'[[["Ayarlar ve bildirimler","Settings and notifications",null,null,1]],null,"en"]'

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_response
        res = ai_engine.free_web_translate("Settings and notifications", target_lang="tr")
        assert res == "Ayarlar ve bildirimler"



