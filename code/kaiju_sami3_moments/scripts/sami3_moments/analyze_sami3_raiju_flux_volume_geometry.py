#!/usr/bin/env python3
"""Audit Voltron TubeShell bVol overlap geometry in a SAMI3->RAIJU weight file."""

import argparse
import json
import os
import sys

import h5py
import numpy as np

from build_sami3_to_raiju_weights import (
    TINY,
    circular_mean_rad_1d,
    linear_bin_overlaps,
    periodic_bin_overlaps,
    require_moments_h5,
    unwrap_deg_near,
)
from sami3_moments_to_raiju_diag import output_paths


STATUS_USED = 0
STATUS_BAD_BVOL = 1
STATUS_BAD_GEOMETRY = 2
STATUS_LARGE_FOOTPRINT = 3
STATUS_OUTSIDE_TARGET = 4
STATUS_NO_TERMS = 5


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weight-file", required=True, help="SAMI3->RAIJU sparse mapping-weight HDF5 file.")
    parser.add_argument("--out", required=True, help="Output prefix or .h5 path for geometry audit.")
    parser.add_argument(
        "--voltron-tube-longitude",
        choices=("lon0", "lonc"),
        default=None,
        help="TubeShell corner longitude to audit. Defaults to weight-file metadata voltron_tube_longitude or lon0.",
    )
    parser.add_argument("--voltron-bvol-floor", type=float, default=0.0)
    parser.add_argument("--voltron-overlap-max-l-span", type=float, default=None)
    parser.add_argument("--voltron-overlap-max-lon-span", type=float, default=None)
    return parser.parse_args()


def decode_h5_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if hasattr(value, "tobytes"):
        return value.tobytes().decode("utf-8")
    return str(value)


def read_required(handle, name):
    if name not in handle:
        raise KeyError("missing required dataset /{0}".format(name))
    return handle[name][:]


def finite_summary(arr):
    values = np.asarray(arr)
    finite = np.isfinite(values)
    out = {
        "shape": list(values.shape),
        "finite_count": int(np.count_nonzero(finite)),
        "total_count": int(values.size),
        "nonfinite_count": int(values.size - np.count_nonzero(finite)),
    }
    if np.count_nonzero(finite):
        vals = values[finite].astype(np.float64, copy=False)
        out.update(
            {
                "min": float(np.min(vals)),
                "p01": float(np.percentile(vals, 1.0)),
                "p05": float(np.percentile(vals, 5.0)),
                "median": float(np.percentile(vals, 50.0)),
                "p95": float(np.percentile(vals, 95.0)),
                "p99": float(np.percentile(vals, 99.0)),
                "max": float(np.max(vals)),
                "mean": float(np.mean(vals)),
            }
        )
    else:
        out.update({"min": None, "p01": None, "p05": None, "median": None, "p95": None, "p99": None, "max": None, "mean": None})
    return out


def load_weight_geometry(path):
    h5py = require_moments_h5(path)
    with h5py.File(path, "r") as handle:
        metadata = {}
        if "metadata/json" in handle:
            metadata = json.loads(decode_h5_text(handle["metadata/json"][()]))
        data = {
            "metadata": metadata,
            "target_l_edge": read_required(handle, "dst/L_edge").astype(np.float64),
            "target_lon_edge": read_required(handle, "dst/MLT_edge_deg_unwrapped").astype(np.float64),
            "target_bvol_cc": read_required(handle, "dst/bvol_cc").astype(np.float64),
            "target_closed_mask": read_required(handle, "quality/closed_field_mask").astype(np.uint8),
            "stored_coverage_count": read_required(handle, "quality/coverage_count").astype(np.int32),
            "stored_weight_sum": read_required(handle, "quality/weight_sum").astype(np.float64),
            "stored_v2r_dst": read_required(handle, "intermediate/voltron_to_raiju/dst_index").astype(np.int32),
            "stored_v2r_src": read_required(handle, "intermediate/voltron_to_raiju/src_index").astype(np.int32),
            "stored_v2r_weight": read_required(handle, "intermediate/voltron_to_raiju/weight").astype(np.float64),
            "voltron_l_corner": read_required(handle, "intermediate/Lb_corner").astype(np.float64),
            "voltron_bvol_cc": read_required(handle, "intermediate/bvol_cc").astype(np.float64),
            "voltron_closed_mask": read_required(handle, "intermediate/closed_cell_mask").astype(np.uint8),
            "voltron_l_cc": read_required(handle, "intermediate/Lb_cc").astype(np.float64),
            "voltron_lon0_cc": read_required(handle, "intermediate/lon0_cc_deg").astype(np.float64),
            "voltron_lonc_cc": read_required(handle, "intermediate/lonc_cc_deg").astype(np.float64),
        }
        if "intermediate/lon0_corner_rad" not in handle or "intermediate/lonc_corner_rad" not in handle:
            raise KeyError(
                "weight file is missing TubeShell corner longitude datasets; regenerate with the updated writer"
            )
        data["voltron_lon0_corner"] = read_required(handle, "intermediate/lon0_corner_rad").astype(np.float64)
        data["voltron_lonc_corner"] = read_required(handle, "intermediate/lonc_corner_rad").astype(np.float64)
        for optional in ("intermediate/wMAG", "intermediate/Tb", "intermediate/nTrc_cc"):
            key = optional.split("/")[-1]
            data[key] = handle[optional][:].astype(np.float64) if optional in handle else None
    return data


def recompute_overlap(data, longitude_key, bvol_floor, max_l_span, max_lon_span):
    target_l_edge = data["target_l_edge"]
    target_lon_edge = data["target_lon_edge"]
    target_bvol = data["target_bvol_cc"]
    src_l_corner = data["voltron_l_corner"]
    src_lon_corner = data["voltron_{0}_corner".format(longitude_key)]
    src_bvol = data["voltron_bvol_cc"]
    l_low = np.minimum(target_l_edge[:-1], target_l_edge[1:])
    l_high = np.maximum(target_l_edge[:-1], target_l_edge[1:])
    nj, ni = target_bvol.shape

    raw_bvol_sum = np.zeros((nj, ni), dtype=np.float64)
    coverage_count = np.zeros((nj, ni), dtype=np.int32)
    source_mapped_fraction = np.zeros(src_bvol.shape, dtype=np.float64)
    source_status = np.full(src_bvol.shape, STATUS_NO_TERMS, dtype=np.int16)
    source_l_span = np.full(src_bvol.shape, np.nan, dtype=np.float64)
    source_lon_span = np.full(src_bvol.shape, np.nan, dtype=np.float64)
    source_terms = np.zeros(src_bvol.shape, dtype=np.int32)
    source_mapped_bvol = np.zeros(src_bvol.shape, dtype=np.float64)

    rows_dst = []
    rows_src = []
    rows_raw = []
    skipped = {
        "bad_bvol": 0,
        "bad_geometry": 0,
        "large_footprint": 0,
        "outside_target": 0,
        "no_terms": 0,
        "used": 0,
    }

    for jv in range(src_bvol.shape[0]):
        for iv in range(src_bvol.shape[1]):
            bvol = float(src_bvol[jv, iv])
            if (not np.isfinite(bvol)) or bvol <= bvol_floor:
                source_status[jv, iv] = STATUS_BAD_BVOL
                skipped["bad_bvol"] += 1
                continue
            l_corners = src_l_corner[jv : jv + 2, iv : iv + 2]
            lon_corners = src_lon_corner[jv : jv + 2, iv : iv + 2]
            if np.count_nonzero(np.isfinite(l_corners)) != 4 or np.count_nonzero(np.isfinite(lon_corners)) != 4:
                source_status[jv, iv] = STATUS_BAD_GEOMETRY
                skipped["bad_geometry"] += 1
                continue
            l_span = float(np.max(l_corners) - np.min(l_corners))
            source_l_span[jv, iv] = l_span
            lon_center_rad = circular_mean_rad_1d(lon_corners)
            lon_center_deg = float(np.mod(np.degrees(lon_center_rad), 360.0))
            lon_unwrapped = unwrap_deg_near(np.mod(np.degrees(lon_corners), 360.0), lon_center_deg)
            lon_span = float(np.max(lon_unwrapped) - np.min(lon_unwrapped))
            source_lon_span[jv, iv] = lon_span
            if lon_span > 180.0:
                source_status[jv, iv] = STATUS_BAD_GEOMETRY
                skipped["bad_geometry"] += 1
                continue
            if (max_l_span is not None and max_l_span > 0.0 and l_span > max_l_span) or (
                max_lon_span is not None and max_lon_span > 0.0 and lon_span > max_lon_span
            ):
                source_status[jv, iv] = STATUS_LARGE_FOOTPRINT
                skipped["large_footprint"] += 1
                continue
            l_overlaps = linear_bin_overlaps(float(np.min(l_corners)), float(np.max(l_corners)), l_low, l_high)
            lon_overlaps = periodic_bin_overlaps(float(np.min(lon_unwrapped)), float(np.max(lon_unwrapped)), target_lon_edge)
            if not l_overlaps or not lon_overlaps:
                source_status[jv, iv] = STATUS_OUTSIDE_TARGET
                skipped["outside_target"] += 1
                continue
            term_count = 0
            fraction_sum = 0.0
            for i, l_fraction in l_overlaps:
                for j, lon_fraction in lon_overlaps:
                    fraction = l_fraction * lon_fraction
                    if fraction <= 0.0:
                        continue
                    raw = bvol * fraction
                    raw_bvol_sum[j, i] += raw
                    coverage_count[j, i] += 1
                    rows_dst.append((j, i))
                    rows_src.append((jv, iv))
                    rows_raw.append(raw)
                    term_count += 1
                    fraction_sum += fraction
            if term_count == 0:
                source_status[jv, iv] = STATUS_NO_TERMS
                skipped["no_terms"] += 1
                continue
            source_status[jv, iv] = STATUS_USED
            source_terms[jv, iv] = term_count
            source_mapped_fraction[jv, iv] = fraction_sum
            source_mapped_bvol[jv, iv] = bvol * fraction_sum
            skipped["used"] += 1

    if not rows_raw:
        raise RuntimeError("recomputed overlap has no nonzero terms")
    dst = np.asarray(rows_dst, dtype=np.int32)
    src = np.asarray(rows_src, dtype=np.int32)
    raw = np.asarray(rows_raw, dtype=np.float64)
    norm = raw_bvol_sum[dst[:, 0], dst[:, 1]]
    normalized = raw / np.maximum(norm, TINY)
    normalized_sum = np.zeros((nj, ni), dtype=np.float64)
    np.add.at(normalized_sum, (dst[:, 0], dst[:, 1]), normalized)

    ratio = np.full((nj, ni), np.nan, dtype=np.float64)
    ratio_mask = (target_bvol > 0.0) & (raw_bvol_sum > 0.0) & np.isfinite(target_bvol)
    ratio[ratio_mask] = raw_bvol_sum[ratio_mask] / target_bvol[ratio_mask]

    return {
        "dst_index": dst,
        "src_index": src,
        "raw_weight": raw,
        "normalized_weight": normalized,
        "raw_bvol_sum": raw_bvol_sum,
        "coverage_count": coverage_count,
        "normalized_sum": normalized_sum,
        "raw_to_target_bvol_ratio": ratio,
        "source_mapped_fraction": source_mapped_fraction,
        "source_mapped_bvol": source_mapped_bvol,
        "source_status": source_status,
        "source_l_span": source_l_span,
        "source_lon_span": source_lon_span,
        "source_terms": source_terms,
        "skipped": skipped,
    }


def compare_stored_weights(data, audit):
    stored_dst = data["stored_v2r_dst"]
    stored_src = data["stored_v2r_src"]
    stored_weight = data["stored_v2r_weight"]
    recomputed = {}
    for dst, src, weight in zip(audit["dst_index"], audit["src_index"], audit["normalized_weight"]):
        recomputed[(int(dst[0]), int(dst[1]), int(src[0]), int(src[1]))] = float(weight)
    missing = 0
    diffs = []
    for dst, src, weight in zip(stored_dst, stored_src, stored_weight):
        key = (int(dst[0]), int(dst[1]), int(src[0]), int(src[1]))
        if key not in recomputed:
            missing += 1
            continue
        diffs.append(abs(float(weight) - recomputed[key]))
    extra = max(0, len(recomputed) - (stored_weight.size - missing))
    diffs = np.asarray(diffs, dtype=np.float64)
    return {
        "stored_count": int(stored_weight.size),
        "recomputed_count": int(audit["normalized_weight"].size),
        "missing_stored_terms": int(missing),
        "extra_recomputed_terms": int(extra),
        "max_abs_diff": float(np.max(diffs)) if diffs.size else None,
        "mean_abs_diff": float(np.mean(diffs)) if diffs.size else None,
    }


def build_summary(data, audit, weight_compare, args, longitude_key, out_h5):
    target_positive = audit["raw_bvol_sum"] > 0.0
    source_used = audit["source_status"] == STATUS_USED
    source_valid_bvol = np.isfinite(data["voltron_bvol_cc"]) & (data["voltron_bvol_cc"] > args.voltron_bvol_floor)
    mapped_bvol = np.sum(audit["source_mapped_bvol"][source_used])
    total_valid_bvol = np.sum(data["voltron_bvol_cc"][source_valid_bvol])
    mapped_fraction_values = audit["source_mapped_fraction"][source_used]
    ratio_values = audit["raw_to_target_bvol_ratio"][target_positive]
    return {
        "product": "sami3_raiju_flux_volume_geometry_audit",
        "weight_file": os.path.abspath(args.weight_file),
        "output_hdf5": os.path.abspath(out_h5),
        "voltron_tube_longitude": longitude_key,
        "voltron_bvol_floor": args.voltron_bvol_floor,
        "voltron_overlap_max_l_span": args.voltron_overlap_max_l_span,
        "voltron_overlap_max_lon_span": args.voltron_overlap_max_lon_span,
        "target_shape_j_i": list(audit["raw_bvol_sum"].shape),
        "source_shape_j_i": list(data["voltron_bvol_cc"].shape),
        "target_positive_count": int(np.count_nonzero(target_positive)),
        "target_zero_count": int(target_positive.size - np.count_nonzero(target_positive)),
        "target_positive_fraction": float(np.count_nonzero(target_positive) / float(target_positive.size)),
        "source_status_counts": {str(code): int(np.count_nonzero(audit["source_status"] == code)) for code in range(6)},
        "source_status_legend": {
            str(STATUS_USED): "used",
            str(STATUS_BAD_BVOL): "bad_bvol",
            str(STATUS_BAD_GEOMETRY): "bad_geometry",
            str(STATUS_LARGE_FOOTPRINT): "large_footprint",
            str(STATUS_OUTSIDE_TARGET): "outside_target",
            str(STATUS_NO_TERMS): "no_terms",
        },
        "skipped": audit["skipped"],
        "source_valid_bvol_sum": float(total_valid_bvol),
        "source_mapped_bvol_sum": float(mapped_bvol),
        "source_mapped_bvol_fraction_of_valid": float(mapped_bvol / total_valid_bvol) if total_valid_bvol > 0.0 else None,
        "mapped_fraction_stats": finite_summary(mapped_fraction_values),
        "source_l_span_stats_used": finite_summary(audit["source_l_span"][source_used]),
        "source_lon_span_stats_used": finite_summary(audit["source_lon_span"][source_used]),
        "source_terms_stats_used": finite_summary(audit["source_terms"][source_used]),
        "target_raw_bvol_sum_stats_positive": finite_summary(audit["raw_bvol_sum"][target_positive]),
        "target_raw_to_raiju_bvol_ratio_stats_positive": finite_summary(ratio_values),
        "target_bvol_cc_stats_positive": finite_summary(data["target_bvol_cc"][data["target_bvol_cc"] > 0.0]),
        "target_normalized_sum_stats_positive": finite_summary(audit["normalized_sum"][target_positive]),
        "weight_compare": weight_compare,
    }


def create_dataset(group, name, data, units, description):
    dset = group.create_dataset(name, data=data, compression="gzip", shuffle=True)
    dset.attrs["Units"] = units
    dset.attrs["Description"] = description
    return dset


def write_audit(path, summary, data, audit):
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with h5py.File(path, "w") as handle:
        handle.attrs["product"] = summary["product"]
        handle.attrs["weight_file"] = summary["weight_file"]
        handle.attrs["voltron_tube_longitude"] = summary["voltron_tube_longitude"]
        handle.attrs["status_code_0"] = "used"
        handle.attrs["status_code_1"] = "bad_bvol"
        handle.attrs["status_code_2"] = "bad_geometry"
        handle.attrs["status_code_3"] = "large_footprint"
        handle.attrs["status_code_4"] = "outside_target"
        handle.attrs["status_code_5"] = "no_terms"

        target = handle.create_group("target")
        create_dataset(target, "raw_bvol_sum", audit["raw_bvol_sum"].astype(np.float32), "Voltron bVol units", "Unnormalized source TubeShell bVol contribution sum by RAIJU target j,i.")
        create_dataset(target, "coverage_count", audit["coverage_count"].astype(np.int32), "count", "Number of source TubeShell overlap terms by RAIJU target j,i.")
        create_dataset(target, "normalized_sum", audit["normalized_sum"].astype(np.float32), "normalized", "Sum of recomputed normalized overlap weights by target j,i.")
        create_dataset(target, "raw_to_target_bvol_ratio", audit["raw_to_target_bvol_ratio"].astype(np.float32), "ratio", "Raw Voltron bVol contribution sum divided by RAIJU target bvol_cc where finite.")
        create_dataset(target, "raiju_bvol_cc", data["target_bvol_cc"].astype(np.float32), "RAIJU bVol units", "RAIJU target bvol_cc from the mapping file.")
        create_dataset(target, "closed_field_mask", data["target_closed_mask"].astype(np.uint8), "logical", "RAIJU closed-field mask from the mapping file.")

        source = handle.create_group("source")
        create_dataset(source, "status_code", audit["source_status"].astype(np.int16), "enum", "Source TubeShell cell audit status code.")
        create_dataset(source, "mapped_fraction", audit["source_mapped_fraction"].astype(np.float32), "fraction", "Sum of target-bin overlap fractions accepted for each source cell.")
        create_dataset(source, "mapped_bvol", audit["source_mapped_bvol"].astype(np.float32), "Voltron bVol units", "Source bVol multiplied by mapped_fraction.")
        create_dataset(source, "bvol_cc", data["voltron_bvol_cc"].astype(np.float32), "Voltron bVol units", "Voltron TubeShell cell-centered bVol.")
        create_dataset(source, "closed_cell_mask", data["voltron_closed_mask"].astype(np.uint8), "logical", "Voltron TubeShell closed-cell mask.")
        create_dataset(source, "l_span", audit["source_l_span"].astype(np.float32), "Re", "Source TubeShell corner Lb span.")
        create_dataset(source, "lon_span", audit["source_lon_span"].astype(np.float32), "degrees", "Source TubeShell corner longitude span after periodic unwrapping.")
        create_dataset(source, "term_count", audit["source_terms"].astype(np.int32), "count", "Number of target overlap terms for each source cell.")
        create_dataset(source, "Lb_cc", data["voltron_l_cc"].astype(np.float32), "Re", "Voltron TubeShell cell-centered Lb.")
        create_dataset(source, "lon0_cc_deg", data["voltron_lon0_cc"].astype(np.float32), "degrees", "Voltron TubeShell cell-centered lon0.")
        create_dataset(source, "lonc_cc_deg", data["voltron_lonc_cc"].astype(np.float32), "degrees", "Voltron TubeShell cell-centered lonc.")

        sparse = handle.create_group("sparse")
        create_dataset(sparse, "dst_index", audit["dst_index"], "index", "Recomputed sparse destination indices, columns are j,i.")
        create_dataset(sparse, "src_index", audit["src_index"], "index", "Recomputed sparse source indices, columns are j,i.")
        create_dataset(sparse, "raw_weight", audit["raw_weight"].astype(np.float32), "Voltron bVol units", "Raw source bVol overlap contribution before per-target normalization.")
        create_dataset(sparse, "normalized_weight", audit["normalized_weight"].astype(np.float32), "normalized", "Recomputed normalized source-to-target weight.")

        metadata = handle.create_group("metadata")
        metadata.create_dataset("json", data=json.dumps(summary, indent=2, sort_keys=True))


def main():
    args = parse_args()
    data = load_weight_geometry(os.path.abspath(args.weight_file))
    metadata = data["metadata"]
    longitude_key = args.voltron_tube_longitude or metadata.get("voltron_tube_longitude") or "lon0"
    max_l_span = args.voltron_overlap_max_l_span
    if max_l_span is None:
        max_l_span = metadata.get("voltron_overlap_max_l_span", 20.0)
    max_lon_span = args.voltron_overlap_max_lon_span
    if max_lon_span is None:
        max_lon_span = metadata.get("voltron_overlap_max_lon_span", 10.0)

    audit = recompute_overlap(data, longitude_key, args.voltron_bvol_floor, max_l_span, max_lon_span)
    weight_compare = compare_stored_weights(data, audit)
    out_h5, out_json = output_paths(args.out)
    summary = build_summary(data, audit, weight_compare, args, longitude_key, out_h5)
    write_audit(out_h5, summary, data, audit)
    with open(out_json, "w") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print("wrote {0}".format(out_h5))
    print("wrote {0}".format(out_json))
    print("target_positive_fraction={0}".format(summary["target_positive_fraction"]))
    print("source_mapped_bvol_fraction_of_valid={0}".format(summary["source_mapped_bvol_fraction_of_valid"]))
    print("weight_compare_max_abs_diff={0}".format(summary["weight_compare"]["max_abs_diff"]))
    print("source_status_counts={0}".format(summary["source_status_counts"]))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        sys.exit(1)
