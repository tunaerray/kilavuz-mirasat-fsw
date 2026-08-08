"""
Görevi        : APAM aktüatörü. Uçuş durum makinesinin fazını izler; faz
                EMERGENCY_APAM'a YENİ GEÇTİĞİ anda (her döngüde değil, yalnız bir
                kez) Pixhawk/ArduPilot'a MAV_CMD_DO_PARACHUTE (param1=2, RELEASE)
                komutunu gönderir ve COMMAND_ACK'i bekleyip sonucu loglar.
Neden Gerekli : EKSİK-001 / ASSUMPTION-001 — RPi 5 ↔ Pixhawk bağı bugüne dek soyut
                FlightControllerLink ve mock servo olarak modellendi; acil paraşüt
                açma için donanıma GERÇEK bir MAVLink komutu gönderen katman yoktu.
                Bu sürücü o boşluğu (yalnız FLIGHT/HIL'de aktif) kapatır.
İlişkiler     : config.pixhawk (port/baud/ACK timeout) ve config.is_simulation
                okur; FlightPhase (state_machine) fazını girdi alır. pymavlink
                (mavutil) fiziksel taşımadır; real_lora.py gibi LAZY import edilir.
DÜRÜSTLÜK NOTU: Gerçek MAVLink G/Ç fiziksel Pixhawk ve `pymavlink` gerektirir; bu
                ortamda cihaz YOKTUR. SIMULATION_ONLY'de gerçek komut GÖNDERİLMEZ,
                yalnız log basılır. pymavlink yoksa veya bağlantı açılamazsa sürücü
                sessizce ÇÖKMEZ; açık UNAVAILABLE/IO_ERROR döndürür (saha doğrulaması
                Aşama 5, docs/HARDWARE_BRINGUP.md).
Nasıl Test    : tests/test_apam_actuator.py — sahte (fake) mavlink bağlantısıyla:
                EMERGENCY_APAM'a geçişte tek sefer gönderim, tekrar göndermeme, sim
                modunda yalnız log, ACK ACCEPTED/FAILED/timeout, param1=2 doğrulama.
"""
from __future__ import annotations

from typing import Callable, Optional

from config.default import AppConfig
from src.common.result import ErrorCode, Result
from src.state_machine.flight_state_machine import FlightPhase

# MAVLink sabitleri (pymavlink olmadan da test/log için gömülü tutulur; enum
# değerleri MAVLink standardıdır ve donanımdan bağımsızdır).
MAV_CMD_DO_PARACHUTE = 208      # ArduPilot: paraşüt eylemi
PARACHUTE_RELEASE = 2           # param1=2 → paraşütü BIRAK (aç)
MAV_RESULT_ACCEPTED = 0         # COMMAND_ACK.result kabul kodu

# Bağlantı üreticisi: (port, baud) → mavlink bağlantı nesnesi. Test bunu enjekte
# ederek gerçek donanım olmadan sahte bir bağlantı verir.
ConnectFn = Callable[[str, int], object]


def _default_connect(port: str, baud: int) -> object:
    """Varsayılan bağlantı: pymavlink mavutil ile seri MAVLink bağı (lazy import)."""
    from pymavlink import mavutil  # type: ignore  # yalnız donanım profilinde kurulu

    return mavutil.mavlink_connection(port, baud=baud)


class ApamActuator:
    """
    Fazı izleyip EMERGENCY_APAM'a geçişte tek sefer paraşüt açma komutu gönderen
    aktüatör. `update(phase)` her çevrim çağrılır; kenar (edge) tespiti ve tek
    seferlik latch içeride tutulur — çağıran tarafın durum tutması gerekmez.
    """

    def __init__(self, config: AppConfig,
                 log: Optional[Callable[[str], None]] = None,
                 connect_fn: Optional[ConnectFn] = None) -> None:
        self._cfg = config
        self._pix = config.pixhawk
        self._simulate = config.is_simulation
        self._log = log if log is not None else (lambda s: None)
        self._connect_fn = connect_fn if connect_fn is not None else _default_connect
        self._conn: object | None = None
        self._prev_phase: FlightPhase | None = None
        self._fired = False            # tek seferlik latch (yeniden gönderim yok)

    @property
    def fired(self) -> bool:
        """Paraşüt açma komutu (en az bir kez) gönderildi mi."""
        return self._fired

    def update(self, phase: FlightPhase) -> Optional[Result[None]]:
        """
        Bir çevrim değerlendirir. Faz EMERGENCY_APAM'a YENİ geçtiyse paraşüt açma
        komutunu bir kez tetikler ve sonucunu döndürür; aksi halde None döner
        (yapılacak iş yok). Latch sayesinde faz APAM'da kalsa bile tekrar gönderilmez.
        """
        prev = self._prev_phase
        self._prev_phase = phase

        entering_apam = phase is FlightPhase.EMERGENCY_APAM and prev is not phase
        if not entering_apam or self._fired:
            return None

        self._fired = True             # önce latch'le: hata olsa da tekrar denenmez
        return self._deploy_parachute()

    def _deploy_parachute(self) -> Result[None]:
        """Paraşüt açma sıralaması (sim ise yalnız log, değilse gerçek MAVLink)."""
        if self._simulate:
            # SIMULATION_ONLY: donanıma DOKUNMA; yalnız niyeti kaydet.
            self._log("APAM ACTUATOR [SIM]: MAV_CMD_DO_PARACHUTE param1=2 (RELEASE) "
                      "— simülasyon, gerçek komut gönderilmedi")
            return Result.ok(None)

        conn = self._ensure_connection()
        if conn.is_err:
            self._log(f"APAM ACTUATOR: bağlantı yok — komut gönderilemedi ({conn.message})")
            return conn

        return self._send_and_wait_ack(conn.unwrap())

    def _ensure_connection(self) -> Result[object]:
        """MAVLink bağlantısını (gerekirse) açar. pymavlink/port yoksa açık hata."""
        if self._conn is not None:
            return Result.ok(self._conn)
        try:
            self._conn = self._connect_fn(self._pix.port, self._pix.baud)
        except ImportError:
            return Result.err(ErrorCode.UNAVAILABLE,
                              "pymavlink kurulu değil (donanım profili gerektirir)")
        except Exception as exc:  # pragma: no cover - donanıma özgü G/Ç hataları
            return Result.err(ErrorCode.IO_ERROR,
                              f"MAVLink bağlantısı açılamadı ({self._pix.port}): {exc}")
        return Result.ok(self._conn)

    def _send_and_wait_ack(self, conn: object) -> Result[None]:
        """DO_PARACHUTE(RELEASE) gönderir ve COMMAND_ACK'i bekleyip sonucu loglar."""
        try:
            # command_long_send(target_system, target_component, command, confirmation,
            #                    param1..param7)
            conn.mav.command_long_send(
                conn.target_system, conn.target_component,
                MAV_CMD_DO_PARACHUTE, 0,
                PARACHUTE_RELEASE, 0, 0, 0, 0, 0, 0)
        except Exception as exc:  # pragma: no cover - donanıma özgü G/Ç hataları
            self._log(f"APAM ACTUATOR: komut gönderimi başarısız: {exc}")
            return Result.err(ErrorCode.IO_ERROR, f"DO_PARACHUTE gönderilemedi: {exc}")

        ack = conn.recv_match(type="COMMAND_ACK", blocking=True,
                              timeout=self._pix.command_ack_timeout_s)
        if ack is None:
            self._log(f"APAM ACTUATOR: COMMAND_ACK zaman aşımı "
                      f"({self._pix.command_ack_timeout_s:.1f} sn) — komut teyit EDİLMEDİ")
            return Result.err(ErrorCode.TIMEOUT, "DO_PARACHUTE COMMAND_ACK zaman aşımı")

        result = getattr(ack, "result", None)
        if result == MAV_RESULT_ACCEPTED:
            self._log("APAM ACTUATOR: MAV_CMD_DO_PARACHUTE RELEASE ACCEPTED "
                      "(paraşüt açma komutu Pixhawk tarafından kabul edildi)")
            return Result.ok(None)

        self._log(f"APAM ACTUATOR: DO_PARACHUTE REDDEDİLDİ (MAV_RESULT={result})")
        return Result.err(ErrorCode.IO_ERROR,
                          f"DO_PARACHUTE reddedildi (MAV_RESULT={result})")
