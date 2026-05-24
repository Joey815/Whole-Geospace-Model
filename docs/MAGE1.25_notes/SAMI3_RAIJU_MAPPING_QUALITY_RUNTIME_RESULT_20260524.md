# SAMI3 -> RAIJU MappingQuality Runtime Ingest Smoke

Date: 2026-05-24

## Scope

This checkpoint verifies that the Voltron/RAIJU runtime reader still ingests a
SAMI3 moment product correctly when the HDF5 file also contains the new
`/MappingQuality` diagnostic group.

The runtime deck still points the Fortran hook at:

```text
/RaiCplMomentsOnly
```

The extra group is diagnostic-only.  It is not parsed by the Fortran reader and
must not perturb runtime ingestion of `Pavg`, `Davg`, `Pstd`, `Dstd`, or
`tiote`.

## Input Product

Input HDF5:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_l_mlt_20260524.h5
```

Relevant checks:

```text
input_has_MappingQuality = True
input_RaiCplMomentsOnly_Pavg_shape = (2, 188, 45)
input_RaiCplMomentsOnly_tiote_shape = (188, 45)
input_mapping_mode = l_mlt
input_mapping_quality_finite_all_fraction = 1.0
input_mapping_quality_l_extrapolated_cell_count = 0
```

## Runtime Decks

Run directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_mapping_quality_20260524
```

Decks:

```text
tinyCase_base_control_mapq.xml
tinyCase_sami3_moments_mapq_D005_P005_stateTiote.xml
```

Prototype settings:

```text
alphaDavg = 0.05
alphaPavg = 0.05
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
moments/useStateTioteForIngest = T
sami3Moments/group = /RaiCplMomentsOnly
```

## Run Result

Slurm job:

```text
jobid = 7648737
jobname = sami3_mapq_smoke
state = COMPLETED
exit = 0:0
elapsed = 00:02:02
batch MaxRSS = 1021216K
```

Both baseline/control and MappingQuality-product logs reached:

```text
Fin
```

Both runs wrote 4 RAIJU HDF5 DATA blocks.  The MappingQuality run confirms:

```text
SAMI3 moments ingest applied after RAIJU realtime pack
```

The word `MappingQuality` does not appear in either runtime log, which is the
expected behavior because the Fortran hook reads only `/RaiCplMomentsOnly`.

## Formula Checks

Final `raiCpl` restart formula checks against baseline/control and the SAMI3
moment product:

```text
Pavg_formula_max_abs = 0.0
Pavg_formula_max_rel = 0.0
Pavg_actual_mean = 0.0016012076243789371
Pavg_actual_max = 0.012184295058250428

Davg_formula_max_abs = 0.0
Davg_formula_max_rel = 0.0
Davg_actual_mean = 99.32539397052527
Davg_actual_max = 872.230859375

Pstd_formula_max_abs = 0.0
Pstd_formula_max_rel = 0.0
Dstd_formula_max_abs = 0.0
Dstd_formula_max_rel = 0.0
```

No checked physical restart or history fields contained non-finite values:

```text
nonfinite_physics_base_raiCpl_res = []
nonfinite_physics_mapq_raiCpl_res = []
nonfinite_physics_base_raiju_res = []
nonfinite_physics_mapq_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_mapq_gam_res = []
nonfinite_physics_mapq_raiju_history = []
nonfinite_physics_mapq_gam_history = []
```

The only non-finite entries were performance timer cache datasets under
`timeAttributeCache/_perf_*`, not physics fields.

## Final-State Response

MappingQuality-product run versus baseline/control at final restart:

```text
State/Pavg_in max_abs = 0.012184295058250428
State/Pavg_in mean_abs = 0.0011874576956966423

State/Davg_in max_abs = 872.230859375
State/Davg_in mean_abs = 99.27106288278063

State/eta max_abs = 658578162.0162892
State/eta mean_abs = 1331480.1268928621

State/Density max_abs = 3.6291416521227338
State/Density mean_abs = 0.19274910328960174

State/Pressure max_abs = 0.003918246350490817
State/Pressure mean_abs = 0.00023430574676482196

GAMERA/Gas0 max_abs = 3.539851024860331
GAMERA/Gas0 mean_abs = 0.017140940619025425
```

## Interpretation

The diagnostic `/MappingQuality` group is safe for the current runtime path:
the Fortran reader ignores it, ingests `/RaiCplMomentsOnly`, applies the
requested conservative blend exactly, and produces finite checked physics
fields.

This closes the immediate integration check for adding MappingQuality arrays to
stage-2 products.  It does not close the remaining physics blocker: the current
`ds_over_B + l_mlt` mapping is still a prototype, not yet a Voltron
traced-tube or `bvol`-consistent production mapping.

## Evidence

Archived under:

```text
logs/sami3_mapping_quality_runtime_20260524/
```

including both XML decks, both runtime logs, Slurm output, the launcher, and
`mapq_runtime_summary.txt`.
