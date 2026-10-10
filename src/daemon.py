"""Persistent local correction service for repeated desktop hotkey requests."""

import json
import os
import socket
import socketserver
import sys
from typing import Callable

from src.grammar import fix_sentence

MAX_REQUEST_BYTES = 4 * 1024 * 1024
SOCKET_FILENAME = "turkce-otoduzeltici.sock"


def socket_path() -> str:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        raise RuntimeError("XDG_RUNTIME_DIR tanımlı değil; kullanıcı oturumu gerekli.")
    return os.path.join(runtime_dir, SOCKET_FILENAME)


class CorrectionHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        line = self.rfile.readline(MAX_REQUEST_BYTES + 1)
        if not line or len(line) > MAX_REQUEST_BYTES:
            self._reply({"ok": False, "error": "İstek boş veya izin verilen boyutu aşıyor."})
            return

        try:
            request = json.loads(line.decode("utf-8"))
            text = request.get("text")
            if not isinstance(text, str):
                raise ValueError("text alanı metin olmalı")
            result = self.server.corrector(text)  # type: ignore[attr-defined]
            self._reply({"ok": True, "text": result})
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._reply({"ok": False, "error": str(exc)})
        except Exception:
            self._reply({"ok": False, "error": "Metin düzeltilemedi."})

    def _reply(self, data: dict) -> None:
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8") + b"\n")


class CorrectionServer(socketserver.UnixStreamServer):
    def __init__(self, path: str, corrector: Callable[[str], str] = fix_sentence):
        self.corrector = corrector
        super().__init__(path, CorrectionHandler)


def main() -> int:
    path = socket_path()
    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)

    if os.path.lexists(path):
        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            probe.connect(path)
        except OSError:
            os.unlink(path)
        else:
            print("Düzeltme servisi zaten çalışıyor.", file=sys.stderr)
            return 0
        finally:
            probe.close()

    server = CorrectionServer(path)
    os.chmod(path, 0o600)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
