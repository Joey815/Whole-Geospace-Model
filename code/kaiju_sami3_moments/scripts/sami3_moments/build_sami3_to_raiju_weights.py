#!/usr/bin/env python3
"""Build an explicit SAMI3-to-RAIJU sparse mapping-weight file.

This script serializes the current prototype separable L/MLT interpolation into
a standalone HDF5 contract.  The weight file is intentionally more explicit
than the inline mapper: it stores source/destination coordinates, sparse
source/destination index pairs, weights, and quality masks.  A later production
file can keep this contract while replacing the generator with Voltron
traced-tube or bvol-aligned geometry.
"""

import argparse
import json
import os
import sys

import numpy as np

from sami3_moments_to_raiju_diag import (
    TINY,
    circular_mean_deg,
    decode_h5_text,
    finite_stats,
    linear_interp_brackets,
    output_paths,
    periodic_interp_brackets_deg,
    read_raicpl_target_l_mlt,
    read_sami3_l_mlt_grid,
    require_moments_h5,
)

TUBE_CLOSED = 2.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build an explicit sparse SAMI3-to-RAIJU mapping-weight HDF5 file."
    )
    parser.add_argument("moments_h5", help="Stage-1 SAMI3 moments HDF5 file.")
    parser.add_argument("--out", required=True, help="Output prefix or .h5 path.")
    parser.add_argument(
        "--mapping-mode",
        choices=("l_mlt_separable", "voltron_shell_l_mlt", "voltron_tubeshell_l_mlt"),
        default="l_mlt_separable",
        help=(
            "Weight-generation path. l_mlt_separable maps SAMI3 directly to "
            "RAIJU target L/MLT. voltron_shell_l_mlt composes SAMI3->Voltron "
            "ShellGrid and Voltron->RAIJU target shell-grid interpolation. "
            "voltron_tubeshell_l_mlt maps SAMI3 onto Voltron TubeShell Lb and "
            "footpoint longitude before the Voltron->RAIJU step."
        ),
    )
    parser.add_argument(
        "--raicpl-template",
        required=True,
        help="RAIJU coupler template containing /ShellGrid/theta and /ShellGrid/phi.",
    )
    parser.add_argument(
        "--voltron-template",
        default=None,
        help=(
            "Voltron restart/output HDF5 containing /ShellGrid and /TubeShell. "
            "Required for --mapping-mode voltron_shell_l_mlt."
        ),
    )
    parser.add_argument(
        "--apply-voltron-closed-mask",
        action="store_true",
        help=(
            "For voltron_shell_l_mlt, skip intermediate Voltron cells whose "
            "four TubeShell/topo corners are not all TUBE_CLOSED. The remaining "
            "weights are renormalized per RAIJU target cell."
        ),
    )
    parser.add_argument(
        "--voltron-tube-longitude",
        choices=("lon0", "lonc"),
        default="lon0",
        help=(
            "For voltron_tubeshell_l_mlt, choose the cell-centered TubeShell "
            "longitude used as the SAMI3 MLT/longitude query coordinate."
        ),
    )
    parser.add_argument(
        "--sami3-grid-dir",
        default=None,
        help="SAMI3 run directory containing baltu/blatu/blonu.dat. Defaults to stage-1 metadata run_dir.",
    )
    return parser.parse_args()


def read_stage1_grid_metadata(path):
    h5py = require_moments_h5(path)
    with h5py.File(path, "r") as handle:
        if "moments/Pavg" in handle:
            shape2 = tuple(handle["moments/Pavg"].shape)
        elif "moments/Pavg_i" in handle:
            shape2 = tuple(handle["moments/Pavg_i"].shape)
        else:
            raise KeyError("stage-1 moments file is missing /moments/Pavg or /moments/Pavg_i")
        metadata = {}
        if "metadata/json" in handle:
            metadata = json.loads(decode_h5_text(handle["metadata/json"][()]))
    if len(shape2) != 2:
        raise ValueError("stage-1 moment arrays must be 2-D, got {0}".format(shape2))
    dims = metadata.get("dimensions", {})
    if "nz" not in dims:
        raise ValueError("stage-1 metadata is missing dimensions.nz")
    return shape2, int(dims["nz"]), metadata


def build_sparse_l_mlt_weights(source_grid, target_grid):
    source_l = source_grid["source_l"]
    source_mlt = source_grid["source_lon_deg"]
    target_l = target_grid["target_l"]
    target_mlt = target_grid["target_lon_deg"]
    ni = target_l.size
    nj = target_mlt.size

    lq = linear_interp_brackets(source_l, target_l)
    mltq = periodic_interp_brackets_deg(source_mlt, target_mlt)
    l_left = lq["left_source_index"].astype(np.int32)
    l_right = lq["right_source_index"].astype(np.int32)
    l_weight = lq["interp_weight"].astype(np.float64)
    mlt_left = mltq["left_source_index"].astype(np.int32)
    mlt_right = mltq["right_source_index"].astype(np.int32)
    mlt_weight = mltq["interp_weight"].astype(np.float64)

    dst_rows = []
    src_rows = []
    weight_rows = []
    corner_rows = []
    weight_sum = np.zeros((nj, ni), dtype=np.float64)
    coverage_count = np.zeros((nj, ni), dtype=np.int16)

    for j in range(nj):
        for i in range(ni):
            corners = (
                (l_left[i], mlt_left[j], (1.0 - l_weight[i]) * (1.0 - mlt_weight[j]), 0),
                (l_right[i], mlt_left[j], l_weight[i] * (1.0 - mlt_weight[j]), 1),
                (l_left[i], mlt_right[j], (1.0 - l_weight[i]) * mlt_weight[j], 2),
                (l_right[i], mlt_right[j], l_weight[i] * mlt_weight[j], 3),
            )
            for src_i, src_j, weight, corner in corners:
                if weight <= 0.0:
                    continue
                dst_rows.append((j, i))
                src_rows.append((int(src_i), int(src_j)))
                weight_rows.append(float(weight))
                corner_rows.append(int(corner))
                weight_sum[j, i] += weight
                coverage_count[j, i] += 1

    if len(weight_rows) == 0:
        raise ValueError("generated mapping contains no nonzero weights")
    if np.any(weight_sum <= 0.0):
        raise ValueError("generated mapping contains target cells with zero weight sum")

    l_extrap_i = lq["outside"].astype(np.uint8)
    extrap_runtime = np.tile(l_extrap_i.reshape(1, ni), (nj, 1)).astype(np.uint8)

    return {
        "dst_index": np.asarray(dst_rows, dtype=np.int32),
        "src_index": np.asarray(src_rows, dtype=np.int32),
        "weight": np.asarray(weight_rows, dtype=np.float32),
        "corner": np.asarray(corner_rows, dtype=np.int8),
        "coverage_count": coverage_count,
        "weight_sum": weight_sum.astype(np.float32),
        "extrapolation_flag": extrap_runtime,
        "closed_field_mask": np.ones((nj, ni), dtype=np.uint8),
        "l_left_source_index": l_left,
        "l_right_source_index": l_right,
        "l_interp_weight": l_weight.astype(np.float32),
        "l_extrapolated_i": l_extrap_i,
        "mlt_left_source_index": mlt_left,
        "mlt_right_source_index": mlt_right,
        "mlt_interp_weight": mlt_weight.astype(np.float32),
    }


def build_sparse_l_mlt_weights_2d(source_grid, target_l_2d, target_mlt_2d):
    source_l = source_grid["source_l"]
    source_mlt = source_grid["source_lon_deg"]
    target_l_2d = np.asarray(target_l_2d, dtype=np.float64)
    target_mlt_2d = np.asarray(target_mlt_2d, dtype=np.float64)
    if target_l_2d.shape != target_mlt_2d.shape:
        raise ValueError(
            "target_l_2d shape {0} does not match target_mlt_2d shape {1}".format(
                target_l_2d.shape, target_mlt_2d.shape
            )
        )
    nj, ni = target_l_2d.shape
    dst_rows = []
    src_rows = []
    weight_rows = []
    corner_rows = []
    weight_sum = np.zeros((nj, ni), dtype=np.float64)
    coverage_count = np.zeros((nj, ni), dtype=np.int16)
    l_extrapolated = np.zeros((nj, ni), dtype=np.uint8)

    flat_lq = linear_interp_brackets(source_l, target_l_2d.reshape(-1))
    flat_mq = periodic_interp_brackets_deg(source_mlt, target_mlt_2d.reshape(-1))
    for j in range(nj):
        for i in range(ni):
            flat = j * ni + i
            wl = float(flat_lq["interp_weight"][flat])
            wm = float(flat_mq["interp_weight"][flat])
            if bool(flat_lq["outside"][flat]):
                l_extrapolated[j, i] = 1
            corners = (
                (int(flat_lq["left_source_index"][flat]), int(flat_mq["left_source_index"][flat]), (1.0 - wl) * (1.0 - wm), 0),
                (int(flat_lq["right_source_index"][flat]), int(flat_mq["left_source_index"][flat]), wl * (1.0 - wm), 1),
                (int(flat_lq["left_source_index"][flat]), int(flat_mq["right_source_index"][flat]), (1.0 - wl) * wm, 2),
                (int(flat_lq["right_source_index"][flat]), int(flat_mq["right_source_index"][flat]), wl * wm, 3),
            )
            for src_i, src_j, weight, corner in corners:
                if weight <= 0.0:
                    continue
                dst_rows.append((j, i))
                src_rows.append((src_i, src_j))
                weight_rows.append(float(weight))
                corner_rows.append(int(corner))
                weight_sum[j, i] += weight
                coverage_count[j, i] += 1

    if len(weight_rows) == 0:
        raise ValueError("generated 2-D L/MLT mapping contains no nonzero weights")
    if np.any(weight_sum <= 0.0):
        raise ValueError("generated 2-D L/MLT mapping contains target cells with zero weight sum")

    return {
        "dst_index": np.asarray(dst_rows, dtype=np.int32),
        "src_index": np.asarray(src_rows, dtype=np.int32),
        "weight": np.asarray(weight_rows, dtype=np.float32),
        "corner": np.asarray(corner_rows, dtype=np.int8),
        "coverage_count": coverage_count,
        "weight_sum": weight_sum.astype(np.float32),
        "l_extrapolated_mask": l_extrapolated,
        "l_extrapolated_count": int(np.count_nonzero(l_extrapolated)),
    }


def build_sparse_grid_to_grid(source_l, source_mlt, target_l, target_mlt):
    ni = target_l.size
    nj = target_mlt.size
    lq = linear_interp_brackets(source_l, target_l)
    mltq = periodic_interp_brackets_deg(source_mlt, target_mlt)
    dst_rows = []
    src_rows = []
    weight_rows = []
    corner_rows = []
    weight_sum = np.zeros((nj, ni), dtype=np.float64)
    coverage_count = np.zeros((nj, ni), dtype=np.int16)

    for j in range(nj):
        for i in range(ni):
            wl = float(lq["interp_weight"][i])
            wm = float(mltq["interp_weight"][j])
            corners = (
                (int(lq["left_source_index"][i]), int(mltq["left_source_index"][j]), (1.0 - wl) * (1.0 - wm), 0),
                (int(lq["right_source_index"][i]), int(mltq["left_source_index"][j]), wl * (1.0 - wm), 1),
                (int(lq["left_source_index"][i]), int(mltq["right_source_index"][j]), (1.0 - wl) * wm, 2),
                (int(lq["right_source_index"][i]), int(mltq["right_source_index"][j]), wl * wm, 3),
            )
            for src_i, src_j, weight, corner in corners:
                if weight <= 0.0:
                    continue
                dst_rows.append((j, i))
                src_rows.append((src_j, src_i))
                weight_rows.append(float(weight))
                corner_rows.append(int(corner))
                weight_sum[j, i] += weight
                coverage_count[j, i] += 1

    if len(weight_rows) == 0:
        raise ValueError("generated grid-to-grid mapping contains no nonzero weights")
    return {
        "dst_index": np.asarray(dst_rows, dtype=np.int32),
        "src_index": np.asarray(src_rows, dtype=np.int32),
        "weight": np.asarray(weight_rows, dtype=np.float64),
        "corner": np.asarray(corner_rows, dtype=np.int8),
        "coverage_count": coverage_count,
        "weight_sum": weight_sum,
        "l_left_source_index": lq["left_source_index"].astype(np.int32),
        "l_right_source_index": lq["right_source_index"].astype(np.int32),
        "l_interp_weight": lq["interp_weight"].astype(np.float32),
        "mlt_left_source_index": mltq["left_source_index"].astype(np.int32),
        "mlt_right_source_index": mltq["right_source_index"].astype(np.int32),
        "mlt_interp_weight": mltq["interp_weight"].astype(np.float32),
    }


def compose_sami3_voltron_raiju_weights(
    sami3_to_voltron,
    voltron_to_raiju,
    voltron_closed_mask=None,
    voltron_extrapolated_mask=None,
):
    if voltron_extrapolated_mask is not None:
        voltron_extrapolated_mask = np.asarray(voltron_extrapolated_mask, dtype=bool)

    per_voltron = {}
    for dst, src, weight in zip(
        sami3_to_voltron["dst_index"],
        sami3_to_voltron["src_index"],
        sami3_to_voltron["weight"],
    ):
        key = (int(dst[0]), int(dst[1]))
        per_voltron.setdefault(key, []).append((int(src[0]), int(src[1]), float(weight)))

    per_target = {}
    skipped_by_mask = 0
    extrapolated_source_terms = 0
    extrapolated_target_keys = set()
    for dst, vsrc, vweight in zip(
        voltron_to_raiju["dst_index"],
        voltron_to_raiju["src_index"],
        voltron_to_raiju["weight"],
    ):
        vkey = (int(vsrc[0]), int(vsrc[1]))
        if voltron_closed_mask is not None and not bool(voltron_closed_mask[vkey[0], vkey[1]]):
            skipped_by_mask += 1
            continue
        target_key = (int(dst[0]), int(dst[1]))
        source_terms = per_voltron.get(vkey, ())
        if not source_terms:
            continue
        if voltron_extrapolated_mask is not None and bool(
            voltron_extrapolated_mask[vkey[0], vkey[1]]
        ):
            extrapolated_source_terms += 1
            extrapolated_target_keys.add(target_key)
        acc = per_target.setdefault(target_key, {})
        for src_i, src_j, sw in source_terms:
            src_key = (src_i, src_j)
            acc[src_key] = acc.get(src_key, 0.0) + float(vweight) * sw

    dst_rows = []
    src_rows = []
    weight_rows = []
    raw_weight_sum = {}
    zero_target_count = 0
    for j, i in sorted(per_target):
        acc = per_target[(j, i)]
        total = sum(acc.values())
        raw_weight_sum[(j, i)] = total
        if total <= 0.0:
            zero_target_count += 1
            continue
        for src_key, weight in sorted(acc.items()):
            if weight <= 0.0:
                continue
            dst_rows.append((j, i))
            src_rows.append(src_key)
            weight_rows.append(float(weight) / total)

    if len(weight_rows) == 0:
        raise ValueError("composed Voltron-shell mapping contains no nonzero weights")

    dst_arr = np.asarray(dst_rows, dtype=np.int32)
    src_arr = np.asarray(src_rows, dtype=np.int32)
    weight_arr = np.asarray(weight_rows, dtype=np.float32)
    nj = int(np.max(voltron_to_raiju["dst_index"][:, 0])) + 1
    ni = int(np.max(voltron_to_raiju["dst_index"][:, 1])) + 1
    coverage_count = np.zeros((nj, ni), dtype=np.int16)
    weight_sum = np.zeros((nj, ni), dtype=np.float32)
    np.add.at(coverage_count, (dst_arr[:, 0], dst_arr[:, 1]), weight_arr > 0.0)
    np.add.at(weight_sum, (dst_arr[:, 0], dst_arr[:, 1]), weight_arr)
    extrapolation_flag = np.zeros((nj, ni), dtype=np.uint8)
    for j, i in extrapolated_target_keys:
        extrapolation_flag[j, i] = 1
    return {
        "dst_index": dst_arr,
        "src_index": src_arr,
        "weight": weight_arr,
        "corner": np.zeros(weight_arr.shape, dtype=np.int8),
        "coverage_count": coverage_count,
        "weight_sum": weight_sum,
        "extrapolation_flag": extrapolation_flag,
        "skipped_voltron_to_raiju_terms_by_mask": int(skipped_by_mask),
        "intermediate_extrapolated_source_terms": int(extrapolated_source_terms),
        "intermediate_extrapolated_target_count": int(np.count_nonzero(extrapolation_flag)),
        "zero_target_count": int(zero_target_count),
        "raw_weight_sum_min": float(min(raw_weight_sum.values())) if raw_weight_sum else None,
        "raw_weight_sum_max": float(max(raw_weight_sum.values())) if raw_weight_sum else None,
    }


def center_corners_2d(arr):
    return 0.25 * (arr[:-1, :-1] + arr[1:, :-1] + arr[:-1, 1:] + arr[1:, 1:])


def center_periodic_rad_2d(arr):
    sin_cc = center_corners_2d(np.sin(arr))
    cos_cc = center_corners_2d(np.cos(arr))
    return np.mod(np.arctan2(sin_cc, cos_cc), 2.0 * np.pi)


def read_optional_dataset(handle, name):
    if name in handle:
        return handle[name][:].astype(np.float64)
    return None


def finite_stats_optional(name, arr):
    if arr is None:
        return {
            "name": name,
            "shape": None,
            "finite_count": 0,
            "total_count": 0,
            "min": None,
            "max": None,
            "mean": None,
        }
    return finite_stats(name, arr)


def read_raicpl_target_geometry(template_path, target_shape):
    """Read target-side RAIJU geometry diagnostics from a raiCpl restart.

    RAIJU stores ShellGridVar arrays in HDF5 order j,i.  The runtime moment
    fields are cell-centered (NJ, NI), while bvol/topo/Bmin corner fields use
    (NJ+1, NI+1).  RAIJU only copies moment values into State where all four
    surrounding topo corners are closed, so the cell mask mirrors that rule.
    """
    h5py = require_moments_h5(template_path)
    ni, nj = target_shape
    with h5py.File(template_path, "r") as handle:
        bvol = read_optional_dataset(handle, "bvol")
        bvol_cc = read_optional_dataset(handle, "bvol_cc")
        topo = read_optional_dataset(handle, "topo")
        topo_mask = read_optional_dataset(handle, "topo_mask")
        bmin = read_optional_dataset(handle, "Bmin")
        bmin_mask = read_optional_dataset(handle, "Bmin_mask")
        xyz_min = read_optional_dataset(handle, "xyzMin")
        xyz_min_cc = read_optional_dataset(handle, "xyzMincc")
        thcon = read_optional_dataset(handle, "thcon")
        phcon = read_optional_dataset(handle, "phcon")
        va_frac = read_optional_dataset(handle, "vaFrac")
        tb = read_optional_dataset(handle, "Tb")

    corner_shape = (nj + 1, ni + 1)
    center_shape = (nj, ni)
    if bvol is not None and bvol.shape != corner_shape:
        raise ValueError("bvol shape {0} does not match {1}".format(bvol.shape, corner_shape))
    if bvol_cc is not None and bvol_cc.shape != center_shape:
        raise ValueError("bvol_cc shape {0} does not match {1}".format(bvol_cc.shape, center_shape))
    if topo is not None and topo.shape != corner_shape:
        raise ValueError("topo shape {0} does not match {1}".format(topo.shape, corner_shape))
    if bmin is not None and bmin.shape != (3, nj + 1, ni + 1):
        raise ValueError("Bmin shape {0} does not match (3,NJ+1,NI+1)".format(bmin.shape))
    if xyz_min_cc is not None and xyz_min_cc.shape != (3, nj, ni):
        raise ValueError("xyzMincc shape {0} does not match (3,NJ,NI)".format(xyz_min_cc.shape))
    if thcon is not None and thcon.shape != corner_shape:
        raise ValueError("thcon shape {0} does not match {1}".format(thcon.shape, corner_shape))
    if phcon is not None and phcon.shape != corner_shape:
        raise ValueError("phcon shape {0} does not match {1}".format(phcon.shape, corner_shape))
    if va_frac is not None and va_frac.shape != corner_shape:
        raise ValueError("vaFrac shape {0} does not match {1}".format(va_frac.shape, corner_shape))
    if tb is not None and tb.shape != center_shape:
        raise ValueError("Tb shape {0} does not match {1}".format(tb.shape, center_shape))

    if bvol_cc is None and bvol is not None:
        bvol_cc = center_corners_2d(bvol)
    if topo is None:
        topo = np.ones(corner_shape, dtype=np.float64)
    closed_field_mask = (
        (topo[:-1, :-1] == 1.0)
        & (topo[1:, :-1] == 1.0)
        & (topo[:-1, 1:] == 1.0)
        & (topo[1:, 1:] == 1.0)
    ).astype(np.uint8)

    bmin_mag = None
    bmin_mag_cc = None
    if bmin is not None:
        bmin_mag = np.sqrt(np.sum(bmin * bmin, axis=0))
        bmin_mag_cc = center_corners_2d(bmin_mag)

    stats = [
        finite_stats_optional("target_bvol_corner", bvol),
        finite_stats_optional("target_bvol_cc", bvol_cc),
        finite_stats_optional("target_topo_corner", topo),
        finite_stats_optional("target_closed_field_mask", closed_field_mask),
        finite_stats_optional("target_bmin_mag_corner", bmin_mag),
        finite_stats_optional("target_bmin_mag_cc", bmin_mag_cc),
        finite_stats_optional("target_vaFrac_corner", va_frac),
        finite_stats_optional("target_Tb_center", tb),
    ]
    return {
        "template": os.path.abspath(template_path),
        "bvol": bvol,
        "bvol_cc": bvol_cc,
        "topo": topo,
        "topo_mask": topo_mask,
        "closed_field_mask": closed_field_mask,
        "bmin": bmin,
        "bmin_mask": bmin_mask,
        "bmin_mag": bmin_mag,
        "bmin_mag_cc": bmin_mag_cc,
        "xyzMin": xyz_min,
        "xyzMincc": xyz_min_cc,
        "thcon": thcon,
        "phcon": phcon,
        "vaFrac": va_frac,
        "Tb": tb,
        "stats": stats,
    }


def read_voltron_tubeshell_geometry(template_path):
    shell_grid = read_raicpl_target_l_mlt(template_path, None)
    h5py = require_moments_h5(template_path)
    ni = shell_grid["target_l"].size
    nj = shell_grid["target_lon_deg"].size
    corner_shape = (nj + 1, ni + 1)
    center_shape = (nj, ni)
    with h5py.File(template_path, "r") as handle:
        required = (
            "TubeShell/bVol",
            "TubeShell/topo",
            "TubeShell/Lb",
            "TubeShell/bmin",
            "TubeShell/nTrc",
            "TubeShell/lon0",
            "TubeShell/lat0",
            "TubeShell/lonc",
            "TubeShell/latc",
        )
        for item in required:
            if item not in handle:
                raise KeyError("voltron template is missing /{0}".format(item))
        bvol = handle["TubeShell/bVol"][:].astype(np.float64)
        topo = handle["TubeShell/topo"][:].astype(np.float64)
        lb = handle["TubeShell/Lb"][:].astype(np.float64)
        bmin = handle["TubeShell/bmin"][:].astype(np.float64)
        ntrc = handle["TubeShell/nTrc"][:].astype(np.float64)
        lon0 = handle["TubeShell/lon0"][:].astype(np.float64)
        lat0 = handle["TubeShell/lat0"][:].astype(np.float64)
        lonc = handle["TubeShell/lonc"][:].astype(np.float64)
        latc = handle["TubeShell/latc"][:].astype(np.float64)
        wmag = read_optional_dataset(handle, "TubeShell/wMAG")
        tb = read_optional_dataset(handle, "TubeShell/Tb")

    for name, value in (
        ("TubeShell/bVol", bvol),
        ("TubeShell/topo", topo),
        ("TubeShell/Lb", lb),
        ("TubeShell/bmin", bmin),
        ("TubeShell/nTrc", ntrc),
        ("TubeShell/lon0", lon0),
        ("TubeShell/lat0", lat0),
        ("TubeShell/lonc", lonc),
        ("TubeShell/latc", latc),
    ):
        if value.shape != corner_shape:
            raise ValueError("{0} shape {1} does not match {2}".format(name, value.shape, corner_shape))
    if wmag is not None and wmag.shape != corner_shape:
        raise ValueError("TubeShell/wMAG shape {0} does not match {1}".format(wmag.shape, corner_shape))
    if tb is not None and tb.shape != corner_shape:
        raise ValueError("TubeShell/Tb shape {0} does not match {1}".format(tb.shape, corner_shape))

    closed_cell_mask = (
        (topo[:-1, :-1] == TUBE_CLOSED)
        & (topo[1:, :-1] == TUBE_CLOSED)
        & (topo[:-1, 1:] == TUBE_CLOSED)
        & (topo[1:, 1:] == TUBE_CLOSED)
    ).astype(np.uint8)
    bvol_cc = center_corners_2d(bvol)
    lb_cc = center_corners_2d(lb)
    bmin_cc = center_corners_2d(bmin)
    ntrc_cc = center_corners_2d(ntrc)
    lon0_cc = center_periodic_rad_2d(lon0)
    lonc_cc = center_periodic_rad_2d(lonc)
    lat0_cc = center_corners_2d(lat0)
    latc_cc = center_corners_2d(latc)
    lon0_cc_deg = np.mod(np.degrees(lon0_cc), 360.0)
    lonc_cc_deg = np.mod(np.degrees(lonc_cc), 360.0)
    stats = shell_grid["stats"] + [
        finite_stats("voltron_tubeshell_bVol_corner", bvol),
        finite_stats("voltron_tubeshell_bVol_cc", bvol_cc),
        finite_stats("voltron_tubeshell_Lb_corner", lb),
        finite_stats("voltron_tubeshell_Lb_cc", lb_cc),
        finite_stats("voltron_tubeshell_lon0_cc_deg", lon0_cc_deg),
        finite_stats("voltron_tubeshell_lonc_cc_deg", lonc_cc_deg),
        finite_stats("voltron_tubeshell_lat0_cc_rad", lat0_cc),
        finite_stats("voltron_tubeshell_latc_cc_rad", latc_cc),
        finite_stats("voltron_tubeshell_topo_corner", topo),
        finite_stats("voltron_tubeshell_closed_cell_mask", closed_cell_mask),
        finite_stats("voltron_tubeshell_bmin_corner", bmin),
        finite_stats("voltron_tubeshell_bmin_cc", bmin_cc),
        finite_stats("voltron_tubeshell_nTrc_corner", ntrc),
        finite_stats("voltron_tubeshell_nTrc_cc", ntrc_cc),
    ]
    return {
        "template": os.path.abspath(template_path),
        "target_l": shell_grid["target_l"],
        "target_lon_deg": shell_grid["target_lon_deg"],
        "bvol": bvol,
        "bvol_cc": bvol_cc,
        "topo": topo,
        "closed_cell_mask": closed_cell_mask,
        "Lb": lb,
        "Lb_cc": lb_cc,
        "bmin": bmin,
        "bmin_cc": bmin_cc,
        "nTrc": ntrc,
        "nTrc_cc": ntrc_cc,
        "lon0": lon0,
        "lat0": lat0,
        "lonc": lonc,
        "latc": latc,
        "lon0_cc": lon0_cc,
        "lat0_cc": lat0_cc,
        "lonc_cc": lonc_cc,
        "latc_cc": latc_cc,
        "lon0_cc_deg": lon0_cc_deg,
        "lonc_cc_deg": lonc_cc_deg,
        "wMAG": wmag,
        "Tb": tb,
        "stats": stats,
    }


def create_dataset(group, name, data, units, description):
    dset = group.create_dataset(name, data=data, compression="gzip", shuffle=True)
    dset.attrs["Units"] = units
    dset.attrs["Description"] = description
    return dset


def write_intermediate_group(handle, intermediate):
    if intermediate is None:
        return
    group = handle.create_group("intermediate")
    group.attrs["description"] = "Voltron TubeShell intermediate grid and sparse submaps."
    create_dataset(group, "L", intermediate["target_l"].astype(np.float32), "Re", "Voltron ShellGrid cell-center L by i index.")
    create_dataset(group, "MLT_deg", intermediate["target_lon_deg"].astype(np.float32), "degrees", "Voltron ShellGrid cell-center periodic MLT by j index.")
    create_dataset(group, "bvol_corner", intermediate["bvol"].astype(np.float32), "Rp/nT", "Voltron TubeShell corner bVol.")
    create_dataset(group, "bvol_cc", intermediate["bvol_cc"].astype(np.float32), "Rp/nT", "Voltron TubeShell cell-centered bVol.")
    create_dataset(group, "topo_corner", intermediate["topo"].astype(np.int16), "enum", "Voltron TubeShell corner topology; TUBE_CLOSED=2.")
    create_dataset(group, "closed_cell_mask", intermediate["closed_cell_mask"].astype(np.uint8), "logical", "Voltron cell mask, 1 where all four TubeShell topo corners are TUBE_CLOSED.")
    create_dataset(group, "Lb_corner", intermediate["Lb"].astype(np.float32), "Rp", "Voltron TubeShell corner Lb.")
    create_dataset(group, "Lb_cc", intermediate["Lb_cc"].astype(np.float32), "Rp", "Voltron TubeShell cell-centered Lb.")
    create_dataset(group, "lon0_cc_deg", intermediate["lon0_cc_deg"].astype(np.float32), "degrees", "Voltron TubeShell cell-centered lon0.")
    create_dataset(group, "lonc_cc_deg", intermediate["lonc_cc_deg"].astype(np.float32), "degrees", "Voltron TubeShell cell-centered lonc.")
    create_dataset(group, "lat0_cc_rad", intermediate["lat0_cc"].astype(np.float32), "radian", "Voltron TubeShell cell-centered lat0.")
    create_dataset(group, "latc_cc_rad", intermediate["latc_cc"].astype(np.float32), "radian", "Voltron TubeShell cell-centered latc.")
    create_dataset(group, "bmin_corner", intermediate["bmin"].astype(np.float32), "nT", "Voltron TubeShell corner bmin.")
    create_dataset(group, "bmin_cc", intermediate["bmin_cc"].astype(np.float32), "nT", "Voltron TubeShell cell-centered bmin.")
    create_dataset(group, "nTrc_corner", intermediate["nTrc"].astype(np.float32), "count", "Voltron TubeShell corner nTrc.")
    create_dataset(group, "nTrc_cc", intermediate["nTrc_cc"].astype(np.float32), "count", "Voltron TubeShell cell-centered nTrc.")
    for optional_name, units, description in (
        ("wMAG", "normalized", "Voltron TubeShell corner wMAG."),
        ("Tb", "s", "Voltron TubeShell corner Tb."),
    ):
        if intermediate.get(optional_name) is not None:
            create_dataset(group, optional_name, intermediate[optional_name].astype(np.float32), units, description)
    if intermediate.get("sami3_to_voltron") is not None:
        sub = group.create_group("sami3_to_voltron")
        item = intermediate["sami3_to_voltron"]
        create_dataset(sub, "dst_index", item["dst_index"], "index", "Voltron intermediate destination indices; columns are j,i.")
        create_dataset(sub, "src_index", item["src_index"], "index", "SAMI3 source indices; columns are nf,nlt.")
        create_dataset(sub, "weight", item["weight"].astype(np.float32), "normalized", "SAMI3-to-Voltron sparse weights.")
        if "l_extrapolated_mask" in item:
            create_dataset(sub, "l_extrapolated_mask", item["l_extrapolated_mask"], "logical", "1 where the Voltron TubeShell Lb query was clamped to the SAMI3 L range.")
    if intermediate.get("voltron_to_raiju") is not None:
        sub = group.create_group("voltron_to_raiju")
        item = intermediate["voltron_to_raiju"]
        create_dataset(sub, "dst_index", item["dst_index"], "index", "RAIJU destination indices; columns are j,i.")
        create_dataset(sub, "src_index", item["src_index"], "index", "Voltron source indices; columns are j,i.")
        create_dataset(sub, "weight", item["weight"].astype(np.float32), "normalized", "Voltron-to-RAIJU sparse weights.")


def write_weight_file(path, metadata, source_grid, target_grid, target_geometry, sparse, intermediate=None):
    h5py = require_moments_h5(metadata["source_moments_h5"])
    out_dir = os.path.dirname(path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with h5py.File(path, "w") as handle:
        handle.attrs["product"] = "sami3_to_raiju_mapping_weights"
        handle.attrs["schema_version"] = metadata["schema_version"]
        handle.attrs["mapping_mode"] = metadata["mapping_mode"]
        handle.attrs["physical_validity"] = "prototype"
        handle.attrs["physical_note"] = metadata["physical_note"]
        handle.attrs["source_shape_nf_nlt"] = metadata["source_shape_nf_nlt"]
        handle.attrs["target_shape_ni_nj"] = metadata["target_shape_ni_nj"]
        handle.attrs["target_geometry_source"] = metadata["target_template"]
        handle.attrs["apply_voltron_closed_mask"] = int(metadata["apply_voltron_closed_mask"])
        if metadata["voltron_template"] is not None:
            handle.attrs["voltron_template"] = metadata["voltron_template"]
        if metadata["voltron_tube_longitude"] is not None:
            handle.attrs["voltron_tube_longitude"] = metadata["voltron_tube_longitude"]
        handle.attrs["runtime_index_layout"] = "dst_index columns are j,i; src_index columns are nf,nlt"
        handle.attrs["note"] = (
            "Prototype sparse mapping weights with RAIJU target bvol/topology "
            "diagnostics. See metadata/json for whether the sparse weights use "
            "direct L/MLT or Voltron-shell intermediate projection."
        )

        src = handle.create_group("src")
        create_dataset(src, "L", source_grid["source_l"].astype(np.float32), "Re", "SAMI3 source L by nf index.")
        create_dataset(
            src,
            "MLT_deg",
            source_grid["source_lon_deg"].astype(np.float32),
            "degrees",
            "SAMI3 source periodic longitude/MLT by nlt index.",
        )
        create_dataset(
            src,
            "tube_L",
            source_grid["tube_l"].astype(np.float32),
            "Re",
            "SAMI3 tube L estimate by nf,nlt before median collapse.",
        )
        create_dataset(src, "nf_index", np.arange(metadata["source_shape_nf_nlt"][0], dtype=np.int32), "index", "SAMI3 nf index.")
        create_dataset(src, "nlt_index", np.arange(metadata["source_shape_nf_nlt"][1], dtype=np.int32), "index", "SAMI3 nlt index.")

        dst = handle.create_group("dst")
        create_dataset(dst, "L", target_grid["target_l"].astype(np.float32), "Re", "RAIJU target L by i index.")
        create_dataset(
            dst,
            "MLT_deg",
            target_grid["target_lon_deg"].astype(np.float32),
            "degrees",
            "RAIJU target periodic longitude/MLT by j index.",
        )
        create_dataset(dst, "shell_index", np.arange(metadata["target_shape_ni_nj"][0], dtype=np.int32), "index", "RAIJU i/shell index.")
        create_dataset(dst, "mlt_index", np.arange(metadata["target_shape_ni_nj"][1], dtype=np.int32), "index", "RAIJU j/MLT index.")
        if target_geometry["bvol"] is not None:
            create_dataset(dst, "bvol_corner", target_geometry["bvol"].astype(np.float32), "Rx/nT", "RAIJU target corner flux-tube volume from raiCpl%bvol.")
        if target_geometry["bvol_cc"] is not None:
            create_dataset(dst, "bvol_cc", target_geometry["bvol_cc"].astype(np.float32), "Rx/nT", "RAIJU target cell-centered flux-tube volume from raiCpl%bvol_cc.")
        if target_geometry["topo"] is not None:
            create_dataset(dst, "topo_corner", target_geometry["topo"].astype(np.int16), "0=open,1=closed", "RAIJU target corner topology from raiCpl%topo.")
        if target_geometry["topo_mask"] is not None:
            create_dataset(dst, "topo_mask", target_geometry["topo_mask"].astype(np.uint8), "logical", "RAIJU target topology data mask from raiCpl restart.")
        if target_geometry["bmin"] is not None:
            create_dataset(dst, "Bmin_corner", target_geometry["bmin"].astype(np.float32), "nT", "RAIJU target corner Bmin vector from raiCpl%Bmin.")
        if target_geometry["bmin_mag"] is not None:
            create_dataset(dst, "Bmin_mag_corner", target_geometry["bmin_mag"].astype(np.float32), "nT", "Magnitude of RAIJU target corner Bmin vector.")
        if target_geometry["bmin_mag_cc"] is not None:
            create_dataset(dst, "Bmin_mag_cc", target_geometry["bmin_mag_cc"].astype(np.float32), "nT", "Cell-centered average of Bmin magnitude.")
        if target_geometry["xyzMincc"] is not None:
            create_dataset(dst, "xyzMincc", target_geometry["xyzMincc"].astype(np.float32), "Re", "RAIJU target cell-centered minimum-B location.")
        if target_geometry["thcon"] is not None:
            create_dataset(dst, "thcon_corner", target_geometry["thcon"].astype(np.float32), "rad", "RAIJU target corner conjugate theta.")
        if target_geometry["phcon"] is not None:
            create_dataset(dst, "phcon_corner", target_geometry["phcon"].astype(np.float32), "rad", "RAIJU target corner conjugate phi.")
        if target_geometry["vaFrac"] is not None:
            create_dataset(dst, "vaFrac_corner", target_geometry["vaFrac"].astype(np.float32), "normalized", "RAIJU target corner Alfven-speed fraction.")
        if target_geometry["Tb"] is not None:
            create_dataset(dst, "Tb", target_geometry["Tb"].astype(np.float32), "unknown", "RAIJU target cell-centered Tb diagnostic from raiCpl.")

        mapping = handle.create_group("map")
        create_dataset(mapping, "dst_index", sparse["dst_index"], "index", "Sparse destination runtime indices; columns are j,i.")
        create_dataset(mapping, "src_index", sparse["src_index"], "index", "Sparse source SAMI3 indices; columns are nf,nlt.")
        create_dataset(mapping, "weight", sparse["weight"], "normalized", "Sparse interpolation weights.")
        create_dataset(mapping, "corner", sparse["corner"], "index", "Bilinear corner id: 0 LL, 1 RL, 2 LR, 3 RR.")
        for name, units, description in (
            ("l_left_source_index", "index", "Lower source index used by direct l_mlt_separable mapping."),
            ("l_right_source_index", "index", "Upper source index used by direct l_mlt_separable mapping."),
            ("l_interp_weight", "normalized", "Linear L interpolation weight used by direct l_mlt_separable mapping."),
            ("mlt_left_source_index", "index", "Left periodic source index used by direct l_mlt_separable mapping."),
            ("mlt_right_source_index", "index", "Right periodic source index used by direct l_mlt_separable mapping."),
            ("mlt_interp_weight", "normalized", "Periodic MLT interpolation weight used by direct l_mlt_separable mapping."),
        ):
            if name in sparse:
                create_dataset(mapping, name, sparse[name], units, description)

        quality = handle.create_group("quality")
        create_dataset(quality, "coverage_count", sparse["coverage_count"], "count", "Number of nonzero weights at each runtime j,i cell.")
        create_dataset(quality, "weight_sum", sparse["weight_sum"], "normalized", "Sum of sparse weights at each runtime j,i cell.")
        create_dataset(quality, "extrapolation_flag", sparse["extrapolation_flag"], "logical", "1 where the direct target or any contributing Voltron intermediate cell was outside the SAMI3 source L range and clamped.")
        create_dataset(
            quality,
            "closed_field_mask",
            sparse["closed_field_mask"],
            "logical",
            "Cell-centered closed-field mask: 1 where all four RAIJU topo corners are closed.",
        )
        create_dataset(quality, "l_extrapolated_i", sparse["l_extrapolated_i"], "logical", "1 where target i is L-clamped.")
        if "intermediate_closed_mask" in sparse:
            create_dataset(
                quality,
                "intermediate_closed_mask",
                sparse["intermediate_closed_mask"].astype(np.uint8),
                "logical",
                "Voltron intermediate closed-cell mask used or recorded by the composed mapping.",
            )
        write_intermediate_group(handle, intermediate)

        meta = handle.create_group("metadata")
        meta.create_dataset("json", data=json.dumps(metadata, indent=2, sort_keys=True))


def main():
    args = parse_args()
    moments_h5 = os.path.abspath(args.moments_h5)
    out_h5, out_json = output_paths(args.out)
    shape2, nz, source_metadata = read_stage1_grid_metadata(moments_h5)
    grid_dir = args.sami3_grid_dir or source_metadata.get("run_dir")
    if not grid_dir:
        raise ValueError("--sami3-grid-dir is required when stage-1 metadata has no run_dir")

    source_grid = read_sami3_l_mlt_grid(
        os.path.abspath(grid_dir), (int(nz), int(shape2[0]), int(shape2[1]))
    )
    target_grid = read_raicpl_target_l_mlt(os.path.abspath(args.raicpl_template), None)
    target_geometry = read_raicpl_target_geometry(
        os.path.abspath(args.raicpl_template),
        (target_grid["target_l"].size, target_grid["target_lon_deg"].size),
    )
    intermediate = None
    if args.mapping_mode == "l_mlt_separable":
        sparse = build_sparse_l_mlt_weights(source_grid, target_grid)
        schema_version = 2
        physical_note = "direct SAMI3-to-RAIJU separable L/MLT sparse weights"
        voltron_template = None
        apply_voltron_mask = False
    else:
        if not args.voltron_template:
            raise ValueError("--mapping-mode {0} requires --voltron-template".format(args.mapping_mode))
        voltron_geometry = read_voltron_tubeshell_geometry(os.path.abspath(args.voltron_template))
        if args.mapping_mode == "voltron_shell_l_mlt":
            sami3_to_voltron = build_sparse_l_mlt_weights(source_grid, voltron_geometry)
            physical_note = (
                "SAMI3-to-Voltron-shell then Voltron-shell-to-RAIJU composed sparse weights"
            )
            voltron_tube_longitude = None
        else:
            longitude_key = args.voltron_tube_longitude + "_cc_deg"
            sami3_to_voltron = build_sparse_l_mlt_weights_2d(
                source_grid,
                voltron_geometry["Lb_cc"],
                voltron_geometry[longitude_key],
            )
            physical_note = (
                "SAMI3-to-Voltron-TubeShell Lb/{0} then Voltron-shell-to-RAIJU composed sparse weights".format(
                    args.voltron_tube_longitude
                )
            )
            voltron_tube_longitude = args.voltron_tube_longitude
        voltron_to_raiju = build_sparse_grid_to_grid(
            voltron_geometry["target_l"],
            voltron_geometry["target_lon_deg"],
            target_grid["target_l"],
            target_grid["target_lon_deg"],
        )
        sparse = compose_sami3_voltron_raiju_weights(
            sami3_to_voltron,
            voltron_to_raiju,
            voltron_geometry["closed_cell_mask"] if args.apply_voltron_closed_mask else None,
            sami3_to_voltron.get("l_extrapolated_mask")
            if args.mapping_mode == "voltron_tubeshell_l_mlt"
            else sami3_to_voltron.get("extrapolation_flag"),
        )
        sparse["l_extrapolated_i"] = np.any(sparse["extrapolation_flag"], axis=0).astype(
            np.uint8
        )
        sparse["intermediate_closed_mask"] = voltron_geometry["closed_cell_mask"]
        intermediate = dict(voltron_geometry)
        intermediate["sami3_to_voltron"] = sami3_to_voltron
        intermediate["voltron_to_raiju"] = voltron_to_raiju
        schema_version = 3
        voltron_template = os.path.abspath(args.voltron_template)
        apply_voltron_mask = bool(args.apply_voltron_closed_mask)

    sparse["closed_field_mask"] = target_geometry["closed_field_mask"]
    ni = target_grid["target_l"].size
    nj = target_grid["target_lon_deg"].size

    metadata = {
        "product": "sami3_to_raiju_mapping_weights",
        "schema_version": schema_version,
        "mapping_mode": args.mapping_mode,
        "physical_validity": "prototype",
        "physical_note": physical_note,
        "source_moments_h5": moments_h5,
        "source_grid_dir": os.path.abspath(grid_dir),
        "target_template": os.path.abspath(args.raicpl_template),
        "voltron_template": voltron_template,
        "voltron_tube_longitude": (
            voltron_tube_longitude if args.mapping_mode == "voltron_tubeshell_l_mlt" else None
        ),
        "apply_voltron_closed_mask": apply_voltron_mask,
        "output_hdf5": out_h5,
        "source_shape_nf_nlt": [int(shape2[0]), int(shape2[1])],
        "target_shape_ni_nj": [int(ni), int(nj)],
        "sparse_weight_count": int(sparse["weight"].size),
        "coverage_count_min": int(np.min(sparse["coverage_count"])),
        "coverage_count_max": int(np.max(sparse["coverage_count"])),
        "weight_sum_min": float(np.min(sparse["weight_sum"])),
        "weight_sum_max": float(np.max(sparse["weight_sum"])),
        "l_extrapolated_cell_count": int(np.count_nonzero(sparse["extrapolation_flag"])),
        "closed_field_mask_policy": "RAIJU cell is closed only if all four target topo corners are RAIJUCLOSED",
        "closed_field_cell_count": int(np.count_nonzero(sparse["closed_field_mask"])),
        "closed_field_fraction": float(np.count_nonzero(sparse["closed_field_mask"]))
        / float(sparse["closed_field_mask"].size),
        "bvol_cc_min": (
            float(np.nanmin(target_geometry["bvol_cc"]))
            if target_geometry["bvol_cc"] is not None
            else None
        ),
        "bvol_cc_max": (
            float(np.nanmax(target_geometry["bvol_cc"]))
            if target_geometry["bvol_cc"] is not None
            else None
        ),
        "sparse_raw_weight_sum_min": sparse.get("raw_weight_sum_min"),
        "sparse_raw_weight_sum_max": sparse.get("raw_weight_sum_max"),
        "sami3_to_voltron_l_extrapolated_count": (
            intermediate["sami3_to_voltron"].get("l_extrapolated_count")
            if intermediate is not None
            else None
        ),
        "skipped_voltron_to_raiju_terms_by_mask": sparse.get(
            "skipped_voltron_to_raiju_terms_by_mask"
        ),
        "intermediate_extrapolated_source_terms": sparse.get(
            "intermediate_extrapolated_source_terms"
        ),
        "intermediate_extrapolated_target_count": sparse.get(
            "intermediate_extrapolated_target_count"
        ),
        "source_l_formula": "median_nz_nlt((baltu/Re)/cos(blatu)^2)",
        "source_mlt_formula": "circular_mean_nz_nf(blonu) degrees",
        "target_l_formula": "1/sin(theta_cell_center)^2 from ShellGrid/theta",
        "target_mlt_formula": "ShellGrid/phi cell centers modulo 360 degrees",
        "stats": source_grid["stats"]
        + target_grid["stats"]
        + target_geometry["stats"]
        + (intermediate["stats"] if intermediate is not None else [])
        + [
            finite_stats("mapping_weight", sparse["weight"]),
            finite_stats("mapping_weight_sum", sparse["weight_sum"]),
            finite_stats("mapping_coverage_count", sparse["coverage_count"]),
        ],
    }

    write_weight_file(out_h5, metadata, source_grid, target_grid, target_geometry, sparse, intermediate)
    with open(out_json, "w") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("wrote {0}".format(out_h5))
    print("wrote {0}".format(out_json))
    print("sparse_weight_count={0}".format(metadata["sparse_weight_count"]))
    print("coverage_count_min={0}".format(metadata["coverage_count_min"]))
    print("coverage_count_max={0}".format(metadata["coverage_count_max"]))
    print("weight_sum_min={0}".format(metadata["weight_sum_min"]))
    print("weight_sum_max={0}".format(metadata["weight_sum_max"]))
    print("l_extrapolated_cell_count={0}".format(metadata["l_extrapolated_cell_count"]))
    print("closed_field_cell_count={0}".format(metadata["closed_field_cell_count"]))
    print("closed_field_fraction={0}".format(metadata["closed_field_fraction"]))
    print("bvol_cc_min={0}".format(metadata["bvol_cc_min"]))
    print("bvol_cc_max={0}".format(metadata["bvol_cc_max"]))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        sys.exit(1)
