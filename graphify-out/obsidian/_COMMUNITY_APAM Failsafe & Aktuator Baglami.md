---
type: community
members: 55
---

# APAM Failsafe & Aktuator Baglami

**Members:** 55 nodes

## Members
- [[.__init__()_10]] - code - src/services/failsafe.py
- [[.any_fault()]] - code - src/mission/context.py
- [[.apam_active()]] - code - src/services/failsafe.py
- [[.execute_apam()]] - code - src/services/failsafe.py
- [[.overspeed_timer_s()]] - code - src/services/failsafe.py
- [[.parachute_deployed()]] - code - src/services/failsafe.py
- [[.update()]] - code - src/services/failsafe.py
- [[APAM  failsafe testleri — Şartname G-10 (REQ-SAFE-003..008, CONFLICT önlemleri)]] - rationale - tests/test_failsafe_apam.py
- [[APAM açma sıralamasını uygular (KESİN sıra)           1) MOTOR KILL (tüm motorl]] - rationale - src/services/failsafe.py
- [[APAM durum makinesi. Bir kez tetiklenince (latch) motor kill ve paraşüt     açma]] - rationale - src/services/failsafe.py
- [[APAM tetikleme parametreleri — Şartname Gereksinim-10 s.11 (DOĞRULANMIŞ).]] - rationale - config/default.py
- [[ActuatorSuite]] - code - src/drivers/mock_actuators.py
- [[ActuatorSuite_1]] - code - src/services/failsafe.py
- [[ApamConfig]] - code - config/default.py
- [[ApamConfig_1]] - code - src/services/failsafe.py
- [[ApamTrigger]] - code - src/services/failsafe.py
- [[Bir kontrol çevriminin karar girdileri.]] - rationale - src/mission/context.py
- [[Bir çevrim değerlendirir. `ctx.mission_time_s` monoton artan görev         zaman]] - rationale - src/services/failsafe.py
- [[Bir çevrimin failsafe çıktısı.]] - rationale - src/services/failsafe.py
- [[FailsafeDecision]] - code - src/services/failsafe.py
- [[FailsafeManager]] - code - src/services/failsafe.py
- [[FlightContext]] - code - src/mission/context.py
- [[FlightContext_1]] - code - src/services/failsafe.py
- [[Görev zamanını start→stop arası ilerletip her adımda update çağırır.]] - rationale - tests/test_failsafe_apam.py
- [[Görevi         Failsafe yöneticisi ve APAM (Acil Paraşüt Açma) mantığı. 16 ms]] - rationale - src/services/failsafe.py
- [[Görevi         Uçuş bağlamı (FlightContext). Bir çevrimde kestirilenölçülen]] - rationale - src/mission/context.py
- [[HealthFlags]] - code - src/mission/context.py
- [[Hız güvenli seviyeye düşerse sayaç sıfırlanır (anlık artış tetiklemez).]] - rationale - tests/test_failsafe_apam.py
- [[KESİN sıra önce motor kill, sonra paraşüt OPEN.]] - rationale - tests/test_failsafe_apam.py
- [[Link loss TEK BAŞINA APAM tetiklemez (hız güvenli).]] - rationale - tests/test_failsafe_apam.py
- [[Result_4]] - code - src/services/failsafe.py
- [[Sağlık izleyici çıktısı (bayraklar).]] - rationale - src/mission/context.py
- [[Servo güvenliaktif konumları (somut açı sürücüde eşlenir).]] - rationale - src/hal/interfaces.py
- [[ServoPosition_1]] - code - src/hal/interfaces.py
- [[Tüm aktüatörleri bir arada tutar ve topluca Safe State'e alır.]] - rationale - src/drivers/mock_actuators.py
- [[Yükselme sırasında APAM tetiklenmez (iniş fazı kilidi).]] - rationale - tests/test_failsafe_apam.py
- [[_ctx()]] - code - tests/test_failsafe_apam.py
- [[_step()]] - code - tests/test_failsafe_apam.py
- [[bool_6]] - code - src/mission/context.py
- [[bool_7]] - code - src/services/failsafe.py
- [[context.py]] - code - src/mission/context.py
- [[failsafe.py]] - code - src/services/failsafe.py
- [[float_7]] - code - src/services/failsafe.py
- [[test_altitude_guard_below_100m_no_deploy()]] - code - tests/test_failsafe_apam.py
- [[test_apam_latches_active()]] - code - tests/test_failsafe_apam.py
- [[test_counter_resets_when_speed_safe()]] - code - tests/test_failsafe_apam.py
- [[test_execute_apam_kills_motors_before_parachute()]] - code - tests/test_failsafe_apam.py
- [[test_failsafe_apam.py]] - code - tests/test_failsafe_apam.py
- [[test_link_loss_alone_does_not_trigger()]] - code - tests/test_failsafe_apam.py
- [[test_manual_apam_blocked_below_100m()]] - code - tests/test_failsafe_apam.py
- [[test_manual_apam_triggers_above_100m()]] - code - tests/test_failsafe_apam.py
- [[test_no_trigger_before_10s()]] - code - tests/test_failsafe_apam.py
- [[test_no_trigger_during_ascent()]] - code - tests/test_failsafe_apam.py
- [[test_triggers_after_16mps_10s()]] - code - tests/test_failsafe_apam.py
- [[İrtifa ≤100 m ise paraşüt açılmaz (kesin 100 m kuralı).]] - rationale - tests/test_failsafe_apam.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/APAM_Failsafe__Aktuator_Baglami
SORT file.name ASC
```

## Connections to other communities
- 53 edges to [[_COMMUNITY_Ana Uygulama Dongusu]]
- 24 edges to [[_COMMUNITY_Mock Suruculer & Cekirdek]]
- 19 edges to [[_COMMUNITY_Guvenli Aktuatorler]]
- 2 edges to [[_COMMUNITY_HAL Arayuzleri]]
- 2 edges to [[_COMMUNITY_Durum Makinesi Testleri]]

## Top bridge nodes
- [[ServoPosition_1]] - degree 37, connects to 4 communities
- [[ActuatorSuite]] - degree 32, connects to 3 communities
- [[FailsafeManager]] - degree 34, connects to 2 communities
- [[FlightContext]] - degree 32, connects to 2 communities
- [[test_failsafe_apam.py]] - degree 22, connects to 2 communities