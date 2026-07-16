"""
Görevi        : Profil bazlı sürücü fabrikası. Çalışma profiline göre mock veya
                gerçek telemetri linkini seçer ve FLIGHT/HIL profilinde donanım
                desteğinin varlığını denetler.
Neden Gerekli : SIMULATION_ONLY masaüstünde mock sürücülerle çalışır; FLIGHT/HIL
                gerçek donanım sürücüleri gerektirir. Yanlış profilde sessizce mock'a
                düşmek güvenlik riskidir → açık kapı (gate) gerekir.
İlişkiler     : Ana döngü telemetri linkini bu fabrikadan alabilir. Gerçek sürücüler
                (real_lora) donanım kütüphaneleri mevcutsa kullanılır.
Nasıl Test    : tests/test_driver_factory.py — SIMULATION→mock; FLIGHT donanım
                yokken açık hata; gerçek link güvenli degrade.
"""
from __future__ import annotations

import importlib.util

from config.default import AppConfig, RunProfile
from src.common.result import ErrorCode, Result
from src.drivers.mock_sensors import MockTelemetryLink
from src.drivers.real_lora import RealLoraE22Link

# FLIGHT/HIL için gerekli donanım kütüphaneleri (varlık kontrolü; import etmez).
_HARDWARE_MODULES = ("serial",)   # pyserial (LoRa/GPS UART). smbus2/pymavlink Aşama 5.


def hardware_libs_available() -> bool:
    """Gerekli donanım kütüphaneleri kurulu mu (import etmeden kontrol)."""
    return all(importlib.util.find_spec(m) is not None for m in _HARDWARE_MODULES)


def check_profile_runnable(config: AppConfig) -> Result[None]:
    """
    Profilin bu ortamda çalıştırılabilir olduğunu doğrular. SIMULATION her zaman
    çalışır; FLIGHT/HIL donanım kütüphaneleri yoksa açık hata döndürür.
    """
    if config.profile is RunProfile.SIMULATION_ONLY:
        return Result.ok(None)
    if not hardware_libs_available():
        return Result.err(
            ErrorCode.UNAVAILABLE,
            f"{config.profile.value} profili donanım kütüphanelerini gerektirir "
            f"(eksik: {[m for m in _HARDWARE_MODULES if importlib.util.find_spec(m) is None]}). "
            "requirements-hardware.txt kurulmalı ve gerçek donanımda çalıştırılmalı.")
    return Result.ok(None)


def create_telemetry_link(config: AppConfig, port: str = "/dev/ttyAMA0"):
    """
    Profile göre telemetri linki döndürür. SIMULATION → MockTelemetryLink;
    FLIGHT/HIL → RealLoraE22Link (henüz açık değil; open() donanımda çağrılır).
    """
    if config.profile is RunProfile.SIMULATION_ONLY:
        return MockTelemetryLink()
    return RealLoraE22Link(port, config.telemetry)
