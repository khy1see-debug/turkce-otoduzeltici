#!/bin/bash
# Wayland seçili metni düzeltip, seçim hâlâ etkin durumdayken aynı yere yapıştırır.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# Bash command substitution drops trailing newlines. A sentinel preserves the
# exact text while still allowing command status checks.
capture_command_output() {
    local captured status
    captured=$("$@" 2>/dev/null; status=$?; printf '\001'; exit "$status")
    status=$?
    CAPTURED_OUTPUT=${captured%$'\001'}
    return "$status"
}

CORRECTOR_BIN="${TURKCE_DUZELT_BIN:-$(command -v turkce-duzelt-fast || true)}"
if [ -z "$CORRECTOR_BIN" ] && [ -x "$SCRIPT_DIR/.venv/bin/turkce-duzelt-fast" ]; then
    CORRECTOR_BIN="$SCRIPT_DIR/.venv/bin/turkce-duzelt-fast"
fi
if [ -z "$CORRECTOR_BIN" ]; then
    CORRECTOR_BIN="$(command -v turkce-duzelt || true)"
fi
if [ -z "$CORRECTOR_BIN" ] && [ -x "$SCRIPT_DIR/turkce-duzelt" ]; then
    CORRECTOR_BIN="$SCRIPT_DIR/turkce-duzelt"
fi
if [ -z "$CORRECTOR_BIN" ]; then
    notify-send -a "Türkçe Düzeltici" -u critical "Hata" "turkce-duzelt komutu bulunamadı. Önce projeyi kurun."
    exit 1
fi

# 1. Zen / Firefox ve web siteleri için panoyu temizle
echo "" | wl-copy --primary 2>/dev/null
echo "" | wl-copy 2>/dev/null

# 2. Tuş bırakma payı ve Ctrl+C (Zen Browser kopyalama garantisi)
sleep 0.15
ydotool key 29:1 46:1 46:0 29:0 2>/dev/null || wtype -M ctrl c -m ctrl
sleep 0.25

# 3. Kopyalanan metni al (Primary veya Normal Clipboard)
if ! capture_command_output wl-paste || [ -z "$CAPTURED_OUTPUT" ]; then
    capture_command_output wl-paste --primary || true
fi
TARGET_TEXT=$CAPTURED_OUTPUT

# Boşlukları xargs ile yeniden biçimlendirme; seçimin satır ve boşluklarını koru.
if [ -z "${TARGET_TEXT//[[:space:]]/}" ]; then
    notify-send -a "Türkçe Düzeltici" -u low "Uyarı" "Düzeltilecek metin seçilmedi!"
    exit 0
fi

# 4. Çevrimdışı düzelticiyi çalıştır
if ! capture_command_output "$CORRECTOR_BIN" "$TARGET_TEXT"; then
    notify-send -a "Türkçe Düzeltici" -u critical "Hata" "Seçili metin düzeltilemedi."
    exit 1
fi
FIXED_TEXT=$CAPTURED_OUTPUT

if [ -n "$FIXED_TEXT" ]; then
    # Seçim, önizleme penceresiyle odağı kaybetmesin. Panoya yazıp hemen
    # Ctrl+V gönderince uygulama mevcut seçimi yeni metinle değiştirir.
    echo -n "$FIXED_TEXT" | wl-copy
    echo -n "$FIXED_TEXT" | wl-copy --primary

    # Geri yapıştır (Ctrl+V), seçili eski metnin üzerine yazar.
    sleep 0.1
    ydotool key 29:1 47:1 47:0 29:0 2>/dev/null || wtype -M ctrl v -m ctrl
    
    # 7. Ses ve Bildirim
    paplay /usr/share/sounds/freedesktop/stereo/message-new-instant.oga 2>/dev/null &
    notify-send -a "Türkçe Düzeltici" -i edit-paste -t 2000 "Düzeltildi ✨" "$FIXED_TEXT"
fi
