# SAMI3 -> RAIJU Forced Extrapolation Mask Runtime Result

Date: 2026-05-24

## Purpose

The real TubeShell lon0 target is fully valid for the current tiny smoke grid,
so `coverage_closed_no_extrap` previously exercised only the all-valid path.
This checkpoint creates a controlled synthetic artifact with exactly one
RAIJU target cell marked as extrapolated:

```text
j = 0
i = 0
```

The goal is to verify the full runtime behavior for a channel-0 cell whose
SAMI3 product value is finite but whose mask is false.

## Forced Weight Artifact

Starting file:

```text
sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_extrapflag_20260524.h5
```

Forced local edit:

```text
/quality/extrapolation_flag[0,0] = 1
/quality/l_extrapolated_i[0] = 1
```

Committed small artifact:

```text
logs/sami3_forced_extrap_mask_20260524/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_forced_extrap_j000_i000_20260524.h5
```

Generation log:

```text
logs/sami3_forced_extrap_mask_20260524/force_extrap_weight_j000_i000.log
```

## Stage-2 Result

Stage-2 was run with:

```text
--mapping-mode weights
--runtime-mask-policy coverage_closed_no_extrap
```

The diagnostic product validated successfully:

```text
validate_forced_extrap_policy: passed
runtime_valid_count = 8459
runtime_invalid_count = 1
extrapolation_flag_runtime_count = 1
forced_cell_runtime_valid = 0
Pavg/Davg/Pstd/Dstd channel-0 mask count = 8459
Pavg/Davg/Pstd/Dstd channel-1 mask count = 0
tiote mask count = 8459
```

The generated HDF5 diagnostic product is local only and listed in the large
artifact manifest:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_forced_extrap_j000_i000_20260524.h5
```

## Runtime Smoke

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_forced_extrap_mask_20260524
```

Slurm:

```text
jobid = 7650550
state = COMPLETED
exit = 0:0
elapsed = 00:02:19
node = qhcn290
batch MaxRSS = 1004776K
```

Runtime settings:

```text
alphaDavg = 0.05
alphaPavg = 0.05
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
useStateTioteForIngest = T
```

Runtime log confirmed the Fortran hook saw only 8459 valid cells:

```text
SAMI3 moments valid mask counts Pavg/Davg/Pstd/Dstd/tiote:
8459 8459 8459 8459 8459
```

## Critical Check

For the forced-invalid cell `(channel=0, j=0, i=0)`, all checked runtime fields
preserved the baseline:

```text
Pavg forced_cell_actual_minus_base = 0.0
Davg forced_cell_actual_minus_base = 0.0
Pstd forced_cell_actual_minus_base = 0.0
Dstd forced_cell_actual_minus_base = 0.0
State/Pavg_in forced_cell_actual_minus_base = 0.0
State/Davg_in forced_cell_actual_minus_base = 0.0
State/Density forced_cell_actual_minus_base = 0.0
State/Pressure forced_cell_actual_minus_base = 0.0
State/eta forced_cell_actual_minus_base = 0.0
```

A neighboring valid cell did change for the enabled blended fields:

```text
Pavg valid_neighbor_actual_minus_base = -5.666370116850562e-05
Davg valid_neighbor_actual_minus_base = 0.08444136376925193
```

The mask-gated formula matched runtime output within write precision:

```text
Pavg formula max_abs = 5.587935444223424e-10
Davg formula max_abs = 3.662109372726263e-05
Pstd formula max_abs = 0.0
Dstd formula max_abs = 0.0
nonfinite checked physics arrays = none
```

## Conclusion

This closes the runtime-mask contract test.  The adapter now has evidence for:

```text
mask true  -> finite SAMI3 scalar moment is blended/applied
mask false -> original RAIJU/MAGE moment is preserved cell-by-cell
```

The next remaining physics work is no longer mask behavior; it is replacing the
current TubeShell `Lb/lon0` interpolation with a bvol-aware traced-tube remap
and then running the same rejection test on naturally invalid cells instead of
this forced synthetic one.
