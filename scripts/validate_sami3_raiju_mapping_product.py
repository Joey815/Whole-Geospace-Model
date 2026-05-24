#!/usr/bin/env python3
"""Validate SAMI3 -> RAIJU stage-2 mapping-quality datasets."""

import argparse
import json
from pathlib import Path

import h5py
import numpy as np


MOMENT_FIELDS = ["Pavg", "Davg", "Pstd", "Dstd"]


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def fraction(mask):
    arr = np.asarray(mask).astype(bool)
    if arr.size == 0:
        return 0.0
    return float(np.count_nonzero(arr) / arr.size)


def finite_count(data):
    arr = np.asarray(data)
    return int(np.count_nonzero(np.isfinite(arr)))


def monotonic_non_decreasing(values):
    arr = np.asarray(values, dtype=np.float64)
    return bool(np.all(np.diff(arr) >= -1.0e-6))


def in_range(values, lower, upper):
    arr = np.asarray(values, dtype=np.float64)
    return bool(np.all((arr >= lower) & (arr <= upper)))


def validate(args):
    path = Path(args.product_h5).expanduser().resolve()
    checks = []
    meta = {"product_h5": str(path)}
    add(checks, "product_exists", path.is_file(), path)
    if not path.is_file():
        return checks, meta

    with h5py.File(str(path), "r") as h5:
        add(checks, "raicpl_group_exists", "RaiCplMomentsOnly" in h5, "RaiCplMomentsOnly")
        add(checks, "mapping_quality_group_exists", "MappingQuality" in h5, "MappingQuality")
        if "RaiCplMomentsOnly" not in h5 or "MappingQuality" not in h5:
            return checks, meta

        moments = h5["RaiCplMomentsOnly"]
        quality = h5["MappingQuality"]
        meta["root_attrs"] = {key: str(value) for key, value in h5.attrs.items()}
        meta["mapping_attrs"] = {key: str(value) for key, value in quality.attrs.items()}
        mapping_mode = str(quality.attrs.get("mapping_mode", ""))
        if args.expect_mapping_mode:
            add(
                checks,
                "mapping_mode",
                mapping_mode == args.expect_mapping_mode,
                "actual={} expected={}".format(mapping_mode, args.expect_mapping_mode),
            )

        shape2 = None
        for field in MOMENT_FIELDS:
            add(checks, field + "_exists", field in moments, field)
            add(checks, field + "_mask_exists", field + "_mask" in moments, field + "_mask")
            if field not in moments or field + "_mask" not in moments:
                continue
            data = moments[field][...]
            mask = moments[field + "_mask"][...].astype(bool)
            add(checks, field + "_finite", finite_count(data) == data.size, "nonfinite={}".format(data.size - finite_count(data)))
            add(checks, field + "_mask_shape", data.shape == mask.shape, "{} vs {}".format(data.shape, mask.shape))
            if shape2 is None:
                shape2 = data.shape[-2:]
            add(checks, field + "_runtime_shape", data.shape[-2:] == shape2, "{} expected suffix {}".format(data.shape, shape2))

        add(checks, "tiote_exists", "tiote" in moments, "tiote")
        add(checks, "tiote_mask_exists", "tiote_mask" in moments, "tiote_mask")
        if "tiote" in moments and "tiote_mask" in moments:
            tiote = moments["tiote"][...]
            tiote_mask = moments["tiote_mask"][...].astype(bool)
            add(checks, "tiote_finite", finite_count(tiote) == tiote.size, "nonfinite={}".format(tiote.size - finite_count(tiote)))
            add(checks, "tiote_mask_shape", tiote.shape == tiote_mask.shape, "{} vs {}".format(tiote.shape, tiote_mask.shape))

        if "finite_all_moments_runtime_mask" in quality:
            finite_all = quality["finite_all_moments_runtime_mask"][...].astype(bool)
            finite_fraction = fraction(finite_all)
            meta["finite_all_fraction"] = finite_fraction
            add(
                checks,
                "finite_all_fraction",
                finite_fraction >= args.min_finite_all_fraction,
                "fraction={} min={}".format(finite_fraction, args.min_finite_all_fraction),
            )
        else:
            add(checks, "finite_all_moments_runtime_mask_exists", False, "missing")

        if "runtime_valid_mask" in quality:
            valid = quality["runtime_valid_mask"][...].astype(bool)
        elif "finite_all_moments_runtime_mask" in quality:
            valid = quality["finite_all_moments_runtime_mask"][...].astype(bool)
        else:
            valid = None
        if valid is not None:
            valid_fraction = fraction(valid)
            meta["runtime_valid_fraction"] = valid_fraction
            add(
                checks,
                "runtime_valid_fraction",
                valid_fraction >= args.min_valid_fraction,
                "fraction={} min={}".format(valid_fraction, args.min_valid_fraction),
            )

        if "extrapolation_flag_runtime_mask" in quality:
            extrap = quality["extrapolation_flag_runtime_mask"][...].astype(bool)
        elif "l_extrapolated_runtime_mask" in quality:
            extrap = quality["l_extrapolated_runtime_mask"][...].astype(bool)
        else:
            extrap = None
        if extrap is not None:
            extrap_fraction = fraction(extrap)
            meta["extrapolated_fraction"] = extrap_fraction
            add(
                checks,
                "extrapolated_fraction",
                extrap_fraction <= args.max_extrapolated_fraction,
                "fraction={} max={}".format(extrap_fraction, args.max_extrapolated_fraction),
            )

        if "coverage_count_runtime" in quality:
            cov = quality["coverage_count_runtime"][...]
            meta["coverage_count_min"] = int(np.min(cov))
            meta["coverage_count_max"] = int(np.max(cov))
            add(checks, "coverage_count_nonnegative", bool(np.all(cov >= 0)), "min={}".format(np.min(cov)))
            if valid is not None:
                add(checks, "coverage_valid_positive", bool(np.all(cov[valid] > 0)), "valid_min={}".format(np.min(cov[valid]) if np.any(valid) else None))

        if "weight_sum_runtime" in quality:
            weight_sum = quality["weight_sum_runtime"][...]
            if valid is not None and np.any(valid):
                valid_weights = weight_sum[valid]
                max_dev = float(np.max(np.abs(valid_weights - 1.0)))
                meta["weight_sum_valid_max_deviation"] = max_dev
                add(checks, "weight_sum_valid_near_one", max_dev <= args.weight_sum_tol, "max_dev={} tol={}".format(max_dev, args.weight_sum_tol))

        for coord in ["source_l", "target_l", "source_mlt_deg", "target_mlt_deg"]:
            if coord in quality:
                values = quality[coord][...]
                add(checks, coord + "_finite", finite_count(values) == values.size, "nonfinite={}".format(values.size - finite_count(values)))
                min_value = float(np.min(values))
                max_value = float(np.max(values))
                if coord.endswith("_l"):
                    add(checks, coord + "_positive", bool(np.all(values > 0.0)), "min={} max={}".format(min_value, max_value))
                else:
                    add(checks, coord + "_range", in_range(values, 0.0, 360.0), "min={} max={}".format(min_value, max_value))

                require_monotonic = coord.startswith("source_") or args.require_target_monotonic
                if require_monotonic:
                    add(checks, coord + "_monotonic", monotonic_non_decreasing(values), "min={} max={}".format(min_value, max_value))

    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-h5", required=True)
    parser.add_argument("--expect-mapping-mode", default=None)
    parser.add_argument("--min-valid-fraction", type=float, default=0.0)
    parser.add_argument("--min-finite-all-fraction", type=float, default=1.0)
    parser.add_argument("--max-extrapolated-fraction", type=float, default=0.0)
    parser.add_argument("--weight-sum-tol", type=float, default=5.0e-6)
    parser.add_argument("--require-target-monotonic", action="store_true")
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
