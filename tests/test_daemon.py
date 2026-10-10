import socket
import threading
from types import SimpleNamespace

import pytest


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix sockets are required")
def test_persistent_service_client_roundtrip(tmp_path):
    from src.daemon import CorrectionServer
    from src.daemon_client import correct_text

    path = str(tmp_path / "corrector.sock")
    server = CorrectionServer(path, corrector=lambda text: f"düzeltildi: {text}")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert correct_text("yanlış   metin\nikinci satır", path) == (
            "düzeltildi: yanlış   metin\nikinci satır"
        )
        assert correct_text("ikinci istek", path) == "düzeltildi: ikinci istek"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.skipif(not hasattr(socket, "AF_UNIX"), reason="Unix sockets are required")
def test_client_falls_back_when_user_service_is_not_installed(tmp_path, monkeypatch):
    from src import daemon_client

    monkeypatch.setattr(
        daemon_client.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1),
    )
    monkeypatch.setattr(daemon_client, "_correct_locally", lambda text: f"local: {text}")

    assert daemon_client.correct_text("deneme", str(tmp_path / "missing.sock")) == "local: deneme"
