# SAMI3 -> RAIJU Recommended Prototype 1800s Result

Date: 2026-05-25

## Scope

This extends the recommended SAMI3 -> RAIJU/GAMERA scalar-moment prototype from
the completed 900 second checkpoint to an 1800 second Slurm run.  The moment
adapter settings were not changed.

Prototype settings:

```text
weight-mode = ds_over_B
mapping-mode = l_mlt
density-mode = num
pressure-mode = ion
alphaDavg = 0.05
alphaPavg = 0.05
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
moments/useStateTioteForIngest = T
```

Runtime decks:

```text
tinyCase_base_control_long1800.xml
tinyCase_sami3_moments_dsB_lmlt_recommended_long1800.xml
```

## Run Result

Slurm job:

```text
jobid = 7663122
jobname = sami3_rai_long1800
state = COMPLETED
exit = 0:0
elapsed = 01:23:20
node = qhcn065
batch MaxRSS = 1169988K
```

Strict validator result:

```text
overall = ok
baseline_fin = Fin line
prototype_fin = Fin line
baseline_raiju_writes = 362
prototype_raiju_writes = 362
baseline_gamera_writes = 364
prototype_gamera_writes = 364
fatal marker matches = 0
expected baseline/prototype HDF5 products = present
slurm_run_complete = 1
```

The archive gate also ran the moment-product validator and the final summary
validator.  Both returned:

```text
overall = ok
```

## Mapping Product Gate

The committed archive records the product gate for:

```text
sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_l_mlt_20260524.h5
```

Key checks:

```text
mapping_mode = l_mlt
finite_all_fraction = 1.0
runtime_valid_fraction = 1.0
extrapolated_fraction = 0.0
Pavg/Davg/Pstd/Dstd masked values are finite and nonnegative
tiote masked range = 0.8748378753662109 to 1.0004479885101318
source_l range = 1.0141534805297852 to 1058.5191650390625
target_l range = 1.5087870359420776 to 30.111604690551758
source_mlt_deg range = 1.8750001192092896 to 358.1249694824219
target_mlt_deg range = 1.0 to 359.0
```

## Formula Checks

Final `raiCpl` restart formula checks against the baseline/control and the
SAMI3 moment product:

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
Pstd_actual_mean = 0.0001685590862329495
Pstd_actual_max = 0.002409403797901249

Dstd_formula_max_abs = 0.0
Dstd_formula_max_rel = 0.0
Dstd_actual_mean = 0.008178260314749292
Dstd_actual_max = 0.09626227232160983
```

No checked physics datasets contained non-finite values:

```text
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
```

## Final-State Response

Recommended prototype versus baseline/control at final restart:

```text
State/Pavg_in max_abs = 0.012184295058250428
State/Pavg_in mean_abs = 0.0011874576956966423
State/Davg_in max_abs = 872.230859375
State/Davg_in mean_abs = 99.27106288278063
State/eta max_abs = 658578162.0162892
State/Density max_abs = 3.6291416521227338
State/Pressure max_abs = 0.0039182463504908172
GAMERA/Gas0 max_abs = 3.5398510248603312
```

Mean final restart comparison:

```text
State/Davg_in recommended_mean = 99.32539397052527
State/Davg_in baseline_mean = 0.05433108774465306
State/Pavg_in recommended_mean = 0.0016012076243789371
State/Pavg_in baseline_mean = 0.00043784124116159
State/Density recommended_mean = 994.7134849242166
State/Density baseline_mean = 994.5915339820937
State/Pressure recommended_mean = 0.27765787363762223
State/Pressure baseline_mean = 0.27778404853351163
GAMERA/Gas0 mean_abs_delta = 0.017140940619025425
```

Final history-step comparison (`Step#361` versus `Step#361`):

```text
RAIJU/Davg_in mean_abs_delta = 80.59820585585571
RAIJU/Pavg_in mean_abs_delta = 0.01062564049268319
RAIJU/Density mean_abs_delta = 0.6365761505997633
RAIJU/Pressure mean_abs_delta = 0.005121059222602455
GAMERA/D mean_abs_delta = 0.41361765624198987
GAMERA/P mean_abs_delta = 0.007801311148941497
GAMERA/SrcD_COLD mean_abs_delta = 0.061255920453737546
GAMERA/SrcP_COLD mean_abs_delta = 6.330810554705103e-06
```

## Interpretation

The recommended prototype now passes an 1800 second Slurm baseline/control run
with exact final `raiCpl` blend formula checks, strict product validation, and
no non-finite checked RAIJU or GAMERA physics fields.  This is the strongest
current evidence for the conservative SAMI3-derived scalar-moment ingest path.

This remains prototype physics, not production coupling.  The current path is
`ds_over_B + l_mlt` with conservative alpha blending; it does not yet replace
the prototype mapping with a traced flux-tube-volume or Voltron `bvol`-aligned
map, and it still uses scalar moments rather than a complete plasma state.

## Evidence

Archived under:

```text
logs/sami3_dsB_lmlt_recommended_long1800_20260525/
```

including both XML decks, both run logs, Slurm output, `sacct_7663122.txt`,
the strict validator JSON, the moment-product validator JSON, the summary
validator JSON, and `recommended_long1800_summary.txt`.

Large HDF5 history/restart products are intentionally not committed. They
remain in the local run directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long1800_20260525
```
