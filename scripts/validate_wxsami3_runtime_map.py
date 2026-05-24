#!/usr/bin/env python3
"""Validate a WACCM-X -> SAMI3 live runtime-map binary against ESMF weights."""

import argparse
import json
from pathlib import Path

import numpy as np

try:
    from netCDF4 import Dataset
except ImportError:  # pragma: no cover - dependency is environment-provided
    Dataset = None


MAP_MAGIC = 20260524


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def read_weight_dims(path):
    if Dataset is None:
        raise RuntimeError("netCDF4 is required; use the mage-vis Python environment")
    with Dataset(str(path)) as ds:
        return {
            "n_a": len(ds.dimensions["n_a"]),
            "n_b": len(ds.dimensions["n_b"]),
            "n_s": len(ds.dimensions["n_s"]),
        }


def validate(args):
    map_path = Path(args.runtime_map).expanduser().resolve()
    weights_path = Path(args.weights_nc).expanduser().resolve() if args.weights_nc else None
    checks = []
    meta = {"runtime_map": str(map_path), "weights_nc": str(weights_path) if weights_path else None}

    add(checks, "runtime_map_exists", map_path.is_file(), map_path)
    if not map_path.is_file():
        return checks, meta

    expected_size_min = 8 * 4
    add(checks, "runtime_map_not_empty", map_path.stat().st_size >= expected_size_min, "bytes={}".format(map_path.stat().st_size))
    if map_path.stat().st_size < expected_size_min:
        return checks, meta

    with map_path.open("rb") as fp:
        header = np.fromfile(fp, dtype="<i4", count=8)
        if header.size != 8:
            add(checks, "runtime_map_header_read", False, "size={}".format(header.size))
            return checks, meta
        magic, version, nz, nf, nlt, npoints, n_s, nsource = [int(value) for value in header]
        meta["header"] = {
            "magic": magic,
            "version": version,
            "nz": nz,
            "nf": nf,
            "nlt": nlt,
            "npoints": npoints,
            "n_s": n_s,
            "nsource": nsource,
        }
        add(checks, "header_magic", magic == MAP_MAGIC, magic)
        add(checks, "header_version", version == 1, version)
        add(checks, "header_npoints", npoints == nz * nf * nlt, "npoints={} nz*nf*nlt={}".format(npoints, nz * nf * nlt))
        if args.expected_nsource is not None:
            add(checks, "header_expected_nsource", nsource == args.expected_nsource, "nsource={} expected={}".format(nsource, args.expected_nsource))

        expected_size = 8 * 4 + npoints * 4 + npoints * 4 + npoints * 4 + n_s * 4 + n_s * 8
        meta["expected_bytes"] = int(expected_size)
        meta["actual_bytes"] = map_path.stat().st_size
        add(checks, "runtime_map_size", map_path.stat().st_size == expected_size, "actual={} expected={}".format(map_path.stat().st_size, expected_size))

        zalt = np.fromfile(fp, dtype="<f4", count=npoints)
        row_start = np.fromfile(fp, dtype="<i4", count=npoints)
        row_count = np.fromfile(fp, dtype="<i4", count=npoints)
        col = np.fromfile(fp, dtype="<i4", count=n_s)
        weights = np.fromfile(fp, dtype="<f8", count=n_s)

    add(checks, "zalt_count", zalt.size == npoints, "got={} expected={}".format(zalt.size, npoints))
    add(checks, "row_start_count", row_start.size == npoints, "got={} expected={}".format(row_start.size, npoints))
    add(checks, "row_count_count", row_count.size == npoints, "got={} expected={}".format(row_count.size, npoints))
    add(checks, "col_count", col.size == n_s, "got={} expected={}".format(col.size, n_s))
    add(checks, "weight_count", weights.size == n_s, "got={} expected={}".format(weights.size, n_s))

    if zalt.size == npoints:
        meta["zalt_min"] = float(np.nanmin(zalt))
        meta["zalt_max"] = float(np.nanmax(zalt))
        add(checks, "zalt_finite", bool(np.isfinite(zalt).all()), "min={} max={}".format(meta["zalt_min"], meta["zalt_max"]))

    if row_start.size == npoints and row_count.size == npoints:
        covered = row_count > 0
        meta["covered_rows"] = int(np.count_nonzero(covered))
        meta["row_count_sum"] = int(row_count.sum(dtype=np.int64))
        add(checks, "row_count_nonnegative", bool((row_count >= 0).all()), "min={}".format(int(row_count.min())))
        add(checks, "row_count_sum", int(row_count.sum(dtype=np.int64)) == n_s, "sum={} n_s={}".format(int(row_count.sum(dtype=np.int64)), n_s))
        if np.any(covered):
            starts = row_start[covered]
            counts = row_count[covered]
            ends = starts + counts - 1
            add(checks, "row_start_positive_for_covered", bool((starts >= 1).all()), "min={}".format(int(starts.min())))
            add(checks, "row_end_within_ns", bool((ends <= n_s).all()), "max_end={} n_s={}".format(int(ends.max()), n_s))
            add(checks, "row_start_zero_for_uncovered", bool((row_start[~covered] == 0).all()), "uncovered={}".format(int(np.count_nonzero(~covered))))

    if col.size == n_s:
        meta["col_min"] = int(col.min()) if col.size else None
        meta["col_max"] = int(col.max()) if col.size else None
        add(checks, "col_source_range", bool(((col >= 1) & (col <= nsource)).all()), "min={} max={} nsource={}".format(meta["col_min"], meta["col_max"], nsource))

    if weights.size == n_s:
        meta["weight_min"] = float(np.nanmin(weights)) if weights.size else None
        meta["weight_max"] = float(np.nanmax(weights)) if weights.size else None
        add(checks, "weights_finite", bool(np.isfinite(weights).all()), "min={} max={}".format(meta["weight_min"], meta["weight_max"]))

    if weights_path:
        add(checks, "weights_nc_exists", weights_path.is_file(), weights_path)
        if weights_path.is_file():
            dims = read_weight_dims(weights_path)
            meta["weights_dims"] = dims
            add(checks, "weights_dim_n_a_matches_nsource", dims["n_a"] == nsource, "n_a={} nsource={}".format(dims["n_a"], nsource))
            add(checks, "weights_dim_n_b_matches_npoints", dims["n_b"] == npoints, "n_b={} npoints={}".format(dims["n_b"], npoints))
            add(checks, "weights_dim_n_s_matches_ns", dims["n_s"] == n_s, "dim_n_s={} header_n_s={}".format(dims["n_s"], n_s))

    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-map", required=True)
    parser.add_argument("--weights-nc", default=None)
    parser.add_argument("--expected-nsource", type=int, default=None)
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
