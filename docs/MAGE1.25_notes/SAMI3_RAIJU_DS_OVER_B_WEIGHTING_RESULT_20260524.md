# SAMI3 -> RAIJU `ds_over_B` Weighting Prototype Result

Date: 2026-05-24

## Scope

This checkpoint extends the SAMI3 stage-1 scalar-moment adapter with a
prototype flux-tube-volume quadrature:

```text
weight_k = ds_k / max(bms_k, bms_floor)
```

where:

- `ds_k` is the distance between adjacent SAMI3 `xsu/ysu/zsu` s-grid centers.
- `bmstu.dat` provides normalized magnetic-field magnitude `B/B0`.
- `bms_floor` defaults to `1.0e-4` and is recorded in metadata.

This is still a prototype quadrature.  It is not yet a Voltron traced-tube
`bvol` mapping and should not be labeled production physical coupling.

## Code

Updated files:

- `code/kaiju_sami3_moments/scripts/sami3_moments/sami3_to_voltron_moments.py`
- `code/kaiju_sami3_moments/scripts/sami3_moments/sami3_moments_to_raiju_diag.py`
- `code/kaiju_sami3_moments/scripts/sami3_moments/run_sami3_mage_moments_smoke.sh`
- `code/kaiju_sami3_moments/scripts/sami3_moments/README.md`

The new command path is:

```text
sami3_to_voltron_moments.py --weight-mode ds_over_B
```

with optional:

```text
--weight-bmin <normalized B/B0 floor>
```

The stage-2 metadata warning was also generalized: `Pstd/Dstd` remain the
existing ion/number-density std fields, so runtime prototype runs should use
`alphaPstd=0` and `alphaDstd=0` unless matching std definitions are added.

## Verification

Smoke command:

```text
scripts/sami3_moments/run_sami3_mage_moments_smoke.sh \
  > analysis/sami3_ds_over_B_weighting_20260524.log 2>&1
```

Result:

```text
SAMI3 MAGE moments smoke passed
```

The smoke covers:

- default simple weighting, `density_mode=num`, `pressure_mode=ion`
- `nFluidIn=1`
- `density_mode=massEq`, `pressure_mode=total`
- `weight_mode=ds_over_B`, `nFluidIn=1`

## `ds_over_B` Metadata

From `analysis/sami3_moments_stubpayload_ds_over_B_20260524.json`:

```text
moment_weighting = ds_over_B
physical_validity = prototype
bms_floor = 1.0e-4
bms_floor_hit_count = 1152
bms_floor_hit_fraction = 3.1833616298811547e-4

bms min = 1.1267823341043481e-09
bms max = 2.0681204795837402
bms mean = 1.0165203277793788

bms_effective min = 1.0e-4
bms_effective max = 2.0681204795837402
bms_effective mean = 1.0165203531635152

ds_over_B_weight min = 0.11683273451666609
ds_over_B_weight max = 60456252423.67498
ds_over_B_weight mean = 2489173.0761641823
```

The floor prevents pathological near-zero `bmstu` samples from dominating the
weighted mean.  The hit fraction is small but nonzero, so downstream analyses
must preserve this metadata.

## Moment Values

Stage-1 `ds_over_B` output:

```text
Pavg mean = 0.5670714974403381 nPa
Davg mean = 36795.40234375 cm^-3
Pstd mean = 0.6109516024589539 nPa
Dstd mean = 36530.1171875 cm^-3
tiote mean = 0.9328573942184448
Davg_massEq mean = 556836.0625 proton-equivalent cm^-3
Pavg_total mean = 1.2174482345581055 nPa
```

Stage-2 `ds_over_B`, `nFluidIn=1`, default source modes:

```text
density_mode = num
density_source = Davg_num
pressure_mode = ion
pressure_source = Pavg_i

Voltron.avgP / RAIJU.Pavg mean = 0.5670715121648862
Voltron.avgN / RAIJU.Davg mean = 36795.40061156311
tiote mean = 0.9328574435065641
```

The validator confirmed the generated HDF5 file.

## Remaining Limitation

The `ds_over_B` prototype makes `RAIJU_State.Pstd/Dstd` large after the normal
RAIJU normalization:

```text
RAIJU_State.Pstd max = 143.18782045339753
RAIJU_State.Dstd max = 86.95889332449026
```

This is expected for the current diagnostic std definition, not a production
std contract.  For runtime prototype tests, use:

```text
alphaPstd = 0
alphaDstd = 0
```

until `Pstd/Dstd` are redefined consistently for weighted or mass-equivalent
moments.

## Next Step

Replace the stage-2 index-space resize with an explicit SAMI3-to-RAIJU mapping
contract.  The first target is L/MLT mapping with periodic MLT interpolation,
coverage diagnostics, and metadata flags before attempting full Voltron
`bvol` alignment.
