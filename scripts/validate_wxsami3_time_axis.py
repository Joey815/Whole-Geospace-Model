#!/usr/bin/env python3
"""Validate WACCM-X/SAMI3 neutral and phi time-axis consistency."""

import argparse
import json
import re
from pathlib import Path

from validate_remix_sami3_phi_payload import find_payload, parse_payload


LOG_PATTERNS = [
    "slurm-*.out",
    "slurm-*.err",
    "waccmx_cesm.out",
    "sami3_online_receiver.out",
]


def read_text(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def collect_text(run_dir):
    chunks = []
    paths = []
    for pattern in LOG_PATTERNS:
        for path in sorted(run_dir.glob(pattern)):
            if path.is_file():
                paths.append(path)
                chunks.append(read_text(path))
    return "\n".join(chunks), paths


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def close(a, b, tol):
    return abs(float(a) - float(b)) <= tol


def floats_from_tail(line, marker):
    try:
        tail = line.split(marker, 1)[1]
    except IndexError:
        return []
    values = []
    for token in tail.split():
        try:
            values.append(float(token))
        except ValueError:
            pass
    return values


def parse_sender_neutral_packets(text):
    records = []
    seen = set()
    marker = "WXSAMI3 sent live neutral packet:"
    for line in text.splitlines():
        if marker not in line:
            continue
        values = floats_from_tail(line, marker)
        if len(values) < 3:
            continue
        record = {
            "nstep": int(values[0]),
            "packet_hour": float(values[1]),
            "packet_index": int(values[2]),
        }
        key = (record["nstep"], round(record["packet_hour"], 9), record["packet_index"])
        if key not in seen:
            seen.add(key)
            records.append(record)
    return records


def parse_receiver_neutral_packets(text):
    records = []
    for line in text.splitlines():
        if "WACCMX_RECV_QC" not in line:
            continue
        values = floats_from_tail(line, "WACCMX_RECV_QC")
        if len(values) < 3:
            continue
        records.append(
            {
                "taskid": int(values[0]),
                "packet_index": int(values[1]),
                "packet_hour": float(values[2]),
            }
        )
    return records


def parse_receiver_phi_records(text):
    records = []
    seen = set()
    for line in text.splitlines():
        if "WACCMX_PHI_RECV" not in line:
            continue
        values = floats_from_tail(line, "WACCMX_PHI_RECV")
        if len(values) < 7:
            continue
        record = {
            "frame_index": int(values[0]),
            "nframes": int(values[1]),
            "hrut": float(values[2]),
            "frame_hour": float(values[3]),
            "valid_until": float(values[4]),
            "min": float(values[5]),
            "max": float(values[6]),
        }
        key = (
            record["frame_index"],
            record["nframes"],
            round(record["hrut"], 9),
            round(record["frame_hour"], 9),
            round(record["valid_until"], 6) if abs(record["valid_until"]) < 1.0e20 else "huge",
        )
        if key not in seen:
            seen.add(key)
            records.append(record)
    return records


def packet_summary(records):
    by_packet = {}
    for record in records:
        item = by_packet.setdefault(record["packet_index"], {"hours": [], "tasks": set(), "count": 0})
        item["hours"].append(record["packet_hour"])
        item["tasks"].add(record["taskid"])
        item["count"] += 1
    summary = {}
    for packet, item in by_packet.items():
        hours = item["hours"]
        summary[packet] = {
            "count": item["count"],
            "unique_tasks": len(item["tasks"]),
            "hour_min": min(hours),
            "hour_max": max(hours),
        }
    return summary


def intervals_cover(hours, frames, tol):
    uncovered = []
    for hour in hours:
        covered = False
        for frame in frames:
            if hour >= frame["hour"] - tol and hour <= frame["valid_until"] + tol:
                covered = True
                break
        if not covered:
            uncovered.append(hour)
    return uncovered


def validate(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    checks = []
    meta = {"run_dir": str(run_dir)}
    add(checks, "run_dir_exists", run_dir.is_dir() or args.allow_incomplete, run_dir)
    text, paths = collect_text(run_dir)
    meta["log_files"] = [str(path) for path in paths]

    sender_packets = parse_sender_neutral_packets(text)
    receiver_packets = parse_receiver_neutral_packets(text)
    receiver_summary = packet_summary(receiver_packets)
    receiver_phi = parse_receiver_phi_records(text)
    meta["sender_neutral_packets"] = sender_packets
    meta["receiver_neutral_packet_summary"] = {
        str(key): value for key, value in sorted(receiver_summary.items())
    }
    meta["receiver_phi_records"] = receiver_phi

    if args.expected_neutral_packets is not None:
        add(
            checks,
            "sender_neutral_packet_count",
            len(sender_packets) == args.expected_neutral_packets or args.allow_incomplete,
            "sender_packets={} expected={}".format(len(sender_packets), args.expected_neutral_packets),
        )
        add(
            checks,
            "receiver_neutral_packet_count",
            len(receiver_summary) == args.expected_neutral_packets or args.allow_incomplete,
            "receiver_packets={} expected={}".format(len(receiver_summary), args.expected_neutral_packets),
        )

    sender_hours = [record["packet_hour"] for record in sorted(sender_packets, key=lambda item: item["packet_index"])]
    receiver_hours = [
        value["hour_min"]
        for _, value in sorted(receiver_summary.items())
        if close(value["hour_min"], value["hour_max"], args.hour_tol)
    ]
    add(
        checks,
        "receiver_packet_hours_consistent",
        all(close(value["hour_min"], value["hour_max"], args.hour_tol) for value in receiver_summary.values())
        or args.allow_incomplete,
        receiver_summary,
    )
    add(
        checks,
        "receiver_packet_hours_monotonic",
        all(receiver_hours[idx] > receiver_hours[idx - 1] - args.hour_tol for idx in range(1, len(receiver_hours))),
        f"receiver_hours={receiver_hours}",
    )
    if args.expected_sami3_workers is not None:
        add(
            checks,
            "receiver_worker_coverage",
            all(value["unique_tasks"] == args.expected_sami3_workers for value in receiver_summary.values())
            or args.allow_incomplete,
            "unique_tasks={} expected={}".format(
                [value["unique_tasks"] for _, value in sorted(receiver_summary.items())],
                args.expected_sami3_workers,
            ),
        )
    if sender_hours and receiver_hours:
        matched = 0
        for hour in sender_hours:
            if any(close(hour, recv_hour, args.hour_tol) for recv_hour in receiver_hours):
                matched += 1
        add(
            checks,
            "sender_receiver_neutral_hours_match",
            matched == len(sender_hours) or args.allow_incomplete,
            "matched={} sender_hours={} receiver_hours={}".format(matched, sender_hours, receiver_hours),
        )

    if args.expected_neutral_cadence_hours is not None and len(receiver_hours) > 1:
        diffs = [receiver_hours[idx] - receiver_hours[idx - 1] for idx in range(1, len(receiver_hours))]
        add(
            checks,
            "receiver_neutral_cadence",
            all(close(diff, args.expected_neutral_cadence_hours, args.hour_tol) for diff in diffs),
            "diffs={} expected={}".format(diffs, args.expected_neutral_cadence_hours),
        )

    payload = find_payload(run_dir, args.phi_payload)
    if payload is None:
        add(checks, "phi_payload_exists", args.allow_incomplete, "missing")
        frames = []
    else:
        parsed = parse_payload(payload)
        meta["phi_payload"] = parsed
        frames = parsed["frames"]
        if args.expected_phi_frames is not None:
            add(
                checks,
                "phi_payload_frame_count",
                len(frames) == args.expected_phi_frames,
                "frames={} expected={}".format(len(frames), args.expected_phi_frames),
            )
        add(
            checks,
            "phi_payload_hours_strictly_increasing",
            all(frames[idx]["hour"] > frames[idx - 1]["hour"] + args.hour_tol for idx in range(1, len(frames))),
            "hours={}".format([frame["hour"] for frame in frames]),
        )
        if args.allow_overlap_phi_validity:
            add(
                checks,
                "phi_payload_valid_until_overlaps_next",
                all(
                    frames[idx]["valid_until"] + args.hour_tol >= frames[idx + 1]["hour"]
                    for idx in range(len(frames) - 1)
                ),
                "hours={} valid_until={}".format(
                    [frame["hour"] for frame in frames],
                    [frame["valid_until"] for frame in frames],
                ),
            )
        else:
            add(
                checks,
                "phi_payload_valid_until_links",
                all(close(frames[idx]["valid_until"], frames[idx + 1]["hour"], args.hour_tol) for idx in range(len(frames) - 1)),
                "hours={} valid_until={}".format(
                    [frame["hour"] for frame in frames],
                    [frame["valid_until"] for frame in frames],
                ),
            )

    neutral_hours = receiver_hours or sender_hours
    if frames and neutral_hours:
        uncovered = intervals_cover(neutral_hours, frames, args.hour_tol)
        add(
            checks,
            "phi_payload_covers_neutral_packets",
            not uncovered,
            "uncovered_neutral_hours={}".format(uncovered),
        )

    if args.expected_phi_frames is not None:
        add(
            checks,
            "receiver_phi_frame_count",
            len(receiver_phi) >= args.expected_phi_frames or args.allow_incomplete,
            "receiver_phi_records={} expected_min={}".format(len(receiver_phi), args.expected_phi_frames),
        )
    add(
        checks,
        "receiver_phi_records_within_validity",
        all(
            record["hrut"] >= record["frame_hour"] - args.hour_tol
            and record["hrut"] <= record["valid_until"] + args.hour_tol
            for record in receiver_phi
        ),
        "records={}".format(len(receiver_phi)),
    )
    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--phi-payload", default=None)
    parser.add_argument("--expected-neutral-packets", type=int, default=None)
    parser.add_argument("--expected-phi-frames", type=int, default=None)
    parser.add_argument("--expected-sami3-workers", type=int, default=None)
    parser.add_argument("--expected-neutral-cadence-hours", type=float, default=None)
    parser.add_argument("--hour-tol", type=float, default=1.0e-6)
    parser.add_argument(
        "--allow-overlap-phi-validity",
        action="store_true",
        help="Allow phi valid_until windows to overlap the next frame hour instead of requiring exact linkage.",
    )
    parser.add_argument("--allow-incomplete", action="store_true")
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
