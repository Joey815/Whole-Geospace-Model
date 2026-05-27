#!/usr/bin/env python3
"""Archive a compact integrated WACCM-X/SAMI3/RAIJU/GAMERA prototype result.

This script intentionally collects evidence from already validated component
runs.  It does not claim that those runs were one single production full-chain
simulation, and it does not copy large HDF5 model products.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


COLLAB_ROOT = Path(__file__).resolve().parents[1]
MAGE_ROOT = COLLAB_ROOT.parent

LIVE_DIR = COLLAB_ROOT / "logs" / "waccmx_live_directmpi_nosmoke_dt300_24pkt_24phi_hrmax8_20260526"
RAIJU_DENSITY_DIR = COLLAB_ROOT / "logs" / "sami3_exclude_lmax_density_long1800_20260526"
RAIJU_TIOTE_DIR = COLLAB_ROOT / "logs" / "sami3_exclude_lmax_density_tiote_long1800_20260526"

DEFAULT_OUT = (
    MAGE_ROOT
    / "integrated_results"
    / "MAGE_WACCMX_SAMI3_RAIJU_GAMERA_PROTOTYPE_20260527"
)

KEY_DOCS = [
    COLLAB_ROOT / "README.md",
    COLLAB_ROOT / "docs" / "MAGE1.25_notes" / "GOAL_MODE_COUPLING_STATUS_20260525.md",
    COLLAB_ROOT / "docs" / "MAGE1.25_notes" / "SAMI3_RAIJU_GAMERA_PHYSICS_REVIEW_20260523.md",
    COLLAB_ROOT / "docs" / "MAGE1.25_notes" / "WACCMX_SAMI3_LIVE_DIRECTMPI_RESULT_20260525.md",
    COLLAB_ROOT / "docs" / "MAGE1.25_notes" / "WACCMX_SAMI3_LIVE_DIRECTMPI4_RESULT_20260525.md",
    COLLAB_ROOT / "docs" / "MAGE1.25_notes" / "SAMI3_RAIJU_EXCLUDE_LMAX_RUNTIME_SMOKE_20260526.md",
]


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def unique_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    for idx in range(2, 100):
        candidate = path.with_name(f"{path.name}_v{idx}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not allocate unique output path for {path}")


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
    shutil.copy2(src, dst)
    copied.append((src, dst))


def copy_many(src_dir: Path, dst_dir: Path, patterns: List[str], copied: List[Tuple[Path, Path]]) -> None:
    seen = set()  # type: Set[Path]
    for pattern in patterns:
        for src in sorted(src_dir.glob(pattern)):
            if not src.is_file() or src in seen:
                continue
            seen.add(src)
            copy_file(src, dst_dir / src.name, copied)


def copy_validator_tree(src_dir: Path, dst_dir: Path, copied: List[Tuple[Path, Path]]) -> None:
    if not src_dir.exists():
        return
    for src in sorted(src_dir.glob("*")):
        if src.is_file() and src.suffix in {".txt", ".json"}:
            copy_file(src, dst_dir / src.name, copied)


def validator_overall(path: Path) -> str:
    text = read_text(path)
    if "overall=ok" in text:
        return "ok"
    if "overall=FAIL" in text:
        return "FAIL"
    if re.search(r"\bFAIL\b", text):
        return "FAIL"
    if "classification=diagnostic_only" in text:
        return "diagnostic_only"
    return "unknown"


def parse_validator_statuses(root: Path) -> Dict[str, str]:
    statuses = {}  # type: Dict[str, str]
    for path in sorted(root.rglob("*.txt")):
        if "validator" in path.parts or path.name.startswith("validate_"):
            statuses[str(path.relative_to(root))] = validator_overall(path)
    return statuses


def first_matching_float(text: str, pattern: str) -> Optional[float]:
    m = re.search(pattern, text)
    if not m:
        return None
    return float(m.group(1))


def extract_formula_checks(summary: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out = {}  # type: Dict[str, Dict[str, Any]]
    checks = summary.get("formula_checks", {})
    if not isinstance(checks, dict):
        return out
    for name, values in checks.items():
        if not isinstance(values, dict):
            continue
        out[name] = {
            "alpha": values.get("alpha"),
            "formula_max_abs": values.get("formula_max_abs"),
            "formula_max_rel": values.get("formula_max_rel"),
            "mask_true": values.get("mask_true"),
            "mask_total": values.get("mask_total"),
        }
    return out


def write_lines(path: Path, lines: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n")


def build_summary(out_dir: Path, copied: List[Tuple[Path, Path]]) -> Dict[str, Any]:
    live_archive = read_json(LIVE_DIR / "archive_summary.json")
    live_meta = read_json(LIVE_DIR / "wxsami3_live_meta.json")
    density_archive = read_json(RAIJU_DENSITY_DIR / "archive_summary.json")
    tiote_archive = read_json(RAIJU_TIOTE_DIR / "archive_summary.json")
    density_summary = read_json(RAIJU_DENSITY_DIR / "recommended_long1800_exclude_lmax_dens005_summary.json")
    tiote_summary = read_json(RAIJU_TIOTE_DIR / "recommended_long1800_exclude_lmax_dens005_tiote_summary.json")
    tiote_compare = read_json(RAIJU_TIOTE_DIR / "tiote_vs_density_only_comparison.json")

    prod_diag_txt = read_text(RAIJU_TIOTE_DIR / "validate_sami3_raiju_production_contract_diagnostic.txt")
    prod_fail_txt = read_text(RAIJU_TIOTE_DIR / "validate_sami3_raiju_production_contract_production.txt")
    skipped_fraction = first_matching_float(
        prod_fail_txt + "\n" + prod_diag_txt,
        r"source_domain_skipped_above_lmax_fraction(?:_finite)?:\s*([0-9.eE+-]+)",
    )
    runtime_valid_fraction = first_matching_float(prod_fail_txt, r"runtime_valid_fraction:\s*([0-9.eE+-]+)")

    status = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "output_dir": str(out_dir),
        "classification": "integrated_prototype_evidence_not_production_full_coupling",
        "waccmx_sami3_phi": {
            "archive_ok": live_archive.get("ok"),
            "job_id": live_archive.get("job_id"),
            "run_dir": live_archive.get("run_dir"),
            "expected_neutral_packets": live_archive.get("expected_packets"),
            "expected_phi_frames": live_archive.get("expected_phi_frames"),
            "validator_returncodes": live_archive.get("validator_returncodes"),
            "payload_version": live_meta.get("payload_version"),
            "runtime_source": live_meta.get("runtime_source"),
            "actual_transport": live_meta.get("actual_transport"),
            "packet_hour_last": live_meta.get("packet_hour"),
            "runtime_map": live_meta.get("runtime_map"),
            "source_flags": live_meta.get("source_flags"),
            "runtime_qc": live_meta.get("runtime_qc"),
            "fallback_policy": live_meta.get("fallback_policy"),
        },
        "sami3_raiju_gamera_density": {
            "archive_ok": density_archive.get("ok"),
            "job_id": density_archive.get("job_id"),
            "run_dir": density_archive.get("run_dir"),
            "history_last_steps": density_summary.get("history_last_steps"),
            "nonfinite": density_summary.get("nonfinite"),
            "formula_checks": extract_formula_checks(density_summary),
        },
        "sami3_raiju_gamera_density_tiote": {
            "archive_ok": tiote_archive.get("ok"),
            "job_id": tiote_archive.get("job_id"),
            "run_dir": tiote_archive.get("run_dir"),
            "history_last_steps": tiote_summary.get("history_last_steps"),
            "nonfinite": tiote_summary.get("nonfinite"),
            "formula_checks": extract_formula_checks(tiote_summary),
            "tiote_vs_density_only": tiote_compare,
        },
        "production_contract": {
            "diagnostic_contract": validator_overall(
                RAIJU_TIOTE_DIR / "validate_sami3_raiju_production_contract_diagnostic.txt"
            ),
            "production_readiness": validator_overall(
                RAIJU_TIOTE_DIR / "validate_sami3_raiju_production_contract_production.txt"
            ),
            "source_domain_skipped_above_lmax_fraction": skipped_fraction,
            "runtime_valid_fraction": runtime_valid_fraction,
        },
        "copied_file_count": len(copied),
    }
    (out_dir / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True))
    return status


def write_reports(out_dir: Path, status: Dict[str, Any]) -> None:
    wx = status["waccmx_sami3_phi"]
    dens = status["sami3_raiju_gamera_density"]
    tiote = status["sami3_raiju_gamera_density_tiote"]
    contract = status["production_contract"]

    validator_status = parse_validator_statuses(out_dir / "validators")
    validator_lines = [f"- `{name}`: `{state}`" for name, state in validator_status.items()]
    if not validator_lines:
        validator_lines = ["- No validator text files found."]

    write_lines(
        out_dir / "summary.md",
        [
            "# MAGE WACCM-X SAMI3 RAIJU GAMERA Integrated Prototype Evidence",
            "",
            f"- Generated: `{status['generated_at']}`",
            f"- Classification: `{status['classification']}`",
            "- This is a unified evidence archive from validated component/prototype runs.",
            "- It is not a claim of production physical full coupling.",
            "",
            "## Source Evidence",
            "",
            "### WACCM-X -> SAMI3 Neutral + REMIX/Voltron -> SAMI3 Phi",
            "",
            f"- Job: `{wx.get('job_id')}`",
            f"- Run dir: `{wx.get('run_dir')}`",
            f"- Runtime source: `{wx.get('runtime_source')}`",
            f"- Transport: `{wx.get('actual_transport')}`",
            f"- Neutral packets: `{wx.get('expected_neutral_packets')}`",
            f"- Phi frames: `{wx.get('expected_phi_frames')}`",
            f"- Payload version: `{wx.get('payload_version')}`",
            f"- Last packet hour: `{wx.get('packet_hour_last')}`",
            "",
            "### SAMI3 -> RAIJU/GAMERA Density-Only 1800s",
            "",
            f"- Job: `{dens.get('job_id')}`",
            f"- Run dir: `{dens.get('run_dir')}`",
            f"- Last history steps: `{dens.get('history_last_steps')}`",
            f"- Formula checks: `{dens.get('formula_checks')}`",
            f"- Non-finite checked fields: `{dens.get('nonfinite')}`",
            "",
            "### SAMI3 -> RAIJU/GAMERA Density + Tiote 1800s",
            "",
            f"- Job: `{tiote.get('job_id')}`",
            f"- Run dir: `{tiote.get('run_dir')}`",
            f"- Last history steps: `{tiote.get('history_last_steps')}`",
            f"- Formula checks: `{tiote.get('formula_checks')}`",
            f"- Non-finite checked fields: `{tiote.get('nonfinite')}`",
            "",
            "## Validator Snapshot",
            "",
            *validator_lines,
            "",
            "## Production Contract",
            "",
            f"- Diagnostic contract: `{contract.get('diagnostic_contract')}`",
            f"- Production-readiness gate: `{contract.get('production_readiness')}`",
            f"- Source bVol skipped above target Lmax: `{contract.get('source_domain_skipped_above_lmax_fraction')}`",
            f"- Runtime valid fraction: `{contract.get('runtime_valid_fraction')}`",
            "",
            "## Bottom Line",
            "",
            "The archive supports a fast integrated-prototype statement:",
            "",
            "```text",
            "WACCM-X CAM phys_state(:) live neutral packets reach SAMI3.",
            "REMIX/Voltron runtime POT reaches SAMI3 as direct-MPI phi frames.",
            "SAMI3-derived scalar moments can be ingested by RAIJU/GAMERA with conservative blending.",
            "The current downstream adapter remains diagnostic/prototype because of the RAIJU target-domain source-volume issue.",
            "```",
        ],
    )

    write_lines(
        out_dir / "limitations.md",
        [
            "# Limitations",
            "",
            "1. This is an integrated evidence package, not one single production full-chain run.",
            "2. SAMI3 -> RAIJU/GAMERA currently passes scalar moments only: `Pavg`, `Davg`, `Pstd`, `Dstd`, and `tiote`.",
            "3. Bulk velocity, momentum density, anisotropic pressure tensor, field-aligned flow, and ExB drift are not coupled.",
            "4. The conservative exclude-Lmax product is diagnostic. The production-readiness validator intentionally fails.",
            f"5. The current source bVol skipped above target Lmax is `{contract.get('source_domain_skipped_above_lmax_fraction')}`.",
            "6. WACCM-X feedback consumption from MAGE/RAIJU/GAMERA should still get stronger per-frame runtime diagnostics before science claims.",
            "7. The WACCM-X -> SAMI3 live neutral evidence is f19-based; f09/finer production scaling remains separate work.",
            "8. Large HDF5 model products are not copied into this archive; source paths are recorded in manifests.",
        ],
    )

    write_lines(
        out_dir / "reproduce.md",
        [
            "# Reproduce And Revalidate",
            "",
            "Set the collaboration root:",
            "",
            "```bash",
            f"cd {COLLAB_ROOT}",
            "```",
            "",
            "Revalidate the WACCM-X -> SAMI3 live packet contract:",
            "",
            "```bash",
            "python3 scripts/validate_wxsami3_live_packet_contract.py \\",
            f"  --run-dir {wx.get('run_dir')} \\",
            "  --expected-packets 24 \\",
            "  --expected-source-columns 13824 \\",
            "  --expected-receiver-ranks 32 \\",
            "  --expected-n2-mode invalid \\",
            "  --expect-n2-residual \\",
            "  --expect-he-native \\",
            "  --require-zero-unknown-source-flags",
            "```",
            "",
            "Revalidate the SAMI3 -> RAIJU/GAMERA long-run smoke:",
            "",
            "```bash",
            "python3 scripts/validate_sami3_raiju_longrun.py \\",
            f"  --run-dir {dens.get('run_dir')} \\",
            "  --label long1800_exclude_lmax_dens005 \\",
            "  --expect-slurm",
            "```",
            "",
            "The HDF5 mapping-product and summary validators require a Python environment with `h5py`; archived outputs are under `validators/raiju_density_*` and `validators/raiju_density_tiote_*`.",
            "",
            "Regenerate this archive:",
            "",
            "```bash",
            "python3 scripts/archive_integrated_prototype_result.py",
            "```",
        ],
    )


def write_manifest(out_dir: Path, copied: List[Tuple[Path, Path]]) -> None:
    lines = ["source_path\tarchive_path\tsize_bytes\tsha256"]
    for src, dst in sorted(copied, key=lambda item: str(item[1])):
        rel = dst.relative_to(out_dir)
        lines.append(f"{src}\t{rel}\t{dst.stat().st_size}\t{sha256_file(dst)}")
    write_lines(out_dir / "manifests" / "file_manifest.tsv", lines)

    source_lines = [
        "label\tpath",
        f"collab_root\t{COLLAB_ROOT}",
        f"live_waccmx_sami3_phi_archive\t{LIVE_DIR}",
        f"raiju_density_archive\t{RAIJU_DENSITY_DIR}",
        f"raiju_density_tiote_archive\t{RAIJU_TIOTE_DIR}",
    ]
    write_lines(out_dir / "manifests" / "source_paths.tsv", source_lines)


def archive(out_dir: Path) -> Path:
    out_dir = unique_output_path(out_dir)
    copied = []  # type: List[Tuple[Path, Path]]

    (out_dir / "validators").mkdir(parents=True, exist_ok=True)
    (out_dir / "logs").mkdir(parents=True, exist_ok=True)
    (out_dir / "docs").mkdir(parents=True, exist_ok=True)
    (out_dir / "configs").mkdir(parents=True, exist_ok=True)
    (out_dir / "manifests").mkdir(parents=True, exist_ok=True)

    copy_validator_tree(LIVE_DIR / "run_validators", out_dir / "validators" / "waccmx_sami3_phi_24pkt", copied)
    copy_many(
        LIVE_DIR,
        out_dir / "logs" / "waccmx_sami3_phi_24pkt",
        [
            "README.md",
            "archive_summary.json",
            "wxsami3_live_meta.json",
            "phi_payload_summary.txt",
            "sacct_*.txt",
            "slurm-*.out",
            "slurm-*.err",
            "waccmx_cesm.out",
            "sami3_online_receiver.out",
            "voltron_runtime_direct.out",
            "live_dump_summary_pkt*.txt",
            "recv_qc_compare_pkt*.txt",
            "replay_builder_pkt*.out",
        ],
        copied,
    )

    for label, src_dir in [
        ("raiju_density_long1800", RAIJU_DENSITY_DIR),
        ("raiju_density_tiote_long1800", RAIJU_TIOTE_DIR),
    ]:
        copy_many(
            src_dir,
            out_dir / "logs" / label,
            ["README.md", "*.log", "*.out", "*.txt", "*.json", "*.xml", "*.sbatch"],
            copied,
        )
        copy_many(
            src_dir,
            out_dir / "validators" / label,
            ["validate_*.txt", "validate_*.json", "tiote_vs_density_only_comparison.*"],
            copied,
        )
        copy_many(src_dir, out_dir / "configs" / label, ["*.xml", "*.sbatch"], copied)

    for doc in KEY_DOCS:
        copy_file(doc, out_dir / "docs" / doc.name, copied)

    status = build_summary(out_dir, copied)
    write_reports(out_dir, status)
    write_manifest(out_dir, copied)
    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    out_dir = archive(args.output_dir)
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
