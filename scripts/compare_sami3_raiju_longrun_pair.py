#!/usr/bin/env python3
"""Compare two SAMI3 -> RAIJU/GAMERA longrun prototype outputs."""

import argparse
import json
import re
from pathlib import Path

import h5py
import numpy as np


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
    arr = np.asarray(values, dtype=np.float64)
    finite = np.isfinite(arr)
    if not finite.any():
        return {"mean": None, "max": None, "nonfinite": int(arr.size)}
    vals = arr[finite]
    return {
        "mean": float(vals.mean()),
        "max": float(vals.max()),
        "nonfinite": int(arr.size - np.count_nonzero(finite)),
    }


def compare_arrays(a, b):
    av = np.asarray(a, dtype=np.float64)
    bv = np.asarray(b, dtype=np.float64)
    diff = np.abs(av - bv)
    finite = np.isfinite(diff)
    if not finite.any():
        return {"max_abs": None, "mean_abs": None, "max_rel": None}
    rel = diff / np.maximum(np.abs(bv), 1.0e-300)
    return {
        "max_abs": float(np.nanmax(diff)),
        "mean_abs": float(np.nanmean(diff)),
        "max_rel": float(np.nanmax(rel)),
    }


def last_step_name(path):
    step_re = re.compile(r"^Step#(\d+)$")
    last = None
    with h5py.File(str(path), "r") as h5:
        for key in h5.keys():
            match = step_re.match(key)
            if match is None:
                continue
            value = int(match.group(1))
            if last is None or value > last:
                last = value
    return None if last is None else "Step#{}".format(last)


def compare_datasets(path_a, path_b, names):
    out = {}
    with h5py.File(str(path_a), "r") as a, h5py.File(str(path_b), "r") as b:
        for name in names:
            if name not in a or name not in b:
                out[name] = {"missing": True}
                continue
            stats = compare_arrays(a[name][...], b[name][...])
            stats["a_mean"] = finite_stats(a[name][...])["mean"]
            stats["b_mean"] = finite_stats(b[name][...])["mean"]
            out[name] = stats
    return out


def compare_history(path_a, path_b, step, names):
    if step is None:
        return {}
    return compare_datasets(
        path_a,
        path_b,
        ["{}/{}".format(step, name) for name in names],
    )


def output_paths(run_dir, label):
    prefix = run_dir / "sami3_moments_dsB_lmlt_recommended_{}".format(label)
    return {
        "raiju_res": Path(str(prefix) + ".raiju.Res.00000.h5"),
        "gam_res": Path(str(prefix) + ".gam.Res.00000.h5"),
        "raiju_history": Path(str(prefix) + ".raiju.h5"),
        "gam_history": Path(str(prefix) + ".gam.h5"),
    }


def require_paths(paths):
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing required files: {}".format(", ".join(missing)))


def render(result):
    lines = []
    lines.append("{}_vs_{}".format(result["a_name"], result["b_name"]))
    lines.append("run_dir {}".format(result["run_dir"]))
    lines.append("a_label {}".format(result["a_label"]))
    lines.append("b_label {}".format(result["b_label"]))
    lines.append("history_steps a_raiju={} b_raiju={} a_gam={} b_gam={}".format(
        result["history_steps"]["a_raiju"],
        result["history_steps"]["b_raiju"],
        result["history_steps"]["a_gam"],
        result["history_steps"]["b_gam"],
    ))
    for section in (
        "final_restart_raiju",
        "final_restart_gam",
        "history_raiju",
        "history_gam",
    ):
        lines.append(section)
        for name, stats in result[section].items():
            if stats.get("missing"):
                lines.append("  {} missing".format(name))
            else:
                lines.append(
                    "  {} max_abs={} mean_abs={} max_rel={} a_mean={} b_mean={}".format(
                        name,
                        stats["max_abs"],
                        stats["mean_abs"],
                        stats["max_rel"],
                        stats["a_mean"],
                        stats["b_mean"],
                    )
                )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--a-label", required=True)
    parser.add_argument("--b-label", required=True)
    parser.add_argument("--a-name", default="run_a")
    parser.add_argument("--b-name", default="run_b")
    parser.add_argument("--json-output")
    parser.add_argument("--text-output")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    a_paths = output_paths(run_dir, args.a_label)
    b_paths = output_paths(run_dir, args.b_label)
    require_paths(a_paths)
    require_paths(b_paths)

    a_raiju_step = last_step_name(a_paths["raiju_history"])
    b_raiju_step = last_step_name(b_paths["raiju_history"])
    a_gam_step = last_step_name(a_paths["gam_history"])
    b_gam_step = last_step_name(b_paths["gam_history"])
    raiju_step = a_raiju_step if a_raiju_step == b_raiju_step else None
    gam_step = a_gam_step if a_gam_step == b_gam_step else None

    result = {
        "run_dir": str(run_dir),
        "a_label": args.a_label,
        "b_label": args.b_label,
        "a_name": args.a_name,
        "b_name": args.b_name,
        "history_steps": {
            "a_raiju": a_raiju_step,
            "b_raiju": b_raiju_step,
            "a_gam": a_gam_step,
            "b_gam": b_gam_step,
        },
        "final_restart_raiju": compare_datasets(a_paths["raiju_res"], b_paths["raiju_res"], RAIJU_RESTART_FIELDS),
        "final_restart_gam": compare_datasets(a_paths["gam_res"], b_paths["gam_res"], GAM_RESTART_FIELDS),
        "history_raiju": compare_history(a_paths["raiju_history"], b_paths["raiju_history"], raiju_step, RAIJU_HISTORY_FIELDS),
        "history_gam": compare_history(a_paths["gam_history"], b_paths["gam_history"], gam_step, GAM_HISTORY_FIELDS),
    }
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    text = render(result)
    if args.text_output:
        Path(args.text_output).write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
