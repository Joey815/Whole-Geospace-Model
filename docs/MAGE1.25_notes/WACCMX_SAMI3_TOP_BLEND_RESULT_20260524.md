# WACCM-X -> SAMI3 Top-Blend Prototype Result

Date: 2026-05-24

## Goal

Move the WACCM-X top treatment from an implicit hard fallback toward an
explicit, logged transition policy:

```text
below blend_bottom_km: use valid WACCM-X payload
between blend_bottom_km and blend_top_km: linear WACCM-X/native blend
above blend_top_km or invalid/above_top payload: retain SAMI3 native MSIS/HWM
```

This is still a prototype control/physics guardrail, not a final production
neutral-forcing policy.

## Code Changes

Receiver-side blending was added in:

```text
code/sami3_receiver/waccmx_neutral_mod.f90
```

Runtime controls:

```text
WXSAMI3_TOP_BLEND_MODE=none|linear
WXSAMI3_BLEND_BOTTOM_KM=<km>
WXSAMI3_BLEND_TOP_KM=<km>
```

Default behavior is unchanged:

```text
WXSAMI3_TOP_BLEND_MODE unset -> no blending;
valid WACCM-X cells overwrite native SAMI3, invalid cells retain native SAMI3.
```

For `linear`, the receiver computes the WACCM-X fraction from SAMI3 `alts`:

```text
alpha = 1                         z <= blend_bottom_km
alpha = 0                         z >= blend_top_km
alpha = (blend_top_km-z)/(top-bottom) otherwise
X = alpha * X_WACCMX + (1-alpha) * X_SAMI3_native
```

The receiver still retains native SAMI3 He.  Source-flag invalid/above-top
cells are not blended; they remain native.

The active SAMI3 Makefile was also reordered so a clean build creates
`grid_mod.mod` before compiling `waccmx_neutral_mod.f90`.

## Validation Run

Launcher:

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_multipacket_topblend_20260524.sbatch
```

Run:

```text
job_id=7645541
run_dir=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_multipacket_topblend_20260524_0000
TOP_BLEND_MODE=linear
BLEND_BOTTOM_KM=600
BLEND_TOP_KM=720
```

Result:

```text
7645541 COMPLETED 0:0 elapsed=00:03:29
SAMI3: MASTER: All Done!
CESM/CAM: END OF MODEL RUN
```

Replay-vs-receiver checks:

```text
packet0: WACCMX_RECV_QC compare ok, max_rel=4.83248e-13
packet1: WACCMX_RECV_QC compare ok, max_rel=6.76502e-13
```

Blend diagnostics:

```text
WACCMX_APPLY_BLEND lines: 320
blend_i_total: 2601
blend_f_total: 2601
nonzero blend lines: 178
max blend cells in one apply line: 36
```

Source-flag totals across the run:

```text
source_valid_total: 8423223
source_above_top_total: 3283378
source_n2_invalid_total: 356119
source_other_invalid_total: 0
source_unknown_total: 0
```

Archived logs:

```text
logs/topblend_20260524/
```

## Interpretation

The receiver can now distinguish:

```text
valid WACCM-X overwrite
valid WACCM-X/native transition blend
invalid or above-top native fallback
```

This closes the immediate engineering gap that the WACCM-X top fallback was
only implicit.  The chosen 600-720 km transition is a validation setting tied
to the current f19 live run, where WACCM-X `ZM` tops out near 720-722 km.

## Remaining Issues

The top transition is implemented and validated as a runtime mechanism, but
the production policy still needs physics review:

```text
choose blend_bottom/top from WACCM-X valid vertical coverage and SAMI3 geometry
decide whether each variable should share one alpha or have variable-specific policy
keep W disabled until vertical-wind semantics are validated
keep He native until WACCM-X He availability and units are validated
```

Next priority remains:

```text
REMIX -> SAMI3 potential/E-field forcing
SAMI3 -> RAIJU/GAMERA flux-tube-volume weighting
SAMI3 -> RAIJU/GAMERA L/MLT geometry mapping
```
