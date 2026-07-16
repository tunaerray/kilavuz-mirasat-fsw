---
type: community
members: 11
---

# Durum Makinesi Testleri

**Members:** 11 nodes

## Members
- [[Durum makinesi testleri — faz geçişleri + statü 0..5 (REQ-TLM-007, CONFLICT-002)]] - rationale - tests/test_state_machine.py
- [[_ctx()_1]] - code - tests/test_state_machine.py
- [[_sm()]] - code - tests/test_state_machine.py
- [[test_apam_forces_emergency_phase()]] - code - tests/test_state_machine.py
- [[test_boot_to_ready()]] - code - tests/test_state_machine.py
- [[test_fault_status_before_separation_is_ready()]] - code - tests/test_state_machine.py
- [[test_full_nominal_sequence()]] - code - tests/test_state_machine.py
- [[test_hovering_then_final_and_land()]] - code - tests/test_state_machine.py
- [[test_manual_separation_command_transitions()]] - code - tests/test_state_machine.py
- [[test_state_machine.py]] - code - tests/test_state_machine.py
- [[test_status_code_mapping_matches_spec()]] - code - tests/test_state_machine.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Durum_Makinesi_Testleri
SORT file.name ASC
```

## Connections to other communities
- 6 edges to [[_COMMUNITY_Ana Uygulama Dongusu]]
- 2 edges to [[_COMMUNITY_APAM Failsafe & Aktuator Baglami]]

## Top bridge nodes
- [[test_state_machine.py]] - degree 15, connects to 2 communities
- [[_sm()]] - degree 10, connects to 1 community
- [[_ctx()_1]] - degree 8, connects to 1 community