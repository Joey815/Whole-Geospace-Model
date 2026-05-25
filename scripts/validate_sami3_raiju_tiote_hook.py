#!/usr/bin/env python3
"""Validate runtime evidence for SAMI3 -> RAIJU tiote ingestion."""

import argparse
import json
import re
from pathlib import Path

import h5py
import numpy as np


FLOAT_RE = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][-+]?\d+)?")
FATAL_RE = re.compile(
    r"(?:\bFATAL\b|\bforrtl\b|MPI_Abort|Segmentation fault|Traceback \(most recent call last\)|^\s*ERROR(?:\s+STOP|:|\s|$))",
    re.IGNORECASE | re.MULTILINE,
)


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def floats_from(text):
    return [float(value) for value in FLOAT_RE.findall(text)]


def block_after(lines, marker, extra_lines):
    for i, line in enumerate(lines):
        if marker in line:
            first = line.split(marker, 1)[1]
            return "\n".join([first] + lines[i + 1 : i + 1 + extra_lines])
    return ""


def validate(args):
    log_path = Path(args.run_log).expanduser().resolve()
    product_path = Path(args.product_h5).expanduser().resolve()
    checks = []
    meta = {
        "run_log": str(log_path),
        "product_h5": str(product_path),
    }
    add(checks, "run_log_exists", log_path.is_file(), log_path)
    add(checks, "product_exists", product_path.is_file(), product_path)
    if not log_path.is_file() or not product_path.is_file():
        return checks, meta

    text = log_path.read_text(errors="replace")
    lines = text.splitlines()
    add(checks, "fin_marker", re.search(r"^\s*Fin\s*$", text, re.MULTILINE) is not None, "Fin")
    fatal = FATAL_RE.findall(text)
    add(checks, "fatal_markers_absent", len(fatal) == 0, "matches={}".format(len(fatal)))

    alpha_block = block_after(lines, "SAMI3 moments alpha Pavg/Davg/Pstd/Dstd/tiote:", 2)
    alphas = floats_from(alpha_block)
    meta["runtime_alphas"] = alphas[:5]
    expected_alphas = [
        args.expect_alpha_pavg,
        args.expect_alpha_davg,
        args.expect_alpha_pstd,
        args.expect_alpha_dstd,
        args.expect_alpha_tiote,
    ]
    add(checks, "alpha_count", len(alphas) >= 5, "values={}".format(alphas[:5]))
    if len(alphas) >= 5:
        max_alpha_diff = max(abs(alphas[i] - expected_alphas[i]) for i in range(5))
        add(
            checks,
            "alpha_values",
            max_alpha_diff <= args.tol,
            "actual={} expected={} max_diff={}".format(alphas[:5], expected_alphas, max_alpha_diff),
        )

    tiote_block = block_after(lines, "SAMI3 moments tiote min/max:", 0)
    tiote_minmax = floats_from(tiote_block)
    meta["runtime_tiote_minmax"] = tiote_minmax[:2]
    add(checks, "runtime_tiote_minmax_count", len(tiote_minmax) >= 2, "values={}".format(tiote_minmax[:2]))
    if len(tiote_minmax) >= 2:
        add(
            checks,
            "runtime_tiote_min",
            abs(tiote_minmax[0] - args.expect_runtime_tiote_min) <= args.tol,
            "actual={} expected={}".format(tiote_minmax[0], args.expect_runtime_tiote_min),
        )
        add(
            checks,
            "runtime_tiote_max",
            abs(tiote_minmax[1] - args.expect_runtime_tiote_max) <= args.tol,
            "actual={} expected={}".format(tiote_minmax[1], args.expect_runtime_tiote_max),
        )

    mask_block = block_after(lines, "SAMI3 moments valid mask counts Pavg/Davg/Pstd/Dstd/tiote:", 1)
    mask_counts = [int(round(value)) for value in floats_from(mask_block)]
    meta["runtime_mask_counts"] = mask_counts[:5]
    add(checks, "runtime_mask_count_values", len(mask_counts) >= 5, "values={}".format(mask_counts[:5]))
    if len(mask_counts) >= 5:
        add(
            checks,
            "runtime_mask_counts_match",
            all(value == args.expect_mask_count for value in mask_counts[:5]),
            "actual={} expected_each={}".format(mask_counts[:5], args.expect_mask_count),
        )

    with h5py.File(str(product_path), "r") as h5:
        add(checks, "raicpl_group_exists", "RaiCplMomentsOnly" in h5, "RaiCplMomentsOnly")
        if "RaiCplMomentsOnly" in h5:
            group = h5["RaiCplMomentsOnly"]
            add(checks, "tiote_exists", "tiote" in group, "tiote")
            add(checks, "tiote_mask_exists", "tiote_mask" in group, "tiote_mask")
            if "tiote" in group and "tiote_mask" in group:
                tiote = group["tiote"][...]
                mask = group["tiote_mask"][...].astype(bool)
                masked = tiote[mask]
                meta["product_tiote_mask_count"] = int(np.count_nonzero(mask))
                meta["product_tiote_masked_min"] = float(np.min(masked)) if masked.size else None
                meta["product_tiote_masked_max"] = float(np.max(masked)) if masked.size else None
                add(checks, "product_tiote_finite", bool(np.all(np.isfinite(tiote))), "nonfinite={}".format(tiote.size - np.count_nonzero(np.isfinite(tiote))))
                add(checks, "product_tiote_mask_count", int(np.count_nonzero(mask)) == args.expect_mask_count, "count={}".format(np.count_nonzero(mask)))
                if masked.size:
                    add(
                        checks,
                        "product_tiote_masked_min",
                        abs(float(np.min(masked)) - args.expect_product_tiote_min) <= args.tol,
                        "actual={} expected={}".format(float(np.min(masked)), args.expect_product_tiote_min),
                    )
                    add(
                        checks,
                        "product_tiote_masked_max",
                        abs(float(np.max(masked)) - args.expect_product_tiote_max) <= args.tol,
                        "actual={} expected={}".format(float(np.max(masked)), args.expect_product_tiote_max),
                    )
    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-log", required=True)
    parser.add_argument("--product-h5", required=True)
    parser.add_argument("--expect-alpha-pavg", type=float, default=0.0)
    parser.add_argument("--expect-alpha-davg", type=float, default=0.05)
    parser.add_argument("--expect-alpha-pstd", type=float, default=0.0)
    parser.add_argument("--expect-alpha-dstd", type=float, default=0.0)
    parser.add_argument("--expect-alpha-tiote", type=float, default=1.0)
    parser.add_argument("--expect-mask-count", type=int, default=5940)
    parser.add_argument("--expect-runtime-tiote-min", type=float, default=0.873951375484467)
    parser.add_argument("--expect-runtime-tiote-max", type=float, default=4.0)
    parser.add_argument("--expect-product-tiote-min", type=float, default=0.8739513754844666)
    parser.add_argument("--expect-product-tiote-max", type=float, default=1.0004502534866333)
    parser.add_argument("--tol", type=float, default=1.0e-10)
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
