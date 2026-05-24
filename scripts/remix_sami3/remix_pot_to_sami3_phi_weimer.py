#!/usr/bin/env python3
"""Convert a MAGE/REMIX POT export package to SAMI3 phi_weimer.inp.

This is a prototype adapter for the REMIX -> SAMI3 electric-potential path.
It keeps the transport route that SAMI3 already has:

    phi_weimer.inp -> potential.f90:weimer -> potpphi -> exb(phi)

The default output is a static potential packet.  SAMI3's current reader
expects a leading hour, one potential record, then the next hour; the default
next hour is a far-future sentinel so short smoke runs do not read past the
static frame.
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
    values = np.loadtxt(path, dtype=np.float64).reshape(-1)
    expected = nlat + nlon
    if values.size != expected:
        raise ValueError(
            f"{path} has {values.size} grid values; expected {expected} "
            f"for nlat={nlat}, nlon={nlon}"
        )
    return values[:nlat], values[nlat:]


def load_remix_pot(path: Path, group: str) -> dict[str, Any]:
    with h5py.File(path, "r") as h5:
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


def write_phi_weimer(path: Path, phi_statv: np.ndarray, hour0: float, valid_until: float) -> None:
    phi_f4 = np.asarray(phi_statv, dtype="<f4", order="F")
    with path.open("wb") as out:
        out.write(_fortran_record(np.asarray([hour0], dtype="<f4").tobytes()))
        out.write(_fortran_record(phi_f4.tobytes(order="F")))
        out.write(_fortran_record(np.asarray([valid_until], dtype="<f4").tobytes()))


def read_static_phi_weimer(path: Path, nlat: int, nlon: int) -> dict[str, np.ndarray]:
    records: list[bytes] = []
    with path.open("rb") as inp:
        for _ in range(3):
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

    hour0 = np.frombuffer(records[0], dtype="<f4").copy()
    phi = np.frombuffer(records[1], dtype="<f4").reshape((nlat, nlon), order="F").copy()
    valid_until = np.frombuffer(records[2], dtype="<f4").copy()
    return {"hour0": hour0, "phi": phi, "valid_until": valid_until}


def write_diagnostic_h5(
    path: Path,
    target_mlat: np.ndarray,
    target_mlon: np.ndarray,
    phi_kv: np.ndarray,
    phi_statv: np.ndarray,
    summary: dict[str, Any],
) -> None:
    with h5py.File(path, "w") as h5:
        h5.create_dataset("target_mlat_deg", data=target_mlat)
        h5.create_dataset("target_mlon_deg", data=target_mlon)
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
    parser.add_argument("--input", required=True, type=Path, help="waccmx_voltron_forward_package.h5")
    parser.add_argument("--group", default="NORTH_APEX", help="HDF5 group containing POT/theta/phi")
    parser.add_argument("--weimer-grid", required=True, type=Path, help="SAMI3 weimer_grid.dat")
    parser.add_argument("--output", required=True, type=Path, help="Output phi_weimer.inp")
    parser.add_argument("--summary-json", type=Path, help="Optional JSON summary")
    parser.add_argument("--diagnostic-h5", type=Path, help="Optional diagnostic HDF5 output")
    parser.add_argument("--target-nlat", type=int, default=125)
    parser.add_argument("--target-nlon", type=int, default=97)
    parser.add_argument("--hour0", type=float, default=0.0)
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


def main() -> None:
    args = parse_args()
    target_mlat, target_mlon = read_weimer_grid(
        args.weimer_grid, args.target_nlat, args.target_nlon
    )
    source = load_remix_pot(args.input, args.group)
    phi_kv = remix_to_sami3_phi(
        source,
        target_mlat,
        target_mlon,
        args.low_lat_mode,
        args.scale,
        args.cap_abs_kv,
        args.zero_reference,
    )
    phi_statv = phi_kv * STATVOLT_PER_KV

    if not np.all(np.isfinite(phi_statv)):
        raise ValueError("mapped phi contains NaN/Inf")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_phi_weimer(args.output, phi_statv, args.hour0, args.valid_until_hour)
    readback = read_static_phi_weimer(args.output, args.target_nlat, args.target_nlon)
    readback_diff = np.max(np.abs(readback["phi"].astype(np.float64) - phi_statv))

    summary: dict[str, Any] = {
        "schema": "remix_pot_to_sami3_phi_weimer.v0",
        "input": str(args.input),
        "group": args.group,
        "weimer_grid": str(args.weimer_grid),
        "output": str(args.output),
        "target_nlat": args.target_nlat,
        "target_nlon": args.target_nlon,
        "hour0": args.hour0,
        "valid_until_hour": args.valid_until_hour,
        "low_lat_mode": args.low_lat_mode,
        "scale": args.scale,
        "cap_abs_kv": args.cap_abs_kv if args.cap_abs_kv is not None else "none",
        "zero_reference": args.zero_reference,
        "source_pot_units": source["attrs"]["POT_units"],
        "source_mlat_min": float(np.nanmin(source["mlat_deg"])),
        "source_mlat_max": float(np.nanmax(source["mlat_deg"])),
        "source_lon_min": float(np.nanmin(source["lon_deg"])),
        "source_lon_max": float(np.nanmax(source["lon_deg"])),
        "target_mlat_min": float(np.nanmin(target_mlat)),
        "target_mlat_max": float(np.nanmax(target_mlat)),
        "target_mlon_min": float(np.nanmin(target_mlon)),
        "target_mlon_max": float(np.nanmax(target_mlon)),
        "low_lat_zero_count": int(np.count_nonzero(target_mlat < np.nanmin(source["mlat_deg"]))),
        "readback_hour0": float(readback["hour0"][0]),
        "readback_valid_until": float(readback["valid_until"][0]),
        "readback_phi_max_abs_diff_statV": float(readback_diff),
    }
    summary.update(summarize_array("phi_kV", phi_kv))
    summary.update(summarize_array("phi_statV", phi_statv))

    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if args.diagnostic_h5:
        args.diagnostic_h5.parent.mkdir(parents=True, exist_ok=True)
        write_diagnostic_h5(args.diagnostic_h5, target_mlat, target_mlon, phi_kv, phi_statv, summary)

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
