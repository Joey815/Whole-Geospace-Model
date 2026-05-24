#!/usr/bin/env python3
"""Validate the WACCM-X -> SAMI3 live neutral packet contract.

This validator is intentionally evidence-driven.  It does not compare against a
later CAM history time mean.  Instead, it checks the same-call-site path:

CAM phys_state(:) live dump
-> offline replay payload generated from that live dump
-> SAMI3 receiver WACCMX_RECV_QC lines

If every replay comparison passes, the receiver-side neutral packet can be
reconstructed from the live dump written at the sender call site.
"""

import argparse
import ast
import json
import math
import re
from pathlib import Path


DEFAULT_SOURCE_COLUMNS = 144 * 96
DEFAULT_RECEIVER_RANKS = 32
DEFAULT_QC_MAX_REL = 1.0e-6


def read_text(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def read_json(path):
    with path.open() as fp:
        return json.load(fp)


def add_check(checks, name, ok, detail):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})


def count(pattern, text):
    return len(re.findall(pattern, text))


def find_first(run_dir, names):
    for name in names:
        path = run_dir / name
        if path.exists():
            return path
    return None


def collect_run_text(run_dir, paths):
    chunks = []
    for path in paths:
        if path is not None:
            chunks.append(read_text(path))
    for pattern in ("slurm-*.out", "slurm-*.err", "slurm_*.out", "slurm_*.err"):
        for path in sorted(run_dir.glob(pattern)):
            chunks.append(read_text(path))
    return "\n".join(chunk for chunk in chunks if chunk)


def parse_int_list(text):
    vals = []
    for item in text.split(","):
        item = item.strip()
        if item:
            vals.append(int(item))
    return vals


def parse_summary(path):
    text = read_text(path)
    out = {"path": str(path), "text": text, "field_stats": {}}
    m = re.search(r"files=(\d+)\s+ranks=(\d+)\s+total_cols=(\d+)", text)
    if m:
        out["files"] = int(m.group(1))
        out["ranks"] = int(m.group(2))
        out["total_cols"] = int(m.group(3))
    m = re.search(r"packets=\[([^\]]*)\]\s+nsteps=\[([^\]]*)\]", text)
    if m:
        out["packets"] = parse_int_list(m.group(1))
        out["nsteps"] = parse_int_list(m.group(2))
    out["has_bad_size_files"] = "bad_size_files=" in text
    for label, raw in re.findall(r"([A-Za-z0-9_]+)=({[^}]*})", text):
        try:
            value = ast.literal_eval(raw)
        except (SyntaxError, ValueError):
            continue
        if isinstance(value, dict):
            out["field_stats"][label] = value
    return out


def parse_replay_builder(path):
    text = read_text(path)
    out = {"path": str(path), "text": text}
    m = re.search(r"N2 negative residual mode:\s+(\S+)", text)
    if m:
        out["n2_mode"] = m.group(1)
    m = re.search(r"loaded live dump:\s+source_cols=(\d+)\s+filled=(\d+)\s+pver=(\d+)", text)
    if m:
        out["source_cols"] = int(m.group(1))
        out["filled"] = int(m.group(2))
        out["pver"] = int(m.group(3))
    for phase in ("initial", "final"):
        m = re.search(
            r"sample QC %s:.*?samples=(\d+)\s+invalid=(\d+)\s+"
            r"bad_weighted_z=(\d+)\s+above_live_top=(\d+)\s+"
            r"n2_residual_used=(\d+)\s+n2_residual_negative=(\d+)\s+"
            r"n2_residual_min=([^\s]+)\s+n2_residual_max=([^\s]+)" % phase,
            text,
        )
        if m:
            out[phase] = {
                "samples": int(m.group(1)),
                "invalid": int(m.group(2)),
                "bad_weighted_z": int(m.group(3)),
                "above_live_top": int(m.group(4)),
                "n2_residual_used": int(m.group(5)),
                "n2_residual_negative": int(m.group(6)),
                "n2_residual_min": float(m.group(7)),
                "n2_residual_max": float(m.group(8)),
            }
    m = re.search(r"wrote live-dump replay payload prefix:\s+(\S+)", text)
    if m:
        out["payload_prefix"] = m.group(1)
    return out


def parse_recv_compare(path):
    text = read_text(path)
    out = {"path": str(path), "text": text}
    m = re.search(
        r"WACCMX_RECV_QC compare ok:\s+ranks=(\d+)\s+occurrence=(\d+)\s+"
        r"step_set=\[([^\]]*)\]\s+packet_hour_set=\[([^\]]*)\]\s+"
        r"max_abs=([^\s]+)\s+max_rel=([^\s]+)",
        text,
    )
    if m:
        out["ok_marker"] = True
        out["ranks"] = int(m.group(1))
        out["occurrence"] = int(m.group(2))
        out["step_set"] = parse_int_list(m.group(3))
        out["packet_hour_set"] = [
            float(item.strip()) for item in m.group(4).split(",") if item.strip()
        ]
        out["max_abs"] = float(m.group(5))
        out["max_rel"] = float(m.group(6))
    else:
        out["ok_marker"] = False
    return out


def numeric(value):
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def close_enough(a, b, rtol, atol):
    if not (numeric(a) and numeric(b)):
        return False
    return abs(float(a) - float(b)) <= max(atol, rtol * max(abs(float(a)), abs(float(b)), 1.0))


def check_meta(checks, meta, args):
    add_check(
        checks,
        "meta_payload_version",
        meta.get("payload_version") == "wxsami3-live-payload-v2",
        meta.get("payload_version"),
    )
    add_check(
        checks,
        "meta_runtime_source",
        meta.get("runtime_source") == "CAM phys_state(:)",
        meta.get("runtime_source"),
    )
    add_check(
        checks,
        "meta_actual_transport",
        meta.get("actual_transport") == "runtime_live_packet",
        meta.get("actual_transport"),
    )
    add_check(
        checks,
        "meta_last_packet_index",
        meta.get("packet_index") == args.expected_packets - 1 or args.allow_incomplete,
        "packet_index={} expected={}".format(meta.get("packet_index"), args.expected_packets - 1),
    )
    add_check(
        checks,
        "meta_dtime_phys_positive",
        numeric(meta.get("dtime_phys_s")) and float(meta.get("dtime_phys_s")) > 0.0,
        meta.get("dtime_phys_s"),
    )
    add_check(
        checks,
        "meta_send_every_nsteps_positive",
        isinstance(meta.get("send_every_nsteps"), int) and meta.get("send_every_nsteps") > 0,
        meta.get("send_every_nsteps"),
    )
    expected_packet_hour = None
    if numeric(meta.get("dtime_phys_s")) and isinstance(meta.get("nstep"), int):
        expected_packet_hour = float(meta["nstep"]) * float(meta["dtime_phys_s"]) / 3600.0
    add_check(
        checks,
        "meta_packet_hour_matches_nstep_dtime",
        expected_packet_hour is not None
        and close_enough(meta.get("packet_hour"), expected_packet_hour, args.packet_hour_rtol, args.packet_hour_atol),
        "packet_hour={} expected={}".format(meta.get("packet_hour"), expected_packet_hour),
    )

    header = meta.get("payload_header", {})
    expected_header = {
        "magic": 20260522,
        "nz": args.expected_payload_nz,
        "nf": args.expected_payload_nf,
        "nl": args.expected_payload_nl,
        "nneut": args.expected_payload_nneut,
    }
    for key, expected in expected_header.items():
        add_check(
            checks,
            "meta_payload_header_{}".format(key),
            header.get(key) == expected,
            "{} expected={}".format(header.get(key), expected),
        )

    runtime_map = meta.get("runtime_map", {})
    add_check(
        checks,
        "meta_runtime_map_source_columns",
        runtime_map.get("source_columns") == args.expected_source_columns,
        "source_columns={} expected={}".format(
            runtime_map.get("source_columns"), args.expected_source_columns
        ),
    )
    add_check(
        checks,
        "meta_runtime_map_npoints",
        runtime_map.get("npoints", 0) > 0,
        "npoints={}".format(runtime_map.get("npoints")),
    )

    source_units = meta.get("source_units", {})
    expected_source_units = {
        "temperature": "K",
        "wind": "m/s",
        "pressure": "Pa",
        "height": "m",
        "composition": "mass_mixing_ratio",
    }
    for key, expected in expected_source_units.items():
        add_check(
            checks,
            "meta_source_unit_{}".format(key),
            source_units.get(key) == expected,
            "{} expected={}".format(source_units.get(key), expected),
        )

    payload_units = meta.get("payload_units", {})
    expected_payload_units = {
        "density": "cm^-3",
        "temperature": "K",
        "wind": "cm/s",
    }
    for key, expected in expected_payload_units.items():
        add_check(
            checks,
            "meta_payload_unit_{}".format(key),
            payload_units.get(key) == expected,
            "{} expected={}".format(payload_units.get(key), expected),
        )

    add_check(
        checks,
        "meta_density_conversion",
        "1e-6 -> cm^-3" in meta.get("density_conversion", ""),
        meta.get("density_conversion", ""),
    )
    add_check(
        checks,
        "meta_source_species_order",
        meta.get("source_species_order") == ["O", "O2", "H", "N", "NO", "N2", "He"],
        meta.get("source_species_order"),
    )
    add_check(
        checks,
        "meta_payload_species_order",
        meta.get("payload_species_order") == ["H", "O", "NO", "O2", "He", "N2", "N"],
        meta.get("payload_species_order"),
    )
    add_check(
        checks,
        "meta_source_flag_mpi_tag",
        meta.get("source_flag_mpi_tag") == 212,
        meta.get("source_flag_mpi_tag"),
    )
    expected_flag_values = {
        "WACCMX_VALID": 1,
        "SAMI3_NATIVE_ABOVE_TOP": 2,
        "SAMI3_NATIVE_N2_INVALID": 3,
        "SAMI3_NATIVE_OTHER_INVALID": 4,
    }
    add_check(
        checks,
        "meta_source_flag_values",
        meta.get("source_flag_values") == expected_flag_values,
        meta.get("source_flag_values"),
    )

    species_indices = {
        item.get("name"): item.get("index")
        for item in meta.get("source_species_indices", [])
        if isinstance(item, dict)
    }
    for name in ["O", "O2", "H", "N", "NO"]:
        add_check(
            checks,
            "meta_species_index_{}".format(name),
            isinstance(species_indices.get(name), int) and species_indices.get(name) >= 0,
            species_indices.get(name),
        )
    if args.expect_n2_residual:
        add_check(checks, "meta_species_index_N2_residual", species_indices.get("N2") == -1, species_indices.get("N2"))
    if args.expect_he_native:
        add_check(checks, "meta_species_index_He_native", species_indices.get("He") == -1, species_indices.get("He"))

    fallback = meta.get("fallback_policy", {})
    add_check(
        checks,
        "meta_n2_negative_mode",
        fallback.get("N2_negative_mode") == args.expected_n2_mode,
        fallback.get("N2_negative_mode"),
    )
    add_check(
        checks,
        "meta_he_policy",
        (not args.expect_he_native)
        or "SAMI3 native" in fallback.get("He", "")
        or "MSIS" in fallback.get("He", ""),
        fallback.get("He", ""),
    )
    add_check(
        checks,
        "meta_w_policy",
        "payload value 0" in fallback.get("W", ""),
        fallback.get("W", ""),
    )

    source_flags = meta.get("source_flags", {})
    runtime_qc = meta.get("runtime_qc", {})
    samples = runtime_qc.get("samples")
    flag_total = (
        int(source_flags.get("WACCMX_VALID", 0))
        + int(source_flags.get("SAMI3_NATIVE_ABOVE_TOP", 0))
        + int(source_flags.get("SAMI3_NATIVE_N2_INVALID", 0))
        + int(source_flags.get("SAMI3_NATIVE_OTHER_INVALID", 0))
    )
    add_check(
        checks,
        "meta_source_flags_sum",
        samples is not None and flag_total == int(samples),
        "flag_total={} samples={}".format(flag_total, samples),
    )
    add_check(
        checks,
        "meta_invalid_sum",
        runtime_qc.get("invalid")
        == int(source_flags.get("SAMI3_NATIVE_ABOVE_TOP", 0))
        + int(source_flags.get("SAMI3_NATIVE_N2_INVALID", 0))
        + int(source_flags.get("SAMI3_NATIVE_OTHER_INVALID", 0)),
        "invalid={} above+n2+other={}".format(
            runtime_qc.get("invalid"),
            int(source_flags.get("SAMI3_NATIVE_ABOVE_TOP", 0))
            + int(source_flags.get("SAMI3_NATIVE_N2_INVALID", 0))
            + int(source_flags.get("SAMI3_NATIVE_OTHER_INVALID", 0)),
        ),
    )
    add_check(
        checks,
        "meta_above_top_flag_count",
        runtime_qc.get("above_live_top") == source_flags.get("SAMI3_NATIVE_ABOVE_TOP"),
        "above_live_top={} source_flag={}".format(
            runtime_qc.get("above_live_top"), source_flags.get("SAMI3_NATIVE_ABOVE_TOP")
        ),
    )
    add_check(
        checks,
        "meta_n2_invalid_flag_count",
        runtime_qc.get("n2_residual_negative") == source_flags.get("SAMI3_NATIVE_N2_INVALID"),
        "n2_residual_negative={} source_flag={}".format(
            runtime_qc.get("n2_residual_negative"), source_flags.get("SAMI3_NATIVE_N2_INVALID")
        ),
    )
    if args.require_zero_unknown_source_flags:
        add_check(
            checks,
            "meta_other_invalid_zero",
            int(source_flags.get("SAMI3_NATIVE_OTHER_INVALID", -1)) == 0,
            source_flags.get("SAMI3_NATIVE_OTHER_INVALID"),
        )

    checksum = meta.get("sender_checksum", {})
    add_check(
        checks,
        "meta_checksum_valid_counts",
        checksum.get("valid_i") == source_flags.get("WACCMX_VALID")
        and checksum.get("valid_f") == source_flags.get("WACCMX_VALID"),
        "valid_i={} valid_f={} source_valid={}".format(
            checksum.get("valid_i"), checksum.get("valid_f"), source_flags.get("WACCMX_VALID")
        ),
    )
    add_check(
        checks,
        "meta_checksum_invalid_counts",
        checksum.get("invalid_i") == runtime_qc.get("invalid")
        and checksum.get("invalid_f") == runtime_qc.get("invalid"),
        "invalid_i={} invalid_f={} runtime_invalid={}".format(
            checksum.get("invalid_i"), checksum.get("invalid_f"), runtime_qc.get("invalid")
        ),
    )


def check_packet_artifacts(checks, meta_out, run_dir, packet, args):
    packet_tag = "pkt{:06d}".format(packet)
    summary_path = run_dir / "live_dump_summary_{}.txt".format(packet_tag)
    replay_path = run_dir / "replay_builder_{}.out".format(packet_tag)
    compare_path = run_dir / "recv_qc_compare_{}.txt".format(packet_tag)

    add_check(
        checks,
        "packet{}_summary_exists".format(packet),
        summary_path.exists() or args.allow_incomplete,
        summary_path,
    )
    add_check(
        checks,
        "packet{}_replay_exists".format(packet),
        replay_path.exists() or args.allow_incomplete,
        replay_path,
    )
    add_check(
        checks,
        "packet{}_recv_compare_exists".format(packet),
        compare_path.exists() or args.allow_incomplete,
        compare_path,
    )

    pkt_meta = {}
    if summary_path.exists():
        summary = parse_summary(summary_path)
        pkt_meta["summary"] = {k: v for k, v in summary.items() if k != "text"}
        add_check(
            checks,
            "packet{}_summary_source_columns".format(packet),
            summary.get("total_cols") == args.expected_source_columns,
            "total_cols={} expected={}".format(summary.get("total_cols"), args.expected_source_columns),
        )
        add_check(
            checks,
            "packet{}_summary_packet_index".format(packet),
            summary.get("packets") == [packet],
            "packets={}".format(summary.get("packets")),
        )
        add_check(
            checks,
            "packet{}_summary_no_bad_size_files".format(packet),
            not summary.get("has_bad_size_files"),
            "bad_size_files_present={}".format(summary.get("has_bad_size_files")),
        )
        field_stats = summary.get("field_stats", {})
        zero_bad_fields = [
            "lat_deg",
            "lon_deg",
            "T_K",
            "U_m_s",
            "V_m_s",
            "PMID_Pa",
            "ZM_m",
            "MBARV_kg_mol",
            "q_O",
            "q_O2",
            "q_H",
            "q_N",
            "q_NO",
        ]
        for label in zero_bad_fields:
            stat = field_stats.get(label, {})
            add_check(
                checks,
                "packet{}_summary_{}_bad".format(packet, label),
                stat.get("bad") == 0,
                "bad={}".format(stat.get("bad")),
            )
        cid = field_stats.get("cid", {})
        add_check(
            checks,
            "packet{}_summary_cid_coverage".format(packet),
            cid.get("missing") == 0
            and cid.get("unique") == args.expected_source_columns,
            "missing={} unique={} expected={}".format(
                cid.get("missing"), cid.get("unique"), args.expected_source_columns
            ),
        )

        range_limits = {
            "lat_deg": (-90.0, 90.0),
            "lon_deg": (0.0, 360.0),
            "T_K": (50.0, 5000.0),
            "U_m_s": (-5000.0, 5000.0),
            "V_m_s": (-5000.0, 5000.0),
            "PMID_Pa": (0.0, 2.0e5),
            "ZM_m": (-1.0e3, 2.0e6),
            "MBARV_kg_mol": (1.0, 60.0),
            "q_O": (-1.0e-12, 1.1),
            "q_O2": (-1.0e-12, 1.1),
            "q_H": (-1.0e-12, 1.1),
            "q_N": (-1.0e-12, 1.1),
            "q_NO": (-1.0e-12, 1.1),
        }
        for label, (lo, hi) in range_limits.items():
            stat = field_stats.get(label, {})
            got_min = stat.get("min")
            got_max = stat.get("max")
            add_check(
                checks,
                "packet{}_summary_{}_range".format(packet, label),
                numeric(got_min)
                and numeric(got_max)
                and float(got_min) >= lo
                and float(got_max) <= hi,
                "min={} max={} allowed=[{},{}]".format(got_min, got_max, lo, hi),
            )

    if replay_path.exists():
        replay = parse_replay_builder(replay_path)
        pkt_meta["replay"] = {k: v for k, v in replay.items() if k != "text"}
        add_check(
            checks,
            "packet{}_replay_source_coverage".format(packet),
            replay.get("source_cols") == args.expected_source_columns
            and replay.get("filled") == args.expected_source_columns,
            "source_cols={} filled={} expected={}".format(
                replay.get("source_cols"), replay.get("filled"), args.expected_source_columns
            ),
        )
        add_check(
            checks,
            "packet{}_replay_n2_mode".format(packet),
            replay.get("n2_mode") == args.expected_n2_mode,
            replay.get("n2_mode"),
        )
        final_qc = replay.get("final", {})
        initial_qc = replay.get("initial", {})
        add_check(
            checks,
            "packet{}_replay_bad_weighted_z".format(packet),
            final_qc.get("bad_weighted_z") == 0,
            "bad_weighted_z={}".format(final_qc.get("bad_weighted_z")),
        )
        add_check(
            checks,
            "packet{}_replay_samples_positive".format(packet),
            final_qc.get("samples", 0) > 0,
            "samples={}".format(final_qc.get("samples")),
        )
        for key in ("samples", "invalid", "above_live_top", "n2_residual_used", "n2_residual_negative"):
            add_check(
                checks,
                "packet{}_replay_initial_final_{}".format(packet, key),
                initial_qc.get(key) == final_qc.get(key),
                "initial={} final={}".format(initial_qc.get(key), final_qc.get(key)),
            )
        if args.expect_n2_residual:
            add_check(
                checks,
                "packet{}_replay_n2_residual_used_positive".format(packet),
                final_qc.get("n2_residual_used", 0) > 0,
                "n2_residual_used={}".format(final_qc.get("n2_residual_used")),
            )
            add_check(
                checks,
                "packet{}_replay_n2_residual_bounds".format(packet),
                numeric(final_qc.get("n2_residual_min"))
                and numeric(final_qc.get("n2_residual_max"))
                and final_qc.get("n2_residual_min") <= final_qc.get("n2_residual_max"),
                "min={} max={}".format(
                    final_qc.get("n2_residual_min"), final_qc.get("n2_residual_max")
                ),
            )

    if compare_path.exists():
        compare = parse_recv_compare(compare_path)
        pkt_meta["recv_compare"] = {k: v for k, v in compare.items() if k != "text"}
        add_check(
            checks,
            "packet{}_recv_compare_ok".format(packet),
            compare.get("ok_marker"),
            "ok_marker={}".format(compare.get("ok_marker")),
        )
        add_check(
            checks,
            "packet{}_recv_compare_ranks".format(packet),
            compare.get("ranks") == args.expected_receiver_ranks,
            "ranks={} expected={}".format(compare.get("ranks"), args.expected_receiver_ranks),
        )
        add_check(
            checks,
            "packet{}_recv_compare_occurrence".format(packet),
            compare.get("occurrence") == packet,
            "occurrence={} expected={}".format(compare.get("occurrence"), packet),
        )
        add_check(
            checks,
            "packet{}_recv_compare_max_rel".format(packet),
            compare.get("max_rel", float("inf")) <= args.max_qc_rel,
            "max_rel={} limit={}".format(compare.get("max_rel"), args.max_qc_rel),
        )

    meta_out.setdefault("packets", {})[str(packet)] = pkt_meta


def validate(args):
    run_dir = Path(args.run_dir).expanduser().resolve()
    checks = []
    meta_out = {"run_dir": str(run_dir)}

    add_check(checks, "run_dir_exists", run_dir.is_dir() or args.allow_incomplete, run_dir)
    if not run_dir.is_dir():
        return checks, meta_out

    waccmx_log = find_first(run_dir, ["waccmx_cesm.out"])
    sami3_log = find_first(run_dir, ["sami3_online_receiver.out"])
    text = collect_run_text(run_dir, [waccmx_log, sami3_log])
    meta_out["logs"] = {
        "waccmx_cesm": str(waccmx_log) if waccmx_log else None,
        "sami3_online_receiver": str(sami3_log) if sami3_log else None,
    }

    meta_path = run_dir / "wxsami3_live_meta.json"
    add_check(checks, "live_meta_exists", meta_path.exists() or args.allow_incomplete, meta_path)
    if meta_path.exists():
        live_meta = read_json(meta_path)
        meta_out["live_meta"] = live_meta
        check_meta(checks, live_meta, args)

    for packet in range(args.expected_packets):
        check_packet_artifacts(checks, meta_out, run_dir, packet, args)

    sent_packets = count(r"WXSAMI3 sent live neutral packet:", text)
    recv_qc_lines = count(r"WACCMX_RECV_QC", text)
    add_check(
        checks,
        "sender_live_packet_count",
        sent_packets >= args.expected_packets or args.allow_incomplete,
        "sent_packets={} expected={}".format(sent_packets, args.expected_packets),
    )
    add_check(
        checks,
        "receiver_qc_line_count",
        recv_qc_lines >= args.expected_packets * args.expected_receiver_ranks
        or args.allow_incomplete,
        "qc_lines={} expected_min={}".format(
            recv_qc_lines, args.expected_packets * args.expected_receiver_ranks
        ),
    )
    add_check(
        checks,
        "sami3_done",
        "MASTER: All Done!" in text or args.allow_incomplete,
        "present={}".format("MASTER: All Done!" in text),
    )
    add_check(
        checks,
        "waccmx_done",
        "END OF MODEL RUN" in text or args.allow_incomplete,
        "present={}".format("END OF MODEL RUN" in text),
    )

    fatal = re.findall(r"(?:ERROR|FATAL|forrtl|Abort|header mismatch)", text, re.IGNORECASE)
    add_check(checks, "fatal_markers_absent", len(fatal) == 0, "matches={}".format(len(fatal)))
    return checks, meta_out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--expected-packets", type=int, default=1)
    parser.add_argument("--expected-source-columns", type=int, default=DEFAULT_SOURCE_COLUMNS)
    parser.add_argument("--expected-receiver-ranks", type=int, default=DEFAULT_RECEIVER_RANKS)
    parser.add_argument("--expected-payload-nz", type=int, default=304)
    parser.add_argument("--expected-payload-nf", type=int, default=124)
    parser.add_argument("--expected-payload-nl", type=int, default=5)
    parser.add_argument("--expected-payload-nneut", type=int, default=7)
    parser.add_argument("--expected-n2-mode", default="invalid", choices=["floor", "invalid", "fail"])
    parser.add_argument("--expect-n2-residual", action="store_true", default=True)
    parser.add_argument("--expect-he-native", action="store_true", default=True)
    parser.add_argument("--require-zero-unknown-source-flags", action="store_true")
    parser.add_argument("--max-qc-rel", type=float, default=DEFAULT_QC_MAX_REL)
    parser.add_argument("--packet-hour-rtol", type=float, default=1.0e-7)
    parser.add_argument("--packet-hour-atol", type=float, default=1.0e-7)
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    checks, meta = validate(args)
    ok = all(check["ok"] for check in checks)
    result = {"ok": ok, "checks": checks, "meta": meta}
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    for check in checks:
        status = "ok" if check["ok"] else "FAIL"
        print("{:4s} {}: {}".format(status, check["name"], check["detail"]))
    print("overall={}".format("ok" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
