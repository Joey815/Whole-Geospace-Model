#!/usr/bin/env python3
"""Compare SAMI3 receiver-side WACCMX_RECV_QC lines with payload binaries."""

from __future__ import print_function

import argparse
import glob
import math
import os
import struct
import sys

import numpy as np


NZ = 304
NF = 124
NL = 5
NNEUT = 7
MAGIC = 20260522

NLOCAL = NZ * NF * NL
NLOCAL4 = NLOCAL * NNEUT

FIELDS = [
    "sum_denni",
    "sum_tni",
    "sum_ui",
    "sum_vi",
    "sum_wi",
    "sum_dennf",
    "sum_tnf",
    "sum_uf",
    "sum_vf",
    "sum_wf",
]


def read_payload(prefix, rank):
    path = "{}{:04d}.bin".format(prefix, rank)
    if not os.path.exists(path):
        raise RuntimeError("missing payload file: {}".format(path))
    with open(path, "rb") as fp:
        header = struct.unpack("5i", fp.read(20))
        if header != (MAGIC, NZ, NF, NL, NNEUT):
            raise RuntimeError("bad header in {}: {}".format(path, header))
        denni = np.fromfile(fp, dtype=np.float32, count=NLOCAL4)
        tni = np.fromfile(fp, dtype=np.float32, count=NLOCAL)
        ui = np.fromfile(fp, dtype=np.float32, count=NLOCAL)
        vi = np.fromfile(fp, dtype=np.float32, count=NLOCAL)
        wi = np.fromfile(fp, dtype=np.float32, count=NLOCAL)
        dennf = np.fromfile(fp, dtype=np.float32, count=NLOCAL4)
        tnf = np.fromfile(fp, dtype=np.float32, count=NLOCAL)
        uf = np.fromfile(fp, dtype=np.float32, count=NLOCAL)
        vf = np.fromfile(fp, dtype=np.float32, count=NLOCAL)
        wf = np.fromfile(fp, dtype=np.float32, count=NLOCAL)
    arrays = [denni, tni, ui, vi, wi, dennf, tnf, uf, vf, wf]
    expected_sizes = [NLOCAL4, NLOCAL, NLOCAL, NLOCAL, NLOCAL,
                      NLOCAL4, NLOCAL, NLOCAL, NLOCAL, NLOCAL]
    for name, arr, size in zip(["denni", "tni", "ui", "vi", "wi",
                                "dennf", "tnf", "uf", "vf", "wf"],
                               arrays, expected_sizes):
        if arr.size != size:
            raise RuntimeError("{} in {} has {} values, expected {}".format(
                name, path, arr.size, size))

    pth_i = denni.reshape((NNEUT, NL, NF, NZ))[0]
    pth_f = dennf.reshape((NNEUT, NL, NF, NZ))[0]
    out = {
        "valid_i": int((pth_i >= 0.0).sum()),
        "invalid_i": int((pth_i < 0.0).sum()),
        "valid_f": int((pth_f >= 0.0).sum()),
        "invalid_f": int((pth_f < 0.0).sum()),
    }
    for name, arr in zip(FIELDS, arrays):
        out[name] = float(arr.astype(np.float64).sum())
    return out


def parse_qc(log_path):
    qc = {}
    with open(log_path, "r") as fp:
        for line in fp:
            if "WACCMX_RECV_QC" not in line:
                continue
            parts = line.split()
            idx = parts.index("WACCMX_RECV_QC")
            vals = parts[idx + 1:]
            if len(vals) < 17:
                raise RuntimeError("short WACCMX_RECV_QC line: {}".format(line.rstrip()))
            task = int(vals[0])
            entry = {
                "step": int(vals[1]),
                "packet_hour": float(vals[2]),
                "valid_i": int(vals[3]),
                "invalid_i": int(vals[4]),
                "valid_f": int(vals[5]),
                "invalid_f": int(vals[6]),
            }
            for name, value in zip(FIELDS, vals[7:17]):
                entry[name] = float(value.replace("D", "E"))
            qc.setdefault(task, []).append(entry)
    return qc


def close_enough(a, b, rtol, atol):
    if not (math.isfinite(a) and math.isfinite(b)):
        return False
    return abs(a - b) <= max(atol, rtol * max(abs(a), abs(b), 1.0))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload-prefix", required=True,
                        help="payload prefix ending in waccmx_neutral_rank")
    parser.add_argument("--receiver-log", required=True,
                        help="SAMI3 receiver stdout containing WACCMX_RECV_QC lines")
    parser.add_argument("--packet-occurrence", type=int, default=0,
                        help="0-based WACCMX_RECV_QC occurrence per task to compare")
    parser.add_argument("--rtol", type=float, default=1.0e-6)
    parser.add_argument("--atol", type=float, default=1.0e-2)
    args = parser.parse_args(argv)

    qc = parse_qc(args.receiver_log)
    expected_tasks = set(range(1, 33))
    got_tasks = set(qc)
    if got_tasks != expected_tasks:
        missing = sorted(expected_tasks - got_tasks)
        extra = sorted(got_tasks - expected_tasks)
        raise SystemExit("bad task set missing={} extra={}".format(missing, extra))
    if args.packet_occurrence < 0:
        raise SystemExit("--packet-occurrence must be >= 0")

    max_abs = 0.0
    max_rel = 0.0
    mismatches = []
    packet_hours = []
    steps = []
    for rank in range(1, 33):
        exp = read_payload(args.payload_prefix, rank)
        if len(qc[rank]) <= args.packet_occurrence:
            raise SystemExit("task {} has {} QC occurrences, need occurrence {}".format(
                rank, len(qc[rank]), args.packet_occurrence))
        got = qc[rank][args.packet_occurrence]
        packet_hours.append(got["packet_hour"])
        steps.append(got["step"])
        for name in ["valid_i", "invalid_i", "valid_f", "invalid_f"]:
            if got[name] != exp[name]:
                mismatches.append((rank, name, got[name], exp[name]))
        for name in FIELDS:
            a = got[name]
            b = exp[name]
            diff = abs(a - b)
            rel = diff / max(abs(b), 1.0)
            max_abs = max(max_abs, diff)
            max_rel = max(max_rel, rel)
            if not close_enough(a, b, args.rtol, args.atol):
                mismatches.append((rank, name, a, b))

    if mismatches:
        print("WACCMX_RECV_QC compare failed; first mismatches:", file=sys.stderr)
        for item in mismatches[:20]:
            print(item, file=sys.stderr)
        raise SystemExit(1)

    print("WACCMX_RECV_QC compare ok: ranks=32 occurrence={} step_set={} packet_hour_set={} max_abs={:.6g} max_rel={:.6g}".format(
        args.packet_occurrence,
        sorted(set(steps)),
        sorted(set(packet_hours)),
        max_abs,
        max_rel))


if __name__ == "__main__":
    main()
