---
type: community
members: 80
---

# Mock Suruculer & Cekirdek

**Members:** 80 nodes

## Members
- [[.__init__()_1]] - code - src/common/result.py
- [[.__init__()_7]] - code - src/drivers/mock_sensors.py
- [[.__init__()_8]] - code - src/drivers/mock_sensors.py
- [[.__init__()_9]] - code - src/drivers/mock_sensors.py
- [[.__init__()_12]] - code - src/services/persistence.py
- [[.__repr__()]] - code - src/common/result.py
- [[._truth()]] - code - src/drivers/mock_sensors.py
- [[.err()]] - code - src/common/result.py
- [[.is_connected()]] - code - src/drivers/mock_sensors.py
- [[.is_err()]] - code - src/common/result.py
- [[.is_ok()]] - code - src/common/result.py
- [[.read()]] - code - src/drivers/mock_sensors.py
- [[.read()_1]] - code - src/drivers/mock_sensors.py
- [[.read()_2]] - code - src/drivers/mock_sensors.py
- [[.read()_3]] - code - src/drivers/mock_sensors.py
- [[.read()_4]] - code - src/hal/interfaces.py
- [[.read()_5]] - code - src/hal/interfaces.py
- [[.read()_6]] - code - src/hal/interfaces.py
- [[.read()_7]] - code - src/hal/interfaces.py
- [[.send()]] - code - src/drivers/mock_sensors.py
- [[.set_connected()]] - code - src/drivers/mock_sensors.py
- [[Açık, ayrıştırılabilir hata türleri. Metin mesaj yalnız tanılama içindir.]] - rationale - src/common/result.py
- [[Barometer]] - code - src/hal/interfaces.py
- [[BarometerReading]] - code - src/drivers/mock_sensors.py
- [[BarometerReading_1]] - code - src/hal/interfaces.py
- [[Battery]] - code - src/hal/interfaces.py
- [[BatteryReading]] - code - src/drivers/mock_sensors.py
- [[BatteryReading_1]] - code - src/hal/interfaces.py
- [[Başarılı bir değer VEYA açık bir hata taşır. Asla ikisini birden değil.]] - rationale - src/common/result.py
- [[Clock_1]] - code - src/common/clock.py
- [[Clock_2]] - code - src/drivers/mock_sensors.py
- [[Clock_3]] - code - src/services/persistence.py
- [[Diske yazılan kalıcı durum.]] - rationale - src/services/persistence.py
- [[ErrorCode]] - code - src/common/result.py
- [[FlightProfile]] - code - src/drivers/flight_profile.py
- [[FlightProfile_1]] - code - src/drivers/mock_sensors.py
- [[Gps]] - code - src/hal/interfaces.py
- [[GpsReading]] - code - src/drivers/mock_sensors.py
- [[GpsReading_1]] - code - src/hal/interfaces.py
- [[Görevi         Donanım Soyutlama Katmanı (HAL) arayüzleri. Sensör, aktüatör,]] - rationale - src/hal/interfaces.py
- [[Görevi         Kalıcı depo. Görev zamanı ve telemetri paket sayacını işlemci]] - rationale - src/services/persistence.py
- [[Görevi         Mock sensör sürücüleri (barometre, IMU, GPS, batarya, telemetri]] - rationale - src/drivers/mock_sensors.py
- [[Imu]] - code - src/hal/interfaces.py
- [[ImuReading]] - code - src/drivers/mock_sensors.py
- [[ImuReading_1]] - code - src/hal/interfaces.py
- [[LoRa E22 mock. Gönderileni tamponlar; bağlantı durumu kontrol edilebilir.]] - rationale - src/drivers/mock_sensors.py
- [[Mock sensör testleri (REQ-FUNC-001).]] - rationale - tests/test_mock_sensors.py
- [[MockBarometer]] - code - src/drivers/mock_sensors.py
- [[MockBattery]] - code - src/drivers/mock_sensors.py
- [[MockGps]] - code - src/drivers/mock_sensors.py
- [[MockImu]] - code - src/drivers/mock_sensors.py
- [[MockTelemetryLink]] - code - src/drivers/mock_sensors.py
- [[Ortak mod yönetimi ve zamangörev-zamanı erişimi.]] - rationale - src/drivers/mock_sensors.py
- [[PersistentState]] - code - src/services/persistence.py
- [[Protocol]] - code
- [[Result]] - code - src/common/result.py
- [[Result_2]] - code - src/drivers/mock_sensors.py
- [[SensorMode]] - code - src/drivers/mock_sensors.py
- [[Zaman kaynağı sözleşmesi.]] - rationale - src/common/clock.py
- [[Zaman tabanlı senaryo. Anahtar kareler (keyframe) arasında irtifa DOĞRUSAL     i]] - rationale - src/drivers/flight_profile.py
- [[_Base]] - code - src/drivers/mock_sensors.py
- [[_rig()]] - code - tests/test_mock_sensors.py
- [[bool_1]] - code - src/common/result.py
- [[bool_4]] - code - src/drivers/mock_sensors.py
- [[float_5]] - code - src/drivers/mock_sensors.py
- [[interfaces.py]] - code - src/hal/interfaces.py
- [[mock_sensors.py]] - code - src/drivers/mock_sensors.py
- [[persistence.py]] - code - src/services/persistence.py
- [[str_2]] - code - src/common/result.py
- [[str_5]] - code - src/drivers/mock_sensors.py
- [[str_7]] - code - src/services/persistence.py
- [[test_barometer_nominal()]] - code - tests/test_mock_sensors.py
- [[test_barometer_outlier()]] - code - tests/test_mock_sensors.py
- [[test_barometer_timeout()]] - code - tests/test_mock_sensors.py
- [[test_battery_discharges_over_time()]] - code - tests/test_mock_sensors.py
- [[test_gps_nominal_has_fix()]] - code - tests/test_mock_sensors.py
- [[test_gps_outlier_no_fix()]] - code - tests/test_mock_sensors.py
- [[test_imu_modes()]] - code - tests/test_mock_sensors.py
- [[test_link_loss_send_fails_but_is_reported()]] - code - tests/test_mock_sensors.py
- [[test_mock_sensors.py]] - code - tests/test_mock_sensors.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Mock_Suruculer__Cekirdek
SORT file.name ASC
```

## Connections to other communities
- 68 edges to [[_COMMUNITY_Ana Uygulama Dongusu]]
- 24 edges to [[_COMMUNITY_APAM Failsafe & Aktuator Baglami]]
- 23 edges to [[_COMMUNITY_Guvenli Aktuatorler]]
- 21 edges to [[_COMMUNITY_Saat & Kalicilik]]
- 19 edges to [[_COMMUNITY_HAL Arayuzleri]]
- 15 edges to [[_COMMUNITY_Telemetri Servisi & Paket]]
- 8 edges to [[_COMMUNITY_Result Hata Modeli]]
- 7 edges to [[_COMMUNITY_Ucus Profili Simulasyonu]]

## Top bridge nodes
- [[Result]] - degree 84, connects to 7 communities
- [[ErrorCode]] - degree 62, connects to 6 communities
- [[interfaces.py]] - degree 18, connects to 5 communities
- [[Clock_1]] - degree 40, connects to 2 communities
- [[FlightProfile]] - degree 37, connects to 2 communities