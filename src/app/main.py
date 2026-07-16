"""
Görevi        : Ana uygulama döngüsü. Bağımlılıkları kurar, aktüatörleri Safe
                State'e alır, sabit periyotlu SINIRLI döngüde sensör okur, uçuş
                bağlamı üretir, sağlık/failsafe/durum makinesini günceller ve 1 Hz
                telemetri paketi üretir. `--max-cycles`/`--duration` ile sınırlıdır.
Neden Gerekli : ANA_PROMPT F.10 + agentic_execution — süreç ASLA sonsuz çalışmaz.
                Tüm katmanları çalışan bir iskelette birleştirir.
İlişkiler     : config, clock, persistence, mock sürücüler, telemetri servisi,
                state machine, health, failsafe. Enjeksiyon ile test edilebilir.
Nasıl Test    : tests/test_app_integration.py — sınırlı koşu, paket üretimi, CSV,
                determinizm, APAM senaryosu (runaway profil).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

from config.default import AppConfig, get_config
from src.common.clock import Clock, FakeClock
from src.control.descent_controller import DescentController
from src.control.estimator import StateEstimator
from src.drivers.flight_profile import FlightProfile
from src.drivers.mock_actuators import ActuatorSuite
from src.drivers.mock_sensors import (
    MockBarometer,
    MockBattery,
    MockGps,
    MockImu,
    MockTelemetryLink,
)
from src.drivers.sim_flight_controller import SimulatedFlightControllerLink
from src.hal.interfaces import ServoPosition
from src.mission.context import FlightContext
from src.services.failsafe import FailsafeManager
from src.services.health_monitor import HealthInputs, HealthMonitor
from src.services.motor_health import MotorHealthMonitor
from src.services.persistence import PersistenceStore
from src.state_machine.flight_state_machine import FlightPhase, FlightStateMachine
from src.telemetry.packet import (
    ArasInputs,
    TelemetryFields,
    TelemetryPacketBuilder,
    compute_error_code,
)
from src.telemetry.telemetry_service import TelemetryService


@dataclass
class RunSummary:
    """Bir koşunun özeti (test ve raporlama için)."""

    cycles: int
    packets: int
    final_phase: FlightPhase
    final_status: int
    apam_triggered: bool
    last_telemetry: str
    parachute_deployed: bool
    motor_fault_detected: bool = False
    max_throttle: float = 0.0
    motors_ever_armed: bool = False


class SimClock(FakeClock):
    """Simülasyon saati: gerçek zaman beklemeden her çevrimde ilerletilir."""


def build_and_run(config: AppConfig, max_cycles: int, duration_s: float | None,
                  clock: Clock | None = None, profile_name: str = "nominal_descent",
                  event_sink=None, motor_fault_factor: float = 1.0) -> RunSummary:
    """
    Sınırlı döngüyü kurar ve çalıştırır. `clock` verilmezse SimClock kullanılır
    (deterministik, gerçek zaman beklemesiz). `event_sink(str)` log satırlarını alır.
    """
    log = event_sink if event_sink is not None else (lambda s: None)
    period = config.loop_period_s
    clk = clock if clock is not None else SimClock()

    # Görev zamanı kaynağı ve profil.
    profile = FlightProfile(profile_name, config.mission.release_altitude_m)

    # Kalıcılık
    persistence = PersistenceStore(config.paths.persistence_file, clk)
    load = persistence.load()
    if load.is_err:
        raise RuntimeError(f"Kalıcı durum yüklenemedi: {load.message}")

    def mission_time() -> float:
        return persistence.mission_time_s()

    # Sürücüler (mock)
    baro = MockBarometer(clk, profile, mission_time)
    imu = MockImu(clk, profile, mission_time)
    gps = MockGps(clk, profile, mission_time)
    batt = MockBattery(clk, profile, mission_time)
    link = MockTelemetryLink()
    actuators = ActuatorSuite()

    # GÜVENLİK: başlangıçta Safe State (motorlar disarm, servolar güvenli).
    actuators.enter_safe_state()
    log("BOOT: aktüatörler Safe State'e alındı (SIMULATION_ONLY)")

    # Servisler
    builder = TelemetryPacketBuilder(
        decimal_places=config.telemetry.decimal_places,
        separator=config.telemetry.field_separator)
    telemetry = TelemetryService(builder, link, config.paths.telemetry_csv)
    health = HealthMonitor(config.health)
    failsafe = FailsafeManager(config.apam)
    state = FlightStateMachine(config.mission)

    # Baro sıfırlama (kalkış = 0 m). Referans basınç YALNIZ ilk boot'ta yakalanır
    # ve kalıcı depoya yazılır; işlemci yeniden başlarsa aynı referans kullanılır
    # (restart sonrası irtifa tutarlılığı — G-17 ile aynı ruh, EKSİK-003).
    zero_alt_pressure = persistence.altitude_zero_ref()
    if zero_alt_pressure is None:
        first_baro = baro.read()
        if first_baro.is_ok:
            zero_alt_pressure = first_baro.unwrap().pressure_pa
            persistence.set_altitude_zero_ref(zero_alt_pressure)
            log(f"BOOT: barometre sıfırlandı (referans {zero_alt_pressure:.0f} Pa)")

    # Aşama 2: kontrol & navigasyon bileşenleri.
    estimator = StateEstimator(config.control, zero_alt_pressure or 101325.0)
    controller = DescentController(config.control, config.mission)
    motor_health = MotorHealthMonitor(config.control)
    # FC link, yönelimi kestiriciden okur (en güncel füzyon çıktısı).
    attitude_holder = {"att": (0.0, 0.0, 0.0)}
    fc_link = SimulatedFlightControllerLink(
        config.control, clk, attitude_fn=lambda: attitude_holder["att"])
    if motor_fault_factor < 1.0:
        fc_link.set_motor_fault(motor_fault_factor)   # test/senaryo enjeksiyonu

    # Döngü durumu
    separation_confirmed = False
    arms_deployed = False
    motor_fault_prev = False
    last_link_ok_s = clk.now_monotonic()
    next_telemetry_at = 0.0     # görev zamanı; ilk pakette hemen üretir
    packets = 0
    apam_ever = False
    motor_fault_ever = False
    max_throttle = 0.0
    motors_ever_armed = False

    cycle = 0
    while cycle < max_cycles:
        cycle_start = clk.now_monotonic()
        t = mission_time()
        if duration_s is not None and t >= duration_s:
            break

        # --- Sensörleri oku ---
        b = baro.read()
        i = imu.read()
        g = gps.read()
        v = batt.read()
        any_valid = any(r.is_ok for r in (b, i, g, v))
        newest_ts = max((r.unwrap().timestamp_s for r in (b, i, g, v) if r.is_ok),
                        default=cycle_start)

        # --- Sensör füzyonu (Aşama 2): irtifa/hız/yönelim + çoklu-sensör tutarlılık ---
        est = estimator.update(b, i, g, dt=period)
        attitude_holder["att"] = (est.pitch_deg, est.roll_deg, est.yaw_deg)
        altitude = est.altitude_m
        descent_speed = est.vertical_speed_mps
        ascending = descent_speed < -0.5
        gps_valid = est.gps_valid

        # --- Görev mantığı: otonom ayrılma ve kol açma (Aşama 1 iskelet) ---
        sep_alt = config.mission.separation_altitude_m
        if (not separation_confirmed and not ascending
                and altitude <= sep_alt and t > 0.0
                and state.phase in (FlightPhase.CARRIER_DESCENT,
                                    FlightPhase.SEPARATION)):
            actuators.separation_servo.move_to(ServoPosition.OPEN)
            separation_confirmed = True
            log(f"SEPARATION: ~{altitude:.0f} m otonom ayrılma komutu")
        if separation_confirmed and not arms_deployed and \
                state.phase in (FlightPhase.SEPARATION, FlightPhase.ARM_DEPLOY):
            actuators.arms.deploy_and_lock()
            arms_deployed = True
            log("ARM_DEPLOY: SİGMA kolları açıldı ve kilitlendi")

        # --- Sağlık ---
        loop_dur = max(0.0, clk.now_monotonic() - cycle_start)
        if link.is_connected():
            last_link_ok_s = clk.now_monotonic()
        hflags = health.evaluate(HealthInputs(
            now_s=clk.now_monotonic(),
            newest_sensor_timestamp_s=newest_ts,
            any_sensor_valid=any_valid,
            battery_v=v.unwrap().voltage_v if v.is_ok else 0.0,
            last_link_ok_s=last_link_ok_s,
            loop_duration_s=loop_dur,
            loop_period_s=period,
        ))

        # --- Failsafe / APAM ---
        ctx = FlightContext(
            mission_time_s=t, altitude_m=altitude, descent_speed_mps=descent_speed,
            ascending=ascending, gps_valid=gps_valid,
            separation_confirmed=separation_confirmed, arms_deployed=arms_deployed,
            speed_consistent=est.speed_consistent, motor_fault=motor_fault_prev,
            health=hflags)
        decision = failsafe.update(ctx)
        if decision.apam_should_deploy:
            res = failsafe.execute_apam(actuators)
            log(f"APAM: {decision.reason} | sıra motor-kill→paraşüt "
                f"({'ok' if res.is_ok else res.message})")
        ctx.apam_active = decision.apam_active
        apam_ever = apam_ever or decision.apam_active

        # --- Durum makinesi ---
        if hflags.any_fault() and state.phase in (
                FlightPhase.BOOT, FlightPhase.READY_TO_FLY):
            # Ayrılma öncesi kritik arıza → FAULT (güvenli tarafta kal).
            state.to_fault(ctx)
        else:
            state.update(ctx)

        # --- Kontrol & Navigasyon (Aşama 2): aktif iniş throttle üretimi ---
        cmd = controller.compute(state.phase, descent_speed, altitude, dt=period)
        if decision.apam_active:
            # APAM aktifse motorlar zaten kill edildi; kontrol devreye girmez.
            applied_throttle = 0.0
        elif cmd.active:
            if actuators.motors.arm_state.name != "ARMED":
                actuators.motors.arm()
                motors_ever_armed = True
                log(f"CONTROL: motorlar arm edildi (faz {state.phase.value})")
            actuators.motors.set_throttle(cmd.throttle)
            fc_link.send_setpoint(cmd.throttle, target_alt_m=altitude)
            applied_throttle = cmd.throttle
            max_throttle = max(max_throttle, cmd.throttle)
        else:
            # Pasif faz: motorları güvenli konuma al (disarm/0).
            if actuators.motors.arm_state.name == "ARMED":
                actuators.motors.disarm()
            applied_throttle = 0.0

        # --- Motor sağlığı (PWM/RPM tutarlılık) ---
        fc_tlm = fc_link.read_telemetry()
        actual_rpm = min(fc_tlm.unwrap().motor_rpm) if fc_tlm.is_ok else 0.0
        mh = motor_health.update(applied_throttle, actual_rpm, dt=period)
        if mh.fault and not motor_fault_prev:
            log(f"MOTOR ARIZA: beklenen {mh.expected_rpm:.0f} RPM, "
                f"gerçek {actual_rpm:.0f} RPM ({mh.mismatch_timer_s:.1f} sn tutarsız)")
        motor_fault_prev = mh.fault
        motor_fault_ever = motor_fault_ever or mh.fault

        # --- Telemetri (1 Hz) ---
        if t >= next_telemetry_at:
            next_telemetry_at = t + config.telemetry_period_s
            pn = persistence.next_packet_number().unwrap()
            speed_check = state.phase in (
                FlightPhase.ACTIVE_DESCENT, FlightPhase.FINAL_APPROACH)
            error_code = compute_error_code(ArasInputs(
                descent_speed_mps=descent_speed,
                speed_check_active=speed_check,
                gps_valid=gps_valid,
                separation_done=separation_confirmed,
                apam_active=decision.apam_active,
                target_speed_min=config.mission.target_descent_speed_range[0],
                target_speed_max=config.mission.target_descent_speed_range[1],
            ), digits=config.telemetry.error_code_digits)

            gps_r = g.unwrap() if g.is_ok else None
            fields = TelemetryFields(
                packet_number=pn,
                status=state.status_code(),
                error_code=error_code,
                send_time=clk.now_utc(),
                pressure_pa=b.unwrap().pressure_pa if b.is_ok else 0.0,
                altitude_m=altitude,
                descent_speed_mps=descent_speed,
                temperature_c=b.unwrap().temperature_c if b.is_ok else 0.0,
                battery_v=v.unwrap().voltage_v if v.is_ok else 0.0,
                gps_lat=gps_r.latitude if gps_r else 0.0,
                gps_lon=gps_r.longitude if gps_r else 0.0,
                gps_alt_m=gps_r.altitude_m if gps_r else 0.0,
                # Yönelim, füzyon kestiriminden (aykırı reddi uygulanmış).
                pitch_deg=est.pitch_deg,
                roll_deg=est.roll_deg,
                yaw_deg=est.yaw_deg,
                rhrhrh="",       # BONUS-2 Aşama 3'te doldurulur
                team_number=config.team_number,
            )
            pub = telemetry.publish(fields)
            if pub.is_ok:
                packets += 1

        # --- Çevrim ilerlet ---
        cycle += 1
        if isinstance(clk, FakeClock):
            clk.advance(period)     # sim: gerçek zaman beklemeden ilerle

    # KAPANIŞ: Safe State (güvenlik).
    actuators.enter_safe_state()
    log(f"SHUTDOWN: {cycle} çevrim, {packets} paket; Safe State'e alındı")

    return RunSummary(
        cycles=cycle,
        packets=packets,
        final_phase=state.phase,
        final_status=int(state.status_code()),
        apam_triggered=apam_ever,
        last_telemetry=telemetry.last_line,
        parachute_deployed=failsafe.parachute_deployed,
        motor_fault_detected=motor_fault_ever,
        max_throttle=max_throttle,
        motors_ever_armed=motors_ever_armed,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="KILAVUZ MİRASAT Uçuş Yazılımı — SINIRLI simülasyon koşusu")
    parser.add_argument("--config", default="simulation",
                        help="Çalışma profili (varsayılan: simulation)")
    parser.add_argument("--max-cycles", type=int, default=100,
                        help="Maksimum döngü sayısı (sonsuz döngü önlemi)")
    parser.add_argument("--duration", type=float, default=None,
                        help="Simüle görev süresi (saniye) üst sınırı")
    parser.add_argument("--profile", default="nominal_descent",
                        choices=["nominal_descent", "runaway_descent"],
                        help="Simülasyon uçuş profili")
    parser.add_argument("--motor-fault", type=float, default=1.0,
                        help="Motor verim faktörü (1.0 sağlıklı, <1 arıza enjekte)")
    args = parser.parse_args(argv)

    config = get_config(args.config)
    # Güvenlik teyidi: yalnız SIMULATION_ONLY desteklenir.
    if not config.is_simulation:
        raise SystemExit("Yalnızca SIMULATION_ONLY profili desteklenir (Aşama 2).")

    summary = build_and_run(
        config, max_cycles=args.max_cycles, duration_s=args.duration,
        profile_name=args.profile, event_sink=print,
        motor_fault_factor=args.motor_fault)

    print("--- KOŞU ÖZETİ ---")
    print(f"Çevrim: {summary.cycles}  Paket: {summary.packets}")
    print(f"Son faz: {summary.final_phase.value}  Statü kodu: {summary.final_status}")
    print(f"APAM tetiklendi: {summary.apam_triggered}  "
          f"Paraşüt açıldı: {summary.parachute_deployed}")
    print(f"Motorlar arm edildi: {summary.motors_ever_armed}  "
          f"Maks throttle: {summary.max_throttle:.2f}  "
          f"Motor arıza: {summary.motor_fault_detected}")
    print(f"Son telemetri: {summary.last_telemetry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
