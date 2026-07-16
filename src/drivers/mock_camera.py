"""
Görevi        : Mock kamera ve mock canlı video akış bağı. SIMULATION_ONLY'de
                gerçek CSI kamera veya Wi-Fi olmadan kare üretimini, SD kaydını ve
                akış durumunu modeller.
Neden Gerekli : Gereksinim-20/21/22 (yanal ≥720p kamera, SD kayıt + canlı akış).
                Fiziksel kamera yokken kayıt/akış mimarisini test edilebilir kılar.
İlişkiler     : HAL Camera / VideoStreamLink arayüzlerini uygular; CameraService
                kullanır. Gerçek picamera2/H.264 sürücüsü Aşama 5'e ertelenmiştir.
Nasıl Test    : tests/test_camera.py (dolaylı, CameraService üzerinden) — çözünürlük
                doğrulama, kare sayımı, akış kopukluğu.
"""
from __future__ import annotations

from src.common.result import ErrorCode, Result

_MIN_HEIGHT = 720   # Gereksinim-21


class MockCamera:
    """Kare indeksini artırır; SD'ye 'kayıt' için yalnız sayaç tutar."""

    def __init__(self) -> None:
        self._recording = False
        self._frame_index = 0
        self._resolution = (0, 0)

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def frames_captured(self) -> int:
        return self._frame_index

    @property
    def resolution(self) -> tuple:
        return self._resolution

    def start(self, width: int, height: int) -> Result[None]:
        if height < _MIN_HEIGHT:
            return Result.err(ErrorCode.OUT_OF_RANGE,
                              f"çözünürlük min 720p olmalı: {width}x{height}")
        self._resolution = (width, height)
        self._recording = True
        return Result.ok(None)

    def capture(self) -> Result[int]:
        if not self._recording:
            return Result.err(ErrorCode.UNAVAILABLE, "kamera kayıtta değil")
        idx = self._frame_index
        self._frame_index += 1
        return Result.ok(idx)

    def stop(self) -> Result[None]:
        self._recording = False
        return Result.ok(None)


class MockWifiVideoLink:
    """Canlı video akış bağı (5 GHz Wi-Fi mock). Kopukluk enjekte edilebilir."""

    def __init__(self) -> None:
        self._connected = True
        self.streamed_frames: list[int] = []

    def set_connected(self, value: bool) -> None:
        self._connected = value

    def is_connected(self) -> bool:
        return self._connected

    def stream_frame(self, frame_index: int) -> Result[None]:
        if not self._connected:
            return Result.err(ErrorCode.UNAVAILABLE, "video akış bağı kopuk")
        self.streamed_frames.append(frame_index)
        return Result.ok(None)
