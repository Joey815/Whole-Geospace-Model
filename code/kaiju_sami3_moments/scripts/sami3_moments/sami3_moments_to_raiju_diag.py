#!/usr/bin/env python3
"""Build a Voltron/RAIJU diagnostic ingest product from SAMI3 moments.

This is the second offline sidecar in the SAMI3 -> MAGE moments path.  It reads
the intermediate moments HDF5 from sami3_to_voltron_moments.py and writes a
diagnostic HDF5 with the same plasma fields used by the existing Voltron/RAIJU
coupling line:

    Voltron TubeShell: avgP/avgN/stdP/stdN/Tiote0
    RAIJU coupler:    Pavg/Davg/Pstd/Dstd/tiote
    RAIJU state:      Pavg/Davg/Pstd/Dstd/tiote, with std normalized

It does not write a complete TubeShell or raiCpl restart because those files
also need ShellGrid topology, masks, magnetic geometry, potentials, and timing.
"""

import argparse
import json
import os
import sys

import numpy as np

from sami3_to_voltron_moments import read_fortran_record, require_file


MAXTUBEFLUIDS = 5
TINY = 1.0e-30
RE_KM = 6370.0
MOMENTS = ("Pavg", "Davg", "Pstd", "Dstd", "tiote")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert SAMI3 moments HDF5 into a Voltron/RAIJU diagnostic ingest product."
    )
    parser.add_argument("moments_h5", help="Input HDF5 from sami3_to_voltron_moments.py")
    parser.add_argument(
        "--out",
        required=True,
        help="Output prefix or .h5 path. A matching .json metadata file is written.",
    )
    parser.add_argument(
        "--n-fluid-in",
        type=int,
        default=0,
        help=(
            "RAIJU nFluidIn value for diagnostic channel allocation. "
            "The bulk SAMI3 moment is placed in channel 0 by default. "
            "Default: 0."
        ),
    )
    parser.add_argument(
        "--bulk-channel",
        type=int,
        default=0,
        help="Channel that receives the bulk SAMI3 moment. Default: 0.",
    )
    parser.add_argument(
        "--density-mode",
        choices=("num", "massEq"),
        default="num",
        help=(
            "Davg source for runtime products. num uses total ion number density "
            "Davg_num/Davg; massEq uses proton-equivalent Davg_massEq. Default: num."
        ),
    )
    parser.add_argument(
        "--pressure-mode",
        choices=("ion", "total"),
        default="ion",
        help=(
            "Pavg source for runtime products. ion uses ion pressure Pavg_i/Pavg; "
            "total uses Pavg_total. Default: ion."
        ),
    )
    parser.add_argument(
        "--allow-nonfinite",
        action="store_true",
        help="Write output even if one of the required arrays contains non-finite values.",
    )
    parser.add_argument(
        "--raicpl-template",
        help=(
            "Optional raiCpl restart/output HDF5 used to infer the runtime "
            "ReadInSGV layout for /RaiCplMomentsOnly from its Pavg dataset."
        ),
    )
    parser.add_argument(
        "--target-raicpl-shape",
        nargs=2,
        type=int,
        metavar=("NI", "NJ"),
        help=(
            "Optional target raijuCoupler_T cell-center shape for "
            "/RaiCplMomentsOnly. Use NI NJ in Fortran order."
        ),
    )
    parser.add_argument(
        "--mapping-mode",
        choices=("index", "l_mlt", "weights"),
        default="index",
        help=(
            "Runtime /RaiCplMomentsOnly mapping mode when a target layout is "
            "requested. index preserves the old normalized-index resize. "
            "l_mlt maps SAMI3 L/longitude onto RAIJU ShellGrid theta/phi with "
            "periodic MLT interpolation. weights applies an explicit sparse "
            "mapping-weight HDF5 file. Default: index."
        ),
    )
    parser.add_argument(
        "--mapping-weight-file",
        default=None,
        help=(
            "Explicit sparse SAMI3-to-RAIJU mapping weight file for "
            "--mapping-mode weights. If no --raicpl-template or "
            "--target-raicpl-shape is supplied, the target shape is inferred "
            "from this file."
        ),
    )
    parser.add_argument(
        "--sami3-grid-dir",
        default=None,
        help=(
            "Optional SAMI3 run directory containing baltu/blatu/blonu.dat for "
            "--mapping-mode l_mlt. Defaults to the stage-1 source metadata run_dir."
        ),
    )
    return parser.parse_args()


def strip_h5_suffix(path):
    for suffix in (".hdf5", ".h5"):
        if path.endswith(suffix):
            return path[: -len(suffix)]
    return path


def output_paths(out_arg):
    prefix = strip_h5_suffix(os.path.abspath(out_arg))
    return prefix + ".h5", prefix + ".json"


def decode_h5_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if hasattr(value, "shape") and value.shape == ():
        return decode_h5_text(value[()])
    return str(value)


def finite_stats(name, arr):
    finite = np.isfinite(arr)
    stat = {
        "name": name,
        "shape": list(arr.shape),
        "finite_count": int(np.count_nonzero(finite)),
        "total_count": int(arr.size),
    }
    if stat["finite_count"] == 0:
        stat.update({"min": None, "max": None, "mean": None})
        return stat
    vals = arr[finite]
    stat.update(
        {
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "mean": float(np.mean(vals)),
        }
    )
    return stat


def jsonable_h5_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def require_h5py():
    try:
        import h5py
    except Exception as exc:
        raise RuntimeError("h5py is required; use the mage-vis Python environment") from exc
    return h5py


def require_moments_h5(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    return require_h5py()


def select_dataset_name(handle, preferred, fallback=None):
    dset_path = "moments/{0}".format(preferred)
    if dset_path in handle:
        return preferred
    if fallback is not None and "moments/{0}".format(fallback) in handle:
        return fallback
    raise KeyError("missing required dataset /{0}".format(dset_path))


def moment_source_selection(handle, density_mode, pressure_mode):
    if density_mode == "num":
        davg_source = select_dataset_name(handle, "Davg_num", fallback="Davg")
    elif density_mode == "massEq":
        davg_source = select_dataset_name(handle, "Davg_massEq")
    else:
        raise ValueError("unsupported density mode: {0}".format(density_mode))

    if pressure_mode == "ion":
        pavg_source = select_dataset_name(handle, "Pavg_i", fallback="Pavg")
    elif pressure_mode == "total":
        pavg_source = select_dataset_name(handle, "Pavg_total")
    else:
        raise ValueError("unsupported pressure mode: {0}".format(pressure_mode))

    return {
        "Pavg": pavg_source,
        "Davg": davg_source,
        "Pstd": "Pstd",
        "Dstd": "Dstd",
        "tiote": "tiote",
    }


def read_moments(path, density_mode, pressure_mode):
    h5py = require_moments_h5(path)
    arrays = {}
    source_metadata = {}
    source_attrs = {}
    selection = {}
    with h5py.File(path, "r") as handle:
        selection = moment_source_selection(handle, density_mode, pressure_mode)
        for name in MOMENTS:
            dset_path = "moments/{0}".format(selection[name])
            if dset_path not in handle:
                raise KeyError("missing required dataset /{0}".format(dset_path))
            arrays[name] = handle[dset_path][:].astype(np.float64)
            source_attrs[name] = dict(handle[dset_path].attrs)
        if "metadata/json" in handle:
            source_metadata = json.loads(decode_h5_text(handle["metadata/json"][()]))
    shape = arrays["Pavg"].shape
    if len(shape) != 2:
        raise ValueError("Pavg must be 2-D, got shape {0}".format(shape))
    for name in MOMENTS[1:]:
        if arrays[name].shape != shape:
            raise ValueError(
                "{0} shape {1} does not match Pavg shape {2}".format(
                    name, arrays[name].shape, shape
                )
            )
    return arrays, source_metadata, source_attrs, selection


def resize_2d(arr, target_shape):
    if tuple(arr.shape) == tuple(target_shape):
        return arr.astype(np.float64, copy=True)
    ni, nj = target_shape
    if ni <= 0 or nj <= 0:
        raise ValueError("target shape must be positive, got {0}".format(target_shape))
    src_i = np.linspace(0.0, 1.0, arr.shape[0])
    src_j = np.linspace(0.0, 1.0, arr.shape[1])
    dst_i = np.linspace(0.0, 1.0, ni)
    dst_j = np.linspace(0.0, 1.0, nj)
    tmp = np.empty((ni, arr.shape[1]), dtype=np.float64)
    for j in range(arr.shape[1]):
        tmp[:, j] = np.interp(dst_i, src_i, arr[:, j])
    out = np.empty((ni, nj), dtype=np.float64)
    for i in range(ni):
        out[i, :] = np.interp(dst_j, src_j, tmp[i, :])
    return out


def circular_mean_deg(values, axis):
    radians = np.deg2rad(values)
    sin_mean = np.nanmean(np.sin(radians), axis=axis)
    cos_mean = np.nanmean(np.cos(radians), axis=axis)
    return np.mod(np.rad2deg(np.arctan2(sin_mean, cos_mean)), 360.0)


def read_sami3_l_mlt_grid(run_dir, shape):
    """Return separable SAMI3 L-shell and magnetic-longitude coordinates.

    SAMI3's helper L_n.f90 uses p=(r/Re)/cos(blat)^2 as the dipole-like shell
    coordinate.  We use the median over nz/nlt for the nf shell coordinate and
    circular mean blonu over nz/nf for the nlt longitude coordinate.
    """
    balt, _, _ = read_fortran_record(
        require_file(os.path.join(run_dir, "baltu.dat")), shape, "last"
    )
    blat, _, _ = read_fortran_record(
        require_file(os.path.join(run_dir, "blatu.dat")), shape, "last"
    )
    blon, _, _ = read_fortran_record(
        require_file(os.path.join(run_dir, "blonu.dat")), shape, "last"
    )

    cos2 = np.cos(np.deg2rad(blat.astype(np.float64))) ** 2
    l_shell_3d = (balt.astype(np.float64) / RE_KM) / np.maximum(cos2, TINY)
    tube_l = np.nanmedian(l_shell_3d, axis=0)
    source_l = np.nanmedian(tube_l, axis=1)
    source_lon = circular_mean_deg(blon.astype(np.float64), axis=(0, 1))

    if np.any(~np.isfinite(source_l)) or np.any(source_l <= 0.0):
        raise ValueError("SAMI3 L-shell coordinate contains invalid values")
    if np.any(~np.isfinite(source_lon)):
        raise ValueError("SAMI3 longitude coordinate contains invalid values")

    return {
        "run_dir": os.path.abspath(run_dir),
        "source_l": source_l.astype(np.float64),
        "source_lon_deg": source_lon.astype(np.float64),
        "tube_l": tube_l.astype(np.float64),
        "stats": [
            finite_stats("sami3_l_shell_3d", l_shell_3d),
            finite_stats("sami3_tube_l", tube_l),
            finite_stats("sami3_source_l", source_l),
            finite_stats("sami3_source_lon_deg", source_lon),
        ],
    }


def read_raicpl_target_l_mlt(template_path, target_shape):
    h5py = require_moments_h5(template_path)
    with h5py.File(template_path, "r") as handle:
        if "ShellGrid/phi" not in handle or "ShellGrid/theta" not in handle:
            raise KeyError(
                "template must contain /ShellGrid/phi and /ShellGrid/theta for l_mlt mapping"
            )
        phi = handle["ShellGrid/phi"][:].astype(np.float64)
        theta = handle["ShellGrid/theta"][:].astype(np.float64)

    if target_shape is None:
        ni, nj = theta.size - 1, phi.size - 1
    else:
        ni, nj = target_shape
        if phi.size != nj + 1 or theta.size != ni + 1:
            raise ValueError(
                "ShellGrid node sizes phi={0}, theta={1} do not match target shape {2}".format(
                    phi.size, theta.size, target_shape
                )
            )

    phi_cc = 0.5 * (phi[:-1] + phi[1:])
    theta_cc = 0.5 * (theta[:-1] + theta[1:])
    target_lon = np.mod(np.rad2deg(phi_cc), 360.0)
    target_l = 1.0 / np.maximum(np.sin(theta_cc) ** 2, TINY)

    return {
        "target_l": target_l.astype(np.float64),
        "target_lon_deg": target_lon.astype(np.float64),
        "template": os.path.abspath(template_path),
        "stats": [
            finite_stats("raicpl_target_l", target_l),
            finite_stats("raicpl_target_lon_deg", target_lon),
        ],
    }


def map_l_mlt_2d(arr, source_grid, target_grid):
    source_l = source_grid["source_l"]
    source_lon = source_grid["source_lon_deg"]
    target_l = target_grid["target_l"]
    target_lon = target_grid["target_lon_deg"]

    l_order = np.argsort(source_l)
    lon_order = np.argsort(source_lon)
    source_l_sorted = source_l[l_order]
    source_lon_sorted = source_lon[lon_order]
    values_l_sorted = arr[l_order, :]

    l_mapped = np.empty((target_l.size, arr.shape[1]), dtype=np.float64)
    for j in range(arr.shape[1]):
        values = values_l_sorted[:, j]
        l_mapped[:, j] = np.interp(
            target_l,
            source_l_sorted,
            values,
            left=values[0],
            right=values[-1],
        )

    l_mapped = l_mapped[:, lon_order]
    lon_ext = np.concatenate(
        (source_lon_sorted - 360.0, source_lon_sorted, source_lon_sorted + 360.0)
    )
    out = np.empty((target_l.size, target_lon.size), dtype=np.float64)
    for i in range(target_l.size):
        values_ext = np.concatenate((l_mapped[i, :], l_mapped[i, :], l_mapped[i, :]))
        out[i, :] = np.interp(target_lon, lon_ext, values_ext)
    return out


def linear_interp_brackets(source, target):
    source = np.asarray(source, dtype=np.float64)
    target = np.asarray(target, dtype=np.float64)
    order = np.argsort(source)
    sorted_source = source[order]
    right = np.searchsorted(sorted_source, target, side="right")
    outside = (target < sorted_source[0]) | (target > sorted_source[-1])
    right = np.clip(right, 1, sorted_source.size - 1)
    left = right - 1
    denom = np.maximum(sorted_source[right] - sorted_source[left], TINY)
    weight = (target - sorted_source[left]) / denom
    weight = np.clip(weight, 0.0, 1.0)
    left = np.where(target <= sorted_source[0], 0, left)
    right = np.where(target <= sorted_source[0], 0, right)
    left = np.where(target >= sorted_source[-1], sorted_source.size - 1, left)
    right = np.where(target >= sorted_source[-1], sorted_source.size - 1, right)
    weight = np.where(outside, 0.0, weight)
    return {
        "left_source_index": order[left].astype(np.int32),
        "right_source_index": order[right].astype(np.int32),
        "interp_weight": weight.astype(np.float32),
        "outside": outside,
    }


def periodic_interp_brackets_deg(source_deg, target_deg):
    source = np.mod(np.asarray(source_deg, dtype=np.float64), 360.0)
    target = np.mod(np.asarray(target_deg, dtype=np.float64), 360.0)
    order = np.argsort(source)
    source_sorted = source[order]
    source_ext = np.concatenate((source_sorted - 360.0, source_sorted, source_sorted + 360.0))
    order_ext = np.concatenate((order, order, order))
    right = np.searchsorted(source_ext, target, side="right")
    right = np.clip(right, 1, source_ext.size - 1)
    left = right - 1
    denom = np.maximum(source_ext[right] - source_ext[left], TINY)
    weight = (target - source_ext[left]) / denom
    return {
        "left_source_index": order_ext[left].astype(np.int32),
        "right_source_index": order_ext[right].astype(np.int32),
        "interp_weight": np.clip(weight, 0.0, 1.0).astype(np.float32),
    }


def peek_mapping_weight_target_shape(path):
    h5py = require_moments_h5(path)
    with h5py.File(path, "r") as handle:
        if "target_shape_ni_nj" in handle.attrs:
            shape = np.asarray(handle.attrs["target_shape_ni_nj"], dtype=np.int64)
            if shape.size != 2:
                raise ValueError("target_shape_ni_nj must have two entries in {0}".format(path))
            return int(shape[0]), int(shape[1])
        if "map/dst_index" not in handle:
            raise KeyError("mapping weight file is missing /map/dst_index: {0}".format(path))
        dst = handle["map/dst_index"][:].astype(np.int64)
    if dst.ndim != 2 or dst.shape[1] != 2 or dst.size == 0:
        raise ValueError("/map/dst_index must have shape (nnz, 2)")
    # dst_index columns are runtime j,i.
    return int(np.max(dst[:, 1])) + 1, int(np.max(dst[:, 0])) + 1


def read_optional_h5_dataset(handle, path, default=None):
    if path in handle:
        return handle[path][:]
    return default


def read_mapping_weight_file(path, target_shape, source_shape):
    h5py = require_moments_h5(path)
    with h5py.File(path, "r") as handle:
        required = (
            "map/dst_index",
            "map/src_index",
            "map/weight",
            "src/L",
            "src/MLT_deg",
            "dst/L",
            "dst/MLT_deg",
        )
        for item in required:
            if item not in handle:
                raise KeyError("mapping weight file is missing /{0}".format(item))

        dst_index = handle["map/dst_index"][:].astype(np.int64)
        src_index = handle["map/src_index"][:].astype(np.int64)
        weights = handle["map/weight"][:].astype(np.float64)
        source_l = handle["src/L"][:].astype(np.float64)
        source_mlt = handle["src/MLT_deg"][:].astype(np.float64)
        target_l = handle["dst/L"][:].astype(np.float64)
        target_mlt = handle["dst/MLT_deg"][:].astype(np.float64)

        coverage = read_optional_h5_dataset(handle, "quality/coverage_count")
        weight_sum = read_optional_h5_dataset(handle, "quality/weight_sum")
        extrap = read_optional_h5_dataset(handle, "quality/extrapolation_flag")
        closed = read_optional_h5_dataset(handle, "quality/closed_field_mask")
        corner = read_optional_h5_dataset(handle, "map/corner")
        l_left = read_optional_h5_dataset(handle, "map/l_left_source_index")
        l_right = read_optional_h5_dataset(handle, "map/l_right_source_index")
        l_weight = read_optional_h5_dataset(handle, "map/l_interp_weight")
        mlt_left = read_optional_h5_dataset(handle, "map/mlt_left_source_index")
        mlt_right = read_optional_h5_dataset(handle, "map/mlt_right_source_index")
        mlt_weight = read_optional_h5_dataset(handle, "map/mlt_interp_weight")
        attrs = {key: jsonable_h5_value(value) for key, value in handle.attrs.items()}

    if dst_index.ndim != 2 or dst_index.shape[1] != 2:
        raise ValueError("/map/dst_index must have shape (nnz, 2)")
    if src_index.shape != dst_index.shape:
        raise ValueError("/map/src_index shape must match /map/dst_index")
    if weights.ndim != 1 or weights.shape[0] != dst_index.shape[0]:
        raise ValueError("/map/weight must have shape (nnz,)")

    ni, nj = target_shape
    nf, nlt = source_shape
    if source_l.shape != (nf,) or source_mlt.shape != (nlt,):
        raise ValueError("mapping weight source coordinate shapes do not match SAMI3 moments")
    if target_l.shape != (ni,) or target_mlt.shape != (nj,):
        raise ValueError("mapping weight target coordinate shapes do not match runtime layout")

    if np.any(src_index[:, 0] < 0) or np.any(src_index[:, 0] >= nf):
        raise ValueError("/map/src_index nf column outside source range")
    if np.any(src_index[:, 1] < 0) or np.any(src_index[:, 1] >= nlt):
        raise ValueError("/map/src_index nlt column outside source range")
    if np.any(dst_index[:, 0] < 0) or np.any(dst_index[:, 0] >= nj):
        raise ValueError("/map/dst_index j column outside target range")
    if np.any(dst_index[:, 1] < 0) or np.any(dst_index[:, 1] >= ni):
        raise ValueError("/map/dst_index i column outside target range")
    if np.any(~np.isfinite(weights)) or np.any(weights < 0.0):
        raise ValueError("/map/weight contains non-finite or negative weights")

    if coverage is None or weight_sum is None:
        coverage = np.zeros((nj, ni), dtype=np.int16)
        weight_sum = np.zeros((nj, ni), dtype=np.float64)
        np.add.at(coverage, (dst_index[:, 0], dst_index[:, 1]), weights > 0.0)
        np.add.at(weight_sum, (dst_index[:, 0], dst_index[:, 1]), weights)
    else:
        coverage = coverage.astype(np.int16)
        weight_sum = weight_sum.astype(np.float64)
    if coverage.shape != (nj, ni) or weight_sum.shape != (nj, ni):
        raise ValueError("mapping quality arrays must use runtime shape (NJ, NI)")
    if extrap is None:
        extrap = np.zeros((nj, ni), dtype=np.uint8)
    if closed is None:
        closed = np.ones((nj, ni), dtype=np.uint8)
    extrap = extrap.astype(np.uint8)
    closed = closed.astype(np.uint8)
    if extrap.shape != (nj, ni) or closed.shape != (nj, ni):
        raise ValueError("mapping flag arrays must use runtime shape (NJ, NI)")

    summary = {
        "weight_file": os.path.abspath(path),
        "weight_file_schema_version": int(attrs.get("schema_version", 0)),
        "weight_file_mapping_mode": attrs.get("mapping_mode", "unknown"),
        "weight_file_physical_validity": attrs.get("physical_validity", "unknown"),
        "source_shape_nf_nlt": [int(nf), int(nlt)],
        "target_shape_ni_nj": [int(ni), int(nj)],
        "sparse_weight_count": int(weights.size),
        "coverage_count_min": int(np.min(coverage)),
        "coverage_count_max": int(np.max(coverage)),
        "weight_sum_min": float(np.min(weight_sum)),
        "weight_sum_max": float(np.max(weight_sum)),
        "extrapolated_cell_count": int(np.count_nonzero(extrap)),
        "closed_field_mask_zero_count": int(closed.size - np.count_nonzero(closed)),
    }
    optional = {
        "corner": corner,
        "l_left_source_index": l_left,
        "l_right_source_index": l_right,
        "l_interp_weight": l_weight,
        "mlt_left_source_index": mlt_left,
        "mlt_right_source_index": mlt_right,
        "mlt_interp_weight": mlt_weight,
    }
    return {
        "path": os.path.abspath(path),
        "attrs": attrs,
        "dst_index": dst_index.astype(np.int64),
        "src_index": src_index.astype(np.int64),
        "weight": weights.astype(np.float64),
        "source_l": source_l,
        "source_mlt_deg": source_mlt,
        "target_l": target_l,
        "target_mlt_deg": target_mlt,
        "coverage_count": coverage,
        "weight_sum": weight_sum,
        "extrapolation_flag": extrap,
        "closed_field_mask": closed,
        "optional": optional,
        "summary": summary,
    }


def map_weight_file_2d(arr, weight_info):
    target_l = weight_info["target_l"]
    target_mlt = weight_info["target_mlt_deg"]
    ni = target_l.size
    nj = target_mlt.size
    dst = weight_info["dst_index"]
    src = weight_info["src_index"]
    weights = weight_info["weight"]
    runtime = np.zeros((nj, ni), dtype=np.float64)
    weight_sum = np.zeros((nj, ni), dtype=np.float64)
    np.add.at(runtime, (dst[:, 0], dst[:, 1]), arr[src[:, 0], src[:, 1]] * weights)
    np.add.at(weight_sum, (dst[:, 0], dst[:, 1]), weights)
    runtime = runtime / np.maximum(weight_sum, TINY)
    return runtime.T


def build_mapping_quality_from_weights(mapped, target_shape, weight_info):
    result = build_mapping_quality("weights", mapped, target_shape)
    datasets = result["datasets"]
    summary = result["summary"]
    attrs = result["attrs"]
    attrs["weight_file"] = weight_info["path"]
    attrs["weight_file_mapping_mode"] = str(weight_info["summary"]["weight_file_mapping_mode"])
    attrs["weight_file_physical_validity"] = str(
        weight_info["summary"]["weight_file_physical_validity"]
    )
    datasets.update(
        {
            "source_l": {
                "data": weight_info["source_l"].astype(np.float32),
                "units": "Re",
                "description": "Source SAMI3 shell coordinate by nf index from mapping weight file.",
            },
            "source_mlt_deg": {
                "data": weight_info["source_mlt_deg"].astype(np.float32),
                "units": "degrees",
                "description": "Source SAMI3 periodic longitude/MLT coordinate by nlt index from mapping weight file.",
            },
            "target_l": {
                "data": weight_info["target_l"].astype(np.float32),
                "units": "Re",
                "description": "RAIJU target shell coordinate by i index from mapping weight file.",
            },
            "target_mlt_deg": {
                "data": weight_info["target_mlt_deg"].astype(np.float32),
                "units": "degrees",
                "description": "RAIJU target periodic longitude/MLT coordinate by j index from mapping weight file.",
            },
            "coverage_count_runtime": {
                "data": weight_info["coverage_count"].astype(np.int16),
                "units": "count",
                "description": "Number of nonzero sparse mapping weights at each runtime j,i cell.",
            },
            "weight_sum_runtime": {
                "data": weight_info["weight_sum"].astype(np.float32),
                "units": "normalized",
                "description": "Sparse mapping weight sum at each runtime j,i cell.",
            },
            "extrapolation_flag_runtime_mask": {
                "data": weight_info["extrapolation_flag"].astype(np.uint8),
                "units": "logical",
                "description": "1 where the mapping weight file marks the target cell as extrapolated.",
            },
            "closed_field_mask": {
                "data": weight_info["closed_field_mask"].astype(np.uint8),
                "units": "logical",
                "description": "Closed-field mask from mapping weight file; prototype files may set all cells to 1.",
            },
        }
    )
    optional_shapes = {
        "l_left_source_index": ("index", "Lower SAMI3 nf source index used for each target i."),
        "l_right_source_index": ("index", "Upper SAMI3 nf source index used for each target i."),
        "l_interp_weight": ("normalized", "Linear L interpolation weight toward l_right_source_index."),
        "mlt_left_source_index": ("index", "Left periodic SAMI3 nlt source index used for each target j."),
        "mlt_right_source_index": ("index", "Right periodic SAMI3 nlt source index used for each target j."),
        "mlt_interp_weight": ("normalized", "Periodic MLT interpolation weight toward mlt_right_source_index."),
    }
    for name, (units, description) in optional_shapes.items():
        value = weight_info["optional"].get(name)
        if value is not None:
            datasets[name] = {
                "data": value,
                "units": units,
                "description": description,
            }
    summary.update(weight_info["summary"])
    return result


def build_mapping_metadata_from_weights(target_shape, weight_info):
    return {
        "mode": "weights",
        "target_shape": [int(target_shape[0]), int(target_shape[1])],
        "weight_file": weight_info["path"],
        "weight_file_schema_version": weight_info["summary"]["weight_file_schema_version"],
        "weight_file_mapping_mode": weight_info["summary"]["weight_file_mapping_mode"],
        "weight_file_physical_validity": weight_info["summary"][
            "weight_file_physical_validity"
        ],
        "source_shape_nf_nlt": weight_info["summary"]["source_shape_nf_nlt"],
        "target_shape_ni_nj": weight_info["summary"]["target_shape_ni_nj"],
        "physical_validity": "prototype",
        "note": (
            "Sparse mapping-weight application.  The current generated weight "
            "file can encode the prototype separable L/MLT interpolation; later "
            "files should replace it with Voltron traced-tube or bvol-aligned weights."
        ),
        "quality_summary": weight_info["summary"],
    }


def build_mapping_quality(mode, mapped, target_shape, source_grid=None, target_grid=None):
    ni, nj = target_shape
    finite_count = np.zeros((nj, ni), dtype=np.int16)
    for name in MOMENTS:
        finite_count += np.isfinite(mapped[name]).T.astype(np.int16)
    finite_all = finite_count == len(MOMENTS)

    datasets = {
        "finite_moment_count_runtime": {
            "data": finite_count,
            "units": "count",
            "description": "Number of finite mapped moment fields at each runtime cell; HDF5 order j,i.",
        },
        "finite_all_moments_runtime_mask": {
            "data": finite_all.astype(np.uint8),
            "units": "logical",
            "description": "1 where all mapped moment fields are finite; HDF5 order j,i.",
        },
    }
    summary = {
        "mode": mode,
        "target_runtime_shape_j_i": [int(nj), int(ni)],
        "finite_all_cell_count": int(np.count_nonzero(finite_all)),
        "finite_all_fraction": float(np.count_nonzero(finite_all)) / float(finite_all.size),
        "finite_moment_count_min": int(np.min(finite_count)),
        "finite_moment_count_max": int(np.max(finite_count)),
    }
    attrs = {
        "mapping_mode": mode,
        "runtime_layout": "j,i for 2-D mapping-quality masks",
    }

    if mode == "l_mlt":
        lq = linear_interp_brackets(source_grid["source_l"], target_grid["target_l"])
        mltq = periodic_interp_brackets_deg(
            source_grid["source_lon_deg"], target_grid["target_lon_deg"]
        )
        l_extrap_i = lq["outside"].astype(np.uint8)
        l_extrap_runtime = np.tile(l_extrap_i.reshape(1, ni), (nj, 1)).astype(np.uint8)
        datasets.update(
            {
                "source_l": {
                    "data": source_grid["source_l"].astype(np.float32),
                    "units": "Re",
                    "description": "SAMI3 source shell coordinate by nf index.",
                },
                "source_mlt_deg": {
                    "data": source_grid["source_lon_deg"].astype(np.float32),
                    "units": "degrees",
                    "description": "SAMI3 periodic source longitude/MLT coordinate by nlt index.",
                },
                "target_l": {
                    "data": target_grid["target_l"].astype(np.float32),
                    "units": "Re",
                    "description": "RAIJU target shell coordinate by i index.",
                },
                "target_mlt_deg": {
                    "data": target_grid["target_lon_deg"].astype(np.float32),
                    "units": "degrees",
                    "description": "RAIJU target periodic longitude/MLT coordinate by j index.",
                },
                "l_left_source_index": {
                    "data": lq["left_source_index"],
                    "units": "index",
                    "description": "Lower SAMI3 nf source index used for each target i.",
                },
                "l_right_source_index": {
                    "data": lq["right_source_index"],
                    "units": "index",
                    "description": "Upper SAMI3 nf source index used for each target i.",
                },
                "l_interp_weight": {
                    "data": lq["interp_weight"],
                    "units": "normalized",
                    "description": "Linear interpolation weight toward l_right_source_index for each target i.",
                },
                "l_extrapolated_i": {
                    "data": l_extrap_i,
                    "units": "logical",
                    "description": "1 where target L is outside the SAMI3 source L range and was clamped.",
                },
                "l_extrapolated_runtime_mask": {
                    "data": l_extrap_runtime,
                    "units": "logical",
                    "description": "Runtime j,i mask for L-clamped target cells.",
                },
                "mlt_left_source_index": {
                    "data": mltq["left_source_index"],
                    "units": "index",
                    "description": "Left periodic SAMI3 nlt source index used for each target j.",
                },
                "mlt_right_source_index": {
                    "data": mltq["right_source_index"],
                    "units": "index",
                    "description": "Right periodic SAMI3 nlt source index used for each target j.",
                },
                "mlt_interp_weight": {
                    "data": mltq["interp_weight"],
                    "units": "normalized",
                    "description": "Periodic interpolation weight toward mlt_right_source_index for each target j.",
                },
            }
        )
        summary.update(
            {
                "periodic_mlt": True,
                "l_extrapolated_i_count": int(np.count_nonzero(l_extrap_i)),
                "l_extrapolated_cell_count": int(np.count_nonzero(l_extrap_runtime)),
                "l_extrapolated_fraction": float(np.count_nonzero(l_extrap_runtime))
                / float(l_extrap_runtime.size),
                "source_l_min": float(np.min(source_grid["source_l"])),
                "source_l_max": float(np.max(source_grid["source_l"])),
                "target_l_min": float(np.min(target_grid["target_l"])),
                "target_l_max": float(np.max(target_grid["target_l"])),
            }
        )
        attrs["periodic_mlt"] = "true"

    return {"attrs": attrs, "datasets": datasets, "summary": summary}


def build_mapping_metadata(mode, target_shape, source_grid=None, target_grid=None):
    if mode == "index":
        return {
            "mode": "index",
            "target_shape": [int(target_shape[0]), int(target_shape[1])],
            "physical_validity": "smoke_only",
            "note": "Normalized index-space resize; no physical L/MLT mapping.",
        }

    source_l = source_grid["source_l"]
    target_l = target_grid["target_l"]
    outside_l = (target_l < np.min(source_l)) | (target_l > np.max(source_l))
    source_lon = source_grid["source_lon_deg"]
    target_lon = target_grid["target_lon_deg"]
    return {
        "mode": "l_mlt",
        "source_grid_dir": source_grid["run_dir"],
        "target_template": target_grid["template"],
        "target_shape": [int(target_shape[0]), int(target_shape[1])],
        "source_l_formula": "median_nz_nlt((baltu/Re)/cos(blatu)^2)",
        "source_mlt_formula": "circular_mean_nz_nf(blonu) degrees",
        "target_l_formula": "1/sin(theta_cell_center)^2 from ShellGrid/theta",
        "target_mlt_formula": "ShellGrid/phi cell centers modulo 360 degrees",
        "periodic_mlt": True,
        "l_extrapolated_i_count": int(np.count_nonzero(outside_l)),
        "l_extrapolated_cell_count": int(np.count_nonzero(outside_l)) * int(target_lon.size),
        "l_extrapolated_fraction": (
            float(np.count_nonzero(outside_l)) / float(target_l.size)
            if target_l.size
            else 0.0
        ),
        "physical_validity": "prototype",
        "note": (
            "Prototype separable L/MLT interpolation.  L outside the source range "
            "is clamped to the nearest SAMI3 shell and counted as extrapolated. "
            "This is not yet a full Voltron traced-tube bvol mapping."
        ),
        "stats": source_grid["stats"] + target_grid["stats"],
    }


def infer_raicpl_template(path, expected_channels):
    h5py = require_moments_h5(path)
    with h5py.File(path, "r") as handle:
        if "Pavg" not in handle:
            raise KeyError("template is missing root dataset /Pavg: {0}".format(path))
        shape = tuple(handle["Pavg"].shape)
    if len(shape) != 3:
        raise ValueError("template /Pavg must be 3-D, got shape {0}".format(shape))
    n_channels, nj, ni = shape
    if n_channels != expected_channels:
        raise ValueError(
            "template channel count {0} does not match nFluidIn+1={1}".format(
                n_channels, expected_channels
            )
        )
    return {
        "template": os.path.abspath(path),
        "hdf5_shape": [int(n_channels), int(nj), int(ni)],
        "fortran_shape": [int(ni), int(nj), int(n_channels)],
        "target_2d_shape": [int(ni), int(nj)],
        "layout": "ReadInSGV runtime HDF5 order: channel, j, i",
    }


def build_raicpl_runtime_layout(
    arrays,
    n_channels,
    channel,
    target_shape,
    mapping_mode,
    source_metadata,
    sami3_grid_dir,
    template_path,
    mapping_weight_file,
):
    if mapping_mode == "index":
        mapped = {name: resize_2d(arrays[name], target_shape) for name in MOMENTS}
        mapping_metadata = build_mapping_metadata("index", target_shape)
        mapping_quality = build_mapping_quality("index", mapped, target_shape)
    elif mapping_mode == "l_mlt":
        if not template_path:
            raise ValueError("--mapping-mode l_mlt requires --raicpl-template")
        grid_dir = sami3_grid_dir or source_metadata.get("run_dir")
        if not grid_dir:
            raise ValueError(
                "--mapping-mode l_mlt requires --sami3-grid-dir or stage-1 run_dir metadata"
            )
        dims = source_metadata.get("dimensions", {})
        if "nz" not in dims:
            raise ValueError("stage-1 metadata is missing dimensions.nz")
        shape3 = (int(dims["nz"]), int(arrays["Pavg"].shape[0]), int(arrays["Pavg"].shape[1]))
        source_grid = read_sami3_l_mlt_grid(os.path.abspath(grid_dir), shape3)
        target_grid = read_raicpl_target_l_mlt(os.path.abspath(template_path), target_shape)
        mapped = {
            name: map_l_mlt_2d(arrays[name], source_grid, target_grid)
            for name in MOMENTS
        }
        mapping_metadata = build_mapping_metadata(
            "l_mlt", target_shape, source_grid=source_grid, target_grid=target_grid
        )
        mapping_quality = build_mapping_quality(
            "l_mlt", mapped, target_shape, source_grid=source_grid, target_grid=target_grid
        )
    elif mapping_mode == "weights":
        if not mapping_weight_file:
            raise ValueError("--mapping-mode weights requires --mapping-weight-file")
        weight_info = read_mapping_weight_file(
            os.path.abspath(mapping_weight_file), target_shape, arrays["Pavg"].shape
        )
        mapped = {
            name: map_weight_file_2d(arrays[name], weight_info)
            for name in MOMENTS
        }
        mapping_metadata = build_mapping_metadata_from_weights(target_shape, weight_info)
        mapping_quality = build_mapping_quality_from_weights(mapped, target_shape, weight_info)
    else:
        raise ValueError("unsupported mapping mode: {0}".format(mapping_mode))

    out = {}
    masks = {}
    for name in ("Pavg", "Davg", "Pstd", "Dstd"):
        out[name] = np.zeros((n_channels, target_shape[1], target_shape[0]), dtype=np.float32)
        masks[name] = np.zeros_like(out[name], dtype=np.float32)
        out[name][channel, :, :] = mapped[name].T.astype(np.float32)
        masks[name][channel, :, :] = np.isfinite(mapped[name]).T.astype(np.float32)
    out["tiote"] = mapped["tiote"].T.astype(np.float32)
    masks["tiote"] = np.isfinite(mapped["tiote"]).T.astype(np.float32)
    mapping_metadata["mapped_stats"] = [
        finite_stats("RaiCplMomentsOnly.Pavg_mapped", mapped["Pavg"]),
        finite_stats("RaiCplMomentsOnly.Davg_mapped", mapped["Davg"]),
        finite_stats("RaiCplMomentsOnly.Pstd_mapped", mapped["Pstd"]),
        finite_stats("RaiCplMomentsOnly.Dstd_mapped", mapped["Dstd"]),
        finite_stats("RaiCplMomentsOnly.tiote_mapped", mapped["tiote"]),
    ]
    mapping_metadata["quality_summary"] = mapping_quality["summary"]
    return out, masks, mapping_metadata, mapping_quality


def make_channel_array(arr, n_channels, channel):
    out = np.zeros((arr.shape[0], arr.shape[1], n_channels), dtype=np.float32)
    out[:, :, channel] = arr.astype(np.float32)
    return out


def make_channel_mask(arr, n_channels, channel):
    out = np.zeros((arr.shape[0], arr.shape[1], n_channels), dtype=np.float32)
    out[:, :, channel] = np.isfinite(arr).astype(np.float32)
    return out


def make_tubeshell_array(arr, channel):
    return make_channel_array(arr, MAXTUBEFLUIDS + 1, channel)


def make_tubeshell_mask(arr, channel):
    return make_channel_mask(arr, MAXTUBEFLUIDS + 1, channel)


def create_dataset(group, name, data, units, description):
    dset = group.create_dataset(name, data=data, compression="gzip", shuffle=True)
    dset.attrs["Units"] = units
    dset.attrs["Description"] = description
    return dset


def write_voltron_moment_fields(group, arrays, channel_arrays, masks):
    create_dataset(group, "avgP", channel_arrays["Pavg"], "nPa", "TubeShell avgP, absolute pressure")
    create_dataset(group, "avgN", channel_arrays["Davg"], "#/cc", "TubeShell avgN, number density")
    create_dataset(group, "stdP", channel_arrays["Pstd"], "nPa", "TubeShell stdP, absolute pressure std")
    create_dataset(group, "stdN", channel_arrays["Dstd"], "#/cc", "TubeShell stdN, absolute density std")
    create_dataset(group, "Tiote0", arrays["tiote"].astype(np.float32), "normalized", "TubeShell TioTe0/Tiote0")
    for name in ("avgP", "avgN", "stdP", "stdN"):
        src_name = {
            "avgP": "Pavg",
            "avgN": "Davg",
            "stdP": "Pstd",
            "stdN": "Dstd",
        }[name]
        create_dataset(
            group,
            "{0}_mask".format(name),
            masks[src_name],
            "logical",
            "diagnostic finite-value mask for {0}".format(name),
        )
    create_dataset(
        group,
        "Tiote0_mask",
        np.isfinite(arrays["tiote"]).astype(np.float32),
        "logical",
        "diagnostic finite-value mask for Tiote0",
    )


def write_raiju_coupler_fields(group, arrays, channel_arrays, masks):
    create_dataset(group, "Pavg", channel_arrays["Pavg"], "nPa", "RAIJU coupler Pavg")
    create_dataset(group, "Davg", channel_arrays["Davg"], "#/cc", "RAIJU coupler Davg")
    create_dataset(group, "Pstd", channel_arrays["Pstd"], "nPa", "RAIJU coupler Pstd, absolute")
    create_dataset(group, "Dstd", channel_arrays["Dstd"], "#/cc", "RAIJU coupler Dstd, absolute")
    create_dataset(group, "tiote", arrays["tiote"].astype(np.float32), "normalized", "RAIJU coupler tiote")
    for name in ("Pavg", "Davg", "Pstd", "Dstd"):
        create_dataset(
            group,
            "{0}_mask".format(name),
            masks[name],
            "logical",
            "diagnostic finite-value mask for {0}".format(name),
        )


def write_raiju_coupler_fields_runtime(group, runtime_arrays, runtime_masks):
    create_dataset(group, "Pavg", runtime_arrays["Pavg"], "nPa", "RAIJU coupler Pavg")
    create_dataset(group, "Davg", runtime_arrays["Davg"], "#/cc", "RAIJU coupler Davg")
    create_dataset(group, "Pstd", runtime_arrays["Pstd"], "nPa", "RAIJU coupler Pstd, absolute")
    create_dataset(group, "Dstd", runtime_arrays["Dstd"], "#/cc", "RAIJU coupler Dstd, absolute")
    create_dataset(group, "tiote", runtime_arrays["tiote"], "normalized", "RAIJU coupler tiote")
    for name in ("Pavg", "Davg", "Pstd", "Dstd", "tiote"):
        create_dataset(
            group,
            "{0}_mask".format(name),
            runtime_masks[name],
            "logical",
            "diagnostic finite-value mask for {0}".format(name),
        )


def write_mapping_quality(handle, mapping_quality):
    if mapping_quality is None:
        return
    group = handle.create_group("MappingQuality")
    for key, value in mapping_quality.get("attrs", {}).items():
        group.attrs[key] = value
    for name, spec in mapping_quality.get("datasets", {}).items():
        create_dataset(group, name, spec["data"], spec["units"], spec["description"])


def write_product(path, arrays, channel_arrays, masks, metadata):
    h5py = require_h5py()
    string_dtype = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as handle:
        handle.attrs["product"] = metadata["product"]
        handle.attrs["schema_version"] = metadata["schema_version"]
        handle.attrs["source_moments_h5"] = metadata["source_moments_h5"]
        handle.attrs["note"] = metadata["compatibility"]["note"]

        voltron = handle.create_group("Voltron")
        voltron.attrs["view"] = "TubeShell field-name view; not a full TubeShell restart"
        write_voltron_moment_fields(voltron, arrays, channel_arrays, masks)

        tubeshell = handle.create_group("TubeShellMomentsOnly")
        tubeshell.attrs["view"] = "TubeShell_T moments-only view with MAXTUBEFLUIDS+1 channels"
        tubeshell.attrs["warning"] = "Not a complete /TubeShell restart group"
        write_voltron_moment_fields(
            tubeshell,
            arrays,
            metadata["_internal_tubeshell_arrays"],
            metadata["_internal_tubeshell_masks"],
        )

        rai_cpl = handle.create_group("RAIJU_Coupler")
        rai_cpl.attrs["view"] = "raijuCoupler_T field-name view before raiCpl2RAIJU normalization"
        write_raiju_coupler_fields(rai_cpl, arrays, channel_arrays, masks)

        rai_cpl_moments = handle.create_group("RaiCplMomentsOnly")
        rai_cpl_moments.attrs["view"] = "raijuCoupler_T moments-only view; not a complete raiCpl restart"
        if metadata.get("_internal_raicpl_runtime_arrays") is not None:
            rai_cpl_moments.attrs["layout"] = "runtime ReadInSGV order: channel, j, i"
            write_raiju_coupler_fields_runtime(
                rai_cpl_moments,
                metadata["_internal_raicpl_runtime_arrays"],
                metadata["_internal_raicpl_runtime_masks"],
            )
        else:
            write_raiju_coupler_fields(rai_cpl_moments, arrays, channel_arrays, masks)

        rai_state = handle.create_group("RAIJU_State")
        rai_state.attrs["view"] = "RAIJU State arrays after raiCpl2RAIJU copy/normalization"
        create_dataset(rai_state, "Pavg", channel_arrays["Pavg"], "nPa", "RAIJU State Pavg")
        create_dataset(rai_state, "Davg", channel_arrays["Davg"], "#/cc", "RAIJU State Davg")
        create_dataset(
            rai_state,
            "Pstd",
            channel_arrays["Pstd_normalized"],
            "normalized",
            "RAIJU State Pstd = coupler Pstd / max(Pavg,TINY)",
        )
        create_dataset(
            rai_state,
            "Dstd",
            channel_arrays["Dstd_normalized"],
            "normalized",
            "RAIJU State Dstd = coupler Dstd / max(Davg,TINY)",
        )
        create_dataset(rai_state, "tiote", arrays["tiote"].astype(np.float32), "normalized", "RAIJU State tiote")

        write_mapping_quality(handle, metadata.get("_internal_mapping_quality"))

        meta = handle.create_group("metadata")
        meta.create_dataset(
            "json",
            data=json.dumps(
                {k: v for k, v in metadata.items() if not k.startswith("_internal_")},
                indent=2,
                sort_keys=True,
            ),
            dtype=string_dtype,
        )


def main():
    args = parse_args()
    if args.n_fluid_in < 0 or args.n_fluid_in > MAXTUBEFLUIDS:
        raise ValueError(
            "--n-fluid-in must be between 0 and {0}".format(MAXTUBEFLUIDS)
        )
    n_channels = args.n_fluid_in + 1
    if args.bulk_channel < 0 or args.bulk_channel >= n_channels:
        raise ValueError(
            "--bulk-channel {0} outside channel range 0..{1}".format(
                args.bulk_channel, n_channels - 1
            )
        )

    moments_h5 = os.path.abspath(args.moments_h5)
    out_h5, out_json = output_paths(args.out)
    out_dir = os.path.dirname(out_h5)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    arrays, source_metadata, source_attrs, source_selection = read_moments(
        moments_h5, args.density_mode, args.pressure_mode
    )
    nonfinite = {
        name: int(arr.size - np.count_nonzero(np.isfinite(arr)))
        for name, arr in arrays.items()
    }
    if not args.allow_nonfinite:
        bad = {name: count for name, count in nonfinite.items() if count > 0}
        if bad:
            raise ValueError("required moment arrays contain non-finite values: {0}".format(bad))

    pstd_norm = arrays["Pstd"] / np.maximum(arrays["Pavg"], TINY)
    dstd_norm = arrays["Dstd"] / np.maximum(arrays["Davg"], TINY)

    raicpl_runtime_layout = None
    raicpl_runtime_arrays = None
    raicpl_runtime_masks = None
    raicpl_runtime_mapping = None
    raicpl_runtime_mapping_quality = None
    if args.raicpl_template:
        raicpl_runtime_layout = infer_raicpl_template(args.raicpl_template, n_channels)
    if args.target_raicpl_shape:
        ni, nj = args.target_raicpl_shape
        raicpl_runtime_layout = {
            "template": os.path.abspath(args.raicpl_template) if args.raicpl_template else None,
            "hdf5_shape": [int(n_channels), int(nj), int(ni)],
            "fortran_shape": [int(ni), int(nj), int(n_channels)],
            "target_2d_shape": [int(ni), int(nj)],
            "layout": "ReadInSGV runtime HDF5 order: channel, j, i",
        }
    if (
        args.mapping_mode == "weights"
        and args.mapping_weight_file
        and raicpl_runtime_layout is None
    ):
        ni, nj = peek_mapping_weight_target_shape(args.mapping_weight_file)
        raicpl_runtime_layout = {
            "template": os.path.abspath(args.raicpl_template) if args.raicpl_template else None,
            "mapping_weight_file": os.path.abspath(args.mapping_weight_file),
            "hdf5_shape": [int(n_channels), int(nj), int(ni)],
            "fortran_shape": [int(ni), int(nj), int(n_channels)],
            "target_2d_shape": [int(ni), int(nj)],
            "layout": "ReadInSGV runtime HDF5 order: channel, j, i",
        }
    if raicpl_runtime_layout is not None:
        target_shape = tuple(raicpl_runtime_layout["target_2d_shape"])
        (
            raicpl_runtime_arrays,
            raicpl_runtime_masks,
            raicpl_runtime_mapping,
            raicpl_runtime_mapping_quality,
        ) = build_raicpl_runtime_layout(
            arrays,
            n_channels,
            args.bulk_channel,
            target_shape,
            args.mapping_mode,
            source_metadata,
            args.sami3_grid_dir,
            args.raicpl_template,
            args.mapping_weight_file,
        )
        raicpl_runtime_layout["mapping_mode"] = args.mapping_mode
    elif args.mapping_mode != "index":
        raise ValueError("--mapping-mode {0} requires a runtime target layout".format(args.mapping_mode))

    channel_arrays = {
        "Pavg": make_channel_array(arrays["Pavg"], n_channels, args.bulk_channel),
        "Davg": make_channel_array(arrays["Davg"], n_channels, args.bulk_channel),
        "Pstd": make_channel_array(arrays["Pstd"], n_channels, args.bulk_channel),
        "Dstd": make_channel_array(arrays["Dstd"], n_channels, args.bulk_channel),
        "Pstd_normalized": make_channel_array(pstd_norm, n_channels, args.bulk_channel),
        "Dstd_normalized": make_channel_array(dstd_norm, n_channels, args.bulk_channel),
    }
    masks = {
        "Pavg": make_channel_mask(arrays["Pavg"], n_channels, args.bulk_channel),
        "Davg": make_channel_mask(arrays["Davg"], n_channels, args.bulk_channel),
        "Pstd": make_channel_mask(arrays["Pstd"], n_channels, args.bulk_channel),
        "Dstd": make_channel_mask(arrays["Dstd"], n_channels, args.bulk_channel),
    }
    tubeshell_arrays = {
        "Pavg": make_tubeshell_array(arrays["Pavg"], args.bulk_channel),
        "Davg": make_tubeshell_array(arrays["Davg"], args.bulk_channel),
        "Pstd": make_tubeshell_array(arrays["Pstd"], args.bulk_channel),
        "Dstd": make_tubeshell_array(arrays["Dstd"], args.bulk_channel),
    }
    tubeshell_masks = {
        "Pavg": make_tubeshell_mask(arrays["Pavg"], args.bulk_channel),
        "Davg": make_tubeshell_mask(arrays["Davg"], args.bulk_channel),
        "Pstd": make_tubeshell_mask(arrays["Pstd"], args.bulk_channel),
        "Dstd": make_tubeshell_mask(arrays["Dstd"], args.bulk_channel),
    }

    metadata = {
        "product": "sami3_voltron_raiju_moments_diagnostic",
        "schema_version": 1,
        "source_moments_h5": moments_h5,
        "output_hdf5": out_h5,
        "nFluidIn": args.n_fluid_in,
        "n_channels": n_channels,
        "MAXTUBEFLUIDS": MAXTUBEFLUIDS,
        "tubeshell_moments_channels": MAXTUBEFLUIDS + 1,
        "bulk_channel": args.bulk_channel,
        "density_mode": args.density_mode,
        "pressure_mode": args.pressure_mode,
        "moment_source_selection": source_selection,
        "raicpl_runtime_mapping": raicpl_runtime_mapping,
        "raicpl_runtime_mapping_quality": (
            raicpl_runtime_mapping_quality["summary"]
            if raicpl_runtime_mapping_quality is not None
            else None
        ),
        "std_source_warning": (
            "Pstd/Dstd are still read from the existing ion/number-density std fields. "
            "For massEq density, total pressure, or prototype weighted-moment runs, "
            "use runtime alphaPstd/alphaDstd=0 unless matching std definitions are added."
        ),
        "channel_semantics": {
            str(args.bulk_channel): "bulk SAMI3 ion moment mapped to MAGE BLK channel",
        },
        "mage_read_groups": {
            "/TubeShellMomentsOnly": "moments-only TubeShell_T field group; avgP/avgN/stdP/stdN have MAXTUBEFLUIDS+1 channels",
            "/RaiCplMomentsOnly": "moments-only raijuCoupler_T field group; Pavg/Davg/Pstd/Dstd have nFluidIn+1 channels",
        },
        "source_metadata": source_metadata,
        "source_attrs": {
            name: {key: decode_h5_text(value) for key, value in attrs.items()}
            for name, attrs in source_attrs.items()
        },
        "units": {
            "Voltron.avgP": "nPa",
            "Voltron.avgN": "#/cc",
            "Voltron.stdP": "nPa absolute",
            "Voltron.stdN": "#/cc absolute",
            "Voltron.Tiote0": "normalized Ti/Te",
            "RAIJU_Coupler.Pstd": "nPa absolute",
            "RAIJU_Coupler.Dstd": "#/cc absolute",
            "TubeShellMomentsOnly.stdP": "nPa absolute",
            "TubeShellMomentsOnly.stdN": "#/cc absolute",
            "RAIJU_State.Pstd": "normalized by Pavg",
            "RAIJU_State.Dstd": "normalized by Davg",
        },
        "normalization": {
            "Pstd": "RAIJU_State.Pstd = RAIJU_Coupler.Pstd / max(Pavg, 1e-30)",
            "Dstd": "RAIJU_State.Dstd = RAIJU_Coupler.Dstd / max(Davg, 1e-30)",
        },
        "compatibility": {
            "tube_shell_restart": False,
            "rai_cpl_restart": False,
            "gamera_equation_change": False,
            "note": (
                "Field-name and unit diagnostic product only; a production restart "
                "requires ShellGrid, topology, magnetic geometry, potentials, masks, and timing."
            ),
        },
        "_internal_tubeshell_arrays": tubeshell_arrays,
        "_internal_tubeshell_masks": tubeshell_masks,
        "_internal_raicpl_runtime_arrays": raicpl_runtime_arrays,
        "_internal_raicpl_runtime_masks": raicpl_runtime_masks,
        "_internal_mapping_quality": raicpl_runtime_mapping_quality,
        "raicpl_runtime_layout": raicpl_runtime_layout,
        "validation": {
            "nonfinite_counts": nonfinite,
            "negative_or_zero_counts": {
                "Pavg": int(np.count_nonzero(arrays["Pavg"] <= 0.0)),
                "Davg": int(np.count_nonzero(arrays["Davg"] <= 0.0)),
                "tiote": int(np.count_nonzero(arrays["tiote"] <= 0.0)),
            },
        },
        "stats": [
            finite_stats("Voltron.avgP/RAIJU.Pavg", arrays["Pavg"]),
            finite_stats("Voltron.avgN/RAIJU.Davg", arrays["Davg"]),
            finite_stats("Voltron.stdP absolute", arrays["Pstd"]),
            finite_stats("Voltron.stdN absolute", arrays["Dstd"]),
            finite_stats("RAIJU_State.Pstd normalized", pstd_norm),
            finite_stats("RAIJU_State.Dstd normalized", dstd_norm),
            finite_stats("tiote", arrays["tiote"]),
        ]
        + (raicpl_runtime_mapping.get("mapped_stats", []) if raicpl_runtime_mapping else []),
    }

    write_product(out_h5, arrays, channel_arrays, masks, metadata)
    with open(out_json, "w") as handle:
        json.dump(
            {k: v for k, v in metadata.items() if not k.startswith("_internal_")},
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    print("wrote {0}".format(out_h5))
    print("wrote {0}".format(out_json))
    for item in metadata["stats"]:
        print(
            "{name}: shape={shape} finite={finite_count}/{total_count} min={min} max={max} mean={mean}".format(
                **item
            )
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        sys.exit(1)
