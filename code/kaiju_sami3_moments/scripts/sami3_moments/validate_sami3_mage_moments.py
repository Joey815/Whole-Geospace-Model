#!/usr/bin/env python3
"""Validate SAMI3 moments products against the local MAGE moment contracts."""

import argparse
import json
import os
import sys

import numpy as np


MAXTUBEFLUIDS = 5
TINY = 1.0e-30


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate SAMI3 moments and Voltron/RAIJU diagnostic HDF5 products."
    )
    parser.add_argument("moments_h5", help="Stage-1 moments HDF5")
    parser.add_argument("diag_h5", help="Stage-2 Voltron/RAIJU diagnostic HDF5")
    parser.add_argument(
        "--n-fluid-in",
        type=int,
        default=None,
        help="Expected RAIJU nFluidIn value. Defaults to metadata value.",
    )
    parser.add_argument(
        "--bulk-channel",
        type=int,
        default=None,
        help="Expected bulk channel. Defaults to metadata value.",
    )
    return parser.parse_args()


def require_h5py():
    try:
        import h5py
    except Exception as exc:
        raise RuntimeError("h5py is required; use the mage-vis Python environment") from exc
    return h5py


def decode_h5_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if hasattr(value, "shape") and value.shape == ():
        return decode_h5_text(value[()])
    return str(value)


def require_dataset(handle, name):
    if name not in handle:
        raise AssertionError("missing dataset /{0}".format(name))
    return handle[name]


def require_units(dset, expected):
    got = dset.attrs.get("Units", dset.attrs.get("units"))
    if got is None:
        raise AssertionError("{0} has no Units/units attribute".format(dset.name))
    got = decode_h5_text(got)
    if got != expected:
        raise AssertionError("{0} units {1!r} != {2!r}".format(dset.name, got, expected))


def require_close(name, got, expected, rtol=1.0e-5, atol=1.0e-7):
    if not np.allclose(got, expected, rtol=rtol, atol=atol, equal_nan=False):
        diff = np.nanmax(np.abs(got - expected))
        raise AssertionError("{0} mismatch; max abs diff={1}".format(name, diff))


def require_finite(name, arr):
    bad = int(arr.size - np.count_nonzero(np.isfinite(arr)))
    if bad:
        raise AssertionError("{0} has {1} non-finite values".format(name, bad))


def kaiju_io_roundtrip(arr):
    """Emulate kaiju IOArray*DFill shape contract after a flat read buffer."""
    data = np.asarray(arr)
    return np.reshape(data.ravel(order="F"), data.shape, order="F")


def require_channel_shape(name, arr, nf, nlt, n_channels):
    expected = (nf, nlt, n_channels)
    if arr.shape != expected:
        raise AssertionError("{0} shape {1} != {2}".format(name, arr.shape, expected))
    require_close("{0} kaiju-reshape-roundtrip".format(name), kaiju_io_roundtrip(arr), arr)


def read_metadata(handle):
    if "metadata/json" not in handle:
        return {}
    return json.loads(decode_h5_text(handle["metadata/json"][()]))


def main():
    args = parse_args()
    for path in (args.moments_h5, args.diag_h5):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)

    h5py = require_h5py()
    with h5py.File(args.moments_h5, "r") as m, h5py.File(args.diag_h5, "r") as d:
        pavg = require_dataset(m, "moments/Pavg")[:].astype(np.float64)
        davg = require_dataset(m, "moments/Davg")[:].astype(np.float64)
        pstd = require_dataset(m, "moments/Pstd")[:].astype(np.float64)
        dstd = require_dataset(m, "moments/Dstd")[:].astype(np.float64)
        tiote = require_dataset(m, "moments/tiote")[:].astype(np.float64)

        nf, nlt = pavg.shape
        for name, arr in (
            ("moments/Pavg", pavg),
            ("moments/Davg", davg),
            ("moments/Pstd", pstd),
            ("moments/Dstd", dstd),
            ("moments/tiote", tiote),
        ):
            if arr.shape != (nf, nlt):
                raise AssertionError("{0} shape {1} != {(nf, nlt)}".format(name, arr.shape))
            require_finite(name, arr)

        require_units(m["moments/Pavg"], "nPa")
        require_units(m["moments/Davg"], "#/cc")
        require_units(m["moments/Pstd"], "nPa")
        require_units(m["moments/Dstd"], "#/cc")
        require_units(m["moments/tiote"], "normalized")

        metadata = read_metadata(d)
        n_fluid_in = args.n_fluid_in
        if n_fluid_in is None:
            n_fluid_in = int(metadata.get("nFluidIn", 0))
        bulk_channel = args.bulk_channel
        if bulk_channel is None:
            bulk_channel = int(metadata.get("bulk_channel", 0))
        n_channels = n_fluid_in + 1

        if bulk_channel < 0 or bulk_channel >= n_channels:
            raise AssertionError("bulk channel outside RAIJU channel range")
        if bulk_channel > MAXTUBEFLUIDS:
            raise AssertionError("bulk channel outside TubeShell channel range")

        rai_pavg = require_dataset(d, "RAIJU_Coupler/Pavg")[:].astype(np.float64)
        rai_davg = require_dataset(d, "RAIJU_Coupler/Davg")[:].astype(np.float64)
        rai_pstd = require_dataset(d, "RAIJU_Coupler/Pstd")[:].astype(np.float64)
        rai_dstd = require_dataset(d, "RAIJU_Coupler/Dstd")[:].astype(np.float64)
        rai_tiote = require_dataset(d, "RAIJU_Coupler/tiote")[:].astype(np.float64)
        for name, arr in (
            ("RAIJU_Coupler/Pavg", rai_pavg),
            ("RAIJU_Coupler/Davg", rai_davg),
            ("RAIJU_Coupler/Pstd", rai_pstd),
            ("RAIJU_Coupler/Dstd", rai_dstd),
        ):
            require_channel_shape(name, arr, nf, nlt, n_channels)
        if rai_tiote.shape != (nf, nlt):
            raise AssertionError("RAIJU_Coupler/tiote shape mismatch")

        require_close("RAIJU_Coupler/Pavg bulk", rai_pavg[:, :, bulk_channel], pavg)
        require_close("RAIJU_Coupler/Davg bulk", rai_davg[:, :, bulk_channel], davg)
        require_close("RAIJU_Coupler/Pstd bulk", rai_pstd[:, :, bulk_channel], pstd)
        require_close("RAIJU_Coupler/Dstd bulk", rai_dstd[:, :, bulk_channel], dstd)
        require_close("RAIJU_Coupler/tiote", rai_tiote, tiote)

        ts_avgp = require_dataset(d, "TubeShellMomentsOnly/avgP")[:].astype(np.float64)
        ts_avgn = require_dataset(d, "TubeShellMomentsOnly/avgN")[:].astype(np.float64)
        ts_stdp = require_dataset(d, "TubeShellMomentsOnly/stdP")[:].astype(np.float64)
        ts_stdn = require_dataset(d, "TubeShellMomentsOnly/stdN")[:].astype(np.float64)
        ts_tiote = require_dataset(d, "TubeShellMomentsOnly/Tiote0")[:].astype(np.float64)
        for name, arr in (
            ("TubeShellMomentsOnly/avgP", ts_avgp),
            ("TubeShellMomentsOnly/avgN", ts_avgn),
            ("TubeShellMomentsOnly/stdP", ts_stdp),
            ("TubeShellMomentsOnly/stdN", ts_stdn),
        ):
            require_channel_shape(name, arr, nf, nlt, MAXTUBEFLUIDS + 1)
        if ts_tiote.shape != (nf, nlt):
            raise AssertionError("TubeShellMomentsOnly/Tiote0 shape mismatch")

        require_close("TubeShellMomentsOnly/avgP bulk", ts_avgp[:, :, bulk_channel], pavg)
        require_close("TubeShellMomentsOnly/avgN bulk", ts_avgn[:, :, bulk_channel], davg)
        require_close("TubeShellMomentsOnly/stdP bulk", ts_stdp[:, :, bulk_channel], pstd)
        require_close("TubeShellMomentsOnly/stdN bulk", ts_stdn[:, :, bulk_channel], dstd)
        require_close("TubeShellMomentsOnly/Tiote0", ts_tiote, tiote)

        state_pstd = require_dataset(d, "RAIJU_State/Pstd")[:].astype(np.float64)
        state_dstd = require_dataset(d, "RAIJU_State/Dstd")[:].astype(np.float64)
        require_channel_shape("RAIJU_State/Pstd", state_pstd, nf, nlt, n_channels)
        require_channel_shape("RAIJU_State/Dstd", state_dstd, nf, nlt, n_channels)
        require_close(
            "RAIJU_State/Pstd normalized",
            state_pstd[:, :, bulk_channel],
            pstd / np.maximum(pavg, TINY),
        )
        require_close(
            "RAIJU_State/Dstd normalized",
            state_dstd[:, :, bulk_channel],
            dstd / np.maximum(davg, TINY),
        )

        for path, units in (
            ("RAIJU_Coupler/Pavg", "nPa"),
            ("RAIJU_Coupler/Davg", "#/cc"),
            ("RAIJU_Coupler/Pstd", "nPa"),
            ("RAIJU_Coupler/Dstd", "#/cc"),
            ("RAIJU_State/Pstd", "normalized"),
            ("RAIJU_State/Dstd", "normalized"),
            ("TubeShellMomentsOnly/avgP", "nPa"),
            ("TubeShellMomentsOnly/avgN", "#/cc"),
            ("TubeShellMomentsOnly/stdP", "nPa"),
            ("TubeShellMomentsOnly/stdN", "#/cc"),
        ):
            require_units(d[path], units)

    print("validated {0}".format(args.diag_h5))
    print("grid: nf={0} nlt={1}".format(nf, nlt))
    print("RAIJU channels: {0}; bulk channel: {1}".format(n_channels, bulk_channel))
    print("TubeShellMomentsOnly channels: {0}".format(MAXTUBEFLUIDS + 1))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: {0}".format(exc), file=sys.stderr)
        sys.exit(1)
