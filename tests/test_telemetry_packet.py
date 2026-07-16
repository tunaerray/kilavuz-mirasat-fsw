"""Telemetri paket format testleri — Şartname §2.4 (REQ-TLM-001/006, REQ-TEST-003)."""
from datetime import datetime, timezone

from src.telemetry.packet import (
    FIELD_HEADERS,
    FIELD_UNITS,
    SatelliteStatus,
    TelemetryFields,
    TelemetryPacketBuilder,
)


def _fields():
    return TelemetryFields(
        packet_number=152,
        status=SatelliteStatus.PAYLOAD_DESCENT,   # 4
        error_code="0000",
        send_time=datetime(2026, 5, 4, 14, 32, 10, tzinfo=timezone.utc),
        pressure_pa=91234.5,
        altitude_m=748.2,
        descent_speed_mps=8.7,
        temperature_c=28.4,
        battery_v=11.4,
        gps_lat=39.9255,
        gps_lon=32.8662,
        gps_alt_m=985.3,
        pitch_deg=5.2,
        roll_deg=-3.1,
        yaw_deg=120.6,
        rhrhrh="2R0G1B",
        team_number=947450,
    )


def test_header_and_units_have_17_fields():
    assert len(FIELD_HEADERS) == 17
    assert len(FIELD_UNITS) == 17


def test_field_order_matches_spec():
    # Şartname §2.4 alan sırası
    assert FIELD_HEADERS[0] == "PAKET_NUMARASI"
    assert FIELD_HEADERS[1] == "UYDU_STATUSU"
    assert FIELD_HEADERS[2] == "HATA_KODU"
    assert FIELD_HEADERS[3] == "GONDERME_SAATI"
    assert FIELD_HEADERS[6] == "INIS_HIZI"
    assert FIELD_HEADERS[-1] == "TAKIM_NO"
    # Birimler
    assert FIELD_UNITS[4] == "Pa"
    assert FIELD_UNITS[5] == "m"
    assert FIELD_UNITS[6] == "m/s"
    assert FIELD_UNITS[7] == "C"
    assert FIELD_UNITS[8] == "V"


def test_build_has_17_comma_separated_fields():
    line = TelemetryPacketBuilder().build(_fields())
    parts = line.split(",")
    assert len(parts) == 17


def test_matches_pdr_example_packet():
    """PDR s.63 örnek paketiyle alan-alan uyum (boşluklar hariç, takım no 947450)."""
    line = TelemetryPacketBuilder(decimal_places=1).build(_fields())
    parts = line.split(",")
    assert parts[0] == "152"
    assert parts[1] == "4"                      # UYDU STATÜSÜ = Görev Yükü İniş
    assert parts[2] == "0000"
    assert parts[3] == "04/05/2026 14:32:10"    # GG/AA/YYYY SS:DD:ss
    assert parts[4] == "91234.5"
    assert parts[5] == "748.2"
    assert parts[6] == "8.7"
    assert parts[7] == "28.4"
    assert parts[8] == "11.4"
    assert parts[9] == "39.9255"
    assert parts[10] == "32.8662"
    assert parts[11] == "985.3"
    assert parts[12] == "5.2"
    assert parts[13] == "-3.1"
    assert parts[14] == "120.6"
    assert parts[15] == "2R0G1B"
    assert parts[16] == "947450"


def test_status_code_is_integer_0_to_5():
    for s in SatelliteStatus:
        assert 0 <= int(s) <= 5


def test_time_format_is_dmy_hms():
    line = TelemetryPacketBuilder().build(_fields())
    assert line.split(",")[3] == "04/05/2026 14:32:10"
