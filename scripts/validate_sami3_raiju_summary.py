#!/usr/bin/env python3
"""Validate a SAMI3 -> RAIJU/GAMERA longrun summary JSON."""

import argparse
import json
import math
from pathlib import Path


RAICPL_FIELDS = ["Pavg", "Davg", "Pstd", "Dstd"]


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def finite_number(value):
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def iter_compare_groups(summary):
    for section_name in ("final_restart_recommended_vs_baseline", "final_history_recommended_vs_baseline"):
        section = summary.get(section_name, {})
        for group_name, group in section.items():
            if not isinstance(group, dict):
                continue
            for field_name, stats in group.items():
                yield section_name, group_name, field_name, stats


def validate(args):
    path = Path(args.summary_json).expanduser().resolve()
    checks = []
    meta = {"summary_json": str(path)}
    add(checks, "summary_json_exists", path.is_file(), path)
    if not path.is_file():
        return checks, meta

    summary = json.loads(path.read_text())
    meta["label"] = summary.get("label")
    meta["run_dir"] = summary.get("run_dir")

    formulas = summary.get("formula_checks", {})
    for field in RAICPL_FIELDS:
        stats = formulas.get(field, {})
        max_abs = stats.get("formula_max_abs")
        max_rel = stats.get("formula_max_rel")
        add(
            checks,
            "{}_formula_abs".format(field),
            finite_number(max_abs) and abs(float(max_abs)) <= args.formula_abs_tol,
            "max_abs={} tol={}".format(max_abs, args.formula_abs_tol),
        )
        add(
            checks,
            "{}_formula_rel".format(field),
            finite_number(max_rel) and abs(float(max_rel)) <= args.formula_rel_tol,
            "max_rel={} tol={}".format(max_rel, args.formula_rel_tol),
        )
        if args.require_positive_inputs and field in ("Pavg", "Davg"):
            actual_mean = stats.get("actual_mean")
            actual_max = stats.get("actual_max")
            add(
                checks,
                "{}_positive_actual".format(field),
                finite_number(actual_mean)
                and finite_number(actual_max)
                and float(actual_mean) > 0.0
                and float(actual_max) > 0.0,
                "mean={} max={}".format(actual_mean, actual_max),
            )

    nonfinite = summary.get("nonfinite", {})
    for group_name in ("base_raiju_res", "proto_raiju_res", "base_gam_res", "proto_gam_res"):
        items = nonfinite.get(group_name)
        add(
            checks,
            "nonfinite_{}_empty".format(group_name),
            items == [],
            items,
        )

    history_steps = summary.get("history_last_steps", {})
    raiju_step = history_steps.get("raiju")
    gam_step = history_steps.get("gam")
    add(
        checks,
        "history_last_steps_exist",
        bool(raiju_step) and bool(gam_step),
        history_steps,
    )
    add(
        checks,
        "history_last_steps_match",
        (not args.require_matching_history_step) or (raiju_step == gam_step),
        history_steps,
    )

    missing = []
    nonfinite_stats = []
    for section_name, group_name, field_name, stats in iter_compare_groups(summary):
        if stats.get("missing"):
            missing.append("{}/{}/{}".format(section_name, group_name, field_name))
            continue
        for key in ("max_abs", "mean_abs", "recommended_mean", "baseline_mean"):
            if not finite_number(stats.get(key)):
                nonfinite_stats.append("{}/{}/{}/{}".format(section_name, group_name, field_name, key))
    add(checks, "comparison_fields_present", not missing, missing)
    add(checks, "comparison_stats_finite", not nonfinite_stats, nonfinite_stats)
    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--formula-abs-tol", type=float, default=1.0e-12)
    parser.add_argument("--formula-rel-tol", type=float, default=1.0e-12)
    parser.add_argument("--require-positive-inputs", action="store_true")
    parser.add_argument("--require-matching-history-step", action="store_true")
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
