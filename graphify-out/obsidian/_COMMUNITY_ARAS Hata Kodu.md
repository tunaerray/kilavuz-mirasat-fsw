---
type: community
members: 14
---

# ARAS Hata Kodu

**Members:** 14 nodes

## Members
- [[ARAS hata kodu testleri — Şartname §2.2 (REQ-TLM-011..015, CONFLICT-003).]] - rationale - tests/test_error_code.py
- [[ARAS hata kodunu üretir — Şartname §2.2 s.13-14 (DOĞRULANMIŞ)       Bit-1 iniş]] - rationale - src/telemetry/packet.py
- [[_inp()]] - code - tests/test_error_code.py
- [[compute_error_code()]] - code - src/telemetry/packet.py
- [[test_all_nominal_is_0000()]] - code - tests/test_error_code.py
- [[test_apam_active_is_0001()]] - code - tests/test_error_code.py
- [[test_digits_config_padding()]] - code - tests/test_error_code.py
- [[test_digits_too_small_raises()]] - code - tests/test_error_code.py
- [[test_error_code.py]] - code - tests/test_error_code.py
- [[test_multiple_faults()]] - code - tests/test_error_code.py
- [[test_not_separated_sets_bit3()]] - code - tests/test_error_code.py
- [[test_position_lost_is_0100()]] - code - tests/test_error_code.py
- [[test_speed_check_inactive_gives_bit1_zero()]] - code - tests/test_error_code.py
- [[test_speed_out_of_range_sets_bit1()]] - code - tests/test_error_code.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/ARAS_Hata_Kodu
SORT file.name ASC
```

## Connections to other communities
- 6 edges to [[_COMMUNITY_Ana Uygulama Dongusu]]
- 2 edges to [[_COMMUNITY_Telemetri Servisi & Paket]]

## Top bridge nodes
- [[compute_error_code()]] - degree 17, connects to 2 communities
- [[test_error_code.py]] - degree 13, connects to 1 community
- [[_inp()]] - degree 11, connects to 1 community