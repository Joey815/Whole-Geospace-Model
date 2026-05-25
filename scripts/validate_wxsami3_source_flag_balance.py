#!/usr/bin/env python3
"""Validate WACCM-X/SAMI3 source-flag and top-blend count balance.

This validator is intentionally receiver-log driven.  It checks that the
source-flag totals received by SAMI3 and the per-shell apply diagnostics close
against the live-packet metadata written by the WACCM-X sender.
"""

import argparse
import json
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text())


def read_text(path):
    try:
        return Path(path).read_text(errors="replace")
    except OSError:
        return ""


def add(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def parse_numeric_lines(text, marker):
    rows = []
    for line in text.splitlines():
        if marker not in line:
            continue
        values = []
        for token in line.split(marker, 1)[1].split():
            try:
                values.append(float(token))
            except ValueError:
                pass
        rows.append(values)
    return rows


def sum_columns(rows, expected_len):
    sums = [0.0] * expected_len
    valid = []
    for row in rows:
        if len(row) != expected_len:
            continue
        valid.append(row)
        for idx, value in enumerate(row):
            sums[idx] += value
    return valid, sums


def close_int(actual, expected):
    return int(round(actual)) == int(expected)


def close_float(actual, expected, tol):
    return abs(float(actual) - float(expected)) <= tol


def int_detail(actual, expected):
    return "actual={} expected={}".format(int(round(actual)), int(expected))


def filter_packet_rows(rows, packet_index=None, packet_col=None, packet_hour=None, hour_col=None, hour_tol=1.0e-6):
    filtered = []
    for row in rows:
        keep = True
        if packet_index is not None and packet_col is not None:
            keep = keep and len(row) > packet_col and int(round(row[packet_col])) == int(packet_index)
        if packet_hour is not None and hour_col is not None:
            keep = keep and len(row) > hour_col and close_float(row[hour_col], packet_hour, hour_tol)
        if keep:
            filtered.append(row)
    return filtered


def validate(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    receiver_log = Path(args.receiver_log).expanduser().resolve() if args.receiver_log else run_dir / "sami3_online_receiver.out"
    meta_path = Path(args.meta).expanduser().resolve() if args.meta else run_dir / "wxsami3_live_meta.json"

    checks = []
    meta = {"run_dir": str(run_dir), "receiver_log": str(receiver_log), "meta": str(meta_path)}
    text = read_text(receiver_log)
    add(checks, "receiver_log_exists", bool(text) or args.allow_incomplete, receiver_log)
    if not text:
        return checks, meta

    sender_meta = {}
    if meta_path.is_file():
        sender_meta = read_json(meta_path)
    add(checks, "live_meta_exists", bool(sender_meta) or args.allow_incomplete, meta_path)

    source_flags = sender_meta.get("source_flags", {})
    checksum = sender_meta.get("sender_checksum", {})
    runtime_qc = sender_meta.get("runtime_qc", {})
    selected_packet_index = args.packet_index
    if selected_packet_index is None and sender_meta and sender_meta.get("packet_index") is not None:
        selected_packet_index = int(sender_meta["packet_index"])
    selected_packet_hour = args.packet_hour
    if selected_packet_hour is None and sender_meta and sender_meta.get("packet_hour") is not None:
        selected_packet_hour = float(sender_meta["packet_hour"])
    expected_samples = int(runtime_qc.get("samples", 0))
    expected_valid = int(source_flags.get("WACCMX_VALID", 0))
    expected_above = int(source_flags.get("SAMI3_NATIVE_ABOVE_TOP", 0))
    expected_n2 = int(source_flags.get("SAMI3_NATIVE_N2_INVALID", 0))
    expected_other = int(source_flags.get("SAMI3_NATIVE_OTHER_INVALID", 0))
    expected_invalid = int(runtime_qc.get("invalid", expected_above + expected_n2 + expected_other))

    recv_source_rows = parse_numeric_lines(text, "WACCMX_RECV_SOURCE_FLAGS")
    apply_source_rows = parse_numeric_lines(text, "WACCMX_APPLY_SOURCE_FLAGS")
    apply_qc_rows = parse_numeric_lines(text, "WACCMX_APPLY_QC")
    apply_blend_rows = parse_numeric_lines(text, "WACCMX_APPLY_BLEND")

    recv_source_rows = filter_packet_rows(
        recv_source_rows,
        packet_index=selected_packet_index,
        packet_col=1,
        packet_hour=selected_packet_hour,
        hour_col=2,
        hour_tol=args.packet_hour_tol,
    )
    apply_source_rows = filter_packet_rows(
        apply_source_rows,
        packet_hour=selected_packet_hour,
        hour_col=2,
        hour_tol=args.packet_hour_tol,
    )
    apply_qc_rows = filter_packet_rows(
        apply_qc_rows,
        packet_hour=selected_packet_hour,
        hour_col=2,
        hour_tol=args.packet_hour_tol,
    )
    apply_blend_rows = filter_packet_rows(
        apply_blend_rows,
        packet_hour=selected_packet_hour,
        hour_col=2,
        hour_tol=args.packet_hour_tol,
    )

    recv_rows, recv_sum = sum_columns(recv_source_rows, 17)
    apply_rows, apply_sum = sum_columns(apply_source_rows, 9)
    qc_rows, qc_sum = sum_columns(apply_qc_rows, 12)
    blend_rows, blend_sum = sum_columns(apply_blend_rows, 13)

    meta["line_counts"] = {
        "recv_source_flags": len(recv_rows),
        "apply_source_flags": len(apply_rows),
        "apply_qc": len(qc_rows),
        "apply_blend": len(blend_rows),
    }
    meta["selected_packet_index"] = selected_packet_index
    meta["selected_packet_hour"] = selected_packet_hour
    add(
        checks,
        "recv_source_flag_lines",
        len(recv_rows) >= args.expected_sami3_workers or args.allow_incomplete,
        "lines={} expected_min={}".format(len(recv_rows), args.expected_sami3_workers),
    )
    if args.expected_nl is not None:
        expected_apply = args.expected_sami3_workers * args.expected_nl
        add(
            checks,
            "apply_source_flag_lines",
            len(apply_rows) == expected_apply or args.allow_incomplete,
            "lines={} expected={}".format(len(apply_rows), expected_apply),
        )
        add(
            checks,
            "apply_qc_lines",
            len(qc_rows) == expected_apply or args.allow_incomplete,
            "lines={} expected={}".format(len(qc_rows), expected_apply),
        )
        add(
            checks,
            "apply_blend_lines",
            len(blend_rows) == expected_apply or args.allow_incomplete,
            "lines={} expected={}".format(len(blend_rows), expected_apply),
        )

    if sender_meta:
        # WACCMX_RECV_SOURCE_FLAGS:
        # taskid, packet, hour, nlocal, valid, above, n2, other, unknown,
        # valid_i, invalid_i, valid_f, invalid_f, he_i, he_f, wzero_i, wzero_f
        add(checks, "recv_samples_match_meta", close_int(recv_sum[3], expected_samples), int_detail(recv_sum[3], expected_samples))
        add(checks, "recv_valid_match_meta", close_int(recv_sum[4], expected_valid), int_detail(recv_sum[4], expected_valid))
        add(checks, "recv_above_top_match_meta", close_int(recv_sum[5], expected_above), int_detail(recv_sum[5], expected_above))
        add(checks, "recv_n2_invalid_match_meta", close_int(recv_sum[6], expected_n2), int_detail(recv_sum[6], expected_n2))
        add(checks, "recv_other_invalid_match_meta", close_int(recv_sum[7], expected_other), int_detail(recv_sum[7], expected_other))
        add(checks, "recv_unknown_zero", int(round(recv_sum[8])) == 0, "unknown={}".format(int(round(recv_sum[8]))))
        add(checks, "recv_valid_i_match_checksum", close_int(recv_sum[9], checksum.get("valid_i", expected_valid)), int_detail(recv_sum[9], checksum.get("valid_i", expected_valid)))
        add(checks, "recv_invalid_i_match_checksum", close_int(recv_sum[10], checksum.get("invalid_i", expected_invalid)), int_detail(recv_sum[10], checksum.get("invalid_i", expected_invalid)))
        add(checks, "recv_valid_f_match_checksum", close_int(recv_sum[11], checksum.get("valid_f", expected_valid)), int_detail(recv_sum[11], checksum.get("valid_f", expected_valid)))
        add(checks, "recv_invalid_f_match_checksum", close_int(recv_sum[12], checksum.get("invalid_f", expected_invalid)), int_detail(recv_sum[12], checksum.get("invalid_f", expected_invalid)))
        add(checks, "recv_he_native_matches_valid", close_int(recv_sum[13], expected_valid) and close_int(recv_sum[14], expected_valid), "he_i={} he_f={} valid={}".format(int(round(recv_sum[13])), int(round(recv_sum[14])), expected_valid))
        add(checks, "recv_w_zero_matches_valid", close_int(recv_sum[15], expected_valid) and close_int(recv_sum[16], expected_valid), "w_i={} w_f={} valid={}".format(int(round(recv_sum[15])), int(round(recv_sum[16])), expected_valid))

        # WACCMX_APPLY_SOURCE_FLAGS: taskid, nll, hour, nplane, valid, above,
        # n2, other, unknown
        add(checks, "apply_samples_match_meta", close_int(apply_sum[3], expected_samples), int_detail(apply_sum[3], expected_samples))
        add(checks, "apply_valid_match_meta", close_int(apply_sum[4], expected_valid), int_detail(apply_sum[4], expected_valid))
        add(checks, "apply_above_top_match_meta", close_int(apply_sum[5], expected_above), int_detail(apply_sum[5], expected_above))
        add(checks, "apply_n2_invalid_match_meta", close_int(apply_sum[6], expected_n2), int_detail(apply_sum[6], expected_n2))
        add(checks, "apply_other_invalid_match_meta", close_int(apply_sum[7], expected_other), int_detail(apply_sum[7], expected_other))
        add(checks, "apply_unknown_zero", int(round(apply_sum[8])) == 0, "unknown={}".format(int(round(apply_sum[8]))))

        # WACCMX_APPLY_QC: taskid, nll, hour, nplane, valid_i, invalid_i,
        # valid_f, invalid_f, he_i, he_f, wzero_i, wzero_f
        add(checks, "apply_qc_valid_i_match_meta", close_int(qc_sum[4], expected_valid), int_detail(qc_sum[4], expected_valid))
        add(checks, "apply_qc_invalid_i_match_meta", close_int(qc_sum[5], expected_invalid), int_detail(qc_sum[5], expected_invalid))
        add(checks, "apply_qc_valid_f_match_meta", close_int(qc_sum[6], expected_valid), int_detail(qc_sum[6], expected_valid))
        add(checks, "apply_qc_invalid_f_match_meta", close_int(qc_sum[7], expected_invalid), int_detail(qc_sum[7], expected_invalid))
        add(checks, "apply_qc_he_native_matches_valid", close_int(qc_sum[8], expected_valid) and close_int(qc_sum[9], expected_valid), "he_i={} he_f={} valid={}".format(int(round(qc_sum[8])), int(round(qc_sum[9])), expected_valid))
        add(checks, "apply_qc_w_zero_matches_valid", close_int(qc_sum[10], expected_valid) and close_int(qc_sum[11], expected_valid), "w_i={} w_f={} valid={}".format(int(round(qc_sum[10])), int(round(qc_sum[11])), expected_valid))

        # WACCMX_APPLY_BLEND: taskid, nll, hour, nplane, enabled,
        # bottom_km, top_km, full_i, blend_i, native_i, full_f, blend_f, native_f
        full_i, blend_i, native_i = blend_sum[7], blend_sum[8], blend_sum[9]
        full_f, blend_f, native_f = blend_sum[10], blend_sum[11], blend_sum[12]
        add(checks, "blend_i_partition_valid", close_int(full_i + blend_i + native_i, expected_valid), "full+blend+native={} valid={}".format(int(round(full_i + blend_i + native_i)), expected_valid))
        add(checks, "blend_f_partition_valid", close_int(full_f + blend_f + native_f, expected_valid), "full+blend+native={} valid={}".format(int(round(full_f + blend_f + native_f)), expected_valid))
        add(checks, "blend_cells_min", int(round(blend_i + blend_f)) >= args.min_total_blend_cells, "blend_i+blend_f={} min={}".format(int(round(blend_i + blend_f)), args.min_total_blend_cells))

    meta["sums"] = {
        "recv_source_flags": [int(round(value)) for value in recv_sum],
        "apply_source_flags": [int(round(value)) for value in apply_sum],
        "apply_qc": [int(round(value)) for value in qc_sum],
        "apply_blend": [int(round(value)) for value in blend_sum],
    }
    return checks, meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default=".")
    parser.add_argument("--receiver-log", default=None)
    parser.add_argument("--meta", default=None)
    parser.add_argument("--expected-sami3-workers", type=int, default=32)
    parser.add_argument("--expected-nl", type=int, default=5)
    parser.add_argument("--min-total-blend-cells", type=int, default=0)
    parser.add_argument("--packet-index", type=int, default=None)
    parser.add_argument("--packet-hour", type=float, default=None)
    parser.add_argument("--packet-hour-tol", type=float, default=1.0e-6)
    parser.add_argument("--allow-incomplete", action="store_true")
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
