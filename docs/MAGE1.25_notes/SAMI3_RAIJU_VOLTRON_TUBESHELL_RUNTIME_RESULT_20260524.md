# SAMI3 -> RAIJU Voltron-TubeShell Product Runtime Smoke

Date: 2026-05-24

## Scope

This checkpoint verifies that the current Fortran runtime hook can ingest the
stage-2 SAMI3 product generated with the prototype Voltron TubeShell-coordinate
mapping:

```text
SAMI3 L/MLT grid
-> Voltron TubeShell cell-centered Lb + lon0
-> RAIJU ShellGrid /RaiCplMomentsOnly
```

The runtime reader interface is unchanged.  It still reads only:

```text
/RaiCplMomentsOnly
```

The TubeShell geometry is used upstream by the Python product generator and is
archived in the weight-file diagnostics.

## Input Product

Input HDF5:

```text
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_20260524.h5
```

Runtime deck:

```text
analysis/runtime_ingest_voltron_tubeshell_20260524/tinyCase_sami3_moments_tubeshell_lon0_D005_P005_stateTiote.xml
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
jobid = 7649574
jobname = sami3_tubeshell_smoke
state = COMPLETED
exit = 0:0
elapsed = 00:02:03
batch MaxRSS = 1023236K
node = qhcn078
```

Both baseline/control and TubeShell lon0 product logs reached:

```text
Fin
```

The product run log contains:

```text
SAMI3 moments ingest applied after RAIJU realtime pack
```

## Mapping Quality Carried By Product

The stage-2 product passed the runtime mapping quality checks:

```text
MappingQuality/weight_sum_runtime_min = 0.9999998807907104
MappingQuality/weight_sum_runtime_max = 1.0000001192092896
MappingQuality/finite_all_moments_runtime_mask_min = 1.0
MappingQuality/finite_all_moments_runtime_mask_max = 1.0
MappingQuality/coverage_count_runtime_min = 4.0
MappingQuality/coverage_count_runtime_max = 4.0
MappingQuality/closed_field_mask_min = 1.0
MappingQuality/closed_field_mask_max = 1.0
```

## Formula Checks

Final `raiCpl` restart formula checks against the baseline/control restart and
the TubeShell lon0 SAMI3 moment product:

```text
Pavg_formula_max_abs = 0.0
Pavg_formula_max_rel = 0.0
Pavg_actual_mean = 0.0014467727522445271
Pavg_actual_max = 0.011298136413097383

Davg_formula_max_abs = 0.0
Davg_formula_max_rel = 0.0
Davg_actual_mean = 86.26910149020793
Davg_actual_max = 817.850244140625

Pstd_formula_max_abs = 0.0
Pstd_formula_max_rel = 0.0
Dstd_formula_max_abs = 0.0
Dstd_formula_max_rel = 0.0
```

The ingested tiote range from the product is:

```text
tiote_input_min = 0.8779889941215515
tiote_input_max = 1.0004392862319946
```

No checked physical restart or history fields contained non-finite values:

```text
nonfinite_physics_base_raiCpl_res = []
nonfinite_physics_tubeshell_raiCpl_res = []
nonfinite_physics_base_raiju_res = []
nonfinite_physics_tubeshell_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_tubeshell_gam_res = []
nonfinite_physics_tubeshell_raiju_history = []
nonfinite_physics_tubeshell_gam_history = []
```

## Final-State Response

TubeShell lon0 product run versus baseline/control at final restart:

```text
State/Pavg_in max_abs = 0.011298136413097383
State/Pavg_in mean_abs = 0.0010438257161357557

State/Davg_in max_abs = 817.850244140625
State/Davg_in mean_abs = 86.21477040246327

State/eta max_abs = 89147087.11813514
State/eta mean_abs = 240123.65430572446

State/Density max_abs = 0.6470478858327899
State/Density mean_abs = 0.06418033143572646

State/Pressure max_abs = 0.0013832529208793465
State/Pressure mean_abs = 0.00017203304354966218

GAMERA/Gas0 max_abs = 0.6220269376977541
GAMERA/Gas0 mean_abs = 0.0055265866952026125
```

## Interpretation

The TubeShell-coordinate stage-2 product is runtime-safe for the current SAMI3
RAIJU hook.  The blend is exact at the `raiCpl` level, checked physics fields
remain finite, and the perturbation propagates continuously through RAIJU and
GAMERA.

This is still a prototype coordinate bridge, not a production physical mapping.
The next blocker is to replace this Lb/longitude coordinate remap with true
Voltron traced-tube or `bvol`-consistent flux-tube weights, with an explicit
open/closed coverage policy.

## Evidence

Archived under:

```text
logs/sami3_voltron_tubeshell_runtime_20260524/
```

Included small artifacts:

```text
base_control_tubeshell.log
tubeshell_lon0_D005_P005_stateTiote.log
slurm-7649574.out
run_tubeshell_lon0_smoke.sbatch
tinyCase_base_control_tubeshell.xml
tinyCase_sami3_moments_tubeshell_lon0_D005_P005_stateTiote.xml
tubeshell_lon0_runtime_summary.txt
```

Generated HDF5 runtime outputs are intentionally omitted from git and listed in
`manifests/large_artifacts_not_committed.txt`.
