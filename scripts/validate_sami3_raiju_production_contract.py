#!/usr/bin/env python3
"""Validate production-readiness labeling for SAMI3 -> RAIJU products.

This validator is intentionally about product semantics, not numerical
roundoff.  The current Voltron/RAIJU sparse product can be runtime-valid while
still being diagnostic-only physics, because most positive active Voltron
source bVol sits outside the current RAIJU target L range.
"""

import argparse
import json
import math
from pathlib import Path

import h5py


NONPRODUCTION_LABELS = {
    "",
    "unknown",
    "smoke_only",
    "prototype",
    "diagnostic",
    "diagnostic_only",
    "diagnostic_overlap_only_prototype",
    "diagnostic_runtime_adapter",
}


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def finite_number(value):
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def h5_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def h5_attrs(handle):
    return {key: h5_value(value) for key, value in handle.attrs.items()}


def decode_text(raw):
    if isinstance(raw, bytes):
        return raw.decode("utf-8")
    return str(raw)


def read_metadata(handle):
    if "metadata/json" not in handle:
        return {}
    try:
        return json.loads(decode_text(handle["metadata/json"][()]))
    except json.JSONDecodeError:
        return {}


def nested_get(data, keys, default=None):
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def first_present(*values):
    for value in values:
        if value is not None:
            return value
    return None


def normalize_label(value):
    if value is None:
        return "unknown"
    return str(value).strip().lower()


def resolve_weight_file(product_path, product_meta, mapping_attrs):
    candidates = [
        nested_get(product_meta, ["raicpl_runtime_mapping_quality", "weight_file"]),
        nested_get(product_meta, ["raicpl_runtime_mapping", "weight_file"]),
        mapping_attrs.get("weight_file"),
    ]
    for candidate in candidates:
        if candidate:
            path = Path(str(candidate)).expanduser()
            if not path.is_absolute():
                path = product_path.parent / path
            return path.resolve()
    return None


def read_product(path):
    with h5py.File(str(path), "r") as handle:
        attrs = h5_attrs(handle)
        meta = read_metadata(handle)
        mapping_attrs = h5_attrs(handle["MappingQuality"]) if "MappingQuality" in handle else {}
    return attrs, meta, mapping_attrs


def read_weight_file(path):
    with h5py.File(str(path), "r") as handle:
        attrs = h5_attrs(handle)
        meta = read_metadata(handle)
    return attrs, meta


def read_target_admissible_subset(path):
    if path is None:
        return None
    subset_path = Path(path).expanduser().resolve()
    summary = {
        "path": str(subset_path),
        "exists": subset_path.is_file(),
        "parsable": False,
        "target_admissible_bvol_fraction": None,
        "target_admissible_is_representative": None,
    }
    if not subset_path.is_file():
        return summary
    try:
        data = json.loads(subset_path.read_text())
    except json.JSONDecodeError:
        return summary

    fraction = first_present(
        nested_get(data, ["interpretation", "target_admissible_bvol_fraction"]),
        nested_get(data, ["subsets", "target_admissible_lrange", "fraction_of_total_positive_bvol"]),
    )
    representative = nested_get(data, ["interpretation", "target_admissible_is_representative"])
    if fraction is not None:
        fraction = float(fraction)

    summary.update(
        {
            "parsable": True,
            "target_L_edge_min": data.get("target_L_edge_min"),
            "target_L_edge_max": data.get("target_L_edge_max"),
            "positive_source_bvol_sum": data.get("positive_source_bvol_sum"),
            "target_admissible_bvol_fraction": fraction,
            "target_admissible_is_representative": representative,
        }
    )
    return summary


def source_domain_summary(weight_attrs, weight_meta):
    return {
        "policy": first_present(
            weight_meta.get("voltron_source_domain_policy"),
            weight_attrs.get("voltron_source_domain_policy"),
            "none",
        ),
        "skipped_above_lmax_fraction": first_present(
            weight_meta.get("voltron_to_raiju_source_domain_skipped_above_lmax_bvol_fraction"),
            weight_attrs.get("voltron_to_raiju_source_domain_skipped_above_lmax_bvol_fraction"),
        ),
        "positive_bvol_sum": first_present(
            weight_meta.get("voltron_to_raiju_source_domain_positive_bvol_sum"),
            weight_attrs.get("voltron_to_raiju_source_domain_positive_bvol_sum"),
        ),
        "target_l_min": first_present(
            weight_meta.get("voltron_to_raiju_source_domain_target_l_min"),
            weight_attrs.get("voltron_to_raiju_source_domain_target_l_min"),
        ),
        "target_l_max": first_present(
            weight_meta.get("voltron_to_raiju_source_domain_target_l_max"),
            weight_attrs.get("voltron_to_raiju_source_domain_target_l_max"),
        ),
    }


def validate(args):
    product_path = Path(args.product_h5).expanduser().resolve()
    checks = []
    meta = {
        "product_h5": str(product_path),
        "mode": args.mode,
        "max_production_source_above_lmax_fraction": args.max_production_source_above_lmax_fraction,
        "min_production_target_admissible_bvol_fraction": (
            args.min_production_target_admissible_bvol_fraction
        ),
    }
    add(checks, "product_exists", product_path.is_file(), product_path)
    if not product_path.is_file():
        return checks, meta

    product_attrs, product_meta, mapping_attrs = read_product(product_path)
    product_kind = product_attrs.get("product") or product_meta.get("product")
    product_label = normalize_label(
        product_attrs.get("physical_validity") or product_meta.get("physical_validity")
    )
    product_note = product_attrs.get("note") or nested_get(product_meta, ["compatibility", "note"], "")
    meta["product"] = product_kind
    meta["product_physical_validity"] = product_label
    meta["product_note"] = product_note
    add(
        checks,
        "product_kind",
        product_kind == "sami3_voltron_raiju_moments_diagnostic",
        product_kind,
    )

    weight_path = resolve_weight_file(product_path, product_meta, mapping_attrs)
    meta["weight_file"] = str(weight_path) if weight_path is not None else None
    add(checks, "weight_file_resolved", weight_path is not None, weight_path)
    if weight_path is None:
        return checks, meta
    add(checks, "weight_file_exists", weight_path.is_file(), weight_path)
    if not weight_path.is_file():
        return checks, meta

    weight_attrs, weight_meta = read_weight_file(weight_path)
    weight_label = normalize_label(weight_attrs.get("physical_validity") or weight_meta.get("physical_validity"))
    domain = source_domain_summary(weight_attrs, weight_meta)
    skipped_above = domain["skipped_above_lmax_fraction"]
    if skipped_above is not None:
        skipped_above = float(skipped_above)
    meta["weight_physical_validity"] = weight_label
    meta["source_domain"] = domain

    add(
        checks,
        "weight_product_kind",
        weight_attrs.get("product") == "sami3_to_raiju_mapping_weights",
        weight_attrs.get("product"),
    )
    add(
        checks,
        "source_domain_policy_known",
        str(domain["policy"]) not in ("", "none", "unknown"),
        domain["policy"],
    )
    add(
        checks,
        "source_domain_skipped_above_lmax_fraction_finite",
        finite_number(skipped_above),
        skipped_above,
    )

    high_skip = finite_number(skipped_above) and skipped_above > args.max_production_source_above_lmax_fraction
    subset = read_target_admissible_subset(args.target_admissible_json)
    low_target_admissible = False
    if subset is not None:
        meta["target_admissible_subset"] = subset
        admissible_fraction = subset["target_admissible_bvol_fraction"]
        add(checks, "target_admissible_json_exists", subset["exists"], subset["path"])
        add(checks, "target_admissible_json_parsable", subset["parsable"], subset["path"])
        add(
            checks,
            "target_admissible_bvol_fraction_finite",
            finite_number(admissible_fraction),
            admissible_fraction,
        )
        low_target_admissible = (
            finite_number(admissible_fraction)
            and admissible_fraction < args.min_production_target_admissible_bvol_fraction
        )
    elif args.require_target_admissible_json:
        add(
            checks,
            "target_admissible_json_required",
            False,
            "--require-target-admissible-json set but --target-admissible-json not supplied",
        )

    meta["high_source_domain_skip"] = bool(high_skip)
    meta["low_target_admissible_bvol_fraction"] = bool(low_target_admissible)
    meta["classification"] = (
        "diagnostic_only" if (high_skip or low_target_admissible) else "production_candidate"
    )

    if args.mode == "diagnostic-contract":
        if high_skip:
            add(
                checks,
                "high_skip_is_not_labeled_production",
                product_label in NONPRODUCTION_LABELS and weight_label in NONPRODUCTION_LABELS,
                "product={} weight={} skipped_above_lmax_fraction={}".format(
                    product_label, weight_label, skipped_above
                ),
            )
        if low_target_admissible:
            add(
                checks,
                "low_target_admissible_fraction_is_not_labeled_production",
                product_label in NONPRODUCTION_LABELS and weight_label in NONPRODUCTION_LABELS,
                "product={} weight={} target_admissible_bvol_fraction={} min={}".format(
                    product_label,
                    weight_label,
                    subset["target_admissible_bvol_fraction"],
                    args.min_production_target_admissible_bvol_fraction,
                ),
            )
        if high_skip or low_target_admissible:
            add(
                checks,
                "diagnostic_note_present",
                "diagnostic" in str(product_note).lower() or product_label in NONPRODUCTION_LABELS,
                product_note,
            )
        else:
            add(
                checks,
                "production_threshold_not_exceeded",
                True,
                "skipped_above_lmax_fraction={}".format(skipped_above),
            )
    else:
        add(
            checks,
            "production_source_domain_skip_threshold",
            finite_number(skipped_above)
            and skipped_above <= args.max_production_source_above_lmax_fraction,
            "fraction={} max={}".format(
                skipped_above, args.max_production_source_above_lmax_fraction
            ),
        )
        add(
            checks,
            "production_label",
            product_label == "production" and weight_label == "production",
            "product={} weight={}".format(product_label, weight_label),
        )
        add(
            checks,
            "runtime_valid_fraction",
            nested_get(product_meta, ["raicpl_runtime_mapping_quality", "runtime_valid_fraction"], 0.0)
            >= args.min_runtime_valid_fraction,
            nested_get(product_meta, ["raicpl_runtime_mapping_quality", "runtime_valid_fraction"], None),
        )
        if subset is not None:
            add(
                checks,
                "production_target_admissible_bvol_fraction",
                finite_number(subset["target_admissible_bvol_fraction"])
                and subset["target_admissible_bvol_fraction"]
                >= args.min_production_target_admissible_bvol_fraction,
                "fraction={} min={}".format(
                    subset["target_admissible_bvol_fraction"],
                    args.min_production_target_admissible_bvol_fraction,
                ),
            )

    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-h5", required=True)
    parser.add_argument(
        "--mode",
        choices=("diagnostic-contract", "production-readiness"),
        default="diagnostic-contract",
    )
    parser.add_argument("--max-production-source-above-lmax-fraction", type=float, default=0.05)
    parser.add_argument("--min-production-target-admissible-bvol-fraction", type=float, default=0.05)
    parser.add_argument("--min-runtime-valid-fraction", type=float, default=0.95)
    parser.add_argument(
        "--target-admissible-json",
        default=None,
        help="Optional output from analyze_sami3_raiju_target_admissible_subset.py.",
    )
    parser.add_argument(
        "--require-target-admissible-json",
        action="store_true",
        help="Fail if --target-admissible-json is not supplied.",
    )
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    checks, meta = validate(args)
    ok = all(item["ok"] for item in checks)
    result = {"ok": ok, "checks": checks, "meta": meta}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for item in checks:
        print("{:4s} {}: {}".format("ok" if item["ok"] else "FAIL", item["name"], item["detail"]))
    print("classification={}".format(meta.get("classification", "unknown")))
    print("overall={}".format("ok" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
