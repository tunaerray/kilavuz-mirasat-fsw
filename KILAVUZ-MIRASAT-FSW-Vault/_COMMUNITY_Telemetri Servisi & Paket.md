---
type: community
members: 34
---

# Telemetri Servisi & Paket

**Members:** 34 nodes

## Members
- [[.__init__()_14]] - code - src/telemetry/packet.py
- [[.__init__()_15]] - code - src/telemetry/telemetry_service.py
- [[._ensure_header()]] - code - src/telemetry/telemetry_service.py
- [[._f()]] - code - src/telemetry/packet.py
- [[.build()]] - code - src/telemetry/packet.py
- [[.csv_header()]] - code - src/telemetry/packet.py
- [[.csv_units()]] - code - src/telemetry/packet.py
- [[.publish()]] - code - src/telemetry/telemetry_service.py
- [[17 alanı şartname sırasına göre CSV satırına dönüştürür.]] - rationale - src/telemetry/packet.py
- [[Görevi         Telemetri servisi. Üretilen paket satırını SD karta CSV olarak]] - rationale - src/telemetry/telemetry_service.py
- [[LoRa E22 karşılığı. Aşama 1'de mock; yalnız gönderim durumu döner.]] - rationale - src/hal/interfaces.py
- [[PDR s.63 örnek paketiyle alan-alan uyum (boşluklar hariç, takım no 947450).]] - rationale - tests/test_telemetry_packet.py
- [[Paketi üretir, SDCSV'ye ekler ve linkten gönderir. Satırı döndürür.         SD]] - rationale - src/telemetry/telemetry_service.py
- [[Result_6]] - code - src/telemetry/telemetry_service.py
- [[Telemetri paket format testleri — Şartname §2.4 (REQ-TLM-001006, REQ-TEST-003).]] - rationale - tests/test_telemetry_packet.py
- [[TelemetryFields_1]] - code - src/telemetry/telemetry_service.py
- [[TelemetryLink]] - code - src/hal/interfaces.py
- [[TelemetryLink_1]] - code - src/telemetry/telemetry_service.py
- [[TelemetryPacketBuilder]] - code - src/telemetry/packet.py
- [[TelemetryPacketBuilder_1]] - code - src/telemetry/telemetry_service.py
- [[_fields()]] - code - tests/test_telemetry_packet.py
- [[float_9]] - code - src/telemetry/packet.py
- [[int_2]] - code - src/telemetry/packet.py
- [[str_8]] - code - src/telemetry/packet.py
- [[str_9]] - code - src/telemetry/telemetry_service.py
- [[telemetry_service.py]] - code - src/telemetry/telemetry_service.py
- [[test_build_has_17_comma_separated_fields()]] - code - tests/test_telemetry_packet.py
- [[test_field_order_matches_spec()]] - code - tests/test_telemetry_packet.py
- [[test_header_and_units_have_17_fields()]] - code - tests/test_telemetry_packet.py
- [[test_matches_pdr_example_packet()]] - code - tests/test_telemetry_packet.py
- [[test_status_code_is_integer_0_to_5()]] - code - tests/test_telemetry_packet.py
- [[test_telemetry_packet.py]] - code - tests/test_telemetry_packet.py
- [[test_time_format_is_dmy_hms()]] - code - tests/test_telemetry_packet.py
- [[Şartname §2.4 sırasıyla tek bir telemetri satırı (CSV) üretir.]] - rationale - src/telemetry/packet.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Telemetri_Servisi__Paket
SORT file.name ASC
```

## Connections to other communities
- 26 edges to [[_COMMUNITY_Ana Uygulama Dongusu]]
- 15 edges to [[_COMMUNITY_Mock Suruculer & Cekirdek]]
- 2 edges to [[_COMMUNITY_Saat & Kalicilik]]
- 2 edges to [[_COMMUNITY_HAL Arayuzleri]]
- 2 edges to [[_COMMUNITY_ARAS Hata Kodu]]

## Top bridge nodes
- [[TelemetryLink]] - degree 13, connects to 3 communities
- [[test_telemetry_packet.py]] - degree 12, connects to 2 communities
- [[telemetry_service.py]] - degree 7, connects to 2 communities
- [[str_9]] - degree 7, connects to 2 communities
- [[Result_6]] - degree 7, connects to 2 communities