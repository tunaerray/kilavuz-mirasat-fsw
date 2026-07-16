# FRR Sistem Test Prosedürleri (FRR_TEST_PROCEDURES)

Şartname §4.2 ve FRR kapsamındaki sistem seviyesi testler.

> ⚠️ **DÜRÜSTLÜK / KAPSAM NOTU:** Aşağıdaki **fiziksel** testler (10G şok, 150–200 Hz
> titreşim masası, düşme testi) gerçek donanım ve laboratuvar ekipmanı gerektirir.
> Bu yazılım geliştirme ortamında **çalıştırılamazlar** ve çalıştırıldığı iddia
> EDİLMEMİŞTİR. Bu belge test prosedürlerini tanımlar; yazılımın karşılık gelen
> **yazılım-analoğu** dayanıklılık kontrolleri otomatik testlerle doğrulanmıştır
> (aşağıda "Yazılım analoğu" satırları).

## 1. Titreşim Testi (150–200 Hz) — Gereksinim/§4.2
- **Fiziksel prosedür:** Model uydu titreşim masasına bağlanır; 150–200 Hz bandında
  titreştirilirken sistem AÇIK olmalı ve telemetri **kesintisiz** iletmeye devam
  etmelidir. Gevşeyen bağlantı/konnektör kontrol edilir.
- **Kabul kriteri:** Titreşim boyunca 1 Hz telemetri kaybı yok; paketler CRC-geçerli.
- **Yazılım analoğu (OTOMATİK ✅):** `tests/test_vibration.py` — sensörlere 175 Hz
  titreşim gürültüsü enjekte edilir; telemetri paket sayısı temiz koşuyla aynı
  kalır (kesinti yok), APAM yanlış tetiklenmez, yönelim kestirimi makul kalır.
  Komut: `python -m src.app.main --vibration 1.0 --max-cycles 4000 --duration 180`.

## 2. Şok Dayanımı (10G) — Gereksinim-12
- **Fiziksel prosedür:** Bileşenler ve bağlantılar 10G şoka dayanacak şekilde;
  şok tablasında/darbe testinde doğrulanır. Test sırasında sistem açık ve veri
  iletiyor olmalıdır.
- **Kabul kriteri:** Şok sonrası tüm alt sistemler çalışır; veri iletimi sürdü.
- **Yazılım tarafı:** Şok anında sensör aykırı değerleri `Estimatorout` aykırı
  reddi ve `HealthMonitor` bayraklarıyla ele alınır; anlık bozulma APAM'ı tek
  başına tetiklemez (16 m/s × 10 sn kuralı). Fiziksel dayanım donanım/mekanik
  sorumluluğundadır.

## 3. Düşme Testi — §4.2
- **Fiziksel prosedür:** Sistem açık ve veri iletirken kontrollü düşme yapılır.
- **Kabul kriteri:** Düşme boyunca telemetri sürer; iniş sonrası buzzer + konum.
- **Yazılım analoğu (OTOMATİK ✅):** Tam iniş simülasyonu (`test_app_integration`),
  iniş sonrası buzzer ve telemetri penceresi (`test_recovery`).

## 4. Yer İstasyonundan Ayrılma Komutu Testi — Gereksinim-7, §4.2
- **Prosedür:** Yer istasyonundan manuel ayrılma komutu gönderilir; ayrılma
  mekanizması tetiklenir.
- **Yazılım analoğu (OTOMATİK ✅):** `tests/test_command_service.py`,
  `tests/test_app_integration.py::test_manual_apam_command_triggers_apam` ve manuel
  ayrılma yolu. Komut: `python -m src.app.main --command "T:SEP"`.

## 5. Z.I.R.H Kesinti Bölgesi Senaryosu — BONUS-3 (PDR test planı)
- **Prosedür:** Haberleşme karıştırma/kesinti bölgesi simüle edilir; kayıp veriler
  bölgeden çıkınca başarıyla iletilmelidir.
- **Yazılım analoğu (OTOMATİK ✅):** `tests/test_store_forward.py`,
  `test_app_integration::test_zirh_buffers_then_forwards_after_jam`.
  Komut: `python -m src.app.main --jam "80:110"`.

## Otomatik Yazılım Doğrulama Özeti
Tüm yazılım-analoğu kontroller test süitinde koşar:
```
python -m pytest --timeout=30       # tüm birim + entegrasyon testleri
python -m src.app.main --preflight   # uçuşa hazırlık go/no-go
```
Fiziksel testler saha/laboratuvarda, gerçek donanım profili (FLIGHT) ile ve gerçek
sürücüler kurulduktan sonra yürütülür (bkz. `PREFLIGHT_CHECKLIST.md`, `factory.py`).
