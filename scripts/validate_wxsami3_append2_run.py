#!/usr/bin/env python3
"""Validate a WACCM-X/SAMI3 append2 coupling smoke run.

The validator is intentionally log-driven.  It checks the contract that matters
for the current integration smoke:

* Voltron/REMIX produced a two-frame SAMI3 MPI phi payload.
* The WACCM-X sender advertised and sent the expected phi frames.
* SAMI3 received both frames and advanced through the time gate.
* The neutral replay QC still matches the receiver log.
* Both sides reached the clean shutdown markers.
"""

import argparse
import json
import re
import struct
from pathlib import Path


PHI_MAGIC = 20260524
PHI_VERSION = 1
PHI_NLAT = 125
PHI_NLON = 97


def read_text(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def collect_text(paths):
    chunks = []
    for path in paths:
        text = read_text(path)
        if text:
            chunks.append(f"\n### {path}\n{text}")
    return "\n".join(chunks)


def existing_logs(run_dir):
    names = [
        "slurm-*.out",
        "slurm-*.err",
        "waccmx_cesm.out",
        "sami3_online_receiver.out",
        "phi_payload_summary.txt",
        "recv_qc_compare*.txt",
        "live_dump_summary_pkt*.txt",
        "replay_builder_pkt*.out",
    ]
    paths = []
    for pattern in names:
        paths.extend(sorted(run_dir.glob(pattern)))
    return [p for p in paths if p.is_file()]


def parse_phi_payload(path):
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError(f"{path} is too short for phi payload header")
    magic, version, nlat, nlon, nframes = struct.unpack_from("<5i", raw, 0)
    off = 20
    frames = []
    for iframe in range(nframes):
        need = off + 4 + 8 + nlat * nlon * 4
        if len(raw) < need:
            raise ValueError(f"{path} ended inside frame {iframe}")
        frame_index = struct.unpack_from("<i", raw, off)[0]
        off += 4
        hour, valid_until = struct.unpack_from("<2f", raw, off)
        off += 8
        vals = struct.unpack_from(f"<{nlat*nlon}f", raw, off)
        off += nlat * nlon * 4
        frames.append(
            {
                "frame_index": frame_index,
                "hour": hour,
                "valid_until": valid_until,
                "min": min(vals),
                "max": max(vals),
                "nonzero": sum(1 for value in vals if value != 0.0),
            }
        )
    return {
        "path": str(path),
        "size": len(raw),
        "header": [magic, version, nlat, nlon, nframes],
        "frames": frames,
    }


def find_payload(run_dir, explicit):
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.exists() else None
    candidates = sorted(run_dir.glob("**/*phi_payload*.bin"))
    if not candidates:
        candidates = sorted(run_dir.glob("**/*append2*.bin"))
    return candidates[0] if candidates else None


def add_check(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def count(pattern, text):
    return len(re.findall(pattern, text))


def validate(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    checks = []
    meta = {"run_dir": str(run_dir)}

    add_check(checks, "run_dir_exists", run_dir.is_dir() or args.allow_incomplete, str(run_dir))
    paths = existing_logs(run_dir)
    text = collect_text(paths)
    meta["log_files"] = [str(path) for path in paths]

    payload = find_payload(run_dir, args.phi_payload)
    if payload is None:
        add_check(checks, "phi_payload_exists", args.allow_incomplete, "no payload found")
    else:
        try:
            phi = parse_phi_payload(payload)
            meta["phi_payload"] = phi
            header = phi["header"]
            nframes = header[4]
            add_check(
                checks,
                "phi_payload_header",
                header[:4] == [PHI_MAGIC, PHI_VERSION, PHI_NLAT, PHI_NLON],
                str(header),
            )
            add_check(
                checks,
                "phi_payload_frame_count",
                nframes == args.expected_phi_frames,
                f"nframes={nframes}, expected={args.expected_phi_frames}",
            )
            first_hour = phi["frames"][0]["hour"] if phi["frames"] else None
            add_check(
                checks,
                "phi_payload_starts_at_zero",
                first_hour is not None and abs(first_hour) <= args.hour_tol,
                f"first_hour={first_hour}",
            )
        except Exception as exc:  # noqa: BLE001 - report validation detail
            add_check(checks, "phi_payload_parse", False, str(exc))

    sender_frames = count(r"WXSAMI3 sent phi frame:", text)
    sender_payload_frames = re.findall(r"WXSAMI3 sent phi payload frames:\s+(\d+)", text)
    add_check(
        checks,
        "sender_phi_frames",
        sender_frames >= args.expected_phi_frames or args.allow_incomplete,
        f"sender_phi_frame_markers={sender_frames}",
    )
    if sender_payload_frames:
        got = int(sender_payload_frames[-1])
        add_check(
            checks,
            "sender_phi_payload_frame_count",
            got == args.expected_phi_frames,
            f"reported={got}, expected={args.expected_phi_frames}",
        )
    else:
        add_check(
            checks,
            "sender_phi_payload_frame_count",
            args.allow_incomplete,
            "no sender payload-frame marker",
        )

    if args.expect_phi_wait_marker:
        wait_markers = count(r"WXSAMI3 phi payload ready after wait", text)
        add_check(
            checks,
            "sender_phi_wait_marker",
            wait_markers >= 1 or args.allow_incomplete,
            f"wait_markers={wait_markers}",
        )

    if args.expect_direct_wait_mode:
        direct_wait_markers = count(r"DIRECT_WAIT_MODE=1", text)
        writer_pid_markers = count(r"VOLTRON_WRITER_PID=\d+", text)
        add_check(
            checks,
            "direct_wait_mode_marker",
            direct_wait_markers >= 1 or args.allow_incomplete,
            f"direct_wait_markers={direct_wait_markers}",
        )
        add_check(
            checks,
            "voltron_writer_pid_marker",
            writer_pid_markers >= 1 or args.allow_incomplete,
            f"writer_pid_markers={writer_pid_markers}",
        )

    recv_frames = count(r"WACCMX_PHI_RECV", text)
    add_check(
        checks,
        "receiver_phi_frames",
        recv_frames >= args.expected_phi_frames or args.allow_incomplete,
        f"receiver_phi_markers={recv_frames}",
    )

    add_check(
        checks,
        "receiver_done",
        "MASTER: All Done!" in text or args.allow_incomplete,
        "MASTER: All Done!" if "MASTER: All Done!" in text else "missing",
    )
    add_check(
        checks,
        "sender_done",
        "END OF MODEL RUN" in text or args.allow_incomplete,
        "END OF MODEL RUN" if "END OF MODEL RUN" in text else "missing",
    )
    qc_ok = count(r"WACCMX_RECV_QC compare ok", text)
    add_check(
        checks,
        "neutral_replay_qc",
        qc_ok >= 1 or args.allow_incomplete,
        f"qc_ok_markers={qc_ok}",
    )
    bad = re.findall(r"(?:ERROR|FATAL|forrtl|NaN|Abort|header mismatch)", text, re.IGNORECASE)
    add_check(checks, "fatal_markers_absent", len(bad) == 0, f"matches={len(bad)}")
    return checks, meta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--phi-payload", default=None)
    parser.add_argument("--expected-phi-frames", type=int, default=2)
    parser.add_argument("--hour-tol", type=float, default=1.0e-7)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--expect-phi-wait-marker", action="store_true")
    parser.add_argument("--expect-direct-wait-mode", action="store_true")
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    checks, meta = validate(args)
    ok = all(check["ok"] for check in checks)
    result = {"ok": ok, "checks": checks, "meta": meta}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    for check in checks:
        status = "ok" if check["ok"] else "FAIL"
        print(f"{status:4s} {check['name']}: {check['detail']}")
    print(f"overall={'ok' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
