#!/usr/bin/env python3
"""Archive small validation evidence from a WACCM-X/SAMI3 append2 run."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


COPY_PATTERNS = [
    "slurm-*.out",
    "slurm-*.err",
    "waccmx_cesm.out",
    "sami3_online_receiver.out",
    "phi_payload_summary.txt",
    "voltron_phi*.out",
    "voltron_phi*.err",
    "live_dump_summary_pkt*.txt",
    "replay_builder_pkt*.out",
    "recv_qc_compare_pkt*.txt",
    "wxsami3_live_meta.json",
]

SKIP_SUFFIXES = {
    ".bin",
    ".nc",
    ".h5",
    ".npz",
}


def run_checked(cmd, stdout_path):
    with stdout_path.open("w") as fp:
        proc = subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, universal_newlines=True)
    return proc.returncode


def collect_files(run_dir):
    files = []
    seen = set()
    for pattern in COPY_PATTERNS:
        for path in sorted(run_dir.glob(pattern)):
            if not path.is_file():
                continue
            if path.suffix in SKIP_SUFFIXES:
                continue
            if path in seen:
                continue
            seen.add(path)
            files.append(path)
    return files


def copy_files(files, archive_dir):
    copied = []
    for src in files:
        dst = archive_dir / src.name
        shutil.copy2(str(src), str(dst))
        copied.append({"source": str(src), "archive": str(dst), "bytes": dst.stat().st_size})
    return copied


def write_sacct(job_id, archive_dir):
    if not job_id:
        return None
    out = archive_dir / "sacct_{}.txt".format(job_id)
    cmd = [
        "sacct",
        "-j",
        str(job_id),
        "--format=JobID,JobName,State,ExitCode,Elapsed,NodeList,MaxRSS",
        "-P",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    out.write_text(proc.stdout)
    return {"path": str(out), "returncode": proc.returncode}


def runtime_map_from_meta(run_dir):
    meta_path = run_dir / "wxsami3_live_meta.json"
    if not meta_path.is_file():
        return None
    try:
        meta = json.loads(meta_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    runtime_map = meta.get("runtime_map", {})
    return runtime_map.get("file")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--archive-dir", required=True)
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--expected-phi-frames", type=int, default=2)
    parser.add_argument("--expected-first-phi-hour", type=float, default=0.0)
    parser.add_argument("--expected-live-packets", type=int, default=1)
    parser.add_argument("--expect-phi-wait-marker", action="store_true")
    parser.add_argument("--expect-direct-wait-mode", action="store_true")
    parser.add_argument("--require-nonzero-phi", action="store_true")
    parser.add_argument("--require-changing-phi-frames", action="store_true")
    parser.add_argument("--min-phi-frame-max-abs-diff", type=float, default=1.0e-6)
    parser.add_argument("--require-receiver-phi-values", action="store_true")
    parser.add_argument("--phi-value-tol", type=float, default=1.0e-4)
    parser.add_argument("--expect-top-blend-mode", choices=["linear", "none"], default=None)
    parser.add_argument("--expect-blend-bottom-km", type=float, default=None)
    parser.add_argument("--expect-blend-top-km", type=float, default=None)
    parser.add_argument("--min-total-blend-cells", type=int, default=0)
    parser.add_argument("--require-zero-unknown-source-flags", action="store_true")
    parser.add_argument("--require-he-native", action="store_true")
    parser.add_argument("--require-w-zero", action="store_true")
    parser.add_argument("--runtime-map", default=None)
    parser.add_argument("--weights-nc", default=None)
    parser.add_argument("--expected-runtime-map-nsource", type=int, default=None)
    parser.add_argument("--runtime-map-python", default="/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    run_dir = Path(args.run_dir).expanduser().resolve()
    archive_dir = Path(args.archive_dir).expanduser()
    archive_dir.mkdir(parents=True, exist_ok=True)

    append2_json = archive_dir / "validate_wxsami3_append2_run.json"
    append2_txt = archive_dir / "validate_wxsami3_append2_run.txt"
    append2_cmd = [
        sys.executable,
        str(repo / "scripts" / "validate_wxsami3_append2_run.py"),
        "--run-dir",
        str(run_dir),
        "--expected-phi-frames",
        str(args.expected_phi_frames),
        "--expected-first-phi-hour",
        str(args.expected_first_phi_hour),
        "--json-output",
        str(append2_json),
    ]
    if args.expect_phi_wait_marker:
        append2_cmd.append("--expect-phi-wait-marker")
    if args.expect_direct_wait_mode:
        append2_cmd.append("--expect-direct-wait-mode")
    if args.require_nonzero_phi:
        append2_cmd.append("--require-nonzero-phi")
    if args.require_changing_phi_frames:
        append2_cmd.extend(["--require-changing-phi-frames", "--min-phi-frame-max-abs-diff", str(args.min_phi_frame_max_abs_diff)])
    if args.require_receiver_phi_values:
        append2_cmd.extend(["--require-receiver-phi-values", "--phi-value-tol", str(args.phi_value_tol)])
    if args.allow_incomplete:
        append2_cmd.append("--allow-incomplete")
    append2_rc = run_checked(append2_cmd, append2_txt)

    contract_json = archive_dir / "validate_wxsami3_live_packet_contract.json"
    contract_txt = archive_dir / "validate_wxsami3_live_packet_contract.txt"
    contract_cmd = [
        sys.executable,
        str(repo / "scripts" / "validate_wxsami3_live_packet_contract.py"),
        "--run-dir",
        str(run_dir),
        "--expected-packets",
        str(args.expected_live_packets),
        "--json-output",
        str(contract_json),
    ]
    if args.allow_incomplete:
        contract_cmd.append("--allow-incomplete")
    contract_rc = run_checked(contract_cmd, contract_txt)

    topblend_rc = 0
    topblend_txt = None
    topblend_json = None
    if args.expect_top_blend_mode:
        topblend_json = archive_dir / "validate_wxsami3_topblend_policy.json"
        topblend_txt = archive_dir / "validate_wxsami3_topblend_policy.txt"
        topblend_cmd = [
            sys.executable,
            str(repo / "scripts" / "validate_wxsami3_topblend_policy.py"),
            "--run-dir",
            str(run_dir),
            "--expect-top-blend-mode",
            args.expect_top_blend_mode,
            "--min-apply-blend-lines",
            "1",
            "--min-total-blend-cells",
            str(args.min_total_blend_cells),
            "--json-output",
            str(topblend_json),
        ]
        if args.expect_blend_bottom_km is not None:
            topblend_cmd.extend(["--expect-bottom-km", str(args.expect_blend_bottom_km)])
        if args.expect_blend_top_km is not None:
            topblend_cmd.extend(["--expect-top-km", str(args.expect_blend_top_km)])
        if args.require_zero_unknown_source_flags:
            topblend_cmd.append("--require-zero-unknown-source-flags")
        if args.require_he_native:
            topblend_cmd.append("--require-he-native")
        if args.require_w_zero:
            topblend_cmd.append("--require-w-zero")
        if args.allow_incomplete:
            topblend_cmd.append("--allow-incomplete")
        topblend_rc = run_checked(topblend_cmd, topblend_txt)

    runtime_map_info = None
    if args.runtime_map or args.weights_nc:
        runtime_map_json = archive_dir / "validate_wxsami3_runtime_map.json"
        runtime_map_txt = archive_dir / "validate_wxsami3_runtime_map.txt"
        runtime_map_path = args.runtime_map or runtime_map_from_meta(run_dir)
        if runtime_map_path:
            runtime_map_cmd = [
                args.runtime_map_python,
                str(repo / "scripts" / "validate_wxsami3_runtime_map.py"),
                "--runtime-map",
                str(runtime_map_path),
                "--json-output",
                str(runtime_map_json),
            ]
            if args.weights_nc:
                runtime_map_cmd.extend(["--weights-nc", str(args.weights_nc)])
            if args.expected_runtime_map_nsource is not None:
                runtime_map_cmd.extend(["--expected-nsource", str(args.expected_runtime_map_nsource)])
            runtime_map_rc = run_checked(runtime_map_cmd, runtime_map_txt)
        elif args.allow_incomplete:
            runtime_map_rc = 0
            runtime_map_txt.write_text("runtime map not available yet; allowed while incomplete\n")
            runtime_map_json.write_text(json.dumps({"ok": True, "skipped": "runtime map not available yet"}, indent=2) + "\n")
        else:
            runtime_map_rc = 1
            runtime_map_txt.write_text("runtime map not found; pass --runtime-map or wait for wxsami3_live_meta.json\n")
            runtime_map_json.write_text(json.dumps({"ok": False, "error": "runtime map not found"}, indent=2) + "\n")
        runtime_map_info = {
            "returncode": runtime_map_rc,
            "text": str(runtime_map_txt),
            "json": str(runtime_map_json),
            "python": args.runtime_map_python,
            "runtime_map": runtime_map_path,
            "weights_nc": args.weights_nc,
            "expected_nsource": args.expected_runtime_map_nsource,
        }

    copied = copy_files(collect_files(run_dir), archive_dir)
    sacct = write_sacct(args.job_id, archive_dir)

    summary = {
        "ok": append2_rc == 0
        and contract_rc == 0
        and topblend_rc == 0
        and (runtime_map_info is None or runtime_map_info["returncode"] == 0),
        "run_dir": str(run_dir),
        "archive_dir": str(archive_dir),
        "job_id": args.job_id,
        "append2_validator": {
            "returncode": append2_rc,
            "text": str(append2_txt),
            "json": str(append2_json),
        },
        "live_packet_contract_validator": {
            "returncode": contract_rc,
            "text": str(contract_txt),
            "json": str(contract_json),
        },
        "topblend_policy_validator": {
            "returncode": topblend_rc,
            "text": str(topblend_txt) if topblend_txt else None,
            "json": str(topblend_json) if topblend_json else None,
        },
        "runtime_map_validator": runtime_map_info,
        "copied_files": copied,
        "sacct": sacct,
    }
    (archive_dir / "archive_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    lines = [
        "# WACCM-X/SAMI3 Append2 Archive Summary",
        "",
        "run_dir: {}".format(run_dir),
        "job_id: {}".format(args.job_id if args.job_id else ""),
        "append2_validator_returncode: {}".format(append2_rc),
        "live_packet_contract_returncode: {}".format(contract_rc),
        "topblend_policy_returncode: {}".format(topblend_rc),
        "runtime_map_returncode: {}".format(runtime_map_info["returncode"] if runtime_map_info else ""),
        "copied_files: {}".format(len(copied)),
        "overall: {}".format("ok" if summary["ok"] else "FAIL"),
        "",
        "Validator text outputs:",
        "",
        "- validate_wxsami3_append2_run.txt",
        "- validate_wxsami3_live_packet_contract.txt",
        "- validate_wxsami3_topblend_policy.txt",
        "- validate_wxsami3_runtime_map.txt",
    ]
    (archive_dir / "README.md").write_text("\n".join(lines) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
