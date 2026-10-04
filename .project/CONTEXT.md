# Çevrimdışı Türkçe Otomatik Düzeltici — proje bağlamı

Revision: 0 · Yetkili kaynak: .project/state.json

Bu görünüm türetilmiştir. Güncel kanıt kontrolü için context komutunu çalıştır.

Amaç: Bitişik yazılan (sendemigeliyorusn gibi), hatalı Türkçe metinleri çevrimdışı, 0-token maliyetiyle düzeltmek
Hedef kitle: Hızlı ve hatasız Türkçe yazmak isteyen kullanıcılar

## Kapsam

- Bitişik kelime ayırma
- Yazım denetimi
- Soru eki ve bağlaç ayrımı
- CLI ve kütüphane

## Kapsam dışı

- Ücretli cloud API bağımlılığı

## Kısıtlar

- Tamamen yerel ve 0-token çalışmalı
- Python 3.10+ uyumlu

## Açık sorular

- Yok.

## Nesneler ve ilişkiler

- modul-segmenter (modul): Segmenter Modülü
- modul-speller (modul): Yazım Düzeltme Modülü
- modul-grammar (modul): Dilbilgisi ve Noktalama Modülü

### Somut nesne değerleri

- modul-segmenter: {"path": "src/segmenter.py", "status": "taslak"}
- modul-speller: {"path": "src/speller.py", "status": "taslak"}
- modul-grammar: {"path": "src/grammar.py", "status": "taslak"}

Türler ve bağlantı kuralları: `ontology` komutu / `ONTOLOJİ.md`.

## Kararlar


## Görevler

- T-MOTOR [todo] Segmenter, Speller ve Dilbilgisi motorunu oluştur (kayıt: todo)
  - Ölçüt: Segmenter bitişik kelimeleri ayırabilmeli
  - Ölçüt: Speller harf hatalarını düzeltebilmeli
  - İlgili nesneler: modul-segmenter, modul-speller, modul-grammar
  - Girdiler: yok
  - Ürettiği nesneler: modul-segmenter, modul-speller, modul-grammar
  - Etkin önkoşullar: yok
  - Kabul güncelliği: henüz doğrulanmadı · tamamlanma sayısı: 0
- T-TEST [blocked] 'sendemigeliyorusn' ve varyant testlerini yaz ve doğrula (kayıt: todo)
  - Ölçüt: pytest ile tüm testler sıfır hata ile geçmeli
  - İlgili nesneler: modul-segmenter, modul-speller, modul-grammar
  - Girdiler: modul-segmenter, modul-speller, modul-grammar
  - Ürettiği nesneler: yok
  - Etkin önkoşullar: T-MOTOR
  - Üretici bağı: modul-grammar ← T-MOTOR
  - Üretici bağı: modul-segmenter ← T-MOTOR
  - Üretici bağı: modul-speller ← T-MOTOR
  - Kabul güncelliği: henüz doğrulanmadı · tamamlanma sayısı: 0
  - Kontrol: dependency T-MOTOR: todo

## Çalışılabilir görevler

T-MOTOR

## Uyarılar

- Yok.

## Onarım işlemleri

Bunlar öneridir; gerekçeyi değerlendir, actor ekle ve güncel revision ile uygula.
- Yok.

Kanıt hash'i dosya sürümünü denetler; kalite veya insan kabulünü ispatlamaz.
