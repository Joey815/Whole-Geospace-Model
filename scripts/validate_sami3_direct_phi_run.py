#!/usr/bin/env python3
"""Validate a SAMI3 run using separate neutral and direct-phi MPI ports."""

import argparse
import json
import re
from pathlib import Path


FATAL_PATTERNS = (
    "fatal",
    "forrtl",
    "header mismatch",
    "mpi_abort",
    "nan",
)

IGNORED_FATAL_LINES = (
    "abortOnNonfinit",
)


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def count_re(pattern, text):
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def fatal_lines(text):
    hits = []
    for line in text.splitlines():
        if any(ignored in line for ignored in IGNORED_FATAL_LINES):
            continue
        lower = line.lower()
        if "abort" in lower and not re.search(r"\babort(ed|ing)?\b", lower):
            continue
        if any(pattern in lower for pattern in FATAL_PATTERNS) or re.search(
            r"\babort(ed|ing)?\b", lower
        ):
            hits.append(line.strip())
    return hits


def parse_phi_recv(text):
    frames = []
    regex = re.compile(
        r"WACCMX_PHI_RECV\s+"
        r"(?P<frame>\d+)\s+(?P<nframes>\d+)\s+"
        r"(?P<hrut>[-+0-9.Ee]+)\s+(?P<hour>[-+0-9.Ee]+)\s+"
        r"(?P<valid>[-+0-9.Ee]+)\s+(?P<pmin>[-+0-9.Ee]+)\s+"
        r"(?P<pmax>[-+0-9.Ee]+)"
    )
    for match in regex.finditer(text):
        item = match.groupdict()
        frames.append(
            {
                "frame": int(item["frame"]),
                "nframes": int(item["nframes"]),
                "hrut": float(item["hrut"]),
                "hour": float(item["hour"]),
                "valid_until": float(item["valid"]),
                "min": float(item["pmin"]),
                "max": float(item["pmax"]),
            }
        )
    return frames


def validate(args):
    checks = []
    meta = {}
    receiver_path = Path(args.receiver_log)
    phi_sender_path = Path(args.phi_sender_log)
    neutral_sender_path = Path(args.neutral_sender_log) if args.neutral_sender_log else None
    qc_path = Path(args.recv_qc_compare) if args.recv_qc_compare else None

    add(checks, "receiver_log_exists", receiver_path.exists(), receiver_path)
    add(checks, "phi_sender_log_exists", phi_sender_path.exists(), phi_sender_path)
    if neutral_sender_path:
        add(checks, "neutral_sender_log_exists", neutral_sender_path.exists(), neutral_sender_path)
    if qc_path:
        add(checks, "recv_qc_compare_exists", qc_path.exists(), qc_path)
    if not receiver_path.exists() or not phi_sender_path.exists():
        return checks, meta

    receiver = receiver_path.read_text(errors="replace")
    phi_sender = phi_sender_path.read_text(errors="replace")
    neutral_sender = neutral_sender_path.read_text(errors="replace") if neutral_sender_path and neutral_sender_path.exists() else ""
    recv_qc = qc_path.read_text(errors="replace") if qc_path and qc_path.exists() else ""

    fatal_hits = fatal_lines(receiver) + fatal_lines(phi_sender)
    add(checks, "no_fatal_markers", not fatal_hits, fatal_hits or "none")
    add(checks, "direct_phi_port_ready", "SAMI3 direct phi port ready" in receiver, "marker")
    add(checks, "direct_phi_connected", "SAMI3 direct phi sender connected" in receiver, "marker")
    add(checks, "master_done", "MASTER: All Done!" in receiver, "marker")
    add(
        checks,
        "neutral_done_received",
        "WACCMX online done signal received:" in receiver,
        "marker",
    )
    add(
        checks,
        "direct_phi_done_received",
        "SAMI3 direct phi done signal received:" in receiver,
        "marker",
    )

    frames = parse_phi_recv(receiver)
    meta["phi_recv_frames"] = frames
    add(
        checks,
        "phi_recv_frame_count",
        len(frames) == args.expected_frames,
        f"observed={len(frames)} expected={args.expected_frames}",
    )
    add(
        checks,
        "phi_recv_frame_indices",
        [item["frame"] for item in frames] == list(range(args.expected_frames)),
        [item["frame"] for item in frames],
    )
    add(
        checks,
        "phi_recv_total_frames",
        all(item["nframes"] == args.expected_frames for item in frames),
        [item["nframes"] for item in frames],
    )
    add(
        checks,
        "phi_recv_finite_range",
        all(item["min"] <= item["max"] for item in frames),
        [(item["min"], item["max"]) for item in frames],
    )
    if args.require_changing_phi and len(frames) > 1:
        changed = any(
            abs(frames[idx]["min"] - frames[idx - 1]["min"]) > args.change_tol
            or abs(frames[idx]["max"] - frames[idx - 1]["max"]) > args.change_tol
            for idx in range(1, len(frames))
        )
        add(checks, "phi_recv_frames_change", changed, frames)

    add(
        checks,
        "phi_sender_sent_frames",
        count_re(r"PHI_DIRECT_SENDER sent frame=", phi_sender)
        + count_re(r"WACCMX_SAMI3_PHI_DIRECT sent frame=", phi_sender)
        == args.expected_frames,
        "count={}".format(
            count_re(r"PHI_DIRECT_SENDER sent frame=", phi_sender)
            + count_re(r"WACCMX_SAMI3_PHI_DIRECT sent frame=", phi_sender)
        ),
    )
    add(
        checks,
        "phi_sender_sent_done",
        "PHI_DIRECT_SENDER sent done=" in phi_sender
        or "WACCMX_SAMI3_PHI_DIRECT sent done=" in phi_sender,
        "marker",
    )
    if neutral_sender_path:
        add(
            checks,
            "neutral_sender_sent_done",
            "NEUTRAL_SENDER sent done signal" in neutral_sender,
            "marker",
        )
    if qc_path:
        add(
            checks,
            "recv_qc_compare_ok",
            "compare ok" in recv_qc,
            recv_qc.strip() or "empty",
        )

    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receiver-log", required=True)
    parser.add_argument("--phi-sender-log", required=True)
    parser.add_argument("--neutral-sender-log", default=None)
    parser.add_argument("--recv-qc-compare", default=None)
    parser.add_argument("--expected-frames", type=int, default=2)
    parser.add_argument("--require-changing-phi", action="store_true")
    parser.add_argument(
        "--allow-incomplete-run",
        action="store_true",
        help="Treat model-exit/finalize markers as advisory for live handshake checks.",
    )
    parser.add_argument("--change-tol", type=float, default=1.0e-6)
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    checks, meta = validate(args)
    advisory = set()
    if args.allow_incomplete_run:
        advisory.update(
            {
                "master_done",
                "neutral_done_received",
                "direct_phi_done_received",
                "recv_qc_compare_exists",
                "recv_qc_compare_ok",
            }
        )
    ok = all(check["ok"] or check["name"] in advisory for check in checks)
    result = {"ok": ok, "checks": checks, "meta": meta}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for check in checks:
        print("{:4s} {}: {}".format("ok" if check["ok"] else "FAIL", check["name"], check["detail"]))
    print("overall={}".format("ok" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
