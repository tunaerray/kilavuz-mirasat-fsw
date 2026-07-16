"""Kamera servisi testleri (REQ-TLM-010, Gereksinim-20/21/22)."""
from config.default import VideoConfig
from src.common.result import ErrorCode
from src.drivers.mock_camera import MockCamera, MockWifiVideoLink
from src.services.camera_service import CameraService


def _svc(fps=30, height=720):
    cam = MockCamera()
    wifi = MockWifiVideoLink()
    cfg = VideoConfig(fps=fps, height=height)
    return CameraService(cam, wifi, cfg), cam, wifi


def test_start_validates_resolution():
    svc, cam, _ = _svc(height=480)         # 720p altı
    r = svc.start()
    assert r.is_err and r.code is ErrorCode.OUT_OF_RANGE
    assert not cam.is_recording


def test_start_ok_720p():
    svc, cam, _ = _svc(height=720)
    assert svc.start().is_ok
    assert cam.is_recording
    assert cam.resolution == (1280, 720)


def test_frames_captured_per_fps():
    svc, _, _ = _svc(fps=30)
    svc.start()
    st = svc.tick(1.0)                       # 1 sn → 30 kare
    assert st.frames_recorded == 30
    assert st.frames_streamed == 30
    assert st.frames_dropped_stream == 0


def test_partial_second_accumulates():
    svc, _, _ = _svc(fps=10)
    svc.start()
    svc.tick(0.05)                           # 0.5 kare → henüz 0
    assert svc.frames_recorded == 0
    svc.tick(0.05)                           # toplam 0.1 sn → 1 kare
    assert svc.frames_recorded == 1


def test_recording_continues_when_stream_down():
    svc, _, wifi = _svc(fps=10)
    svc.start()
    wifi.set_connected(False)
    st = svc.tick(1.0)                        # 10 kare
    assert st.frames_recorded == 10          # SD kaydı sürer
    assert st.frames_streamed == 0
    assert st.frames_dropped_stream == 10    # akış düştü


def test_stream_resumes_after_reconnect():
    svc, _, wifi = _svc(fps=10)
    svc.start()
    wifi.set_connected(False)
    svc.tick(1.0)                            # 10 düşük
    wifi.set_connected(True)
    svc.tick(1.0)                            # 10 akıtıldı
    assert svc.frames_streamed == 10
    assert svc.frames_dropped_stream == 10
    assert svc.frames_recorded == 20


def test_no_capture_before_start():
    svc, _, _ = _svc()
    st = svc.tick(1.0)                        # start çağrılmadı
    assert st.frames_recorded == 0
    assert not st.recording
