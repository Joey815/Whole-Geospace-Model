# SAMI3 / Voltron Trace-Line Debug Export

Date: 2026-05-25 CST

## Purpose

The current SAMI3 -> Voltron/RAIJU/GAMERA mapping still fails the
target-domain closure gate.  The no-span diagnostic showed that the blocker is
not only the conservative overlap threshold: most valid active Voltron tube
volume still lands outside the current RAIJU target domain.

This update adds a default-off Voltron diagnostic export for traced field-line
geometry.  It is intended to expose the data needed for the next geometry
iteration:

```text
source tube id
s index
xyz(s)
B(s)
dl / B edge weights
active-domain edge flag
```

The diagnostic does not change the production tube data model and does not add
new fields to `Tube_T`.

## Code Patch

```text
patch = code/kaiju_sami3_moments/patches/voltron_trace_debug_export_20260525.patch
source = src/voltron/voltCplHelper.F90
```

The export is controlled by environment variables:

```text
VOLTRON_TRACE_DEBUG_FILE       # HDF5 output path; unset/NONE disables export
VOLTRON_TRACE_DEBUG_MAX_TUBES  # optional sample count, default 16, clamped 1..256
VOLTRON_TRACE_DEBUG_SOURCE_I   # optional single Voltron TubeShell i index
VOLTRON_TRACE_DEBUG_SOURCE_J   # optional single Voltron TubeShell j index
```

When enabled, `genVoltTubes` writes `/TraceLineDebug` after `tubes2Shell`.
Current behavior overwrites the same group on each `genVoltTubes` call, so the
HDF5 file represents the final exported update in the smoke run.  This is
acceptable for the current geometry debug gate, but it is not a time-series
export format.

## Runtime Smoke

```text
archive = logs/sami3_trace_debug_export_smoke_20260525/
jobid = 7677855
state = COMPLETED
exit = 0:0
elapsed = 00:01:00
node = qhcn349
batch MaxRSS = 1040740K
run_complete = 1
```

The first harness attempt, job `7677854`, failed before reaching the diagnostic
because the run directory did not yet contain the required input symlinks.  The
rerun above used the fixed harness.

Runtime marker:

```text
VOLTRON_TRACE_DEBUG wrote 8 traces to .../sami3_trace_debug_smoke.traceDebug.h5
```

This marker appears three times because `genVoltTubes` was called three times
during the smoke and the diagnostic group was rewritten each time.

## HDF5 Output

```text
file = logs/sami3_trace_debug_export_smoke_20260525/sami3_trace_debug_smoke.traceDebug.h5
size = 10254208 bytes
group = /TraceLineDebug
trace_count = 8
max_nodes = 10001
max_edges = 10000
summary = logs/sami3_trace_debug_export_smoke_20260525/trace_debug_smoke_summary_20260525.txt
```

Datasets as viewed by `h5py`:

```text
Bxyz_node            shape=[3, 8, 10001]
xyz_node             shape=[3, 8, 10001]
ijk_node             shape=[3, 8, 10001]
magB_node            shape=[8, 10001]
node_s_index         shape=[8, 10001]
dl_over_B_edge       shape=[8, 10000]
active_edge_mask     shape=[8, 10000]
edge_left_s_index    shape=[8, 10000]
edge_right_s_index   shape=[8, 10000]
node_count           shape=[8]
edge_count           shape=[8]
source_i             shape=[8]
source_j             shape=[8]
source_topo          shape=[8]
source_Nm            shape=[8]
source_Np            shape=[8]
```

The existing Kaiju HDF5 IO layer reverses Fortran array dimension order as
viewed by `h5py`; for example Fortran `(maxNodes,maxTubes,NDIM)` appears as
`[3, 8, 10001]`.

All checked datasets are finite:

```text
Bxyz_node finite = 240024 / 240024
xyz_node finite = 240024 / 240024
ijk_node finite = 240024 / 240024
magB_node finite = 80008 / 80008
dl_over_B_edge finite = 80000 / 80000
active_edge_mask finite = 80000 / 80000
NaN count = 0
Inf count = 0
```

Per-trace active edge coverage in this smoke sample is 100%:

```text
trace 0 src=(1,1) topo=1 nodes=361 edges=360 active=360
trace 1 src=(2,1) topo=1 nodes=534 edges=533 active=533
trace 2 src=(3,1) topo=2 nodes=895 edges=894 active=894
trace 3 src=(4,1) topo=2 nodes=863 edges=862 active=862
trace 4 src=(5,1) topo=2 nodes=836 edges=835 active=835
trace 5 src=(6,1) topo=2 nodes=719 edges=718 active=718
trace 6 src=(7,1) topo=2 nodes=603 edges=602 active=602
trace 7 src=(8,1) topo=2 nodes=583 edges=582 active=582
```

This confirms the diagnostic path works, but it does not yet sample the
closure-failing source cells.  The next geometry step should add source-cell
selection/filtering so the export can target the source cells that the
target-domain closure validator marks as outside-target or large-footprint.

## Targeted Closure-Failure Smoke

The export now supports optional `source_i/source_j` filtering.  A targeted
smoke was run against the largest active-bVol outside-target source cell from
the no-span closure audit:

```text
archive = logs/sami3_trace_debug_target_i005_j095_20260525/
jobid = 7677907
state = COMPLETED
exit = 0:0
elapsed = 00:01:10
node = qhcn203
batch MaxRSS = 1042088K
VOLTRON_TRACE_DEBUG_SOURCE_I = 5
VOLTRON_TRACE_DEBUG_SOURCE_J = 95
```

No-span closure-audit context for this source cell:

```text
status = outside_target
source_i = 5
source_j = 95
bvol_active = 14539.834
Lb_cc = 450.228
lon0 = 181 deg
mapped_fraction = 0
term_count = 0
```

Targeted trace output:

```text
file = logs/sami3_trace_debug_target_i005_j095_20260525/sami3_trace_debug_target_i005_j095.traceDebug.h5
trace_count = 1
source = (i=5, j=95)
topo = 2
Nm = 834
Np = 0
node_count = 835
edge_count = 834
active_edge_count = 834
active_edge_fraction = 1.0
dl_over_B_sum_all = 3496.88043
dl_over_B_sum_active = 3496.88043
magB_min = 0.0312174951
magB_max = 209029.915
R_min = 1.01911227
R_max = 190.349119
```

Interpretation:

```text
The targeted hook can now capture a specific closure-failing Voltron TubeShell
source cell.  This particular outside-target cell traces to a very extended
line with Rmax about 190 Rp and zero mapped RAIJU terms in the current
overlap product.  The next step is to compare the exported trace-edge
quadrature against the active-bVol ledger and decide whether the target-domain
failure is caused by target L-range limits, line-end topology, or how the
TubeShell corner geometry is being collapsed into the overlap bins.
```

## Target-Domain L-Range Classification

The targeted trace was compared against the no-span closure audit and RAIJU
target grid:

```text
trace_vs_audit = logs/sami3_trace_debug_target_i005_j095_20260525/trace_debug_target_i005_j095_vs_audit_20260525.txt
lrange_classification = logs/sami3_trace_debug_target_i005_j095_20260525/trace_debug_outside_target_lrange_classification_20260525.txt
```

For source `(i=5,j=95)`:

```text
source Lb_cc = 450.2276916503906
target L_edge_max = 33.16343747752636
source_Lb_over_target_L_edge_max = 13.576026066522608
trace_Rmax_over_target_L_edge_max = 5.739728252832102
bvol_active / trace_dlB_active = 4.157944278661308
```

The `bvol_active / trace_dlB_active` ratio is diagnostic only; `bVolActive`
contains shell-cell geometry scaling and is not expected to equal the simple
trace-edge `sum(dl/B)`.

Global classification using the no-span closure-audit status codes and
positive `bvol_active_cc`:

```text
target_L_edge_min = 1.4902905965657023
target_L_edge_max = 33.16343747752636

positive_all active_bvol_sum = 2268464.0
positive_all above_target_Lmax_bvol_sum = 2267547.5
positive_all above_target_Lmax_bvol_fraction = 0.9995959997177124
positive_all inside_target_Lrange_bvol_sum = 915.995849609375
positive_all inside_target_Lrange_bvol_fraction = 0.0004037956241518259

outside_target active_bvol_sum = 2013959.0
outside_target above_target_Lmax_bvol_fraction = 0.9999998211860657
```

Important nuance:

```text
Some high-L source cells are marked used because their huge footprint clips a
small part of the RAIJU target L domain.  The target-domain failure is still
dominated by source tube volume far outside the RAIJU target L range; tuning
the overlap threshold cannot make that volume physically close inside a
target grid whose outer L edge is about 33.16.
```

## Validation Commands

Serial Voltron build:

```text
build_dir = /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523
target = voltron.x
result = [100%] Built target voltron.x
```

OpenMPI Voltron helper build:

```text
build_dir = /home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_phi_direct_openmpi_20260525
target = voltron_mpi.x
result = [100%] Built target voltron_mpi.x
```

Patch reversibility gate:

```text
git apply --check --reverse code/kaiju_sami3_moments/patches/voltron_trace_debug_export_20260525.patch
```

## Next Work Order

Use this diagnostic to close the geometry blocker:

```text
1. Decide the physical policy for source volume with `Lb` outside the RAIJU
   target L range: exclude, project/clamp only for diagnostics, or extend the
   target domain.
2. Rebuild the SAMI3 -> Voltron -> RAIJU sparse product from trace edges only
   for physically admissible target-domain volume.
3. Keep the target-domain closure validator as the acceptance gate.
```
