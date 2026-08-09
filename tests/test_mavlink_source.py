"""
MavlinkSource ve HAL adaptörleri testleri (EKSİK-001 gerçek — Mini Pix MAVLink).

Sahte (fake) bir MAVLink bağlantısı enjekte edilir; pymavlink/donanım GEREKMEZ.
Doğrulananlar: stream isteği (SET_MESSAGE_INTERVAL), mesaj→reading eşlemesi ve
birim dönüşümleri, pump öncesi UNAVAILABLE, verinin ALINDIĞI zamanla damgalanması,
pymavlink yokken güvenli degrade, FC telemetri motor_rpm=0 (ESC telem yok),
send_setpoint açık UNAVAILABLE.
"""
from config.default import PixhawkConfig
from src.common.clock import FakeClock
from src.common.result import ErrorCode
from src.drivers.mavlink_source import (
    MavlinkBarometer,
    MavlinkBattery,
    MavlinkFlightControllerLink,
    MavlinkGps,
    MavlinkImu,
    MavlinkSource,
)


# --------------------------------------------------------------- test yardımcıları
class _FakeMsg:
    def __init__(self, mtype: str, **fields) -> None:
        self._mtype = mtype
        self.__dict__.update(fields)

    def get_type(self) -> str:
        return self._mtype


class _FakeMav:
    def __init__(self) -> None:
        self.streams: list[tuple] = []

    def request_data_stream_send(self, *args) -> None:
        self.streams.append(args)


class _FakeConn:
    """recv_match ile kuyruktaki mesajları sırayla döndüren sahte bağlantı."""

    def __init__(self, messages=None, heartbeat=True) -> None:
        self._queue = list(messages or [])
        self.mav = _FakeMav()
        self.target_system = 0
        self.target_component = 0
        self._heartbeat = heartbeat
        self.closed = False

    def wait_heartbeat(self, timeout=None):
        if not self._heartbeat:
            return None                    # zaman aşımı simülasyonu
        self.target_system = 1             # heartbeat sonrası öğrenilir
        self.target_component = 1
        return _FakeMsg("HEARTBEAT")

    def queue(self, *messages) -> None:
        self._queue.extend(messages)

    def recv_match(self, blocking=False, **kw):
        if self._queue:
            return self._queue.pop(0)
        return None

    def close(self) -> None:
        self.closed = True


def _source(messages=None, clock=None, heartbeat=True):
    conn = _FakeConn(messages, heartbeat=heartbeat)
    clk = clock or FakeClock()
    src = MavlinkSource(PixhawkConfig(), clk, connect_fn=lambda p, b: conn)
    return src, conn, clk


# ------------------------------------------------------------------------- testler
def test_open_requests_data_streams_after_heartbeat():
    src, conn, _ = _source()
    assert src.open().is_ok
    assert src.is_connected()
    # Heartbeat sonrası target_system öğrenildi (istekler 0'a değil 1'e gitmeli).
    assert conn.target_system == 1
    # 4 akış grubu REQUEST_DATA_STREAM ile istendi, doğru target_system'e.
    assert len(conn.mav.streams) == 4
    assert all(args[0] == 1 for args in conn.mav.streams)     # target_system=1
    assert all(args[4] == 1 for args in conn.mav.streams)     # start_stop=1 (başlat)


def test_open_fails_on_heartbeat_timeout():
    src, conn, _ = _source(heartbeat=False)
    r = src.open()
    assert r.is_err and r.code is ErrorCode.TIMEOUT
    # Heartbeat gelmediği için akış İSTENMEZ (target_system bilinmiyor).
    assert conn.mav.streams == []


def test_barometer_mapping_and_receive_timestamp():
    clk = FakeClock()
    src, conn, _ = _source(clock=clk)
    src.open()
    clk.advance(1.5)   # mesajın ALINDIĞI zaman = 1.5
    conn.queue(_FakeMsg("SCALED_PRESSURE", press_abs=1013.25, temperature=2150))
    assert src.pump() == 1
    r = MavlinkBarometer(src).read()
    assert r.is_ok
    reading = r.unwrap()
    assert abs(reading.pressure_pa - 101325.0) < 1e-6   # hPa → Pa
    assert abs(reading.temperature_c - 21.5) < 1e-6     # cdeg → °C
    assert reading.timestamp_s == 1.5                   # alım zamanı damgası


def test_imu_mapping_degrees_and_accel():
    import math
    src, conn, _ = _source()
    src.open()
    conn.queue(
        _FakeMsg("ATTITUDE", roll=math.radians(10.0), pitch=math.radians(-5.0),
                 yaw=math.radians(90.0)),
        _FakeMsg("SCALED_IMU", zacc=1000),   # 1000 mG = 1 g
    )
    src.pump()
    r = MavlinkImu(src).read()
    assert r.is_ok
    reading = r.unwrap()
    assert abs(reading.roll_deg - 10.0) < 1e-6
    assert abs(reading.pitch_deg + 5.0) < 1e-6
    assert abs(reading.yaw_deg - 90.0) < 1e-6
    assert abs(reading.accel_z_mps2 - 9.80665) < 1e-6


def test_imu_accel_falls_back_to_raw_imu():
    src, conn, _ = _source()
    src.open()
    # SCALED_IMU yok; ArduPilot varsayılan akışındaki RAW_IMU kullanılmalı.
    conn.queue(
        _FakeMsg("ATTITUDE", roll=0.0, pitch=0.0, yaw=0.0),
        _FakeMsg("RAW_IMU", zacc=2000),   # 2000 mG = 2 g
    )
    src.pump()
    reading = MavlinkImu(src).read().unwrap()
    assert abs(reading.accel_z_mps2 - 2 * 9.80665) < 1e-6


def test_gps_mapping_and_fix():
    src, conn, _ = _source()
    src.open()
    conn.queue(_FakeMsg("GPS_RAW_INT", lat=395000000, lon=325000000,
                        alt=150000, satellites_visible=9, fix_type=3))
    src.pump()
    r = MavlinkGps(src).read()
    assert r.is_ok
    reading = r.unwrap()
    assert abs(reading.latitude - 39.5) < 1e-9
    assert abs(reading.longitude - 32.5) < 1e-9
    assert abs(reading.altitude_m - 150.0) < 1e-6   # mm → m
    assert reading.satellites == 9
    assert reading.fix_valid is True


def test_gps_no_fix_when_fix_type_below_3():
    src, conn, _ = _source()
    src.open()
    conn.queue(_FakeMsg("GPS_RAW_INT", lat=0, lon=0, alt=0,
                        satellites_visible=0, fix_type=1))
    src.pump()
    assert MavlinkGps(src).read().unwrap().fix_valid is False


def test_battery_mapping_mv_to_v():
    src, conn, _ = _source()
    src.open()
    conn.queue(_FakeMsg("SYS_STATUS", voltage_battery=16400))
    src.pump()
    assert abs(MavlinkBattery(src).read().unwrap().voltage_v - 16.4) < 1e-6


def test_adapters_unavailable_before_any_message():
    src, _, _ = _source()
    src.open()   # pump çağrılmadı → cache boş
    for adapter in (MavlinkBarometer(src), MavlinkImu(src),
                    MavlinkGps(src), MavlinkBattery(src)):
        r = adapter.read()
        assert r.is_err and r.code is ErrorCode.UNAVAILABLE


def test_flight_controller_attitude_and_zero_rpm():
    import math
    src, conn, clk = _source()
    src.open()
    conn.queue(_FakeMsg("ATTITUDE", roll=0.0, pitch=math.radians(3.0), yaw=0.0))
    src.pump()
    fc = MavlinkFlightControllerLink(src, clk)
    assert fc.is_connected()
    tlm = fc.read_telemetry()
    assert tlm.is_ok
    t = tlm.unwrap()
    assert abs(t.pitch_deg - 3.0) < 1e-6
    # ESC telemetri yok → motor RPM güvenli 0 (REQ-SAFE-010).
    assert t.motor_rpm == (0.0, 0.0, 0.0, 0.0)


def test_flight_controller_send_setpoint_unavailable():
    src, _, clk = _source()
    src.open()
    r = MavlinkFlightControllerLink(src, clk).send_setpoint(0.5, 100.0)
    assert r.is_err and r.code is ErrorCode.UNAVAILABLE


def test_pump_keeps_latest_of_each_type():
    src, conn, _ = _source()
    src.open()
    conn.queue(
        _FakeMsg("SCALED_PRESSURE", press_abs=1000.0, temperature=2000),
        _FakeMsg("SCALED_PRESSURE", press_abs=900.0, temperature=1900),
    )
    assert src.pump() == 2
    # En güncel (son) mesaj kalır.
    assert abs(MavlinkBarometer(src).read().unwrap().pressure_pa - 90000.0) < 1e-6


def test_safe_degrade_without_pymavlink():
    def _raise_import(port, baud):
        raise ImportError("pymavlink yok")

    src = MavlinkSource(PixhawkConfig(), FakeClock(), connect_fn=_raise_import)
    r = src.open()
    assert r.is_err and r.code is ErrorCode.UNAVAILABLE
    assert not src.is_connected()
    assert src.pump() == 0   # bağlantı yokken çökme yok


def test_close_is_safe_and_idempotent():
    src, conn, _ = _source()
    src.open()
    assert src.close().is_ok
    assert conn.closed
