# SAMI3 RAIJU Mask-Gated Runtime Ingest

Date: 2026-05-24

## Scope

This checkpoint fixes and verifies the runtime semantics of the
`RaiCplMomentsOnly/*_mask` datasets written by the SAMI3 stage-2 product.

Before this change, `ReadInSGV` read the product masks, but
`applySami3RaiCplMoments` restored the original RAIJU masks before blending and
therefore did not use the product masks as a coverage gate.  That meant any
channel/cell with a valid array value but a false product mask could still be
blended into the live RAIJU coupler.

The runtime hook now:

```text
1. saves the original RAIJU data and masks
2. reads SAMI3 Pavg/Davg/Pstd/Dstd/tiote and their *_mask datasets
3. uses the SAMI3 masks as the input-use masks for blend/floor/clamp
4. restores the original RAIJU masks after ingest
5. leaves mask=false channel/cell values equal to the original RAIJU values
```

This makes `/RaiCplMomentsOnly/*_mask` an actual runtime coverage policy rather
than only a diagnostic dataset.

## Code Change

Changed file:

```text
code/kaiju_sami3_moments/src/voltron/modelInterfaces/raijuCplHelper.F90
```

Key behavior:

```text
mask=true:
  X_new = (1 - alpha) * X_original + alpha * X_SAMI3
  floors/clamps apply

mask=false:
  X_new = X_original
  floors/clamps do not alter that cell/channel
```

The runtime log now prints one-time valid mask counts:

```text
SAMI3 moments valid mask counts Pavg/Davg/Pstd/Dstd/tiote
```

## Build Result

The copied working tree was rebuilt successfully:

```text
make -C /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523 -j8
```

The build completed with:

```text
[100%] Built target voltron.x
[100%] Built target voltron
```

## Runtime Smoke

Slurm job:

```text
jobid = 7649667
jobname = sami3_maskgate_smoke
state = COMPLETED
exit = 0:0
elapsed = 00:02:03
batch MaxRSS = 1023576K
node = qhcn176
```

Input product:

```text
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_20260524.h5
```

Runtime settings:

```text
alphaDavg = 0.05
alphaPavg = 0.05
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
moments/useStateTioteForIngest = T
sami3Moments/group = /RaiCplMomentsOnly
```

Both baseline/control and mask-gated product logs reached:

```text
Fin
```

The product log contains:

```text
SAMI3 moments ingest applied after RAIJU realtime pack
SAMI3 moments valid mask counts Pavg/Davg/Pstd/Dstd/tiote: 8460 8460 8460 8460 8460
```

## Formula Checks

The `raiCpl` restart matches the mask-gated formula exactly:

```text
Pavg_masked_formula_max_abs = 0.0
Pavg_masked_formula_max_rel = 0.0
Davg_masked_formula_max_abs = 0.0
Davg_masked_formula_max_rel = 0.0
Pstd_masked_formula_max_abs = 0.0
Pstd_masked_formula_max_rel = 0.0
Dstd_masked_formula_max_abs = 0.0
Dstd_masked_formula_max_rel = 0.0
```

Channel coverage behavior:

```text
Pavg_channel0_mask_true_count = 8460
Pavg_channel0_vs_base_max_abs = 0.011298136413097383
Pavg_channel1_mask_true_count = 0
Pavg_channel1_vs_base_max_abs = 0.0

Davg_channel0_mask_true_count = 8460
Davg_channel0_vs_base_max_abs = 817.850244140625
Davg_channel1_mask_true_count = 0
Davg_channel1_vs_base_max_abs = 0.0
```

So the bulk SAMI3 channel is blended, while the non-bulk channel remains
identical to baseline.

No checked physical restart or history fields contained non-finite values:

```text
nonfinite_physics_base_raiCpl_res = []
nonfinite_physics_maskgate_raiCpl_res = []
nonfinite_physics_base_raiju_res = []
nonfinite_physics_maskgate_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_maskgate_gam_res = []
nonfinite_physics_maskgate_raiju_history = []
nonfinite_physics_maskgate_gam_history = []
```

## Interpretation

This closes a runtime correctness gap in the SAMI3 -> RAIJU adapter.  The
stage-2 product can now carry explicit coverage through its masks, and the
Fortran hook will preserve the native MAGE/RAIJU plasma moments outside that
coverage.

This does not yet solve the production physical mapping problem.  The remaining
physics blocker is still a true Voltron traced-tube or `bvol`-consistent
flux-tube remap.  This change is required before that next mapping can be used
safely, because it prevents uncovered cells/channels from being modified.

## Evidence

Archived under:

```text
logs/sami3_tubeshell_maskgate_runtime_20260524/
```

Included small artifacts:

```text
base_control_maskgate.log
tubeshell_lon0_maskgate_D005_P005_stateTiote.log
slurm-7649667.out
run_tubeshell_lon0_maskgate_smoke.sbatch
tinyCase_base_control_maskgate.xml
tinyCase_sami3_moments_tubeshell_lon0_maskgate_D005_P005_stateTiote.xml
tubeshell_lon0_maskgate_runtime_summary.txt
```

Generated HDF5 runtime outputs are intentionally omitted from git and listed in
`manifests/large_artifacts_not_committed.txt`.
