# TASK_TRACKER — Açık İşler ve Teknik Borçlar

Aşama 1'de bilinçli olarak ERTELENEN işler. Placeholder/boş fonksiyon bırakma
yasağı gereği, uygulanmayan işler burada gereksinim kimliğiyle listelenir.

## Aşama 2 — Kontrol & Navigasyon
- [ ] REQ-CTRL-001: Sensör füzyonu (baro+IMU+GPS) irtifa/iniş hızı/yönelim kestirimi.
- [ ] REQ-CTRL-002: PID ile 8–10 m/s kontrollü alçalma.
- [ ] REQ-CTRL-003: SİGMA kol açma/kilitleme kontrol dizisi.
- [ ] REQ-CTRL-005: Motor/servo komut üretimi + endpoint/açı limiti.
- [ ] REQ-SAFE-010: Motor PWM/RPM tutarsızlığı → motor arıza tespiti.
- [ ] EKSİK-001: `FlightControllerLink` somut MAVLink implementasyonu (ASSUMPTION-001).

## Aşama 3 — Görev & Bonus
- [ ] REQ-MISSION-006: Manuel ayrılma komutu servisi.
- [ ] REQ-SAFE-006: Manuel APAM komutu.
- [ ] REQ-BONUS-001: BONUS-1 Hovering (200 m, 10 sn, 0–1 m/s) kontrol modu.
- [ ] REQ-BONUS-002: BONUS-2 S2D-IOT RHRHRH al→SD→IoT yönlendirme + doğrulama.
- [ ] REQ-MISSION-010: Buzzer / kurtarma sesli ikaz; iniş sonrası TLM süre yönetimi.

## Aşama 4 — Haberleşme & Kayıt
- [ ] REQ-TLM-008: CRC/checksum doğrulama.
- [ ] REQ-TLM-009 / REQ-BONUS-003: Z.I.R.H store-and-forward tamponu.
- [ ] REQ-TLM-010: Kamera H.264 + 5 GHz Wi-Fi canlı akış, SD video.
- [ ] REQ-HW-003: LoRa E22 gerçek UART sürücüsü (ASSUMPTION-002 parametreleri).

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
