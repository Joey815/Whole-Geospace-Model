#!/usr/bin/env python3
"""Archive a compact WACCM-X 2024-10-03 flare/no-flare science result.

The source WACCM-X NetCDF products and full quicklook trees are large.  This
script collects a shareable evidence package: namelist control differences,
history-file inventory, forcing summary, selected 12:00-13:00 UT key frames,
and paths to the full local products.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple


COLLAB_ROOT = Path(__file__).resolve().parents[1]
USER_ROOT = Path("/home/jiaoy_group/jiaoy")
WACCMX_ROOT = USER_ROOT / "data" / "WACCMX"

FLARE_CASE = "waccmx_fism2_flare_f09_20241003_x9_r5_5min"
NOFLARE_CASE = "waccmx_fism2_noflare_f09_20241003_x9_r5_5min"

CASE_ROOT = WACCMX_ROOT / "cases"
OUT_ROOT = WACCMX_ROOT / "output" / "cesm_2.2.0_result" / "intel"
SOLAR_ROOT = WACCMX_ROOT / "inputdata" / "solar" / "fism2_20241003_x9"
QL_ROOT = WACCMX_ROOT / "quicklook"

DEFAULT_OUT = COLLAB_ROOT / "logs" / "waccmx_20241003_flare_noflare_science_20260527"

# Keep the GitHub archive compact.  Full 5-minute quicklook trees remain in
# the local WACCM-X quicklook directory and are recorded in source_paths.tsv.
KEY_TIMES = ["1230"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def copy_file(src: Path, dst: Path, copied: List[Tuple[Path, Path]]) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    copied.append((src, dst))


def write_lines(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def extract_solar_file(atm_in: Path) -> str:
    text = read_text(atm_in)
    match = re.search(r"solar_euv_data_file\s*=\s*'([^']+)'", text)
    if match:
        return match.group(1)
    return ""


def hist_inventory(case: str) -> List[Dict[str, Any]]:
    run_dir = OUT_ROOT / case / "run"
    rows = []
    for stream in ["h1", "h2", "h3", "h4", "h6"]:
        files = sorted(run_dir.glob(f"{case}.cam.{stream}.*.nc"))
        for path in files:
            rows.append(
                {
                    "case": case,
                    "stream": stream,
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "mtime": dt.datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                }
            )
    return rows


def collect_key_frames(out_dir: Path, copied: List[Tuple[Path, Path]]) -> List[Dict[str, str]]:
    frame_specs = []

    ql_global = QL_ROOT / "fism2_20241003_x9_r5_5min_global_maps"
    ql_ne = QL_ROOT / "fism2_20241003_x9_r5_5min_electron_density_altitudes"
    ql_talt = QL_ROOT / "fism2_20241003_x9_r5_5min_temperature_altitudes"
    ql_t250 = QL_ROOT / "fism2_20241003_x9_r5_5min_250km_T_TEC"

    for name in [
        "global_T_TEC_flare_noflare_diff_windowmean_1210_1305UT.png",
        "global_T_flare_noflare_diff_windowmean_1210_1305UT.png",
        "global_TEC_flare_noflare_diff_windowmean_1210_1305UT.png",
    ]:
        frame_specs.append(("window_mean", ql_global / name))

    for hhmm in KEY_TIMES:
        frame_specs.extend(
            [
                (
                    "global_T_TEC_with_fism",
                    ql_global
                    / "all_times_with_fism"
                    / f"global_T_TEC_flare_noflare_diff_20241003_{hhmm}UT.png",
                ),
                (
                    "electron_density_altitudes",
                    ql_ne
                    / "1000_1400_with_fism_nature"
                    / f"electron_density_30_60_90_150_250km_flare_noflare_logratio_20241003_{hhmm}UT.png",
                ),
                (
                    "temperature_altitudes",
                    ql_talt
                    / "all_times_with_fism_nature"
                    / f"temperature_60_90_150_250km_flare_noflare_diff_20241003_{hhmm}UT.png",
                ),
                (
                    "T250_TEC",
                    ql_t250
                    / "all_times_with_fism_nature"
                    / f"global_T250km_TEC_flare_noflare_diff_20241003_{hhmm}UT.png",
                ),
            ]
        )

    manifest = []
    for label, src in frame_specs:
        dst = out_dir / "quicklook_keyframes" / label / src.name
        copy_file(src, dst, copied)
        if dst.exists():
            manifest.append({"label": label, "source": str(src), "archive": str(dst.relative_to(out_dir))})
    return manifest


def write_manifest(out_dir: Path, copied: List[Tuple[Path, Path]]) -> None:
    lines = ["source_path\tarchive_path\tsize_bytes\tsha256"]
    for src, dst in sorted(copied, key=lambda item: str(item[1])):
        rel = dst.relative_to(out_dir)
        lines.append(f"{src}\t{rel}\t{dst.stat().st_size}\t{sha256_file(dst)}")
    write_lines(out_dir / "manifests" / "file_manifest.tsv", lines)


def archive(out_dir: Path) -> Path:
    if out_dir.exists():
        shutil.rmtree(str(out_dir))
    out_dir.mkdir(parents=True)
    copied = []  # type: List[Tuple[Path, Path]]

    flare_atm = CASE_ROOT / FLARE_CASE / "CaseDocs" / "atm_in"
    noflare_atm = CASE_ROOT / NOFLARE_CASE / "CaseDocs" / "atm_in"

    copy_file(flare_atm, out_dir / "configs" / "flare_atm_in", copied)
    copy_file(noflare_atm, out_dir / "configs" / "noflare_atm_in", copied)
    copy_file(SOLAR_ROOT / "fism2_20241003_x9_pair_summary.txt", out_dir / "forcing" / "fism2_pair_summary.txt", copied)
    copy_file(SOLAR_ROOT / "fism2_flare_bands_20241003_x9_waccmx.nc", out_dir / "forcing" / "fism2_flare_bands_20241003_x9_waccmx.nc", copied)
    copy_file(SOLAR_ROOT / "fism2_noflare_bands_20241003_x9_removed_waccmx.nc", out_dir / "forcing" / "fism2_noflare_bands_20241003_x9_removed_waccmx.nc", copied)

    # Copy quicklook index files for complete local-frame context.
    index_sources = [
        (
            "global_T_TEC",
            QL_ROOT / "fism2_20241003_x9_r5_5min_global_maps" / "all_times_with_fism" / "frames_index.md",
        ),
        (
            "electron_density_altitudes",
            QL_ROOT
            / "fism2_20241003_x9_r5_5min_electron_density_altitudes"
            / "1000_1400_with_fism_nature"
            / "frames_index.md",
        ),
        (
            "temperature_altitudes",
            QL_ROOT
            / "fism2_20241003_x9_r5_5min_temperature_altitudes"
            / "all_times_with_fism_nature"
            / "frames_index.md",
        ),
        (
            "T250_TEC",
            QL_ROOT / "fism2_20241003_x9_r5_5min_250km_T_TEC" / "all_times_with_fism_nature" / "frames_index.md",
        ),
    ]
    for label, src in index_sources:
        copy_file(src, out_dir / "quicklook_indexes" / label / src.name, copied)

    frame_manifest = collect_key_frames(out_dir, copied)

    inv = hist_inventory(FLARE_CASE) + hist_inventory(NOFLARE_CASE)
    status = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "classification": "waccmx_flare_noflare_science_pair_evidence",
        "event": "NOAA AR3842 X9.0 flare",
        "event_peak_utc": "2024-10-03T12:18:00Z",
        "analysis_window_utc": "2024-10-03T12:00:00Z/2024-10-03T13:00:00Z",
        "flare_case": FLARE_CASE,
        "noflare_case": NOFLARE_CASE,
        "flare_solar_euv_data_file": extract_solar_file(flare_atm),
        "noflare_solar_euv_data_file": extract_solar_file(noflare_atm),
        "hist_inventory": inv,
        "hist_streams_present": sorted(set(row["stream"] for row in inv)),
        "quicklook_key_times_utc": KEY_TIMES,
        "quicklook_keyframes": frame_manifest,
        "limitations": [
            "This package is WACCM-X flare/no-flare science evidence, not a new full WACCM-X/SAMI3/RAIJU/GAMERA run.",
            "NetCDF history products are not copied because the paired h1-h4 products are multi-GB.",
            "The current shell environment lacks ncdump/netCDF4/xarray; validation uses existing generated quicklooks and file inventories.",
        ],
    }
    (out_dir / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True))

    inv_lines = ["case\tstream\tsize_bytes\tmtime\tpath"]
    for row in inv:
        inv_lines.append(
            f"{row['case']}\t{row['stream']}\t{row['size_bytes']}\t{row['mtime']}\t{row['path']}"
        )
    write_lines(out_dir / "manifests" / "hist_inventory.tsv", inv_lines)

    source_lines = [
        "label\tpath",
        f"flare_case_root\t{CASE_ROOT / FLARE_CASE}",
        f"noflare_case_root\t{CASE_ROOT / NOFLARE_CASE}",
        f"flare_run_output\t{OUT_ROOT / FLARE_CASE / 'run'}",
        f"noflare_run_output\t{OUT_ROOT / NOFLARE_CASE / 'run'}",
        f"solar_forcing_root\t{SOLAR_ROOT}",
        f"full_quicklook_root\t{QL_ROOT}",
    ]
    write_lines(out_dir / "manifests" / "source_paths.tsv", source_lines)

    report_lines = [
        "# WACCM-X 2024-10-03 X9 Flare/No-Flare Science Evidence",
        "",
        f"- Generated: `{status['generated_at']}`",
        f"- Classification: `{status['classification']}`",
        f"- Event: `{status['event']}`, peak `{status['event_peak_utc']}`",
        f"- Analysis window: `{status['analysis_window_utc']}`",
        f"- Flare case: `{FLARE_CASE}`",
        f"- No-flare case: `{NOFLARE_CASE}`",
        "",
        "## Control Difference",
        "",
        "The paired WACCM-X cases use the same history-output settings.  The controlling science difference is `solar_euv_data_file`:",
        "",
        f"- Flare: `{status['flare_solar_euv_data_file']}`",
        f"- No-flare: `{status['noflare_solar_euv_data_file']}`",
        "",
        "The local FISM2 pair summary states that the no-flare forcing replaces the observed 12:08-13:08 UTC flare window with per-band linear interpolation, which corresponds to 12:10-13:05 UTC samples at 5-minute cadence.",
        "",
        "## Available Model Products",
        "",
        "- Both cases have CAM `h1`, `h2`, `h3`, `h4`, and `h6` history streams.",
        "- The history products are recorded in `manifests/hist_inventory.tsv` and not copied into this archive.",
        "- Existing quicklook products cover the requested 12:00-13:00 UTC interval.",
        "",
        "## Included Key Frames",
        "",
        "- Window mean: `quicklook_keyframes/window_mean/` for 12:10-13:05 UTC.",
        "- 12:30 UTC snapshots near the flare peak response:",
        "  `global_T_TEC_with_fism`, `electron_density_altitudes`, `temperature_altitudes`, and `T250_TEC`.",
        "- Full 5-minute local quicklook paths are recorded in `manifests/source_paths.tsv` and summarized in `quicklook_indexes/`.",
        "",
        "## Current Interpretation",
        "",
        "This package is enough for the first-stage science comparison: a controlled WACCM-X flare/no-flare pair driven by FISM2, with existing 5-minute quicklooks through the requested interval.",
        "",
        "It does not yet prove the same 2024-10-03 interval has been run through the live WACCM-X -> SAMI3 -> RAIJU/GAMERA prototype.  That should be the next integration step after this WACCM-X-only science comparison is accepted.",
    ]
    write_lines(out_dir / "report.md", report_lines)

    write_manifest(out_dir, copied)
    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(archive(args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
