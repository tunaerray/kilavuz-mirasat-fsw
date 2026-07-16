"""Teslim paketi aracı testleri (Şartname §2.4 teslim düzeni)."""
import zipfile

from src.common.result import ErrorCode
from src.telemetry.packet import FIELD_HEADERS, FIELD_UNITS
from tools.package_submission import build_submission, validate_telemetry_csv

HEADER = ",".join(FIELD_HEADERS)
UNITS = ",".join(FIELD_UNITS)
ROW = ("1,0,0000,04/05/2026 14:32:10,101325.0,0.0,0.0,28.0,16.4,"
       "39.9255,32.8663,15.0,0.0,0.0,0.0,,947450")


def _write_csv(path, header=HEADER, units=UNITS, rows=(ROW,)):
    path.write_text("\n".join([header, units, *rows]) + "\n", encoding="utf-8")
    return str(path)


def test_validate_ok(tmp_path):
    p = _write_csv(tmp_path / "tlm.csv")
    r = validate_telemetry_csv(p)
    assert r.is_ok and r.unwrap() == 1        # 1 veri satırı


def test_validate_bad_header(tmp_path):
    p = _write_csv(tmp_path / "tlm.csv", header="WRONG,HEADER")
    r = validate_telemetry_csv(p)
    assert r.is_err and r.code is ErrorCode.INVALID_DATA


def test_validate_bad_units(tmp_path):
    p = _write_csv(tmp_path / "tlm.csv", units="x,y,z")
    assert validate_telemetry_csv(p).is_err


def test_validate_wrong_field_count(tmp_path):
    p = _write_csv(tmp_path / "tlm.csv", rows=("1,2,3",))
    assert validate_telemetry_csv(p).is_err


def test_build_submission_produces_files(tmp_path):
    tlm = _write_csv(tmp_path / "tlm.csv")
    out = tmp_path / "submission"
    res = build_submission(947450, tlm, str(_project_root()), str(out))
    assert res.is_ok
    s = res.unwrap()
    assert s.telemetry_path.endswith("TMUY2026_947450_TLM.csv")
    assert s.software_zip_path.endswith("TMUY2026_947450_UCUSYAZILIMI.zip")
    assert s.telemetry_valid
    assert (out / "TMUY2026_947450_TLM.csv").exists()
    assert (out / "TMUY2026_947450_UCUSYAZILIMI.zip").exists()


def test_software_zip_contains_source(tmp_path):
    tlm = _write_csv(tmp_path / "tlm.csv")
    out = tmp_path / "submission"
    build_submission(947450, tlm, str(_project_root()), str(out)).unwrap()
    with zipfile.ZipFile(out / "TMUY2026_947450_UCUSYAZILIMI.zip") as zf:
        names = zf.namelist()
    # kaynak kod ve config paketlendi
    assert any(n.replace("\\", "/").endswith("src/app/main.py") for n in names)
    assert any(n.replace("\\", "/").endswith("config/default.py") for n in names)
    # üretilen/çöp dizinler hariç
    assert not any("__pycache__" in n for n in names)
    assert not any("run_data" in n for n in names)


def test_build_reports_invalid_telemetry(tmp_path):
    bad = _write_csv(tmp_path / "bad.csv", header="NOPE")
    out = tmp_path / "sub"
    res = build_submission(947450, bad, str(_project_root()), str(out))
    # paket yine üretilir ama doğrulama başarısız işaretlenir
    assert res.is_ok
    assert not res.unwrap().telemetry_valid


def _project_root():
    import os
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
