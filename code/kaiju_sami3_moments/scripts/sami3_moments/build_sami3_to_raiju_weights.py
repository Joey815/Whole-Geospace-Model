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


def create_dataset(group, name, data, units, description):
    dset = group.create_dataset(name, data=data, compression="gzip", shuffle=True)
    dset.attrs["Units"] = units
    dset.attrs["Description"] = description
    return dset


def write_weight_file(path, metadata, source_grid, target_grid, sparse):
    h5py = require_moments_h5(metadata["source_moments_h5"])
    out_dir = os.path.dirname(path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with h5py.File(path, "w") as handle:
        handle.attrs["product"] = "sami3_to_raiju_mapping_weights"
        handle.attrs["schema_version"] = 1
        handle.attrs["mapping_mode"] = "l_mlt_separable"
        handle.attrs["physical_validity"] = "prototype"
        handle.attrs["source_shape_nf_nlt"] = metadata["source_shape_nf_nlt"]
        handle.attrs["target_shape_ni_nj"] = metadata["target_shape_ni_nj"]
        handle.attrs["runtime_index_layout"] = "dst_index columns are j,i; src_index columns are nf,nlt"
        handle.attrs["note"] = (
            "Prototype sparse serialization of separable L/MLT interpolation; "
            "not yet a Voltron traced-tube or bvol-aligned mapping."
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
            "Prototype all-one mask; no traced-field topology filter is encoded yet.",
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
    sparse = build_sparse_l_mlt_weights(source_grid, target_grid)
    ni = target_grid["target_l"].size
    nj = target_grid["target_lon_deg"].size

    metadata = {
        "product": "sami3_to_raiju_mapping_weights",
        "schema_version": 1,
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
        "closed_field_mask_policy": "prototype_all_one_no_traced_topology_filter",
        "source_l_formula": "median_nz_nlt((baltu/Re)/cos(blatu)^2)",
        "source_mlt_formula": "circular_mean_nz_nf(blonu) degrees",
        "target_l_formula": "1/sin(theta_cell_center)^2 from ShellGrid/theta",
        "target_mlt_formula": "ShellGrid/phi cell centers modulo 360 degrees",
        "stats": source_grid["stats"]
        + target_grid["stats"]
        + [
            finite_stats("mapping_weight", sparse["weight"]),
            finite_stats("mapping_weight_sum", sparse["weight_sum"]),
            finite_stats("mapping_coverage_count", sparse["coverage_count"]),
        ],
    }

    write_weight_file(out_h5, metadata, source_grid, target_grid, sparse)
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


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        sys.exit(1)
