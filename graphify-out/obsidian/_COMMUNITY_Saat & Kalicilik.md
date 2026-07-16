---
type: community
members: 56
---

# Saat & Kalicilik

**Members:** 56 nodes

## Members
- [[.__init__()]] - code - src/common/clock.py
- [[._save()]] - code - src/services/persistence.py
- [[.advance()]] - code - src/common/clock.py
- [[.altitude_zero_ref()]] - code - src/services/persistence.py
- [[.boot_count()]] - code - src/services/persistence.py
- [[.current_packet_number()]] - code - src/services/persistence.py
- [[.load()]] - code - src/services/persistence.py
- [[.mission_time_s()]] - code - src/services/persistence.py
- [[.next_packet_number()]] - code - src/services/persistence.py
- [[.now_monotonic()]] - code - src/common/clock.py
- [[.now_monotonic()_1]] - code - src/common/clock.py
- [[.now_monotonic()_2]] - code - src/common/clock.py
- [[.now_utc()]] - code - src/common/clock.py
- [[.now_utc()_1]] - code - src/common/clock.py
- [[.now_utc()_2]] - code - src/common/clock.py
- [[.set_altitude_zero_ref()]] - code - src/services/persistence.py
- [[.set_utc()]] - code - src/common/clock.py
- [[Atomik dosya tabanlı kalıcı depo. Her değişiklik tmp dosyaya yazılıp     os.repl]] - rationale - src/services/persistence.py
- [[Clock birim testleri (REQ-SW-004).]] - rationale - tests/test_clock.py
- [[Deterministik test saati. Gerçek zaman beklemesi yok; testler `advance()` ile]] - rationale - src/common/clock.py
- [[FakeClock]] - code - src/common/clock.py
- [[Gerçek zamanlı UTC (telemetri GÖNDERME SAATİ için).]] - rationale - src/common/clock.py
- [[Görev zamanı restart'a dayanır ve artmaya devam eder (G-17).]] - rationale - tests/test_persistence.py
- [[Görevi         Zaman soyutlaması. Monoton döngü zamanı ve UTC duvar saati için]] - rationale - src/common/clock.py
- [[Hem monoton hem UTC saati ileri alır (normal zaman akışı).]] - rationale - src/common/clock.py
- [[Kalıcılık testleri sayaç + RESTART senaryosu (REQ-TLM-003004, REQ-TEST-002).]] - rationale - tests/test_persistence.py
- [[PersistenceStore]] - code - src/services/persistence.py
- [[RealClock]] - code - src/common/clock.py
- [[Result_5]] - code - src/services/persistence.py
- [[Saniye cinsinden monoton artan süre (döngü zamanlaması için).]] - rationale - src/common/clock.py
- [[Sıradaki paket numarasını döndürür (1'den başlar, monoton artar) ve         duru]] - rationale - src/services/persistence.py
- [[Toplam görev süresi (s) restart öncesi birikmiş + bu oturumun süresi.         İ]] - rationale - src/services/persistence.py
- [[UTC'yi bağımsız ayarlar (ör. GPSUTC senkronizasyonu simülasyonu).]] - rationale - src/common/clock.py
- [[Varsa önceki durumu yükler ve boot_count'u artırır. Dosya yoksa temiz         ba]] - rationale - src/services/persistence.py
- [[_store()]] - code - tests/test_persistence.py
- [[clock.py]] - code - src/common/clock.py
- [[datetime]] - code - src/common/clock.py
- [[float_2]] - code - src/common/clock.py
- [[float_8]] - code - src/services/persistence.py
- [[int_1]] - code - src/services/persistence.py
- [[test_altitude_zero_ref_persists()]] - code - tests/test_persistence.py
- [[test_atomic_file_written()]] - code - tests/test_persistence.py
- [[test_clock.py]] - code - tests/test_clock.py
- [[test_counter_starts_at_one()]] - code - tests/test_persistence.py
- [[test_fake_clock_advance_moves_both()]] - code - tests/test_clock.py
- [[test_fake_clock_is_monotonic()]] - code - tests/test_clock.py
- [[test_fake_clock_no_backwards()]] - code - tests/test_clock.py
- [[test_mission_time_survives_restart()]] - code - tests/test_persistence.py
- [[test_next_before_load_errors()]] - code - tests/test_persistence.py
- [[test_persistence.py]] - code - tests/test_persistence.py
- [[test_protocol_conformance()]] - code - tests/test_clock.py
- [[test_real_clock_monotonic_increases()]] - code - tests/test_clock.py
- [[test_restart_resumes_counter()]] - code - tests/test_persistence.py
- [[test_set_utc_independent()]] - code - tests/test_clock.py
- [[Üretim saati OS monoton sayacı + UTC duvar saati.]] - rationale - src/common/clock.py
- [[İşlemci yeniden başlarsa paket no kaldığı yerden devam eder (G-18).]] - rationale - tests/test_persistence.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Saat__Kalicilik
SORT file.name ASC
```

## Connections to other communities
- 21 edges to [[_COMMUNITY_Mock Suruculer & Cekirdek]]
- 18 edges to [[_COMMUNITY_Ana Uygulama Dongusu]]
- 2 edges to [[_COMMUNITY_Telemetri Servisi & Paket]]

## Top bridge nodes
- [[FakeClock]] - degree 30, connects to 2 communities
- [[PersistenceStore]] - degree 29, connects to 2 communities
- [[datetime]] - degree 12, connects to 2 communities
- [[test_clock.py]] - degree 11, connects to 1 community
- [[Result_5]] - degree 7, connects to 1 community