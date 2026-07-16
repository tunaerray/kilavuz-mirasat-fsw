# Graph Report - .  (2026-07-16)

## Corpus Check
- Corpus is ~19,653 words - fits in a single context window. You may not need a graph.

## Summary
- 641 nodes · 1538 edges · 57 communities (32 shown, 25 thin omitted)
- Extraction: 65% EXTRACTED · 35% INFERRED · 0% AMBIGUOUS · INFERRED: 531 edges (avg confidence: 0.53)
- Token cost: 210,178 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Ana Uygulama Dongusu|Ana Uygulama Dongusu]]
- [[_COMMUNITY_Mock Suruculer & Cekirdek|Mock Suruculer & Cekirdek]]
- [[_COMMUNITY_Saat & Kalicilik|Saat & Kalicilik]]
- [[_COMMUNITY_APAM Failsafe & Aktuator Baglami|APAM Failsafe & Aktuator Baglami]]
- [[_COMMUNITY_Guvenli Aktuatorler|Guvenli Aktuatorler]]
- [[_COMMUNITY_Sartname Gereksinimleri (SIGMA)|Sartname Gereksinimleri (SIGMA)]]
- [[_COMMUNITY_Telemetri Servisi & Paket|Telemetri Servisi & Paket]]
- [[_COMMUNITY_FSW Mimari Konseptleri|FSW Mimari Konseptleri]]
- [[_COMMUNITY_HAL Arayuzleri|HAL Arayuzleri]]
- [[_COMMUNITY_Cift Islemci & ADR-001|Cift Islemci & ADR-001]]
- [[_COMMUNITY_Haberlesme & Bonus Gorevler (PDR)|Haberlesme & Bonus Gorevler (PDR)]]
- [[_COMMUNITY_Result Hata Modeli|Result Hata Modeli]]
- [[_COMMUNITY_Ucus Profili Simulasyonu|Ucus Profili Simulasyonu]]
- [[_COMMUNITY_ARAS Hata Kodu|ARAS Hata Kodu]]
- [[_COMMUNITY_Katmanli Mimari (READMEs)|Katmanli Mimari (READMEs)]]
- [[_COMMUNITY_Saglik Izleme|Saglik Izleme]]
- [[_COMMUNITY_Durum Makinesi Testleri|Durum Makinesi Testleri]]
- [[_COMMUNITY_Ayrilma Fazi|Ayrilma Fazi]]
- [[_COMMUNITY_Hovering (BONUS-1)|Hovering (BONUS-1)]]
- [[_COMMUNITY_LoRa Donanim Gereksinimi|LoRa Donanim Gereksinimi]]
- [[_COMMUNITY_Aktif Inis Fazi|Aktif Inis Fazi]]
- [[_COMMUNITY_Tasiyici Inis Fazi|Tasiyici Inis Fazi]]
- [[_COMMUNITY_Pil Gerilimi Olcumu|Pil Gerilimi Olcumu]]
- [[_COMMUNITY_Gorev Zamani Kaliciligi|Gorev Zamani Kaliciligi]]
- [[_COMMUNITY_Paket Sayaci Kaliciligi|Paket Sayaci Kaliciligi]]
- [[_COMMUNITY_Kurtarma Sesli Ikaz|Kurtarma Sesli Ikaz]]
- [[_COMMUNITY_Dogrulanmis Gorev Profili|Dogrulanmis Gorev Profili]]
- [[_COMMUNITY_Yukselme Fazi|Yukselme Fazi]]
- [[_COMMUNITY_BOOTHazir Fazi|BOOT/Hazir Fazi]]
- [[_COMMUNITY_InisKurtarma Fazi|Inis/Kurtarma Fazi]]
- [[_COMMUNITY_Statu 0 Ucusa Hazir|Statu 0: Ucusa Hazir]]
- [[_COMMUNITY_Statu 1 Yukselme|Statu 1: Yukselme]]
- [[_COMMUNITY_Statu 4 Gorev Yuku Inis|Statu 4: Gorev Yuku Inis]]
- [[_COMMUNITY_Telemetri Basinc|Telemetri: Basinc]]
- [[_COMMUNITY_Telemetri GPS Altitude|Telemetri: GPS Altitude]]
- [[_COMMUNITY_Telemetri GPS Latitude|Telemetri: GPS Latitude]]
- [[_COMMUNITY_Telemetri GPS Longitude|Telemetri: GPS Longitude]]
- [[_COMMUNITY_Telemetri Inis Hizi|Telemetri: Inis Hizi]]
- [[_COMMUNITY_Telemetri Pitch|Telemetri: Pitch]]
- [[_COMMUNITY_Telemetri Roll|Telemetri: Roll]]
- [[_COMMUNITY_Telemetri Sicaklik|Telemetri: Sicaklik]]
- [[_COMMUNITY_Telemetri Takim No|Telemetri: Takim No]]
- [[_COMMUNITY_Telemetri Yaw|Telemetri: Yaw]]
- [[_COMMUNITY_Telemetri Yukseklik|Telemetri: Yukseklik]]
- [[_COMMUNITY_Araclar (tools)|Araclar (tools)]]

## God Nodes (most connected - your core abstractions)
1. `Result` - 84 edges
2. `ErrorCode` - 62 edges
3. `Clock` - 40 edges
4. `build_and_run()` - 37 edges
5. `FlightProfile` - 37 edges
6. `ServoPosition` - 37 edges
7. `FailsafeManager` - 34 edges
8. `SimClock` - 33 edges
9. `ActuatorSuite` - 32 edges
10. `FlightContext` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Z.I.R.H Store-and-Forward (BONUS-3)` --semantically_similar_to--> `Persistence Store (restart-safe)`  [INFERRED] [semantically similar]
  ANA_PROMPT.md → docs/DATA_FLOW.md
- `_fields()` --calls--> `datetime`  [INFERRED]
  tests/test_telemetry_packet.py → src/common/clock.py
- `test_arm_mechanism_deploy_and_lock()` --calls--> `ActuatorSuite`  [EXTRACTED]
  tests/test_actuators.py → src/drivers/mock_actuators.py
- `test_suite_safe_state()` --calls--> `ActuatorSuite`  [EXTRACTED]
  tests/test_actuators.py → src/drivers/mock_actuators.py
- `CONFLICT: PDR 4 haneli hata kodu (spec 2.4 = 5 haneli)` --conceptually_related_to--> `TLM: Hata Kodu (5 haneli - spec)`  [AMBIGUOUS]
  KILAVUZ_MİRASAT_PDR (1).pdf → 2026_Model_Uydu_Yarışması_Şartnamesi_xu1ZC.pdf

## Import Cycles
- 1-file cycle: `src/common/clock.py -> src/common/clock.py`

## Hyperedges (group relationships)
- **Mission Flight Phase Sequence** — docs_architecture_phase_boot, docs_architecture_phase_ascent, docs_architecture_phase_carrier_descent, docs_architecture_phase_separation, docs_architecture_phase_active_descent, docs_architecture_phase_hovering, docs_architecture_phase_recovery [EXTRACTED 1.00]
- **APAM Trigger Conditions** — docs_requirements_req_safe_003, docs_requirements_req_safe_005, docs_requirements_req_safe_008, docs_safety_concept_failsafe [EXTRACTED 1.00]
- **Specification to Requirements to Test Traceability** — docs_source_analysis_sartname, docs_requirements_telemetry_format, docs_test_plan_test_plan [INFERRED 0.85]
- **Telemetri Formati 17 Alan (2.4)** — sartname_tlm_paket_numarasi, sartname_tlm_uydu_statusu, sartname_tlm_hata_kodu, sartname_tlm_gonderme_saati, sartname_tlm_basinc, sartname_tlm_yukseklik, sartname_tlm_inis_hizi, sartname_tlm_sicaklik, sartname_tlm_pil_gerilimi, sartname_tlm_gps_latitude, sartname_tlm_gps_longitude, sartname_tlm_gps_altitude, sartname_tlm_pitch, sartname_tlm_roll, sartname_tlm_yaw, sartname_tlm_rhrhrh, sartname_tlm_takim_no [EXTRACTED 1.00]
- **ARAS Hata Kodu 4 Bit** — sartname_aras_bit0_inis_hizi, sartname_aras_bit1_gps_konum, sartname_aras_bit2_ayrilma, sartname_aras_bit3_acil_parasut [EXTRACTED 1.00]
- **Uydu Statu Kodlari 0-5 (Inis Sekansi)** — sartname_status_0_ucusa_hazir, sartname_status_1_yukselme, sartname_status_2_model_uydu_inis, sartname_status_3_ayrilma, sartname_status_4_gorev_yuku_inis, sartname_status_5_kurtarma [EXTRACTED 1.00]
- **Flight software layered architecture** — config_readme, common_readme, hal_readme, drivers_readme, services_readme, state_machine_readme, telemetry_readme, control_readme, mission_readme, app_readme [INFERRED 0.85]

## Communities (57 total, 25 thin omitted)

### Community 0 - "Ana Uygulama Dongusu"
Cohesion: 0.05
Nodes (80): build_and_run(), main(), Görevi        : Ana uygulama döngüsü. Bağımlılıkları kurar, aktüatörleri Safe, Bir koşunun özeti (test ve raporlama için)., Simülasyon saati: gerçek zaman beklemeden her çevrimde ilerletilir., Sınırlı döngüyü kurar ve çalıştırır. `clock` verilmezse SimClock kullanılır, RunSummary, SimClock (+72 more)

### Community 1 - "Mock Suruculer & Cekirdek"
Cohesion: 0.09
Nodes (55): BarometerReading, BatteryReading, Clock, Zaman kaynağı sözleşmesi., ErrorCode, Açık, ayrıştırılabilir hata türleri. Metin mesaj yalnız tanılama içindir., Başarılı bir değer VEYA açık bir hata taşır. Asla ikisini birden değil., Result (+47 more)

### Community 2 - "Saat & Kalicilik"
Cohesion: 0.06
Nodes (36): FakeClock, Görevi        : Zaman soyutlaması. Monoton döngü zamanı ve UTC duvar saati için, Saniye cinsinden monoton artan süre (döngü zamanlaması için)., Gerçek zamanlı UTC (telemetri GÖNDERME SAATİ için)., Üretim saati: OS monoton sayacı + UTC duvar saati., Deterministik test saati. Gerçek zaman beklemesi yok; testler `advance()` ile, Hem monoton hem UTC saati ileri alır (normal zaman akışı)., UTC'yi bağımsız ayarlar (ör. GPS/UTC senkronizasyonu simülasyonu). (+28 more)

### Community 3 - "APAM Failsafe & Aktuator Baglami"
Cohesion: 0.09
Nodes (45): ActuatorSuite, ApamConfig, ApamConfig, APAM tetikleme parametreleri — Şartname Gereksinim-10 s.11 (DOĞRULANMIŞ)., ActuatorSuite, Tüm aktüatörleri bir arada tutar ve topluca Safe State'e alır., Servo güvenli/aktif konumları (somut açı sürücüde eşlenir)., ServoPosition (+37 more)

### Community 4 - "Guvenli Aktuatorler"
Cohesion: 0.07
Nodes (26): ArmState, MockArmMechanism, MockMotorGroup, MockServo, Görevi        : Güvenli mock aktüatörler (4× motor grubu, ayrılma servosu, APAM, Kolları 90° açar ve kilitler (ayrılma → aktif iniş arası)., Safe State: mevcut konumda kilitli kalır (kolları geri katlamaz)., Safe State: motorlar disarm/0, servolar güvenli konum, kollar kilitli.         B (+18 more)

### Community 5 - "Sartname Gereksinimleri (SIGMA)"
Cohesion: 0.05
Nodes (41): KILAVUZ MIRASAT PDR (Takim No 947450), APAM Algoritmasi (16 m/s >10sn, motor dur, servo pim), PDR ARAS Implementasyonu (4 bit, iki katman, cerceve alarm), BME280 Sicaklik/Basinc Sensoru, Emax ECO II 2207 1700KV Fircasiz Motor (x4), Hatali Tetikleme Analizi (coklu kosul, PWM/RPM tutarlilik), CONFLICT: PDR 4 haneli hata kodu (spec 2.4 = 5 haneli), MPU6500 IMU/Gyro (Pixhawk) (+33 more)

### Community 6 - "Telemetri Servisi & Paket"
Cohesion: 0.10
Nodes (21): LoRa E22 karşılığı. Aşama 1'de mock; yalnız gönderim durumu döner., TelemetryLink, float, int, str, Result, str, 17 alanı şartname sırasına göre CSV satırına dönüştürür. (+13 more)

### Community 7 - "FSW Mimari Konseptleri"
Cohesion: 0.09
Nodes (30): Layered Architecture (5 layers), Z.I.R.H Store-and-Forward (BONUS-3), Phase EMERGENCY_APAM, Flight State Machine, Internal Phase to Status Code Mapping, CONFLICT-001: Post-Landing Telemetry Duration, CONFLICT-002: Satellite Status Codes Reversed, CONFLICT-003: Error Code Digit Count (4 vs 5) (+22 more)

### Community 8 - "HAL Arayuzleri"
Cohesion: 0.10
Nodes (12): FlightControllerLink, FlightControllerTelemetry, MotorGroup, 4× fırçasız motor grubu (SİGMA). Throttle 0..1. Arm olmadan çalışmaz., Tekil servo (ayrılma / APAM paraşüt kapağı / kol)., PixMin/STM32'den gelen üst seviye durum (EKSİK-001, ASSUMPTION-001)., RPi 5 ↔ PixMin arası soyut bağ. Protokol PDR'de belirtilmemiş (EKSİK-001);     M, Servo (+4 more)

### Community 9 - "Cift Islemci & ADR-001"
Cohesion: 0.12
Nodes (20): ADR-001: Language and Target Platform, Dual-Processor Architecture (RPi 5 + PixMin), FlightControllerLink HAL Interface, Flight Software (FSW) Project, PixMin V1.0 Flight Controller (STM32F405), Raspberry Pi 5 4GB Mission Computer, S2D-IoT (BONUS-2, RHRHRH command relay), ASSUMPTION-001: RPi-PixMin Protocol is MAVLink (+12 more)

### Community 10 - "Haberlesme & Bonus Gorevler (PDR)"
Cohesion: 0.11
Nodes (19): Ucus Yazilimi Durum Diyagrami (State Machine), ESP32 IoT Istasyonu Islemcisi, LoRa E22 900T22D Haberlesme Modulu, PDR S2D-IOT Cozumu (E22 LoRa, Role/Kuru Kontak, RGB Panel), CONFLICT: PDR statu 2=Ayrilma, 3=Model Uydu Inis (spec ters), STM32F405VGT6 Islemci, PDR Telemetri Formati (17 alan, CSV, ornek 152,4,0000...), Ucus Yazilimi (C/C++, VS Code + Arduino IDE) (+11 more)

### Community 11 - "Result Hata Modeli"
Cohesion: 0.11
Nodes (7): Görevi        : Açık hata/sonuç modeli (Result[T] + ErrorCode). Sessizce başarıs, Bir hata sonucu unwrap edilmeye çalışıldığında yükseltilir., Değeri döndürür; hata ise ResultError yükseltir (sessiz geçiş yok)., ResultError, Exception, T, Result/ErrorCode birim testleri (REQ-SW-005).

### Community 12 - "Ucus Profili Simulasyonu"
Cohesion: 0.17
Nodes (9): altitude_to_pressure(), Görevi        : Deterministik uçuş profili (yer gerçekliği). Görev zamanına göre, İrtifanın alçalırken target_alt'a ulaştığı ilk zaman (ayrılma anı)., Barometrik formül (kalkış = deniz seviyesi kabulü, sim için yeterli)., Belirli bir görev zamanındaki gerçek (simüle) durum., TruthState, bool, float (+1 more)

### Community 13 - "ARAS Hata Kodu"
Cohesion: 0.34
Nodes (13): compute_error_code(), ARAS hata kodunu üretir — Şartname §2.2 s.13-14 (DOĞRULANMIŞ):       Bit-1: iniş, _inp(), ARAS hata kodu testleri — Şartname §2.2 (REQ-TLM-011..015, CONFLICT-003)., test_all_nominal_is_0000(), test_apam_active_is_0001(), test_digits_config_padding(), test_digits_too_small_raises() (+5 more)

### Community 14 - "Katmanli Mimari (READMEs)"
Cohesion: 0.22
Nodes (13): src/app: bounded main application loop, src/common: cross-cutting core (Result/ErrorCode/Clock), config layer: profiles and parameters, src/control: control/navigation layer, src/drivers: mock sensor/actuator drivers, failsafe / APAM logic, src/hal: hardware abstraction interfaces, src/mission: mission orchestration (+5 more)

### Community 15 - "Saglik Izleme"
Cohesion: 0.41
Nodes (11): _hm(), _inp(), Sağlık izleyici testleri (REQ-SAFE-009)., test_all_nominal_no_flags(), test_any_fault_only_critical(), test_critical_battery(), test_link_loss(), test_loop_overrun() (+3 more)

### Community 16 - "Durum Makinesi Testleri"
Cohesion: 0.42
Nodes (10): _ctx(), Durum makinesi testleri — faz geçişleri + statü 0..5 (REQ-TLM-007, CONFLICT-002), _sm(), test_apam_forces_emergency_phase(), test_boot_to_ready(), test_fault_status_before_separation_is_ready(), test_full_nominal_sequence(), test_hovering_then_final_and_land() (+2 more)

### Community 17 - "Ayrilma Fazi"
Cohesion: 0.67
Nodes (3): SIGMA Arm Deploy/Lock Mechanism, Phase SEPARATION, REQ-MISSION-005: Autonomous Separation at 1000m

### Community 18 - "Hovering (BONUS-1)"
Cohesion: 0.67
Nodes (3): Hovering / Station Keeping (BONUS-1), Phase HOVERING, REQ-CTRL-004: BONUS-1 Hovering 200m 10s

### Community 19 - "LoRa Donanim Gereksinimi"
Cohesion: 0.67
Nodes (3): LoRa E22 900T22D Telemetry Radio, EKSİK-002: Low-Level Parameters Missing, REQ-HW-003: LoRa E22 900T22D Telemetry

## Ambiguous Edges - Review These
- `TLM: Hata Kodu (5 haneli - spec)` → `CONFLICT: PDR 4 haneli hata kodu (spec 2.4 = 5 haneli)`  [AMBIGUOUS]
  KILAVUZ_MİRASAT_PDR (1).pdf · relation: conceptually_related_to
- `Uydu Statusu 2: Model Uydu Inis (spec)` → `CONFLICT: PDR statu 2=Ayrilma, 3=Model Uydu Inis (spec ters)`  [AMBIGUOUS]
  KILAVUZ_MİRASAT_PDR (1).pdf · relation: conceptually_related_to
- `Uydu Statusu 3: Ayrilma (spec)` → `CONFLICT: PDR statu 2=Ayrilma, 3=Model Uydu Inis (spec ters)`  [AMBIGUOUS]
  KILAVUZ_MİRASAT_PDR (1).pdf · relation: conceptually_related_to

## Knowledge Gaps
- **87 isolated node(s):** `bool`, `str`, `bool`, `bool`, `float` (+82 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `TLM: Hata Kodu (5 haneli - spec)` and `CONFLICT: PDR 4 haneli hata kodu (spec 2.4 = 5 haneli)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Uydu Statusu 2: Model Uydu Inis (spec)` and `CONFLICT: PDR statu 2=Ayrilma, 3=Model Uydu Inis (spec ters)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Uydu Statusu 3: Ayrilma (spec)` and `CONFLICT: PDR statu 2=Ayrilma, 3=Model Uydu Inis (spec ters)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Result` connect `Mock Suruculer & Cekirdek` to `Ana Uygulama Dongusu`, `Saat & Kalicilik`, `APAM Failsafe & Aktuator Baglami`, `Guvenli Aktuatorler`, `Telemetri Servisi & Paket`, `HAL Arayuzleri`, `Result Hata Modeli`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Why does `ErrorCode` connect `Mock Suruculer & Cekirdek` to `Ana Uygulama Dongusu`, `Saat & Kalicilik`, `APAM Failsafe & Aktuator Baglami`, `Guvenli Aktuatorler`, `Telemetri Servisi & Paket`, `Result Hata Modeli`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `FailsafeManager` connect `APAM Failsafe & Aktuator Baglami` to `Ana Uygulama Dongusu`, `Mock Suruculer & Cekirdek`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 68 inferred relationships involving `Result` (e.g. with `ActuatorSuite` and `ApamConfig`) actually correct?**
  _`Result` has 68 INFERRED edges - model-reasoned connections that need verification._