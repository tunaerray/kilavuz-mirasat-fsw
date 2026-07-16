---
source_file: "src/services/failsafe.py"
type: "code"
community: "APAM Failsafe & Aktuator Baglami"
location: "L59"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/APAM_Failsafe__Aktuator_Baglami
---

# bool

## Connections
- [[.apam_active()]] - `references` [EXTRACTED]
- [[.parachute_deployed()]] - `references` [EXTRACTED]
- [[ActuatorSuite]] - `uses` [INFERRED]
- [[ApamConfig]] - `uses` [INFERRED]
- [[ErrorCode]] - `uses` [INFERRED]
- [[FlightContext]] - `uses` [INFERRED]
- [[Result]] - `uses` [INFERRED]
- [[ServoPosition_1]] - `uses` [INFERRED]

#graphify/code #graphify/INFERRED #community/APAM_Failsafe__Aktuator_Baglami