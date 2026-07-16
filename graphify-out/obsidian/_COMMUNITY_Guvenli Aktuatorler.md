---
type: community
members: 46
---

# Guvenli Aktuatorler

**Members:** 46 nodes

## Members
- [[.__init__()_3]] - code - src/drivers/mock_actuators.py
- [[.__init__()_4]] - code - src/drivers/mock_actuators.py
- [[.__init__()_5]] - code - src/drivers/mock_actuators.py
- [[.__init__()_6]] - code - src/drivers/mock_actuators.py
- [[.arm()]] - code - src/drivers/mock_actuators.py
- [[.arm_state()]] - code - src/drivers/mock_actuators.py
- [[.deploy_and_lock()]] - code - src/drivers/mock_actuators.py
- [[.deployed()]] - code - src/drivers/mock_actuators.py
- [[.disarm()]] - code - src/drivers/mock_actuators.py
- [[.enter_safe_state()]] - code - src/drivers/mock_actuators.py
- [[.kill()]] - code - src/drivers/mock_actuators.py
- [[.locked()]] - code - src/drivers/mock_actuators.py
- [[.move_to()]] - code - src/drivers/mock_actuators.py
- [[.position()]] - code - src/drivers/mock_actuators.py
- [[.set_throttle()]] - code - src/drivers/mock_actuators.py
- [[.throttle()]] - code - src/drivers/mock_actuators.py
- [[.to_safe()]] - code - src/drivers/mock_actuators.py
- [[.to_safe()_1]] - code - src/drivers/mock_actuators.py
- [[4× fırçasız motor. Throttle 0..1. Arm interlock ve kill destekli.]] - rationale - src/drivers/mock_actuators.py
- [[ArmState]] - code - src/drivers/mock_actuators.py
- [[ArmState_1]] - code - src/hal/interfaces.py
- [[Ayrılma  APAM paraşüt kapağı  kol servosu. Güvenli konuma geçebilir.]] - rationale - src/drivers/mock_actuators.py
- [[Görevi         Güvenli mock aktüatörler (4× motor grubu, ayrılma servosu, APAM]] - rationale - src/drivers/mock_actuators.py
- [[Güvenli aktüatör testleri (REQ-SAFE-001002).]] - rationale - tests/test_actuators.py
- [[Kolları 90° açar ve kilitler (ayrılma → aktif iniş arası).]] - rationale - src/drivers/mock_actuators.py
- [[MockArmMechanism]] - code - src/drivers/mock_actuators.py
- [[MockMotorGroup]] - code - src/drivers/mock_actuators.py
- [[MockServo]] - code - src/drivers/mock_actuators.py
- [[Motor kill gaz 0 + disarm. Paraşüt açılmadan HEMEN ÖNCE çağrılır.]] - rationale - src/drivers/mock_actuators.py
- [[Result_1]] - code - src/drivers/mock_actuators.py
- [[Safe State mevcut konumda kilitli kalır (kolları geri katlamaz).]] - rationale - src/drivers/mock_actuators.py
- [[Safe State motorlar disarm0, servolar güvenli konum, kollar kilitli.         B]] - rationale - src/drivers/mock_actuators.py
- [[ServoPosition]] - code - src/drivers/mock_actuators.py
- [[SİGMA kol açmakilitleme mekanizması. Başlangıçta gövde içinde KAPALIkilitli;]] - rationale - src/drivers/mock_actuators.py
- [[bool_3]] - code - src/drivers/mock_actuators.py
- [[float_4]] - code - src/drivers/mock_actuators.py
- [[mock_actuators.py]] - code - src/drivers/mock_actuators.py
- [[str_4]] - code - src/drivers/mock_actuators.py
- [[test_actuators.py]] - code - tests/test_actuators.py
- [[test_arm_mechanism_deploy_and_lock()]] - code - tests/test_actuators.py
- [[test_kill_disarms_and_zeros()]] - code - tests/test_actuators.py
- [[test_motor_starts_disarmed_zero()]] - code - tests/test_actuators.py
- [[test_no_throttle_without_arm()]] - code - tests/test_actuators.py
- [[test_suite_safe_state()]] - code - tests/test_actuators.py
- [[test_throttle_after_arm()]] - code - tests/test_actuators.py
- [[test_throttle_out_of_range_rejected()]] - code - tests/test_actuators.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Guvenli_Aktuatorler
SORT file.name ASC
```

## Connections to other communities
- 23 edges to [[_COMMUNITY_Mock Suruculer & Cekirdek]]
- 19 edges to [[_COMMUNITY_APAM Failsafe & Aktuator Baglami]]
- 1 edge to [[_COMMUNITY_Ana Uygulama Dongusu]]
- 1 edge to [[_COMMUNITY_HAL Arayuzleri]]

## Top bridge nodes
- [[ArmState_1]] - degree 17, connects to 4 communities
- [[MockMotorGroup]] - degree 20, connects to 2 communities
- [[Result_1]] - degree 13, connects to 2 communities
- [[test_actuators.py]] - degree 13, connects to 2 communities
- [[MockArmMechanism]] - degree 12, connects to 2 communities