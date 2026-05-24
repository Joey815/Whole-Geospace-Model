# SAMI3 -> RAIJU Runtime Blend/Floor Controls Result, 2026-05-24

## Scope

This step extends the existing SAMI3-derived scalar plasma moments runtime hook:

```text
packRaijuCoupler_RT
  -> tubeShell2RaiCpl
  -> applySami3RaiCplMoments
  -> raiCpl2RAIJU
```

The hook still reads the existing moments-only contract:

```text
/RaiCplMomentsOnly/Pavg
/RaiCplMomentsOnly/Davg
/RaiCplMomentsOnly/Pstd
/RaiCplMomentsOnly/Dstd
/RaiCplMomentsOnly/tiote
```

It does not change GAMERA equations and does not feed raw SAMI3 3-D arrays into
GAMERA.

## Implemented Runtime Controls

The `Kaiju/RAIJU/sami3Moments` XML block now accepts:

```xml
<sami3Moments
  doIngest="T"
  file="/path/to/sami3_raicpl_moments.h5"
  group="/RaiCplMomentsOnly"
  alphaPavg="1.0"
  alphaDavg="1.0"
  alphaPstd="1.0"
  alphaDstd="1.0"
  alphaTiote="1.0"
  densityFloor="0.0"
  pressureFloor="0.0"
  tioteMin="0.0"
  tioteMax="1.0e30"
  abortOnNonfinite="T"/>
```

For each field:

```text
X_runtime = (1 - alphaX) * X_original + alphaX * X_SAMI3
```

Defaults preserve the previous full-overwrite behavior.  `alpha=0` is a
baseline recovery mode.  `alpha=1` is the original SAMI3 overwrite mode.

The code clamps `alpha` into `[0,1]`, enforces non-negative density/pressure
floors, clamps `tiote`, and aborts by default if SAMI3 input contains NaN/Inf.

## Mask Handling

`ReadInSGV` reads both data and mask datasets from the SAMI3 HDF5 product.  This
step explicitly restores the original masks from `tubeShell2RaiCpl` after the
read.  Therefore SAMI3 can override/blend scalar moment values, but the runtime
RAIJU geometry/topology/mask semantics remain the MAGE/Voltron ones.

This fix was required because an initial alpha=0 test matched RAIJU state data
but changed `Davg_mask` in `raiCpl.Res.00000`.  After restoring masks, alpha=0
matches baseline exactly for the compared numeric datasets.

## Validation

Build:

```text
cd /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523
LD_LIBRARY_PATH=/apps/support/intel_spr_rocky8.9/oneapi/2023.2.0/compiler/2023.2.0/linux/compiler/lib/intel64_lin:$LD_LIBRARY_PATH make voltron.x -j 8
```

Runtime smoke directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_blend_20260524
```

Runs:

```text
tinyCase_base_control.xml
tinyCase_sami3_moments_alpha0.xml
tinyCase_sami3_moments_default.xml
```

Results:

```text
alpha0_vs_baseline raiCpl.Res.00000:
  datasets=36 max_abs=0.0 max_rel=0.0

alpha0_vs_baseline raiju.Res.00000:
  datasets=47 max_abs=0.0 max_rel=0.0

default_alpha1_input_vs_raiCpl:
  Pavg max_abs=0.0 max_rel=0.0
  Davg max_abs=0.0 max_rel=0.0
  Pstd max_abs=0.0 max_rel=0.0
  Dstd max_abs=0.0 max_rel=0.0
```

The `tiote` runtime log also shows expected SAMI3 min/max for default alpha=1,
but the current `raiCpl` restart writer does not include `tiote`, so field-level
HDF5 comparison above covers `Pavg/Davg/Pstd/Dstd`.

Evidence logs are archived in:

```text
logs/sami3_runtime_blending_20260524/
```

## Code Snapshot

Updated snapshot files:

```text
code/kaiju_sami3_moments/src/base/types/volttypes.F90
code/kaiju_sami3_moments/src/voltron/modelInterfaces/raijuCplHelper.F90
code/kaiju_sami3_moments/src/voltron/modelInterfaces/sami3MomentsAdapter.F90
```

## Current Interpretation

The SAMI3 -> RAIJU runtime bridge now has a safe operational envelope:

```text
alpha=0:
  adapter enabled but exactly baseline in validated runtime outputs

alphaDavg=1, alphaPavg=0:
  density-only prototype mode

alphaDavg=1, alphaPavg=0.0-0.2:
  density plus cold-pressure correction prototype

alpha=1:
  full overwrite smoke/upper-bound mode
```

This still remains a scalar moments adapter.  Physical production coupling still
requires final decisions on `Davg` number vs mass-equivalent density, `Pavg` ion
vs total pressure, flux-tube-volume weighting, and L/MLT geometry mapping.

