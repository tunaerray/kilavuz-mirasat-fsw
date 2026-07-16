# Geliştirme Yol Haritası (DEVELOPMENT_PLAN)

Tüm yazılım tek seferde yazılmaz. Aşağıda uçuşa hazır hale gelene kadar tüm yol
haritası, **bu oturumda yalnız Aşama 1** fiziksel olarak uygulanır.

## Aşama 1 — Çekirdek İskelet (BU OTURUM) ✅
Kapsam (ANA_PROMPT `<phase_1_mandatory_scope>`):
1. Yapılandırma sistemi (SIMULATION_ONLY varsayılan, tüm eşikler parametre).
2. Zaman soyutlaması (RealClock/FakeClock).
3. Hata/sonuç modeli (Result/ErrorCode).
4. Uçuş durum makinesi + statü kodu (0..5) eşlemesi.
5. Kalıcılık (görev zamanı + paket sayacı, restart dayanımı).
6. Telemetri paket üretici (17 alan, ARAS hata kodu).
7. Mock sensörler (nominal/aykırı/timeout).
8. Güvenli aktüatör arayüzleri (arm/safe state).
9. Sağlık izleme temeli.
10. Sınırlı ana döngü (`--max-cycles` / `--duration`).
+ Birim & entegrasyon testleri; derleme/test/statik analiz komutlarının çalıştırılması.

## Aşama 2 — Kontrol & Navigasyon
- Sensör füzyonu (baro+IMU+GPS) ile irtifa/iniş hızı/yönelim kestirimi.
- PID kontrolcüler; 8–10 m/s kontrollü alçalma; SİGMA kol açma/kilitleme.
- FlightControllerLink somut MAVLink implementasyonu; motor PWM/RPM tutarlılık.
- APAM'ın füzyon tabanlı çoklu-sensör kararı; motor arıza tespiti.

## Aşama 3 — Görev & Bonus Servisleri
- Komut servisi: manuel ayrılma, manuel APAM, RHRHRH (BONUS-2 S2D-IOT).
- BONUS-1 Hovering (200 m, 10 sn, 0–1 m/s) kontrol modu.
- Buzzer / kurtarma statüsü; iniş sonrası telemetri süresi yönetimi.

## Aşama 4 — Haberleşme & Kayıt Sistemleri
- LoRa E22 gerçek sürücü; CRC/checksum; 1 Hz RF gönderimi.
- BONUS-3 Z.I.R.H store-and-forward tamponlama/geri-aktarım.
- Kamera (Pi Camera V2) H.264 + 5 GHz Wi-Fi canlı akış; SD video.

## Aşama 5 — Donanım Entegrasyonu & FRR  (YAZILIM tarafı uygulandı)
- ✅ Preflight go/no-go kapısı (`preflight.py`, `--preflight`).
- ✅ Saha baro kalibrasyonu (`calibration.py`, çok örnekli).
- ✅ Titreşim/gürültü dayanıklılığı — FRR §4.2 yazılım analoğu (`--vibration`).
- ✅ Profil bazlı sürücü fabrikası + FLIGHT gate (`factory.py`); guarded gerçek
  LoRa sürücü iskeleti (`real_lora.py`).
- ✅ Uçuş öncesi checklist (`docs/PREFLIGHT_CHECKLIST.md`) ve FRR prosedürleri
  (`docs/FRR_TEST_PROCEDURES.md`).
- ⏳ **Donanım gerektiren (bu ortamda yapılamaz):** gerçek sensör/aktüatör/FC
  sürücülerinin fiziksel I/O doğrulaması; MAVLink; 10G şok / titreşim masası /
  düşme fiziksel testleri. Prosedürler belgelendi, saha/laboratuvara bırakıldı.
