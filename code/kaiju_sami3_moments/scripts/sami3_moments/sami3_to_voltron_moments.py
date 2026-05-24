#!/usr/bin/env python3
"""Build diagnostic Voltron-style plasma moments from SAMI3 output files.

This is an offline sidecar adapter.  It reads SAMI3 sequential-unformatted
regular output arrays and writes HDF5/NPZ plus JSON metadata products with
Pavg, Davg, Pstd, Dstd, and tiote fields.  It intentionally does not write a
full TubeShell restart because that also requires matching ShellGrid metadata.
"""

import argparse
import json
import os
import struct
import sys

import numpy as np


NZ = 304
NF = 124
NLT = 96
NION = 7
ION_NAMES = ("H+", "O+", "NO+", "O2+", "He+", "N2+", "N+")
ION_MASS_AMU = np.array((1.0, 16.0, 30.0, 32.0, 4.0, 28.0, 14.0), dtype=np.float64)
ION_FRACTION_NAMES = ("f_H", "f_O", "f_NO", "f_O2", "f_He", "f_N2", "f_N")
KB_CGS_TO_NPA = 1.38044e-8
TINY = 1.0e-30


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute diagnostic SAMI3 -> Voltron moments."
    )
    parser.add_argument("run_dir", help="SAMI3 output directory")
    parser.add_argument(
        "--out",
        required=True,
        help="Output prefix or .h5/.npz path. A matching .json metadata file is written.",
    )
    parser.add_argument(
        "--format",
        choices=("hdf5", "npz", "both"),
        default="hdf5",
        help="Output format. Default: hdf5.",
    )
    parser.add_argument(
        "--record",
        default="last",
        help="Fortran record to read: 'last' or a zero-based integer. Default: last.",
    )
    parser.add_argument(
        "--nz", type=int, default=NZ, help="SAMI3 nz dimension. Default: 304."
    )
    parser.add_argument(
        "--nf", type=int, default=NF, help="SAMI3 nf dimension. Default: 124."
    )
    parser.add_argument(
        "--nlt", type=int, default=NLT, help="SAMI3 nlt dimension. Default: 96."
    )
    parser.add_argument(
        "--weight-mode",
        choices=("simple", "external", "ds_over_B"),
        default=None,
        help=(
            "Moment weighting contract. Default is inferred: simple when "
            "--weight-file is omitted, external when --weight-file is present. "
            "ds_over_B builds prototype flux-tube weights from xsu/ysu/zsu/bmstu."
        ),
    )
    parser.add_argument(
        "--weight-file",
        default=None,
        help=(
            "Optional Fortran-unformatted weight array with shape (nz,nf,nlt). "
            "If omitted, simple along-field averaging is used."
        ),
    )
    parser.add_argument(
        "--weight-bmin",
        type=float,
        default=1.0e-4,
        help=(
            "Minimum normalized B/B0 used by --weight-mode ds_over_B. "
            "Default: 1.0e-4."
        ),
    )
    parser.add_argument(
        "--no-coords",
        action="store_true",
        help="Do not attempt to include mean zalt/glat/glon coordinate arrays.",
    )
    return parser.parse_args()


def strip_known_suffix(path):
    for suffix in (".hdf5", ".h5", ".npz"):
        if path.endswith(suffix):
            return path[: -len(suffix)]
    return path


def output_paths(out_arg, fmt):
    prefix = strip_known_suffix(out_arg)
    h5_path = prefix + ".h5"
    npz_path = prefix + ".npz"
    json_path = prefix + ".json"
    if fmt == "hdf5":
        return h5_path, None, json_path
    if fmt == "npz":
        return None, npz_path, json_path
    return h5_path, npz_path, json_path


def resolve_record_index(record_arg, n_records):
    if n_records < 1:
        raise ValueError("no records found")
    if record_arg == "last":
        return n_records - 1
    try:
        idx = int(record_arg)
    except ValueError:
        raise ValueError("--record must be 'last' or a zero-based integer")
    if idx < 0 or idx >= n_records:
        raise ValueError(
            "record index {0} outside available range 0..{1}".format(
                idx, n_records - 1
            )
        )
    return idx


def count_fortran_records(path, n_values, dtype):
    record_bytes = np.dtype(dtype).itemsize * n_values
    file_bytes = os.path.getsize(path)
    stride = record_bytes + 8
    if file_bytes % stride != 0:
        raise ValueError(
            "{0}: size {1} is not an integer number of {2}-byte records".format(
                path, file_bytes, stride
            )
        )
    return file_bytes // stride


def read_fortran_record(path, shape, record_arg="last", dtype="<f4"):
    n_values = int(np.prod(shape))
    dtype_np = np.dtype(dtype)
    record_bytes = dtype_np.itemsize * n_values
    n_records = count_fortran_records(path, n_values, dtype_np)
    rec_idx = resolve_record_index(record_arg, n_records)
    offset = rec_idx * (record_bytes + 8)
    with open(path, "rb") as handle:
        handle.seek(offset)
        lead = handle.read(4)
        if len(lead) != 4:
            raise ValueError("{0}: could not read leading record marker".format(path))
        marker = struct.unpack("<i", lead)[0]
        if marker != record_bytes:
            marker_be = struct.unpack(">i", lead)[0]
            if marker_be == record_bytes:
                raise ValueError(
                    "{0}: big-endian record markers are not supported yet".format(path)
                )
            raise ValueError(
                "{0}: record marker {1} != expected {2}".format(
                    path, marker, record_bytes
                )
            )
        raw = np.fromfile(handle, dtype=dtype_np, count=n_values)
        if raw.size != n_values:
            raise ValueError(
                "{0}: expected {1} values, read {2}".format(
                    path, n_values, raw.size
                )
            )
        trail = handle.read(4)
        if len(trail) != 4:
            raise ValueError("{0}: could not read trailing record marker".format(path))
        marker2 = struct.unpack("<i", trail)[0]
        if marker2 != record_bytes:
            raise ValueError(
                "{0}: trailing marker {1} != expected {2}".format(
                    path, marker2, record_bytes
                )
            )
    return raw.reshape(shape, order="F"), rec_idx, n_records


def require_file(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    return path


def weighted_mean(values, weights, axis=0):
    wsum = np.sum(weights, axis=axis)
    return np.sum(values * weights, axis=axis) / np.maximum(wsum, TINY)


def weighted_std(values, weights, mean, axis=0):
    wsum = np.sum(weights, axis=axis)
    diff = values - np.expand_dims(mean, axis=axis)
    return np.sqrt(np.sum(weights * diff * diff, axis=axis) / np.maximum(wsum, TINY))


def finite_stats(name, arr):
    finite = np.isfinite(arr)
    if not np.any(finite):
        return {
            "name": name,
            "shape": list(arr.shape),
            "finite_count": 0,
            "min": None,
            "max": None,
            "mean": None,
        }
    vals = arr[finite]
    return {
        "name": name,
        "shape": list(arr.shape),
        "finite_count": int(vals.size),
        "min": float(np.min(vals)),
        "max": float(np.max(vals)),
        "mean": float(np.mean(vals)),
    }


def read_time_table(path):
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, "r") as handle:
        for line in handle:
            parts = line.split()
            if not parts:
                continue
            rows.append(parts)
    return rows


def write_hdf5(path, arrays, metadata):
    try:
        import h5py
    except Exception as exc:
        raise RuntimeError(
            "h5py is required for --format hdf5/both; use the mage-vis venv or --format npz"
        ) from exc

    string_dtype = h5py.string_dtype(encoding="utf-8")
    with h5py.File(path, "w") as handle:
        handle.attrs["product"] = metadata["product"]
        handle.attrs["schema_version"] = metadata["schema_version"]
        handle.attrs["note"] = metadata["compatibility"]["note"]
        handle.attrs["moment_weighting"] = metadata["moment_weighting"]
        handle.attrs["physical_validity"] = metadata["physical_validity"]

        moments = handle.create_group("moments")
        moments.attrs["moment_weighting"] = metadata["moment_weighting"]
        moments.attrs["physical_validity"] = metadata["physical_validity"]
        for name in (
            "Pavg",
            "Davg",
            "Pstd",
            "Dstd",
            "tiote",
            "Ti_eff",
            "Te_eff",
            "Davg_num",
            "Davg_massEq",
            "mu_eff",
            "Pavg_i",
            "Pavg_e",
            "Pavg_total",
        ):
            dataset = moments.create_dataset(
                name, data=arrays[name], compression="gzip", shuffle=True
            )
            if name in ("Pavg", "Pstd", "Pavg_i", "Pavg_e", "Pavg_total"):
                dataset.attrs["units"] = "nPa"
            elif name in ("Davg", "Dstd", "Davg_num"):
                dataset.attrs["units"] = "#/cc"
            elif name == "Davg_massEq":
                dataset.attrs["units"] = "proton_equivalent_#/cc"
            elif name in ("Ti_eff", "Te_eff"):
                dataset.attrs["units"] = "K"
            else:
                dataset.attrs["units"] = "normalized"

        species = handle.create_group("species")
        species.create_dataset("ion_order", data=np.array(ION_NAMES, dtype=object), dtype=string_dtype)
        dset = species.create_dataset(
            "Pavg_ion", data=arrays["Pavg_ion"], compression="gzip", shuffle=True
        )
        dset.attrs["units"] = "nPa"
        dset = species.create_dataset(
            "Davg_ion", data=arrays["Davg_ion"], compression="gzip", shuffle=True
        )
        dset.attrs["units"] = "#/cc"
        for name in ION_FRACTION_NAMES + ("f_molecular",):
            dset = species.create_dataset(
                name, data=arrays[name], compression="gzip", shuffle=True
            )
            dset.attrs["units"] = "fraction"

        coords = handle.create_group("coords")
        for name, value in arrays.items():
            if name.endswith("_mean_km") or name.endswith("_mean_deg"):
                dset = coords.create_dataset(name, data=value, compression="gzip", shuffle=True)
                dset.attrs["units"] = "km" if name.endswith("_km") else "deg"

        meta = handle.create_group("metadata")
        meta.create_dataset("json", data=json.dumps(metadata, indent=2, sort_keys=True), dtype=string_dtype)


def maybe_read_coord(run_dir, name, shape, record_arg):
    path = os.path.join(run_dir, name)
    if not os.path.isfile(path):
        return None
    arr, _, _ = read_fortran_record(path, shape, record_arg)
    return np.mean(arr, axis=0).astype(np.float32)


def build_ds_over_b_weights(run_dir, shape, bmin):
    """Build prototype flux-tube-volume weights proportional to ds/B.

    SAMI3 writes xsu/ysu/zsu on the s-grid in km and bmstu as b/b0.  The
    absolute constants cancel in weighted means, so we use km/(b/b0).
    """
    if shape[0] < 2:
        raise ValueError("ds_over_B weighting requires nz >= 2")
    if not np.isfinite(bmin) or bmin <= 0.0:
        raise ValueError("--weight-bmin must be finite and positive")

    grid = {}
    records = {}
    for fname, key in (
        ("xsu.dat", "x"),
        ("ysu.dat", "y"),
        ("zsu.dat", "z"),
        ("bmstu.dat", "bms"),
    ):
        arr, rec_idx, n_rec = read_fortran_record(
            require_file(os.path.join(run_dir, fname)), shape, "last"
        )
        grid[key] = arr.astype(np.float64)
        records[fname] = {
            "record_index": int(rec_idx),
            "record_count": int(n_rec),
        }

    ds = np.empty(shape, dtype=np.float64)
    dx = np.diff(grid["x"], axis=0)
    dy = np.diff(grid["y"], axis=0)
    dz = np.diff(grid["z"], axis=0)
    ds[:-1, :, :] = np.sqrt(dx * dx + dy * dy + dz * dz)
    ds[-1, :, :] = ds[-2, :, :]

    bad_bms = np.count_nonzero((~np.isfinite(grid["bms"])) | (grid["bms"] <= 0.0))
    if bad_bms:
        raise ValueError("bmstu.dat contains {0} non-finite/non-positive cells".format(int(bad_bms)))

    bms_floor_hits = grid["bms"] < bmin
    bms_eff = np.where(bms_floor_hits, bmin, grid["bms"])
    weights = ds / bms_eff
    bad = np.count_nonzero((~np.isfinite(weights)) | (weights <= 0.0))
    if bad:
        raise ValueError("ds_over_B weights contain {0} non-finite/non-positive cells".format(int(bad)))

    metadata = {
        "mode": "ds_over_B",
        "source": "xsu/ysu/zsu center spacing divided by bmstu",
        "grid_files": records,
        "ds_units": "km",
        "b_source": "bmstu.dat, normalized B=b/b0",
        "bms_floor": float(bmin),
        "bms_floor_hit_count": int(np.count_nonzero(bms_floor_hits)),
        "bms_floor_hit_fraction": float(np.count_nonzero(bms_floor_hits)) / float(np.prod(shape)),
        "physical_validity": "prototype",
        "note": (
            "Weights are proportional to ds/B using SAMI3 s-grid centers. "
            "This is a prototype flux-tube-volume quadrature, not yet a "
            "Voltron traced-tube bvol-aligned production mapping.  The "
            "normalized magnetic field is floored by --weight-bmin to prevent "
            "pathological near-zero bmstu samples from dominating the mean."
        ),
        "stats": [
            finite_stats("ds_km", ds),
            finite_stats("bms", grid["bms"]),
            finite_stats("bms_effective", bms_eff),
            finite_stats("ds_over_B_weight", weights),
        ],
    }
    return weights, metadata, records


def main():
    args = parse_args()
    run_dir = os.path.abspath(args.run_dir)
    shape = (args.nz, args.nf, args.nlt)
    h5_path, npz_path, json_path = output_paths(os.path.abspath(args.out), args.format)
    first_out = h5_path or npz_path
    out_dir = os.path.dirname(first_out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    deni = []
    ti = []
    records = {}
    for ion_idx in range(1, NION + 1):
        den_path = require_file(os.path.join(run_dir, "deni{0}u.dat".format(ion_idx)))
        ti_path = require_file(os.path.join(run_dir, "ti{0}u.dat".format(ion_idx)))
        den_arr, rec_idx, n_rec = read_fortran_record(den_path, shape, args.record)
        ti_arr, ti_rec_idx, ti_n_rec = read_fortran_record(ti_path, shape, args.record)
        deni.append(den_arr.astype(np.float64))
        ti.append(ti_arr.astype(np.float64))
        records[os.path.basename(den_path)] = {
            "record_index": int(rec_idx),
            "record_count": int(n_rec),
        }
        records[os.path.basename(ti_path)] = {
            "record_index": int(ti_rec_idx),
            "record_count": int(ti_n_rec),
        }

    te_path = require_file(os.path.join(run_dir, "teu.dat"))
    te, te_rec_idx, te_n_rec = read_fortran_record(te_path, shape, args.record)
    te = te.astype(np.float64)
    records["teu.dat"] = {
        "record_index": int(te_rec_idx),
        "record_count": int(te_n_rec),
    }

    deni_stack = np.stack(deni, axis=0)
    ti_stack = np.stack(ti, axis=0)

    weight_mode = args.weight_mode
    if weight_mode is None:
        weight_mode = "external" if args.weight_file else "simple"
    if weight_mode == "external" and not args.weight_file:
        raise ValueError("--weight-mode external requires --weight-file")
    if weight_mode in ("simple", "ds_over_B") and args.weight_file:
        raise ValueError("--weight-mode {0} cannot be combined with --weight-file".format(weight_mode))

    dene_path = os.path.join(run_dir, "deneu.dat")
    if os.path.isfile(dene_path):
        ne, ne_rec_idx, ne_n_rec = read_fortran_record(dene_path, shape, args.record)
        ne = ne.astype(np.float64)
        ne_source = "deneu.dat"
        records["deneu.dat"] = {
            "record_index": int(ne_rec_idx),
            "record_count": int(ne_n_rec),
        }
    else:
        ne = np.sum(deni_stack, axis=0)
        ne_source = "sum(deni1..deni7)"

    if weight_mode == "external":
        weights, w_rec_idx, w_n_rec = read_fortran_record(
            os.path.abspath(args.weight_file), shape, args.record
        )
        weights = weights.astype(np.float64)
        weighting = {
            "mode": "external",
            "source": "fortran_unformatted_weight_file",
            "path": os.path.abspath(args.weight_file),
            "record_index": int(w_rec_idx),
            "record_count": int(w_n_rec),
            "physical_validity": "prototype",
            "note": (
                "External weights are interpreted as moment quadrature weights; "
                "the product is only physically meaningful if the file encodes "
                "ds/B, SAMI3 cell volume, or Voltron-equivalent flux-tube weights."
            ),
        }
    elif weight_mode == "ds_over_B":
        weights, weighting, weight_records = build_ds_over_b_weights(run_dir, shape, args.weight_bmin)
        records.update(weight_records)
    else:
        weights = np.ones(shape, dtype=np.float64)
        weighting = {
            "mode": "simple",
            "source": "unit_weights_along_sami3_nz",
            "physical_validity": "smoke_only",
            "note": "No SAMI3 vol array was provided; output is not a true Voltron flux-tube-volume moment.",
        }

    n_total = np.sum(deni_stack, axis=0)
    n_mass_equiv = np.sum(ION_MASS_AMU[:, None, None, None] * deni_stack, axis=0)
    p_ion = deni_stack * ti_stack * KB_CGS_TO_NPA
    p_total = np.sum(p_ion, axis=0)
    p_e = ne * te * KB_CGS_TO_NPA

    davg = weighted_mean(n_total, weights, axis=0)
    davg_mass_equiv = weighted_mean(n_mass_equiv, weights, axis=0)
    mu_eff = davg_mass_equiv / np.maximum(davg, TINY)
    pavg = weighted_mean(p_total, weights, axis=0)
    pavg_e = weighted_mean(p_e, weights, axis=0)
    pavg_total = weighted_mean(p_total + p_e, weights, axis=0)
    dstd = weighted_std(n_total, weights, davg, axis=0)
    pstd = weighted_std(p_total, weights, pavg, axis=0)

    davg_ion = np.empty((NION, args.nf, args.nlt), dtype=np.float64)
    pavg_ion = np.empty((NION, args.nf, args.nlt), dtype=np.float64)
    for ion_idx in range(NION):
        davg_ion[ion_idx] = weighted_mean(deni_stack[ion_idx], weights, axis=0)
        pavg_ion[ion_idx] = weighted_mean(p_ion[ion_idx], weights, axis=0)
    ion_fraction = davg_ion / np.maximum(davg[None, :, :], TINY)
    f_molecular = ion_fraction[2] + ion_fraction[3] + ion_fraction[5]

    ti_num = np.sum(weights[None, :, :, :] * deni_stack * ti_stack, axis=(0, 1))
    ti_den = np.sum(weights[None, :, :, :] * deni_stack, axis=(0, 1))
    ti_eff = ti_num / np.maximum(ti_den, TINY)
    te_eff = np.sum(weights * ne * te, axis=0) / np.maximum(
        np.sum(weights * ne, axis=0), TINY
    )
    tiote = ti_eff / np.maximum(te_eff, TINY)

    arrays = {
        "Pavg": pavg.astype(np.float32),
        "Davg": davg.astype(np.float32),
        "Pstd": pstd.astype(np.float32),
        "Dstd": dstd.astype(np.float32),
        "tiote": tiote.astype(np.float32),
        "Davg_num": davg.astype(np.float32),
        "Davg_massEq": davg_mass_equiv.astype(np.float32),
        "mu_eff": mu_eff.astype(np.float32),
        "Pavg_i": pavg.astype(np.float32),
        "Pavg_e": pavg_e.astype(np.float32),
        "Pavg_total": pavg_total.astype(np.float32),
        "Pavg_ion": pavg_ion.astype(np.float32),
        "Davg_ion": davg_ion.astype(np.float32),
        "Ti_eff": ti_eff.astype(np.float32),
        "Te_eff": te_eff.astype(np.float32),
        "f_molecular": f_molecular.astype(np.float32),
    }
    for idx, name in enumerate(ION_FRACTION_NAMES):
        arrays[name] = ion_fraction[idx].astype(np.float32)

    coord_sources = {}
    if not args.no_coords:
        for fname, out_name in (
            ("zaltu.dat", "zalt_mean_km"),
            ("glatu.dat", "glat_mean_deg"),
            ("glonu.dat", "glon_mean_deg"),
            ("baltu.dat", "balt_mean_km"),
            ("blatu.dat", "blat_mean_deg"),
            ("blonu.dat", "blon_mean_deg"),
        ):
            coord = maybe_read_coord(run_dir, fname, shape, args.record)
            if coord is not None:
                arrays[out_name] = coord
                coord_sources[out_name] = fname

    metadata = {
        "product": "sami3_voltron_moments_diagnostic",
        "schema_version": 1,
        "run_dir": run_dir,
        "output_hdf5": h5_path,
        "output_npz": npz_path,
        "dimensions": {"nz": args.nz, "nf": args.nf, "nlt": args.nlt, "nion": NION},
        "ion_order": list(ION_NAMES),
        "ion_mass_amu": ION_MASS_AMU.tolist(),
        "records": records,
        "time_rows": read_time_table(os.path.join(run_dir, "time.dat")),
        "density_units": "#/cc",
        "pressure_units": "nPa",
        "temperature_units": "K",
        "std_units": {
            "Pstd": "nPa absolute; RAIJU normalizes later",
            "Dstd": "#/cc absolute; RAIJU normalizes later",
        },
        "density_semantics": {
            "Davg": "alias for Davg_num; total ion number density",
            "Davg_num": "sum_i n_i, #/cc",
            "Davg_massEq": "sum_i A_i n_i, proton-equivalent #/cc",
            "mu_eff": "Davg_massEq / Davg_num",
        },
        "pressure_semantics": {
            "Pavg": "alias for Pavg_i; total ion pressure",
            "Pavg_i": "sum_i n_i kB Ti_i, nPa",
            "Pavg_e": "ne kB Te, nPa",
            "Pavg_total": "Pavg_i + Pavg_e, nPa",
        },
        "pressure_conversion": {
            "formula": "p_nPa = deni_cm3 * ti_K * 1.38044e-8",
            "kB_cgs_times_dyn_cm2_to_nPa": KB_CGS_TO_NPA,
        },
        "ne_source": ne_source,
        "moment_weighting": weighting["mode"],
        "physical_validity": weighting["physical_validity"],
        "weighting": weighting,
        "coordinate_sources": coord_sources,
        "compatibility": {
            "target_fields": ["Pavg", "Davg", "Pstd", "Dstd", "tiote"],
            "intermediate_hdf5": h5_path is not None,
            "tube_shell_restart": False,
            "note": "This is a diagnostic intermediate product, not a complete Voltron TubeShell restart.",
        },
        "stats": [
            finite_stats("Pavg", arrays["Pavg"]),
            finite_stats("Davg", arrays["Davg"]),
            finite_stats("Pstd", arrays["Pstd"]),
            finite_stats("Dstd", arrays["Dstd"]),
            finite_stats("tiote", arrays["tiote"]),
            finite_stats("Davg_massEq", arrays["Davg_massEq"]),
            finite_stats("mu_eff", arrays["mu_eff"]),
            finite_stats("Pavg_e", arrays["Pavg_e"]),
            finite_stats("Pavg_total", arrays["Pavg_total"]),
            finite_stats("f_molecular", arrays["f_molecular"]),
            finite_stats("Ti_eff", arrays["Ti_eff"]),
            finite_stats("Te_eff", arrays["Te_eff"]),
        ],
    }

    if h5_path is not None:
        write_hdf5(h5_path, arrays, metadata)
    if npz_path is not None:
        np.savez_compressed(npz_path, **arrays)

    with open(json_path, "w") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")

    if h5_path is not None:
        print("wrote {0}".format(h5_path))
    if npz_path is not None:
        print("wrote {0}".format(npz_path))
    print("wrote {0}".format(json_path))
    for item in metadata["stats"]:
        print(
            "{name}: shape={shape} finite={finite_count} min={min} max={max} mean={mean}".format(
                **item
            )
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        sys.exit(1)
