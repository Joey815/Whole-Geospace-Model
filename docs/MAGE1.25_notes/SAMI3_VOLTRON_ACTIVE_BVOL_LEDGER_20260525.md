# SAMI3 -> Voltron Active bVol Ledger

Date: 2026-05-25 CST

## Purpose

The previous flux-volume geometry audit showed that the current
`bin_bvol_overlap` mapping is reproducible, but it also showed that most valid
Voltron TubeShell bVol is rejected by the broad-footprint QC gate before it can
enter the current RAIJU target domain.

The next step toward a true traced-tube quadrature is to expose the volume
accounting already computed during Voltron field-line tracing.  The current
Voltron restart contains compressed TubeShell fields such as `bVol`, `Lb`,
`lon0`, `lonc`, and `nTrc`, but it does not contain the full traced-line arrays
`xyz(s)` and `B(s)`.

## Source Finding

The runtime code already has the needed integral split while tracing a field
line:

```text
magLine_T:
  xyz(-Nm:+Np, XDIR:ZDIR)
  Bxyz(-Nm:+Np, XDIR:ZDIR)
  magB(-Nm:+Np)
  Gas(-Nm:+Np, NVARMHD, 0:nSpc)

FLThermo:
  dvB        = sum(dl / bMag)
  dvB_active = sum(dl / bMag) only where both segment endpoints are inside
               the active ebGrid radial domain
```

Before this patch, `dvB_active` was used to normalize `avgP/avgN/stdP/stdN`
inside `FLThermo`, but it was not returned to `Line2Tube` or written into the
TubeShell restart.

## Patch

Archived patch:

```text
code/kaiju_sami3_moments/patches/voltron_active_bvol_ledger_20260525.patch
```

The patch adds compact diagnostic fields:

```text
Tube_T%bVolActive
Tube_T%bVolActiveFrac
TubeShell_T%bVolActive
TubeShell_T%bVolActiveFrac
```

It also extends `FLThermo` with an optional output:

```text
dvBActiveO
```

`Line2Tube` now captures `dvBActiveO` on the bulk species pass and writes:

```text
bVolActive     = dvBActive / oBScl
bVolActiveFrac = bVolActive / bVol
```

The Voltron TubeShell restart writer now emits:

```text
/TubeShell/bVolActive
/TubeShell/bVolActiveFrac
```

This is intentionally compact.  It does not write full traced-line arrays yet;
it only exposes the active-domain volume ledger that Voltron already uses for
field-line plasma averages.

## Mapper Support

The stage-2 weight builder now treats the new fields as optional.  If a future
Voltron template contains them, it will carry them through:

```text
/intermediate/bvol_active_corner
/intermediate/bvol_active_cc
/intermediate/bvol_active_frac_corner
/intermediate/bvol_active_frac_cc
```

Old Voltron templates remain compatible.  A reader smoke using the old
`sami3_moments_base_control.volt.Res.00000.h5` template produced the same sparse
runtime mapping as the schema v6 geometry-audit product:

```text
map/dst_index = identical
map/src_index = identical
map/weight max_abs_diff = 0
intermediate/voltron_to_raiju/weight max_abs_diff = 0
quality/coverage_count = identical
quality/weight_sum max_abs_diff = 0
optional active bVol datasets present = false
```

Reader-smoke archive:

```text
logs/sami3_active_bvol_ledger_reader_smoke_20260525/
```

## Validation Status

Completed checks:

```text
Fortran patch whitespace check = pass
Python mapper py_compile = pass
Old-template optional-reader smoke = pass
Kaiju rebuild = pass, [100%] Built target voltron.x
Runtime Voltron smoke = pass, job 7677534 COMPLETED 0:0
Regenerated active-ledger weight/audit artifact = pass
```

Runtime note:

```text
The first runtime smoke, job 7677510, exposed an IO chain capacity error after
adding two TubeShell restart fields:

  ERROR: Overflow on IO Chain, exiting ...

The source fix was to raise writeTubeShellRestart's local IOVars capacity from
50 to 60.  The rerun, job 7677534, completed cleanly:

  jobname = active_bvol_smk2
  state = COMPLETED
  exit = 0:0
  elapsed = 00:01:00
  node = qhcn349
  batch MaxRSS = 1026064K
  run_complete = 1
```

The new restart fields are present and finite in:

```text
analysis/runtime_ingest_active_bvol_ledger_smoke2_20260525/
  sami3_moments_active_bvol_ledger_smoke2.volt.Res.00000.h5

/TubeShell/bVol:
  shape = [189,181]
  finite = 34209/34209
  max = 18541.31774786079
  mean = 66.32110296651743

/TubeShell/bVolActive:
  shape = [189,181]
  finite = 34209/34209
  max = 18541.31774786079
  mean = 66.32110296651743

/TubeShell/bVolActiveFrac:
  shape = [189,181]
  finite = 34209/34209
  min/max = 0/1
  mean = 0.9838054313192435

For positive bVol cells:
  count = 33655
  bVolActive / bVol min/max/mean = 1/1/1
  max_abs_diff_vs_bVolActiveFrac = 0
```

Active-ledger audit:

```text
weight_compare stored/recomputed = 39853/39853
weight_compare missing/extra = 0/0
weight_compare max_abs_diff = 1.4889254773553517e-08

source_valid_bvol_sum = 2268463.9952379456
source_valid_bvol_active_sum = 2268463.9952379456

source_bvol_active_by_status:
  used fraction_of_valid_bvol_active = 0.00040379562605685195
  large_footprint fraction_of_valid_bvol_active = 0.9384275226700948
  outside_target fraction_of_valid_bvol_active = 0.061168681703848454

source_bvol_active_frac_stats_valid:
  finite_count/total = 33676/33676
  min = 0.25
  p01 = 0.5
  p05 = 1.0
  median = 1.0
  mean = 0.994061052381518
  max = 1.0
```

Evidence archive:

```text
logs/sami3_active_bvol_ledger_runtime_smoke_20260525/
```

## Next Gate

The compact active-domain ledger is now validated for this runtime template.
The next gate should decide how to use this ledger before adding a larger full
trace export:

```text
1. Keep /TubeShell/bVolActive and /TubeShell/bVolActiveFrac as the low-cost
   active-domain volume ledger in all new TubeShell mapping audits.
2. Define the target-domain closure rule that compares used, large_footprint,
   outside_target, and active-domain volume before accepting a SAMI3->RAIJU
   mapping as physically meaningful.
3. If the compact ledger is still insufficient, add an optional debug export of
   traced-line quadrature inputs: xyz(s), B(s), dl/B, and active-domain flags.
```
