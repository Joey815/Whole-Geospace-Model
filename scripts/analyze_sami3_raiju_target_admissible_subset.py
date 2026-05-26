#!/usr/bin/env python3
"""Analyze the Voltron source subset inside the current RAIJU target L range."""

import argparse
import json
import math
from pathlib import Path

import h5py
import numpy as np


STATUS_LABELS = {
    0: "used",
    1: "bad_bvol",
    2: "bad_geometry",
    3: "large_footprint",
    4: "outside_target",
    5: "no_terms",
}


def finite_float(value):
    value = float(value)
    return value if math.isfinite(value) else None


def weighted_quantile(values, weights, quantiles):
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    if values.size == 0 or np.sum(weights) <= 0.0:
        return {str(q): None for q in quantiles}
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    cumulative = np.cumsum(sorted_weights, dtype=np.float64)
    total = float(cumulative[-1])
    result = {}
    for q in quantiles:
        idx = int(np.searchsorted(cumulative, float(q) * total, side="left"))
        idx = min(max(idx, 0), sorted_values.size - 1)
        result[str(q)] = float(sorted_values[idx])
    return result


def weighted_circular_mean_deg(deg, weights):
    deg = np.asarray(deg, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    total = float(np.sum(weights))
    if deg.size == 0 or total <= 0.0:
        return None
    radians = np.deg2rad(np.mod(deg, 360.0))
    sin_mean = float(np.sum(np.sin(radians) * weights) / total)
    cos_mean = float(np.sum(np.cos(radians) * weights) / total)
    return float(np.mod(np.rad2deg(np.arctan2(sin_mean, cos_mean)), 360.0))


def summarize_subset(name, mask, bvol, lb, lon, status, term_count, mapped_fraction, total_bvol):
    count = int(np.count_nonzero(mask))
    bsum = float(np.nansum(bvol[mask]))
    status_rows = []
    for code, label in STATUS_LABELS.items():
        code_mask = mask & (status == code)
        code_bsum = float(np.nansum(bvol[code_mask]))
        status_rows.append(
            {
                "code": int(code),
                "label": label,
                "count": int(np.count_nonzero(code_mask)),
                "bvol_sum": code_bsum,
                "fraction_of_subset_bvol": code_bsum / bsum if bsum > 0.0 else None,
                "fraction_of_total_positive_bvol": code_bsum / total_bvol if total_bvol > 0.0 else None,
            }
        )
    if count:
        lb_values = lb[mask]
        lon_values = lon[mask]
        b_values = bvol[mask]
        return {
            "name": name,
            "count": count,
            "fraction_of_positive_cells": None,
            "bvol_sum": bsum,
            "fraction_of_total_positive_bvol": bsum / total_bvol if total_bvol > 0.0 else None,
            "Lb_min": finite_float(np.nanmin(lb_values)),
            "Lb_max": finite_float(np.nanmax(lb_values)),
            "Lb_weighted_mean": finite_float(np.nansum(lb_values * b_values) / bsum) if bsum > 0.0 else None,
            "Lb_weighted_quantiles": weighted_quantile(lb_values, b_values, [0.1, 0.5, 0.9]),
            "lon_min_deg": finite_float(np.nanmin(np.mod(lon_values, 360.0))),
            "lon_max_deg": finite_float(np.nanmax(np.mod(lon_values, 360.0))),
            "lon_weighted_circular_mean_deg": weighted_circular_mean_deg(lon_values, b_values),
            "term_count_min": int(np.nanmin(term_count[mask])),
            "term_count_max": int(np.nanmax(term_count[mask])),
            "mapped_fraction_min": finite_float(np.nanmin(mapped_fraction[mask])),
            "mapped_fraction_max": finite_float(np.nanmax(mapped_fraction[mask])),
            "status": status_rows,
        }
    return {
        "name": name,
        "count": 0,
        "fraction_of_positive_cells": None,
        "bvol_sum": 0.0,
        "fraction_of_total_positive_bvol": 0.0,
        "status": status_rows,
    }


def mlt_histogram(mask, bvol, lon, bins):
    lon_values = np.mod(lon[mask], 360.0)
    b_values = bvol[mask]
    if lon_values.size == 0:
        return []
    edges = np.linspace(0.0, 360.0, bins + 1)
    total = float(np.nansum(b_values))
    rows = []
    for i in range(bins):
        if i == bins - 1:
            item = (lon_values >= edges[i]) & (lon_values <= edges[i + 1])
        else:
            item = (lon_values >= edges[i]) & (lon_values < edges[i + 1])
        bsum = float(np.nansum(b_values[item]))
        rows.append(
            {
                "bin": int(i),
                "lon_min_deg": float(edges[i]),
                "lon_max_deg": float(edges[i + 1]),
                "count": int(np.count_nonzero(item)),
                "bvol_sum": bsum,
                "fraction_of_subset_bvol": bsum / total if total > 0.0 else None,
            }
        )
    return rows


def top_cells(mask, bvol, lb, lon, status, term_count, mapped_fraction, top_n):
    indices = np.argwhere(mask)
    if indices.size == 0:
        return []
    values = bvol[mask]
    order = np.argsort(values)[::-1][:top_n]
    rows = []
    for idx in order:
        j, i = indices[idx]
        code = int(status[j, i])
        rows.append(
            {
                "source_i": int(i + 1),
                "source_j": int(j + 1),
                "bvol_active": float(bvol[j, i]),
                "Lb_cc": float(lb[j, i]),
                "lon_deg": float(np.mod(lon[j, i], 360.0)),
                "status_code": code,
                "status_label": STATUS_LABELS.get(code, "unknown"),
                "term_count": int(term_count[j, i]),
                "mapped_fraction": float(mapped_fraction[j, i]),
            }
        )
    return rows


def analyze(args):
    audit_h5 = Path(args.audit_h5).expanduser().resolve()
    weights_h5 = Path(args.weights_h5).expanduser().resolve()
    with h5py.File(str(weights_h5), "r") as handle:
        l_edge = np.asarray(handle[args.target_l_edge_dataset][()], dtype=np.float64)
    target_lmin = float(np.nanmin(l_edge))
    target_lmax = float(np.nanmax(l_edge))

    with h5py.File(str(audit_h5), "r") as handle:
        source = handle["source"]
        lb = np.asarray(source[args.source_l_dataset][()], dtype=np.float64)
        lon = np.asarray(source[args.source_lon_dataset][()], dtype=np.float64)
        bvol = np.asarray(source[args.source_bvol_dataset][()], dtype=np.float64)
        status = np.asarray(source["status_code"][()], dtype=np.int16)
        term_count = np.asarray(source["term_count"][()], dtype=np.int32)
        mapped_fraction = np.asarray(source["mapped_fraction"][()], dtype=np.float64)

    shape = lb.shape
    for name, arr in (
        ("lon", lon),
        ("bvol", bvol),
        ("status", status),
        ("term_count", term_count),
        ("mapped_fraction", mapped_fraction),
    ):
        if arr.shape != shape:
            raise ValueError("{} shape {} does not match Lb shape {}".format(name, arr.shape, shape))

    positive = np.isfinite(lb) & np.isfinite(bvol) & (bvol > args.bvol_floor)
    inside = positive & (lb >= target_lmin) & (lb <= target_lmax)
    below = positive & (lb < target_lmin)
    above = positive & (lb > target_lmax)
    total_bvol = float(np.nansum(bvol[positive]))

    subsets = {}
    for name, mask in (
        ("positive_all", positive),
        ("target_admissible_lrange", inside),
        ("below_target_lrange", below),
        ("above_target_lrange", above),
        ("target_admissible_used", inside & (status == 0)),
    ):
        item = summarize_subset(name, mask, bvol, lb, lon, status, term_count, mapped_fraction, total_bvol)
        item["fraction_of_positive_cells"] = (
            float(item["count"] / np.count_nonzero(positive)) if np.count_nonzero(positive) else None
        )
        subsets[name] = item

    result = {
        "product": "sami3_raiju_target_admissible_source_subset",
        "audit_h5": str(audit_h5),
        "weights_h5": str(weights_h5),
        "source_l_dataset": args.source_l_dataset,
        "source_lon_dataset": args.source_lon_dataset,
        "source_bvol_dataset": args.source_bvol_dataset,
        "target_l_edge_dataset": args.target_l_edge_dataset,
        "target_L_edge_min": target_lmin,
        "target_L_edge_max": target_lmax,
        "positive_source_cell_count": int(np.count_nonzero(positive)),
        "positive_source_bvol_sum": total_bvol,
        "subsets": subsets,
        "target_admissible_mlt_histogram": mlt_histogram(inside, bvol, lon, args.mlt_bins),
        "top_target_admissible_by_bvol": top_cells(
            inside, bvol, lb, lon, status, term_count, mapped_fraction, args.top_n
        ),
        "top_above_target_by_bvol": top_cells(
            above, bvol, lb, lon, status, term_count, mapped_fraction, args.top_n
        ),
        "interpretation": {
            "diagnostic_only_if_target_admissible_fraction_below": args.min_admissible_bvol_fraction,
            "target_admissible_bvol_fraction": subsets["target_admissible_lrange"][
                "fraction_of_total_positive_bvol"
            ],
            "target_admissible_is_representative": bool(
                subsets["target_admissible_lrange"]["fraction_of_total_positive_bvol"]
                is not None
                and subsets["target_admissible_lrange"]["fraction_of_total_positive_bvol"]
                >= args.min_admissible_bvol_fraction
            ),
        },
    }
    return result


def render_text(result):
    lines = []
    lines.append("SAMI3 -> RAIJU target-admissible source subset")
    lines.append("audit_h5 {}".format(result["audit_h5"]))
    lines.append("weights_h5 {}".format(result["weights_h5"]))
    lines.append("target_L_edge_min {:.17g}".format(result["target_L_edge_min"]))
    lines.append("target_L_edge_max {:.17g}".format(result["target_L_edge_max"]))
    lines.append("positive_source_cell_count {}".format(result["positive_source_cell_count"]))
    lines.append("positive_source_bvol_sum {:.17g}".format(result["positive_source_bvol_sum"]))
    lines.append("")
    for name in (
        "target_admissible_lrange",
        "target_admissible_used",
        "above_target_lrange",
        "below_target_lrange",
    ):
        item = result["subsets"][name]
        lines.append("[{}]".format(name))
        for key in (
            "count",
            "fraction_of_positive_cells",
            "bvol_sum",
            "fraction_of_total_positive_bvol",
            "Lb_min",
            "Lb_max",
            "Lb_weighted_mean",
            "lon_weighted_circular_mean_deg",
            "term_count_min",
            "term_count_max",
            "mapped_fraction_min",
            "mapped_fraction_max",
        ):
            if key in item:
                lines.append("{}={}".format(key, item[key]))
        lines.append("status_code label count bvol_sum fraction_of_subset_bvol")
        for status in item["status"]:
            lines.append(
                "{code} {label} {count} {bvol_sum:.17g} {fraction_of_subset_bvol}".format(
                    **status
                )
            )
        lines.append("")
    lines.append("[target_admissible_mlt_histogram]")
    lines.append("bin lon_min lon_max count bvol_sum fraction_of_subset_bvol")
    for row in result["target_admissible_mlt_histogram"]:
        lines.append(
            "{bin} {lon_min_deg:.6g} {lon_max_deg:.6g} {count} {bvol_sum:.17g} {fraction_of_subset_bvol}".format(
                **row
            )
        )
    lines.append("")
    lines.append("[top_target_admissible_by_bvol]")
    for row in result["top_target_admissible_by_bvol"]:
        lines.append(
            "source_i={source_i} source_j={source_j} bvol_active={bvol_active:.9g} "
            "Lb_cc={Lb_cc:.9g} lon_deg={lon_deg:.9g} status={status_label} "
            "term_count={term_count} mapped_fraction={mapped_fraction:.9g}".format(**row)
        )
    lines.append("")
    interp = result["interpretation"]
    lines.append("[interpretation]")
    lines.append(
        "target_admissible_bvol_fraction={}".format(
            interp["target_admissible_bvol_fraction"]
        )
    )
    lines.append(
        "target_admissible_is_representative={}".format(
            interp["target_admissible_is_representative"]
        )
    )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-h5", required=True)
    parser.add_argument("--weights-h5", required=True)
    parser.add_argument("--source-l-dataset", default="Lb_cc")
    parser.add_argument("--source-lon-dataset", default="lon0_cc_deg")
    parser.add_argument("--source-bvol-dataset", default="bvol_active_cc")
    parser.add_argument("--target-l-edge-dataset", default="/dst/L_edge")
    parser.add_argument("--bvol-floor", type=float, default=0.0)
    parser.add_argument("--mlt-bins", type=int, default=24)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--min-admissible-bvol-fraction", type=float, default=0.05)
    parser.add_argument("--json-output", default=None)
    parser.add_argument("--text-output", default=None)
    args = parser.parse_args()

    result = analyze(args)
    text = render_text(result)
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.text_output:
        Path(args.text_output).write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
