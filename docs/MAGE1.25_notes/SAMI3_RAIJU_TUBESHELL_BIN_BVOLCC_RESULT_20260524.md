# SAMI3 -> RAIJU TubeShell bVol-Binned Mapping Prototype

Date: 2026-05-24

## Purpose

The previous `voltron_tubeshell_l_mlt` prototype used traced TubeShell
coordinates (`Lb + lon0/lonc`), but its Voltron-to-RAIJU step still behaved
like shell-grid interpolation.  This checkpoint adds a stronger prototype:

```text
--voltron-compose-weight-mode bin_bvol_cc
```

Instead of evaluating each RAIJU target from a single interpolated Voltron
sample, `bin_bvol_cc` bins Voltron TubeShell cell centers into the coarser
RAIJU target L/MLT cells and weights contributing source cells by Voltron
`bvol_cc`.

This is still a prototype mapping, not a production flux-tube-volume mapper.
It is, however, the first current path where multiple traced TubeShell cells
can contribute to one RAIJU target cell with explicit bVol weighting.

## Code Change

Updated:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/build_sami3_to_raiju_weights.py
code/kaiju_sami3_moments/scripts/sami3_moments/sami3_moments_to_raiju_diag.py
code/kaiju_sami3_moments/scripts/sami3_moments/README.md
```

New compose modes:

```text
--voltron-compose-weight-mode interp
--voltron-compose-weight-mode bvol_cc
--voltron-compose-weight-mode bin_bvol_cc
```

The simple `bvol_cc` mode was tested first.  It multiplies interpolation terms
by `bvol_cc`, but with the current one-source-per-target stencil the per-target
normalization cancels that factor.  It is therefore numerically a no-op for the
current template:

```text
Pavg bvol_cc_vs_interp_max_abs = 1.8189894035458565e-12
Davg bvol_cc_vs_interp_max_abs = 0.0
Pstd bvol_cc_vs_interp_max_abs = 0.0
Dstd bvol_cc_vs_interp_max_abs = 0.0
tiote bvol_cc_vs_interp_max_abs = 0.0
```

The implemented useful mode is `bin_bvol_cc`.

## Generated Weight File

Committed small artifact:

```text
logs/sami3_tubeshell_bin_bvolcc_20260524/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvolcc_20260524.h5
logs/sami3_tubeshell_bin_bvolcc_20260524/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_bin_bvolcc_20260524.json
```

Generation summary:

```text
mapping_mode = voltron_tubeshell_l_mlt
voltron_tube_longitude = lon0
voltron_compose_weight_mode = bin_bvol_cc
sparse_weight_count = 25920
coverage_count_min/max = 0 / 6
coverage_count unique = [(0, 2520), (4, 4860), (6, 1080)]
weight_sum_positive_min/max = 0.9999998807907104 / 1.0000001192092896
runtime_valid_count = 5940
runtime_invalid_count = 2520
closed_field_cell_count = 8460
closed_field_fraction = 1.0
```

Interpretation: all target cells remain closed-field, but 2520 cells have no
Voltron TubeShell source centers in the target bin and are therefore invalid
under the runtime coverage mask.

## Stage-2 Product

Stage-2 was run with:

```text
--mapping-mode weights
--runtime-mask-policy coverage_closed_no_extrap
```

Local diagnostic product, not committed:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvolcc_20260524.h5
```

Committed sidecar:

```text
logs/sami3_tubeshell_bin_bvolcc_20260524/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_bin_bvolcc_20260524.json
```

Validation result:

```text
validated ...bin_bvolcc_20260524.h5
runtime_mapping = weights
runtime_mask_policy = coverage_closed_no_extrap
runtime_mapping_quality finite_all_fraction = 1.0
```

Compared with the previous TubeShell `interp` product on valid cells,
`bin_bvol_cc` changes the mapped scalar moments:

```text
Pavg valid_max_abs = 0.022859632968902588
Pavg valid_rms = 0.007996797561645508
Pavg mean interp/bin = 0.05558444932103157 / 0.06074320524930954

Davg valid_max_abs = 1417.8154296875
Davg valid_rms = 582.39453125
Davg mean interp/bin = 4657.79296875 / 5045.98828125

Pstd valid_max_abs = 0.050461336970329285
Dstd valid_max_abs = 3106.8154296875
tiote valid_max_abs = 0.018895208835601807
```

## Runtime Smoke

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvolcc_20260524
```

Slurm:

```text
jobid = 7651071
state = COMPLETED
exit = 0:0
elapsed = 00:02:08
node = qhcn290
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

The Fortran hook read the naturally invalid coverage mask:

```text
SAMI3 moments valid mask counts Pavg/Davg/Pstd/Dstd/tiote:
5940 5940 5940 5940 5940
```

## Runtime Validation

The runtime validation compared baseline and SAMI3-ingest restart outputs
against the exact mask-gated blend formula:

```text
Pavg formula_max_abs = 0.0
Davg formula_max_abs = 0.0
Pstd formula_max_abs = 0.0
Dstd formula_max_abs = 0.0
State/Pavg_in formula_max_abs = 0.0
State/Davg_in formula_max_abs = 0.0
```

Coverage-invalid cells preserve the original baseline:

```text
Pavg invalid_preserve_max_abs = 0.0
Davg invalid_preserve_max_abs = 0.0
Pstd invalid_preserve_max_abs = 0.0
Dstd invalid_preserve_max_abs = 0.0
State/Pavg_in invalid_preserve_max_abs = 0.0
State/Davg_in invalid_preserve_max_abs = 0.0
```

Enabled valid cells changed continuously:

```text
Pavg valid_delta_max_abs = 0.012439010292291643
Davg valid_delta_max_abs = 887.7487304687501
Pstd valid_delta_max_abs = 0.0
Dstd valid_delta_max_abs = 0.0
```

Checked RAIJU physics arrays were finite:

```text
State/Density nonfinite_actual = 0
State/Pressure nonfinite_actual = 0
State/eta nonfinite_actual = 0
```

## Conclusion

This closes the next runtime mapping step after forced synthetic mask testing:
the adapter now handles naturally invalid target cells from a bVol-binned
TubeShell coverage map, preserving baseline values where coverage is absent and
applying exact alpha blending where coverage is present.

Remaining physics work:

```text
1. Replace lon0/bin center assignment with a true traced-tube flux-volume map.
2. Decide whether Davg runtime should use number density or mass-equivalent density.
3. Decide whether Pavg runtime should use ion pressure, total pressure, or a cold correction.
4. Run longer stability tests after the physical density/pressure semantics are selected.
```
