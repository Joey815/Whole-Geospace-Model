#!/usr/bin/env python3
"""Write or append REMIX-derived frames in SAMI3 phi_weimer stream format.

This is a diagnostic bridge toward a live REMIX -> SAMI3 potential feed.  It
uses the same mapping as remix_pot_to_sami3_phi_weimer.py, but can leave a
phi_weimer.inp file intentionally incomplete:

    prefix mode: hour0, phi0, hour1
    append mode: phi1, hour2, phi2, hour3, ...

SAMI3's current reader opens phi_weimer.inp once and advances when hrut reaches
the next hour record.  A runtime append test can therefore check whether a
second REMIX-derived frame appended after SAMI3 startup is visible to the
existing reader before replacing this file-backed stream with an MPI payload.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any

import numpy as np

from remix_pot_to_sami3_phi_weimer import (
    _fortran_record,
    infer_frame_hours,
    load_remix_pot,
    read_weimer_grid,
    remix_to_sami3_phi,
    summarize_array,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write or append REMIX POT frames to a SAMI3 phi_weimer stream"
    )
    parser.add_argument(
        "--write-mode",
        choices=("full", "prefix", "append"),
        required=True,
        help="full writes a complete stream; prefix writes an intentionally open stream; append adds remaining frames",
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        nargs="+",
        help="one or more waccmx_voltron_forward_package.h5 files",
    )
    parser.add_argument("--group", default="NORTH_APEX", help="HDF5 group containing POT/theta/phi")
    parser.add_argument("--weimer-grid", required=True, type=Path, help="SAMI3 weimer_grid.dat")
    parser.add_argument("--output", required=True, type=Path, help="Output phi_weimer.inp")
    parser.add_argument("--summary-json", type=Path, help="Optional JSON summary")
    parser.add_argument("--record-summary", type=Path, help="Optional text record summary")
    parser.add_argument("--target-nlat", type=int, default=125)
    parser.add_argument("--target-nlon", type=int, default=97)
    parser.add_argument("--hour0", type=float, default=0.0)
    parser.add_argument("--frame-hours", help="comma-separated frame hours")
    parser.add_argument("--cadence-hours", type=float, help="fallback frame cadence")
    parser.add_argument("--valid-until-hour", type=float, default=1.0e30)
    parser.add_argument("--low-lat-mode", choices=("zero", "edge", "nan"), default="zero")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--cap-abs-kv", type=float)
    parser.add_argument(
        "--zero-reference",
        choices=("none", "target_pole", "target_mean"),
        default="none",
    )
    parser.add_argument(
        "--prefix-frame-count",
        type=int,
        default=1,
        help="number of frames to write in prefix mode",
    )
    parser.add_argument(
        "--append-start-index",
        type=int,
        default=1,
        help="zero-based frame index to start appending in append mode",
    )
    parser.add_argument(
        "--skip-prefix-check",
        action="store_true",
        help="do not verify that the existing stream ends at the append frame hour",
    )
    return parser.parse_args()


def map_frames(args: argparse.Namespace) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict[str, Any]]]:
    target_mlat, target_mlon = read_weimer_grid(
        args.weimer_grid, args.target_nlat, args.target_nlon
    )
    sources = [load_remix_pot(path, args.group) for path in args.input]
    frame_hours = infer_frame_hours(args, sources)
    phi_kv = np.stack(
        [
            remix_to_sami3_phi(
                source,
                target_mlat,
                target_mlon,
                args.low_lat_mode,
                args.scale,
                args.cap_abs_kv,
                args.zero_reference,
            )
            for source in sources
        ],
        axis=0,
    )
    phi_statv = phi_kv * (1000.0 / 300.0)
    if not np.all(np.isfinite(phi_statv)):
        raise ValueError("mapped phi contains NaN/Inf")
    return frame_hours, phi_kv, phi_statv, sources


def hour_record(hour: float) -> bytes:
    return _fortran_record(np.asarray([hour], dtype="<f4").tobytes())


def phi_record(phi: np.ndarray) -> bytes:
    phi_f4 = np.asarray(phi, dtype="<f4", order="F")
    return _fortran_record(phi_f4.tobytes(order="F"))


def append_records(path: Path, records: list[bytes], append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "ab" if append else "wb"
    with path.open(mode) as out:
        for record in records:
            out.write(record)


def scan_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    offset = 0
    with path.open("rb") as inp:
        index = 0
        while True:
            raw = inp.read(4)
            if not raw:
                break
            if len(raw) != 4:
                raise EOFError(f"truncated record marker at byte offset {offset}")
            (nbytes,) = struct.unpack("<i", raw)
            payload = inp.read(nbytes)
            tail = inp.read(4)
            if len(payload) != nbytes or len(tail) != 4:
                raise EOFError(f"truncated record payload at record {index}")
            (tail_nbytes,) = struct.unpack("<i", tail)
            if tail_nbytes != nbytes:
                raise ValueError(f"record marker mismatch at record {index}")
            item: dict[str, Any] = {
                "index": index,
                "offset": offset,
                "nbytes": nbytes,
                "kind": "hour" if nbytes == 4 else "phi",
            }
            if nbytes == 4:
                item["hour"] = float(np.frombuffer(payload, dtype="<f4")[0])
            records.append(item)
            offset += 8 + nbytes
            index += 1
    return records


def write_record_summary(path: Path, records: list[dict[str, Any]]) -> None:
    lines = []
    for item in records:
        if item["kind"] == "hour":
            lines.append(
                f"{item['index']} hour nbytes={item['nbytes']} hour={item['hour']:.9g}"
            )
        else:
            lines.append(f"{item['index']} phi nbytes={item['nbytes']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def make_records(
    mode: str,
    frame_hours: np.ndarray,
    phi_statv: np.ndarray,
    valid_until: float,
    prefix_frame_count: int,
    append_start_index: int,
) -> tuple[list[bytes], int, int]:
    nframes = phi_statv.shape[0]
    if nframes < 1:
        raise ValueError("at least one frame is required")
    if not np.all(np.diff(frame_hours) > 0.0):
        raise ValueError(f"frame hours must be strictly increasing: {frame_hours.tolist()}")
    if valid_until <= frame_hours[-1]:
        raise ValueError(
            f"valid_until_hour={valid_until} must exceed last frame hour={frame_hours[-1]}"
        )

    if mode == "full":
        start = 0
        stop = nframes
        records = [hour_record(float(frame_hours[0]))]
    elif mode == "prefix":
        if prefix_frame_count < 1 or prefix_frame_count > nframes:
            raise ValueError(
                f"prefix-frame-count must be in [1,{nframes}], got {prefix_frame_count}"
            )
        start = 0
        stop = prefix_frame_count
        records = [hour_record(float(frame_hours[0]))]
    elif mode == "append":
        if append_start_index < 1 or append_start_index >= nframes:
            raise ValueError(
                f"append-start-index must be in [1,{nframes - 1}], got {append_start_index}"
            )
        start = append_start_index
        stop = nframes
        records = []
    else:
        raise ValueError(f"unknown mode {mode}")

    for iframe in range(start, stop):
        records.append(phi_record(phi_statv[iframe]))
        next_hour = frame_hours[iframe + 1] if iframe + 1 < nframes else valid_until
        records.append(hour_record(float(next_hour)))
    return records, start, stop


def verify_append_prefix(path: Path, expected_hour: float) -> None:
    records = scan_records(path)
    if not records:
        raise ValueError(f"{path} is empty")
    last = records[-1]
    if last["kind"] != "hour":
        raise ValueError(f"{path} does not end with an hour record")
    got = float(last["hour"])
    if abs(got - expected_hour) > max(1.0e-6, abs(expected_hour) * 1.0e-6):
        raise ValueError(
            f"{path} ends at hour {got}, expected append start hour {expected_hour}"
        )


def main() -> None:
    args = parse_args()
    frame_hours, phi_kv, phi_statv, sources = map_frames(args)
    if args.write_mode == "append" and not args.skip_prefix_check:
        verify_append_prefix(args.output, float(frame_hours[args.append_start_index]))

    records, start, stop = make_records(
        args.write_mode,
        frame_hours,
        phi_statv,
        args.valid_until_hour,
        args.prefix_frame_count,
        args.append_start_index,
    )
    append_records(args.output, records, append=args.write_mode == "append")
    record_info = scan_records(args.output)

    summary: dict[str, Any] = {
        "schema": "remix_phi_weimer_stream_update.v1",
        "write_mode": args.write_mode,
        "input": [str(path) for path in args.input],
        "group": args.group,
        "weimer_grid": str(args.weimer_grid),
        "output": str(args.output),
        "target_nlat": args.target_nlat,
        "target_nlon": args.target_nlon,
        "nframes_available": int(phi_statv.shape[0]),
        "frame_hours": frame_hours.tolist(),
        "valid_until_hour": args.valid_until_hour,
        "written_frame_start": int(start),
        "written_frame_stop_exclusive": int(stop),
        "prefix_frame_count": args.prefix_frame_count,
        "append_start_index": args.append_start_index,
        "record_count_after_write": len(record_info),
        "last_record": record_info[-1] if record_info else {},
        "source_frames": [
            {
                "input": str(path),
                "hour": float(hour),
                "source_mjd": source["meta"].get("mjd", ""),
                "source_time_seconds": source["meta"].get("time_seconds", ""),
            }
            for path, hour, source in zip(args.input, frame_hours, sources)
        ],
    }
    summary.update(summarize_array("phi_kV", phi_kv))
    summary.update(summarize_array("phi_statV", phi_statv))

    if args.record_summary:
        write_record_summary(args.record_summary, record_info)
    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
