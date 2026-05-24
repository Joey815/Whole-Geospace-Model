#!/usr/bin/env python3
"""Archive small evidence from a SAMI3 -> RAIJU/GAMERA long-run smoke."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run_checked(cmd, stdout_path):
    with stdout_path.open("w") as fp:
        proc = subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, universal_newlines=True)
    return proc.returncode


def copy_if_exists(src, archive_dir, copied):
    if src.is_file():
        dst = archive_dir / src.name
        shutil.copy2(str(src), str(dst))
        copied.append({"source": str(src), "archive": str(dst), "bytes": dst.stat().st_size})


def collect_files(run_dir, label):
    names = [
        "base_control_{0}.log".format(label),
        "dsB_lmlt_recommended_{0}.log".format(label),
        "tinyCase_base_control_{0}.xml".format(label),
        "tinyCase_sami3_moments_dsB_lmlt_recommended_{0}.xml".format(label),
        "recommended_{0}_summary.txt".format(label),
    ]
    files = [run_dir / name for name in names]
    files.extend(sorted(run_dir.glob("slurm-*.out")))
    return files


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
    parser.add_argument("--label", required=True, help="Run label such as long900 or long1800")
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    run_dir = Path(args.run_dir).expanduser().resolve()
    archive_dir = Path(args.archive_dir).expanduser()
    archive_dir.mkdir(parents=True, exist_ok=True)

    validator_json = archive_dir / "validate_sami3_raiju_longrun.json"
    validator_txt = archive_dir / "validate_sami3_raiju_longrun.txt"
    cmd = [
        sys.executable,
        str(repo / "scripts" / "validate_sami3_raiju_longrun.py"),
        "--run-dir",
        str(run_dir),
        "--label",
        args.label,
        "--expect-slurm",
        "--json-output",
        str(validator_json),
    ]
    if args.allow_incomplete:
        cmd.append("--allow-incomplete")
    validator_rc = run_checked(cmd, validator_txt)

    copied = []
    for path in collect_files(run_dir, args.label):
        copy_if_exists(path, archive_dir, copied)
    sacct = write_sacct(args.job_id, archive_dir)

    summary = {
        "ok": validator_rc == 0,
        "run_dir": str(run_dir),
        "archive_dir": str(archive_dir),
        "label": args.label,
        "job_id": args.job_id,
        "validator": {
            "returncode": validator_rc,
            "text": str(validator_txt),
            "json": str(validator_json),
        },
        "copied_files": copied,
        "sacct": sacct,
    }
    (archive_dir / "archive_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    lines = [
        "# SAMI3 -> RAIJU/GAMERA Longrun Archive Summary",
        "",
        "run_dir: {}".format(run_dir),
        "label: {}".format(args.label),
        "job_id: {}".format(args.job_id if args.job_id else ""),
        "validator_returncode: {}".format(validator_rc),
        "copied_files: {}".format(len(copied)),
        "overall: {}".format("ok" if summary["ok"] else "FAIL"),
        "",
        "Validator text output:",
        "",
        "- validate_sami3_raiju_longrun.txt",
    ]
    (archive_dir / "README.md").write_text("\n".join(lines) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
