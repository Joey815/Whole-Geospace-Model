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


MAXTUBEFLUIDS = 5
TINY = 1.0e-30
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


def build_raicpl_runtime_layout(arrays, n_channels, channel, target_shape):
    resized = {name: resize_2d(arrays[name], target_shape) for name in MOMENTS}
    out = {}
    masks = {}
    for name in ("Pavg", "Davg", "Pstd", "Dstd"):
        out[name] = np.zeros((n_channels, target_shape[1], target_shape[0]), dtype=np.float32)
        masks[name] = np.zeros_like(out[name], dtype=np.float32)
        out[name][channel, :, :] = resized[name].T.astype(np.float32)
        masks[name][channel, :, :] = np.isfinite(resized[name]).T.astype(np.float32)
    out["tiote"] = resized["tiote"].T.astype(np.float32)
    masks["tiote"] = np.isfinite(resized["tiote"]).T.astype(np.float32)
    return out, masks


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
    if raicpl_runtime_layout is not None:
        target_shape = tuple(raicpl_runtime_layout["target_2d_shape"])
        raicpl_runtime_arrays, raicpl_runtime_masks = build_raicpl_runtime_layout(
            arrays, n_channels, args.bulk_channel, target_shape
        )

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
        ],
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
