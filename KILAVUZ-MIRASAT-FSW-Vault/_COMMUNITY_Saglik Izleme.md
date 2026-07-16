---
type: community
members: 12
---

# Saglik Izleme

**Members:** 12 nodes

## Members
- [[Sağlık izleyici testleri (REQ-SAFE-009).]] - rationale - tests/test_health_monitor.py
- [[_hm()]] - code - tests/test_health_monitor.py
- [[_inp()_1]] - code - tests/test_health_monitor.py
- [[test_all_nominal_no_flags()]] - code - tests/test_health_monitor.py
- [[test_any_fault_only_critical()]] - code - tests/test_health_monitor.py
- [[test_critical_battery()]] - code - tests/test_health_monitor.py
- [[test_health_monitor.py]] - code - tests/test_health_monitor.py
- [[test_link_loss()]] - code - tests/test_health_monitor.py
- [[test_loop_overrun()]] - code - tests/test_health_monitor.py
- [[test_low_battery()]] - code - tests/test_health_monitor.py
- [[test_stale_sensor_by_age()]] - code - tests/test_health_monitor.py
- [[test_stale_sensor_when_none_valid()]] - code - tests/test_health_monitor.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Saglik_Izleme
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Ana Uygulama Dongusu]]

## Top bridge nodes
- [[test_health_monitor.py]] - degree 15, connects to 1 community
- [[_hm()]] - degree 11, connects to 1 community
- [[_inp()_1]] - degree 10, connects to 1 community