# SAMI3 -> RAIJU Recommended Prototype 900s Smoke

Date: 2026-05-25

## Scope

This extends the recommended SAMI3 -> RAIJU/GAMERA scalar-moment prototype from
the 300 second baseline/control smoke to a 900 second Slurm run.

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
tinyCase_base_control_long900.xml
tinyCase_sami3_moments_dsB_lmlt_recommended_long900.xml
```

## Run Result

Slurm job:

```text
jobid = 7660334
jobname = sami3_rai_long900
state = COMPLETED
exit = 0:0
elapsed = 00:48:44
node = qhcn095
batch MaxRSS = 1067328K
```

Strict validator result:

```text
ok = true
baseline_fin = Fin line
prototype_fin = Fin line
baseline_raiju_writes = 182
prototype_raiju_writes = 182
baseline_gamera_writes = 184
prototype_gamera_writes = 184
fatal marker matches = 0
expected baseline/prototype HDF5 products = present
slurm_run_complete = 1
```

Both baseline/control and recommended logs end with:

```text
Fin
```

The recommended log confirms:

```text
SAMI3 moments ingest applied after RAIJU realtime pack
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
Dstd_actual_mean = 0.008178260314749294
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
State/Pavg_in mean_abs = 0.0011874576956966425
State/Davg_in max_abs = 872.230859375
State/Davg_in mean_abs = 99.27106288278063
State/eta max_abs = 658578162.0162892
State/Density max_abs = 3.6291416521227338
State/Pressure max_abs = 0.003918246350490817
GAMERA/Gas0 max_abs = 3.539851024860331
```

Mean final restart comparison:

```text
State/Davg_in recommended_mean = 99.32539397052527
State/Davg_in baseline_mean = 0.05433108774465307
State/Pavg_in recommended_mean = 0.0016012076243789371
State/Pavg_in baseline_mean = 0.00043784124116159
State/Density recommended_mean = 994.7134849242163
State/Density baseline_mean = 994.5915339820937
State/Pressure recommended_mean = 0.27765787363762223
State/Pressure baseline_mean = 0.2777840485335117
GAMERA/Gas0 mean_abs_delta = 0.017140940619025425
```

Final history-step comparison (`Step#181` versus `Step#181`):

```text
RAIJU/Davg_in mean_abs_delta = 80.57793697330865
RAIJU/Pavg_in mean_abs_delta = 0.01322208696408386
RAIJU/Density mean_abs_delta = 0.5456441189364802
RAIJU/Pressure mean_abs_delta = 0.0025566739740551948
GAMERA/D mean_abs_delta = 0.3129257236106208
GAMERA/P mean_abs_delta = 0.006741168207938279
GAMERA/SrcD_COLD mean_abs_delta = 0.028050062546762566
GAMERA/SrcP_COLD mean_abs_delta = 3.436090786935875e-06
```

## Interpretation

The recommended prototype now passes a 900 second Slurm baseline/control run
with exact final `raiCpl` blend formula checks and no non-finite checked RAIJU
or GAMERA physics fields. This is a stronger runtime stability checkpoint than
the 300 second smoke and is now the best current evidence for the conservative
SAMI3-derived scalar-moment path.

This is still not production physics coupling. The SAMI3-derived density scale
is much larger than the native baseline `Davg_in`, and the current `ds_over_B`
plus L/MLT mapping remains a prototype mapping rather than a traced
flux-tube-volume map. The next physical step should keep these conservative
alphas while replacing the prototype mapping/coverage policy and validating
longer duration response.

## Evidence

Archived under:

```text
logs/sami3_dsB_lmlt_recommended_long900_20260525/
```

including both XML decks, both run logs, Slurm output, `sacct_7660334.txt`,
the strict validator JSON, and `recommended_long900_summary.txt`.

Large HDF5 history/restart products are intentionally not committed. They
remain in the local run directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long900_20260525
```
