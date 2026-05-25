# SAMI3 -> RAIJU Exclude-Lmax Density/Tiote 1800s Result

Date: 2026-05-26 CST

## Purpose

This run combines the latest schema v7 `exclude_above_target_lmax` sparse
mapping product with the already validated `tiote` runtime branch.

The test keeps the current conservative scalar-moment policy:

```text
mapping product = ds_over_B + voltron_tubeshell_l_mlt + lon0 + bin_bvol_overlap + exclude_above_target_lmax
runtime mapping = weights
density-mode = num
pressure-mode = ion
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
density-only alphaTiote = 0.0
density+tiote alphaTiote = 1.0
density+tiote moments/useStateTioteForIngest = T
```

This is still a diagnostic/runtime adapter result.  It does not solve the
source-domain physics blocker that almost all positive active Voltron bVol is
outside the current RAIJU target L range.

## Run Result

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_tiote_long1800_20260526
```

Slurm result:

```text
jobid = 7678667
jobname = sami3_exl_tiote
state = COMPLETED
exit = 0:0
elapsed = 01:22:42
node = qhcn176
batch MaxRSS = 1176956K
```

The job ran two 1800s prototype cases sequentially:

```text
long1800_exclude_lmax_dens005
long1800_exclude_lmax_dens005_tiote
```

Both reached `Fin` and each wrote 362 RAIJU HDF5 frames.

## Standard Gates

Both archive runs passed:

```text
validate_sami3_raiju_longrun = overall ok
validate_sami3_raiju_summary = overall ok
validate_sami3_raiju_mapping_product = overall ok
```

The stage-2 product gate confirms the schema v7 weighted product properties:

```text
mapping_mode = weights
runtime_valid_fraction = 0.9574468085106383
finite_all_fraction = 1.0
extrapolated_fraction = 0.0
coverage_valid_positive valid_min = 4
weight_sum_valid_max_deviation = 1.1920928955078125e-07
tiote masked range = 0.8749623894691467 / 1.0004475116729736
```

Final `raiCpl` formula checks are exact in both density-only and density+tiote
runs:

```text
Pavg_formula_max_abs = 0.0
Davg_formula_max_abs = 0.0
Pstd_formula_max_abs = 0.0
Dstd_formula_max_abs = 0.0
```

No checked restart physics arrays contain non-finite values:

```text
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
```

## Tiote Hook Gate

The dedicated tiote hook validator passed for the density+tiote run:

```text
overall = ok
alpha values = [0.0, 0.05, 0.0, 0.0, 1.0]
runtime tiote min/max = 0.874962389469147 / 4.0
runtime valid mask counts Pavg/Davg/Pstd/Dstd/tiote = 8100 each
product tiote_mask count = 8100
product tiote masked min/max = 0.8749623894691467 / 1.0004475116729736
```

The runtime max of `4.0` is expected because coverage-invalid cells preserve
the baseline/default `tiote`, while valid cells receive the SAMI3 product.

## Density-Only Versus Density+Tiote

A reusable comparator was added:

```text
scripts/compare_sami3_raiju_longrun_pair.py
```

For `tiote` versus `density_only`, the final direct coupler inputs are
unchanged, as expected:

```text
final State/Pavg_in max_abs = 0.0
final State/Davg_in max_abs = 0.0
```

The downstream state responds to the tiote branch:

```text
final State/eta mean_abs = 777495.5483858573
final State/Density mean_abs = 0.049968519636217984
final State/Pressure mean_abs = 6.768535411748468e-05
final GAMERA/Gas0 mean_abs = 0.0036867868848708286
```

Final history-step differences at `Step#361`:

```text
RAIJU/Pavg_in mean_abs_delta = 0.0007442049301780379
RAIJU/Davg_in mean_abs_delta = 0.026932047464110116
RAIJU/Density mean_abs_delta = 0.06496791943939395
RAIJU/Pressure mean_abs_delta = 0.002568324826040811
GAMERA/D mean_abs_delta = 0.07322541544615054
GAMERA/P mean_abs_delta = 0.0019766984531691557
GAMERA/SrcD_COLD mean_abs_delta = 0.010669447877005843
GAMERA/SrcP_COLD mean_abs_delta = 1.3733065978806864e-06
```

## Evidence

Archived under:

```text
logs/sami3_exclude_lmax_density_long1800_20260526/
logs/sami3_exclude_lmax_density_tiote_long1800_20260526/
```

The archives include XML decks, the Slurm script, run logs, `sacct_7678667.txt`,
standard validator JSON/TXT, mapping-product validator JSON/TXT, tiote hook
validator JSON/TXT, and `tiote_vs_density_only_comparison.json/txt`.

## Production-Contract Guardrail

A product-semantics validator was added:

```text
scripts/validate_sami3_raiju_production_contract.py
```

It reads the stage-2 `/RaiCplMomentsOnly` product, follows the referenced
mapping weight file, and checks whether source-domain exclusion is compatible
with any production claim.

For the current exclude-Lmax product, the diagnostic contract passes:

```text
validate_sami3_raiju_production_contract_diagnostic.txt
classification = diagnostic_only
overall = ok
source_domain_policy = exclude_above_target_lmax
source_domain_skipped_above_lmax_fraction = 0.999595965103914
```

The same product intentionally fails production-readiness mode:

```text
validate_sami3_raiju_production_contract_production.txt
FAIL production_source_domain_skip_threshold:
  fraction=0.999595965103914 max=0.05
FAIL production_label:
  product=unknown weight=prototype
classification = diagnostic_only
overall = FAIL
```

This is now a machine-readable guardrail: the current product is runtime-valid
but explicitly diagnostic-only until the source-domain L policy is physically
resolved.

## Interpretation

The current schema v7 exclude-Lmax product now has:

```text
offline mapping product validator: ok
target-admissible closure validator: ok
runtime alpha=0 baseline recovery: ok
runtime alphaDavg=0.05 short smoke: ok
runtime alphaDavg=0.05 1800s density-only: ok
runtime alphaDavg=0.05 + alphaTiote=1.0 1800s: ok
diagnostic production-contract guardrail: ok
production-readiness guardrail: expected FAIL
```

This validates the adapter mechanics for the conservative target-domain product
using the existing MAGE `Pavg/Davg/Pstd/Dstd/tiote` interface.

It remains prototype physics.  The next physics decision is still whether to
extend the RAIJU target domain, derive a different Voltron source subset, or
keep this product as a diagnostic/runtime adapter until a production mapping
policy is chosen.
