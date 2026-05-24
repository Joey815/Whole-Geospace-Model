# SAMI3 -> RAIJU TubeShell bin_bVol massEq/total Pressure Test

Date: 2026-05-24

## Purpose

After validating the `bin_bvol_cc` TubeShell mapping with the default
number-density/ion-pressure semantics, this checkpoint exercises the existing
semantic switches:

```text
--density-mode massEq
--pressure-mode total
```

The goal is not to declare this the production choice.  The goal is to prove
that the current MAGE-facing `Pavg/Davg` interface can carry the conservative
mass-loading and total-pressure interpretation through the same sparse mapping,
masking, and runtime alpha-blending path.

## Stage-1 Source Semantics

The stage-1 `ds_over_B` product already contains the required diagnostics:

```text
Davg_num mean = 36795.40061156311 #/cc
Davg_massEq mean = 556836.1217093801 proton-equivalent #/cc
mu_eff min/max/mean = 1.3312475681304932 / 30.546707153320312 / 13.372474619928466

Pavg_i mean = 0.5670715121648862 nPa
Pavg_e mean = 0.6503766922784623 nPa
Pavg_total mean = 1.2174482041294163 nPa
```

## Stage-2 Product

Generated local product, not committed:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_massEq_total_voltron_tubeshell_l_mlt_lon0_bin_bvolcc_20260524.h5
```

Committed sidecar and logs:

```text
logs/sami3_tubeshell_bin_bvolcc_massEq_total_20260524/
```

Validator result:

```text
validated ...massEq_total_voltron_tubeshell_l_mlt_lon0_bin_bvolcc_20260524.h5
density_mode = massEq source=Davg_massEq
pressure_mode = total source=Pavg_total
runtime_mapping = weights
runtime_mapping_quality finite_all_fraction = 1.0
```

Mapped runtime statistics:

```text
RaiCplMomentsOnly.Pavg_mapped max/mean = 0.524895427015444 / 0.0873051053208327
RaiCplMomentsOnly.Davg_mapped max/mean = 133663.9049981192 / 19471.162734419504
runtime_valid_count = 5940
runtime_invalid_count = 2520
coverage_unique = [(0, 2520), (4, 4860), (6, 1080)]
```

Compared with default `num+ion` on valid cells:

```text
Pavg total/ion ratio min/max/mean = 1.999549890565594 / 2.1442725936188998 / 2.025805245665852
Davg massEq/num ratio min/max/mean = 1.6977211607149911 / 7.528251050239331 / 3.5996960672378715

Pstd difference = 0.0
Dstd difference = 0.0
tiote difference = 0.0
```

This confirms that only the selected bulk `Pavg/Davg` sources changed; the
current std and tiote channels remain unchanged.

## Runtime Smoke

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvolcc_massEq_total_20260524
```

Slurm:

```text
jobid = 7651166
state = COMPLETED
exit = 0:0
elapsed = 00:02:02
node = qhcn335
batch MaxRSS = 1020096K
```

Runtime settings:

```text
alphaDavg = 0.01
alphaPavg = 0.01
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
useStateTioteForIngest = T
```

The Fortran hook saw the expected naturally invalid coverage mask:

```text
SAMI3 moments valid mask counts Pavg/Davg/Pstd/Dstd/tiote:
5940 5940 5940 5940 5940
```

## Runtime Validation

Mask-gated blend formula checks were exact:

```text
Pavg formula_max_abs = 0.0
Davg formula_max_abs = 0.0
Pstd formula_max_abs = 0.0
Dstd formula_max_abs = 0.0
State/Pavg_in formula_max_abs = 0.0
State/Davg_in formula_max_abs = 0.0
```

Coverage-invalid cells preserve baseline exactly:

```text
Pavg invalid_preserve_max_abs = 0.0
Davg invalid_preserve_max_abs = 0.0
Pstd invalid_preserve_max_abs = 0.0
Dstd invalid_preserve_max_abs = 0.0
State/Pavg_in invalid_preserve_max_abs = 0.0
State/Davg_in invalid_preserve_max_abs = 0.0
```

Enabled valid cells changed by the conservative alpha:

```text
Pavg valid_delta_max_abs = 0.00524895429611206
Davg valid_delta_max_abs = 1336.6390625000001
Pstd valid_delta_max_abs = 0.0
Dstd valid_delta_max_abs = 0.0
```

Checked RAIJU physics arrays were finite:

```text
State/Density nonfinite_actual = 0
State/Pressure nonfinite_actual = 0
State/eta nonfinite_actual = 0
```

## Interpretation

The software path for mass-equivalent density and total thermal pressure is now
validated through the current `bin_bvol_cc` mapping and runtime alpha-blending
hook.  The physics decision is still open:

```text
Davg_num is safer if downstream RAIJU expects number density.
Davg_massEq is safer if downstream GAMERA mass loading interprets Davg as proton-equivalent density.
Pavg_i preserves cold ion pressure only.
Pavg_total adds electron pressure, but may double-count if original MAGE Pavg carries hot pressure.
```

Recommended next runtime policy remains conservative:

```text
alphaDavg = 0.01-0.05
alphaPavg = 0.0-0.01 until pressure semantics are confirmed
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0 only for diagnostic runs with useStateTioteForIngest=T
```
