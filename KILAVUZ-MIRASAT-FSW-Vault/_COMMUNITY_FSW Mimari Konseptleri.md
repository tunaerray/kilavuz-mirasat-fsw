---
type: community
members: 30
---

# FSW Mimari Konseptleri

**Members:** 30 nodes

## Members
- [[17-Field Telemetry Packet Format]] - concept - docs/REQUIREMENTS.md
- [[APAM (Emergency Parachute Deployment Mechanism)]] - concept - docs/REQUIREMENTS.md
- [[ARAS Error Code (4-bit)]] - concept - docs/REQUIREMENTS.md
- [[CONFLICT-001 Post-Landing Telemetry Duration]] - document - docs/ASSUMPTIONS_AND_CONFLICTS.md
- [[CONFLICT-002 Satellite Status Codes Reversed]] - document - docs/ASSUMPTIONS_AND_CONFLICTS.md
- [[CONFLICT-003 Error Code Digit Count (4 vs 5)]] - document - docs/ASSUMPTIONS_AND_CONFLICTS.md
- [[Dev Requirements (pytestpytest-timeout)]] - document - requirements-dev.txt
- [[Development Roadmap (5 Phases)]] - document - docs/DEVELOPMENT_PLAN.md
- [[EKSİK-003 Takeoff AltitudePressure Reference]] - document - docs/ASSUMPTIONS_AND_CONFLICTS.md
- [[FRR System Tests (shockvibrationdrop)]] - concept - docs/TEST_PLAN.md
- [[Failsafe Manager Architecture]] - concept - docs/SAFETY_CONCEPT.md
- [[Flight State Machine]] - concept - docs/ARCHITECTURE.md
- [[Health Monitor]] - concept - docs/SAFETY_CONCEPT.md
- [[Internal Phase to Status Code Mapping]] - concept - docs/ARCHITECTURE.md
- [[Layered Architecture (5 layers)]] - concept - ANA_PROMPT.md
- [[Main Loop Data Flow]] - concept - docs/DATA_FLOW.md
- [[Module Design Contracts]] - document - docs/MODULE_DESIGN.md
- [[Persistence Store (restart-safe)]] - concept - docs/DATA_FLOW.md
- [[Phase EMERGENCY_APAM]] - concept - docs/ARCHITECTURE.md
- [[REQ-BONUS-003 Z.I.R.H Store-and-Forward]] - document - docs/REQUIREMENTS.md
- [[REQ-SAFE-003 APAM 16 ms for 10s uninterrupted]] - document - docs/REQUIREMENTS.md
- [[REQ-SAFE-005 Motor Kill Before Parachute]] - document - docs/REQUIREMENTS.md
- [[REQ-SAFE-008 Link Loss Alone Does Not Trigger APAM]] - document - docs/REQUIREMENTS.md
- [[REQ-TLM-001 17-Field Packet Exact OrderUnits]] - document - docs/REQUIREMENTS.md
- [[REQ-TLM-003 Persistent Packet Counter]] - document - docs/REQUIREMENTS.md
- [[Satellite Status Codes (0-5)]] - concept - docs/REQUIREMENTS.md
- [[Telemetry Service (CSV + RF)]] - concept - docs/DATA_FLOW.md
- [[Test Plan (Phase 1 unitintegration)]] - document - docs/TEST_PLAN.md
- [[TÜRKSAT 2026 Şartname V4.0 (Specification)]] - document - docs/SOURCE_ANALYSIS.md
- [[Z.I.R.H Store-and-Forward (BONUS-3)]] - concept - ANA_PROMPT.md

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/FSW_Mimari_Konseptleri
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_Cift Islemci & ADR-001]]

## Top bridge nodes
- [[Failsafe Manager Architecture]] - degree 5, connects to 1 community