# SAMI3 -> RAIJU Moment Semantics And Tiote Runtime Hook

Date: 2026-05-24

## Scope

This note audits the current `Pavg/Davg/Pstd/Dstd/tiote` path used by the
SAMI3 -> Voltron/RAIJU/GAMERA scalar-moment adapter, then records the small
runtime change that makes gridded `tiote` optional but dynamically meaningful.

The runtime path remains:

```text
packRaijuCoupler_RT
  -> tubeShell2RaiCpl
  -> applySami3RaiCplMoments
  -> raiCpl2RAIJU
  -> applyMomentIngestion
  -> DkT2SpcEta / Maxwell2Eta
```

## Semantics Audit

`Davg` is a number-density input in `#/cc`, not a mass-equivalent density, on
the RAIJU moment-ingest path.  In `raiCpl2RAIJU`, `raiCpl%Davg` is copied into
`State%Davg`.  In `applyMomentIngestion`, `State%Davg` is passed as `tmp_D` to
`DkT2SpcEta`, whose interface documents `D` as `[#/cc]`.  `etak2Den` also
inverts eta back to density in `[#/cc]`.

Therefore the current safe runtime source for `Davg` is:

```text
density-mode = num
source       = Davg_num
```

`Davg_massEq` remains useful diagnostic metadata for heavy-ion mass loading,
but should not be routed into this RAIJU `Davg` slot until a distinct
mass-loading path is defined.

`Pavg` is paired with `Davg` as pressure in `nPa`.  The code computes:

```text
kT [keV] = 6.25 * Pavg[nPa] / Davg[#/cc]
```

This `kT` drives the Maxwell/Kappa eta-channel mapping.  For the current cold
SAMI3 prototype, the conservative runtime mode is still:

```text
pressure-mode = ion
alphaPavg     = 0.0 initially, or a small correction scan
```

`Pstd/Dstd` are copied from `raiCpl`, then normalized in `raiCpl2RAIJU`:

```text
State%Pstd = Pstd / max(Pavg,TINY)
State%Dstd = Dstd / max(Davg,TINY)
```

The active-domain use of `Pstd` is currently commented out in `raijuDomain`.
For this adapter they should remain diagnostic or runtime-disabled:

```text
alphaPstd = 0
alphaDstd = 0
```

## Tiote Finding

Before this change, `State%tiote(i,j)` was copied from the coupler and could be
written in debug output, but `applyMomentIngestion` used only scalar
`Model%tiote`.  That meant SAMI3 `tiote` blending did not affect the
moment-to-eta split between H+ and hot electrons.

The new code adds a default-off switch:

```xml
<moments useStateTioteForIngest="T"/>
```

When enabled, `applyMomentIngestion` uses `State%tiote(i,j)` if it is positive,
otherwise it falls back to `Model%tiote`.  Default behavior is unchanged.

Changed source snapshots:

```text
code/kaiju_sami3_moments/src/base/types/raijuTypes.F90
code/kaiju_sami3_moments/src/raiju/raijuStarter.F90
code/kaiju_sami3_moments/src/raiju/raijuBCs.F90
```

## Validation

Build:

```text
make voltron.x -j 8
```

Result:

```text
Built target voltron.x
```

The old HDF5/MPI IPO warnings were still present and are unchanged from prior
successful builds.

Two short runtime cases were run from:

```text
analysis/runtime_ingest_blend_20260524/
```

Case 1: default-off regression

```text
tinyCase_sami3_moments_dsB_lmlt_alpha0.xml
```

Results:

```text
alpha0_vs_base_raiCpl: datasets=36 max_abs=0 max_rel=0
alpha0_vs_base_raiju:  datasets=47 max_abs=0 max_rel=0
nonfinite_count=0
Fin
```

Case 2: state-tiote enabled

```text
tinyCase_sami3_moments_dsB_lmlt_D005_stateTiote.xml
alphaDavg=0.05
alphaPavg=0
alphaPstd=0
alphaDstd=0
alphaTiote=1
moments/useStateTioteForIngest=T
```

Results versus the prior `D005` case:

```text
State/Davg_in max_abs=0
State/Pavg_in max_abs=0
State/eta     max_abs=452793303.24868566
State/Density max_abs=4.4609337436245395
State/Pressure max_abs=0.0035325228984534052
GAMERA/Gas0   max_abs=3.4072678346057494
nonfinite_count=0
Fin
```

Interpretation:

```text
Default-off behavior preserves the baseline exactly.
With the switch enabled, the same Pavg/Davg input produces a changed eta map,
so SAMI3-derived tiote now reaches the runtime moment-to-eta physics.
```

## Current Recommended Prototype Mode

For the next coupled smoke/science-prototype run:

```text
weight-mode     = ds_over_B
mapping-mode    = l_mlt
density-mode    = num
pressure-mode   = ion
alphaDavg       = 0.05 to 0.10
alphaPavg       = 0.0
alphaPstd       = 0.0
alphaDstd       = 0.0
alphaTiote      = 0.0 for control, then 1.0 in a separate scan
useStateTioteForIngest = T only for the tiote scan
```

Do not use `density-mode=massEq` for the current RAIJU scalar-moment slot.

## Evidence

Archived under:

```text
logs/sami3_raiju_moment_semantics_tiote_20260524/
```

including the state-tiote XML deck, the two runtime logs, and
`state_tiote_semantics_summary.txt`.
