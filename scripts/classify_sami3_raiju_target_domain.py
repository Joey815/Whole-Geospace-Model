#!/usr/bin/env python3
"""Classify SAMI3 -> RAIJU source volume against the RAIJU target L domain."""

import argparse
import json
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
    return float(value) if np.isfinite(value) else None


def summarize_mask(name, mask, bvol, lb, lmin, lmax):
    count = int(np.count_nonzero(mask))
    total = float(np.nansum(bvol[mask]))
    above = mask & (lb > lmax)
    below = mask & (lb < lmin)
    inside = mask & (lb >= lmin) & (lb <= lmax)

    def frac(subtotal):
        return float(subtotal / total) if total > 0.0 else None

    weighted_lb = None
    if total > 0.0:
        weighted_lb = float(np.nansum(lb[mask] * bvol[mask]) / total)

    return {
        "name": name,
        "count": count,
        "active_bvol_sum": total,
        "Lb_min": finite_float(np.nanmin(lb[mask])) if count else None,
        "Lb_max": finite_float(np.nanmax(lb[mask])) if count else None,
        "Lb_mean_bvol_weighted": weighted_lb,
        "above_target_Lmax_count": int(np.count_nonzero(above)),
        "above_target_Lmax_bvol_sum": float(np.nansum(bvol[above])),
        "above_target_Lmax_bvol_fraction": frac(float(np.nansum(bvol[above]))),
        "below_target_Lmin_count": int(np.count_nonzero(below)),
        "below_target_Lmin_bvol_sum": float(np.nansum(bvol[below])),
        "below_target_Lmin_bvol_fraction": frac(float(np.nansum(bvol[below]))),
        "inside_target_Lrange_count": int(np.count_nonzero(inside)),
        "inside_target_Lrange_bvol_sum": float(np.nansum(bvol[inside])),
        "inside_target_Lrange_bvol_fraction": frac(float(np.nansum(bvol[inside]))),
    }


def top_outside(outside, bvol, lb, terms, mapped, top_n):
    indices = np.argwhere(outside)
    if indices.size == 0:
        return []
    values = bvol[outside]
    order = np.argsort(values)[::-1][:top_n]
    rows = []
    for idx in order:
        j, i = indices[idx]
        rows.append(
            {
                "source_i": int(i + 1),
                "source_j": int(j + 1),
                "bvol_active": float(values[idx]),
                "Lb_cc": float(lb[j, i]),
                "term_count": int(terms[j, i]),
                "mapped_fraction": float(mapped[j, i]),
            }
        )
    return rows


def classify(args):
    audit_h5 = Path(args.audit_h5).expanduser().resolve()
    weights_h5 = Path(args.weights_h5).expanduser().resolve()

    with h5py.File(weights_h5, "r") as handle:
        l_edge = np.asarray(handle[args.target_l_edge_dataset][()])
        lmin = float(np.nanmin(l_edge))
        lmax = float(np.nanmax(l_edge))

    with h5py.File(audit_h5, "r") as handle:
        group = handle["source"]
        status = np.asarray(group["status_code"][()])
        lb = np.asarray(group[args.source_l_dataset][()])
        bvol = np.asarray(group[args.source_bvol_dataset][()])
        terms = np.asarray(group["term_count"][()])
        mapped = np.asarray(group["mapped_fraction"][()])

    positive = (bvol > args.bvol_floor) & np.isfinite(bvol) & np.isfinite(lb)
    masks = {
        "positive_all": positive,
        "used": positive & (status == 0),
        "outside_target": positive & (status == 4),
    }
    for code, label in STATUS_LABELS.items():
        masks["status_{}".format(label)] = positive & (status == code)

    classes = {}
    for name, mask in masks.items():
        classes[name] = summarize_mask(name, mask, bvol, lb, lmin, lmax)

    result = {
        "product": "sami3_raiju_target_domain_classification",
        "audit_h5": str(audit_h5),
        "weights_h5": str(weights_h5),
        "classification_basis": "status_code with positive {}; no source closed_cell_mask filter".format(
            args.source_bvol_dataset
        ),
        "source_bvol_dataset": args.source_bvol_dataset,
        "source_l_dataset": args.source_l_dataset,
        "target_l_edge_dataset": args.target_l_edge_dataset,
        "target_L_edge_min": lmin,
        "target_L_edge_max": lmax,
        "classes": classes,
        "top_outside_target_by_bvol": top_outside(masks["outside_target"], bvol, lb, terms, mapped, args.top_n),
    }
    return result


def write_text(result, path):
    lines = [
        "product={}".format(result["product"]),
        "classification_basis={}".format(result["classification_basis"]),
        "target_L_edge_min={}".format(result["target_L_edge_min"]),
        "target_L_edge_max={}".format(result["target_L_edge_max"]),
    ]
    for name in sorted(result["classes"]):
        lines.append("[{}]".format(name))
        for key, value in result["classes"][name].items():
            if key == "name":
                continue
            lines.append("{}={}".format(key, value))
    lines.append("[top_outside_target_by_bvol]")
    for row in result["top_outside_target_by_bvol"]:
        lines.append(
            "source_i={source_i} source_j={source_j} bvol_active={bvol_active:.9g} "
            "Lb_cc={Lb_cc:.9g} term_count={term_count} mapped_fraction={mapped_fraction}".format(**row)
        )
    Path(path).write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-h5", required=True)
    parser.add_argument("--weights-h5", required=True)
    parser.add_argument("--source-bvol-dataset", default="bvol_active_cc")
    parser.add_argument("--source-l-dataset", default="Lb_cc")
    parser.add_argument("--target-l-edge-dataset", default="/dst/L_edge")
    parser.add_argument("--bvol-floor", type=float, default=0.0)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--json-output", default=None)
    parser.add_argument("--text-output", default=None)
    args = parser.parse_args()

    result = classify(args)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        Path(args.json_output).write_text(text)
    else:
        print(text, end="")
    if args.text_output:
        write_text(result, args.text_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
