# Gereksinim İzlenebilirlik Matrisi (REQUIREMENTS_TRACEABILITY)

Gereksinim → Tasarım/Kod → Test eşlemesi. Yalnız Aşama 1'de uygulanan öğeler
"Kod" ve "Test" sütunlarında dolu; diğerleri planlıdır (bkz. DEVELOPMENT_PLAN).

| REQ | Kaynak | Kod (Aşama 1) | Test | Durum |
|-----|--------|---------------|------|-------|
| REQ-SW-002 (SIMULATION_ONLY) | ANA_PROMPT | `config/default.py` | `test_config.py` | ✅ |
| REQ-SW-004 (test saati) | ANA_PROMPT | `src/common/clock.py` | `test_clock.py` | ✅ |
| REQ-SW-005 (sonuç modeli) | ANA_PROMPT | `src/common/result.py` | `test_result.py` | ✅ |
| REQ-TLM-003 (paket sayacı) | Şartname G-18 | `src/services/persistence.py` | `test_persistence.py` | ✅ |
| REQ-TLM-004 (görev zamanı) | Şartname G-17 | `src/services/persistence.py` | `test_persistence.py` | ✅ |
| REQ-TEST-002 (restart) | Şartname G-17/18 | `persistence.py` | `test_persistence.py::test_restart_*` | ✅ |
| REQ-TLM-001 (17 alan) | Şartname §2.4 | `src/telemetry/packet.py` | `test_telemetry_packet.py` | ✅ |
| REQ-TLM-006 (başlık/birim) | Şartname §2.4 NOT | `packet.py::csv_header/units` | `test_telemetry_packet.py` | ✅ |
| REQ-TEST-003 (örnek paket) | ANA_PROMPT | `packet.py` | `test_telemetry_packet.py::test_matches_pdr_example` | ✅ |
| REQ-TLM-007 (statü 0..5) | Şartname §2.4 | `state_machine` + `packet.SatelliteStatus` | `test_state_machine.py` | ✅ |
| REQ-TLM-011..015 (ARAS) | Şartname §2.2 | `packet.Aras` | `test_error_code.py` | ✅ |
| REQ-FUNC-001 (sensörler) | Şartname G-15 | `src/drivers/mock_sensors.py` | `test_mock_sensors.py` | ✅ (mock) |
| REQ-FUNC-004 (baro sıfır) | PDR s.90 | `config` + `flight_profile` | `test_telemetry_packet.py` | ✅ |
| REQ-SAFE-001 (safe state) | ANA_PROMPT | `src/drivers/mock_actuators.py` | `test_actuators.py` | ✅ |
| REQ-SAFE-002 (arm) | ANA_PROMPT | `mock_actuators.py` | `test_actuators.py::test_no_move_without_arm` | ✅ |
| REQ-SAFE-003 (16m/s×10s) | Şartname G-10 | `src/services/failsafe.py` | `test_failsafe_apam.py` | ✅ |
| REQ-SAFE-004 (>100 m) | Şartname G-10 | `failsafe.py` | `test_failsafe_apam.py::test_altitude_guard` | ✅ |
| REQ-SAFE-005 (motor kill sıra) | Şartname G-10 | `failsafe.py` | `test_failsafe_apam.py::test_motor_kill_before_chute` | ✅ |
| REQ-SAFE-007 (sayaç sıfır) | ANA_PROMPT | `failsafe.py` | `test_failsafe_apam.py::test_counter_reset` | ✅ |
| REQ-SAFE-008 (link loss) | ANA_PROMPT | `failsafe.py` | `test_failsafe_apam.py::test_link_loss_no_apam` | ✅ |
| REQ-SAFE-009 (sağlık) | ANA_PROMPT | `src/services/health_monitor.py` | `test_health_monitor.py` | ✅ |
| REQ-SW-003 (ana döngü) | ANA_PROMPT | `src/app/main.py` | `test_app_integration.py` | ✅ |
| REQ-SW-006 (max-cycles) | ANA_PROMPT | `src/app/main.py` | `test_app_integration.py` | ✅ |
| REQ-TLM-005 (SD/CSV) | Şartname G-19 | `src/telemetry/telemetry_service.py` | `test_app_integration.py` | ✅ (dosya) |
| REQ-CTRL-001 (füzyon) | ANA_PROMPT §context | `src/control/estimator.py` | `test_estimator.py` | ✅ Aşama 2 |
| REQ-CTRL-002 (8–10 m/s PID) | Şartname G-9 | `src/control/{pid,descent_controller}.py` | `test_pid.py`, `test_descent_controller.py` | ✅ Aşama 2 |
| REQ-CTRL-005 (motor komut+limit) | PDR s.6 | `descent_controller.py` + `mock_actuators` | `test_descent_controller.py` | ✅ Aşama 2 |
| REQ-SAFE-010 (PWM/RPM arıza) | ANA_PROMPT APAM | `src/services/motor_health.py` | `test_motor_health.py`, `test_app_integration.py` | ✅ Aşama 2 |
| EKSİK-001 (FC link) | PDR (yok) | `src/drivers/sim_flight_controller.py` | `test_sim_flight_controller.py` | ✅ (sim) Aşama 2 |
| APAM çoklu-sensör filtresi | ANA_PROMPT APAM | `failsafe.py` + `estimator.speed_consistent` | `test_failsafe_apam.py` | ✅ Aşama 2 |
| REQ-CTRL-003 (kol dizisi) | PDR SİGMA | `main.py` (deploy_and_lock) | `test_app_integration.py` | ◑ kısmi (Aşama 4'te olgunlaşır) |
| REQ-CTRL-004 (Hovering) | Şartname G-36 | `descent_controller` + state machine timer | `test_descent_controller.py` | ✅ Aşama 3 |
| REQ-MISSION-006 (manuel ayrılma) | Şartname G-7 | `command_service.py` + `main.py` | `test_command_service.py`, `test_app_integration.py` | ✅ Aşama 3 |
| REQ-SAFE-006 (manuel APAM) | Şartname G-10 | `command_service.py` + `failsafe.py` | `test_command_service.py`, `test_app_integration.py` | ✅ Aşama 3 |
| REQ-MISSION-010 (buzzer) | Şartname G-28 | `src/services/recovery.py` | `test_recovery.py`, `test_app_integration.py` | ✅ Aşama 3 |
| REQ-BONUS-001 (Hovering) | Şartname G-36 | `flight_state_machine` (hover timer) | `test_state_machine.py` | ✅ Aşama 3 |
| REQ-BONUS-002 (S2D-IOT) | Şartname §2.3 | `src/services/{s2d_iot,command_service}.py` | `test_s2d_iot.py`, `test_command_service.py` | ✅ Aşama 3 |
| CONFLICT-001 (iniş sonrası TLM) | Şartname G-27/§1.3 | `recovery.py` (config penceresi) | `test_recovery.py` | ✅ Aşama 3 (config'e alındı) |
| REQ-TLM-008 (CRC) | PDR test planı | `src/telemetry/framing.py` | `test_framing.py` | ✅ Aşama 4 |
| REQ-TLM-009 / REQ-BONUS-003 (Z.I.R.H) | Şartname G-38 | `src/services/store_forward.py` | `test_store_forward.py`, `test_app_integration.py` | ✅ Aşama 4 |
| REQ-TLM-010 (video) | Şartname G-20/22 | `src/services/camera_service.py`, `mock_camera.py` | `test_camera.py`, `test_app_integration.py` | ✅ Aşama 4 (sim) |
| REQ-HW-003 (LoRa gerçek UART) | PDR s.6 | `src/drivers/real_lora.py` + `factory.py` | `test_driver_factory.py` | ◑ iskelet+gate hazır; seri I/O saha testi (donanım) |
| REQ-FUNC-004 (baro saha kalib.) | PDR s.90 | `src/services/calibration.py` | `test_calibration.py` | ✅ Aşama 5 |
| FRR preflight gate | Şartname §4.2 | `src/services/preflight.py` | `test_preflight.py`, `test_app_integration.py` | ✅ Aşama 5 |
| REQ-TEST-005 (FRR titreşim, yazılım analoğu) | Şartname §4.2 | vibration inj. + `main.py` | `test_vibration.py` | ✅ (sim analoğu); fiziksel test donanım gerekli |
| REQ-TEST-005 (FRR fiziksel: 10G/titreşim/düşme) | Şartname §4.2 | — (prosedür belgelendi) | — | ⏳ Donanım/laboratuvar (bkz. FRR_TEST_PROCEDURES.md) |
| EKSİK-001 (gerçek MAVLink) | PDR (yok) | — (soyut link hazır) | — | ⏳ Donanım (FC gerekli) |
