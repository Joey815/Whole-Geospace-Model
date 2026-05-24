#!/usr/bin/env python3
"""Validate a paired SAMI3 -> RAIJU/GAMERA long-run smoke directory.

This is a lightweight validator that works on the login-node Python without
h5py.  It checks run logs and expected HDF5 products so a long stability run can
be accepted quickly before deeper HDF5 diagnostics.
"""

import argparse
import json
import re
from pathlib import Path


FATAL_RE = re.compile(
    r"(?:\bFATAL\b|\bforrtl\b|MPI_Abort|Unable to open input mesh|Segmentation fault|Traceback \(most recent call last\)|^\s*ERROR(?:\s+STOP|:|\s|$))",
    re.IGNORECASE | re.MULTILINE,
)


def read_text(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def add_maybe_incomplete(checks, name, ok, detail, allow_incomplete):
    if ok or not allow_incomplete:
        add(checks, name, ok, detail)
    else:
        add(checks, name, True, "{0} (allowed while incomplete)".format(detail))


def count(pattern, text):
    return len(re.findall(pattern, text))


def validate_log(checks, label, path, min_raiju_writes, allow_incomplete):
    text = read_text(path)
    add_maybe_incomplete(checks, label + "_log_exists", path.is_file(), str(path), allow_incomplete)
    add_maybe_incomplete(
        checks,
        label + "_fin",
        "Fin" in text,
        "Fin" if "Fin" in text else "missing",
        allow_incomplete,
    )
    raiju_writes = count(r"Writing RAIJU HDF5 DATA", text)
    gamera_writes = count(r"Writing HDF5 DATA", text)
    add_maybe_incomplete(
        checks,
        label + "_raiju_write_count",
        raiju_writes >= min_raiju_writes,
        "raiju_writes={0}, min={1}".format(raiju_writes, min_raiju_writes),
        allow_incomplete,
    )
    add_maybe_incomplete(
        checks,
        label + "_gamera_write_count",
        gamera_writes >= min_raiju_writes,
        "gamera_writes={0}, min={1}".format(gamera_writes, min_raiju_writes),
        allow_incomplete,
    )
    fatal = FATAL_RE.findall(text)
    add(checks, label + "_fatal_markers_absent", len(fatal) == 0, "matches={0}".format(len(fatal)))


def validate(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    checks = []
    add(checks, "run_dir_exists", run_dir.is_dir(), str(run_dir))

    base_log = run_dir / args.base_log
    proto_log = run_dir / args.prototype_log
    validate_log(checks, "baseline", base_log, args.min_raiju_writes, args.allow_incomplete)
    validate_log(checks, "prototype", proto_log, args.min_raiju_writes, args.allow_incomplete)

    required_suffixes = [
        ".gam.h5",
        ".raiju.h5",
        ".raiCpl.Res.00000.h5",
        ".gam.Res.00000.h5",
        ".raiju.Res.00000.h5",
    ]
    if args.skip_h5_products:
        add(checks, "h5_product_checks", True, "skipped")
    else:
        for prefix_label, prefix in (("baseline", args.base_prefix), ("prototype", args.prototype_prefix)):
            for suffix in required_suffixes:
                path = run_dir / (prefix + suffix)
                add_maybe_incomplete(
                    checks,
                    prefix_label + suffix.replace(".", "_") + "_exists",
                    path.is_file(),
                    str(path),
                    args.allow_incomplete,
                )

    slurm_logs = sorted(run_dir.glob("slurm-*.out"))
    if args.expect_slurm:
        add(checks, "slurm_log_exists", bool(slurm_logs), ",".join(str(p) for p in slurm_logs[-3:]))
        if slurm_logs:
            text = read_text(slurm_logs[-1])
            add_maybe_incomplete(
                checks,
                "slurm_run_complete",
                "run_complete=1" in text,
                "run_complete=1" if "run_complete=1" in text else "missing",
                args.allow_incomplete,
            )

    return checks, {"run_dir": str(run_dir)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--base-log", default="base_control_long900.log")
    parser.add_argument("--prototype-log", default="dsB_lmlt_recommended_long900.log")
    parser.add_argument("--base-prefix", default="sami3_moments_base_control_long900")
    parser.add_argument("--prototype-prefix", default="sami3_moments_dsB_lmlt_recommended_long900")
    parser.add_argument("--min-raiju-writes", type=int, default=10)
    parser.add_argument("--expect-slurm", action="store_true")
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--skip-h5-products", action="store_true")
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    checks, meta = validate(args)
    ok = all(item["ok"] for item in checks)
    result = {"ok": ok, "checks": checks, "meta": meta}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for item in checks:
        print("{0:4s} {1}: {2}".format("ok" if item["ok"] else "FAIL", item["name"], item["detail"]))
    print("overall={0}".format("ok" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
