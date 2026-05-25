#!/usr/bin/env python3
"""Validate SAMI3 -> RAIJU target-domain flux-volume closure."""

import argparse
import json
import math
from pathlib import Path


STATUS_CODES = {
    "used": "0",
    "bad_bvol": "1",
    "bad_geometry": "2",
    "large_footprint": "3",
    "outside_target": "4",
    "no_terms": "5",
}


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def finite_number(value):
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def get_status_fraction(status, code, key):
    item = status.get(code)
    if not isinstance(item, dict):
        return None
    value = item.get(key)
    if finite_number(value):
        return float(value)
    return None


def choose_status_group(audit, source):
    if source == "active":
        return audit.get("source_bvol_active_by_status"), "active", "fraction_of_valid_bvol_active"
    if source == "total":
        return audit.get("source_bvol_by_status"), "total", "fraction_of_valid_bvol"

    active = audit.get("source_bvol_active_by_status")
    if isinstance(active, dict):
        return active, "active", "fraction_of_valid_bvol_active"
    return audit.get("source_bvol_by_status"), "total", "fraction_of_valid_bvol"


def validate(args):
    path = Path(args.audit_json).expanduser().resolve()
    checks = []
    meta = {"audit_json": str(path)}
    add(checks, "audit_json_exists", path.is_file(), path)
    if not path.is_file():
        return checks, meta

    audit = json.loads(path.read_text())
    add(
        checks,
        "product_kind",
        audit.get("product") == "sami3_raiju_flux_volume_geometry_audit",
        audit.get("product"),
    )

    weight = audit.get("weight_compare", {})
    stored_count = weight.get("stored_count")
    recomputed_count = weight.get("recomputed_count")
    missing = weight.get("missing_stored_terms")
    extra = weight.get("extra_recomputed_terms")
    max_abs = weight.get("max_abs_diff")
    add(checks, "weight_count_match", stored_count == recomputed_count, "{} vs {}".format(stored_count, recomputed_count))
    add(checks, "weight_no_missing_terms", missing == 0, missing)
    add(checks, "weight_no_extra_terms", extra == 0, extra)
    add(
        checks,
        "weight_max_abs_diff",
        finite_number(max_abs) and float(max_abs) <= args.max_weight_abs_diff,
        "max_abs={} max={}".format(max_abs, args.max_weight_abs_diff),
    )

    target_positive = audit.get("target_positive_fraction")
    add(
        checks,
        "target_positive_fraction",
        finite_number(target_positive) and float(target_positive) >= args.min_target_positive_fraction,
        "fraction={} min={}".format(target_positive, args.min_target_positive_fraction),
    )

    status, source, fraction_key = choose_status_group(audit, args.bvol_source)
    meta["bvol_source_used"] = source
    add(checks, "source_status_group_exists", isinstance(status, dict), source)
    if not isinstance(status, dict):
        return checks, meta

    fractions = {}
    missing_labels = []
    for label, code in STATUS_CODES.items():
        fraction = get_status_fraction(status, code, fraction_key)
        fractions[label] = fraction
        if fraction is None:
            missing_labels.append(label)
    meta["status_fractions"] = fractions
    add(checks, "status_fractions_present", not missing_labels, missing_labels)

    finite_fractions = [value for value in fractions.values() if finite_number(value)]
    if finite_fractions:
        fraction_sum = float(sum(finite_fractions))
        add(
            checks,
            "status_fraction_sum",
            abs(fraction_sum - 1.0) <= args.status_fraction_sum_tol,
            "sum={} tol={}".format(fraction_sum, args.status_fraction_sum_tol),
        )

    used = fractions.get("used")
    large = fractions.get("large_footprint")
    outside = fractions.get("outside_target")
    bad_bvol = fractions.get("bad_bvol")
    bad_geometry = fractions.get("bad_geometry")
    no_terms = fractions.get("no_terms")
    add(
        checks,
        "used_fraction",
        finite_number(used) and used >= args.min_used_fraction,
        "fraction={} min={}".format(used, args.min_used_fraction),
    )
    add(
        checks,
        "large_footprint_fraction",
        finite_number(large) and large <= args.max_large_footprint_fraction,
        "fraction={} max={}".format(large, args.max_large_footprint_fraction),
    )
    add(
        checks,
        "outside_target_fraction",
        finite_number(outside) and outside <= args.max_outside_target_fraction,
        "fraction={} max={}".format(outside, args.max_outside_target_fraction),
    )
    add(
        checks,
        "bad_bvol_fraction",
        finite_number(bad_bvol) and bad_bvol <= args.max_bad_bvol_fraction,
        "fraction={} max={}".format(bad_bvol, args.max_bad_bvol_fraction),
    )
    add(
        checks,
        "bad_geometry_fraction",
        finite_number(bad_geometry) and bad_geometry <= args.max_bad_geometry_fraction,
        "fraction={} max={}".format(bad_geometry, args.max_bad_geometry_fraction),
    )
    add(
        checks,
        "no_terms_fraction",
        finite_number(no_terms) and no_terms <= args.max_no_terms_fraction,
        "fraction={} max={}".format(no_terms, args.max_no_terms_fraction),
    )

    if args.require_active_ledger:
        active_sum = audit.get("source_valid_bvol_active_sum")
        active_frac = audit.get("source_bvol_active_frac_stats_valid")
        add(checks, "active_valid_bvol_sum", finite_number(active_sum) and float(active_sum) > 0.0, active_sum)
        if isinstance(active_frac, dict):
            finite_count = active_frac.get("finite_count")
            total_count = active_frac.get("total_count")
            min_value = active_frac.get("min")
            add(checks, "active_frac_all_finite", finite_count == total_count and total_count != 0, active_frac)
            add(
                checks,
                "active_frac_min",
                finite_number(min_value) and float(min_value) >= args.min_active_frac,
                "min={} required={}".format(min_value, args.min_active_frac),
            )
        else:
            add(checks, "active_frac_stats_present", False, active_frac)

    closure_ratio = audit.get("target_domain_proxy_closure", {}).get("raw_sum_over_positive_target_bvol_sum")
    if args.min_proxy_closure_ratio is not None:
        add(
            checks,
            "proxy_closure_ratio",
            finite_number(closure_ratio) and float(closure_ratio) >= args.min_proxy_closure_ratio,
            "ratio={} min={}".format(closure_ratio, args.min_proxy_closure_ratio),
        )
    meta["proxy_closure_ratio"] = closure_ratio
    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-json", required=True)
    parser.add_argument("--bvol-source", choices=["prefer-active", "active", "total"], default="prefer-active")
    parser.add_argument("--require-active-ledger", action="store_true")
    parser.add_argument("--max-weight-abs-diff", type=float, default=1.0e-6)
    parser.add_argument("--min-target-positive-fraction", type=float, default=0.90)
    parser.add_argument("--status-fraction-sum-tol", type=float, default=1.0e-6)
    parser.add_argument("--min-used-fraction", type=float, default=0.50)
    parser.add_argument("--max-large-footprint-fraction", type=float, default=0.05)
    parser.add_argument("--max-outside-target-fraction", type=float, default=0.05)
    parser.add_argument("--max-bad-bvol-fraction", type=float, default=0.01)
    parser.add_argument("--max-bad-geometry-fraction", type=float, default=0.01)
    parser.add_argument("--max-no-terms-fraction", type=float, default=0.01)
    parser.add_argument("--min-active-frac", type=float, default=0.0)
    parser.add_argument("--min-proxy-closure-ratio", type=float, default=None)
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    checks, meta = validate(args)
    ok = all(check["ok"] for check in checks)
    result = {"ok": ok, "checks": checks, "meta": meta}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for check in checks:
        print("{:4s} {}: {}".format("ok" if check["ok"] else "FAIL", check["name"], check["detail"]))
    print("overall={}".format("ok" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
