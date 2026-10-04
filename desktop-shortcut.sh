#!/bin/bash
# Instagram/Tarayıcı ve tüm pencerelerle %100 uyumlu Türkçe otomatik düzeltme

# 1. Eski panoyu temizle veya işaretle
OLD_CLIP=$(wl-paste 2>/dev/null)

# 2. Seçili metni kopyala (Klavye tuş simülasyonu)
# Windows tuşunu bıraktığından emin olmak için küçük bekleme
sleep 0.1
wtype -M ctrl c -m ctrl
sleep 0.2

# 3. Kopyalanan yeni metni al
NEW_CLIP=$(wl-paste 2>/dev/null)
PRIMARY_CLIP=$(wl-paste --primary 2>/dev/null)

# Eğer yeni bir kopyalama yapıldıysa NEW_CLIP'i kullan, yoksa primary seçimi dene
if [ -n "$NEW_CLIP" ] && [ "$NEW_CLIP" != "$OLD_CLIP" ]; then
    TARGET_TEXT="$NEW_CLIP"
elif [ -n "$PRIMARY_CLIP" ]; then
    TARGET_TEXT="$PRIMARY_CLIP"
else
    TARGET_TEXT="$NEW_CLIP"
fi

if [ -z "$TARGET_TEXT" ]; then
    notify-send -a "Türkçe Düzeltici" "Uyarı" "Düzeltilecek metin bulunamadı!"
    exit 0
fi

# 4. Çevrimdışı düzelticiyi çalıştır
FIXED_TEXT=$(/home/enes/.local/bin/turkce-duzelt "$TARGET_TEXT")

if [ -n "$FIXED_TEXT" ]; then
    # 5. Düzeltilmiş metni panoya yaz
    echo -n "$FIXED_TEXT" | wl-copy
    echo -n "$FIXED_TEXT" | wl-copy --primary
    
    # 6. Yerine yapıştır
    sleep 0.1
    wtype -M ctrl v -m ctrl
    
    # Bildirim
    notify-send -a "Türkçe Düzeltici" -i edit-paste -t 2000 "Düzeltildi ✨" "$FIXED_TEXT"
fi
