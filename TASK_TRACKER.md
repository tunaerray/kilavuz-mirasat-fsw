# TASK_TRACKER — Açık İşler ve Teknik Borçlar

Aşama 1'de bilinçli olarak ERTELENEN işler. Placeholder/boş fonksiyon bırakma
yasağı gereği, uygulanmayan işler burada gereksinim kimliğiyle listelenir.

## Aşama 2 — Kontrol & Navigasyon ✅ (TAMAMLANDI)
- [x] REQ-CTRL-001: Sensör füzyonu (baro+GPS irtifa/hız, IMU yönelim, çoklu-sensör
      tutarlılık) → `src/control/estimator.py`.
- [x] REQ-CTRL-002: PID ile 8–10 m/s kontrollü alçalma → `pid.py`,
      `descent_controller.py`.
- [~] REQ-CTRL-003: SİGMA kol açma/kilitleme — temel dizi `main.py`'de; tam
      kontrol koreografisi (zamanlama/geri bildirim) Aşama 3'te olgunlaşacak.
- [x] REQ-CTRL-005: Motor komut üretimi + throttle endpoint limiti (arm interlock).
- [x] REQ-SAFE-010: Motor PWM/RPM tutarsızlığı → `src/services/motor_health.py`.
- [x] EKSİK-001 (sim): `SimulatedFlightControllerLink` (RPM modeli, arıza enjeksiyonu).
- [x] APAM çoklu-sensör çelişki filtresi (GPS varsa yalanlamayı dikkate al, GPS
      yoksa tek sensöre düş) → `failsafe.py`.
- [ ] EKSİK-001 (gerçek): `FlightControllerLink` gerçek MAVLink implementasyonu
      donanım gerektirir → Aşama 5.

## Aşama 3 — Görev & Bonus ✅ (TAMAMLANDI)
- [x] REQ-MISSION-006: Manuel ayrılma komutu → `command_service.py` + `main.py`.
- [x] REQ-SAFE-006: Manuel APAM komutu → `command_service.py` → `failsafe.py`.
- [x] REQ-BONUS-001: BONUS-1 Hovering (200 m, 10 sn) → durum makinesi zamanlayıcısı
      + `descent_controller` hover modu.
- [x] REQ-BONUS-002: BONUS-2 S2D-IOT RHRHRH doğrula→SD→IoT → `s2d_iot.py`.
- [x] REQ-MISSION-010: Buzzer + iniş sonrası telemetri penceresi → `recovery.py`.
- [x] CONFLICT-001: İniş sonrası telemetri süresi config penceresi olarak uygulandı
      (varsayılan 10 sn; `post_landing_telemetry_s` ile 60 sn'ye çekilebilir).
- Not: REQ-CTRL-003 (SİGMA kol koreografisi) temel dizi olarak çalışıyor; tam
  zamanlama/geri bildirim Aşama 4/5 donanım entegrasyonunda olgunlaşacak.

## Aşama 4 — Haberleşme & Kayıt ✅ (TAMAMLANDI)
- [x] REQ-TLM-008: CRC16-CCITT çerçeveleme/doğrulama → `src/telemetry/framing.py`.
- [x] REQ-TLM-009 / REQ-BONUS-003: Z.I.R.H store-and-forward → `store_forward.py`
      (kesintide SD'ye tampon, çıkışta burst geri-aktarım, kayıp yok).
- [x] REQ-TLM-010: Kamera SD kayıt + canlı akış → `camera_service.py` (sim;
      akış kopukluğunda kayıt sürer). Gerçek picamera2/H.264 sürücüsü Aşama 5.
- [ ] REQ-HW-003: LoRa E22 gerçek UART sürücüsü — framing + store-and-forward
      hazır; yalnız fiziksel taşıma katmanı donanım gerektirir → Aşama 5.

## Aşama 5 — Donanım & FRR
- [ ] REQ-HW-001..005: Gerçek sensör/aktüatör sürücüleri; HIL/FLIGHT profilleri.
- [ ] REQ-TEST-005: 10G şok, 150–200 Hz titreşim, düşme, ayrılma sistem testleri.

## Netleştirilecek Açık Noktalar (CDR/hakem)
- [ ] CONFLICT-001: İniş sonrası TLM süresi 10 sn mi 60 sn mi? (config varsayılan 10)
- [ ] CONFLICT-003: Hata kodu 4 hane mi 5 hane mi? (config varsayılan 4)
- [ ] CONFLICT-002: PDR s.62 statü kodları düzeltilmeli (şartname esas).
- [ ] EKSİK-002: LoRa air-rate/kanal, sensör I2C adresleri kesinleştirilecek.

## Açık Kalan Sorunlar (Aşama 1 çalıştırma)
- Aşama 1 çalıştırmada **açık kalan bloke edici sorun YOK**. 88 test geçti,
  simülasyon nominal (RECOVERY) ve runaway (APAM) senaryolarında doğrulandı.
- Bilinen küçük konu: Windows konsolunda Türkçe karakterler cp1252'de bozuk
  görünebilir; `PYTHONIOENCODING=utf-8` ile düzelir (yalnız kozmetik, log/CSV
  UTF-8'dir). Teknik borç olarak Aşama 4 loglama iyileştirmesine bırakıldı.
- İrtifa sıfır-referansı artık kalıcı (restart sonrası tutarlı); mid-flight ilk
  boot için saha kalibrasyon prosedürü Aşama 5'te netleştirilecek (EKSİK-003).
