# SAMI3 -> RAIJU TubeShell bVol-Binned tiote 1800s Result

Date: 2026-05-25

## Scope

This run tests the `tiote` branch on top of the conservative TubeShell
`bin_bvol_cc` density ingest.  Pressure and standard-deviation ingest remain
disabled:

```text
mapping product = ds_over_B + voltron_tubeshell_l_mlt + lon0 + bin_bvol_cc
runtime mapping = weights
density-mode = num
pressure-mode = ion
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
moments/useStateTioteForIngest = T
```

The baseline/control HDF5 and baseline log were reused from the completed
conservative density-only run because the baseline XML physics is identical
apart from `runid`.  The prototype was run fresh.

## Run Result

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvolcc_tiote_long1800_20260525
```

Slurm result:

```text
jobid = 7673207
jobname = sami3_bvcc_tiote
state = COMPLETED
exit = 0:0
elapsed = 00:39:24
node = qhcn075
batch MaxRSS = 1182664K
```

Longrun validation:

```text
baseline_fin = Fin line
prototype_fin = Fin line
baseline_raiju_writes = 362
prototype_raiju_writes = 362
baseline_gamera_writes = 364
prototype_gamera_writes = 364
fatal marker matches = 0
slurm_run_complete = 1
```

## tiote Hook Gate

A dedicated tiote hook validator was added:

```text
scripts/validate_sami3_raiju_tiote_hook.py
```

It checks the runtime log and the SAMI3 moment product.  Result:

```text
overall = ok
alpha values = [0.0, 0.05, 0.0, 0.0, 1.0]
runtime tiote min/max = 0.873951375484467 / 4.0
runtime valid mask counts Pavg/Davg/Pstd/Dstd/tiote = 5940 each
product tiote_mask count = 5940
product tiote masked min/max = 0.8739513754844666 / 1.0004502534866333
```

The runtime max of `4.0` is expected: coverage-invalid cells preserve the
baseline/default tiote, while valid cells receive the SAMI3 product values.

## Standard Gates

The standard longrun, mapping-product, and summary validators all passed:

```text
validate_sami3_raiju_longrun = overall ok
validate_sami3_raiju_mapping_product = overall ok
validate_sami3_raiju_summary = overall ok
```

The product gate remained unchanged from the conservative density-only run:

```text
mapping_mode = weights
runtime_valid_fraction = 0.7021276595744681
extrapolated_fraction = 0.0
coverage_valid_positive = valid_min 4
weight_sum_valid_max_deviation = 1.1920928955078125e-07
```

Final `raiCpl` formula checks for the scalar fields remained exact:

```text
Pavg_formula_max_abs = 0.0
Davg_formula_max_abs = 0.0
Pstd_formula_max_abs = 0.0
Dstd_formula_max_abs = 0.0
```

No checked restart physics arrays contained non-finite values:

```text
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
```

## Response Relative To Density-Only Run

Because `Pavg` and `Davg` settings match the conservative density-only run,
the direct final coupler inputs are unchanged relative to that run:

```text
tiote_vs_density_only final State/Pavg_in max_abs = 0.0
tiote_vs_density_only final State/Davg_in max_abs = 0.0
```

The downstream state does respond to the tiote branch:

```text
tiote_vs_density_only final State/eta mean_abs = 759970.1668372097
tiote_vs_density_only final State/Density mean_abs = 0.045968829418640946
tiote_vs_density_only final State/Pressure mean_abs = 6.635173480042011e-05
tiote_vs_density_only final GAMERA/Gas0 mean_abs = 0.0036967272713272883
```

Final history-step differences at `Step#361`:

```text
RAIJU/Pavg_in mean_abs_delta = 0.0007599068320287597
RAIJU/Davg_in mean_abs_delta = 0.02887790006244608
RAIJU/Density mean_abs_delta = 0.06550995217082331
RAIJU/Pressure mean_abs_delta = 0.0025851305220132396
GAMERA/D mean_abs_delta = 0.0807438174513004
GAMERA/P mean_abs_delta = 0.0021798070676487763
GAMERA/SrcD_COLD mean_abs_delta = 0.010995499240829898
GAMERA/SrcP_COLD mean_abs_delta = 1.4030938945351775e-06
```

## Interpretation

The tiote runtime path is now validated as a separate, mask-gated branch on top
of the conservative density-only `bin_bvol_cc` run.  It reads the expected
SAMI3 tiote product, preserves invalid coverage cells, completes 1800 seconds,
and produces finite checked RAIJU/GAMERA restart arrays.

This is still prototype physics.  `tiote` is now technically usable for staged
tests, but production use still depends on settling the broader Pavg/Davg/tiote
semantics and replacing the current `lon0` bVol-bin map with a true traced
flux-volume mapping.

## Evidence

Archived under:

```text
logs/sami3_tubeshell_bin_bvolcc_tiote_long1800_20260525/
```

including XML decks, the Slurm script, run logs, Slurm output,
`sacct_7673207.txt`, standard validator JSON/TXT, tiote hook validator
JSON/TXT, and `tiote_vs_density_only_comparison.json/txt`.
