"""
Görevi        : Mini Pix v1.2 (Pixhawk/ArduPilot) MAVLink veri kaynağı ve HAL
                adaptörleri. TEK bir pymavlink bağlantısı açar, akıştaki mesajları
                tipe göre cache'ler (`pump()`), ve mevcut HAL arayüzlerini
                (Barometer/Imu/Gps/Battery/FlightControllerLink) uygulayan
                adaptörlerle üst katmanlara sunar.
Neden Gerekli : EKSİK-001 (gerçek) — sensör verilerini (baro/IMU/GPS/batarya) Mini
                Pix'ten okuyup arayüze giden telemetri zincirini (estimator →
                packet → framing → LoRa) BESLEMEK için gerçek veri kaynağı gerekir.
                Sim'de mock sensörler bu işi yapıyordu; FLIGHT'ta MAVLink yapar.
İlişkiler     : factory.create_sensors/create_flight_controller bu sınıfları FLIGHT
                profilinde üretir; main döngüsü her çevrim `pump()` çağırır (zirh.pump
                gibi). ApamActuator ile AYNI bağlantıyı paylaşır (tek seri port iki
                kez açılamaz): `MavlinkSource.connection`.
DÜRÜSTLÜK NOTU: Gerçek MAVLink G/Ç fiziksel Mini Pix ve `pymavlink` gerektirir; bu
                ortamda cihaz YOKTUR. pymavlink yoksa veya port açılamazsa sürücü
                sessizce ÇÖKMEZ; açık UNAVAILABLE/IO_ERROR döndürür. Veri henüz
                gelmemişse adaptörler UNAVAILABLE döndürür; gelen veri, ALINDIĞI
                monoton zamanla damgalanır → MAVLink kesilirse HealthMonitor
                (max_sensor_age_s) bayatlığı tespit eder (sessiz taze veri YOK).
                ESC telemetri (motor RPM) donanımda olmadığından motor_rpm güvenli
                0 döner (TASK_TRACKER: REQ-SAFE-010). send_setpoint gerçek ArduPilot
                kontrol eşlemesi Aşama 5 kapsamıdır; şimdilik açık UNAVAILABLE döner
                (sessiz başarı YOK). Saha doğrulaması docs/HARDWARE_BRINGUP.md.
Nasıl Test    : tests/test_mavlink_source.py — sahte (fake) bağlantı enjeksiyonuyla
                (pymavlink/donanım olmadan): stream isteği, mesaj→reading eşlemesi,
                pump öncesi UNAVAILABLE, alım-zamanı damgası, güvenli degrade.
"""
from __future__ import annotations

import math
from typing import Callable, Optional

from config.default import PixhawkConfig
from src.common.clock import Clock
from src.common.result import ErrorCode, Result
from src.hal.interfaces import (
    BarometerReading,
    BatteryReading,
    FlightControllerTelemetry,
    GpsReading,
    ImuReading,
)

# MAV_DATA_STREAM grup kimlikleri (MAVLink standardı; pymavlink olmadan gömülü —
# apam_actuator.py ile aynı yaklaşım). ArduPilot bu gruplarla akış açar.
MAV_DATA_STREAM_RAW_SENSORS = 1       # RAW_IMU, SCALED_PRESSURE
MAV_DATA_STREAM_EXTENDED_STATUS = 2   # SYS_STATUS, GPS_RAW_INT
MAV_DATA_STREAM_POSITION = 6          # GLOBAL_POSITION_INT
MAV_DATA_STREAM_EXTRA1 = 10           # ATTITUDE
_G = 9.80665  # standart yerçekimi (mG → m/s² dönüşümü)

# Bağlantı üreticisi: (port, baud) → mavlink bağlantı nesnesi. Test bunu enjekte
# ederek gerçek donanım olmadan sahte bir bağlantı verir (apam_actuator ile aynı desen).
ConnectFn = Callable[[str, int], object]


def _default_connect(port: str, baud: int) -> object:
    """Varsayılan bağlantı: pymavlink mavutil ile seri MAVLink bağı (lazy import)."""
    from pymavlink import mavutil  # type: ignore  # yalnız donanım profilinde kurulu

    return mavutil.mavlink_connection(port, baud=baud)


class MavlinkSource:
    """
    Mini Pix ile tek MAVLink bağının sahibi. `open()` ile açılır, `pump()` ile akış
    boşaltılıp en güncel mesajlar tipe göre saklanır. Adaptörler `latest()` üzerinden
    okur. `open()` çağrılana kadar bağlı değildir.
    """

    def __init__(self, config: PixhawkConfig, clock: Clock,
                 connect_fn: Optional[ConnectFn] = None) -> None:
        self._cfg = config
        self._clock = clock
        self._connect_fn = connect_fn if connect_fn is not None else _default_connect
        self._conn: object | None = None
        self._error: str | None = None
        # msg_type -> (mesaj, alındığı monoton zaman)
        self._latest: dict[str, tuple[object, float]] = {}

    # ------------------------------------------------------------- yaşam döngüsü
    def open(self) -> Result[None]:
        """
        Bağlanır, HEARTBEAT bekler (target_system öğrenir) ve akışları talep eder.
        ArduPilot çoğu mesajı biri istemeden yollamaz; ayrıca istek doğru
        target_system'e gitmeli — bu yüzden akış isteği ÖNCE heartbeat beklenerek
        gönderilir. pymavlink/port yoksa veya heartbeat gelmezse açık hata döner.
        """
        try:
            self._conn = self._connect_fn(self._cfg.port, self._cfg.baud)
        except ImportError:
            self._error = "pymavlink kurulu değil (donanım profili gerektirir)"
            return Result.err(ErrorCode.UNAVAILABLE, self._error)
        except Exception as exc:  # pragma: no cover - donanıma özgü G/Ç hataları
            self._error = f"MAVLink bağlantısı açılamadı ({self._cfg.port}): {exc}"
            return Result.err(ErrorCode.IO_ERROR, self._error)
        try:
            hb = self._conn.wait_heartbeat(timeout=self._cfg.heartbeat_timeout_s)
        except Exception as exc:  # pragma: no cover - donanıma özgü G/Ç hataları
            self._error = f"heartbeat beklenirken hata: {exc}"
            return Result.err(ErrorCode.IO_ERROR, self._error)
        if hb is None:
            self._error = ("MAVLink heartbeat alınamadı "
                           f"({self._cfg.heartbeat_timeout_s:.0f} sn) — FC yanıt vermiyor")
            return Result.err(ErrorCode.TIMEOUT, self._error)
        self._request_streams()
        return Result.ok(None)

    def _request_streams(self) -> None:
        """
        Gerekli MAVLink akış gruplarını REQUEST_DATA_STREAM ile talep eder (ArduPilot'ta
        en güvenilir yöntem; heartbeat SONRASI doğru target_system'e gönderilir).
        BEST-EFFORT: tek tek istek hatası open()'ı bozmaz (akış yokluğu adaptörlerde
        UNAVAILABLE olarak görünür — sessiz taze veri üretilmez).
        """
        if self._conn is None:
            return
        # (grup, hz) — bir grup birden çok mesaj taşır (yorumlar hangi mesajlar).
        streams = [
            (MAV_DATA_STREAM_EXTRA1, self._cfg.attitude_hz),                        # ATTITUDE
            (MAV_DATA_STREAM_RAW_SENSORS,
             max(self._cfg.imu_hz, self._cfg.pressure_hz)),                         # RAW_IMU, SCALED_PRESSURE
            (MAV_DATA_STREAM_EXTENDED_STATUS,
             max(self._cfg.gps_hz, self._cfg.sys_status_hz)),                       # SYS_STATUS, GPS_RAW_INT
            (MAV_DATA_STREAM_POSITION, self._cfg.gps_hz),                           # GLOBAL_POSITION_INT
        ]
        for stream_id, hz in streams:
            if hz <= 0:
                continue
            try:
                self._conn.mav.request_data_stream_send(
                    self._conn.target_system, self._conn.target_component,
                    stream_id, int(hz), 1)   # start_stop=1 → akışı başlat
            except Exception:  # pragma: no cover - donanıma özgü G/Ç hataları
                continue

    def pump(self, max_messages: int = 200) -> int:
        """
        O an biriken mesajları (bloklamadan) çeker ve tipe göre en güncelini
        saklar. Ana döngüde çevrimde bir kez çağrılır (zirh.pump gibi). Okunan
        mesaj sayısını döndürür. Bağlantı yoksa 0.
        """
        if self._conn is None:
            return 0
        count = 0
        for _ in range(max_messages):
            msg = self._conn.recv_match(blocking=False)
            if msg is None:
                break
            self._latest[msg.get_type()] = (msg, self._clock.now_monotonic())
            count += 1
        return count

    def latest(self, msg_type: str) -> Optional[tuple[object, float]]:
        """(mesaj, alındığı monoton zaman) veya henüz gelmemişse None."""
        return self._latest.get(msg_type)

    def is_connected(self) -> bool:
        return self._conn is not None

    @property
    def connection(self) -> object | None:
        """Ham mavutil bağlantısı (ApamActuator komut gönderimi için paylaşılır)."""
        return self._conn

    def close(self) -> Result[None]:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception as exc:  # pragma: no cover
                return Result.err(ErrorCode.IO_ERROR, f"MAVLink kapatma hatası: {exc}")
        return Result.ok(None)


# --------------------------------------------------------------- HAL adaptörleri
class MavlinkBarometer:
    """SCALED_PRESSURE → BarometerReading (hPa→Pa, cdeg→°C)."""

    def __init__(self, source: MavlinkSource) -> None:
        self._s = source

    def read(self) -> Result[BarometerReading]:
        item = self._s.latest("SCALED_PRESSURE")
        if item is None:
            return Result.err(ErrorCode.UNAVAILABLE, "SCALED_PRESSURE mesajı henüz yok")
        msg, ts = item
        return Result.ok(BarometerReading(
            pressure_pa=float(msg.press_abs) * 100.0,      # hPa → Pa
            temperature_c=float(msg.temperature) / 100.0,  # cdegC → °C
            timestamp_s=ts))


class MavlinkImu:
    """ATTITUDE (rad→derece) + SCALED_IMU/RAW_IMU (mG→m/s²) → ImuReading."""

    def __init__(self, source: MavlinkSource) -> None:
        self._s = source

    def read(self) -> Result[ImuReading]:
        item = self._s.latest("ATTITUDE")
        if item is None:
            return Result.err(ErrorCode.UNAVAILABLE, "ATTITUDE mesajı henüz yok")
        msg, ts = item
        accel_z = _G  # ivme mesajı yoksa nominal 1g kabul
        # İvme: SCALED_IMU tercih; yoksa RAW_IMU (ikisi de mG). ArduPilot varsayılan
        # akışında genelde RAW_IMU gelir.
        for imu_type in ("SCALED_IMU", "RAW_IMU"):
            imu_item = self._s.latest(imu_type)
            if imu_item is not None:
                accel_z = float(imu_item[0].zacc) / 1000.0 * _G   # mG → m/s²
                break
        return Result.ok(ImuReading(
            pitch_deg=math.degrees(float(msg.pitch)),
            roll_deg=math.degrees(float(msg.roll)),
            yaw_deg=math.degrees(float(msg.yaw)),
            accel_z_mps2=accel_z,
            timestamp_s=ts))


class MavlinkGps:
    """GPS_RAW_INT → GpsReading (1e7 ölçek, mm→m, fix_type≥3 → geçerli)."""

    def __init__(self, source: MavlinkSource) -> None:
        self._s = source

    def read(self) -> Result[GpsReading]:
        item = self._s.latest("GPS_RAW_INT")
        if item is None:
            return Result.err(ErrorCode.UNAVAILABLE, "GPS_RAW_INT mesajı henüz yok")
        msg, ts = item
        return Result.ok(GpsReading(
            latitude=float(msg.lat) / 1e7,
            longitude=float(msg.lon) / 1e7,
            altitude_m=float(msg.alt) / 1000.0,            # mm → m
            satellites=int(getattr(msg, "satellites_visible", 0)),
            fix_valid=int(getattr(msg, "fix_type", 0)) >= 3,   # 3D fix
            timestamp_s=ts))


class MavlinkBattery:
    """SYS_STATUS.voltage_battery (mV→V) → BatteryReading."""

    def __init__(self, source: MavlinkSource) -> None:
        self._s = source

    def read(self) -> Result[BatteryReading]:
        item = self._s.latest("SYS_STATUS")
        if item is None:
            return Result.err(ErrorCode.UNAVAILABLE, "SYS_STATUS mesajı henüz yok")
        msg, ts = item
        return Result.ok(BatteryReading(
            voltage_v=float(msg.voltage_battery) / 1000.0,  # mV → V
            timestamp_s=ts))


class MavlinkFlightControllerLink:
    """
    ATTITUDE → FlightControllerTelemetry. motor_rpm güvenli 0'dır: ESC telemetri
    (RPM geri bildirimi) donanımda YOKTUR (TASK_TRACKER REQ-SAFE-010). send_setpoint
    gerçek ArduPilot kontrol eşlemesi Aşama 5 kapsamındadır; açık UNAVAILABLE döner.
    """

    def __init__(self, source: MavlinkSource, clock: Clock) -> None:
        self._s = source
        self._clock = clock

    def is_connected(self) -> bool:
        return self._s.is_connected()

    def read_telemetry(self) -> Result[FlightControllerTelemetry]:
        item = self._s.latest("ATTITUDE")
        if item is None:
            return Result.err(ErrorCode.UNAVAILABLE, "ATTITUDE mesajı henüz yok")
        msg, ts = item
        return Result.ok(FlightControllerTelemetry(
            pitch_deg=math.degrees(float(msg.pitch)),
            roll_deg=math.degrees(float(msg.roll)),
            yaw_deg=math.degrees(float(msg.yaw)),
            motor_rpm=(0.0, 0.0, 0.0, 0.0),   # ESC telemetri yok (REQ-SAFE-010)
            healthy=True,
            timestamp_s=ts))

    def send_setpoint(self, throttle: float, target_alt_m: float | None) -> Result[None]:
        # Gerçek ArduPilot kontrol eşlemesi (guided/attitude target) Aşama 5 kapsamı.
        # Sessiz başarı YOK: açık UNAVAILABLE döndürülür.
        return Result.err(ErrorCode.UNAVAILABLE,
                          "MAVLink setpoint gönderimi Aşama 5'te uygulanacak")
