#!/usr/bin/env python3
"""Read and summarize WXSAMI3 live CAM phys_state snapshot dumps.

The dump files are written by the copied CAM SourceMod sender when
WXSAMI3_LIVE_DUMP_PREFIX is set.  They are diagnostic replay inputs, not the
online SAMI3 payload itself.
"""

import argparse
import glob
import json
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np


PROFILE_NAMES = ["T_K", "U_m_s", "V_m_s", "OMEGA_Pa_s", "PMID_Pa", "ZM_m", "MBARV_kg_mol"]
SPECIES = ["O", "O2", "H", "N", "NO", "N2", "He"]


def finite_minmax(values: np.ndarray) -> Tuple[Optional[float], Optional[float], int]:
    good = np.isfinite(values) & (np.abs(values) < np.finfo(np.float64).max * 0.5)
    if not np.any(good):
        return None, None, int(values.size)
    return float(np.min(values[good])), float(np.max(values[good])), int(values.size - np.count_nonzero(good))


def read_one(path: Path) -> dict:
    data = path.read_bytes()
    offset = 0

    def take(dtype: np.dtype, count: int) -> np.ndarray:
        nonlocal offset
        nbytes = np.dtype(dtype).itemsize * count
        if offset + nbytes > len(data):
            raise ValueError(f"{path}: truncated while reading {count} values of {dtype}")
        arr = np.frombuffer(data, dtype=dtype, count=count, offset=offset)
        offset += nbytes
        return arr.copy()

    header = take(np.dtype("<i4"), 12)
    magic, version, nstep, packet, rank, nprocs, pver, nspecies, nprofile, ncols, has_mbarv, layout = header
    dtime_phys = float(take(np.dtype("<f8"), 1)[0])
    species_indices = take(np.dtype("<i4"), int(nspecies))
    cid = take(np.dtype("<i4"), int(ncols))
    lchnk = take(np.dtype("<i4"), int(ncols))
    col = take(np.dtype("<i4"), int(ncols))
    lat = take(np.dtype("<f8"), int(ncols))
    lon = take(np.dtype("<f8"), int(ncols))
    ps = take(np.dtype("<f8"), int(ncols))
    profile_raw = take(np.dtype("<f8"), int(pver * ncols * nprofile))
    qprof_raw = take(np.dtype("<f8"), int(pver * ncols * nspecies))

    profile = profile_raw.reshape((int(pver), int(ncols), int(nprofile)), order="F")
    qprof = qprof_raw.reshape((int(pver), int(ncols), int(nspecies)), order="F")

    return {
        "path": str(path),
        "header": {
            "magic": int(magic),
            "version": int(version),
            "nstep": int(nstep),
            "packet": int(packet),
            "rank": int(rank),
            "nprocs": int(nprocs),
            "pver": int(pver),
            "nspecies": int(nspecies),
            "nprofile": int(nprofile),
            "ncols": int(ncols),
            "has_mbarv": bool(has_mbarv),
            "layout": int(layout),
            "dtime_phys_s": dtime_phys,
            "species_indices": species_indices.astype(int).tolist(),
        },
        "cid": cid,
        "lchnk": lchnk,
        "col": col,
        "lat": lat,
        "lon": lon,
        "ps": ps,
        "profile": profile,
        "qprof": qprof,
        "bytes_read": offset,
        "bytes_total": len(data),
    }


def summarize(files: List[Path]) -> dict:
    records = [read_one(path) for path in files]
    if not records:
        raise SystemExit("no dump files matched")

    total_cols = sum(rec["header"]["ncols"] for rec in records)
    packets = sorted({rec["header"]["packet"] for rec in records})
    ranks = sorted({rec["header"]["rank"] for rec in records})
    nsteps = sorted({rec["header"]["nstep"] for rec in records})
    bad_sizes = [rec["path"] for rec in records if rec["bytes_read"] != rec["bytes_total"]]

    lat = np.concatenate([rec["lat"] for rec in records])
    lon = np.concatenate([rec["lon"] for rec in records])
    cid = np.concatenate([rec["cid"] for rec in records])
    ps = np.concatenate([rec["ps"] for rec in records])

    profile_stats = {}
    for idx, name in enumerate(PROFILE_NAMES):
        values = np.concatenate([rec["profile"][:, :, idx].ravel(order="F") for rec in records])
        profile_stats[name] = dict(zip(["min", "max", "bad"], finite_minmax(values)))

    q_stats = {}
    for idx, name in enumerate(SPECIES):
        values = np.concatenate([rec["qprof"][:, :, idx].ravel(order="F") for rec in records])
        q_stats[name] = dict(zip(["min", "max", "bad"], finite_minmax(values)))

    cid_good = cid[cid >= 0]
    return {
        "file_count": len(records),
        "packets": packets,
        "nsteps": nsteps,
        "ranks": ranks,
        "rank_count": len(ranks),
        "total_cols": int(total_cols),
        "bad_size_files": bad_sizes,
        "lat_deg": dict(zip(["min", "max", "bad"], finite_minmax(lat))),
        "lon_deg": dict(zip(["min", "max", "bad"], finite_minmax(lon))),
        "cid": {
            "min": int(np.min(cid_good)) if cid_good.size else None,
            "max": int(np.max(cid_good)) if cid_good.size else None,
            "missing": int(np.count_nonzero(cid < 0)),
            "unique": int(np.unique(cid_good).size) if cid_good.size else 0,
        },
        "ps_pa": dict(zip(["min", "max", "bad"], finite_minmax(ps))),
        "profile": profile_stats,
        "q": q_stats,
    }


def write_merged_npz(files: List[Path], out_path: Path) -> dict:
    records = [read_one(path) for path in files]
    if not records:
        raise SystemExit("no dump files matched")

    cid = np.concatenate([rec["cid"] for rec in records])
    lchnk = np.concatenate([rec["lchnk"] for rec in records])
    col = np.concatenate([rec["col"] for rec in records])
    lat = np.concatenate([rec["lat"] for rec in records])
    lon = np.concatenate([rec["lon"] for rec in records])
    ps = np.concatenate([rec["ps"] for rec in records])
    profile = np.concatenate([rec["profile"] for rec in records], axis=1)
    qprof = np.concatenate([rec["qprof"] for rec in records], axis=1)

    good_cid = cid >= 0
    if np.any(good_cid):
        order = np.argsort(np.where(good_cid, cid, np.iinfo(np.int32).max))
    else:
        order = np.arange(cid.size)

    header0 = records[0]["header"]
    nsteps = sorted({rec["header"]["nstep"] for rec in records})
    packets = sorted({rec["header"]["packet"] for rec in records})
    ranks = sorted({rec["header"]["rank"] for rec in records})

    np.savez_compressed(
        str(out_path),
        cid=cid[order],
        lchnk=lchnk[order],
        col=col[order],
        lat_deg=lat[order],
        lon_deg=lon[order],
        ps_pa=ps[order],
        profile=profile[:, order, :],
        qprof=qprof[:, order, :],
        profile_names=np.array(PROFILE_NAMES),
        species=np.array(SPECIES),
        species_indices=np.array(header0["species_indices"], dtype=np.int32),
        nsteps=np.array(nsteps, dtype=np.int32),
        packets=np.array(packets, dtype=np.int32),
        ranks=np.array(ranks, dtype=np.int32),
        dtime_phys_s=np.array([header0["dtime_phys_s"]], dtype=np.float64),
    )

    unique_cid = int(np.unique(cid[good_cid]).size) if np.any(good_cid) else 0
    return {
        "out": str(out_path),
        "columns": int(cid.size),
        "unique_cid": unique_cid,
        "missing_cid": int(np.count_nonzero(~good_cid)),
        "rank_count": len(ranks),
        "packets": packets,
        "nsteps": nsteps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pattern", help="Glob pattern, e.g. /path/wxsami3_rank*_pkt000000.bin")
    parser.add_argument("--json", action="store_true", help="Print full JSON summary")
    parser.add_argument("--merged-npz", help="Write merged global snapshot NPZ sorted by cid")
    args = parser.parse_args()

    files = sorted(Path(p) for p in glob.glob(args.pattern))
    summary = summarize(files)
    if args.merged_npz:
        merged = write_merged_npz(files, Path(args.merged_npz))
        summary["merged_npz"] = merged
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"files={summary['file_count']} ranks={summary['rank_count']} total_cols={summary['total_cols']}")
        print(f"packets={summary['packets']} nsteps={summary['nsteps']}")
        print(f"lat_deg={summary['lat_deg']} lon_deg={summary['lon_deg']}")
        print(f"cid={summary['cid']}")
        for name in ["T_K", "U_m_s", "V_m_s", "PMID_Pa", "ZM_m", "MBARV_kg_mol"]:
            print(f"{name}={summary['profile'][name]}")
        for name in SPECIES:
            print(f"q_{name}={summary['q'][name]}")
        if "merged_npz" in summary:
            print(f"merged_npz={summary['merged_npz']}")
        if summary["bad_size_files"]:
            print(f"bad_size_files={summary['bad_size_files']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
