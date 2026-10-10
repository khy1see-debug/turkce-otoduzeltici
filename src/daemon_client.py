"""Client for the persistent local correction service."""

import json
import os
import socket
import subprocess
import sys
import time

SERVICE_NAME = "turkce-otoduzeltici.service"
SOCKET_FILENAME = "turkce-otoduzeltici.sock"
REQUEST_TIMEOUT = 5
SERVICE_START_WAIT = 15


def _socket_path() -> str:
    explicit_path = os.environ.get("TURKCE_DUZELT_SOCKET")
    if explicit_path:
        return explicit_path
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime_dir:
        raise RuntimeError("XDG_RUNTIME_DIR tanımlı değil.")
    return os.path.join(runtime_dir, SOCKET_FILENAME)


def _request(text: str, path: str) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(REQUEST_TIMEOUT)
        client.connect(path)
        client.sendall(json.dumps({"text": text}, ensure_ascii=False).encode("utf-8") + b"\n")
        with client.makefile("rb") as response_file:
            response = json.loads(response_file.readline().decode("utf-8"))
    if not response.get("ok"):
        raise RuntimeError(response.get("error", "Düzeltme servisi hata döndürdü."))
    result = response.get("text")
    if not isinstance(result, str):
        raise RuntimeError("Düzeltme servisi geçersiz yanıt döndürdü.")
    return result


def _correct_locally(text: str) -> str:
    from src.grammar import fix_sentence

    return fix_sentence(text)


def correct_text(text: str, path: str | None = None) -> str:
    try:
        path = path or _socket_path()
    except RuntimeError:
        return _correct_locally(text)
    try:
        return _request(text, path)
    except (OSError, TimeoutError):
        # Service may be installed but not yet started (for example just after login).
        try:
            started = subprocess.run(
                ["systemctl", "--user", "start", "--no-block", SERVICE_NAME],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
        except (OSError, subprocess.SubprocessError):
            started = None
        if started is None or started.returncode != 0:
            return _correct_locally(text)

        deadline = time.monotonic() + SERVICE_START_WAIT
        while time.monotonic() < deadline:
            time.sleep(0.1)
            try:
                return _request(text, path)
            except (OSError, TimeoutError):
                continue

        # Preserve functionality on systems without the optional user service.
        return _correct_locally(text)


def main() -> int:
    if len(sys.argv) < 2:
        print("Kullanım: turkce-duzelt-fast METİN", file=sys.stderr)
        return 2
    try:
        print(correct_text(" ".join(sys.argv[1:])))
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"Düzeltme servisi hatası: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
