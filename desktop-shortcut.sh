#!/bin/bash
# Zen Browser (Firefox tabanlı) ve tüm Wayland pencereleriyle %100 uyumlu Türkçe düzeltici

# 1. Zen / Firefox ve web siteleri için panoyu temizle
echo "" | wl-copy --primary 2>/dev/null
echo "" | wl-copy 2>/dev/null

# 2. Tuş bırakma payı ve Ctrl+C (Zen Browser kopyalama garantisi)
sleep 0.15
ydotool key 29:1 46:1 46:0 29:0 2>/dev/null || wtype -M ctrl c -m ctrl
sleep 0.25

# 3. Kopyalanan metni al (Primary veya Normal Clipboard)
TARGET_TEXT=$(wl-paste 2>/dev/null)
if [ -z "$TARGET_TEXT" ]; then
    TARGET_TEXT=$(wl-paste --primary 2>/dev/null)
fi

# Baştaki/sondaki boşlukları temizle
TARGET_TEXT=$(echo "$TARGET_TEXT" | xargs)

if [ -z "$TARGET_TEXT" ]; then
    notify-send -a "Türkçe Düzeltici" -u low "Uyarı" "Düzeltilecek metin seçilmedi!"
    exit 0
fi

# 4. Çevrimdışı düzelticiyi çalıştır
FIXED_TEXT=$(/home/enes/.local/bin/turkce-duzelt "$TARGET_TEXT")

if [ -n "$FIXED_TEXT" ]; then
    # 5. Düzeltilmiş metni panoya yaz
    echo -n "$FIXED_TEXT" | wl-copy
    echo -n "$FIXED_TEXT" | wl-copy --primary
    
    # 6. Geri yapıştır (Ctrl+V)
    sleep 0.1
    ydotool key 29:1 47:1 47:0 29:0 2>/dev/null || wtype -M ctrl v -m ctrl
    
    # 7. Ses ve Bildirim
    paplay /usr/share/sounds/freedesktop/stereo/message-new-instant.oga 2>/dev/null &
    notify-send -a "Türkçe Düzeltici" -i edit-paste -t 2000 "Düzeltildi ✨" "$FIXED_TEXT"
fi
