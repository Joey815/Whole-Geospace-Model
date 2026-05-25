# SAMI3 -> RAIJU bVol-Overlap Conservative Long1800

Date: 2026-05-25 CST

## Purpose

This run promotes the `bin_bvol_overlap` TubeShell mapping prototype from the
short smoke gate to a 1800 s conservative runtime gate.

Runtime ingest remains density-only:

```text
mapping product = ds_over_B + voltron_tubeshell_l_mlt + lon0 + bin_bvol_overlap
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 0.0
```

The baseline control is reused from the previous conservative 1800 s
`bin_bvol_cc` gate because the baseline physics/configuration is identical and
does not depend on the SAMI3 moment product.

## Runtime

Run directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_conservative_long1800_20260525
```

Prototype job:

```text
jobid = 7674095
jobname = sami3_bvolov_l1800
state = COMPLETED
exit = 0:0
elapsed = 00:41:34
node = qhcn075
batch MaxRSS = 1157928K
```

Runtime log:

```text
Fin = present
run_complete = 1
prototype raiju_writes = 362
prototype gamera_writes = 364
fatal markers = 0
final RAIJU time = 30.083 min
```

## Validation

Runtime validator:

```text
validate_runtime_bvol_overlap_long1800.txt
overall = ok
baseline raiju_writes = 362
baseline gamera_writes = 364
prototype raiju_writes = 362
prototype gamera_writes = 364
```

Summary validator:

```text
validate_bvol_overlap_long1800_summary.txt
overall = ok
history_last_steps = Step#361 for RAIJU and GAMERA
```

Formula checks are exact against the reused baseline restart:

```text
Pavg_formula_max_abs = 0
Davg_formula_max_abs = 0
Pstd_formula_max_abs = 0
Dstd_formula_max_abs = 0
```

Physics restart nonfinite checks are clean:

```text
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
```

The direct coupler inputs in the prototype restart are:

```text
Pavg_actual_mean = 0.00043784124116159
Davg_actual_mean = 91.860631991447192
Pstd_actual_mean = 0.0001685590862329495
Dstd_actual_mean = 0.0081782603147492923
```

Because pressure/std/tiote alphas are zero, only `Davg` is intentionally changed
relative to baseline in this gate.

## Comparison With bin_bvol_cc Long1800

Comparison artifact:

```text
logs/sami3_tubeshell_bin_bvol_overlap_conservative_long1800_20260525/compare_bvol_overlap_vs_bin_bvolcc_long1800.txt
```

Restart-level differences versus the previous conservative `bin_bvol_cc`
prototype:

```text
raiCpl/Pavg max_abs = 0
raiCpl/Davg max_abs = 172.45403475736
raiCpl/Davg mean_abs = 7.765713378082814
raiCpl/Davg old/new mean = 88.62593804380671 / 91.86063199144719
raiCpl/Pstd max_abs = 0
raiCpl/Dstd max_abs = 0
```

Downstream final restart differences:

```text
State/Density mean_abs = 0.030174562468009765
State/Pressure mean_abs = 0.00010156498420149169
GAMERA/Gas0 mean_abs = 0.002248990458541432
```

Final history Step#361 differences:

```text
RAIJU/Davg_in mean_abs = 8.870047540582336
RAIJU/Density mean_abs = 0.05400743509203628
GAMERA/D mean_abs = 0.025972857001357222
GAMERA/P mean_abs = 0.001658950734103431
```

## Interpretation

The `bin_bvol_overlap` conservative long run is stable for 1800 s and passes
the same validation gates as the previous `bin_bvol_cc` conservative run.  It
is now the preferred prototype mapping for the conservative density-only branch.

This is still not production physical coupling.  The remaining physics blockers
are unchanged:

```text
1. Replace approximate TubeShell footprint overlap with a true traced-tube
   flux-volume quadrature.
2. Keep pressure ingest disabled until RAIJU/GAMERA Pavg semantics are settled.
3. Continue toward live WACCM-X neutral extraction and REMIX->SAMI3 potential
   forcing before calling the whole chain physically coupled.
```
