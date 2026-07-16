---
source_file: "src/app/main.py"
type: "code"
community: "Ana Uygulama Dongusu"
location: "L57"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Ana_Uygulama_Dongusu
---

# SimClock

## Connections
- [[ActuatorSuite]] - `uses` [INFERRED]
- [[AppConfig]] - `uses` [INFERRED]
- [[ArasInputs]] - `uses` [INFERRED]
- [[Clock_1]] - `uses` [INFERRED]
- [[FailsafeManager]] - `uses` [INFERRED]
- [[FakeClock]] - `uses` [INFERRED]
- [[FlightContext]] - `uses` [INFERRED]
- [[FlightPhase]] - `uses` [INFERRED]
- [[FlightProfile]] - `uses` [INFERRED]
- [[FlightStateMachine]] - `uses` [INFERRED]
- [[HealthInputs]] - `uses` [INFERRED]
- [[HealthMonitor]] - `uses` [INFERRED]
- [[MockBarometer]] - `uses` [INFERRED]
- [[MockBattery]] - `uses` [INFERRED]
- [[MockGps]] - `uses` [INFERRED]
- [[MockImu]] - `uses` [INFERRED]
- [[MockTelemetryLink]] - `uses` [INFERRED]
- [[PersistenceStore]] - `uses` [INFERRED]
- [[ServoPosition_1]] - `uses` [INFERRED]
- [[Simülasyon saati gerçek zaman beklemeden her çevrimde ilerletilir.]] - `rationale_for` [EXTRACTED]
- [[TelemetryFields]] - `uses` [INFERRED]
- [[TelemetryPacketBuilder]] - `uses` [INFERRED]
- [[TelemetryService]] - `uses` [INFERRED]
- [[build_and_run()]] - `calls` [EXTRACTED]
- [[main.py]] - `contains` [EXTRACTED]
- [[test_app_integration.py]] - `imports` [EXTRACTED]
- [[test_bounded_run_respects_max_cycles()]] - `calls` [EXTRACTED]
- [[test_deterministic_repeatable()]] - `calls` [EXTRACTED]
- [[test_nominal_reaches_descent_or_landing()]] - `calls` [EXTRACTED]
- [[test_run_produces_packets_and_csv()]] - `calls` [EXTRACTED]
- [[test_runaway_profile_triggers_apam()]] - `calls` [EXTRACTED]
- [[test_safe_state_no_motor_output_in_simulation()]] - `calls` [EXTRACTED]
- [[test_telemetry_is_1hz()]] - `calls` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Ana_Uygulama_Dongusu