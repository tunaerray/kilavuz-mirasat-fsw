---
source_file: "src/services/failsafe.py"
type: "code"
community: "APAM Failsafe & Aktuator Baglami"
location: "L43"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/APAM_Failsafe__Aktuator_Baglami
---

# FailsafeManager

## Connections
- [[.__init__()_10]] - `method` [EXTRACTED]
- [[.apam_active()]] - `method` [EXTRACTED]
- [[.execute_apam()]] - `method` [EXTRACTED]
- [[.overspeed_timer_s()]] - `method` [EXTRACTED]
- [[.parachute_deployed()]] - `method` [EXTRACTED]
- [[.update()]] - `method` [EXTRACTED]
- [[APAM durum makinesi. Bir kez tetiklenince (latch) motor kill ve paraşüt     açma]] - `rationale_for` [EXTRACTED]
- [[ActuatorSuite]] - `uses` [INFERRED]
- [[ApamConfig]] - `uses` [INFERRED]
- [[AppConfig_1]] - `uses` [INFERRED]
- [[Clock]] - `uses` [INFERRED]
- [[ErrorCode]] - `uses` [INFERRED]
- [[FlightContext]] - `uses` [INFERRED]
- [[Result]] - `uses` [INFERRED]
- [[RunSummary]] - `uses` [INFERRED]
- [[ServoPosition_1]] - `uses` [INFERRED]
- [[SimClock]] - `uses` [INFERRED]
- [[build_and_run()]] - `calls` [EXTRACTED]
- [[failsafe.py]] - `contains` [EXTRACTED]
- [[float_1]] - `uses` [INFERRED]
- [[int]] - `uses` [INFERRED]
- [[main.py]] - `imports` [EXTRACTED]
- [[str_1]] - `uses` [INFERRED]
- [[test_altitude_guard_below_100m_no_deploy()]] - `calls` [EXTRACTED]
- [[test_apam_latches_active()]] - `calls` [EXTRACTED]
- [[test_counter_resets_when_speed_safe()]] - `calls` [EXTRACTED]
- [[test_execute_apam_kills_motors_before_parachute()]] - `calls` [EXTRACTED]
- [[test_failsafe_apam.py]] - `imports` [EXTRACTED]
- [[test_link_loss_alone_does_not_trigger()]] - `calls` [EXTRACTED]
- [[test_manual_apam_blocked_below_100m()]] - `calls` [EXTRACTED]
- [[test_manual_apam_triggers_above_100m()]] - `calls` [EXTRACTED]
- [[test_no_trigger_before_10s()]] - `calls` [EXTRACTED]
- [[test_no_trigger_during_ascent()]] - `calls` [EXTRACTED]
- [[test_triggers_after_16mps_10s()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/APAM_Failsafe__Aktuator_Baglami