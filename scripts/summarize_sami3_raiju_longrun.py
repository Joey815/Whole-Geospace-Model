#!/usr/bin/env python3
"""Summarize a paired SAMI3 -> RAIJU/GAMERA long-run HDF5 result."""

import argparse
import json
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import h5py
import numpy as np


RAICPL_FIELDS = ["Pavg", "Davg", "Pstd", "Dstd"]
RAICPL_ALPHA_ATTR = {
    "Pavg": "alphaPavg",
    "Davg": "alphaDavg",
    "Pstd": "alphaPstd",
    "Dstd": "alphaDstd",
}
RAIJU_RESTART_FIELDS = [
    "State/Pavg_in",
    "State/Davg_in",
    "State/eta",
    "State/Density",
    "State/Pressure",
    "State/eta_avg",
    "State/Density_avg",
    "State/Pressure_avg",
]
GAM_RESTART_FIELDS = ["Gas0"]
RAIJU_HISTORY_FIELDS = ["Pavg_in", "Davg_in", "Density", "Pressure"]
GAM_HISTORY_FIELDS = ["D", "P", "SrcD_COLD", "SrcP_COLD"]


def finite_stats(values):
    arr = np.asarray(values)
    finite = np.isfinite(arr)
    if not finite.any():
        return {"mean": None, "max": None, "nonfinite": int(arr.size)}
    vals = arr[finite].astype(np.float64, copy=False)
    return {
        "mean": float(vals.mean()),
        "max": float(vals.max()),
        "nonfinite": int(arr.size - np.count_nonzero(finite)),
    }


def compare_arrays(a, b):
    av = np.asarray(a, dtype=np.float64)
    bv = np.asarray(b, dtype=np.float64)
    diff = np.abs(av - bv)
    denom = np.maximum(np.abs(bv), 1.0e-300)
    finite = np.isfinite(diff)
    if not finite.any():
        return {"max_abs": None, "mean_abs": None, "max_rel": None}
    rel = diff / denom
    return {
        "max_abs": float(np.nanmax(diff)),
        "mean_abs": float(np.nanmean(diff)),
        "max_rel": float(np.nanmax(rel)),
    }


def parse_sami3_moments_xml(path):
    tree = ET.parse(str(path))
    elem = tree.find(".//sami3Moments")
    if elem is None:
        raise RuntimeError("missing sami3Moments element in {}".format(path))
    source_file = elem.attrib["file"]
    group = elem.attrib.get("group", "/RaiCplMomentsOnly")
    alphas = {}
    for field, attr in RAICPL_ALPHA_ATTR.items():
        alphas[field] = float(elem.attrib.get(attr, "1.0"))
    return {"source_file": source_file, "group": group, "alphas": alphas}


def nonfinite_fields(path, names):
    out = []
    with h5py.File(str(path), "r") as h5:
        for name in names:
            if name not in h5:
                out.append({"name": name, "missing": True})
                continue
            data = h5[name][...]
            count = int(data.size - np.count_nonzero(np.isfinite(data)))
            if count:
                out.append({"name": name, "nonfinite": count})
    return out


def last_step_name(path):
    step_re = re.compile(r"^Step#(\d+)$")
    last = None
    with h5py.File(str(path), "r") as h5:
        for key in h5.keys():
            m = step_re.match(key)
            if not m:
                continue
            value = int(m.group(1))
            if last is None or value > last:
                last = value
    if last is None:
        return None
    return "Step#{}".format(last)


def dataset_compare(path_a, path_b, names):
    result = {}
    with h5py.File(str(path_a), "r") as a, h5py.File(str(path_b), "r") as b:
        for name in names:
            if name not in a or name not in b:
                result[name] = {"missing": True}
                continue
            stats = compare_arrays(a[name][...], b[name][...])
            stats["recommended_mean"] = finite_stats(a[name][...])["mean"]
            stats["baseline_mean"] = finite_stats(b[name][...])["mean"]
            result[name] = stats
    return result


def history_compare(path_a, path_b, step, names):
    result = {}
    if step is None:
        return result
    with h5py.File(str(path_a), "r") as a, h5py.File(str(path_b), "r") as b:
        for name in names:
            full = "{}/{}".format(step, name)
            if full not in a or full not in b:
                result[full] = {"missing": True}
                continue
            stats = compare_arrays(a[full][...], b[full][...])
            stats["recommended_mean"] = finite_stats(a[full][...])["mean"]
            stats["baseline_mean"] = finite_stats(b[full][...])["mean"]
            result[full] = stats
    return result


def formula_checks(run_dir, label, xml_info):
    base_path = run_dir / "sami3_moments_base_control_{}.raiCpl.Res.00000.h5".format(label)
    proto_path = run_dir / "sami3_moments_dsB_lmlt_recommended_{}.raiCpl.Res.00000.h5".format(label)
    source_path = Path(xml_info["source_file"])
    group = xml_info["group"].strip("/")
    out = {}
    with h5py.File(str(base_path), "r") as base, h5py.File(str(proto_path), "r") as proto, h5py.File(str(source_path), "r") as src:
        src_group = src[group]
        for field in RAICPL_FIELDS:
            alpha = xml_info["alphas"][field]
            base_v = base[field][...].astype(np.float64)
            proto_v = proto[field][...].astype(np.float64)
            src_v = src_group[field][...].astype(np.float64)
            mask_name = field + "_mask"
            if mask_name in src_group:
                mask = src_group[mask_name][...].astype(bool)
            else:
                mask = np.ones(src_v.shape, dtype=bool)
            expected = base_v.copy()
            expected[mask] = (1.0 - alpha) * base_v[mask] + alpha * src_v[mask]
            diff = np.abs(proto_v - expected)
            rel = diff / np.maximum(np.abs(expected), 1.0e-300)
            stats = finite_stats(proto_v)
            out[field] = {
                "alpha": alpha,
                "formula_max_abs": float(np.nanmax(diff)),
                "formula_max_rel": float(np.nanmax(rel)),
                "actual_mean": stats["mean"],
                "actual_max": stats["max"],
                "mask_true": int(np.count_nonzero(mask)),
                "mask_total": int(mask.size),
            }
    return out


def run_sacct(job_id):
    if not job_id:
        return ""
    cmd = [
        "sacct",
        "-j",
        str(job_id),
        "--format=JobID,JobName,State,ExitCode,Elapsed,MaxRSS",
        "-P",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    return proc.stdout


def summarize(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    label = args.label
    xml_path = run_dir / "tinyCase_sami3_moments_dsB_lmlt_recommended_{}.xml".format(label)
    xml_info = parse_sami3_moments_xml(xml_path)

    paths = {
        "base_raicpl_res": run_dir / "sami3_moments_base_control_{}.raiCpl.Res.00000.h5".format(label),
        "proto_raicpl_res": run_dir / "sami3_moments_dsB_lmlt_recommended_{}.raiCpl.Res.00000.h5".format(label),
        "base_raiju_res": run_dir / "sami3_moments_base_control_{}.raiju.Res.00000.h5".format(label),
        "proto_raiju_res": run_dir / "sami3_moments_dsB_lmlt_recommended_{}.raiju.Res.00000.h5".format(label),
        "base_gam_res": run_dir / "sami3_moments_base_control_{}.gam.Res.00000.h5".format(label),
        "proto_gam_res": run_dir / "sami3_moments_dsB_lmlt_recommended_{}.gam.Res.00000.h5".format(label),
        "base_raiju_history": run_dir / "sami3_moments_base_control_{}.raiju.h5".format(label),
        "proto_raiju_history": run_dir / "sami3_moments_dsB_lmlt_recommended_{}.raiju.h5".format(label),
        "base_gam_history": run_dir / "sami3_moments_base_control_{}.gam.h5".format(label),
        "proto_gam_history": run_dir / "sami3_moments_dsB_lmlt_recommended_{}.gam.h5".format(label),
    }
    for key, path in paths.items():
        if not path.exists():
            raise RuntimeError("missing {}: {}".format(key, path))

    raiju_step = last_step_name(paths["proto_raiju_history"])
    gam_step = last_step_name(paths["proto_gam_history"])
    result = {
        "run_dir": str(run_dir),
        "label": label,
        "job_id": args.job_id,
        "xml": xml_info,
        "sacct": run_sacct(args.job_id),
        "formula_checks": formula_checks(run_dir, label, xml_info),
        "nonfinite": {
            "base_raiju_res": nonfinite_fields(paths["base_raiju_res"], RAIJU_RESTART_FIELDS),
            "proto_raiju_res": nonfinite_fields(paths["proto_raiju_res"], RAIJU_RESTART_FIELDS),
            "base_gam_res": nonfinite_fields(paths["base_gam_res"], GAM_RESTART_FIELDS),
            "proto_gam_res": nonfinite_fields(paths["proto_gam_res"], GAM_RESTART_FIELDS),
        },
        "final_restart_recommended_vs_baseline": {
            "raiju": dataset_compare(paths["proto_raiju_res"], paths["base_raiju_res"], RAIJU_RESTART_FIELDS),
            "gam": dataset_compare(paths["proto_gam_res"], paths["base_gam_res"], GAM_RESTART_FIELDS),
        },
        "history_last_steps": {
            "raiju": raiju_step,
            "gam": gam_step,
        },
        "final_history_recommended_vs_baseline": {
            "raiju": history_compare(paths["proto_raiju_history"], paths["base_raiju_history"], raiju_step, RAIJU_HISTORY_FIELDS),
            "gam": history_compare(paths["proto_gam_history"], paths["base_gam_history"], gam_step, GAM_HISTORY_FIELDS),
        },
    }
    return result


def fmt_value(value):
    if value is None:
        return "None"
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return "{:.17g}".format(value)
    return str(value)


def render_text(result):
    lines = []
    lines.append("SAMI3 RAIJU recommended {} summary".format(result["label"]))
    lines.append("run_dir {}".format(result["run_dir"]))
    if result.get("job_id"):
        lines.append("jobid {}".format(result["job_id"]))
    if result.get("sacct"):
        lines.append("sacct")
        for line in result["sacct"].strip().splitlines():
            lines.append("  {}".format(line))
    for field in RAICPL_FIELDS:
        stats = result["formula_checks"][field]
        lines.append("{}_formula_max_abs {}".format(field, fmt_value(stats["formula_max_abs"])))
        lines.append("{}_formula_max_rel {}".format(field, fmt_value(stats["formula_max_rel"])))
        lines.append("{}_actual_mean {}".format(field, fmt_value(stats["actual_mean"])))
        lines.append("{}_actual_max {}".format(field, fmt_value(stats["actual_max"])))
    for key, value in result["nonfinite"].items():
        lines.append("nonfinite_physics_{} {}".format(key, json.dumps(value, sort_keys=True)))
    lines.append("final_restart_recommended_vs_baseline")
    for group in ("raiju", "gam"):
        for name, stats in result["final_restart_recommended_vs_baseline"][group].items():
            if stats.get("missing"):
                lines.append("{}/{} missing".format(group, name))
                continue
            lines.append(
                "{} max_abs={} mean_abs={} recommended_mean={} baseline_mean={}".format(
                    name,
                    fmt_value(stats["max_abs"]),
                    fmt_value(stats["mean_abs"]),
                    fmt_value(stats["recommended_mean"]),
                    fmt_value(stats["baseline_mean"]),
                )
            )
    lines.append("history_last_steps")
    lines.append("raiju_history_last_step {}".format(result["history_last_steps"]["raiju"]))
    lines.append("gam_history_last_step {}".format(result["history_last_steps"]["gam"]))
    lines.append("final_history_recommended_vs_baseline")
    for group in ("raiju", "gam"):
        for name, stats in result["final_history_recommended_vs_baseline"][group].items():
            if stats.get("missing"):
                lines.append("{}/{} missing".format(group, name))
                continue
            lines.append(
                "{} max_abs={} mean_abs={} recommended_mean={} baseline_mean={}".format(
                    name,
                    fmt_value(stats["max_abs"]),
                    fmt_value(stats["mean_abs"]),
                    fmt_value(stats["recommended_mean"]),
                    fmt_value(stats["baseline_mean"]),
                )
            )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--json-output", default=None)
    parser.add_argument("--text-output", default=None)
    args = parser.parse_args()

    result = summarize(args)
    text = render_text(result)
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if args.text_output:
        Path(args.text_output).write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
