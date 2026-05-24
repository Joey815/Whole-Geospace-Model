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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build an explicit sparse SAMI3-to-RAIJU mapping-weight HDF5 file."
    )
    parser.add_argument("moments_h5", help="Stage-1 SAMI3 moments HDF5 file.")
    parser.add_argument("--out", required=True, help="Output prefix or .h5 path.")
    parser.add_argument(
        "--raicpl-template",
        required=True,
        help="RAIJU coupler template containing /ShellGrid/theta and /ShellGrid/phi.",
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


def center_corners_2d(arr):
    return 0.25 * (arr[:-1, :-1] + arr[1:, :-1] + arr[:-1, 1:] + arr[1:, 1:])


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


def create_dataset(group, name, data, units, description):
    dset = group.create_dataset(name, data=data, compression="gzip", shuffle=True)
    dset.attrs["Units"] = units
    dset.attrs["Description"] = description
    return dset


def write_weight_file(path, metadata, source_grid, target_grid, target_geometry, sparse):
    h5py = require_moments_h5(metadata["source_moments_h5"])
    out_dir = os.path.dirname(path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with h5py.File(path, "w") as handle:
        handle.attrs["product"] = "sami3_to_raiju_mapping_weights"
        handle.attrs["schema_version"] = 2
        handle.attrs["mapping_mode"] = "l_mlt_separable"
        handle.attrs["physical_validity"] = "prototype"
        handle.attrs["source_shape_nf_nlt"] = metadata["source_shape_nf_nlt"]
        handle.attrs["target_shape_ni_nj"] = metadata["target_shape_ni_nj"]
        handle.attrs["target_geometry_source"] = metadata["target_template"]
        handle.attrs["runtime_index_layout"] = "dst_index columns are j,i; src_index columns are nf,nlt"
        handle.attrs["note"] = (
            "Prototype sparse serialization of separable L/MLT interpolation; "
            "target bvol/topology diagnostics are copied from the raiCpl template, "
            "but sparse weights are not yet Voltron traced-tube or bvol-aligned."
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
        create_dataset(mapping, "l_left_source_index", sparse["l_left_source_index"], "index", "Lower SAMI3 nf source index for each target i.")
        create_dataset(mapping, "l_right_source_index", sparse["l_right_source_index"], "index", "Upper SAMI3 nf source index for each target i.")
        create_dataset(mapping, "l_interp_weight", sparse["l_interp_weight"], "normalized", "Linear L interpolation weight toward l_right_source_index.")
        create_dataset(mapping, "mlt_left_source_index", sparse["mlt_left_source_index"], "index", "Left periodic SAMI3 nlt source index for each target j.")
        create_dataset(mapping, "mlt_right_source_index", sparse["mlt_right_source_index"], "index", "Right periodic SAMI3 nlt source index for each target j.")
        create_dataset(mapping, "mlt_interp_weight", sparse["mlt_interp_weight"], "normalized", "Periodic MLT interpolation weight toward mlt_right_source_index.")

        quality = handle.create_group("quality")
        create_dataset(quality, "coverage_count", sparse["coverage_count"], "count", "Number of nonzero weights at each runtime j,i cell.")
        create_dataset(quality, "weight_sum", sparse["weight_sum"], "normalized", "Sum of sparse weights at each runtime j,i cell.")
        create_dataset(quality, "extrapolation_flag", sparse["extrapolation_flag"], "logical", "1 where target L was outside the source L range and clamped.")
        create_dataset(
            quality,
            "closed_field_mask",
            sparse["closed_field_mask"],
            "logical",
            "Cell-centered closed-field mask: 1 where all four RAIJU topo corners are closed.",
        )
        create_dataset(quality, "l_extrapolated_i", sparse["l_extrapolated_i"], "logical", "1 where target i is L-clamped.")

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
    sparse = build_sparse_l_mlt_weights(source_grid, target_grid)
    sparse["closed_field_mask"] = target_geometry["closed_field_mask"]
    ni = target_grid["target_l"].size
    nj = target_grid["target_lon_deg"].size

    metadata = {
        "product": "sami3_to_raiju_mapping_weights",
        "schema_version": 2,
        "mapping_mode": "l_mlt_separable",
        "physical_validity": "prototype",
        "source_moments_h5": moments_h5,
        "source_grid_dir": os.path.abspath(grid_dir),
        "target_template": os.path.abspath(args.raicpl_template),
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
        "source_l_formula": "median_nz_nlt((baltu/Re)/cos(blatu)^2)",
        "source_mlt_formula": "circular_mean_nz_nf(blonu) degrees",
        "target_l_formula": "1/sin(theta_cell_center)^2 from ShellGrid/theta",
        "target_mlt_formula": "ShellGrid/phi cell centers modulo 360 degrees",
        "stats": source_grid["stats"]
        + target_grid["stats"]
        + target_geometry["stats"]
        + [
            finite_stats("mapping_weight", sparse["weight"]),
            finite_stats("mapping_weight_sum", sparse["weight_sum"]),
            finite_stats("mapping_coverage_count", sparse["coverage_count"]),
        ],
    }

    write_weight_file(out_h5, metadata, source_grid, target_grid, target_geometry, sparse)
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
