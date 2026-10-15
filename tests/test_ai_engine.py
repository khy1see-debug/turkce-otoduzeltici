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
