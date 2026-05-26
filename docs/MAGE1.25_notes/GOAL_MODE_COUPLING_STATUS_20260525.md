# Goal-Mode Coupling Status

Date: 2026-05-25 CST

## Goal

Drive the current MAGE1.25 / WACCM-X / SAMI3 coupling prototype toward a
single verifiable online chain:

```text
WACCM-X/CAM runtime phys_state(:)
  -> SAMI3 online neutral receiver
REMIX/Voltron runtime potential payload
  -> SAMI3 online phi_weimer receiver
SAMI3 scalar moments
  -> RAIJU/GAMERA runtime ingest with conservative blending
```

The target remains a validated prototype, not a production physics coupling.

## Active Acceptance Gates

Status refreshed: 2026-05-26 00:42:00 CST.

### Latest Completed Gate: Source-Domain L Scan

The post-smoke source-domain scan quantifies whether extending the RAIJU target
L domain is a plausible fix for excluded Voltron active bVol:

```text
script = scripts/analyze_sami3_raiju_source_domain_lscan.py
archive = logs/sami3_raiju_source_domain_lscan_20260526/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_SOURCE_DOMAIN_LSCAN_20260526.md
```

Current source and target facts:

```text
source_positive_bvol_sum = 2268463.9951948179
source_L_bvol_weighted_mean = 354.10948435454907
source_L_max = 553.77520751953125
current_target_Lmax = 33.163437477526358
current_target_dipole_lat_deg = 10.0
```

Active bVol captured by hypothetical target Lmax:

```text
Lmax=33.16  included_fraction=0.000404035
Lmax=100    included_fraction=0.017065090
Lmax=200    included_fraction=0.108782366
Lmax=300    included_fraction=0.309611665
Lmax=350    included_fraction=0.523022953
Lmax=450    included_fraction=0.796474763
Lmax=500    included_fraction=0.866714372
```

Lmax required by active-bVol quantile:

```text
50% active bVol: Lmax=317.8696, dipole-equivalent lat=3.2153 deg
90% active bVol: Lmax=530.3418, dipole-equivalent lat=2.4888 deg
99% active bVol: Lmax=553.7748, dipole-equivalent lat=2.4355 deg
```

Interpretation:

```text
The outside-domain failure is not a small RAIJU grid tuning issue.  Capturing
meaningful fractions of active Voltron bVol would push the target boundary to
L~300-550, equivalent to only ~2.5-3.2 deg dipole latitude.
```

Next work order after this gate:

```text
1. Freeze the current schema v7 exclude-Lmax SAMI3 -> RAIJU path as the safe
   diagnostic/runtime adapter for target-domain density-only tests.
2. Do not force the current RAIJU target grid outward without a separate RAIJU
   grid/physics review.
3. Move the main goal-mode path back to WACCM-X/SAMI3 continued neutral/phi
   cadence and production-cadence policy, while keeping the RAIJU adapter as
   validated downstream feedback smoke.
```

### Previous Completed Gate: Exclude-Lmax Runtime Smoke

The schema v7 `exclude_above_target_lmax` stage-2 product now has a runtime
ingest smoke:

```text
archive = logs/sami3_exclude_lmax_runtime_smoke_20260526/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_EXCLUDE_LMAX_RUNTIME_SMOKE_20260526.md
jobid = 7678065
state = COMPLETED
exit = 0:0
elapsed = 00:04:10
node = qhcn067
```

The smoke ran two paired short checks:

```text
alpha=0 baseline recovery:
  alphaPavg=0 alphaDavg=0 alphaPstd=0 alphaDstd=0 alphaTiote=0

density-only response:
  alphaPavg=0 alphaDavg=0.05 alphaPstd=0 alphaDstd=0 alphaTiote=0
```

Both validators passed:

```text
validate_exclude_lmax_alpha0_smoke_summary: overall=ok
validate_exclude_lmax_dens005_smoke_summary: overall=ok
Pavg/Davg/Pstd/Dstd formula_max_abs = 0 for both labels
nonfinite physics fields = []
history_last_steps = Step#3 / Step#3
```

Alpha-zero baseline recovery is exact for checked final restart fields:

```text
State/Pavg_in max_abs = 0
State/Davg_in max_abs = 0
State/eta max_abs = 0
State/Density max_abs = 0
State/Pressure max_abs = 0
Gas0 max_abs = 0
```

Density-only alpha produces finite, formula-consistent response:

```text
State/Davg_in max_abs = 870.24472656250009
State/Density max_abs = 4.3658608802500751
Gas0 max_abs = 4.2673096857777404
```

Interpretation:

```text
The explicit source-domain policy product is now validated through the runtime
RAIJU ingest hook for baseline recovery and density-only response.  It remains
diagnostic/prototype physics because the source-domain accounting still excludes
about 99.96% of positive active Voltron source bVol above the current RAIJU
target Lmax.
```

### Previous Completed Gate: Explicit Source-Domain Policy Product

The stage-2 sparse weight builder now has an explicit source-domain policy for
Voltron TubeShell source cells outside the current RAIJU target L range:

```text
--voltron-source-domain-policy exclude_above_target_lmax
archive = logs/sami3_tubeshell_bin_bvol_overlap_exclude_lmax_20260526/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_SOURCE_DOMAIN_POLICY_EXCLUDE_LMAX_20260526.md
```

The generated weight file is schema v7 and writes:

```text
/intermediate/voltron_to_raiju/source_domain_excluded_mask
0 = included
1 = source Lb_cc above target Lmax
2 = source Lb_cc below target Lmin
```

Source-domain accounting:

```text
schema_version = 7
target_L_edge_max = 33.16343747752636
source_domain_skipped_above_lmax = 5852
source_domain_skipped_above_lmax_bvol_fraction = 0.999595965103914
source_domain_skipped_below_lmin = 0
```

Independent geometry audit and target-domain closure:

```text
stored_count = 39853
recomputed_count = 39853
weight_compare_max_abs_diff = 1.4889254773553517e-08
target_admissible_used_fraction = 1.0
target_admissible_outside_target_fraction = 0.0
```

The stage-2 `/RaiCplMomentsOnly` product made with this weight file passes the
repeatable mapping-product QC gate:

```text
overall = ok
runtime_valid_fraction = 0.9574468085106383
finite_all_fraction = 1.0
extrapolated_fraction = 0.0
weight_sum_valid_near_one max_dev = 1.1920928955078125e-07
tiote masked range = 0.8749623894691467 / 1.0004475116729736
```

### Previous Completed Gate: Voltron Trace-Line Debug Export Smoke

The geometry diagnostic is implemented and smoke-tested:

```text
patch = code/kaiju_sami3_moments/patches/voltron_trace_debug_export_20260525.patch
doc = docs/MAGE1.25_notes/SAMI3_VOLTRON_TRACE_DEBUG_EXPORT_20260525.md
archive = logs/sami3_trace_debug_export_smoke_20260525/
```

The export is default-off and controlled by:

```text
VOLTRON_TRACE_DEBUG_FILE
VOLTRON_TRACE_DEBUG_MAX_TUBES
```

Runtime smoke:

```text
jobid = 7677855
state = COMPLETED
exit = 0:0
elapsed = 00:01:00
node = qhcn349
trace_count = 8
run_complete = 1
```

The HDF5 diagnostic writes `/TraceLineDebug` with traced nodes, magnetic-field
vectors, `dl_over_B_edge`, active-edge mask, and source tube indices.  The
smoke file has no NaN/Inf in checked datasets.  The current export rewrites the
same HDF5 group on each `genVoltTubes` call, so it is a final-update debug
snapshot, not a time-series format.

The export now also supports targeted source-cell filtering:

```text
VOLTRON_TRACE_DEBUG_SOURCE_I
VOLTRON_TRACE_DEBUG_SOURCE_J
```

Targeted closure-failure smoke:

```text
archive = logs/sami3_trace_debug_target_i005_j095_20260525/
jobid = 7677907
state = COMPLETED
exit = 0:0
source_i = 5
source_j = 95
trace_count = 1
topo = 2
Nm = 834
Np = 0
Rmax = 190.349119 Rp
dl_over_B_sum_active = 3496.88043
```

This targeted cell is the largest active-bVol `outside_target` source in the
no-span closure audit: `bvol_active=14539.834`, `Lb_cc=450.228`,
`mapped_fraction=0`, `term_count=0`.

The targeted trace and no-span audit were then compared against the RAIJU target
L range:

```text
target_L_edge_max = 33.16343747752636
source_i=5, source_j=95 Lb_cc = 450.2276916503906
source_Lb_over_target_L_edge_max = 13.576026066522608
trace_Rmax_over_target_L_edge_max = 5.739728252832102
```

Global no-span classification by positive active bVol:

```text
positive_all active_bvol_sum = 2268464.0
positive_all above_target_Lmax_bvol_sum = 2267547.5
positive_all above_target_Lmax_bvol_fraction = 0.9995959821271133
positive_all inside_target_Lrange_bvol_fraction = 0.000403795629822371
outside_target above_target_Lmax_bvol_fraction = 0.9999998137995858
```

Interpretation: the closure blocker is dominated by Voltron source tube volume
outside the current RAIJU target L range.  Some high-L cells still get marked
`used` because their footprint clips a small target-domain sliver, but the
dominant active bVol cannot close into a target grid whose outer L edge is only
about 33.16.

Next work order after this gate:

```text
1. Decide the physical policy for source volume outside the RAIJU target
   L range: exclude, diagnostic project/clamp, or extend target domain.
2. Build the next sparse SAMI3 -> Voltron -> RAIJU product from trace edges for
   physically admissible target-domain volume.
3. Re-run the target-domain closure validator as the acceptance gate.
```

### Previous Completed Gate: Active bVol Helper MPI Datatype Fix

The active bVol ledger patch added two real fields to `Tube_T`.  The serial
Voltron smoke already passed, but the helper MPI path sends `Tube_T` using a
hand-written datatype in `src/voltron/mpi/volthelpers_mpi.F90`.  That datatype
still used the old layout.

Fix:

```text
expectedSize = 392 -> 408
blockLengths(3) = 13+NDIM+4*(1+MAXTUBEFLUIDS)
               -> 15+NDIM+4*(1+MAXTUBEFLUIDS)
patch = code/kaiju_sami3_moments/patches/voltron_active_bvol_ledger_20260525.patch
archive = logs/sami3_active_bvol_helper_mpi_build_20260525/
```

Validation:

```text
build_dir = /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_phi_direct_openmpi_20260525
target = voltron_mpi.x
result = [100%] Built target voltron_mpi.x
```

This keeps helper-enabled Voltron layouts compatible with the active bVol
ledger diagnostics.  The next geometry step still remains traced-line export;
this was a required consistency fix before adding more data to the tube path.

### Previous Completed Gate: SAMI3 -> RAIJU No-Span Closure Diagnostic

The target-domain closure validator was rerun after disabling both conservative
Voltron footprint span gates:

```text
archive = logs/sami3_raiju_target_closure_nospan_20260525/
voltron_overlap_max_l_span = 0
voltron_overlap_max_lon_span = 0
sparse_weight_count = 238146
overlap_split_term_count = 225658
overlap_max_terms_per_source_cell = 4050
coverage_count_max = 52
```

The no-span product remains an offline diagnostic, not a runtime candidate.
It recomputes the sparse geometry consistently:

```text
weight_count_match = 225658 vs 225658
weight_no_missing_terms = 0
weight_no_extra_terms = 0
weight_max_abs_diff = 2.9787811772763462e-08 <= 1e-06
```

But target-domain closure still fails:

```text
overall = FAIL
used_fraction = 0.112192593703183 < 0.5
large_footprint_fraction = 0.0 <= 0.05
outside_target_fraction = 0.8878074062968169 > 0.05
source_mapped_bvol_fraction_of_valid = 0.008957983012102013
```

Interpretation:

```text
The blocker is not just the conservative large-footprint threshold.  Disabling
that gate increases sparse terms by about 5x and allows individual source cells
to split into as many as 4050 target terms, but valid active bVol still does not
close into the RAIJU target domain.  The next fix must improve the traced-tube
geometry representation, not just tune overlap thresholds.
```

Next work order after this gate:

```text
1. Design the optional traced-line debug export needed for true ds/B
   quadrature: source tube id, s index, xyz(s), B(s), dl/B, active-domain flag.
2. Use the target-domain closure validator as the acceptance gate for the next
   geometry product.
3. Keep current bVol-overlap density-only runtime branch diagnostic until the
   closure validator passes.
```

### Previous Completed Gate: SAMI3 -> RAIJU Target-Domain Closure Gate

The active bVol ledger has now been turned into an explicit target-domain
closure validator:

```text
validator = scripts/validate_sami3_raiju_target_closure.py
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_TARGET_CLOSURE_GATE_20260525.md
archive = logs/sami3_raiju_target_closure_gate_20260525/
input = logs/sami3_active_bvol_ledger_runtime_smoke_20260525/sami3_raiju_flux_volume_geometry_audit_lon0_bvol_overlap_activeledger_20260525.json
bvol_source = active
require_active_ledger = true
```

Technical closure checks passed:

```text
weight_count_match = 39853 vs 39853
weight_no_missing_terms = 0
weight_no_extra_terms = 0
weight_max_abs_diff = 1.4889254773553517e-08 <= 1e-06
target_positive_fraction = 0.9574468085106383 >= 0.9
status_fraction_sum = 1.0
active_frac_all_finite = 33676/33676
active_valid_bvol_sum = 2268463.9952379456
```

Physical target-domain closure intentionally fails:

```text
overall = FAIL
used_fraction = 0.00040379562605685195 < 0.5
large_footprint_fraction = 0.9384275226700948 > 0.05
outside_target_fraction = 0.061168681703848454 > 0.05
```

Interpretation:

```text
The current bVol-overlap mapping is reproducible and the active-domain ledger
is finite, but the target-domain mapping captures far too little valid source
volume.  This remains a diagnostic/runtime adapter, not production physical
SAMI3->RAIJU coupling.
```

Next work order after this gate:

```text
1. Keep this validator as the acceptance gate for any new geometry product.
2. Export or reconstruct traced-tube geometry well enough to split the current
   large-footprint source cells into acceptable target-domain quadrature terms.
3. Do not promote pressure/std/tiote physical interpretation until the closure
   gate passes.
```

### Previous Completed Gate: Voltron Active bVol Ledger Runtime Smoke

The target-domain volume-accounting step is now built, smoke-tested, and
audited:

```text
patch = code/kaiju_sami3_moments/patches/voltron_active_bvol_ledger_20260525.patch
doc = docs/MAGE1.25_notes/SAMI3_VOLTRON_ACTIVE_BVOL_LEDGER_20260525.md
reader-smoke = logs/sami3_active_bvol_ledger_reader_smoke_20260525/
runtime-smoke = logs/sami3_active_bvol_ledger_runtime_smoke_20260525/
```

What changed:

```text
FLThermo now exposes optional dvBActiveO.
Line2Tube records bVolActive = dvBActive / oBScl.
Line2Tube records bVolActiveFrac = bVolActive / bVol.
TubeShell restart writer emits /TubeShell/bVolActive and
/TubeShell/bVolActiveFrac.
The Python stage-2 weight builder carries those fields into /intermediate
when they are present, while preserving compatibility with older templates.
The flux-volume geometry audit now reports active-domain bVol sums by mapping
status and active-fraction statistics.
```

Validation completed:

```text
Fortran patch whitespace check = pass
Python mapper py_compile = pass
old-template optional-reader smoke = pass
runtime sparse map unchanged:
  map/weight max_abs_diff = 0
  intermediate/voltron_to_raiju/weight max_abs_diff = 0
Kaiju rebuild = pass, [100%] Built target voltron.x
active-ledger runtime smoke = pass, job 7677534 COMPLETED 0:0
```

Runtime note:

```text
The first active-ledger smoke, job 7677510, found an IO chain capacity bug after
the two new TubeShell restart fields were added.  The fix was to raise
writeTubeShellRestart's local IOVars capacity from 50 to 60.  The rerun,
job 7677534, completed cleanly:

  elapsed = 00:01:00
  node = qhcn349
  batch MaxRSS = 1026064K
  run_complete = 1
```

Restart validation:

```text
/TubeShell/bVolActive exists and is finite: 34209/34209
/TubeShell/bVolActiveFrac exists and is finite: 34209/34209
/TubeShell/bVolActiveFrac min/max/mean = 0/1/0.9838054313192435
positive-bVol bVolActive/bVol min/max/mean = 1/1/1
positive-bVol max_abs_diff_vs_bVolActiveFrac = 0
```

Active-ledger audit:

```text
weight_compare stored/recomputed = 39853/39853
weight_compare missing/extra = 0/0
weight_compare max_abs_diff = 1.4889254773553517e-08
source_valid_bvol_active_sum = 2268463.9952379456

used fraction_of_valid_bvol_active = 0.00040379562605685195
large_footprint fraction_of_valid_bvol_active = 0.9384275226700948
outside_target fraction_of_valid_bvol_active = 0.061168681703848454

active_frac finite_count/total = 33676/33676
active_frac min/p01/p05/median/mean/max = 0.25/0.5/1/1/0.994061052381518/1
```

Next work order after this gate:

```text
1. Treat /TubeShell/bVolActive and /TubeShell/bVolActiveFrac as the compact
   active-domain ledger for new TubeShell mapping audits.
2. Define a target-domain closure acceptance rule using used, large_footprint,
   outside_target, and active-domain volume.
3. Only if that compact ledger is insufficient, add optional full traced-line
   debug export for xyz(s), B(s), dl/B, and active-domain flags.
```

### Previous Completed Gate: SAMI3 -> RAIJU Flux-Volume Geometry Audit

The bVol-overlap mapping is now independently auditable from its own HDF5
artifact:

```text
archive = logs/sami3_flux_volume_geometry_audit_20260525/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_FLUX_VOLUME_GEOMETRY_AUDIT_20260525.md
mapping product = ds_over_B + voltron_tubeshell_l_mlt + lon0 + bin_bvol_overlap
schema_version = 6
```

The schema v6 weight writer adds float64 TubeShell corner geometry and RAIJU
target bin edges:

```text
/intermediate/lon0_corner_rad
/intermediate/lonc_corner_rad
/intermediate/lat0_corner_rad
/intermediate/latc_corner_rad
/dst/L_edge
/dst/MLT_edge_deg_unwrapped
/dst/MLT_edge_deg
```

The runtime sparse map is unchanged from the previous bVol-overlap gate:

```text
map/weight max_abs_diff = 0
intermediate/voltron_to_raiju/weight max_abs_diff = 0
quality/coverage_count = identical
```

Independent audit result:

```text
stored_count = 39853
recomputed_count = 39853
missing_stored_terms = 0
extra_recomputed_terms = 0
max_abs_diff = 1.4889254773553517e-08
target_positive_fraction = 0.9574468085106383
source_mapped_bvol_fraction_of_valid = 0.00034417894730482345
```

Source bVol accounting:

```text
used fraction_of_valid_bvol = 0.00040379562605685195
large_footprint fraction_of_valid_bvol = 0.9384275226700948
outside_target fraction_of_valid_bvol = 0.06116868170384847
target_domain_proxy raw_sum_over_positive_target_bvol_sum = 0.09301927602773116
```

Interpretation:

```text
The current bVol-overlap mapping is reproducible and suitable as the current
diagnostic/conservative prototype.  It is still not production physics: the
next geometry task is target-domain flux-volume closure plus true traced-tube
flux-volume quadrature, not further tuning of the approximate corner-footprint
overlap weights.
```

Next work order after this gate:

```text
1. Define the target-domain volume accounting contract for SAMI3->RAIJU.
2. Implement traced-tube flux-volume quadrature on top of the schema v6
   geometry/audit infrastructure.
3. Keep the conservative density-only runtime branch on bVol-overlap until
   the quadrature path passes the same audit and runtime gates.
```

### Previous Completed Gate: SAMI3 -> RAIJU bVol-overlap Conservative Long1800

The 1800 s conservative bVol-overlap runtime gate is complete:

```text
mapping product = ds_over_B + voltron_tubeshell_l_mlt + lon0 + bin_bvol_overlap
archive = logs/sami3_tubeshell_bin_bvol_overlap_conservative_long1800_20260525/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_TUBESHELL_BIN_BVOL_OVERLAP_CONSERVATIVE_LONG1800_RESULT_20260525.md
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 0.0
```

Runtime:

```text
jobid = 7674095
jobname = sami3_bvolov_l1800
state = COMPLETED
exit = 0:0
elapsed = 00:41:34
node = qhcn075
batch MaxRSS = 1157928K
prototype raiju_writes = 362
prototype gamera_writes = 364
final history step = Step#361
```

Validated facts:

```text
runtime validator overall = ok
summary validator overall = ok
Pavg/Davg/Pstd/Dstd formula max_abs = 0
nonfinite physics restart checks = clean
```

Compared with previous conservative `bin_bvol_cc` long1800:

```text
raiCpl/Davg mean old/new = 88.62593804380671 / 91.86063199144719
raiCpl/Davg mean_abs diff = 7.765713378082814
State/Density mean_abs diff = 0.030174562468009765
GAMERA/Gas0 mean_abs diff = 0.002248990458541432
```

Interpretation:

```text
The bVol-overlap mapping is now the preferred conservative density-only
prototype for SAMI3->RAIJU/GAMERA.  Pressure/std/tiote runtime blending remains
disabled until their downstream semantics are settled.
```

Next work order after this gate:

```text
1. Keep bVol-overlap as the default prototype mapping for density-only tests.
2. Start the next physics-mapping upgrade: true traced-tube flux-volume
   quadrature, replacing the current corner-footprint overlap approximation.
3. In parallel, return to WACCM-X live neutral extraction and REMIX->SAMI3
   potential forcing for the full online chain.
```

### Previous Completed Gate: SAMI3 -> RAIJU TubeShell bVol-overlap smoke

The first TubeShell bVol-overlap mapping/runtime gate is complete:

The first TubeShell bVol-overlap mapping/runtime gate is complete:

```text
mapping product = ds_over_B + voltron_tubeshell_l_mlt + lon0 + bin_bvol_overlap
archive = logs/sami3_tubeshell_bin_bvol_overlap_20260525/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_TUBESHELL_BIN_BVOL_OVERLAP_RESULT_20260525.md
schema_version = 5
runtime_valid_fraction = 0.9574468085106383
weight_sum_valid max deviation = 1.1920928955078125e-07
```

Runtime smoke:

```text
prototype jobid = 7674022
prototype jobname = sami3_bvol_ov_smk
prototype state = COMPLETED
prototype exit = 0:0
prototype elapsed = 00:01:02
prototype node = qhcn049
prototype batch MaxRSS = 1018724K

baseline jobid = 7674051
baseline jobname = base_bvol_ov_smk
baseline state = COMPLETED
baseline exit = 0:0
baseline elapsed = 00:01:02
baseline node = qhcn287
baseline batch MaxRSS = 1018648K
```

Runtime settings:

```text
tFin = 11.5 s
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 0.0
```

Validated facts:

```text
mapping validator overall = ok
paired runtime validator overall = ok
summary validator overall = ok
Pavg/Davg/Pstd/Dstd formula max_abs = 0
nonfinite physics restart checks = clean
```

Interpretation:

```text
The center-binning mapping has been superseded by a geometry-QC bVol-overlap
prototype for the next conservative run.  This is still prototype mapping,
not production traced-tube quadrature, but it improves target coverage from
5940/8460 to 8100/8460 and removes the pathological broad-footprint source
cells before runtime ingest.
```

Next work order after this gate:

```text
1. Run a conservative 1800 s density-only bVol-overlap case:
   alphaDavg=0.05, alphaPavg=0, alphaPstd=0, alphaDstd=0, alphaTiote=0.
2. Compare against the previous conservative bin_bvol_cc long1800 gate.
3. Keep pressure disabled until Pavg production semantics are settled.
```

### Previous Completed Gate: RAIJU direct tiote debug output

The direct tiote diagnostic gate is complete:

```text
jobid = 7673602
jobname = sami3_tiote_dbg
state = COMPLETED
exit = 0:0
elapsed = 00:01:04
node = qhcn075
batch MaxRSS = 1197564K
archive = logs/sami3_tubeshell_bin_bvolcc_tiote_debug_20260525/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_TIOTE_DEBUG_OUTPUT_RESULT_20260525.md
```

Validated runtime facts:

```text
RAIJU/output doDebug = T exposes State tiote in raiju.h5
last_step = Step#3
last_step_keys_with_tiote = ["tiote"]
tiote_shape = [180, 37]
tiote_finite = true
tiote_min/max = 0.8914262056350708 / 4.0
tiote_nondefault_count = 4680
```

Interpretation:

```text
No Fortran output change is required for direct State%tiote diagnostics.
Future tiote scans can turn on RAIJU doDebug for short diagnostic checks, while
long production-style runs can keep doDebug disabled to avoid larger outputs.
```

Next work order after this gate:

```text
1. Keep pressure disabled until Pavg production semantics are settled.
2. Start replacing lon0 cell-center binning with a true traced-tube
   flux-volume map.
3. Use doDebug=T only for short tiote diagnostic gates, not default long runs.
```

### Previous Completed Gate: SAMI3 -> RAIJU bin_bvolcc tiote Long1800

The previous SAMI3 -> RAIJU/GAMERA scalar-moment gate is complete for the
tiote-enabled traced TubeShell bVol-binned mapping path:

```text
jobid = 7673207
jobname = sami3_bvcc_tiote
state = COMPLETED
exit = 0:0
elapsed = 00:39:24
node = qhcn075
batch MaxRSS = 1182664K
archive = logs/sami3_tubeshell_bin_bvolcc_tiote_long1800_20260525/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_TUBESHELL_BIN_BVOLCC_TIOTE_LONG1800_RESULT_20260525.md
```

Runtime settings:

```text
mapping product = ds_over_B + voltron_tubeshell_l_mlt + lon0 + bin_bvol_cc
runtime mapping = weights
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
moments/useStateTioteForIngest = T
```

Validated runtime facts:

```text
prototype reached Fin
prototype_raiju_writes = 362
prototype_gamera_writes = 364
fatal marker matches = 0
slurm_run_complete = 1
Pavg/Davg/Pstd/Dstd final formula checks = exact
checked RAIJU/GAMERA restart physics arrays contain no non-finite values
```

Dedicated tiote hook validation also passed:

```text
alpha values = [0.0, 0.05, 0.0, 0.0, 1.0]
runtime tiote min/max = 0.873951375484467 / 4.0
runtime valid mask counts Pavg/Davg/Pstd/Dstd/tiote = 5940 each
product tiote_mask count = 5940
product tiote masked min/max = 0.8739513754844666 / 1.0004502534866333
```

Direct final coupler inputs relative to the density-only run:

```text
State/Pavg_in max_abs = 0.0
State/Davg_in max_abs = 0.0
```

Downstream response relative to the density-only run:

```text
final State/Density mean_abs = 0.045968829418640946
final State/Pressure mean_abs = 6.635173480042011e-05
final GAMERA/Gas0 mean_abs = 0.0036967272713272883
```

Next work order after this gate:

```text
1. Keep pressure disabled until Pavg production semantics are settled.
2. Add output/validator support for State%tiote or equivalent direct tiote
   diagnostics, since current evidence is log/product based.
3. Start replacing lon0 cell-center binning with a true traced-tube
   flux-volume map.
```

### Previous Completed Gate: SAMI3 -> RAIJU Conservative bin_bvolcc Long1800

The current SAMI3 -> RAIJU/GAMERA scalar-moment gate is complete for the
conservative traced TubeShell bVol-binned mapping path:

```text
jobid = 7671981
jobname = sami3_bvcc_l1800
state = COMPLETED
exit = 0:0
elapsed = 01:21:54
node = qhcn075
batch MaxRSS = 1179452K
archive = logs/sami3_tubeshell_bin_bvolcc_conservative_long1800_20260525/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_TUBESHELL_BIN_BVOLCC_CONSERVATIVE_LONG1800_RESULT_20260525.md
```

Runtime settings:

```text
mapping product = ds_over_B + voltron_tubeshell_l_mlt + lon0 + bin_bvol_cc
runtime mapping = weights
alphaDavg = 0.05
alphaPavg = 0.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 0.0
```

Validated runtime facts:

```text
baseline/prototype both reached Fin
baseline_raiju_writes = 362
prototype_raiju_writes = 362
baseline_gamera_writes = 364
prototype_gamera_writes = 364
fatal marker matches = 0
slurm_run_complete = 1
Pavg/Davg/Pstd/Dstd final formula checks = exact
checked RAIJU/GAMERA restart physics arrays contain no non-finite values
```

The product gate also passed:

```text
mapping_mode = weights
runtime_valid_fraction = 0.7021276595744681
extrapolated_fraction = 0.0
coverage_valid_positive = valid_min 4
weight_sum_valid_max_deviation = 1.1920928955078125e-07
```

Next work order after this gate:

```text
1. Add a separate tiote-only scan on the same bin_bvolcc long1800 setup:
   alphaDavg=0.05, alphaPavg=0.0, alphaTiote=1.0 with
   moments/useStateTioteForIngest=T.
2. Keep pressure disabled until Pavg production semantics are settled.
3. Start replacing lon0 cell-center binning with a true traced-tube
   flux-volume map.
```

### Previous Completed Gate: No-Smoke 3pkt/3phi Direct-MPI Cadence

The previous same-stack WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-MPI
no-smoke continued-cadence gate is complete:

```text
jobid = 7671766
jobname = wxsami3_3p3f
state = COMPLETED
exit = 0:0
elapsed = 00:15:39
node = qhcn169
batch MaxRSS = 64920656K
archive = logs/waccmx_live_directmpi_nosmoke_dt300_3pkt_3phi_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_NOSMOKE_3PKT_3PHI_RESULT_20260525.md
```

Validated runtime facts:

```text
three WACCM-X/CESM live neutral packets from CAM phys_state(:)
packet 0 received by 32/32 SAMI3 workers
packet 1 received by 32/32 SAMI3 workers
packet 2 received by 32/32 SAMI3 workers
three Voltron direct-MPI phi frames received by SAMI3
phi validity windows cover the neutral packet hours
SAMI3 reached MASTER: All Done!
WACCM-X reached END OF MODEL RUN
SAMI3 direct phi done signal received: 3
skip_count = 0
bad_marker_count = 0
```

All standard validators returned `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run_strict
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

Next work order after this gate:

```text
1. Return to SAMI3 -> RAIJU/GAMERA scalar-moment physics blockers:
   traced flux-tube-volume weighting, L/MLT/tube mapping, and runtime
   blending/floors for Pavg/Davg/Pstd/Dstd/tiote.
2. Keep f19 as the validated online-control grid for now; design f09 and
   distributed live-neutral remap after the scalar-moment path is hardened.
```

### Previous Completed Gate: Direct-MPI Cache After Done

The previous same-stack WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-MPI
cache-after-done gate is complete:

```text
jobid = 7671608
jobname = wxsami3_cache
state = COMPLETED
exit = 0:0
elapsed = 00:14:12
node = qhcn005
batch MaxRSS = 61973.50M
archive = logs/waccmx_live_directmpi_cache_after_done_1pkt_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_CACHE_AFTER_DONE_RESULT_20260525.md
```

This run forced a second SAMI3 phi request after the direct-MPI sender had
already sent done:

```text
PHI_MAX_FRAMES = 1
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e-6
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 0
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 0
MAX_PACKETS = 1
```

Validated runtime facts:

```text
neutral packet 0 received by 32/32 SAMI3 workers
direct phi frame 0 received with valid_until=9.99999997E-07 h
SAMI3 direct phi done signal received during phi receive
WACCMX_PHI_CACHE_AFTER_DONE at hrut=8.33333358E-02 h
SAMI3 reached MASTER: All Done!
WACCM-X reached END OF MODEL RUN
skip_count = 0
bad_marker_count = 0
```

All standard validators returned `overall=ok`, and the supplemental strict
validator with `--require-cache-after-done` also returned `overall=ok`.

Next work order after this gate:

```text
1. Run a longer f19 direct-MPI cadence case with more than two neutral packets
   and continued phi cadence.
2. Keep f19 as the validated development grid; defer f09/distributed remap
   until continued cadence is stable.
3. Return to SAMI3 -> RAIJU/GAMERA physics blockers: traced flux-tube weighting,
   L/MLT mapping, and runtime blending/floors for scalar moments.
```

### Previous Completed Gate: No-Smoke Direct-MPI Phi Harness

The previous same-stack WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-MPI
no-smoke harness gate is complete:

```text
jobid = 7671470
jobname = wxsami3_nc1h
state = COMPLETED
exit = 0:0
elapsed = 00:14:55
node = qhcn660
batch MaxRSS = 64873580K
archive = logs/waccmx_live_directmpi_nosmoke_2pkt_1phi_harness_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_NOSMOKE_2PKT_1PHI_HARNESS_RESULT_20260525.md
```

This run validated the direct-MPI path without the previous final-frame smoke
controls:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL = 0
WACCMX_SAMI3_PHI_STOP_AFTER_DONE = 0
```

Validated runtime facts:

```text
two WACCM-X/CESM live neutral packets from CAM phys_state(:)
packet 0 received by 32/32 SAMI3 workers
packet 1 received by 32/32 SAMI3 workers
one Voltron direct-MPI phi frame received by SAMI3
Voltron direct-MPI phi done sent and consumed during SAMI3 finalize
SAMI3 reached MASTER: All Done!
WACCM-X reached END OF MODEL RUN
skip_count = 0
bad_marker_count = 0
```

All archived validators returned `ok=True` / `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run_strict
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

Harness note: with `WACCMX_SAMI3_PHI_STOP_AFTER_DONE=0`, Voltron continues
after the SAMI3 consumer is done.  The launcher now accepts a Voltron timeout
only after both `WACCMX_SAMI3_PHI_DIRECT sent done=` and `MASTER: All Done!`
are present.  This is a test-harness completion policy, not a production
physics stop policy.

Next work order after this gate:

```text
1. Force a second SAMI3 phi request after direct done to validate the
   WACCMX_PHI_CACHE_AFTER_DONE branch.
2. Run a longer f19 direct-MPI cadence case with more than two neutral packets
   and continued phi cadence.
3. Keep f19 as the validated development grid; defer f09/distributed remap
   until continued cadence is stable.
4. Return to SAMI3 -> RAIJU/GAMERA physics blockers: traced flux-tube weighting,
   L/MLT mapping, and runtime blending/floors for scalar moments.
```

### Previous Completed Gate: Live Neutral Cadence + Direct Voltron Phi

The earlier same-stack WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-MPI
cadence gate is complete:

```text
jobid = 7670231
jobname = wxsami3_ndone
state = COMPLETED
exit = 0:0
elapsed = 00:08:52
node = qhcn119
batch MaxRSS = 64922552K
archive = logs/waccmx_live_directmpi_neutral_doneaware_dt300_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_NEUTRAL_DONEAWARE_DT300_RESULT_20260525.md
```

This run validated the integrated online path:

```text
WACCM-X/CESM live neutral packets from CAM phys_state(:)
OpenMPI Voltron direct-MPI REMIX phi sender
SAMI3 online neutral receiver
SAMI3 direct phi receiver
two neutral packets at the 300 s CESM cadence
three changing phi frames
neutral/phi time-axis consistency
done-aware neutral receive/finalize ordering
```

All archived validators returned `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run_strict
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

Cadence conclusion: the SAMI3 neutral update gate must be tied to the CESM
packet cadence for multi-packet tests.  The receiver now uses:

```text
WXSAMI3_NEUTRAL_UPDATE_HOURS
WXSAMI3_NEUTRAL_SPAN_HOURS
```

with defaults preserving the older 0.25 hour behavior.  For this run both were
set to `0.08333333333333333`, matching the 300 s CESM packet cadence.

The neutral receiver is also done-aware: workers probe the next MPI tag before
expecting a neutral header, so a done tag arriving after the final packet is
stored and consumed during finalize instead of stranding the worker.

Next work order after this gate was:

```text
1. Replace SAMI3_PHI_SKIP_MADALA_AFTER_FINAL / WACCMX_SAMI3_PHI_STOP_AFTER_DONE
   with a continued production cadence policy.
2. Run a longer continued neutral/phi cadence case after the final-frame smoke
   policy is removed.
3. Keep f19 as the validated development grid, then design the f09/distributed
   live-neutral remap once cadence is stable.
4. Return to SAMI3 -> RAIJU/GAMERA physics blockers: traced flux-tube weighting,
   L/MLT mapping, and runtime blending/floors for scalar moments.
```

### WACCM-X/CESM -> SAMI3 Direct-Wait Phi Integration

Slurm:

```text
jobid = 7661005
jobname = wxsami3_ap2w
state = FAILED
exit = 1:0
elapsed = 00:06:23
batch MaxRSS = 60350988K
```

Launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525.sbatch
```

Run directory:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directwait_20260525_0000
```

This direct-wait file-based variant is no longer the active gate.  The current
active path is the direct-MPI Voltron sender on the same PRTE DVM, which is the
path validated by job `7670231`.

### Completed Stability Gates

The full append2 WACCM-X/CESM -> SAMI3 online integration gate is complete:

```text
jobid = 7659727
jobname = wxsami3_ap2
state = COMPLETED
exit = 0:0
elapsed = 00:05:18
node = qhcn332
batch MaxRSS = 60176444K
archive = logs/waccmx_append2_full_20260525/
```

Strict validation returned `overall=ok` for append2 online logs, phi payload
content, time-axis consistency, live packet contract, top-blend policy, and the
f19 runtime-map/ESMF-weight product.  SAMI3 reached `MASTER: All Done!`, WACCM-X
reached `END OF MODEL RUN`, and receiver-side neutral replay matched with
`max_rel=4.83248e-13`.

The earlier direct-MPI four-frame gate is complete:

```text
jobid = 7668967
jobname = wxsami3_dm4t1
state = COMPLETED
exit = 0:0
elapsed = 00:10:06
node = qhcn182
batch MaxRSS = 63607068K
archive = logs/waccmx_live_directmpi4_tphi1_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI4_RESULT_20260525.md
```

It validated one live neutral packet and four changing direct-MPI phi frames.
The follow-on `7670231` gate above extends this to two live neutral packets and
done-aware finalization.

The 1800 second recommended prototype gate is complete:

```text
jobid = 7663122
jobname = sami3_rai_long1800
state = COMPLETED
exit = 0:0
elapsed = 01:23:20
node = qhcn065
batch MaxRSS = 1169988K
archive = logs/sami3_dsB_lmlt_recommended_long1800_20260525/
```

Strict validation, mapping-product validation, and HDF5 summary validation all
returned `overall=ok`.  Baseline/control and recommended runs both reached
`Fin`; they wrote 362 RAIJU history outputs and 364 GAMERA history outputs, and
the final RAIJU/GAMERA history comparison matched at `Step#361`.

The previous 900 second recommended prototype gate is also complete:


```text
jobid = 7660334
jobname = sami3_rai_long900
state = COMPLETED
exit = 0:0
elapsed = 00:48:44
node = qhcn095
batch MaxRSS = 1067328K
archive = logs/sami3_dsB_lmlt_recommended_long900_20260525/
```

Strict validation and HDF5 summary artifacts have been committed and pushed.

## Next Work Order

1. Resume the SAMI3 -> RAIJU/GAMERA physical-moment blockers:
   - traced flux-tube volume weighting instead of simple/index weighting,
   - L/MLT or magnetic-tube geometry mapping instead of index resize,
   - explicit scalar-moment semantics for `Pavg/Davg/Pstd/Dstd/tiote`,
   - runtime blending/floors so density, pressure, std, and tiote can be staged
     independently.
2. Keep f19 as the validated online-control grid for now.  Design
   f09/distributed live neutral remap after the scalar-moment path is hardened.

`intel_expr` fallback note: the previous append2 expr job failed because
`module load` returned nonzero on a non-fatal `.modulerc` `module-hide` warning.
The expr launcher now tolerates that warning after probe jobs confirmed the
oneAPI/HDF5 environment is still applied and the CESM case env returns zero.
It has not been resubmitted yet to avoid racing the queued `intel` job against
the same CESM run directory.

## New Tooling Added In This Goal Pass

```text
scripts/validate_sami3_raiju_mapping_product.py
scripts/validate_wxsami3_append2_run.py --expect-direct-wait-mode
scripts/archive_wxsami3_append2_result.py --expect-direct-wait-mode
scripts/validate_wxsami3_topblend_policy.py
scripts/validate_wxsami3_runtime_map.py
scripts/validate_wxsami3_live_packet_contract.py field-stat gates
scripts/validate_wxsami3_source_flag_balance.py
scripts/validate_sami3_raiju_mapping_product.py strict moment gates
scripts/validate_remix_sami3_phi_payload.py
scripts/validate_wxsami3_time_axis.py
scripts/validate_sami3_raiju_summary.py
scripts/validate_wxsami3_replay_cadence.py
scripts/archive_current_goal_mode_runs.py
```

The mapping-product validator now gates `/RaiCplMomentsOnly` plus
`/MappingQuality` products before runtime ingest.  It now also verifies masked
Pavg/Davg/Pstd/Dstd non-negativity, tiote bounds, and the runtime mask
convention for the populated bulk channel.  The direct-wait validator now
distinguishes a completed pre-generated phi payload from a same-job producer
and waiter path.

The WACCM-X archive gate now also checks the live metadata schema, phi payload
content, top-blend policy diagnostics, and runtime-map/ESMF weight consistency.
The live packet contract validator now also checks live dump field bad-counts
and plausible ranges before replay, covering lat/lon, T, U/V, pressure, height,
mean molecular mass, and the major CAM species used for residual N2.
The source-flag balance validator now closes receiver-side source flags and
per-shell apply diagnostics against `wxsami3_live_meta.json`: total samples,
valid/invalid, above-top, N2 residual invalid, unknown flags, He native fallback,
W zero policy, and top-blend partitions must all agree.

The REMIX/Voltron phi payload now has an independent binary contract gate before
online send: exact schema/version/grid, exact byte size, finite/nonzero values,
strictly increasing frame hours, next-frame `valid_until` linkage, and optional
time-varying-frame enforcement.

The online WACCM-X/SAMI3 evidence gate now also checks timeline consistency:
sender and receiver neutral packet hours, receiver worker coverage, phi-frame
validity intervals, and whether neutral packet hours are covered by the
available phi payload frames.

The live neutral contract gate now also closes fallback accounting: above-top
cells, N2-negative residual cells, unknown invalid cells, and replay
initial/final fallback counts must agree with the source-flag metadata.
It also checks metadata cadence consistency: positive `dtime_phys_s`, positive
`send_every_nsteps`, and `packet_hour = nstep * dtime_phys_s / 3600`.
For legacy multi-packet archives that predate source-flag metadata, the replay
cadence gate verifies packet order, packet-hour cadence, rank count, and
replay-vs-receiver `max_rel` without overstating them as current full-contract
evidence.

The SAMI3 -> RAIJU/GAMERA long-run archive now turns summary diagnostics into a
hard gate: exact Pavg/Davg/Pstd/Dstd blending formula residuals, positive
Pavg/Davg inputs, empty nonfinite restart lists, matching RAIJU/GAMERA history
steps, and finite restart/history response metrics.

`archive_current_goal_mode_runs.py` freezes the strict append2 and direct-wait
archive commands for the active 2026-05-25 goal-mode jobs.  It checks `sacct`
first, skips incomplete jobs by default, and can be used with
`--allow-incomplete` only for explicit partial evidence snapshots.

## 2026-05-25 05:02 CST Update

The same-job Voltron phi writer + CESM/WACCM-X direct-wait run `7661005`
failed, but the failure is now isolated:

```text
archive = logs/waccmx_append2_directwait_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_DIRECTWAIT_FALSE_TIMEOUT_20260525.md
payload validator = overall=ok
source flag balance = ok
time-axis/topblend/runtime-map gates = ok
failure = WXSAMI3 phi payload wait timed out with correct 97044 byte payload present
```

Root cause: `wxsami3_wait_for_phi_payload()` opened the little-endian binary
payload without `convert='little_endian'`, while the sender read path and
payload writer both use little-endian.  That made the wait loop reject the
correct header and time out.

Patch applied to both the active CESM case SourceMod and the GitHub-tracked
SourceMod copy:

```text
code/cesm_source_mods/src.cam/wxsami3_online_stub_mod.F90
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523/SourceMods/src.cam/wxsami3_online_stub_mod.F90
```

The CESM case rebuilt successfully after the fix:

```text
build command used temporary CIME HOME:
  /home/jiaoy_group/jiaoy/data/CESM/experiments/cime_home_v3_qhslurm_20260525
case-local EXTRA_MACHDIR was cleared to avoid the v3 qhslurm fragment reload
MODEL BUILD HAS FINISHED SUCCESSFULLY
Total build time = 95.828171 seconds
```

Next immediate gate: commit/push this failure archive and endian wait fix, then
rerun direct-wait.  Acceptance is no timeout, two sender phi frames, two
receiver `WACCMX_PHI_RECV` records, receiver `MASTER: All Done!`, and strict
direct-wait archive `ok=true`.

## 2026-05-25 05:14 CST Update

The fixed direct-wait run passed:

```text
jobid = 7665666
jobname = wxsami3_ap2w
state = COMPLETED
exit = 0:0
elapsed = 00:08:05
node = qhcn644
archive = logs/waccmx_append2_directwait_fixed_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_DIRECTWAIT_FIXED_RESULT_20260525.md
archive ok = true
```

Key online markers:

```text
VOLTRON_WRITER_PID=2928528
DIRECT_WAIT_MODE=1
WXSAMI3 phi payload ready after wait ... size=97044 elapsed=1
WXSAMI3 sent phi payload frames: 2
WACCMX_PHI_RECV records: 2
MASTER: All Done!
END OF MODEL RUN
```

Strict gates passed:

```text
validate_wxsami3_append2_run = overall=ok
validate_remix_sami3_phi_payload = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_live_packet_contract = returncode 0
validate_wxsami3_time_axis = returncode 0
validate_wxsami3_topblend_policy = returncode 0
validate_wxsami3_runtime_map = returncode 0
```

The direct-wait launcher is patched so future runs stop the background Voltron
writer after CESM/SAMI3 complete.  In this fixed run the writer had already
produced the two-frame payload and the receiver had completed; manual stop was
used only to let the Slurm script continue to summary/replay QC instead of
idling on the standalone writer.

Immediate next work should move from control-path validation to production
coupling hardening:

```text
1. Replace file payload phi producer with a direct REMIX/Voltron -> SAMI3 online handoff.
2. Make f09/distributed live neutral remap explicit instead of f19 root-gather prototype.
3. Turn the top-blend policy into a production per-variable contract.
4. Continue SAMI3 -> RAIJU/GAMERA physical blockers: traced flux-tube weighting and geometry mapping.
```

## 2026-05-25 05:26 CST Update

The first direct REMIX/Voltron -> SAMI3 online phi handoff prototype passed as a
standalone SAMI3 validation:

```text
jobid = 7665788
jobname = sami3_dphi
state = COMPLETED
exit = 0:0
elapsed = 00:01:42
node = qhcn181
archive = logs/sami3_direct_phi_port_20260525/
doc = docs/MAGE1.25_notes/SAMI3_DIRECT_PHI_PORT_RESULT_20260525.md
```

This run separates the channels:

```text
neutral sender -> SAMI3 neutral MPI port
direct phi sender -> SAMI3 rank0 phi-only MPI port
```

Validated markers:

```text
SAMI3 direct phi port ready
SAMI3 direct phi sender connected
WACCMX_PHI_RECV records = 2
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 2
```

Strict gates:

```text
validate_sami3_direct_phi_run = overall=ok
validate_remix_sami3_phi_payload = overall=ok
recv_qc_compare = compare ok
```

New implementation pieces:

```text
SAMI3 env contract: SAMI3_PHI_DIRECT_PORT_FILE
code/sami3_receiver/waccmx_neutral_mod.f90
scripts/wxsami3_phi_direct_sender_stub.c
scripts/validate_sami3_direct_phi_run.py
slurm/run_sami3_online_receiver_direct_phi_port_20260525.sbatch
```

This removes CESM from the online phi forwarding path for the validated
standalone test.  The remaining production blocker is that the direct phi
sender still reads the existing Voltron payload file; next step is to replace
that sender stub with a runtime REMIX/Voltron sender path.

## 2026-05-25 06:40 CST Update

The active REMIX/Voltron -> SAMI3 direct-phi route has moved from the standalone
sender stub to a runtime Voltron sender.  `voltron_mpi.x` was rejected for this
smoke because it enters the MPI Gamera coupler route and waits for a remote
Gamera app.  The working executable is the MPI-enabled serial `voltron.x`, where
only `waccmx_stub_backend.F90` uses MPI to connect to the SAMI3 phi-only port.

Current run:

```text
jobid = 7666704
launcher = slurm/run_sami3_intelmpi_voltron_runtime_direct_phi_20260525.sbatch
doc = docs/MAGE1.25_notes/SAMI3_INTELMPI_VOLTRON_RUNTIME_DIRECT_PHI_RESULT_20260525.md
archive snapshot = logs/sami3_intelmpi_voltron_runtime_direct_phi_20260525/
```

Validated in the live snapshot:

```text
Voltron runtime direct sender connected to SAMI3
Voltron sent two changing phi frames and done=2
SAMI3 received WACCMX_PHI_RECV frame 0 and frame 1
phi payload binary validator = overall=ok
direct-phi handshake validator with --allow-incomplete-run = overall=ok
```

Not yet complete:

```text
strict whole-run validator still fails until SAMI3 reaches finalize and writes
MASTER: All Done!, online done markers, and recv_qc_compare.txt.
```

Next decision gate is whether `7666704` naturally exits before its 30 minute
limit.  If it times out, the next implementation step is a dedicated
smoke-exit/finalize path; rerunning the same parameters is not useful.

## 2026-05-25 08:05 CST Update

The runtime Voltron -> SAMI3 direct-phi smoke now has a strict completed run:

```text
jobid = 7667186
jobname = sami3_vrtd
state = COMPLETED
exit = 0:0
elapsed = 00:04:38
doc = docs/MAGE1.25_notes/SAMI3_INTELMPI_VOLTRON_RUNTIME_DIRECT_PHI_RESULT_20260525.md
archive = logs/sami3_intelmpi_voltron_runtime_direct_phi_20260525/
```

Key markers:

```text
Voltron runtime direct sender connected to SAMI3
Voltron sent two changing phi frames and done=2
Voltron stopped after done via WACCMX_SAMI3_PHI_STOP_AFTER_DONE=1
SAMI3 received WACCMX_PHI_RECV frame 0 and frame 1
SAMI3 reached MASTER: All Done!
SAMI3 received neutral done and direct-phi done
recv_qc_compare = ok
validate_sami3_direct_phi_run strict = overall=ok
validate_remix_sami3_phi_payload = overall=ok
```

This remains a smoke/finalize completion, not production electrodynamics,
because it uses:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL=1
```

That switch only activates after the final available direct-phi frame has been
received; it now returns cached last phi for subsequent `potpphi` calls so the
short online MPI smoke can finalize without dropping to a zero-potential field.
The production next step is a real cadence policy for post-final-frame
potential solves and multi-frame REMIX timing.

## 2026-05-25 08:27 CST Update

The runtime Voltron -> SAMI3 direct-phi path now has a clean four-frame cadence
smoke:

```text
jobid = 7667369
jobname = sami3_vrtd4
state = COMPLETED
exit = 0:0
elapsed = 00:07:13
launcher = slurm/run_sami3_intelmpi_voltron_runtime_direct_phi_4frame_20260525.sbatch
archive = logs/sami3_intelmpi_voltron_runtime_direct_phi_4frame_20260525/
```

Key markers:

```text
SAMI3 ntmmax = 5
Voltron sent frame 0, 1, 2, 3 and done=4
SAMI3 received WACCMX_PHI_RECV frame 0, 1, 2, 3
SAMI3 reached MASTER: All Done!
recv_qc_compare = ok
validate_sami3_direct_phi_run strict = overall=ok
validate_remix_sami3_phi_payload = overall=ok
```

The QC parser was also hardened against interleaved Fortran stdout lines in
multi-frame runs.  It now accepts only the expected `WACCMX_RECV_QC`
continuation widths and skips unrelated `d = ...` or `WACCMX_APPLY_*`
diagnostic lines.

## 2026-05-25 09:03 CST Update

The direct REMIX/Voltron -> SAMI3 online phi route now also passes with the
OpenMPI/PRTE stack used by the WACCM-X/CESM live-neutral branch:

```text
jobid = 7668135
jobname = sami3_ovrtd
state = COMPLETED
exit = 0:0
elapsed = 00:05:23
node = qhcn012
archive = logs/sami3_openmpi_voltron_runtime_direct_phi_20260525/
doc = docs/MAGE1.25_notes/SAMI3_OPENMPI_VOLTRON_RUNTIME_DIRECT_PHI_RESULT_20260525.md
```

This run used:

```text
OpenMPI/PRTE SAMI3 receiver
OpenMPI neutral replay sender
OpenMPI-enabled serial voltron.x
one PRTE DVM
```

Key markers:

```text
SAMI3 direct phi port ready
SAMI3 direct phi sender connected
Voltron sent WACCMX_SAMI3_PHI_DIRECT frame 0 and frame 1
SAMI3 received WACCMX_PHI_RECV frame 0 and frame 1
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL active; returning cached phi
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 2
```

Strict gates:

```text
validate_sami3_direct_phi_run = overall=ok
validate_remix_sami3_phi_payload = overall=ok
recv_qc_compare = ok
```

Important implementation note: OpenMPI `prun` did not reliably propagate the
Voltron direct-phi environment from the launcher subshell.  The working launcher
therefore exports every `WACCMX_SAMI3_PHI_*` variable explicitly with `prun -x`.

Immediate next work is to merge this OpenMPI direct Voltron phi route into the
existing live WACCM-X/CESM `phys_state(:)` neutral launcher.  That will replace
the current file-backed append/direct-wait phi handoff with a same-stack direct
Voltron -> SAMI3 MPI handoff.

## 2026-05-25 09:30 CST Update

The same-stack live WACCM-X/CESM + SAMI3 + OpenMPI Voltron direct-phi smoke now
passes:

```text
jobid = 7668385
jobname = wxsami3_dmpi
state = COMPLETED
exit = 0:0
elapsed = 00:07:10
node = qhcn005
batch MaxRSS = 63585144K
launcher = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
archive = logs/waccmx_live_directmpi_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_RESULT_20260525.md
```

This is the first completed integrated smoke where CESM/WACCM-X sends live
neutral forcing from CAM `phys_state(:)` while phi is sent by runtime OpenMPI
Voltron directly into the SAMI3 phi MPI port.  The old CESM file-backed phi
forwarding path is disabled in this launcher:

```text
WXSAMI3 phi payload enabled: F
```

Key markers:

```text
WXSAMI3 sent live neutral packet
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
WACCMX_SAMI3_PHI_DIRECT sent frame 0 and frame 1
WACCMX_SAMI3_PHI_DIRECT sent done=2
SAMI3 received WACCMX_PHI_RECV frame 0 and frame 1
MASTER: All Done!
WACCMX online done signal received: 1
SAMI3 direct phi done signal received: 2
```

Strict gates:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

This closes the current online control-path milestone.  It remains a prototype
physics coupling because the smoke still uses final-frame cache/stop controls:

```text
SAMI3_PHI_SKIP_MADALA_AFTER_FINAL=1
WACCMX_SAMI3_PHI_STOP_AFTER_DONE=1
```

Next work should move from online handoff validation to production hardening:
multi-cycle REMIX/SAMI3 cadence, f09/distributed live-neutral remap,
production top-blend/fallback policy, and the SAMI3 -> RAIJU/GAMERA traced
flux-tube weighting plus L/MLT mapping.

## 2026-05-25 11:10 CST Update

The first controlled 2-packet live-neutral plus direct-Voltron-phi run completed
the model runtime path but exposed a validator semantics bug:

```text
jobid = 7669353
jobname = wxsami3_p2p1
state = FAILED
exit = 1:0
elapsed = 00:06:50
node = qhcn005
archive = logs/waccmx_live_directmpi_2pkt_phi1_postfix_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_POSTFIX_RESULT_20260525.md
```

Runtime markers showed the coupling path succeeded:

```text
CESM sent live neutral packet 0 at hour 0.00000000
CESM sent live neutral packet 1 at hour 0.0833333358
SAMI3 received 32 worker QC rows for packet 0
SAMI3 received 32 worker QC rows for packet 1
Voltron sent one direct phi frame with final-valid cache
SAMI3 received WACCMX_PHI_RECV frame 0
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 1
```

The failed validator was not filtering apply diagnostics correctly.  Receiver
diagnostics carry WACCM-X packet hour, but `WACCMX_APPLY_*` diagnostics carry
SAMI3 apply hour.  For this run packet 1 has receiver hour `0.0833333358` but
apply hour `0.25`.  The validator now selects the packet-index-th distinct
apply-hour block unless `--apply-hour` is provided.

Post-fix validation on the same run logs is fully green:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

A clean rerun with the fixed validator is active:

```text
jobid = 7669527
run = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_2pkt_phi1_clean_20260525_0000
purpose = produce a Slurm COMPLETED record for the same 2-packet + direct-phi gate
```

## 2026-05-25 11:15 CST Update

The clean rerun completed successfully:

```text
jobid = 7669527
jobname = wxsami3_p2p1c
state = COMPLETED
exit = 0:0
elapsed = 00:06:54
node = qhcn660
batch MaxRSS = 64901032K
archive = logs/waccmx_live_directmpi_2pkt_phi1_clean_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_CLEAN_RESULT_20260525.md
```

Runtime markers:

```text
CESM sent live neutral packet 0 at hour 0.00000000
CESM sent live neutral packet 1 at hour 0.0833333358
SAMI3 received packet 0 on 32 workers
SAMI3 received packet 1 on 32 workers
Voltron sent direct phi frame 0 with final-valid cache
SAMI3 received WACCMX_PHI_RECV frame 0
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 1
```

All batch validators passed:

```text
validate_remix_sami3_phi_payload = overall=ok
validate_sami3_direct_phi_run_strict = overall=ok
validate_wxsami3_live_packet_contract = overall=ok
validate_wxsami3_source_flag_balance = overall=ok
validate_wxsami3_time_axis = overall=ok
validate_wxsami3_topblend_policy = overall=ok
validate_wxsami3_runtime_map = overall=ok
```

This closes the clean 2-packet coexistence gate.  The next target is production
cadence hardening: replace this forced `SAMI3_DT0=900.` / one-final-phi-frame
smoke with repeated neutral consumption and repeated Voltron/REMIX phi frames
without relying on the final-frame cache.

## 2026-05-25 11:32 CST Update

The next controlled 2-packet + 2-direct-phi cadence run was diagnostic rather
than successful:

```text
jobid = 7669625
jobname = wxsami3_p2p2
state = FAILED
exit = 16:0
elapsed = 00:05:51
node = qhcn660
archive = logs/waccmx_live_directmpi_2pkt_phi2_dt900_diag_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_2PHI_DIAGNOSTIC_20260525.md
```

Positive evidence:

```text
SAMI3 received WACCM-X packet 0 on 32 workers
SAMI3 received WACCM-X packet 1 on 32 workers
SAMI3 received direct phi frame 0 of 2
SAMI3 received direct phi frame 1 of 2
packet0 replay/QC max_rel = 4.83248e-13
packet1 replay/QC max_rel = 6.76502e-13
validate_remix_sami3_phi_payload = overall=ok
validate_wxsami3_time_axis_allow_incomplete = overall=ok
```

Failure mode:

```text
SAMI3 did not reach MASTER: All Done!
WACCM-X done and direct-phi done were not received before abort
SAMI3 printed Time step too small / vparallel diagnostics
PRTE reported MPI_ERRORS_ARE_FATAL
```

The run also exposed a sender metadata issue: `PHI_FRAME_HOUR_OFFSET` is
subtracted from Voltron runtime, not used as a frame interval.  With
`PHI_FRAME_HOUR_OFFSET=0.25`, the emitted frame hours were negative:

```text
frame0 hour = -0.248611107
frame1 hour = -0.247222215
```

Next implementation step: add an explicit diagnostic frame-hour override to the
Voltron sender, for example:

```text
WACCMX_SAMI3_PHI_FRAME_HOUR_BASE
WACCMX_SAMI3_PHI_FRAME_HOUR_STEP
```

so controlled cadence tests can emit `frame_hour = base + frame_index * step`
without changing the existing runtime-time based path.

## 2026-05-25 11:50 CST Update

The controlled 2-packet + 2-direct-phi cadence rerun now passes cleanly after
adding explicit Voltron direct-phi frame-hour base/step controls:

```text
jobid = 7669815
jobname = wxsami3_p2p2b
state = COMPLETED
exit = 0:0
elapsed = 00:07:42
node = qhcn005
archive = logs/waccmx_live_directmpi_2pkt_phi2_basestep_clean_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_2PHI_BASESTEP_CLEAN_RESULT_20260525.md
```

New direct-phi sender controls:

```text
WACCMX_SAMI3_PHI_FRAME_HOUR_BASE
WACCMX_SAMI3_PHI_FRAME_HOUR_STEP
frame_hour = base + frame_index * step
```

The successful run used:

```text
PHI_FRAME_HOUR_BASE = 0.0
PHI_FRAME_HOUR_STEP = 0.25
PHI_FRAME_HOUR_OFFSET = 0.0
PHI_MAX_FRAMES = 2
PHI_VALID_HOURS = 0.25
PHI_FINAL_VALID_UNTIL_HOUR = 1.0e30
MAX_PACKETS = 2
```

Key markers:

```text
WXSAMI3 sent live neutral packet 0 at hour 0.00000000
WXSAMI3 sent live neutral packet 1 at hour 0.0833333358
WACCMX_SAMI3_PHI_DIRECT sent frame 0 hour=0.0 valid_until=0.25
WACCMX_SAMI3_PHI_DIRECT sent frame 1 hour=0.25 valid_until=1.0e30
WACCMX_SAMI3_PHI_DIRECT sent done=2
MASTER: All Done!
WACCMX online done signal received: 2
SAMI3 direct phi done signal received: 2
```

All archived gates returned `overall=ok`:

```text
validate_remix_sami3_phi_payload
validate_sami3_direct_phi_run
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance_packet0
validate_wxsami3_source_flag_balance_packet1
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

Current grid contract for this branch:

```text
WACCM-X source grid = f19 = 144 x 96 = 13824 CAM columns
SAMI3 neutral payload header = nz=304, nf=124, nl=5, nneut=7
```

Validator hardening in this update:

```text
validate_sami3_direct_phi_run.py now accepts the live CESM marker:
  WXSAMI3 sent done signal to SAMI3

validate_wxsami3_source_flag_balance.py now only applies wxsami3_live_meta.json
numeric closure when the selected packet index matches the metadata packet.
This keeps packet0 line/count validation from being compared against packet1
metadata in multi-packet runs where the live meta file records the latest packet.
```

Next work should use this clean two-stream gate as the baseline for longer
production-cadence hardening: more than one SAMI3 dynamic step, repeated
Voltron/REMIX phi frames without final-frame cache dependence, and then the
f09/distributed neutral remap plus SAMI3 -> RAIJU/GAMERA physical weighting and
geometry mapping blockers.

## 2026-05-25 12:04 CST Update

The follow-on repeated-cadence diagnostic with smaller `SAMI3_DT0` was
intentionally cancelled after it exposed the next blocker:

```text
jobid = 7670003
jobname = wxsami3_p2p3d300
state = CANCELLED by user
batch exit = 0:15
elapsed = 00:09:07
node = qhcn005
archive = logs/waccmx_live_directmpi_2pkt_phi3_dt300_diag_20260525/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_2PKT_3PHI_DT300_DIAGNOSTIC_20260525.md
```

This run used:

```text
SAMI3_MAXSTEP = 2
SAMI3_DT0 = 300.
PHI_MAX_FRAMES = 3
PHI_FRAME_HOUR_STEP = 0.08333333333333333
PHI_VALID_HOURS = 0.08333333333333333
MAX_PACKETS = 2
```

Positive evidence:

```text
No Time step too small marker
No MPI_ERRORS_ARE_FATAL marker
Voltron sent phi frames at hours 0.0, 0.0833333358, 0.166666672
SAMI3 received all three WACCMX_PHI_RECV frames
SAMI3 reached MASTER: All Done!
validate_remix_sami3_phi_payload = overall=ok
validate_wxsami3_time_axis_allow_incomplete = overall=ok
```

Blocker:

```text
SAMI3 received only WACCM-X neutral packet 0:
  receiver packet count = 32 rows for packet 0, 0 rows for packet 1

Missing markers:
  WACCMX online done signal received
  SAMI3 direct phi done signal received
  WACCMX_SAMI3_PHI_DIRECT sent done
  WXSAMI3 sent done signal to SAMI3
  END OF MODEL RUN
```

Interpretation:

```text
DT0=300 removes the immediate SAMI3 numerical abort seen at DT0=900,
but SAMI3 can now outrun CESM/WACCM-X and finalize before the second live
neutral packet arrives.
```

Next implementation target: add a neutral-cadence synchronization policy rather
than tuning `DT0` further.  Candidate paths are a SAMI3 wait-at-coupling-boundary
mode, a CESM pre-send/startup gate, or a shared coupling clock that prevents
SAMI3 from advancing beyond the available WACCM-X packet stream.

## 2026-05-26 02:31 CST Update

The f19 WACCM-X/CAM live-neutral plus Voltron/REMIX direct-phi path now has a
validated six-cadence no-smoke result:

```text
jobid = 7678504
state = COMPLETED
exit = 0:0
elapsed = 00:25:56
node = qhcn657
archive = logs/waccmx_live_directmpi_nosmoke_dt300_6pkt_6phi_hrmax2_20260526/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_NOSMOKE_6PKT_6PHI_RESULT_20260526.md
```

Validated settings:

```text
SAMI3_MAXSTEP = 400
SAMI3_HRMAX = 2.000000
SAMI3_DT0 = 300.
MAX_PACKETS = 6
PHI_MAX_FRAMES = 6
CESM_STOP_N = 2100
```

All archived validators returned `overall=ok`, including the live packet
contract, source-flag balance, time-axis gate, top-blend policy, direct-phi
strict run validator, phi-payload validator, and runtime-map validator.

The key operational lesson is that the six-packet cadence depends on `HRMAX` as
well as `MAXSTEP`.  Attempts with `HRMAX=.700000` stopped too early even when
`MAXSTEP` was raised, because the effective `ntmmax` stayed too small for all
six five-minute packet/frame cadences.

Current goal-mode baseline:

```text
WACCM-X/CAM live phys_state(:) extraction: validated at f19 for six packets
SAMI3 online receiver and worker distribution: validated for six packets
Voltron/REMIX direct-MPI phi producer: validated for six changing frames
Done/finalize path: validated
```

Next target is to return to the SAMI3 -> Voltron/RAIJU/GAMERA adapter line and
continue from the existing `Pavg/Davg/Pstd/Dstd/tiote` interface, using the
domain-aware Voltron/RAIJU mapping and blending controls already established.

## 2026-05-26 04:11 CST Update

Returned to the SAMI3 -> Voltron/RAIJU/GAMERA scalar-moment adapter line and
validated the latest schema v7 `exclude_above_target_lmax` product for 1800s
runtime use:

```text
jobid = 7678667
state = COMPLETED
exit = 0:0
elapsed = 01:22:42
node = qhcn176
run_dir = /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_tiote_long1800_20260526
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_EXCLUDE_LMAX_DENSITY_TIOTE_LONG1800_RESULT_20260526.md
```

Validated cases:

```text
long1800_exclude_lmax_dens005:
  alphaDavg=0.05, alphaTiote=0.0

long1800_exclude_lmax_dens005_tiote:
  alphaDavg=0.05, alphaTiote=1.0
  moments/useStateTioteForIngest=T
```

Both cases reached `Fin`, wrote 362 RAIJU frames, passed longrun/summary/mapping
validators, and had exact `Pavg/Davg/Pstd/Dstd` formula checks with no
non-finite checked restart physics fields.  The tiote hook validator passed
with runtime alphas `[0.0, 0.05, 0.0, 0.0, 1.0]` and 8100 valid mask cells.

This closes the current runtime-adapter validation target for the conservative
exclude-Lmax product.  It remains prototype physics because the source-domain
L scan still shows nearly all positive active Voltron bVol outside the current
RAIJU target L range.  The next physics decision is target-domain extension
versus a different source subset versus keeping this path diagnostic-only.

## 2026-05-26 07:10 CST Update

Returned to the WACCM-X/SAMI3 online-control side and extended the validated f19
direct-MPI no-smoke cadence from 6 neutral/phi packets to 12:

```text
jobid = 7680171
state = COMPLETED
exit = 0:0
elapsed = 00:48:27
node = qhcn343
run_dir = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_12pkt_12phi_hrmax4_maxstep1400_20260526_0000
archive = logs/waccmx_live_directmpi_nosmoke_dt300_12pkt_12phi_hrmax4_20260526/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_NOSMOKE_12PKT_12PHI_RESULT_20260526.md
```

Validated settings:

```text
SAMI3_MAXSTEP = 1400
SAMI3_HRMAX = 4.000000
SAMI3_DT0 = 300.
MAX_PACKETS = 12
PHI_MAX_FRAMES = 12
CESM_STOP_N = 3900
```

All archived validators returned `overall=ok`.  The run consumed all 12 CAM
live-neutral packets and all 12 REMIX/Voltron direct-phi frames, with SAMI3
receiver packet hours from `0.0` through `0.916666687` h.  Replay/QC compare
files exist for all 12 packets; the worst archived relative mismatch is
`1.12911e-12`, far below the `1e-6` gate.

The previous diagnostic attempt (`jobid=7680009`) with
`SAMI3_MAXSTEP=800, SAMI3_HRMAX=3.0` consumed only 10/12 direct-phi frames
before `MASTER: All Done!`; the successful setting fixes that by raising both
the step and hour limits.

Current goal-mode baseline:

```text
WACCM-X/CAM live phys_state(:) extraction: validated at f19 for 12 packets
SAMI3 online receiver and worker distribution: validated for 12 packets
Voltron/REMIX direct-MPI phi producer: validated for 12 changing frames
Top-blend/source-flag/time-axis gates: validated
Done/finalize path: validated
```

Next target is again the SAMI3 -> Voltron/RAIJU/GAMERA adapter line.  The
remaining blocker is not the WACCM-X/SAMI3 control path; it is the physical
source-domain policy for SAMI3-derived scalar moments before they can be
treated as production RAIJU/GAMERA feedback.

## 2026-05-26 07:28 CST Update

Added a production-contract guardrail for the SAMI3 -> RAIJU exclude-Lmax
product:

```text
script = scripts/validate_sami3_raiju_production_contract.py
diagnostic_contract = logs/sami3_exclude_lmax_density_tiote_long1800_20260526/validate_sami3_raiju_production_contract_diagnostic.txt
production_readiness = logs/sami3_exclude_lmax_density_tiote_long1800_20260526/validate_sami3_raiju_production_contract_production.txt
```

The diagnostic-contract mode passes and classifies the product as
`diagnostic_only`:

```text
source_domain_policy = exclude_above_target_lmax
source_domain_skipped_above_lmax_fraction = 0.999595965103914
overall = ok
```

The production-readiness mode intentionally fails:

```text
FAIL production_source_domain_skip_threshold: fraction=0.999595965103914 max=0.05
FAIL production_label: product=unknown weight=prototype
classification = diagnostic_only
overall = FAIL
```

This turns the current physics caveat into an executable gate.  The adapter can
continue to be used for runtime diagnostics and controlled alpha/blending tests,
but it cannot be accidentally promoted to production plasma feedback without
passing a source-domain closure policy.

## 2026-05-26 07:45 CST Update

Added a target-admissible source-subset analyzer:

```text
script = scripts/analyze_sami3_raiju_target_admissible_subset.py
archive = logs/sami3_raiju_target_admissible_subset_20260526/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_TARGET_ADMISSIBLE_SUBSET_20260526.md
```

Result for the current schema v7 exclude-Lmax audit:

```text
target_L_edge_min = 1.4902905965657023
target_L_edge_max = 33.163437477526358
positive_source_bvol_sum = 2268463.9951948188

target_admissible_lrange count = 15040
target_admissible_lrange bvol_sum = 915.9958388485247
target_admissible_lrange fraction_of_total_positive_bvol = 0.0004037956259340399
target_admissible_lrange status = 100% used

above_target_lrange bvol_sum = 2267547.4565805197
above_target_lrange fraction_of_total_positive_bvol = 0.9995959651040349
```

Interpretation: the current target-admissible subset is geometrically clean, but
it is not representative of the active Voltron source volume.  This strengthens
the diagnostic-only decision: another runtime smoke cannot turn this into
production plasma feedback; the next real decision is source-domain physics.

## 2026-05-26 10:55 CST Update

Connected the target-admissible subset diagnostic to the executable production
contract:

```text
script = scripts/validate_sami3_raiju_production_contract.py
new_archive = logs/sami3_raiju_production_contract_target_subset_20260526/
doc = docs/MAGE1.25_notes/SAMI3_RAIJU_PRODUCTION_CONTRACT_TARGET_SUBSET_20260526.md
```

New validator options:

```text
--target-admissible-json
--require-target-admissible-json
--min-production-target-admissible-bvol-fraction 0.05
```

The current schema v7 exclude-Lmax product still passes diagnostic-contract
mode:

```text
target_admissible_bvol_fraction = 0.0004037956259340399
low_target_admissible_fraction_is_not_labeled_production = ok
classification = diagnostic_only
overall = ok
```

Production-readiness now has a third explicit failure:

```text
FAIL production_source_domain_skip_threshold: fraction=0.999595965103914 max=0.05
FAIL production_label: product=unknown weight=prototype
FAIL production_target_admissible_bvol_fraction: fraction=0.0004037956259340399 min=0.05
classification = diagnostic_only
overall = FAIL
```

This makes the current physics blocker harder to miss: the product is
runtime-valid and target-domain-clean, but the target-admissible source subset is
too small to represent production plasma feedback.

## 2026-05-26 11:12 CST Update

Prepared the WACCM-X/SAMI3 direct-MPI launcher for cadence runs longer than the
current 12pkt/12phi baseline:

```text
script = slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525.sbatch
new env = WXSAMI3_DIRECTMPI_COMPONENT_TIMEOUT_SECONDS
default = 2400
```

The previous launcher hard-coded `timeout 2400s` around the SAMI3 and CESM
`prun` commands.  That was adequate for the 12pkt/12phi run because the
component runtime was still under the 40 minute component timeout, even though
the whole Slurm job elapsed 48:27 including setup and validation.  A 24pkt/24phi
run should not inherit that hard limit, so the component timeout is now
configurable while preserving the old default.

Planned long-cadence submission settings:

```text
MAX_PACKETS = 24
PHI_MAX_FRAMES = 24
SAMI3_DT0 = 300.
SAMI3_HRMAX = 8.000000
SAMI3_MAXSTEP = 2800
CESM_STOP_N = 7500
COMPONENT_TIMEOUT_SECONDS = 7200
VOLTRON_TIMEOUT_SECONDS = 7200
```

Added a dedicated direct-MPI archive driver for this run family:

```text
script = scripts/archive_wxsami3_directmpi_result.py
validators =
  validate_sami3_direct_phi_run.py
  validate_remix_sami3_phi_payload.py
  validate_wxsami3_live_packet_contract.py
  validate_wxsami3_source_flag_balance.py
  validate_wxsami3_time_axis.py
  validate_wxsami3_topblend_policy.py
  validate_wxsami3_runtime_map.py
```

This removes the need to adapt the append2 archiver for direct-MPI runs after a
long cadence job finishes.

## 2026-05-26 12:15 CST Update

Completed and archived the planned f19 WACCM-X/SAMI3 direct-MPI no-smoke
24-cadence run:

```text
jobid = 7697673
jobname = wxsami3_24p24f_h8
state = COMPLETED
exit = 0:0
elapsed = 01:08:04
node = qhcn198
batch MaxRSS = 65297928K
run_dir = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_24pkt_24phi_hrmax8_maxstep2800_20260526_0000
archive = logs/waccmx_live_directmpi_nosmoke_dt300_24pkt_24phi_hrmax8_20260526/
doc = docs/MAGE1.25_notes/WACCMX_SAMI3_LIVE_DIRECTMPI_NOSMOKE_24PKT_24PHI_RESULT_20260526.md
```

Validated settings:

```text
MAX_PACKETS = 24
LIVE_DUMP_MAX = 24
PHI_MAX_FRAMES = 24
SAMI3_DT0 = 300.
SAMI3_HRMAX = 8.000000
SAMI3_MAXSTEP = 2800
CESM_STOP_N = 7500
COMPONENT_TIMEOUT_SECONDS = 7200
VOLTRON_TIMEOUT_SECONDS = 7200
```

All seven archived validators returned `overall=ok`:

```text
validate_sami3_direct_phi_run_strict
validate_remix_sami3_phi_payload
validate_wxsami3_live_packet_contract
validate_wxsami3_source_flag_balance
validate_wxsami3_time_axis
validate_wxsami3_topblend_policy
validate_wxsami3_runtime_map
```

The run consumed all 24 CAM `phys_state(:)` live neutral packets and all 24
changing REMIX/Voltron direct-phi frames.  The time-axis validator confirmed
24 sender packets, 24 receiver packets, 32-worker SAMI3 coverage for every
packet, 24 phi payload frames, 24 receiver phi records, and full phi coverage
for the neutral packet hours `0.0` through `1.91666663` h.  The last replay/QC
comparison remained roundoff-level:

```text
packet23_recv_compare_max_rel = 1.20189e-12
limit = 1e-6
```

The f19 runtime-map/top-blend gates stayed consistent:

```text
nsource = 13824
npoints = 3618816
weights_dim_n_s = 14475264
topblend_mode = linear
bottom_km = 600
top_km = 720
unknown_source_flags = 0
he_native_matches_valid = true
w_zero_matches_valid = true
```

Run-management caveat: the model chain had already reached the direct-phi done
marker, SAMI3 `MASTER: All Done!`, and CESM `END OF MODEL RUN`, but Voltron
remained inside the `timeout 7200s prun ... ./voltron.x` wrapper because
`PHI_STOP_AFTER_DONE=0`.  After the done markers were verified, only the
Voltron wrapper was terminated.  The launcher accepted this as:

```text
INFO: accepting Voltron nonzero exit after direct phi done and SAMI3 completion: status=143
```

This is not a failed physics/control-chain result; it is a post-done launcher
management issue for long cadence runs.  Future runs should use a shorter
post-done Voltron timeout, validate `PHI_STOP_AFTER_DONE=1`, or add explicit
post-done wrapper termination.

The archive driver and live packet validator were also hardened for this
completed-run workflow:

```text
script = scripts/validate_wxsami3_live_packet_contract.py
new option = --exclude-slurm-logs
script = scripts/archive_wxsami3_directmpi_result.py
behavior = re-run live packet contract without Slurm summary logs and copy
           original run validators into archive/run_validators/
```

Reason: after Slurm prints validator excerpts into `slurm-*.out`, post-run
revalidation can otherwise double-count sender packets or match validator text
as fatal markers.  With `--exclude-slurm-logs`, the 24-packet live packet
contract revalidates cleanly:

```text
sender_live_packet_count = 24
receiver_qc_line_count = 768
sami3_done = true
waccmx_done = true
fatal_markers_absent = true
overall = ok
```

Current goal-mode baseline:

```text
WACCM-X/CAM live phys_state(:) extraction: validated at f19 for 24 packets
SAMI3 online receiver and worker distribution: validated for 24 packets
Voltron/REMIX direct-MPI phi producer: validated for 24 changing frames
Top-blend/source-flag/time-axis/runtime-map gates: validated
Done/finalize path: validated, with Voltron post-done wrapper caveat
```

Next target returns to the SAMI3 -> Voltron/RAIJU/GAMERA adapter line.  The
WACCM-X/SAMI3 online control path now has a stronger f19 24-cadence baseline;
the main remaining physics blocker is still the SAMI3 scalar-moment
source-domain policy before any production RAIJU/GAMERA plasma feedback claim.
