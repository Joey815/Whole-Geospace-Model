# SAMI3 -> RAIJU L/MLT Mapping Prototype Result

Date: 2026-05-24

## Scope

This checkpoint replaces the runtime `RaiCplMomentsOnly` index-space resize
with an optional prototype L/MLT mapping:

```text
--mapping-mode index   # old normalized-index resize, default
--mapping-mode l_mlt   # prototype physical-coordinate mapping
```

The default remains `index` so older smoke products and runtime tests keep the
same behavior unless explicitly switched.

## Mapping Contract

For `--mapping-mode l_mlt`, stage 2 now requires a RAIJU `raiCpl` template:

```text
--raicpl-template <raiCpl.Res.*.h5>
```

It reads:

```text
SAMI3 source:
  baltu.dat
  blatu.dat
  blonu.dat

RAIJU target:
  /ShellGrid/theta
  /ShellGrid/phi
```

The source shell coordinate follows the SAMI3 helper formula in `L_n.f90`:

```text
L_src = (baltu / Re) / cos(blatu)^2
```

The target shell coordinate is built from RAIJU shell-grid cell centers:

```text
L_dst = 1 / sin(theta_cc)^2
```

Longitude/MLT mapping is periodic:

```text
source_mlt = circular_mean(blonu)
target_mlt = ShellGrid/phi cell centers modulo 360 degrees
```

This is a separable L/MLT interpolation prototype.  It is not yet a full
Voltron traced-tube `bvol` mapping.

## Code

Updated files:

- `code/kaiju_sami3_moments/scripts/sami3_moments/sami3_moments_to_raiju_diag.py`
- `code/kaiju_sami3_moments/scripts/sami3_moments/validate_sami3_mage_moments.py`
- `code/kaiju_sami3_moments/scripts/sami3_moments/run_sami3_mage_moments_smoke.sh`
- `code/kaiju_sami3_moments/scripts/sami3_moments/README.md`

The validator now checks runtime-order `RaiCplMomentsOnly` arrays when a
runtime layout is present:

```text
(nFluidIn + 1, NJ, NI)
```

for `Pavg/Davg/Pstd/Dstd`, and `(NJ, NI)` for `tiote`.

## Verification

Smoke command:

```text
scripts/sami3_moments/run_sami3_mage_moments_smoke.sh \
  > analysis/sami3_l_mlt_mapping_20260524.log 2>&1
```

Result:

```text
SAMI3 MAGE moments smoke passed
```

The smoke now covers:

- default simple moments
- `nFluidIn=1`
- `density_mode=massEq`, `pressure_mode=total`
- `weight_mode=ds_over_B`
- simple moments mapped with `mapping_mode=l_mlt`
- `ds_over_B` moments mapped with `mapping_mode=l_mlt`

Python syntax check:

```text
python -m py_compile \
  scripts/sami3_moments/sami3_to_voltron_moments.py \
  scripts/sami3_moments/sami3_moments_to_raiju_diag.py \
  scripts/sami3_moments/validate_sami3_mage_moments.py
```

passed.

## Coordinate Coverage

For the current tiny GR/RAIJU runtime template:

```text
RAIJU runtime layout = (nFluidIn+1, NJ, NI) = (2, 188, 45)
Fortran target shape = (45, 188, 2)
```

Coordinate metadata:

```text
SAMI3 source L min/max = 1.0141534559011587 / 1058.519161639254
RAIJU target L min/max = 1.508787000709922 / 30.111605578372767

SAMI3 source longitude min/max = 1.8750000850997979 / 358.1249694824219 deg
RAIJU target longitude min/max = 1.0 / 359.0 deg

L extrapolated cell count = 0
L extrapolated fraction = 0.0
periodic_mlt = true
```

## Simple-Weighted L/MLT Product

For `analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_l_mlt_20260524.json`:

```text
source weighting = simple
mapping = l_mlt
physical_validity = prototype

RaiCplMomentsOnly.Pavg_mapped mean = 0.8998524140932399
RaiCplMomentsOnly.Davg_mapped mean = 56047.55163445836
RaiCplMomentsOnly.Pstd_mapped mean = 1.6541514927030465
RaiCplMomentsOnly.Dstd_mapped mean = 95100.09476674127
RaiCplMomentsOnly.tiote_mapped mean = 0.9202794178286359
```

## `ds_over_B` + L/MLT Product

For `analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_l_mlt_20260524.json`:

```text
source weighting = ds_over_B
mapping = l_mlt
physical_validity = prototype

RaiCplMomentsOnly.Pavg_mapped mean = 0.047410337775382366
RaiCplMomentsOnly.Davg_mapped mean = 3970.9511794482623
RaiCplMomentsOnly.Pstd_mapped mean = 0.1764900396294211
RaiCplMomentsOnly.Dstd_mapped mean = 10358.530521549288
RaiCplMomentsOnly.tiote_mapped mean = 0.9783320295483908
```

This combined product is the current best prototype for the SAMI3 -> RAIJU
runtime moments path, but it should still be run with:

```text
alphaPstd = 0
alphaDstd = 0
```

until the weighted `Pstd/Dstd` semantics are revised.

## Remaining Limitations

- The mapping is separable in L and MLT.  It does not use per-tube Voltron
  `bvol` or traced magnetic topology.
- L outside the SAMI3 range would be clamped and counted; this test had zero
  such cells.
- `Pstd/Dstd` remain diagnostic std fields and should not be fully coupled yet.
- Closed-field mask and extrapolation/coverage products are metadata-only here;
  a later version should emit explicit quality datasets if the runtime reader
  needs them.

## Next Step

Use the combined `ds_over_B + l_mlt` runtime product in a Voltron/RAIJU smoke
run with conservative blending:

```text
alphaDavg = 1
alphaPavg = 0.2
alphaTiote = 1
alphaPstd = 0
alphaDstd = 0
```

and verify continuity against the existing `alpha=0` baseline.
