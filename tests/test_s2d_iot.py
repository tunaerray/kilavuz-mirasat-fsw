"""BONUS-2 S2D-IOT servisi testleri — Şartname §2.3 (REQ-BONUS-002)."""
from src.common.result import ErrorCode
from src.drivers.mock_sensors import MockIotLink
from src.services.s2d_iot import LedState, S2dIotService, parse_password


def _svc(tmp_path, iot=None):
    return S2dIotService(iot or MockIotLink(), str(tmp_path / "s2d.csv"))


# --- ayrıştırma ---
def test_parse_valid_example():
    # Şartname örneği 2R0G1B: kırmızı flashing, yeşil open, mavi close
    cmd = parse_password("2R0G1B").unwrap()
    assert cmd.red is LedState.FLASHING
    assert cmd.green is LedState.OPEN
    assert cmd.blue is LedState.CLOSE
    assert cmd.password == "2R0G1B"


def test_parse_all_states():
    cmd = parse_password("0R1G2B").unwrap()
    assert (cmd.red, cmd.green, cmd.blue) == (LedState.OPEN, LedState.CLOSE, LedState.FLASHING)


def test_parse_wrong_length():
    assert parse_password("2R0G1").code is ErrorCode.INVALID_DATA
    assert parse_password("2R0G1BB").code is ErrorCode.INVALID_DATA


def test_parse_wrong_letters():
    # Gecersiz harf reddedilir
    assert parse_password("2X0R1B").code is ErrorCode.INVALID_DATA
    # Ayni harf iki kez reddedilir
    assert parse_password("2R0R1B").code is ErrorCode.INVALID_DATA


def test_parse_letter_order_is_free():
    """
    Sartname §2.3 harf sirasini SABITLEMEZ; sadece Rakam-Harf ikilisinin uc kez
    tekrarlandigini soyler. Hakemler ucus aninda takima ozgu sifre verir ve
    '2G0R1B' gibi bir sirayla gelebilir. Reddedilirse BONUS-2 puani kaybedilir.
    LED eslemesi konuma degil HARFE gore yapilmalidir.
    """
    r = parse_password("2G0R1B")
    assert r.is_ok
    cmd = r.unwrap()
    assert cmd.green is LedState.FLASHING   # 2G
    assert cmd.red is LedState.OPEN         # 0R
    assert cmd.blue is LedState.CLOSE       # 1B

def test_parse_bad_digit():
    assert parse_password("3R0G1B").code is ErrorCode.INVALID_DATA
    assert parse_password("2R9G1B").code is ErrorCode.INVALID_DATA


# --- servis akışı ---
def test_process_records_and_forwards(tmp_path):
    iot = MockIotLink()
    svc = _svc(tmp_path, iot)
    r = svc.process("2R0G1B")
    assert r.is_ok
    assert svc.current_password == "2R0G1B"
    assert iot.forwarded == ["2R0G1B"]           # IoT'a yönlendirildi
    csv = (tmp_path / "s2d.csv").read_text(encoding="utf-8").strip()
    assert csv.startswith("2R0G1B")               # SD'ye kaydedildi
    assert svc.received_count == 1 and svc.forwarded_count == 1


def test_invalid_password_no_side_effects(tmp_path):
    iot = MockIotLink()
    svc = _svc(tmp_path, iot)
    r = svc.process("BADCMD")
    assert r.is_err
    assert svc.current_password == ""             # durum değişmedi
    assert iot.forwarded == []                    # yönlendirilmedi
    assert not (tmp_path / "s2d.csv").exists()     # kayıt yok


def test_state_maintained_until_new(tmp_path):
    svc = _svc(tmp_path)
    svc.process("2R0G1B").unwrap()
    # geçersiz yeni şifre → eski durum korunur
    svc.process("nope!!")
    assert svc.current_password == "2R0G1B"
    # geçerli yeni şifre → durum güncellenir
    svc.process("1R1G1B").unwrap()
    assert svc.current_password == "1R1G1B"


def test_forward_failure_still_records(tmp_path):
    iot = MockIotLink()
    iot.set_connected(False)
    svc = _svc(tmp_path, iot)
    r = svc.process("2R0G1B")
    assert r.is_err and r.code is ErrorCode.UNAVAILABLE
    # kayıt yapıldı ve durum korunur; yalnız yönlendirme başarısız
    assert svc.current_password == "2R0G1B"
    assert svc.received_count == 1 and svc.forwarded_count == 0
    assert (tmp_path / "s2d.csv").exists()
