# Donanım Devreye Alma Kılavuzu (HARDWARE_BRINGUP)

Bu belge, simülasyonda doğrulanmış uçuş yazılımını (SIMULATION_ONLY) gerçek
**Raspberry Pi 5 + PixMin/STM32** donanımına taşıma sürecini adım adım anlatır.
Hedef: mock sürücüleri gerçek sürücülerle değiştirmek ve güvenli bir devreye alma
sırası izleyerek uçuşa hazır hale gelmek.

> ⚠️ **GÜVENLİK — ÖNCE OKU**
> - Pervaneli hiçbir motoru **kapalı alanda / eller yakınında** çalıştırma.
> - Her aşamada varsayılan profil `SIMULATION_ONLY`'dir; `FLIGHT` profiline yalnız
>   tezgah testleri geçtikten sonra geç.
> - Motor testlerini **pervaneler sökülüyken** yap. Arm interlock (`REQ-SAFE-002`)
>   yazılım koruması; tek güvenlik katmanı değildir — pil/ESC güç anahtarını da kullan.
> - APAM servosunu test ederken paraşütü **elle tutarak** aç; sistem başında ve
>   hatada aktüatörler Safe State'e döner (`enter_safe_state`).

---

## 0. Nerede duruyoruz
- Kod tabanı **RPi 5 üzerindeki üst-seviye Görev Yazılımıdır** (ADR-001).
- Tüm sürücüler şu an **mock** (`src/drivers/mock_*.py`); HAL arayüzleri
  (`src/hal/interfaces.py`) gerçek sürücülerin uyacağı sözleşmeyi tanımlar.
- `src/drivers/factory.py` profile göre sürücü seçer; `FLIGHT`/`HIL` profili şu an
  donanım kütüphanesi yoksa **açık hata** verir (sessiz mock'a düşmez).
- Yapılacak asıl iş: her HAL arayüzü için **gerçek I/O implementasyonu** yazmak.

---

## 1. Donanım envanteri (PDR — doğrulanmış)
| Bileşen | Model | Arayüz | Nereye bağlı |
|---------|-------|--------|--------------|
| Görev bilgisayarı | Raspberry Pi 5 4GB | — | ana kart |
| Uçuş kontrol kartı | PixMin V1.0 / STM32F405 | UART/SPI (MAVLink öner.) | RPi ↔ FC |
| Sıcaklık/Basınç | BME280 (yedek BMP280) | I²C | RPi doğrudan |
| Basınç (yedek) | LPS22HB | (Pixhawk üzerinde) | FC üzerinden |
| IMU/Gyro | MPU6500 (yedek ICM-20948) | (Pixhawk üzerinde) | FC üzerinden |
| Manyetometre | IST8310 / QMC5883L | I²C | RPi/FC |
| GPS | u-blox M8N | UART | RPi doğrudan |
| Telemetri | LoRa E22 900T22D | UART (868 MHz) | RPi doğrudan |
| PWM sürücü | PCA9685 | I²C | servolar |
| Motorlar | 4× Emax ECO II 2207 1700KV | ESC PWM | FC (PID) |
| ESC | BlHeli 45A (4in1) | — | FC |
| Servolar | SG90 / ES08MA2 | PWM (PCA9685/FC) | ayrılma, APAM, kol |
| Kamera | Pi Camera V2 NoIR | CSI | RPi |
| Pil gerilimi | ADC / MAX471 | ADC | RPi |
| Güç | 4S LiPo (SİGMA), 18650 (aviyonik) | — | — |

**Mimari notu:** LPS22HB baro ve MPU6500 IMU **Pixhawk üzerindedir**; bunların
verisi RPi'ye `FlightControllerLink` (MAVLink, `ASSUMPTION-001`) üzerinden gelir.
BME280, GPS ve LoRa **doğrudan RPi'ye** bağlıdır. Bu, hangi sürücünün doğrudan I²C/
UART, hangisinin FC-link üzerinden olacağını belirler.

---

## 2. Kodu Pi'ye alma
```bash
# Raspberry Pi 5 (RPi OS Bookworm 64-bit) terminali:
git clone https://github.com/tunaerray/kilavuz-mirasat-fsw.git
cd kilavuz-mirasat-fsw
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q            # sim testleri donanımsız da yeşil olmalı (~234 test)
python -m src.app.main --config simulation --max-cycles 100   # sim çalışıyor mu
```
Güncellemeler için: `git pull`. Kendi değişikliklerini bir dala (`git checkout -b
hw-drivers`) yapıp PR açman önerilir (CI otomatik koşar).

### Pi arayüzlerini etkinleştir
```bash
sudo raspi-config      # Interface Options → I2C: ON, SPI: ON, Serial(UART): ON (login shell OFF), Camera: ON
sudo apt install -y i2c-tools python3-libgpiod
i2cdetect -y 1         # bağlı I²C cihazlarının adreslerini gör (BME280 0x76/0x77, PCA9685 0x40 vb.)
```

### Donanım bağımlılıkları
```bash
pip install -r requirements-hardware.txt   # pyserial, pymavlink, smbus2
pip install picamera2                       # kamera (RPi OS'ta genelde kurulu)
```

---

## 3. Gerçek sürücüleri yazma
HAL arayüzleri sözleşmedir; **her mock için** aynı arayüzü uygulayan bir gerçek
sürücü yaz. Her sürücü `Result` döndürmeli (sessiz başarısızlık yok) ve donanım/
kütüphane yoksa `ErrorCode.UNAVAILABLE` ile **güvenli degrade** etmeli — desen
`src/drivers/real_lora.py`'de mevcuttur (örnek al).

| Mock (değiştir) | Gerçek sürücü (yaz) | HAL arayüzü | Yol |
|-----------------|---------------------|-------------|-----|
| `MockBarometer` | `RealBme280` | `Barometer` | I²C (smbus2), adres 0x76 |
| `MockImu` | FC-link'ten oku | `Imu`/`FlightControllerLink` | MAVLink ATTITUDE |
| `MockGps` | `RealUbloxM8N` | `Gps` | UART (pyserial, NMEA/UBX) |
| `MockBattery` | `RealAdcBattery` | `Battery` | ADC (MAX471) |
| `MockTelemetryLink` | `RealLoraE22Link` ✅ iskelet var | `TelemetryLink` | UART |
| `MockMotorGroup`/`MockServo` | FC-link setpoint / PCA9685 | `MotorGroup`/`Servo` | MAVLink / I²C |
| `SimulatedFlightControllerLink` | `MavlinkFlightControllerLink` | `FlightControllerLink` | pymavlink |
| `MockCamera`/`MockWifiVideoLink` | `Picamera2Recorder` | `Camera`/`VideoStreamLink` | CSI + H.264 |

**Sürücü yazma deseni** (her biri için):
1. `src/hal/interfaces.py`'deki ilgili `Protocol`'ü aç, metod imzalarını al.
2. `src/drivers/real_<x>.py` oluştur; `__init__`'te donanım kaynağını **açma** (lazy);
   ayrı bir `open()`/`start()` ile aç, hata varsa `Result.err(UNAVAILABLE/IO_ERROR)`.
3. Okuma metodları donanım okur, HAL veri sınıfına (ör. `BarometerReading`) çevirir,
   `timestamp_s`'i `Clock.now_monotonic()` ile doldurur.
4. Her yeni sürücü için birim test yaz (donanımsız CI'da **güvenli degrade**yi test et;
   gerçek I/O'yu Pi'de manuel doğrula — `docs/FRR_TEST_PROCEDURES.md`).

**Sürücü fabrikasına bağla** (`src/drivers/factory.py`): şu an yalnız telemetri linki
seçiliyor; sensör/aktüatör/kamera için de profil bazlı seçim ekle. `SIMULATION_ONLY`
→ mock; `HIL`/`FLIGHT` → gerçek. Ana döngü (`src/app/main.py`) sürücüleri doğrudan
`Mock*` sınıfından kurmak yerine fabrikadan almalı (tek değişiklik noktası).

### RPi ↔ PixMin (EKSİK-001)
Protokol PDR'de belirtilmemiş; **MAVLink önerilir** (`ASSUMPTION-001`). `pymavlink`
ile `MavlinkFlightControllerLink`:
- `read_telemetry()` → `ATTITUDE` (pitch/roll/yaw) + `ESC_STATUS`/`RPM` (motor rpm).
- `send_setpoint()` → throttle/hedef irtifa (ör. `MANUAL_CONTROL` veya özel mesaj).
- Not: yüksek frekanslı stabilizasyon PID'i **PixMin/STM32'de** kalır; RPi yalnız
  üst-seviye setpoint gönderir (ADR-001). CDR'da protokol netleştirilmeli.

---

## 4. Yapılandırma (config)
`config/default.py`:
- `RunProfile`: `SIMULATION_ONLY` (varsayılan) → tezgah sonrası `HARDWARE_IN_THE_LOOP`
  → uçuşta `FLIGHT`.
- `PathsConfig`: SD kart montaj yolları (telemetri CSV, S2D, Z.I.R.H, video) SD'ye
  yönlendir (ör. `/media/sd/...`).
- Seri portlar: LoRa/GPS için gerçek portlar (`/dev/ttyAMA0`, `/dev/ttyUSB0`).
- `ControlConfig`: PID kazançları **gerçek araçta** yeniden ayarlanmalı; sim değerleri
  başlangıç noktasıdır (motor_max_rpm, hover_throttle vb. gerçek ölçümle güncelle).
- `HealthConfig`: `preflight_min_voltage_v`, GPS min uydu, batarya eşikleri saha
  koşullarına göre gözden geçir.

---

## 5. Devreye alma SIRASI (güvenlik kapıları)
Her aşama geçmeden bir sonrakine geçme.

### Aşama A — Tezgah, sensörler (motorsuz)
1. `i2cdetect`/`dmesg` ile her cihaz görünüyor mu.
2. Her gerçek sensör sürücüsünü tek tek çalıştır; makul değer okuyor mu (baro basınç,
   IMU açı, GPS 6+ uydu kilidi, batarya gerilimi).
3. `python -m src.app.main --preflight` (HIL profili, motorlar pasif) → **GO** almalı.

### Aşama B — Tezgah, aktüatörler (PERVANESİZ)
1. Servoları tek tek: ayrılma servosu OPEN/LOCKED, APAM servosu (paraşüt elde), kol
   mekanizması aç/kilitle. Endpoint/açı limitlerini doğrula.
2. Motorları **pervanesiz**, düşük throttle: arm interlock çalışıyor mu (arm olmadan
   dönmemeli), kill komutu anında durduruyor mu, RPM geri bildirimi geliyor mu.
3. Motor PWM/RPM tutarlılık (`MotorHealthMonitor`) gerçek RPM ile doğrula.

### Aşama C — HIL (Hardware-in-the-loop)
1. `HARDWARE_IN_THE_LOOP` profili: gerçek sensörler + FC bağlı, **motorlar disarm**.
2. Tam görev döngüsünü koştur: 1 Hz telemetri + CRC yer istasyonunda alınıyor mu,
   SD kaydı, canlı video, komut (manuel ayrılma/APAM, RHRHRH), Z.I.R.H senaryosu.
3. Saha baro kalibrasyonu (`BaroCalibrator`, kalkış = 0 m) — gerçek basınçla.

### Aşama D — Tethered / kısa sıçrama
1. Açık alanda, bağlı/korumalı, pervaneli **ilk** motor testleri.
2. Kontrollü alçalma PID'ini gerçek araçta ayarla (8–10 m/s).

### Aşama E — Fiziksel FRR testleri
`docs/FRR_TEST_PROCEDURES.md`: 10G şok, 150–200 Hz titreşim masası, düşme, yer
istasyonundan ayrılma komutu. Bu testler **laboratuvar/saha ekipmanı** gerektirir.

---

## 6. Uçuş öncesi (her uçuşta)
`docs/PREFLIGHT_CHECKLIST.md`'i uygula. Kısaca:
```bash
python -m src.app.main --preflight     # GO/NO-GO kapısı
```
GO alınmadan uçma. Baro sahada sıfırlanır (çok örnekli kalibrasyon, kalıcı referans).

---

## 7. Sorun giderme
- **I²C cihaz görünmüyor:** `i2cdetect -y 1`; kablo/pull-up; `raspi-config` I2C açık mı.
- **Seri veri yok:** `raspi-config` login-shell KAPALI, UART AÇIK; doğru port; baud
  (`TelemetryConfig.lora_baud`).
- **GPS kilit yok:** açık gökyüzü, anten yönü; NMEA akıyor mu (`cat /dev/ttyUSB0`).
- **FC bağlanmıyor:** MAVLink baud/port; `mavproxy` ile bağlantıyı ayrı doğrula.
- **Preflight NO-GO:** rapordaki başarısız maddeyi gider (batarya/GPS/sensör/aktüatör).

---

## 8. Özet iş listesi (donanım fazı)
- [ ] Pi hazırlığı (OS, arayüzler, deps, `git clone`, sim testleri yeşil)
- [ ] Gerçek sürücüler: BME280, GPS, ADC batarya, LoRa (iskelet var), FC-link (MAVLink),
      PCA9685 servo, kamera
- [ ] `factory.py`'yi tüm sürücüler için genişlet; `main.py` sürücüleri fabrikadan alsın
- [ ] Her sürücü için güvenli-degrade birim testi (CI) + Pi'de manuel I/O doğrulama
- [ ] Config: profiller, portlar, SD yolları, gerçek PID kazançları
- [ ] Devreye alma A→E sırası, her kapıda go/no-go
- [ ] FRR fiziksel testleri (laboratuvar)

> Bu belgedeki yazılım-tarafı adımlar mevcut mimariyle uyumludur; **gerçek I/O
> kodu ve fiziksel testler donanım elde olduğunda, Pi üzerinde** yapılır ve orada
> doğrulanır (bu simülasyon ortamında çalıştırılamaz).
