# Mimari (ARCHITECTURE)

## Katmanlı Mimari

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. UYGULAMA & GÖREV KATMANI                                        │
│    src/app/main.py            → sınırlı ana döngü (--max-cycles)   │
│    src/mission/mission_manager.py → görev orkestrasyonu           │
│    src/state_machine/         → uçuş durum makinesi + statü eşleme │
├──────────────────────────────────────────────────────────────────┤
│ 2. KONTROL & NAVİGASYON KATMANI  (Aşama 2)                         │
│    src/control/               → füzyon, PID, hovering (iskelet)    │
├──────────────────────────────────────────────────────────────────┤
│ 3. SERVİS KATMANI                                                  │
│    src/telemetry/packet.py    → 17 alanlı paket + ARAS hata kodu   │
│    src/telemetry/telemetry_service.py → CSV kayıt + (mock) gönderim│
│    src/services/persistence.py → restart-güvenli sayaç/zaman       │
│    src/services/health_monitor.py → veri yaşı/pil/link/döngü       │
│    src/services/failsafe.py   → APAM mantığı + safe state          │
│    src/services/command_service.py (Aşama 3)                       │
├──────────────────────────────────────────────────────────────────┤
│ 4. DONANIM SOYUTLAMA KATMANI (HAL)                                 │
│    src/hal/interfaces.py      → Sensor/Actuator/Link/Clock/Power   │
├──────────────────────────────────────────────────────────────────┤
│ 5. SÜRÜCÜ & SİMÜLASYON KATMANI                                     │
│    src/drivers/mock_sensors.py    → baro/imu/gps/battery/link      │
│    src/drivers/mock_actuators.py  → motor/servo/APAM/kol (güvenli) │
│    src/drivers/flight_profile.py  → deterministik uçuş simülasyonu │
├──────────────────────────────────────────────────────────────────┤
│ 0. ÇEKİRDEK (cross-cutting)                                        │
│    src/common/result.py  → Result/ErrorCode                       │
│    src/common/clock.py   → RealClock / FakeClock                   │
│    config/                → profiller ve parametreler             │
└──────────────────────────────────────────────────────────────────┘
```

## Tasarım İlkeleri
- **Bağımlılık yönü:** üst katmanlar alt katmanların **arayüzlerine** bağlıdır,
  somut sürücülere değil (Dependency Inversion). `main` bağımlılıkları enjekte eder.
- **Deterministik zaman:** her modül `Clock` arayüzünü kullanır; testte `FakeClock`.
- **Sessiz başarısızlık yok:** her G/Ç fonksiyonu `Result[T]` döndürür.
- **Güvenlik varsayılanı:** aktüatörler disarmed/safe başlar; SIMULATION_ONLY
  fiziksel çıkış üretmez.

## Uydu Statüsü Eşlemesi (iç durum → şartname kodu)
Şartname §2.4 (bağlayıcı):
| İç durum | Statü kodu | Anlam |
|----------|-----------|-------|
| BOOT, READY_TO_FLY | 0 | Uçuşa Hazır |
| ASCENT | 1 | Yükselme |
| CARRIER_DESCENT | 2 | Model Uydu İniş |
| SEPARATION, ARM_DEPLOY | 3 | Ayrılma |
| ACTIVE_DESCENT, HOVERING, FINAL_APPROACH, EMERGENCY_APAM | 4 | Görev Yükü İniş |
| LANDED, RECOVERY | 5 | Kurtarma |
| SAFE_MODE, FAULT | (mevcut faza göre; ayrılma öncesi 0/1) | — |

> CONFLICT-002: PDR s.62 tablosunda 2 ve 3 ters; ŞARTNAME esas alındı.
