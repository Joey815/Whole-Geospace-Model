#!/usr/bin/env python3
"""Convert a MAGE/REMIX POT export package to SAMI3 phi_weimer.inp.

This is a prototype adapter for the REMIX -> SAMI3 electric-potential path.
It keeps the transport route that SAMI3 already has:

    phi_weimer.inp -> potential.f90:weimer -> potpphi -> exb(phi)

The default output is a static potential packet.  With multiple input packages
the output is a SAMI3-native time sequence:

    hour0, phi0, hour1, phi1, ..., phiN, valid_until_hour

SAMI3's current reader keeps each potential until hrut reaches the following
hour record.  The default final valid-until hour is a far-future sentinel so
short smoke runs do not read past the last replay frame.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any

import h5py
import numpy as np


STATVOLT_PER_KV = 1000.0 / 300.0


def _decode_attr(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "item"):
        try:
            item = value.item()
            if isinstance(item, bytes):
                return item.decode("utf-8", errors="replace")
            return item
        except Exception:
            pass
    return value


def read_weimer_grid(path: Path, nlat: int, nlon: int) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(
        [float(item) for item in path.read_text().split()], dtype=np.float64
    )
    expected = nlat + nlon
    if values.size != expected:
        raise ValueError(
            f"{path} has {values.size} grid values; expected {expected} "
            f"for nlat={nlat}, nlon={nlon}"
        )
    return values[:nlat], values[nlat:]


def load_remix_pot(path: Path, group: str) -> dict[str, Any]:
    with h5py.File(path, "r") as h5:
        meta_attrs = {}
        if "Meta" in h5:
            meta_attrs = {
                key: _decode_attr(value) for key, value in h5["Meta"].attrs.items()
            }
        if group not in h5:
            raise KeyError(f"{path} does not contain group {group!r}")
        grp = h5[group]
        for name in ("theta", "phi", "POT"):
            if name not in grp:
                raise KeyError(f"{path}:{group} does not contain dataset {name!r}")

        theta = np.asarray(grp["theta"][()], dtype=np.float64)
        phi = np.asarray(grp["phi"][()], dtype=np.float64)
        pot = np.asarray(grp["POT"][()], dtype=np.float64)

        attrs = {
            "POT_units": _decode_attr(grp["POT"].attrs.get("Units", "")),
            "theta_units": _decode_attr(grp["theta"].attrs.get("Units", "")),
            "phi_units": _decode_attr(grp["phi"].attrs.get("Units", "")),
        }

    if theta.shape != phi.shape or theta.shape != pot.shape:
        raise ValueError(
            f"theta/phi/POT shape mismatch: {theta.shape}, {phi.shape}, {pot.shape}"
        )
    if attrs["POT_units"] not in ("kV", b"kV"):
        raise ValueError(f"Expected POT units kV, got {attrs['POT_units']!r}")

    theta_deg = np.rad2deg(theta[:, 0])
    lon_deg = np.mod(np.rad2deg(phi[0, :]), 360.0)
    mlat_deg = 90.0 - theta_deg

    return {
        "theta_deg": theta_deg,
        "mlat_deg": mlat_deg,
        "lon_deg": lon_deg,
        "pot_kv": pot,
        "attrs": attrs,
        "meta": meta_attrs,
    }


def interp_periodic_lon(
    source_lon_deg: np.ndarray,
    field_by_lat_lon: np.ndarray,
    target_lon_deg: np.ndarray,
) -> np.ndarray:
    order = np.argsort(source_lon_deg)
    lon_sorted = np.asarray(source_lon_deg[order], dtype=np.float64)
    field_sorted = np.asarray(field_by_lat_lon[:, order], dtype=np.float64)

    if lon_sorted[0] < 0.0 or lon_sorted[-1] >= 360.0:
        lon_sorted = np.mod(lon_sorted, 360.0)
        order = np.argsort(lon_sorted)
        lon_sorted = lon_sorted[order]
        field_sorted = field_sorted[:, order]

    lon_ext = np.concatenate([lon_sorted, [lon_sorted[0] + 360.0]])
    field_ext = np.concatenate([field_sorted, field_sorted[:, :1]], axis=1)
    target = np.mod(target_lon_deg, 360.0)

    out = np.empty((field_by_lat_lon.shape[0], target.size), dtype=np.float64)
    for i in range(field_by_lat_lon.shape[0]):
        out[i, :] = np.interp(target, lon_ext, field_ext[i, :])
    return out


def interp_lat(
    source_mlat_deg: np.ndarray,
    field_by_lat_lon: np.ndarray,
    target_mlat_deg: np.ndarray,
    low_lat_mode: str,
) -> np.ndarray:
    order = np.argsort(source_mlat_deg)
    lat_sorted = np.asarray(source_mlat_deg[order], dtype=np.float64)
    field_sorted = np.asarray(field_by_lat_lon[order, :], dtype=np.float64)

    if low_lat_mode == "zero":
        left = 0.0
    elif low_lat_mode == "edge":
        left = None
    elif low_lat_mode == "nan":
        left = np.nan
    else:
        raise ValueError(f"unknown low-lat mode: {low_lat_mode}")

    out = np.empty((target_mlat_deg.size, field_by_lat_lon.shape[1]), dtype=np.float64)
    for j in range(field_by_lat_lon.shape[1]):
        if left is None:
            out[:, j] = np.interp(target_mlat_deg, lat_sorted, field_sorted[:, j])
        else:
            out[:, j] = np.interp(
                target_mlat_deg,
                lat_sorted,
                field_sorted[:, j],
                left=left,
                right=field_sorted[-1, j],
            )
    return out


def remix_to_sami3_phi(
    source: dict[str, Any],
    target_mlat_deg: np.ndarray,
    target_mlon_deg: np.ndarray,
    low_lat_mode: str,
    scale: float,
    cap_abs_kv: float | None,
    zero_reference: str,
) -> np.ndarray:
    pot_lon = interp_periodic_lon(source["lon_deg"], source["pot_kv"], target_mlon_deg)
    pot_target = interp_lat(source["mlat_deg"], pot_lon, target_mlat_deg, low_lat_mode)

    if zero_reference == "target_pole":
        pole = np.nanmean(pot_target[-1, :])
        pot_target = pot_target - pole
    elif zero_reference == "target_mean":
        pot_target = pot_target - np.nanmean(pot_target)
    elif zero_reference == "none":
        pass
    else:
        raise ValueError(f"unknown zero-reference mode: {zero_reference}")

    pot_target = pot_target * scale

    if cap_abs_kv is not None:
        pot_target = np.clip(pot_target, -cap_abs_kv, cap_abs_kv)

    return pot_target


def _fortran_record(payload: bytes) -> bytes:
    nbytes = len(payload)
    marker = struct.pack("<i", nbytes)
    return marker + payload + marker


def write_phi_weimer(
    path: Path,
    phi_statv: np.ndarray,
    frame_hours: np.ndarray,
    valid_until: float,
) -> None:
    frames = np.asarray(phi_statv, dtype=np.float64)
    if frames.ndim == 2:
        frames = frames[np.newaxis, :, :]
    if frames.ndim != 3:
        raise ValueError(f"phi_statv must be 2D or 3D, got shape {frames.shape}")
    if frame_hours.size != frames.shape[0]:
        raise ValueError(
            f"frame hour count {frame_hours.size} does not match frame count {frames.shape[0]}"
        )
    if not np.all(np.diff(frame_hours) > 0.0):
        raise ValueError(f"frame hours must be strictly increasing: {frame_hours.tolist()}")
    if valid_until <= frame_hours[-1]:
        raise ValueError(
            f"valid_until_hour={valid_until} must be greater than last frame hour={frame_hours[-1]}"
        )

    with path.open("wb") as out:
        out.write(_fortran_record(np.asarray([frame_hours[0]], dtype="<f4").tobytes()))
        for iframe in range(frames.shape[0]):
            phi_f4 = np.asarray(frames[iframe], dtype="<f4", order="F")
            out.write(_fortran_record(phi_f4.tobytes(order="F")))
            next_hour = frame_hours[iframe + 1] if iframe + 1 < frames.shape[0] else valid_until
            out.write(_fortran_record(np.asarray([next_hour], dtype="<f4").tobytes()))


def read_phi_weimer(path: Path, nlat: int, nlon: int, nframes: int) -> dict[str, np.ndarray]:
    records: list[bytes] = []
    nrecords = 2 * nframes + 1
    with path.open("rb") as inp:
        for _ in range(nrecords):
            raw = inp.read(4)
            if len(raw) != 4:
                raise EOFError("unexpected EOF reading record marker")
            (nbytes,) = struct.unpack("<i", raw)
            payload = inp.read(nbytes)
            tail = inp.read(4)
            if len(payload) != nbytes or len(tail) != 4:
                raise EOFError("unexpected EOF reading record payload")
            (nbytes_tail,) = struct.unpack("<i", tail)
            if nbytes_tail != nbytes:
                raise ValueError("Fortran record marker mismatch")
            records.append(payload)

    hours = [float(np.frombuffer(records[0], dtype="<f4")[0])]
    phis = []
    for iframe in range(nframes):
        phis.append(
            np.frombuffer(records[2 * iframe + 1], dtype="<f4")
            .reshape((nlat, nlon), order="F")
            .copy()
        )
        hours.append(float(np.frombuffer(records[2 * iframe + 2], dtype="<f4")[0]))
    return {
        "hours": np.asarray(hours, dtype=np.float64),
        "phi": np.stack(phis, axis=0),
    }


def write_diagnostic_h5(
    path: Path,
    target_mlat: np.ndarray,
    target_mlon: np.ndarray,
    frame_hours: np.ndarray,
    phi_kv: np.ndarray,
    phi_statv: np.ndarray,
    summary: dict[str, Any],
) -> None:
    with h5py.File(path, "w") as h5:
        h5.create_dataset("target_mlat_deg", data=target_mlat)
        h5.create_dataset("target_mlon_deg", data=target_mlon)
        h5.create_dataset("frame_hours", data=frame_hours)
        h5.create_dataset("phi_kV", data=phi_kv)
        h5.create_dataset("phi_statV", data=phi_statv)
        meta = h5.create_group("Meta")
        for key, value in summary.items():
            if isinstance(value, (str, int, float, np.integer, np.floating)):
                meta.attrs[key] = value


def summarize_array(name: str, arr: np.ndarray) -> dict[str, Any]:
    finite = np.isfinite(arr)
    return {
        f"{name}_shape": list(arr.shape),
        f"{name}_finite_count": int(np.count_nonzero(finite)),
        f"{name}_nan_count": int(np.count_nonzero(np.isnan(arr))),
        f"{name}_min": float(np.nanmin(arr)),
        f"{name}_max": float(np.nanmax(arr)),
        f"{name}_mean": float(np.nanmean(arr)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Map MAGE/REMIX POT[kV] HDF5 export to SAMI3 phi_weimer.inp"
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
    parser.add_argument("--diagnostic-h5", type=Path, help="Optional diagnostic HDF5 output")
    parser.add_argument("--target-nlat", type=int, default=125)
    parser.add_argument("--target-nlon", type=int, default=97)
    parser.add_argument("--hour0", type=float, default=0.0)
    parser.add_argument(
        "--frame-hours",
        help="comma-separated frame hours; overrides MJD/cadence inference",
    )
    parser.add_argument(
        "--cadence-hours",
        type=float,
        help="fallback frame cadence when multiple inputs do not have increasing MJD",
    )
    parser.add_argument("--valid-until-hour", type=float, default=1.0e30)
    parser.add_argument("--low-lat-mode", choices=("zero", "edge", "nan"), default="zero")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--cap-abs-kv", type=float)
    parser.add_argument(
        "--zero-reference",
        choices=("none", "target_pole", "target_mean"),
        default="none",
    )
    return parser.parse_args()


def parse_frame_hours(text: str) -> np.ndarray:
    values = [float(item.strip()) for item in text.split(",") if item.strip()]
    if not values:
        raise ValueError("--frame-hours did not contain any values")
    return np.asarray(values, dtype=np.float64)


def infer_frame_hours(args: argparse.Namespace, sources: list[dict[str, Any]]) -> np.ndarray:
    nframes = len(sources)
    if args.frame_hours:
        frame_hours = parse_frame_hours(args.frame_hours)
        if frame_hours.size != nframes:
            raise ValueError(
                f"--frame-hours has {frame_hours.size} values but {nframes} inputs were provided"
            )
        return frame_hours

    mjds = []
    for source in sources:
        value = source["meta"].get("mjd")
        try:
            mjds.append(float(value))
        except (TypeError, ValueError):
            mjds.append(np.nan)
    mjds_arr = np.asarray(mjds, dtype=np.float64)
    if nframes == 1:
        return np.asarray([args.hour0], dtype=np.float64)
    if np.all(np.isfinite(mjds_arr)):
        frame_hours = args.hour0 + (mjds_arr - mjds_arr[0]) * 24.0
        if np.all(np.diff(frame_hours) > 0.0):
            return frame_hours

    if args.cadence_hours is None:
        raise ValueError(
            "multiple inputs require strictly increasing Meta/mjd, --frame-hours, "
            "or --cadence-hours"
        )
    return args.hour0 + np.arange(nframes, dtype=np.float64) * args.cadence_hours


def main() -> None:
    args = parse_args()
    target_mlat, target_mlon = read_weimer_grid(
        args.weimer_grid, args.target_nlat, args.target_nlon
    )
    sources = [load_remix_pot(path, args.group) for path in args.input]
    frame_hours = infer_frame_hours(args, sources)
    phi_kv_frames = [
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
    ]
    if len(phi_kv_frames) == 1:
        phi_kv = phi_kv_frames[0]
    else:
        phi_kv = np.stack(phi_kv_frames, axis=0)
    phi_statv = phi_kv * STATVOLT_PER_KV

    if not np.all(np.isfinite(phi_statv)):
        raise ValueError("mapped phi contains NaN/Inf")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_phi_weimer(args.output, phi_statv, frame_hours, args.valid_until_hour)
    readback = read_phi_weimer(
        args.output, args.target_nlat, args.target_nlon, len(phi_kv_frames)
    )
    readback_phi = readback["phi"][0] if len(phi_kv_frames) == 1 else readback["phi"]
    readback_diff = np.max(np.abs(readback_phi.astype(np.float64) - phi_statv))
    expected_readback_hours = np.asarray(
        np.concatenate([frame_hours, [args.valid_until_hour]]), dtype="<f4"
    ).astype(np.float64)
    readback_hour_diff = np.max(
        np.abs(readback["hours"].astype(np.float64) - expected_readback_hours)
    )

    summary: dict[str, Any] = {
        "schema": "remix_pot_to_sami3_phi_weimer.v1",
        "input": str(args.input[0]) if len(args.input) == 1 else [str(path) for path in args.input],
        "inputs": [str(path) for path in args.input],
        "group": args.group,
        "weimer_grid": str(args.weimer_grid),
        "output": str(args.output),
        "target_nlat": args.target_nlat,
        "target_nlon": args.target_nlon,
        "nframes": len(phi_kv_frames),
        "frame_hours": frame_hours.tolist(),
        "hour0": float(frame_hours[0]),
        "valid_until_hour": args.valid_until_hour,
        "low_lat_mode": args.low_lat_mode,
        "scale": args.scale,
        "cap_abs_kv": args.cap_abs_kv if args.cap_abs_kv is not None else "none",
        "zero_reference": args.zero_reference,
        "source_pot_units": sources[0]["attrs"]["POT_units"],
        "source_mlat_min": float(np.nanmin(sources[0]["mlat_deg"])),
        "source_mlat_max": float(np.nanmax(sources[0]["mlat_deg"])),
        "source_lon_min": float(np.nanmin(sources[0]["lon_deg"])),
        "source_lon_max": float(np.nanmax(sources[0]["lon_deg"])),
        "target_mlat_min": float(np.nanmin(target_mlat)),
        "target_mlat_max": float(np.nanmax(target_mlat)),
        "target_mlon_min": float(np.nanmin(target_mlon)),
        "target_mlon_max": float(np.nanmax(target_mlon)),
        "low_lat_zero_count": int(np.count_nonzero(target_mlat < np.nanmin(sources[0]["mlat_deg"]))),
        "readback_hours": readback["hours"].tolist(),
        "readback_hour_max_abs_diff": float(readback_hour_diff),
        "readback_hour0": float(readback["hours"][0]),
        "readback_valid_until": float(readback["hours"][-1]),
        "readback_phi_max_abs_diff_statV": float(readback_diff),
        "frames": [
            {
                "input": str(path),
                "hour": float(hour),
                "source_mjd": source["meta"].get("mjd", ""),
                "source_time_seconds": source["meta"].get("time_seconds", ""),
                "source_mix": source["meta"].get("source_mix", ""),
            }
            for path, hour, source in zip(args.input, frame_hours, sources)
        ],
    }
    summary.update(summarize_array("phi_kV", phi_kv))
    summary.update(summarize_array("phi_statV", phi_statv))

    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if args.diagnostic_h5:
        args.diagnostic_h5.parent.mkdir(parents=True, exist_ok=True)
        write_diagnostic_h5(
            args.diagnostic_h5, target_mlat, target_mlon, frame_hours, phi_kv, phi_statv, summary
        )

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
