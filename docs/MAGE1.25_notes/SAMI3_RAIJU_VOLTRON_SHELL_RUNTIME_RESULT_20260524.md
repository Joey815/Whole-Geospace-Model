# SAMI3 -> RAIJU Voltron-Shell Product Runtime Smoke

Date: 2026-05-24

## Scope

This checkpoint verifies that the Fortran runtime hook can ingest the
Voltron-shell stage-2 product generated from the schema-3 mapping weight file.

The runtime still reads only:

```text
/RaiCplMomentsOnly
```

The schema-3 weight file and its `/intermediate` Voltron TubeShell geometry are
upstream diagnostics used by the Python stage-2 product generator.  They do not
change the Fortran reader interface.

## Input Product

Input HDF5:

```text
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_shell_l_mlt_20260524.h5
```

Runtime deck:

```text
analysis/runtime_ingest_voltron_shell_20260524/tinyCase_sami3_moments_volshell_D005_P005_stateTiote.xml
```

Prototype runtime settings:

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
jobid = 7649439
jobname = sami3_volshell_smoke
state = COMPLETED
exit = 0:0
elapsed = 00:02:04
batch MaxRSS = 1026416K
node = qhcn078
```

Both baseline/control and Voltron-shell product logs reached:

```text
Fin
```

The product run log contains:

```text
SAMI3 moments ingest applied after RAIJU realtime pack
```

## Formula Checks

Final `raiCpl` restart formula checks against the baseline/control restart and
the Voltron-shell SAMI3 moment product:

```text
Pavg_formula_max_abs = 0.0
Pavg_formula_max_rel = 0.0
Pavg_actual_mean = 0.00160120762428816
Pavg_actual_max = 0.012184295058250428

Davg_formula_max_abs = 0.0
Davg_formula_max_rel = 0.0
Davg_actual_mean = 99.32539397641388
Davg_actual_max = 872.230859375

Pstd_formula_max_abs = 0.0
Pstd_formula_max_rel = 0.0
Dstd_formula_max_abs = 0.0
Dstd_formula_max_rel = 0.0
```

No checked physical restart or history fields contained non-finite values:

```text
nonfinite_physics_base_raiCpl_res = []
nonfinite_physics_volshell_raiCpl_res = []
nonfinite_physics_base_raiju_res = []
nonfinite_physics_volshell_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_volshell_gam_res = []
nonfinite_physics_volshell_raiju_history = []
nonfinite_physics_volshell_gam_history = []
```

## Final-State Response

Voltron-shell product run versus baseline/control at final restart:

```text
State/Pavg_in max_abs = 0.012184295058250428
State/Pavg_in mean_abs = 0.0011874576955885777

State/Davg_in max_abs = 872.230859375
State/Davg_in mean_abs = 99.2710628886692

State/eta max_abs = 658578162.0162892
State/eta mean_abs = 1331480.1362039307

State/Density max_abs = 3.6291416521203286
State/Density mean_abs = 0.19274910437843126

State/Pressure max_abs = 0.003918246350490817
State/Pressure mean_abs = 0.00023430574685410702

GAMERA/Gas0 max_abs = 3.5398509874669823
GAMERA/Gas0 mean_abs = 0.017140940687061446
```

## Interpretation

The schema-3 Voltron-shell stage-2 product is runtime-safe for the current
Fortran hook.  The blend is exact at the `raiCpl` level, the checked physics
fields are finite, and the product drives a continuous response through RAIJU
and GAMERA.

This does not make the mapping production physical.  The remaining physics
blocker is still:

```text
replace the L/MLT shell-grid interpolation with true Voltron traced-tube or
bvol-consistent flux-tube weights
```

## Evidence

Archived under:

```text
logs/sami3_voltron_shell_runtime_20260524/
```

Included small artifacts:

```text
base_control_volshell.log
volshell_D005_P005_stateTiote.log
slurm-7649439.out
run_volshell_smoke.sbatch
tinyCase_base_control_volshell.xml
tinyCase_sami3_moments_volshell_D005_P005_stateTiote.xml
volshell_runtime_summary.txt
```

Large generated HDF5 outputs remain local and are listed in
`manifests/large_artifacts_not_committed.txt`.
