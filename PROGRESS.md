# 📋 Proje İlerleme ve Denetim Kaydı (PROGRESS.md)

Bu dosya `vibecoding-toolkit` ve `self-healing-debugger` protokolleri kapsamında uçtan uca yapılan mimari denetim, hata onarımları ve performans iyileştirmelerini izler.

## ✅ Tamamlanan Atomik Görevler

- [x] **Görev 1: Deasciifier & Speller & Segmenter Performans ve Algoritma Onarımı**
  - `src/deasciifier.py`: `ASCII_TO_TURKISH['i']` altındaki gereksiz `'î'` varyasyonu kaldırılarak $3^k \to 2^k$ kombinasyon indirgemesi yapıldı; `max_indices=6` sınırı getirildi.
  - `src/speller.py`: `edits1` üzerinde önce $O(1)$ sözlük kontrolü, ardından yalnızca yer değiştirme/silme ve ünlü eklemelerinde `deasciify_word` çağrısı yapılarak `pytest` çalışma süresi sonsuz döngüden **~2.9 saniyeye** düşürüldü.
  - `src/segmenter.py`: Bitişik kelimelerin sonundaki 1-3 harfli parçaların (`banasun` sonundaki `n` harfinin `ne` yapılması) hatalı imla düzeltmesine girmesi (`j == n` hatası) engellendi (`banasun` $\rightarrow$ `bana sun`).

- [x] **Görev 2: TDK Kuralları, Eş Sesli Cins İsimler ve Fiil Daralmaları**
  - `src/tdk_rules.py`: `abi` $\rightarrow$ `Ab'i`, `canı` $\rightarrow$ `Can'ı`, `denize` $\rightarrow$ `Deniz'e`, `yağmurda` $\rightarrow$ `Yağmur'da`, `orduda` $\rightarrow$ `Ordu'da` şeklindeki yanlış özel isim/kısaltma kesme işareti hataları giderildi.
  - `src/tdk_rules.py`: Fıstıkçı Şahap ünsüz benzeşmesi yalnızca kelime sonu ek sınırlarına (`-da/-de`, `-dan/-den`, `-dı/-di`, `-cı/-ci`) daraltılarak `takdir`, `tasdik`, `mahcup`, `mescit`, `akdeniz` gibi kelime köklerinin bozulması önlendi.
  - `src/grammar.py`: Belirtme halindeki kelimeleri (`işi`, `evi`, `telefonu`) iyelik sanıp cümlenin ilk kelimesine `-in/-ın` ekleyen (`Bugün işi bitirdim` $\rightarrow$ `Bugünün işi bitirdim`) hatalı kural kaldırıldı.
  - `src/slang.py`: Genel konuşma dili gelecek zaman daralmaları (`-icek` $\rightarrow$ `-ecek`, `-ıcak` $\rightarrow$ `-acak`, `-icem` $\rightarrow$ `-eceğim`, `-ıcam` $\rightarrow$ `-acağım`; örn. `düzelticekleri` $\rightarrow$ `düzeltecekleri`) eklendi.

- [x] **Görev 3: Öz-Öğrenme (Self-Learning) ve Kişisel Sözlük Sanitasyonu**
  - `src/self_learning.py` & `src/dictionary.py`: Kesme işaretinden sonraki eklerin (`PC'den` $\rightarrow$ `den`) ve TDK yazım hatalarının (`şuan`) kişisel sözlüğe sızması engellendi.
  - `Ctrl+Z` (Geri Alma) durumunda hem hatalı düzeltmenin reddedilmesi hem de kullanıcının orijinal özel kelimesinin öğrenilmesi sağlandı.

- [x] **Görev 4: Sistem Tepsisi (`Alt+Q` / `Alt+W`) Hızlandırma ve Hibrit AI Hattı**
  - `src/app_tray.py` & `src/settings_manager.py`: `Alt+Q` kısayolunda önce ~2ms'lik yerel deterministik motorun çalışması sağlandı; `use_ai_in_tray` varsayılanı `False` yapılarak 5-6 saniyelik API gecikmesi sıfırlandı.
  - `src/ai_engine.py`: Varsayılan NVIDIA modeli ~800ms yanıt süreli `meta/llama-3.2-11b-vision-instruct` olarak güncellendi; cümle kırpma (truncation) koruması eklendi.

- [x] **Görev 5: Regresyon Testleri ve Doğrulama**
  - `tests/test_corrector.py`: Tüm yeni dilbilgisi, eş sesli kelime, devrik cümle ve bitişik kelime senaryoları için birim testleri eklendi.
