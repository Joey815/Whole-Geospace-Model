#!/usr/bin/env python3
"""Run the current 2026-05-25 goal-mode WACCM-X/SAMI3 archive gates.

This is intentionally a thin driver around ``archive_wxsami3_append2_result.py``.
It freezes the run directories, job ids, and strict acceptance flags for the
current append2 and direct-wait integration jobs so the completion archive can
be reproduced without retyping a long command.
"""

import argparse
import subprocess
import sys
from pathlib import Path


WEIGHTS_NC = (
    "/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/"
    "esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc"
)


RUNS = {
    "append2": {
        "job_id": "7659727",
        "run_dir": (
            "/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/"
            "waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append2_20260525_0000"
        ),
        "archive_dir": "logs/waccmx_append2_full_20260525",
        "extra_flags": [],
    },
    "directwait": {
        "job_id": "7661005",
        "run_dir": (
            "/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/"
            "waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000"
        ),
        "archive_dir": "logs/waccmx_append2_directwait_20260525",
        "extra_flags": ["--expect-phi-wait-marker", "--expect-direct-wait-mode"],
    },
}


STRICT_FLAGS = [
    "--expected-phi-frames",
    "2",
    "--expected-live-packets",
    "1",
    "--expected-sami3-workers",
    "32",
    "--require-nonzero-phi",
    "--require-receiver-phi-values",
    "--require-changing-phi-frames",
    "--expect-top-blend-mode",
    "linear",
    "--expect-blend-bottom-km",
    "600",
    "--expect-blend-top-km",
    "720",
    "--min-total-blend-cells",
    "1",
    "--require-zero-unknown-source-flags",
    "--require-he-native",
    "--require-w-zero",
    "--weights-nc",
    WEIGHTS_NC,
    "--expected-runtime-map-nsource",
    "13824",
]


def run_text(cmd):
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return proc.returncode, proc.stdout


def top_sacct_state(job_id):
    cmd = [
        "sacct",
        "-j",
        str(job_id),
        "--format=JobID,State,ExitCode",
        "-P",
        "-n",
    ]
    rc, out = run_text(cmd)
    if rc != 0:
        return "UNKNOWN", out.strip()
    for line in out.splitlines():
        parts = line.split("|")
        if parts and parts[0] == str(job_id):
            state = parts[1] if len(parts) > 1 else "UNKNOWN"
            exit_code = parts[2] if len(parts) > 2 else ""
            return state, exit_code
    return "UNKNOWN", out.strip()


def build_archive_cmd(repo, name, spec, allow_incomplete):
    cmd = [
        sys.executable,
        str(repo / "scripts" / "archive_wxsami3_append2_result.py"),
        "--run-dir",
        spec["run_dir"],
        "--archive-dir",
        spec["archive_dir"],
        "--job-id",
        spec["job_id"],
    ]
    cmd.extend(STRICT_FLAGS)
    cmd.extend(spec["extra_flags"])
    if allow_incomplete:
        cmd.append("--allow-incomplete")
    return cmd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=["all"] + sorted(RUNS.keys()),
        default="all",
        help="Which current goal-mode run to archive.",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Run archive gates in partial mode even if sacct is not complete.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    targets = sorted(RUNS.keys()) if args.target == "all" else [args.target]
    failures = 0

    for name in targets:
        spec = RUNS[name]
        state, detail = top_sacct_state(spec["job_id"])
        print(f"{name}: job={spec['job_id']} state={state} detail={detail}")
        if state not in {"COMPLETED", "COMPLETING"} and not args.allow_incomplete:
            print(f"{name}: skip archive until job completes")
            continue

        cmd = build_archive_cmd(repo, name, spec, args.allow_incomplete)
        print(" ".join(cmd))
        if args.dry_run:
            continue
        rc = subprocess.call(cmd)
        print(f"{name}: archive_returncode={rc}")
        if rc != 0:
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
