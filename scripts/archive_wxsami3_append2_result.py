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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--archive-dir", required=True)
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--expected-phi-frames", type=int, default=2)
    parser.add_argument("--expected-live-packets", type=int, default=1)
    parser.add_argument("--expect-phi-wait-marker", action="store_true")
    parser.add_argument("--expect-direct-wait-mode", action="store_true")
    parser.add_argument("--expect-top-blend-mode", choices=["linear", "none"], default=None)
    parser.add_argument("--expect-blend-bottom-km", type=float, default=None)
    parser.add_argument("--expect-blend-top-km", type=float, default=None)
    parser.add_argument("--min-total-blend-cells", type=int, default=0)
    parser.add_argument("--require-zero-unknown-source-flags", action="store_true")
    parser.add_argument("--require-he-native", action="store_true")
    parser.add_argument("--require-w-zero", action="store_true")
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
        "--json-output",
        str(append2_json),
    ]
    if args.expect_phi_wait_marker:
        append2_cmd.append("--expect-phi-wait-marker")
    if args.expect_direct_wait_mode:
        append2_cmd.append("--expect-direct-wait-mode")
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

    copied = copy_files(collect_files(run_dir), archive_dir)
    sacct = write_sacct(args.job_id, archive_dir)

    summary = {
        "ok": append2_rc == 0 and contract_rc == 0 and topblend_rc == 0,
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
        "copied_files: {}".format(len(copied)),
        "overall: {}".format("ok" if summary["ok"] else "FAIL"),
        "",
        "Validator text outputs:",
        "",
        "- validate_wxsami3_append2_run.txt",
        "- validate_wxsami3_live_packet_contract.txt",
        "- validate_wxsami3_topblend_policy.txt",
    ]
    (archive_dir / "README.md").write_text("\n".join(lines) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
