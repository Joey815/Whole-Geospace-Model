#!/usr/bin/env python3
"""Validate a REMIX/Voltron -> SAMI3 MPI phi payload binary.

The payload schema is written by
scripts/remix_sami3/remix_pot_to_sami3_phi_weimer.py:

    int32 magic, version, nlat, nlon, nframes
    repeated nframes:
      int32 frame_index
      float32 frame_hour, valid_until_hour
      float32 phi[nlat,nlon] in Fortran order
"""

import argparse
import json
import math
import struct
from pathlib import Path


PHI_MAGIC = 20260524
PHI_VERSION = 1
PHI_NLAT = 125
PHI_NLON = 97


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def close(a, b, tol):
    return abs(float(a) - float(b)) <= tol


def find_payload(run_dir, explicit):
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.exists() else None
    if not run_dir:
        return None
    root = Path(run_dir).expanduser()
    candidates = sorted(root.glob("**/*phi_payload*.bin"))
    if not candidates:
        candidates = sorted(root.glob("**/*append2*.bin"))
    return candidates[0] if candidates else None


def parse_payload(path):
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError(f"{path} is too short for a phi payload header")
    magic, version, nlat, nlon, nframes = struct.unpack_from("<5i", raw, 0)
    offset = 20
    frame_bytes = nlat * nlon * 4
    frames = []
    frame_diffs = []
    previous = None

    for iframe in range(nframes):
        needed = offset + 4 + 8 + frame_bytes
        if len(raw) < needed:
            raise ValueError(f"{path} ended inside frame {iframe}")
        frame_index = struct.unpack_from("<i", raw, offset)[0]
        offset += 4
        hour, valid_until = struct.unpack_from("<2f", raw, offset)
        offset += 8
        values = struct.unpack_from(f"<{nlat * nlon}f", raw, offset)
        offset += frame_bytes

        finite_values = [value for value in values if math.isfinite(value)]
        finite_count = len(finite_values)
        nonzero_count = sum(1 for value in values if value != 0.0)
        frame = {
            "frame_index": frame_index,
            "hour": hour,
            "valid_until": valid_until,
            "finite_count": finite_count,
            "nonzero_count": nonzero_count,
            "min": min(finite_values) if finite_values else None,
            "max": max(finite_values) if finite_values else None,
            "mean": sum(finite_values) / finite_count if finite_values else None,
        }
        frames.append(frame)

        if previous is not None:
            diffs = [
                value - prev
                for value, prev in zip(values, previous)
                if math.isfinite(value) and math.isfinite(prev)
            ]
            if diffs:
                max_abs = max(abs(value) for value in diffs)
                rms = math.sqrt(sum(value * value for value in diffs) / len(diffs))
            else:
                max_abs = float("nan")
                rms = float("nan")
            frame_diffs.append(
                {
                    "from_frame": iframe - 1,
                    "to_frame": iframe,
                    "finite_pairs": len(diffs),
                    "max_abs": max_abs,
                    "rms": rms,
                }
            )
        previous = values

    return {
        "path": str(path),
        "size": len(raw),
        "expected_size": 20 + nframes * (4 + 8 + frame_bytes),
        "trailing_bytes": len(raw) - offset,
        "header": {
            "magic": magic,
            "version": version,
            "nlat": nlat,
            "nlon": nlon,
            "nframes": nframes,
        },
        "frames": frames,
        "frame_diffs": frame_diffs,
    }


def validate(args):
    checks = []
    meta = {}
    payload = find_payload(args.run_dir, args.payload)
    add(checks, "phi_payload_exists", payload is not None or args.allow_incomplete, payload or "missing")
    if payload is None:
        return checks, meta

    try:
        parsed = parse_payload(payload)
    except Exception as exc:  # noqa: BLE001 - validation tool reports details
        add(checks, "phi_payload_parse", False, exc)
        return checks, meta

    meta["phi_payload"] = parsed
    header = parsed["header"]
    frames = parsed["frames"]
    frame_cells = header["nlat"] * header["nlon"]

    add(
        checks,
        "phi_payload_header",
        header["magic"] == PHI_MAGIC
        and header["version"] == PHI_VERSION
        and header["nlat"] == args.expect_nlat
        and header["nlon"] == args.expect_nlon,
        header,
    )
    if args.expected_frames is not None:
        add(
            checks,
            "phi_payload_frame_count",
            header["nframes"] == args.expected_frames,
            f"nframes={header['nframes']} expected={args.expected_frames}",
        )
    add(
        checks,
        "phi_payload_exact_size",
        parsed["trailing_bytes"] == 0 and parsed["size"] == parsed["expected_size"],
        "size={} expected={} trailing={}".format(
            parsed["size"], parsed["expected_size"], parsed["trailing_bytes"]
        ),
    )
    add(
        checks,
        "phi_payload_frame_indices",
        all(frame["frame_index"] == idx for idx, frame in enumerate(frames)),
        "indices={}".format([frame["frame_index"] for frame in frames]),
    )
    add(
        checks,
        "phi_payload_frames_finite",
        all(frame["finite_count"] == frame_cells for frame in frames),
        "finite_counts={}".format([frame["finite_count"] for frame in frames]),
    )
    hours = [frame["hour"] for frame in frames]
    valid_until = [frame["valid_until"] for frame in frames]
    add(
        checks,
        "phi_payload_hours_strictly_increasing",
        all(hours[idx] > hours[idx - 1] + args.hour_tol for idx in range(1, len(hours))),
        f"hours={hours}",
    )
    add(
        checks,
        "phi_payload_valid_until_after_hour",
        all(v >= h - args.hour_tol for h, v in zip(hours, valid_until)),
        f"hours={hours} valid_until={valid_until}",
    )
    if args.require_linked_valid_until and len(frames) > 1:
        linked = all(
            close(valid_until[idx], hours[idx + 1], args.hour_tol)
            for idx in range(len(frames) - 1)
        )
        add(
            checks,
            "phi_payload_valid_until_links_next_hour",
            linked,
            f"hours={hours} valid_until={valid_until}",
        )
    if args.expected_first_hour is not None:
        first_hour = frames[0]["hour"] if frames else None
        add(
            checks,
            "phi_payload_first_hour",
            first_hour is not None and close(first_hour, args.expected_first_hour, args.hour_tol),
            f"first_hour={first_hour} expected={args.expected_first_hour}",
        )
    if args.require_nonzero_phi:
        add(
            checks,
            "phi_payload_nonzero",
            all(frame["nonzero_count"] > 0 for frame in frames),
            "nonzero_counts={}".format([frame["nonzero_count"] for frame in frames]),
        )
    if args.max_abs_phi_statv is not None:
        extrema = [
            max(abs(frame["min"]), abs(frame["max"]))
            for frame in frames
            if frame["min"] is not None and frame["max"] is not None
        ]
        observed = max(extrema) if extrema else float("nan")
        add(
            checks,
            "phi_payload_abs_range",
            bool(extrema) and observed <= args.max_abs_phi_statv,
            f"max_abs={observed} limit={args.max_abs_phi_statv}",
        )
    if args.require_changing_phi_frames and len(frames) > 1:
        max_diff = max((item["max_abs"] for item in parsed["frame_diffs"]), default=0.0)
        add(
            checks,
            "phi_payload_frame_change",
            max_diff >= args.min_phi_frame_max_abs_diff,
            f"max_abs_diff={max_diff} min={args.min_phi_frame_max_abs_diff}",
        )
    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", default=None)
    parser.add_argument("--run-dir", default=None)
    parser.add_argument("--expected-frames", type=int, default=None)
    parser.add_argument("--expected-first-hour", type=float, default=None)
    parser.add_argument("--expect-nlat", type=int, default=PHI_NLAT)
    parser.add_argument("--expect-nlon", type=int, default=PHI_NLON)
    parser.add_argument("--hour-tol", type=float, default=1.0e-7)
    parser.add_argument("--require-linked-valid-until", action="store_true")
    parser.add_argument("--require-nonzero-phi", action="store_true")
    parser.add_argument("--require-changing-phi-frames", action="store_true")
    parser.add_argument("--min-phi-frame-max-abs-diff", type=float, default=1.0e-6)
    parser.add_argument("--max-abs-phi-statv", type=float, default=None)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    if not args.payload and not args.run_dir:
        parser.error("one of --payload or --run-dir is required")

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
