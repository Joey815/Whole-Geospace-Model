#!/usr/bin/env python3
"""Validate WACCM-X -> SAMI3 receiver top-blend policy diagnostics."""

import argparse
import json
import re
from pathlib import Path


def read_text(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def collect_logs(run_dir, receiver_log):
    if receiver_log:
        path = Path(receiver_log).expanduser().resolve()
        return [path], read_text(path)

    run_dir = Path(run_dir).expanduser().resolve()
    patterns = ["sami3_online_receiver.out", "slurm-*.out", "slurm_*.out"]
    paths = []
    for pattern in patterns:
        paths.extend(sorted(run_dir.glob(pattern)))
    paths = [path for path in paths if path.is_file()]
    chunks = []
    for path in paths:
        text = read_text(path)
        if text:
            chunks.append("\n### {}\n{}".format(path, text))
    return paths, "\n".join(chunks)


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def close(a, b, tol):
    return abs(a - b) <= tol


def parse_policy(text):
    linear = re.search(
        r"WACCMX neutral top blend policy:\s+linear .*? between km\s+"
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)\s+"
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)",
        text,
    )
    if linear:
        return {
            "mode": "linear",
            "bottom_km": float(linear.group(1)),
            "top_km": float(linear.group(2)),
        }
    if re.search(r"WACCMX neutral top blend policy:\s+none", text):
        return {"mode": "none"}
    return None


def parse_numeric_lines(text, marker):
    rows = []
    for line in text.splitlines():
        if marker not in line:
            continue
        tail = line.split(marker, 1)[1]
        values = []
        for token in tail.split():
            try:
                values.append(float(token))
            except ValueError:
                pass
        rows.append(values)
    return rows


def validate(args):
    checks = []
    meta = {}
    paths, text = collect_logs(args.run_dir, args.receiver_log)
    meta["log_files"] = [str(path) for path in paths]
    add(checks, "logs_present", bool(text) or args.allow_incomplete, meta["log_files"])
    if not text:
        return checks, meta

    policy = parse_policy(text)
    meta["policy"] = policy
    add(checks, "topblend_policy_logged", policy is not None or args.allow_incomplete, policy)
    if policy is not None and args.expect_top_blend_mode:
        add(
            checks,
            "topblend_mode",
            policy.get("mode") == args.expect_top_blend_mode,
            "actual={} expected={}".format(policy.get("mode"), args.expect_top_blend_mode),
        )
    if policy is not None and policy.get("mode") == "linear":
        if args.expect_bottom_km is not None:
            add(
                checks,
                "topblend_bottom_km",
                close(policy["bottom_km"], args.expect_bottom_km, args.km_tol),
                "actual={} expected={} tol={}".format(policy["bottom_km"], args.expect_bottom_km, args.km_tol),
            )
        if args.expect_top_km is not None:
            add(
                checks,
                "topblend_top_km",
                close(policy["top_km"], args.expect_top_km, args.km_tol),
                "actual={} expected={} tol={}".format(policy["top_km"], args.expect_top_km, args.km_tol),
            )

    blend_rows = parse_numeric_lines(text, "WACCMX_APPLY_BLEND")
    meta["apply_blend_lines"] = len(blend_rows)
    add(
        checks,
        "apply_blend_line_count",
        len(blend_rows) >= args.min_apply_blend_lines or args.allow_incomplete,
        "count={} min={}".format(len(blend_rows), args.min_apply_blend_lines),
    )
    valid_blend_rows = [row for row in blend_rows if len(row) >= 13]
    meta["apply_blend_parseable_lines"] = len(valid_blend_rows)
    if blend_rows:
        add(checks, "apply_blend_parseable", len(valid_blend_rows) == len(blend_rows), "{} of {}".format(len(valid_blend_rows), len(blend_rows)))

    if valid_blend_rows:
        enabled = [int(row[4]) for row in valid_blend_rows]
        bottom = [row[5] for row in valid_blend_rows]
        top = [row[6] for row in valid_blend_rows]
        blend_i = [int(row[8]) for row in valid_blend_rows]
        blend_f = [int(row[11]) for row in valid_blend_rows]
        full_i = [int(row[7]) for row in valid_blend_rows]
        full_f = [int(row[10]) for row in valid_blend_rows]
        native_i = [int(row[9]) for row in valid_blend_rows]
        native_f = [int(row[12]) for row in valid_blend_rows]

        total_blend = sum(blend_i) + sum(blend_f)
        meta["blend_enabled_values"] = sorted(set(enabled))
        meta["blend_i_total"] = sum(blend_i)
        meta["blend_f_total"] = sum(blend_f)
        meta["blend_cell_total"] = total_blend
        meta["full_i_total"] = sum(full_i)
        meta["full_f_total"] = sum(full_f)
        meta["native_top_i_total"] = sum(native_i)
        meta["native_top_f_total"] = sum(native_f)
        add(
            checks,
            "blend_cell_total",
            total_blend >= args.min_total_blend_cells or args.allow_incomplete,
            "total={} min={}".format(total_blend, args.min_total_blend_cells),
        )
        if args.expect_top_blend_mode == "linear":
            add(checks, "blend_enabled", all(value == 1 for value in enabled), sorted(set(enabled)))
        if args.expect_bottom_km is not None:
            add(
                checks,
                "apply_blend_bottom_km",
                all(close(value, args.expect_bottom_km, args.km_tol) for value in bottom),
                "min={} max={} expected={}".format(min(bottom), max(bottom), args.expect_bottom_km),
            )
        if args.expect_top_km is not None:
            add(
                checks,
                "apply_blend_top_km",
                all(close(value, args.expect_top_km, args.km_tol) for value in top),
                "min={} max={} expected={}".format(min(top), max(top), args.expect_top_km),
            )

    source_rows = parse_numeric_lines(text, "WACCMX_APPLY_SOURCE_FLAGS")
    recv_source_rows = parse_numeric_lines(text, "WACCMX_RECV_SOURCE_FLAGS")
    meta["apply_source_flag_lines"] = len(source_rows)
    meta["recv_source_flag_lines"] = len(recv_source_rows)
    if args.require_zero_unknown_source_flags:
        unknown_apply = [int(row[8]) for row in source_rows if len(row) >= 9]
        unknown_recv = [int(row[8]) for row in recv_source_rows if len(row) >= 9]
        meta["unknown_apply_total"] = sum(unknown_apply) if unknown_apply else None
        meta["unknown_recv_total"] = sum(unknown_recv) if unknown_recv else None
        add(
            checks,
            "apply_source_unknown_zero",
            bool(unknown_apply) and sum(unknown_apply) == 0,
            "total={}".format(sum(unknown_apply) if unknown_apply else None),
        )
        add(
            checks,
            "recv_source_unknown_zero",
            bool(unknown_recv) and sum(unknown_recv) == 0,
            "total={}".format(sum(unknown_recv) if unknown_recv else None),
        )

    qc_rows = parse_numeric_lines(text, "WACCMX_APPLY_QC")
    valid_qc_rows = [row for row in qc_rows if len(row) >= 12]
    meta["apply_qc_lines"] = len(qc_rows)
    if args.require_he_native and valid_qc_rows:
        ok_he = all(int(row[8]) == int(row[4]) and int(row[9]) == int(row[6]) for row in valid_qc_rows)
        add(checks, "he_native_matches_valid", ok_he, "checked_lines={}".format(len(valid_qc_rows)))
    elif args.require_he_native:
        add(checks, "he_native_matches_valid", args.allow_incomplete, "no parseable WACCMX_APPLY_QC lines")

    if args.require_w_zero and valid_qc_rows:
        ok_w = all(int(row[10]) == int(row[4]) and int(row[11]) == int(row[6]) for row in valid_qc_rows)
        add(checks, "w_zero_matches_valid", ok_w, "checked_lines={}".format(len(valid_qc_rows)))
    elif args.require_w_zero:
        add(checks, "w_zero_matches_valid", args.allow_incomplete, "no parseable WACCMX_APPLY_QC lines")

    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default=".")
    parser.add_argument("--receiver-log", default=None)
    parser.add_argument("--expect-top-blend-mode", choices=["linear", "none"], default=None)
    parser.add_argument("--expect-bottom-km", type=float, default=None)
    parser.add_argument("--expect-top-km", type=float, default=None)
    parser.add_argument("--km-tol", type=float, default=1.0e-4)
    parser.add_argument("--min-apply-blend-lines", type=int, default=0)
    parser.add_argument("--min-total-blend-cells", type=int, default=0)
    parser.add_argument("--require-zero-unknown-source-flags", action="store_true")
    parser.add_argument("--require-he-native", action="store_true")
    parser.add_argument("--require-w-zero", action="store_true")
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    checks, meta = validate(args)
    ok = all(item["ok"] for item in checks)
    result = {"ok": ok, "checks": checks, "meta": meta}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for item in checks:
        print("{:4s} {}: {}".format("ok" if item["ok"] else "FAIL", item["name"], item["detail"]))
    print("overall={}".format("ok" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
