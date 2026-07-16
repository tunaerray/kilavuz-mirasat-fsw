# Veri Akışı (DATA_FLOW)

## Ana Döngü Veri Akışı (her çevrim)
```
        ┌─────────────┐
        │  Clock.now  │  (RealClock / FakeClock)
        └──────┬──────┘
               ▼
   ┌────────────────────────┐
   │ Sensörleri oku (HAL)   │  baro, imu, gps, battery, link
   │  → SensorSnapshot      │  (her biri Result[...])
   └───────────┬────────────┘
               ▼
   ┌────────────────────────┐
   │ HealthMonitor.evaluate │  veri yaşı, pil, link, döngü gecikmesi
   │  → HealthReport        │
   └───────────┬────────────┘
               ▼
   ┌────────────────────────┐
   │ FailsafeManager.update │  APAM sayaç/eşik; motor-kill sıralaması
   │  → FailsafeDecision     │
   └───────────┬────────────┘
               ▼
   ┌────────────────────────┐
   │ StateMachine.update    │  faz geçişleri; statü kodu (0..5)
   │  → FlightState         │
   └───────────┬────────────┘
               ▼
   ┌────────────────────────┐
   │ Aras.compute_error_code│  Bit1..Bit4 → "0000"
   └───────────┬────────────┘
               ▼
   ┌────────────────────────┐
   │ Persistence: paket no++ │  (atomik yazma)
   │ TelemetryPacket.build   │  17 alan, tam sıra
   └───────────┬────────────┘
               ▼
   ┌────────────────────────┐
   │ TelemetryService        │  CSV'ye yaz + (mock) RF gönder
   └────────────────────────┘
```

## Telemetri Kaydı (SD/CSV) Düzeni
İlk iki satır başlık ve birim (şartname %2 kesinti önlemi):
```
PAKET_NUMARASI,UYDU_STATUSU,HATA_KODU,GONDERME_SAATI,BASINC,YUKSEKLIK,INIS_HIZI,SICAKLIK,PIL_GERILIMI,GPS_LATITUDE,GPS_LONGITUDE,GPS_ALTITUDE,PITCH,ROLL,YAW,RHRHRH,TAKIM_NO
-,-,-,GG/AA/YYYY SS:DD:ss,Pa,m,m/s,C,V,derece,derece,m,derece,derece,derece,-,-
152,4,0000,04/05/2026 14:32:10,91234.5,748.2,8.7,28.4,11.4,39.9255,32.8662,985.3,5.2,-3.1,120.6,2R0G1B,947450
```
Not: RF hattında gönderilen satır alan-ayracı ile aynı sıradadır (başlık satırları
yalnız dosyada). Ondalık ayracı nokta.

## Kalıcılık Akışı (restart dayanımı)
```
Her paket üretiminde: state = {packet_no, mission_epoch_offset, last_utc}
  → JSON tmp dosyaya yaz → os.replace (atomik) → gerçek dosya
Başlangıçta: dosya varsa yükle → packet_no ve mission time kaldığı yerden.
```

## İşlemciler Arası (RPi ↔ PixMin) — mantıksal
```
RPi (bu FSW) ──FlightControllerLink──▶ PixMin/STM32
  gönderir: setpoint (hedef irtifa/hız, throttle, arm/disarm, kol aç, motor-kill)
  alır:     attitude (pitch/roll/yaw), rpm geri bildirim, FC sağlık
Protokol: ASSUMPTION-001 (MAVLink); Aşama 2/HAL'de somutlaşır.
```
