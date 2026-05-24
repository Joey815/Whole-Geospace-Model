#!/usr/bin/env python3
"""Archive small evidence from a SAMI3 -> RAIJU/GAMERA long-run smoke."""

import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def run_checked(cmd, stdout_path):
    with stdout_path.open("w") as fp:
        proc = subprocess.run(cmd, stdout=fp, stderr=subprocess.STDOUT, universal_newlines=True)
    return proc.returncode


def copy_if_exists(src, archive_dir, copied):
    if src.is_file():
        dst = archive_dir / src.name
        shutil.copy2(str(src), str(dst))
        copied.append({"source": str(src), "archive": str(dst), "bytes": dst.stat().st_size})


def collect_files(run_dir, label, include_existing_summary):
    names = [
        "base_control_{0}.log".format(label),
        "dsB_lmlt_recommended_{0}.log".format(label),
        "tinyCase_base_control_{0}.xml".format(label),
        "tinyCase_sami3_moments_dsB_lmlt_recommended_{0}.xml".format(label),
    ]
    if include_existing_summary:
        names.append("recommended_{0}_summary.txt".format(label))
    files = [run_dir / name for name in names]
    files.extend(sorted(run_dir.glob("slurm-*.out")))
    return files


def write_sacct(job_id, archive_dir):
    if not job_id:
        return None
    out = archive_dir / "sacct_{}.txt".format(job_id)
    cmd = [
        "sacct",
        "-j",
        str(job_id),
        "--format=JobID,JobName,State,ExitCode,Elapsed,NodeList,MaxRSS",
        "-P",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    out.write_text(proc.stdout)
    return {"path": str(out), "returncode": proc.returncode}


def parse_moment_product(run_dir, label):
    xml_path = run_dir / "tinyCase_sami3_moments_dsB_lmlt_recommended_{}.xml".format(label)
    if not xml_path.is_file():
        return None
    tree = ET.parse(str(xml_path))
    elem = tree.find(".//sami3Moments")
    if elem is None:
        return None
    return elem.attrib.get("file")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--archive-dir", required=True)
    parser.add_argument("--label", required=True, help="Run label such as long900 or long1800")
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--summary-python", default="/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python")
    parser.add_argument("--mapping-python", default="/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python")
    parser.add_argument("--skip-summary", action="store_true")
    parser.add_argument("--formula-abs-tol", type=float, default=1.0e-12)
    parser.add_argument("--formula-rel-tol", type=float, default=1.0e-12)
    parser.add_argument("--skip-mapping-product", action="store_true")
    parser.add_argument("--expect-mapping-mode", default="l_mlt")
    parser.add_argument("--min-mapping-valid-fraction", type=float, default=1.0)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    run_dir = Path(args.run_dir).expanduser().resolve()
    archive_dir = Path(args.archive_dir).expanduser()
    archive_dir.mkdir(parents=True, exist_ok=True)

    validator_json = archive_dir / "validate_sami3_raiju_longrun.json"
    validator_txt = archive_dir / "validate_sami3_raiju_longrun.txt"
    cmd = [
        sys.executable,
        str(repo / "scripts" / "validate_sami3_raiju_longrun.py"),
        "--run-dir",
        str(run_dir),
        "--label",
        args.label,
        "--expect-slurm",
        "--json-output",
        str(validator_json),
    ]
    if args.allow_incomplete:
        cmd.append("--allow-incomplete")
    validator_rc = run_checked(cmd, validator_txt)

    summary_info = None
    if not args.skip_summary and not args.allow_incomplete:
        summary_stdout = archive_dir / "summarize_sami3_raiju_longrun.stdout.txt"
        summary_json = archive_dir / "recommended_{}_summary.json".format(args.label)
        summary_txt = archive_dir / "recommended_{}_summary.txt".format(args.label)
        summary_cmd = [
            args.summary_python,
            str(repo / "scripts" / "summarize_sami3_raiju_longrun.py"),
            "--run-dir",
            str(run_dir),
            "--label",
            args.label,
            "--json-output",
            str(summary_json),
            "--text-output",
            str(summary_txt),
        ]
        if args.job_id:
            summary_cmd.extend(["--job-id", str(args.job_id)])
        summary_rc = run_checked(summary_cmd, summary_stdout)
        summary_validate_stdout = archive_dir / "validate_sami3_raiju_summary.txt"
        summary_validate_json = archive_dir / "validate_sami3_raiju_summary.json"
        summary_validate_cmd = [
            sys.executable,
            str(repo / "scripts" / "validate_sami3_raiju_summary.py"),
            "--summary-json",
            str(summary_json),
            "--formula-abs-tol",
            str(args.formula_abs_tol),
            "--formula-rel-tol",
            str(args.formula_rel_tol),
            "--require-positive-inputs",
            "--require-matching-history-step",
            "--json-output",
            str(summary_validate_json),
        ]
        summary_validate_rc = run_checked(summary_validate_cmd, summary_validate_stdout)
        summary_info = {
            "returncode": summary_rc,
            "stdout": str(summary_stdout),
            "json": str(summary_json),
            "text": str(summary_txt),
            "validation_returncode": summary_validate_rc,
            "validation_text": str(summary_validate_stdout),
            "validation_json": str(summary_validate_json),
            "python": args.summary_python,
        }

    mapping_info = None
    if not args.skip_mapping_product:
        product = parse_moment_product(run_dir, args.label)
        mapping_json = archive_dir / "validate_sami3_raiju_mapping_product.json"
        mapping_txt = archive_dir / "validate_sami3_raiju_mapping_product.txt"
        if product:
            mapping_cmd = [
                args.mapping_python,
                str(repo / "scripts" / "validate_sami3_raiju_mapping_product.py"),
                "--product-h5",
                product,
                "--expect-mapping-mode",
                args.expect_mapping_mode,
                "--min-valid-fraction",
                str(args.min_mapping_valid_fraction),
                "--json-output",
                str(mapping_json),
            ]
            mapping_rc = run_checked(mapping_cmd, mapping_txt)
        else:
            mapping_txt.write_text("missing sami3Moments product in XML\n")
            mapping_json.write_text(json.dumps({"ok": False, "error": "missing sami3Moments product in XML"}, indent=2) + "\n")
            mapping_rc = 1
        mapping_info = {
            "returncode": mapping_rc,
            "text": str(mapping_txt),
            "json": str(mapping_json),
            "python": args.mapping_python,
            "product_h5": product,
            "expect_mapping_mode": args.expect_mapping_mode,
            "min_valid_fraction": args.min_mapping_valid_fraction,
        }

    copied = []
    include_existing_summary = args.skip_summary or args.allow_incomplete
    for path in collect_files(run_dir, args.label, include_existing_summary):
        copy_if_exists(path, archive_dir, copied)
    sacct = write_sacct(args.job_id, archive_dir)

    archive_ok = (
        validator_rc == 0
        and (
            summary_info is None
            or (summary_info["returncode"] == 0 and summary_info["validation_returncode"] == 0)
        )
        and (mapping_info is None or mapping_info["returncode"] == 0)
    )
    summary = {
        "ok": archive_ok,
        "run_dir": str(run_dir),
        "archive_dir": str(archive_dir),
        "label": args.label,
        "job_id": args.job_id,
        "validator": {
            "returncode": validator_rc,
            "text": str(validator_txt),
            "json": str(validator_json),
        },
        "summary": summary_info,
        "mapping_product": mapping_info,
        "copied_files": copied,
        "sacct": sacct,
    }
    (archive_dir / "archive_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    lines = [
        "# SAMI3 -> RAIJU/GAMERA Longrun Archive Summary",
        "",
        "run_dir: {}".format(run_dir),
        "label: {}".format(args.label),
        "job_id: {}".format(args.job_id if args.job_id else ""),
        "validator_returncode: {}".format(validator_rc),
        "summary_returncode: {}".format(summary_info["returncode"] if summary_info else ""),
        "summary_validation_returncode: {}".format(summary_info["validation_returncode"] if summary_info else ""),
        "mapping_product_returncode: {}".format(mapping_info["returncode"] if mapping_info else ""),
        "copied_files: {}".format(len(copied)),
        "overall: {}".format("ok" if summary["ok"] else "FAIL"),
        "",
        "Validator text output:",
        "",
        "- validate_sami3_raiju_longrun.txt",
        "- validate_sami3_raiju_summary.txt",
        "- validate_sami3_raiju_mapping_product.txt",
    ]
    (archive_dir / "README.md").write_text("\n".join(lines) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
