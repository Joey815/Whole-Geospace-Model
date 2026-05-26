#!/usr/bin/env python3
"""Analyze SAMI3/Voltron source active-bVol coverage as a function of L."""

import argparse
import json
import math
from pathlib import Path

import h5py
import numpy as np


def finite_float(value):
    value = float(value)
    return value if math.isfinite(value) else None


def parse_float_list(raw):
    values = []
    for item in raw.split(","):
        item = item.strip()
        if item:
            values.append(float(item))
    return values


def weighted_quantile(values, weights, quantiles):
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    valid = np.isfinite(values) & np.isfinite(weights) & (weights > 0.0)
    values = values[valid]
    weights = weights[valid]
    if values.size == 0:
        return {str(q): None for q in quantiles}
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]
    cumulative = np.cumsum(weights, dtype=np.float64)
    total = float(cumulative[-1])
    result = {}
    for q in quantiles:
        idx = int(np.searchsorted(cumulative, float(q) * total, side="left"))
        idx = min(max(idx, 0), values.size - 1)
        result[str(q)] = float(values[idx])
    return result


def fraction_leq(values, weights, threshold):
    mask = values <= threshold
    total = float(np.sum(weights))
    bsum = float(np.sum(weights[mask]))
    return {
        "L_threshold": float(threshold),
        "count": int(np.count_nonzero(mask)),
        "bvol_sum": bsum,
        "fraction_of_positive_bvol": bsum / total if total > 0.0 else None,
    }


def histogram(values, weights, edges):
    rows = []
    total = float(np.sum(weights))
    for i in range(len(edges) - 1):
        lo = float(edges[i])
        hi = float(edges[i + 1])
        if i == len(edges) - 2:
            mask = (values >= lo) & (values <= hi)
        else:
            mask = (values >= lo) & (values < hi)
        bsum = float(np.sum(weights[mask]))
        rows.append(
            {
                "bin": int(i),
                "L_min": lo,
                "L_max": hi,
                "count": int(np.count_nonzero(mask)),
                "bvol_sum": bsum,
                "fraction_of_positive_bvol": bsum / total if total > 0.0 else None,
            }
        )
    return rows


def read_target_l_range(weights_h5, dataset):
    with h5py.File(str(weights_h5), "r") as handle:
        l_edge = np.asarray(handle[dataset][()], dtype=np.float64)
    return float(np.nanmin(l_edge)), float(np.nanmax(l_edge))


def read_source_arrays(audit_h5, l_dataset, bvol_dataset, status_dataset):
    with h5py.File(str(audit_h5), "r") as handle:
        source = handle["source"]
        lb = np.asarray(source[l_dataset][()], dtype=np.float64)
        bvol = np.asarray(source[bvol_dataset][()], dtype=np.float64)
        status = None
        if status_dataset in source:
            status = np.asarray(source[status_dataset][()], dtype=np.int16)
    if lb.shape != bvol.shape:
        raise ValueError("Lb shape {} does not match bVol shape {}".format(lb.shape, bvol.shape))
    if status is not None and status.shape != lb.shape:
        raise ValueError("status shape {} does not match Lb shape {}".format(status.shape, lb.shape))
    return lb, bvol, status


def analyze(args):
    audit_h5 = Path(args.audit_h5).expanduser().resolve()
    weights_h5 = Path(args.weights_h5).expanduser().resolve()
    target_lmin, target_lmax = read_target_l_range(weights_h5, args.target_l_edge_dataset)
    lb, bvol, status = read_source_arrays(
        audit_h5,
        args.source_l_dataset,
        args.source_bvol_dataset,
        args.source_status_dataset,
    )

    positive = np.isfinite(lb) & np.isfinite(bvol) & (bvol > args.bvol_floor)
    positive_count = int(np.count_nonzero(positive))
    lb_pos = lb[positive]
    bvol_pos = bvol[positive]
    total_bvol = float(np.sum(bvol_pos))

    within_target = (lb_pos >= target_lmin) & (lb_pos <= target_lmax)
    below_target = lb_pos < target_lmin
    above_target = lb_pos > target_lmax

    thresholds = sorted(set(parse_float_list(args.l_thresholds) + [target_lmin, target_lmax]))
    thresholds = [value for value in thresholds if math.isfinite(value)]
    quantiles = parse_float_list(args.quantiles)

    l_min = float(np.nanmin(lb_pos)) if positive_count else None
    l_max = float(np.nanmax(lb_pos)) if positive_count else None
    hist_edges = parse_float_list(args.hist_edges)
    if not hist_edges:
        hist_edges = [1, 2, 5, 10, 20, 33.163437477526358, 50, 100, 200, 300, 400, 500, 600]
    hist_edges = sorted(set(hist_edges + [target_lmin, target_lmax]))

    status_rows = []
    if status is not None:
        status_pos = status[positive]
        for code in sorted(set(int(x) for x in np.unique(status_pos))):
            mask = status_pos == code
            bsum = float(np.sum(bvol_pos[mask]))
            status_rows.append(
                {
                    "code": code,
                    "count": int(np.count_nonzero(mask)),
                    "bvol_sum": bsum,
                    "fraction_of_positive_bvol": bsum / total_bvol if total_bvol > 0.0 else None,
                }
            )

    within_bvol = float(np.sum(bvol_pos[within_target]))
    below_bvol = float(np.sum(bvol_pos[below_target]))
    above_bvol = float(np.sum(bvol_pos[above_target]))
    result = {
        "product": "sami3_raiju_source_l_coverage",
        "audit_h5": str(audit_h5),
        "weights_h5": str(weights_h5),
        "source_l_dataset": args.source_l_dataset,
        "source_bvol_dataset": args.source_bvol_dataset,
        "target_l_edge_dataset": args.target_l_edge_dataset,
        "bvol_floor": args.bvol_floor,
        "target_L_edge_min": target_lmin,
        "target_L_edge_max": target_lmax,
        "positive_source_cell_count": positive_count,
        "positive_source_bvol_sum": total_bvol,
        "positive_source_L_min": l_min,
        "positive_source_L_max": l_max,
        "within_target_L": {
            "count": int(np.count_nonzero(within_target)),
            "bvol_sum": within_bvol,
            "fraction_of_positive_bvol": within_bvol / total_bvol if total_bvol > 0.0 else None,
        },
        "below_target_L": {
            "count": int(np.count_nonzero(below_target)),
            "bvol_sum": below_bvol,
            "fraction_of_positive_bvol": below_bvol / total_bvol if total_bvol > 0.0 else None,
        },
        "above_target_L": {
            "count": int(np.count_nonzero(above_target)),
            "bvol_sum": above_bvol,
            "fraction_of_positive_bvol": above_bvol / total_bvol if total_bvol > 0.0 else None,
        },
        "weighted_L_quantiles": weighted_quantile(lb_pos, bvol_pos, quantiles),
        "coverage_by_L_threshold": [fraction_leq(lb_pos, bvol_pos, value) for value in thresholds],
        "L_histogram": histogram(lb_pos, bvol_pos, hist_edges),
        "status_breakdown": status_rows,
        "production_assessment": {
            "min_target_bvol_fraction": args.min_target_bvol_fraction,
            "current_target_bvol_fraction": within_bvol / total_bvol if total_bvol > 0.0 else None,
            "current_target_meets_min_fraction": bool(
                total_bvol > 0.0 and within_bvol / total_bvol >= args.min_target_bvol_fraction
            ),
            "L_required_for_min_fraction": weighted_quantile(
                lb_pos, bvol_pos, [args.min_target_bvol_fraction]
            )[str(args.min_target_bvol_fraction)],
        },
    }
    return result


def render_text(result):
    lines = []
    lines.append("SAMI3 -> RAIJU source L coverage")
    lines.append("audit_h5 {}".format(result["audit_h5"]))
    lines.append("weights_h5 {}".format(result["weights_h5"]))
    lines.append("target_L_edge_min {:.17g}".format(result["target_L_edge_min"]))
    lines.append("target_L_edge_max {:.17g}".format(result["target_L_edge_max"]))
    lines.append("positive_source_cell_count {}".format(result["positive_source_cell_count"]))
    lines.append("positive_source_bvol_sum {:.17g}".format(result["positive_source_bvol_sum"]))
    lines.append("positive_source_L_min {}".format(result["positive_source_L_min"]))
    lines.append("positive_source_L_max {}".format(result["positive_source_L_max"]))
    lines.append("")
    for name in ("within_target_L", "below_target_L", "above_target_L"):
        item = result[name]
        lines.append("[{}]".format(name))
        lines.append("count={}".format(item["count"]))
        lines.append("bvol_sum={:.17g}".format(item["bvol_sum"]))
        lines.append("fraction_of_positive_bvol={}".format(item["fraction_of_positive_bvol"]))
        lines.append("")
    lines.append("[weighted_L_quantiles]")
    for key, value in result["weighted_L_quantiles"].items():
        lines.append("{}={}".format(key, value))
    lines.append("")
    lines.append("[coverage_by_L_threshold]")
    lines.append("L_threshold count bvol_sum fraction_of_positive_bvol")
    for row in result["coverage_by_L_threshold"]:
        lines.append(
            "{L_threshold:.17g} {count} {bvol_sum:.17g} {fraction_of_positive_bvol}".format(**row)
        )
    lines.append("")
    lines.append("[L_histogram]")
    lines.append("L_min L_max count bvol_sum fraction_of_positive_bvol")
    for row in result["L_histogram"]:
        lines.append(
            "{L_min:.17g} {L_max:.17g} {count} {bvol_sum:.17g} {fraction_of_positive_bvol}".format(
                **row
            )
        )
    if result["status_breakdown"]:
        lines.append("")
        lines.append("[status_breakdown]")
        lines.append("code count bvol_sum fraction_of_positive_bvol")
        for row in result["status_breakdown"]:
            lines.append(
                "{code} {count} {bvol_sum:.17g} {fraction_of_positive_bvol}".format(**row)
            )
    assess = result["production_assessment"]
    lines.append("")
    lines.append("[production_assessment]")
    lines.append("min_target_bvol_fraction={}".format(assess["min_target_bvol_fraction"]))
    lines.append("current_target_bvol_fraction={}".format(assess["current_target_bvol_fraction"]))
    lines.append("current_target_meets_min_fraction={}".format(assess["current_target_meets_min_fraction"]))
    lines.append("L_required_for_min_fraction={}".format(assess["L_required_for_min_fraction"]))
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-h5", required=True)
    parser.add_argument("--weights-h5", required=True)
    parser.add_argument("--source-l-dataset", default="Lb_cc")
    parser.add_argument("--source-bvol-dataset", default="bvol_active_cc")
    parser.add_argument("--source-status-dataset", default="status_code")
    parser.add_argument("--target-l-edge-dataset", default="/dst/L_edge")
    parser.add_argument("--bvol-floor", type=float, default=0.0)
    parser.add_argument("--min-target-bvol-fraction", type=float, default=0.05)
    parser.add_argument(
        "--quantiles",
        default="0.001,0.01,0.05,0.1,0.5,0.9,0.95,0.99",
        help="Comma-separated active-bVol weighted L quantiles.",
    )
    parser.add_argument(
        "--l-thresholds",
        default="2,5,10,20,33.163437477526358,50,75,100,150,200,250,300,350,400,450,500,550,600",
        help="Comma-separated L thresholds for cumulative active-bVol coverage.",
    )
    parser.add_argument(
        "--hist-edges",
        default="1,2,5,10,20,33.163437477526358,50,75,100,150,200,250,300,350,400,450,500,550,600",
        help="Comma-separated L histogram edges.",
    )
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
