# SAMI3 -> RAIJU Runtime Mask Policy Result

Date: 2026-05-24

## Purpose

This step moves the SAMI3 stage-2 RAIJU product from a purely finite-value
runtime mask toward an explicit mapping-quality mask.  The runtime Fortran hook
was already mask-gated; this update makes the generated
`RaiCplMomentsOnly/*_mask` arrays optionally reflect coverage, closed-field,
and extrapolation quality before the product reaches Voltron/RAIJU.

## Code change

Updated scripts:

- `code/kaiju_sami3_moments/scripts/sami3_moments/sami3_moments_to_raiju_diag.py`
- `code/kaiju_sami3_moments/scripts/sami3_moments/validate_sami3_mage_moments.py`

New stage-2 option:

```text
--runtime-mask-policy finite
--runtime-mask-policy coverage
--runtime-mask-policy coverage_closed
--runtime-mask-policy coverage_closed_no_extrap
```

`finite` is the backward-compatible default.  The non-finite policies require
`--mapping-mode weights` and build a `MappingQuality/runtime_valid_mask` from
the weight-file diagnostics.  Runtime moment masks are then:

```text
RaiCplMomentsOnly/<field>_mask = finite(mapped_field) AND runtime_valid_mask
```

The validator now checks that the runtime masks match
`MappingQuality/runtime_valid_mask` when that dataset is present.  Older
products without the dataset still validate through the previous path.

## Product generated

Input moments:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_moments_stubpayload_ds_over_B_20260524.h5
```

Weight file:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_to_raiju_weights_voltron_tubeshell_l_mlt_lon0_20260524.h5
```

New product, not committed because it is HDF5:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_coverage_closed_no_extrap_20260524.h5
```

Committed sidecar/log:

```text
logs/sami3_runtime_mask_policy_20260524/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_voltron_tubeshell_l_mlt_lon0_coverage_closed_no_extrap_20260524.json
```

## Product validation

Commands were run with:

```text
/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python
```

Results:

```text
py_compile: passed
validate new coverage_closed_no_extrap product: passed
validate old finite-mask TubeShell product: passed
runtime_mask_policy: coverage_closed_no_extrap
runtime_valid_mask shape: 188 x 45
runtime_valid_mask count: 8460
runtime_valid_mask fraction: 1.0
coverage_count_runtime min/max: 4 / 4
closed_field_mask count: 8460
extrapolation_flag_runtime count: 0
Pavg/Davg/Pstd/Dstd channel-0 mask count: 8460
Pavg/Davg/Pstd/Dstd channel-1 mask count: 0
tiote_mask count: 8460
```

The current TubeShell lon0 map is fully covered and closed with no
extrapolation, so the new policy mask is all valid for this case.  The value of
this step is the product contract: future partial/open-field/traced-tube maps
can now prevent invalid cells from being applied at runtime.

## Runtime smoke

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_policy_mask_20260524
```

Slurm:

```text
jobid: 7650229
state: COMPLETED
exit: 0:0
elapsed: 00:02:04
node: qhcn335
batch MaxRSS: 1023064K
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

Runtime summary:

```text
policy_ingest_line_present: True
policy_valid_count_line_present: True
Pavg policy formula max_abs: 5.59e-10
Davg policy formula max_abs: 3.66e-05
Pstd policy formula max_abs: 0.0
Dstd policy formula max_abs: 0.0
nonfinite checked physics arrays: none
old finite-mask runtime equivalence: max_abs 0.0 for checked RAIJU/raiCpl arrays
```

The small formula residuals for `Pavg` and `Davg` are float roundoff in the
written runtime files.  The new policy product produced the same runtime result
as the previous finite-mask product because this particular weight file has
complete valid coverage.

## Archived logs

```text
logs/sami3_runtime_mask_policy_20260524/
  stage2_generation_coverage_closed_no_extrap.log
  validate_coverage_closed_no_extrap.log
  validate_backcompat_old_tubeshell_finite.log
  run_tubeshell_lon0_policy_mask_smoke.sbatch
  tinyCase_base_control_policy_mask.xml
  tinyCase_sami3_moments_tubeshell_lon0_policy_mask_D005_P005_stateTiote.xml
  slurm-7650229.out
  sacct_7650229.txt
  base_control_policy_mask.log
  tubeshell_lon0_policy_mask_D005_P005_stateTiote.log
  tubeshell_lon0_policy_mask_runtime_summary.txt
```

## Next step

The next physical blocker is no longer runtime mask plumbing.  It is building a
less synthetic mapping product whose valid cells can actually differ from all
true:

1. replace the current TubeShell lon0 proxy geometry with traced/Voltron tube
   geometry where available;
2. carry `bvol`/`Bmin`/closed-field diagnostics into the weight file;
3. generate products where `coverage_closed_no_extrap` can reject bad cells;
4. rerun the same runtime mask-gated smoke to confirm rejected cells preserve
   original RAIJU moments.
