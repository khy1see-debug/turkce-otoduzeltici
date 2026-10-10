#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PROJECT_ROOT}/.venv/bin/python"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
UNIT_DIR="${CONFIG_HOME}/systemd/user"
UNIT_FILE="${UNIT_DIR}/turkce-otoduzeltici.service"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv bulunamadı. Önce uv kurup tekrar deneyin." >&2
    exit 1
fi
if ! command -v systemctl >/dev/null 2>&1 || ! systemctl --user is-system-running >/dev/null 2>&1; then
    echo "Çalışan bir systemd kullanıcı oturumu gerekli." >&2
    exit 1
fi

if [ ! -x "$PYTHON" ]; then
    uv venv "${PROJECT_ROOT}/.venv"
fi
uv pip install --python "${PYTHON}" -e "${PROJECT_ROOT}"
mkdir -p "${UNIT_DIR}"
cat > "${UNIT_FILE}" <<EOF
[Unit]
Description=Türkçe Otomatik Düzeltici arka plan servisi
After=default.target

[Service]
Type=simple
Environment="XDG_CONFIG_HOME=${CONFIG_HOME}"
ExecStart="${PROJECT_ROOT}/.venv/bin/turkce-duzelt-daemon"
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now turkce-otoduzeltici.service
echo "Servis kuruldu ve oturum açılışında başlayacak."
echo "Kısayolda hızlı istemci için ${PROJECT_ROOT}/.venv/bin/turkce-duzelt-fast kullanılabilir."
