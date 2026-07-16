# Modül Tasarımı (MODULE_DESIGN)

Her kaynak dosyanın başında 4 bilgi bulunur: Görevi, Neden Gerekli, İlişkiler,
Nasıl Test Edilir. Aşağıda modül sözleşmeleri özetlenmiştir.

## src/common/result.py
- `ErrorCode` (enum): OK, TIMEOUT, INVALID_DATA, SAFETY_INTERLOCK, NOT_ARMED,
  IO_ERROR, OUT_OF_RANGE, NOT_FOUND, UNAVAILABLE.
- `Result[T]`: `ok(value)` / `err(code, message)`; `.is_ok`, `.unwrap()`.

## src/common/clock.py
- `Clock` (Protocol): `now_monotonic()->float`, `now_utc()->datetime`.
- `RealClock`, `FakeClock(advance/set_utc)`.

## config/
- `default.py`: `AppConfig` veri sınıfı ve `SIMULATION` profili (varsayılan).
  Parametreler: `team_number=947450`, APAM (`apam_speed_mps=16`,
  `apam_duration_s=10`, `apam_min_altitude_m=100`), `telemetry_hz=1`,
  `error_code_digits=4` (CONFLICT-003), `post_landing_telemetry_s=10`
  (CONFLICT-001), `carrier_descent_speed_range=(12,16)` (CONFLICT-004), sağlık
  eşikleri, dosya yolları.

## src/services/persistence.py
- `PersistentState`: `packet_number`, `mission_time_offset_s`, `boot_count`.
- `PersistenceStore(path, clock)`: `load()`, `next_packet_number()`,
  `mission_time_s()`, atomik `_save()`. Restart'ta kaldığı yerden.

## src/telemetry/packet.py
- `TelemetryFields` (17 alan veri sınıfı).
- `SatelliteStatus` (enum 0..5).
- `Aras.compute(...)->str`: Bit1..Bit4, `error_code_digits` genişliğinde.
- `TelemetryPacket.build(fields)->str` (CSV satırı), `csv_header()`, `csv_units()`.
- Örnek paketle birebir format doğrulaması test edilir.

## src/hal/interfaces.py
- `SensorReading` (değer + timestamp). `BarometerSensor`, `ImuSensor`, `GpsSensor`,
  `BatterySensor`, `LinkStatus`, `Actuator`, `MotorGroup`, `ServoActuator`,
  `FlightControllerLink` (Protocol arayüzleri).

## src/drivers/mock_sensors.py
- `flight_profile.py`'den beslenen deterministik mock'lar; `set_mode(nominal/
  outlier/timeout)`.

## src/drivers/mock_actuators.py
- `MockMotorGroup`, `MockServo`, `MockArmMechanism`: arm/disarm, safe state,
  komut logu; SIMULATION_ONLY'de fiziksel çıkış yok.

## src/state_machine/flight_state_machine.py
- `FlightPhase` (enum: BOOT..FAULT). `FlightStateMachine.update(ctx)`.
- `status_code()` → şartname 0..5.

## src/services/health_monitor.py
- `HealthMonitor.evaluate(snapshot, clock)->HealthReport(flags)`.

## src/services/failsafe.py
- `FailsafeManager.update(ctx)->FailsafeDecision`. APAM sayaç/eşik/sıralama.

## src/app/main.py
- `run(config, max_cycles, duration)`; bağımlılık enjeksiyonu; sınırlı döngü;
  döngü aşımı tespiti; her çevrim telemetri üretimi.
