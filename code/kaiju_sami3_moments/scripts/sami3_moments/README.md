# SAMI3 Moments Sidecar

This directory contains the diagnostic adapter chain for:

```text
SAMI3 regular output -> Voltron/RAIJU-style plasma moments
```

It does not modify GAMERA equations and does not write a complete Voltron
`TubeShell` restart.  The first stage writes an intermediate HDF5 diagnostic
product with the fields needed by the existing MAGE moments interface:

```text
Pavg   [nPa]
Davg   [#/cc]
Pstd   [nPa, absolute std before RAIJU normalization]
Dstd   [#/cc, absolute std before RAIJU normalization]
tiote  [Ti/Te]
```

The copied kaiju tree also has a minimal Fortran read hook:

```text
src/voltron/modelInterfaces/sami3MomentsAdapter.F90
```

It provides:

```text
readSami3TubeShellMoments(...)
readSami3RaiCplMoments(...)
```

These routines read only the moments groups and assume the caller has already
initialized the corresponding ShellGridVars.

RAIJU has a default-off XML hook:

```xml
<sami3Moments doIngest="true"
              file="/path/to/sami3_voltron_raiju_diag.h5"
              group="/RaiCplMomentsOnly"/>
```

When enabled under `Kaiju/RAIJU`, `raijuCpl_init` parses and checks the file,
then `packRaijuCoupler_RT` applies `Pavg/Davg/Pstd/Dstd/tiote` after the normal
Voltron-to-RAIJU pack and before `raiCpl2RAIJU`.  Existing runs are unchanged
unless `doIngest` is explicitly true.

## Environment

Use the local Python environment that has `h5py`:

```bash
/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python
```

The system `/usr/bin/python3` is not enough for default HDF5 output because it
does not provide `h5py`.

## Example

Full smoke:

```bash
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/run_sami3_mage_moments_smoke.sh
```

Manual stage commands:

```bash
/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/sami3_to_voltron_moments.py \
  /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000 \
  --out /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523 \
  --format hdf5

/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523.h5 \
  --out /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_20260523 \
  --n-fluid-in 0

/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523.h5 \
  --out /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523 \
  --n-fluid-in 1 \
  --raicpl-template /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_smoke_20260523/sami3_moments_base_control.raiCpl.Res.00000.h5

/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/validate_sami3_mage_moments.py \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523.h5 \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_20260523.h5 \
  --n-fluid-in 0

/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523.h5 \
  --out /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_massEq_total_20260524 \
  --n-fluid-in 1 \
  --density-mode massEq \
  --pressure-mode total
```

Outputs from the smoke run:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523.h5
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_20260523.json
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_20260523.h5
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_20260523.json
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_20260523.h5
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_20260523.json
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523.h5
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523.json
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_massEq_total_20260524.h5
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_massEq_total_20260524.json
```

## Inputs

Required files in the SAMI3 run directory:

```text
deni1u.dat ... deni7u.dat
ti1u.dat   ... ti7u.dat
teu.dat
```

Optional files:

```text
deneu.dat
time.dat
zaltu.dat glatu.dat glonu.dat
baltu.dat blatu.dat blonu.dat
```

The adapter deliberately reads regular output files, not `vsi.rst`, because
the current SAMI3 source opens `vsi.rst` but comments out both `read(212)` and
`write(212)`.

## Output Schema

First-stage HDF5 groups:

```text
/moments/Pavg
/moments/Davg
/moments/Pstd
/moments/Dstd
/moments/tiote
/moments/Ti_eff
/moments/Te_eff
/moments/Davg_num
/moments/Davg_massEq
/moments/mu_eff
/moments/Pavg_i
/moments/Pavg_e
/moments/Pavg_total
/species/Pavg_ion
/species/Davg_ion
/species/f_H /species/f_O /species/f_NO /species/f_O2
/species/f_He /species/f_N2 /species/f_N /species/f_molecular
/species/ion_order
/coords/*_mean_*
/metadata/json
```

Array shapes:

```text
moments:     (nf, nlt) = (124, 96)
species:     (nion, nf, nlt) = (7, 124, 96)
```

Second-stage diagnostic HDF5 groups:

```text
/Voltron/avgP
/Voltron/avgN
/Voltron/stdP
/Voltron/stdN
/Voltron/Tiote0
/TubeShellMomentsOnly/avgP
/TubeShellMomentsOnly/avgN
/TubeShellMomentsOnly/stdP
/TubeShellMomentsOnly/stdN
/TubeShellMomentsOnly/Tiote0
/RAIJU_Coupler/Pavg
/RAIJU_Coupler/Davg
/RAIJU_Coupler/Pstd
/RAIJU_Coupler/Dstd
/RAIJU_Coupler/tiote
/RaiCplMomentsOnly/Pavg
/RaiCplMomentsOnly/Davg
/RaiCplMomentsOnly/Pstd
/RaiCplMomentsOnly/Dstd
/RaiCplMomentsOnly/tiote
/RAIJU_State/Pavg
/RAIJU_State/Davg
/RAIJU_State/Pstd
/RAIJU_State/Dstd
/RAIJU_State/tiote
/metadata/json
```

The second-stage channel arrays use shape:

```text
(nf, nlt, nFluidIn + 1)
```

For direct `ReadInSGV` ingestion into a live `raijuCoupler_T`, pass
`--raicpl-template` or `--target-raicpl-shape NI NJ`.  The
`/RaiCplMomentsOnly` group is then written in runtime HDF5 order:

```text
(nFluidIn + 1, NJ, NI)  # HDF5 order: channel, j, i
```

For the current tiny GR/RAIJU smoke template:

```text
/RaiCplMomentsOnly/Pavg shape = (2, 188, 45)
Fortran target shape          = (45, 188, 2)
```

`TubeShellMomentsOnly` uses the fixed `TubeShell_T` moment channel count:

```text
(nf, nlt, MAXTUBEFLUIDS + 1) = (124, 96, 6)
```

This group is deliberately named `TubeShellMomentsOnly`, not `/TubeShell`,
because it does not contain topology, magnetic geometry, potentials, masks for
all fields, timing, or traced-tube metadata required by a complete restart.

The default example uses `--n-fluid-in 0`.  `--n-fluid-in 1` is also supported
for the common local RAIJU allocation; the adapter fills channel 0 with the bulk
SAMI3 moment and leaves the extra channel zero until an explicit species/fluid
mapping is defined.

`stdP/stdN` and `RAIJU_Coupler/Pstd/Dstd` remain absolute values in MAGE units.
`RAIJU_State/Pstd/Dstd` are normalized the same way as `raiCpl2RAIJU`:

```text
Pstd_state = Pstd_absolute / max(Pavg, 1e-30)
Dstd_state = Dstd_absolute / max(Davg, 1e-30)
```

Ion order:

```text
H+, O+, NO+, O2+, He+, N2+, N+
```

Ion mass numbers used by `Davg_massEq`:

```text
H+=1, O+=16, NO+=30, O2+=32, He+=4, N2+=28, N+=14
```

The legacy RAIJU-facing aliases are intentionally unchanged:

```text
Davg = Davg_num       # total ion number density [#/cc]
Pavg = Pavg_i         # total ion pressure [nPa]
```

Additional diagnostics are written so downstream coupling can later choose
number density versus proton-equivalent mass loading, and ion pressure versus
total thermal pressure:

```text
Davg_massEq = sum_i A_i n_i
mu_eff      = Davg_massEq / Davg_num
Pavg_e      = ne kB Te
Pavg_total  = Pavg_i + Pavg_e
```

Stage 2 can now choose which bulk scalar goes into the MAGE-facing
`Pavg/Davg` contract:

```text
--density-mode num     # Davg_num/Davg, default
--density-mode massEq  # Davg_massEq, proton-equivalent #/cc

--pressure-mode ion    # Pavg_i/Pavg, default
--pressure-mode total  # Pavg_total = ion + electron pressure
```

The selected source datasets are recorded in metadata:

```text
metadata/json.moment_source_selection
metadata/json.density_mode
metadata/json.pressure_mode
```

`Pstd/Dstd` still come from the existing std fields.  For `massEq`, `total`,
or prototype weighted-moment runs, use runtime `alphaPstd=0` and
`alphaDstd=0` unless matching std definitions are added.

## Current Limit

If `--weight-file` is not provided, the adapter uses a simple along-field mean
over SAMI3 `nz`.  That product is useful for diagnostics but must not be called
a true Voltron flux-tube-volume moment.

The stage-1 adapter now exposes an explicit weighting contract:

```text
--weight-mode simple      # unit weights over nz, physical_validity=smoke_only
--weight-mode external    # requires --weight-file, physical_validity=prototype
--weight-mode ds_over_B   # uses xsu/ysu/zsu center spacing divided by bmstu
```

If `--weight-mode` is omitted, the mode is inferred from `--weight-file`.
The first-stage HDF5 and JSON metadata write:

```text
moment_weighting = simple | external | ds_over_B
physical_validity = smoke_only | prototype
```

`ds_over_B` reads:

```text
xsu.dat
ysu.dat
zsu.dat
bmstu.dat
```

It computes:

```text
ds_k = |x_{k+1} - x_k|
weight_k = ds_k / max(bms_k, bms_floor)
```

where `x/y/z` are SAMI3 s-grid center coordinates in km and `bmstu` is the
normalized magnetic field `B/B0`.  The absolute constants cancel in weighted
means.  The default floor is:

```text
--weight-bmin 1.0e-4
```

The metadata records the floor and hit count.  This is a prototype
flux-tube-volume quadrature; it is still not a Voltron traced-tube `bvol`
mapping.

An external weight file is only physically meaningful if it encodes `ds/B`,
SAMI3 cell volume, or a Voltron-equivalent flux-tube quadrature.  A later
version should either expose SAMI3 `vol` directly or map onto real Voltron
traced-tube weights before writing a TubeShell restart.

The Fortran hook was syntax-checked against the existing local GR build module
files with the HDF5 include path recorded in that build, then built through the
standalone `voltron.x` target in:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523
```
