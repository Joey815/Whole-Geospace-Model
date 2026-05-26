#!/usr/bin/env python3
"""Archive validation evidence from a WACCM-X/SAMI3 direct-MPI run."""

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
    "voltron_runtime_direct.out",
    "phi_payload_summary.txt",
    "live_dump_summary_pkt*.txt",
    "replay_builder_pkt*.out",
    "recv_qc_compare_pkt*.txt",
    "wxsami3_live_meta.json",
    "validate_*.txt",
    "validate_*.json",
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


def copy_files(files, archive_dir):
    copied = []
    for src in files:
        dst = archive_dir / src.name
        shutil.copy2(str(src), str(dst))
        copied.append({"source": str(src), "archive": str(dst), "bytes": dst.stat().st_size})
    return copied


def collect_files(run_dir, job_id=None):
    files = []
    seen = set()
    for pattern in COPY_PATTERNS:
        for path in sorted(run_dir.glob(pattern)):
            if not path.is_file():
                continue
            if job_id and path.name.startswith("slurm-") and not path.name.startswith(f"slurm-{job_id}."):
                continue
            if path.suffix in SKIP_SUFFIXES:
                continue
            if path in seen:
                continue
            seen.add(path)
            files.append(path)
    return files


def write_sacct(job_id, archive_dir):
    if not job_id:
        return None
    out = archive_dir / "sacct_{}.txt".format(job_id)
    cmd = [
        "sacct",
        "-j",
        str(job_id),
        "--format=JobID,JobName,State,ExitCode,Elapsed,Timelimit,NodeList,MaxRSS",
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


def maybe_extend(cmd, condition, args):
    if condition:
        cmd.extend(args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--archive-dir", required=True)
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--expected-packets", type=int, required=True)
    parser.add_argument("--expected-phi-frames", type=int, required=True)
    parser.add_argument("--expected-sami3-workers", type=int, default=32)
    parser.add_argument("--expected-source-columns", type=int, default=13824)
    parser.add_argument("--expected-payload-nz", type=int, default=304)
    parser.add_argument("--expected-payload-nf", type=int, default=124)
    parser.add_argument("--expected-payload-nl", type=int, default=5)
    parser.add_argument("--expected-payload-nneut", type=int, default=7)
    parser.add_argument("--expected-neutral-cadence-hours", type=float, default=0.08333333333333333)
    parser.add_argument("--expected-n2-mode", default="invalid")
    parser.add_argument("--runtime-map", default=None)
    parser.add_argument("--weights-nc", default=None)
    parser.add_argument("--runtime-map-python", default="/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python")
    parser.add_argument("--require-changing-phi", action="store_true")
    parser.add_argument("--require-topblend", action="store_true")
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    run_dir = Path(args.run_dir).expanduser().resolve()
    archive_dir = Path(args.archive_dir).expanduser()
    archive_dir.mkdir(parents=True, exist_ok=True)

    receiver_log = run_dir / "sami3_online_receiver.out"
    phi_sender_log = run_dir / "voltron_runtime_direct.out"
    first_recv_qc = run_dir / "recv_qc_compare_pkt000000.txt"

    direct_json = archive_dir / "validate_sami3_direct_phi_run_strict.json"
    direct_txt = archive_dir / "validate_sami3_direct_phi_run_strict.txt"
    direct_cmd = [
        sys.executable,
        str(repo / "scripts" / "validate_sami3_direct_phi_run.py"),
        "--receiver-log",
        str(receiver_log),
        "--phi-sender-log",
        str(phi_sender_log),
        "--recv-qc-compare",
        str(first_recv_qc),
        "--expected-frames",
        str(args.expected_phi_frames),
        "--json-output",
        str(direct_json),
    ]
    if args.require_changing_phi:
        direct_cmd.append("--require-changing-phi")
    if args.allow_incomplete:
        direct_cmd.append("--allow-incomplete-run")
    direct_rc = run_checked(direct_cmd, direct_txt)

    phi_json = archive_dir / "validate_remix_sami3_phi_payload.json"
    phi_txt = archive_dir / "validate_remix_sami3_phi_payload.txt"
    phi_cmd = [
        sys.executable,
        str(repo / "scripts" / "validate_remix_sami3_phi_payload.py"),
        "--run-dir",
        str(run_dir),
        "--expected-frames",
        str(args.expected_phi_frames),
        "--expected-first-hour",
        "0.0",
        "--json-output",
        str(phi_json),
    ]
    if args.require_changing_phi:
        phi_cmd.append("--require-changing-phi-frames")
    if args.allow_incomplete:
        phi_cmd.append("--allow-incomplete")
    phi_rc = run_checked(phi_cmd, phi_txt)

    contract_json = archive_dir / "validate_wxsami3_live_packet_contract.json"
    contract_txt = archive_dir / "validate_wxsami3_live_packet_contract.txt"
    contract_cmd = [
        sys.executable,
        str(repo / "scripts" / "validate_wxsami3_live_packet_contract.py"),
        "--run-dir",
        str(run_dir),
        "--expected-packets",
        str(args.expected_packets),
        "--expected-source-columns",
        str(args.expected_source_columns),
        "--expected-receiver-ranks",
        str(args.expected_sami3_workers),
        "--expected-payload-nz",
        str(args.expected_payload_nz),
        "--expected-payload-nf",
        str(args.expected_payload_nf),
        "--expected-payload-nl",
        str(args.expected_payload_nl),
        "--expected-payload-nneut",
        str(args.expected_payload_nneut),
        "--expected-n2-mode",
        args.expected_n2_mode,
        "--expect-n2-residual",
        "--expect-he-native",
        "--require-zero-unknown-source-flags",
        "--json-output",
        str(contract_json),
    ]
    if args.allow_incomplete:
        contract_cmd.append("--allow-incomplete")
    contract_rc = run_checked(contract_cmd, contract_txt)

    source_json = archive_dir / "validate_wxsami3_source_flag_balance.json"
    source_txt = archive_dir / "validate_wxsami3_source_flag_balance.txt"
    source_cmd = [
        sys.executable,
        str(repo / "scripts" / "validate_wxsami3_source_flag_balance.py"),
        "--run-dir",
        str(run_dir),
        "--expected-sami3-workers",
        str(args.expected_sami3_workers),
        "--min-total-blend-cells",
        "1",
        "--json-output",
        str(source_json),
    ]
    if args.allow_incomplete:
        source_cmd.append("--allow-incomplete")
    source_rc = run_checked(source_cmd, source_txt)

    time_json = archive_dir / "validate_wxsami3_time_axis.json"
    time_txt = archive_dir / "validate_wxsami3_time_axis.txt"
    time_cmd = [
        sys.executable,
        str(repo / "scripts" / "validate_wxsami3_time_axis.py"),
        "--run-dir",
        str(run_dir),
        "--expected-neutral-packets",
        str(args.expected_packets),
        "--expected-phi-frames",
        str(args.expected_phi_frames),
        "--expected-sami3-workers",
        str(args.expected_sami3_workers),
        "--expected-neutral-cadence-hours",
        str(args.expected_neutral_cadence_hours),
        "--allow-overlap-phi-validity",
        "--json-output",
        str(time_json),
    ]
    if args.allow_incomplete:
        time_cmd.append("--allow-incomplete")
    time_rc = run_checked(time_cmd, time_txt)

    topblend_rc = 0
    if args.require_topblend:
        topblend_json = archive_dir / "validate_wxsami3_topblend_policy.json"
        topblend_txt = archive_dir / "validate_wxsami3_topblend_policy.txt"
        topblend_cmd = [
            sys.executable,
            str(repo / "scripts" / "validate_wxsami3_topblend_policy.py"),
            "--run-dir",
            str(run_dir),
            "--expect-top-blend-mode",
            "linear",
            "--expect-bottom-km",
            "600",
            "--expect-top-km",
            "720",
            "--min-total-blend-cells",
            "1",
            "--require-zero-unknown-source-flags",
            "--require-he-native",
            "--require-w-zero",
            "--json-output",
            str(topblend_json),
        ]
        if args.allow_incomplete:
            topblend_cmd.append("--allow-incomplete")
        topblend_rc = run_checked(topblend_cmd, topblend_txt)
    else:
        topblend_txt = None
        topblend_json = None

    runtime_map_json = archive_dir / "validate_wxsami3_runtime_map.json"
    runtime_map_txt = archive_dir / "validate_wxsami3_runtime_map.txt"
    runtime_map_path = args.runtime_map or runtime_map_from_meta(run_dir)
    if runtime_map_path:
        runtime_cmd = [
            args.runtime_map_python,
            str(repo / "scripts" / "validate_wxsami3_runtime_map.py"),
            "--runtime-map",
            str(runtime_map_path),
            "--expected-nsource",
            str(args.expected_source_columns),
            "--json-output",
            str(runtime_map_json),
        ]
        if args.weights_nc:
            runtime_cmd.extend(["--weights-nc", str(args.weights_nc)])
        runtime_rc = run_checked(runtime_cmd, runtime_map_txt)
    elif args.allow_incomplete:
        runtime_rc = 0
        runtime_map_txt.write_text("runtime map not available yet; allowed while incomplete\n")
        runtime_map_json.write_text(json.dumps({"ok": True, "skipped": "runtime map not available yet"}, indent=2) + "\n")
    else:
        runtime_rc = 1
        runtime_map_txt.write_text("runtime map not found\n")
        runtime_map_json.write_text(json.dumps({"ok": False, "error": "runtime map not found"}, indent=2) + "\n")

    copied = copy_files(collect_files(run_dir, args.job_id), archive_dir)
    sacct = write_sacct(args.job_id, archive_dir)
    checks = {
        "direct_phi": direct_rc,
        "phi_payload": phi_rc,
        "live_packet_contract": contract_rc,
        "source_flag_balance": source_rc,
        "time_axis": time_rc,
        "topblend_policy": topblend_rc,
        "runtime_map": runtime_rc,
    }
    ok = all(returncode == 0 for returncode in checks.values())
    summary = {
        "ok": ok,
        "run_dir": str(run_dir),
        "archive_dir": str(archive_dir),
        "job_id": args.job_id,
        "expected_packets": args.expected_packets,
        "expected_phi_frames": args.expected_phi_frames,
        "validator_returncodes": checks,
        "copied_files": copied,
        "sacct": sacct,
        "runtime_map": runtime_map_path,
    }
    (archive_dir / "archive_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    lines = [
        "# WACCM-X/SAMI3 Direct-MPI Archive Summary",
        "",
        "run_dir: {}".format(run_dir),
        "job_id: {}".format(args.job_id if args.job_id else ""),
        "expected_packets: {}".format(args.expected_packets),
        "expected_phi_frames: {}".format(args.expected_phi_frames),
        "direct_phi_returncode: {}".format(direct_rc),
        "phi_payload_returncode: {}".format(phi_rc),
        "live_packet_contract_returncode: {}".format(contract_rc),
        "source_flag_balance_returncode: {}".format(source_rc),
        "time_axis_returncode: {}".format(time_rc),
        "topblend_policy_returncode: {}".format(topblend_rc),
        "runtime_map_returncode: {}".format(runtime_rc),
        "copied_files: {}".format(len(copied)),
        "overall: {}".format("ok" if ok else "FAIL"),
        "",
        "Validator text outputs:",
        "",
        "- validate_sami3_direct_phi_run_strict.txt",
        "- validate_remix_sami3_phi_payload.txt",
        "- validate_wxsami3_live_packet_contract.txt",
        "- validate_wxsami3_source_flag_balance.txt",
        "- validate_wxsami3_time_axis.txt",
        "- validate_wxsami3_topblend_policy.txt",
        "- validate_wxsami3_runtime_map.txt",
    ]
    (archive_dir / "README.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
