#!/usr/bin/env python3
"""Validate WACCM-X/SAMI3 replay compare cadence artifacts."""

import argparse
import json
import re
from pathlib import Path


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def parse_int_list(text):
    return [int(item.strip()) for item in text.split(",") if item.strip()]


def parse_float_list(text):
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def parse_compare(path):
    text = path.read_text(errors="replace")
    match = re.search(
        r"WACCMX_RECV_QC compare ok:\s+ranks=(\d+)\s+occurrence=(\d+)\s+"
        r"step_set=\[([^\]]*)\]\s+packet_hour_set=\[([^\]]*)\]\s+"
        r"max_abs=([^\s]+)\s+max_rel=([^\s]+)",
        text,
    )
    if not match:
        return {"path": str(path), "ok_marker": False, "text": text}
    return {
        "path": str(path),
        "ok_marker": True,
        "ranks": int(match.group(1)),
        "occurrence": int(match.group(2)),
        "step_set": parse_int_list(match.group(3)),
        "packet_hour_set": parse_float_list(match.group(4)),
        "max_abs": float(match.group(5)),
        "max_rel": float(match.group(6)),
    }


def close(a, b, tol):
    return abs(float(a) - float(b)) <= tol


def validate(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    checks = []
    meta = {"run_dir": str(run_dir), "packets": []}
    add(checks, "run_dir_exists", run_dir.is_dir(), run_dir)
    if not run_dir.is_dir():
        return checks, meta

    packet_hours = []
    packet_steps = []
    for packet in range(args.expected_packets):
        tag = "pkt{:06d}".format(packet)
        summary_path = run_dir / "live_dump_summary_{}.txt".format(tag)
        replay_path = run_dir / "replay_builder_{}.out".format(tag)
        compare_path = run_dir / "recv_qc_compare_{}.txt".format(tag)
        add(checks, "packet{}_summary_exists".format(packet), summary_path.is_file(), summary_path)
        add(checks, "packet{}_replay_exists".format(packet), replay_path.is_file(), replay_path)
        add(checks, "packet{}_compare_exists".format(packet), compare_path.is_file(), compare_path)
        if not compare_path.is_file():
            continue
        compare = parse_compare(compare_path)
        meta["packets"].append(compare)
        add(checks, "packet{}_compare_ok_marker".format(packet), compare.get("ok_marker"), compare)
        add(
            checks,
            "packet{}_occurrence".format(packet),
            compare.get("occurrence") == packet,
            "occurrence={} expected={}".format(compare.get("occurrence"), packet),
        )
        add(
            checks,
            "packet{}_ranks".format(packet),
            compare.get("ranks") == args.expected_ranks,
            "ranks={} expected={}".format(compare.get("ranks"), args.expected_ranks),
        )
        steps = compare.get("step_set", [])
        hours = compare.get("packet_hour_set", [])
        add(checks, "packet{}_single_step".format(packet), len(steps) == 1, steps)
        add(checks, "packet{}_single_hour".format(packet), len(hours) == 1, hours)
        if steps:
            packet_steps.append(steps[0])
            add(
                checks,
                "packet{}_step_value".format(packet),
                steps[0] == packet if args.expect_step_equals_packet else steps[0] >= 0,
                "step={} packet={}".format(steps[0], packet),
            )
        if hours:
            packet_hours.append(hours[0])
        add(
            checks,
            "packet{}_max_rel".format(packet),
            compare.get("max_rel", float("inf")) <= args.max_rel,
            "max_rel={} limit={}".format(compare.get("max_rel"), args.max_rel),
        )

    add(
        checks,
        "packet_steps_monotonic",
        all(packet_steps[idx] > packet_steps[idx - 1] for idx in range(1, len(packet_steps))),
        "steps={}".format(packet_steps),
    )
    add(
        checks,
        "packet_hours_monotonic",
        all(packet_hours[idx] > packet_hours[idx - 1] for idx in range(1, len(packet_hours))),
        "hours={}".format(packet_hours),
    )
    if args.expected_cadence_hours is not None and len(packet_hours) > 1:
        diffs = [packet_hours[idx] - packet_hours[idx - 1] for idx in range(1, len(packet_hours))]
        add(
            checks,
            "packet_hour_cadence",
            all(close(diff, args.expected_cadence_hours, args.hour_tol) for diff in diffs),
            "diffs={} expected={}".format(diffs, args.expected_cadence_hours),
        )
    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--expected-packets", type=int, required=True)
    parser.add_argument("--expected-ranks", type=int, default=32)
    parser.add_argument("--expected-cadence-hours", type=float, default=None)
    parser.add_argument("--hour-tol", type=float, default=1.0e-6)
    parser.add_argument("--max-rel", type=float, default=1.0e-6)
    parser.add_argument("--expect-step-equals-packet", action="store_true")
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    checks, meta = validate(args)
    ok = all(check["ok"] for check in checks)
    result = {"ok": ok, "checks": checks, "meta": meta}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for check in checks:
        print("{:4s} {}: {}".format("ok" if check["ok"] else "FAIL", check["name"], check["detail"]))
    print("overall={}".format("ok" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
