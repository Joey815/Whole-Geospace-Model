#!/usr/bin/env python3
"""Scan Voltron source bVol coverage as a function of RAIJU target Lmax."""

import argparse
import json
import math
from pathlib import Path

import h5py
import numpy as np


DEFAULT_LMAX_VALUES = [
    33.16343747752636,
    50.0,
    100.0,
    150.0,
    200.0,
    250.0,
    300.0,
    350.0,
    400.0,
    450.0,
    500.0,
    553.7752075195312,
]

DEFAULT_QUANTILES = [
    0.001,
    0.005,
    0.01,
    0.05,
    0.10,
    0.25,
    0.50,
    0.75,
    0.90,
    0.95,
    0.99,
    0.999,
]


def parse_csv_floats(value):
    if value is None:
        return None
    out = []
    for item in value.split(","):
        text = item.strip()
        if text:
            out.append(float(text))
    return out


def dipole_lat_deg_from_l(l_value):
    if not math.isfinite(l_value) or l_value <= 1.0:
        return 90.0
    arg = min(1.0, 1.0 / math.sqrt(l_value))
    return math.degrees(math.asin(arg))


def weighted_quantile(sorted_values, sorted_weights, cumulative, total, quantile):
    if total <= 0.0:
        return None
    idx = int(np.searchsorted(cumulative, quantile * total, side="left"))
    idx = min(max(idx, 0), sorted_values.size - 1)
    l_value = float(sorted_values[idx])
    return {
        "quantile": float(quantile),
        "Lmax_required": l_value,
        "dipole_lat_deg": dipole_lat_deg_from_l(l_value),
        "included_fraction_at_Lmax": float(cumulative[idx] / total),
        "included_bvol_at_Lmax": float(cumulative[idx]),
        "source_count_at_Lmax": int(idx + 1),
    }


def load_target_lmax(weight_file, dataset):
    if weight_file is None:
        return None
    with h5py.File(str(weight_file), "r") as handle:
        if dataset not in handle:
            raise KeyError("missing target L-edge dataset {} in {}".format(dataset, weight_file))
        values = np.asarray(handle[dataset][()], dtype=np.float64)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return None
    return float(np.max(finite))


def choose_bvol_dataset(handle, mode):
    if mode == "active":
        return "source/bvol_active_cc"
    if mode == "raw":
        return "source/bvol_cc"
    if "source/bvol_active_cc" in handle:
        return "source/bvol_active_cc"
    return "source/bvol_cc"


def analyze(args):
    audit_h5 = Path(args.audit_h5).expanduser().resolve()
    weight_h5 = Path(args.weights_h5).expanduser().resolve() if args.weights_h5 else None
    lmax_values = parse_csv_floats(args.lmax_values) or list(DEFAULT_LMAX_VALUES)
    quantiles = parse_csv_floats(args.quantiles) or list(DEFAULT_QUANTILES)

    with h5py.File(str(audit_h5), "r") as handle:
        if args.source_l_dataset not in handle:
            raise KeyError("missing source L dataset {}".format(args.source_l_dataset))
        source_l = np.asarray(handle[args.source_l_dataset][()], dtype=np.float64)
        bvol_dataset = choose_bvol_dataset(handle, args.bvol_source)
        if bvol_dataset not in handle:
            raise KeyError("missing bVol dataset {}".format(bvol_dataset))
        source_bvol = np.asarray(handle[bvol_dataset][()], dtype=np.float64)

    if source_l.shape != source_bvol.shape:
        raise ValueError(
            "source L shape {} does not match bVol shape {}".format(source_l.shape, source_bvol.shape)
        )

    valid = np.isfinite(source_l) & np.isfinite(source_bvol) & (source_bvol > 0.0)
    l_valid = source_l[valid]
    b_valid = source_bvol[valid]
    if l_valid.size == 0:
        raise RuntimeError("no positive finite source bVol cells found")

    order = np.argsort(l_valid)
    l_sorted = l_valid[order]
    b_sorted = b_valid[order]
    cumulative = np.cumsum(b_sorted, dtype=np.float64)
    total = float(cumulative[-1])
    current_target_lmax = load_target_lmax(weight_h5, args.target_l_edge_dataset)
    if current_target_lmax is not None and current_target_lmax not in lmax_values:
        lmax_values = [current_target_lmax] + lmax_values

    threshold_rows = []
    for lmax in sorted(set(float(value) for value in lmax_values)):
        inside = l_valid <= lmax
        included_bvol = float(np.sum(b_valid[inside], dtype=np.float64))
        threshold_rows.append(
            {
                "Lmax": float(lmax),
                "dipole_lat_deg": dipole_lat_deg_from_l(float(lmax)),
                "included_bvol": included_bvol,
                "included_fraction": included_bvol / total,
                "excluded_fraction": 1.0 - included_bvol / total,
                "included_source_count": int(np.count_nonzero(inside)),
            }
        )

    quantile_rows = [
        weighted_quantile(l_sorted, b_sorted, cumulative, total, float(q)) for q in quantiles
    ]

    result = {
        "product": "sami3_raiju_source_domain_lscan",
        "audit_h5": str(audit_h5),
        "weights_h5": str(weight_h5) if weight_h5 else None,
        "source_l_dataset": args.source_l_dataset,
        "source_bvol_dataset": bvol_dataset,
        "target_l_edge_dataset": args.target_l_edge_dataset if weight_h5 else None,
        "current_target_Lmax": current_target_lmax,
        "current_target_dipole_lat_deg": (
            dipole_lat_deg_from_l(current_target_lmax) if current_target_lmax is not None else None
        ),
        "source_positive_cell_count": int(l_valid.size),
        "source_positive_bvol_sum": total,
        "source_L_min": float(np.min(l_valid)),
        "source_L_max": float(np.max(l_valid)),
        "source_L_bvol_weighted_mean": float(np.sum(l_valid * b_valid, dtype=np.float64) / total),
        "threshold_scan": threshold_rows,
        "required_Lmax_by_bvol_quantile": quantile_rows,
    }
    return result


def render_text(result):
    lines = []
    lines.append("SAMI3 -> RAIJU source-domain L scan")
    lines.append("audit_h5 {}".format(result["audit_h5"]))
    if result.get("weights_h5"):
        lines.append("weights_h5 {}".format(result["weights_h5"]))
    lines.append("source_l_dataset {}".format(result["source_l_dataset"]))
    lines.append("source_bvol_dataset {}".format(result["source_bvol_dataset"]))
    lines.append("source_positive_cell_count {}".format(result["source_positive_cell_count"]))
    lines.append("source_positive_bvol_sum {:.17g}".format(result["source_positive_bvol_sum"]))
    lines.append("source_L_min {:.17g}".format(result["source_L_min"]))
    lines.append("source_L_max {:.17g}".format(result["source_L_max"]))
    lines.append("source_L_bvol_weighted_mean {:.17g}".format(result["source_L_bvol_weighted_mean"]))
    if result.get("current_target_Lmax") is not None:
        lines.append(
            "current_target_Lmax {:.17g} dipole_lat_deg {:.17g}".format(
                result["current_target_Lmax"], result["current_target_dipole_lat_deg"]
            )
        )
    lines.append("")
    lines.append("threshold_scan")
    lines.append("Lmax dipole_lat_deg included_fraction excluded_fraction included_source_count")
    for row in result["threshold_scan"]:
        lines.append(
            "{:.17g} {:.17g} {:.17g} {:.17g} {}".format(
                row["Lmax"],
                row["dipole_lat_deg"],
                row["included_fraction"],
                row["excluded_fraction"],
                row["included_source_count"],
            )
        )
    lines.append("")
    lines.append("required_Lmax_by_bvol_quantile")
    lines.append("quantile Lmax_required dipole_lat_deg included_fraction_at_Lmax source_count_at_Lmax")
    for row in result["required_Lmax_by_bvol_quantile"]:
        lines.append(
            "{:.17g} {:.17g} {:.17g} {:.17g} {}".format(
                row["quantile"],
                row["Lmax_required"],
                row["dipole_lat_deg"],
                row["included_fraction_at_Lmax"],
                row["source_count_at_Lmax"],
            )
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-h5", required=True)
    parser.add_argument("--weights-h5", default=None)
    parser.add_argument("--source-l-dataset", default="source/Lb_cc")
    parser.add_argument("--target-l-edge-dataset", default="dst/L_edge")
    parser.add_argument("--bvol-source", choices=("prefer-active", "active", "raw"), default="prefer-active")
    parser.add_argument("--lmax-values", default=None, help="Comma-separated Lmax values to scan.")
    parser.add_argument("--quantiles", default=None, help="Comma-separated bVol quantiles to invert.")
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
