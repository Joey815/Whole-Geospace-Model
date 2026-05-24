# SAMI3 -> RAIJU Recommended Prototype 300s Smoke

Date: 2026-05-24

## Scope

This extends the recommended SAMI3 -> RAIJU/GAMERA scalar-moment prototype from
the 60 second smoke to a 300 second Slurm run, paired with a 300 second
baseline/control.

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
tinyCase_base_control_long300.xml
tinyCase_sami3_moments_dsB_lmlt_recommended_long300.xml
```

## Run Result

Slurm job:

```text
jobid = 7648350
jobname = sami3_rai_long300
state = COMPLETED
exit = 0:0
elapsed = 00:16:44
batch MaxRSS = 1024404K
```

Both baseline/control and recommended logs end with:

```text
Fin
```

Both logs wrote 62 RAIJU HDF5 DATA blocks and reached final RAIJU output near
5.083 minutes. The recommended log confirms:

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
Dstd_formula_max_abs = 0.0
```

No checked physical datasets contained non-finite values:

```text
nonfinite_physics_base_raiCpl_res = []
nonfinite_physics_proto_raiCpl_res = []
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
nonfinite_physics_base_raiju_history = []
nonfinite_physics_proto_raiju_history = []
nonfinite_physics_base_gam_history = []
nonfinite_physics_proto_gam_history = []
```

The only non-finite history entries were performance timer cache datasets under
`timeAttributeCache/_perf_*`, not physics fields.

## Final-State Response

Recommended prototype versus baseline/control at final restart:

```text
State/Pavg_in max_abs = 0.012184295058250428
State/Davg_in max_abs = 872.230859375
State/eta max_abs = 658578162.0162892
State/Density max_abs = 3.6291416521227338
State/Pressure max_abs = 0.003918246350490817
GAMERA/Gas0 max_abs = 3.539851024860331
```

Mean final restart comparison:

```text
State/Davg_in recommended_mean = 99.32539397052527
State/Davg_in baseline_mean    = 0.05433108774465306
State/Pavg_in recommended_mean = 0.0016012076243789371
State/Pavg_in baseline_mean    = 0.00043784124116159
GAMERA/Gas0 mean_abs_delta     = 0.017140940619025425
```

Final history-step comparison (`Step#61` versus `Step#61`):

```text
RAIJU/Davg_in mean_abs_delta    = 80.4997262126053
RAIJU/Pavg_in mean_abs_delta    = 0.007159633317417969
RAIJU/Density mean_abs_delta    = 0.3713439846454984
RAIJU/Pressure mean_abs_delta   = 0.0014132240630020216
GAMERA/D mean_abs_delta         = 0.13319359135359152
GAMERA/P mean_abs_delta         = 0.0030807005578020372
GAMERA/SrcD_COLD mean_abs_delta = 0.020956078612729665
GAMERA/SrcP_COLD mean_abs_delta = 3.1431973533036332e-06
```

## Interpretation

The recommended prototype now passes a 300 second Slurm smoke with a matched
baseline/control, exact runtime blending formula checks, and no non-finite
physics fields in checked restart or history products. This validates the
current conservative prototype over several RAIJU write cycles.

This is still not a production physics coupling. The SAMI3 density scale is
large relative to baseline, and the current `ds_over_B` plus L/MLT mapping
remains a prototype mapping. The next step should be a longer controlled
duration run at the same conservative settings, followed by output inspection
before any increase of `alphaDavg` or `alphaPavg`.

## Evidence

Archived under:

```text
logs/sami3_dsB_lmlt_recommended_long300_20260524/
```

including both XML decks, both run logs, Slurm output, the launcher, and
`recommended_long300_summary.txt`.
