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
| REQ-CTRL-003 (kol dizisi) | PDR SİGMA | `main.py` (deploy_and_lock) | `test_app_integration.py` | ◑ kısmi (Aşama 3 tamamlanır) |
| REQ-CTRL-004 (Hovering) | Şartname G-36 | `descent_controller` (hover modu hazır) | `test_descent_controller.py` | ◑ mod hazır, faz Aşama 3 |
| REQ-BONUS-* | Şartname §2.3,G-36,38 | — | — | ⏳ Aşama 3/4 |
| REQ-TLM-008/009/010 | PDR/Şartname | — | — | ⏳ Aşama 4 |
| EKSİK-001 (gerçek MAVLink) | PDR (yok) | — | — | ⏳ Aşama 5 (donanım) |
| REQ-TEST-005 (FRR) | Şartname §4.2 | — | — | ⏳ Aşama 5 |
