"""
Görevi        : Yarışma teslim paketi aracı. Telemetri CSV'sini şartname formatına
                göre doğrular ve teslim dosyalarını üretir:
                  TMUY2026_<TAKIMNO>_TLM.csv          (telemetri kaydı)
                  TMUY2026_<TAKIMNO>_UCUSYAZILIMI.zip (uçuş yazılımı kaynak paketi)
Neden Gerekli : Şartname §2.4 (teslim dosya adları) + NOT (sıra/başlık/birim yanlışsa
                %2 uçuş puanı kesintisi). Teslimi otomatik ve doğrulanmış hale getirir.
İlişkiler     : src.telemetry.packet FIELD_HEADERS/UNITS ile format doğrular; uçuş
                yazılımı kaynak ağacını zip'ler. Ana FSW'yi değiştirmez (salt araç).
Nasıl Test    : tests/test_package_submission.py — format doğrulama (geçerli/geçersiz),
                paket üretimi, dosya adları, zip içeriği.
"""
from __future__ import annotations

import argparse
import os
import shutil
import zipfile
from dataclasses import dataclass

from src.common.result import ErrorCode, Result
from src.telemetry.packet import FIELD_HEADERS, FIELD_UNITS

# Uçuş yazılımı teslim paketine dahil edilecek yollar (proje köküne göre).
_INCLUDE = ("src", "config", "docs", "tests", "tools",
            "README.md", "TASK_TRACKER.md", "pytest.ini",
            "requirements-dev.txt", "requirements-hardware.txt", ".github")
# Hariç tutulacak desenler (yol parçası eşleşmesi).
_EXCLUDE_PARTS = ("__pycache__", ".pytest_cache", "run_data",
                  "graphify-out", ".git")


@dataclass
class SubmissionResult:
    telemetry_path: str
    software_zip_path: str
    telemetry_rows: int
    telemetry_valid: bool
    validation_detail: str


def validate_telemetry_csv(path: str) -> Result[int]:
    """
    Telemetri CSV'sini şartname §2.4 düzenine göre doğrular: 1. satır başlık,
    2. satır birim (tam sıra), sonraki satırlar 17 alan. Veri satırı sayısını döner.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.rstrip("\n") for ln in f]
    except OSError as exc:
        return Result.err(ErrorCode.IO_ERROR, f"CSV okunamadı: {exc}")
    if len(lines) < 2:
        return Result.err(ErrorCode.INVALID_DATA, "CSV başlık/birim satırı eksik")

    expected_header = ",".join(FIELD_HEADERS)
    expected_units = ",".join(FIELD_UNITS)
    if lines[0] != expected_header:
        return Result.err(ErrorCode.INVALID_DATA,
                          "başlık satırı şartname sırasına uymuyor (%2 kesinti riski)")
    if lines[1] != expected_units:
        return Result.err(ErrorCode.INVALID_DATA,
                          "birim satırı şartname düzenine uymuyor (%2 kesinti riski)")
    data_rows = [ln for ln in lines[2:] if ln.strip()]
    for i, row in enumerate(data_rows, start=3):
        if len(row.split(",")) != 17:
            return Result.err(ErrorCode.INVALID_DATA,
                              f"{i}. satır 17 alan değil")
    return Result.ok(len(data_rows))


def _should_include(path_parts) -> bool:
    return not any(part in _EXCLUDE_PARTS for part in path_parts)


def build_submission(team_number: int, telemetry_csv: str, project_root: str,
                     output_dir: str) -> Result[SubmissionResult]:
    """Teslim dosyalarını `output_dir` altında üretir."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Telemetri CSV doğrula + kopyala.
    valid = validate_telemetry_csv(telemetry_csv)
    tlm_name = f"TMUY2026_{team_number}_TLM.csv"
    tlm_dst = os.path.join(output_dir, tlm_name)
    try:
        shutil.copyfile(telemetry_csv, tlm_dst)
    except OSError as exc:
        return Result.err(ErrorCode.IO_ERROR, f"telemetri kopyalanamadı: {exc}")

    # 2. Uçuş yazılımı kaynak ağacını zip'le.
    zip_name = f"TMUY2026_{team_number}_UCUSYAZILIMI.zip"
    zip_dst = os.path.join(output_dir, zip_name)
    try:
        with zipfile.ZipFile(zip_dst, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in _INCLUDE:
                src_path = os.path.join(project_root, item)
                if not os.path.exists(src_path):
                    continue
                if os.path.isfile(src_path):
                    zf.write(src_path, item)
                    continue
                for root, dirs, files in os.walk(src_path):
                    dirs[:] = [d for d in dirs if d not in _EXCLUDE_PARTS]
                    for fn in files:
                        full = os.path.join(root, fn)
                        rel = os.path.relpath(full, project_root)
                        if _should_include(rel.split(os.sep)):
                            zf.write(full, rel)
    except OSError as exc:
        return Result.err(ErrorCode.IO_ERROR, f"yazılım paketi oluşturulamadı: {exc}")

    return Result.ok(SubmissionResult(
        telemetry_path=tlm_dst,
        software_zip_path=zip_dst,
        telemetry_rows=valid.unwrap_or(0),
        telemetry_valid=valid.is_ok,
        validation_detail="OK" if valid.is_ok else valid.message,
    ))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="TÜRKSAT Model Uydu teslim paketi üretici")
    parser.add_argument("--team", type=int, default=947450, help="Takım numarası")
    parser.add_argument("--telemetry", default="run_data/TMUY2026_947450_TLM.csv",
                        help="Telemetri CSV yolu")
    parser.add_argument("--root", default=".", help="Proje kök dizini")
    parser.add_argument("--out", default="submission", help="Çıktı dizini")
    args = parser.parse_args(argv)

    res = build_submission(args.team, args.telemetry, args.root, args.out)
    if res.is_err:
        print(f"HATA: {res.message}")
        return 1
    s = res.unwrap()
    print("--- TESLİM PAKETİ ---")
    print(f"Telemetri : {s.telemetry_path} ({s.telemetry_rows} satır, "
          f"doğrulama: {s.validation_detail})")
    print(f"Yazılım   : {s.software_zip_path}")
    return 0 if s.telemetry_valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
