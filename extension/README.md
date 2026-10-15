# 🌐 Türkçe Otomatik Düzeltici — Tarayıcı Eklentisi (Chrome / Edge / Brave)

Bu eklenti, tarayıcınızdaki (Gmail, Notion, Twitter/X, Discord, Google Docs vb.) tüm metin alanlarında **%100 yerel, 0-token ve TDK uyumlu** imla düzeltmesi yapmanızı sağlar.

---

## 🚀 1. Kurulum (10 Saniye)

1. Tarayıcınızın eklenti sayfasına gidin:
   - **Google Chrome / Brave:** `chrome://extensions`
   - **Microsoft Edge:** `edge://extensions`
2. Sağ üstteki **"Geliştirici modu" (Developer mode)** anahtarını açın.
3. Sol üstteki **"Paketlenmemiş öğe yükle" (Load unpacked)** butonuna tıklayın.
4. Bu projede bulunan `extension` klasörünü seçin.
5. Eklenti simgesi araç çubuğunuza eklenecektir! 🎉

---

## ⌨️ 2. Kullanım Şekilleri

1. **Sayfada Sağ Tık:** Herhangi bir web sayfasında veya metin kutusunda metni seçin $\rightarrow$ Sağ tıklayın $\rightarrow$ **"🇹🇷 Türkçe İmla Düzelt"** deyin.
2. **Klavye Kısayolu:** Herhangi bir metin kutusundayken **`Alt + Shift + Q`** tuşlarına basın; metin yerinde TDK kurallarıyla düzeltilir.
3. **Eklenti Açılır Penceresi (Popup):** Araç çubuğundaki eklenti simgesine tıklayın; metninizi yapıştırıp `Ctrl + Enter` veya **Düzelt** butonuyla istediğiniz modda (TDK, De-asciifier, Harf dönüşümü) dönüştürün.

> [!NOTE]
> Eklenti, bilgisayarınızda çalışan yerel REST API'ye (`http://127.0.0.1:8765`) bağlanır. Masaüstü uygulamasını (`turkce-otoduzeltici.exe`) veya web sunucusunu (`python -m src.cli --web`) açık tutmanız yeterlidir. Sıfır dış veri sızıntısı güvencesiyle çalışır.
