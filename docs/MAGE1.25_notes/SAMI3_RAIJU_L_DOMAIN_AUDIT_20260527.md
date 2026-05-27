# SAMI3 -> RAIJU L-Domain Audit, 2026-05-27

## Trigger

The previous production-readiness notes treated Voltron/SAMI3 source cells with
`Lb_cc` up to about 554 as a source-domain coverage problem.  That wording is
not defensible as "SAMI3 covers L~500".  Published SAMI3 domain descriptions are
in the 70/85 km to about 20,000 km altitude range, and some papers summarize
the field-line domain as order-10 Earth radii rather than hundreds of Earth
radii.  The local `L=(r/Re)/cos(blat)^2` and Voltron `TubeShell/Lb` values can
become very large near high magnetic latitude and must not be interpreted as
radial model extent.

Reference checks used for this audit:

- NASA CCMC SAMI3 model page: altitude range 85 km to 20,000 km.
- SAMI3/WACCM-X literature example: altitude range 85 km to about 8 Re and
  magnetic latitudes up to roughly +/-88 degrees.

## Scan Scope

The scan covered:

- `code/kaiju_sami3_moments/scripts/sami3_moments/*.py`
- `code/kaiju_sami3_moments/src/**`
- `code/sami3_receiver/**`
- top-level validation/audit scripts in `scripts/`
- archived logs and notes under `logs/` and `docs/MAGE1.25_notes/`
- the active copied working tree at
  `/online1/jiaoy_group/jiaoy/MAGE1.25/kaiju_sami3_voltron_moments_20260523`

## Findings

### A. Runtime weight generation is affected

`sami3_moments_to_raiju_diag.py` defines the direct SAMI3 L source coordinate as:

```text
L = (baltu / Re) / cos(blatu)^2
```

Key sites:

- `code/kaiju_sami3_moments/scripts/sami3_moments/sami3_moments_to_raiju_diag.py:300`
- `code/kaiju_sami3_moments/scripts/sami3_moments/sami3_moments_to_raiju_diag.py:317`
- `code/kaiju_sami3_moments/scripts/sami3_moments/sami3_moments_to_raiju_diag.py:318`
- `code/kaiju_sami3_moments/scripts/sami3_moments/sami3_moments_to_raiju_diag.py:1043`

`build_sami3_to_raiju_weights.py` imports and reuses this coordinate for every
weight-file build, including the Voltron TubeShell pathway:

- `build_sami3_to_raiju_weights.py:28`
- `build_sami3_to_raiju_weights.py:1343`
- `build_sami3_to_raiju_weights.py:1370`

This means the generated sparse weight files for `l_mlt_separable`,
`voltron_shell_l_mlt`, and `voltron_tubeshell_l_mlt` all inherit the same
high-latitude L-coordinate risk.  These products should remain diagnostic-only
until the source-domain coordinate is replaced or gated by a physical SAMI3
extent mask.

### B. Voltron -> RAIJU source-domain gating is affected

The Voltron-to-RAIJU bVol overlap path reads `/TubeShell/Lb`, centers it as
`Lb_cc`, and compares that directly to the RAIJU target `L_edge` range:

- `build_sami3_to_raiju_weights.py:986`
- `build_sami3_to_raiju_weights.py:999`
- `build_sami3_to_raiju_weights.py:1059`
- `build_sami3_to_raiju_weights.py:1084`
- `build_sami3_to_raiju_weights.py:658`
- `build_sami3_to_raiju_weights.py:710`

The policy `exclude_above_target_lmax` is therefore a Voltron/RAIJU diagnostic
filter on `Lb_cc`, not proof that SAMI3 physically spans or fails to span those
L shells.

### C. Validators and audit scripts inherit the same assumption

These scripts default to `Lb_cc` or to the generated target-admissible subset as
their source-domain denominator:

- `scripts/classify_sami3_raiju_target_domain.py:156`
- `scripts/analyze_sami3_raiju_source_l_coverage.py:262`
- `scripts/analyze_sami3_raiju_target_admissible_subset.py`
- `scripts/analyze_sami3_raiju_source_domain_lscan.py:229`
- `scripts/validate_sami3_raiju_target_closure.py:202`
- `scripts/validate_sami3_raiju_production_contract.py:116`

The resulting `source_domain_skipped_above_lmax_fraction`,
`target_admissible_bvol_fraction`, and related production gates are useful as
diagnostics of the current mapping product, but they should not be treated as a
physical SAMI3 coverage metric.

### D. Documentation and archived logs contain stale wording

Several existing notes and JSON logs repeat the old interpretation or the raw
`source_l_formula`:

- `docs/MAGE1.25_notes/SAMI3_RAIJU_SOURCE_DOMAIN_LSCAN_20260526.md`
- `docs/MAGE1.25_notes/SAMI3_RAIJU_TARGET_ADMISSIBLE_SUBSET_20260526.md`
- `docs/MAGE1.25_notes/SAMI3_RAIJU_PRODUCTION_CONTRACT_TARGET_SUBSET_20260526.md`
- `docs/MAGE1.25_notes/SAMI3_RAIJU_SOURCE_DOMAIN_POLICY_EXCLUDE_LMAX_20260526.md`
- `docs/MAGE1.25_notes/GOAL_MODE_COUPLING_STATUS_20260525.md`
- archived JSONs under `logs/sami3_*`

These should be considered historical diagnostic artifacts, not current physical
claims.

### E. Paths not affected by this specific L-domain bug

The following code paths did not show this L-domain method:

- WACCM-X -> SAMI3 neutral receiver/sender code under `code/sami3_receiver/`
  and `code/cesm_source_mods/`
- REMIX/Voltron -> SAMI3 phi sender path under
  `code/kaiju_sami3_moments/src/remix/waccmx_stub_backend.F90`
- runtime RAIJU ingestion/blending code under
  `code/kaiju_sami3_moments/src/voltron/modelInterfaces/raijuCplHelper.F90`

The runtime hook consumes masks and moments from the prepared HDF5 file.  It
does not compute or reinterpret SAMI3 L.  Therefore the bad assumption enters
before runtime, during offline sparse-weight generation and validation.

## Corrected Interpretation

The current SAMI3 -> Voltron/RAIJU path is still a diagnostic adapter.  The
problem is not "SAMI3 reaches L~500"; the problem is that the adapter used a
dipole-like high-latitude L label and Voltron `Lb_cc` as if they were a physical
source-domain coverage denominator.

## Required Fix Before Production

1. Add a SAMI3 grid-extent audit that reports altitude/radius, magnetic latitude,
   dipole-like L, and active/usable source masks separately.
2. Replace production-domain gating with an explicit physical SAMI3 source mask,
   for example altitude/radius and closed-field/target-admissible flags.
3. Keep `L=(baltu/Re)/cos(blatu)^2` and `TubeShell/Lb` available only as
   diagnostic coordinates unless the run explicitly opts into them.
4. Mark existing `l_mlt`, `voltron_shell_l_mlt`, and `voltron_tubeshell_l_mlt`
   products as `diagnostic_only` unless a physical source-domain mask is present.
5. Update the stale notes so future plans do not repeat the `L500` interpretation.

## Immediate Code Fix, 2026-05-27

The sparse-weight generator now defaults to an explicit overlap gate:

```text
--sami3-overlap-max-l 16.0
--allow-l-extrapolation is off by default
```

This does not claim that SAMI3 physically extends to 16 Re.  It is a conservative
overlap cutoff for the current dipole-like diagnostic L coordinate.  Source
queries above the accepted SAMI3 overlap range now produce zero sparse coverage
instead of being clamped to the nearest SAMI3 shell.  Runtime products generated
from weight files now default to:

```text
--runtime-mask-policy auto
auto -> coverage_closed_no_extrap for --mapping-mode weights
```

The intended runtime behavior is therefore:

```text
overlap target cells: receive SAMI3-derived scalar moments
non-overlap target cells: masks are zero, so RAIJU/MAGE baseline values are kept
```

New weight files are labeled:

```text
physical_validity = diagnostic_overlap_only_prototype
```

That label is deliberate.  The current fix removes the obvious L500 failure
mode, but it is still not a traced production flux-tube mapping.

## Active-Grid Fix, 2026-05-27

The RAIJU target-grid reader now keeps the runtime HDF5 shape, including ghost
cells, but builds an explicit active-cell mask from the ShellGrid ghost-count
metadata:

```text
nGhosts_n, nGhosts_s, nGhosts_w, nGhosts_e
```

The output weight file now writes:

```text
/dst/active_mask
/dst/active_i_mask
/dst/active_j_mask
/dst/L_active
/dst/L_edge_active
/quality/target_active_mask
```

Sparse weights are generated only where `/dst/active_mask == 1`.  Ghost cells
retain zero sparse coverage, so the runtime mask leaves the original RAIJU/MAGE
baseline values untouched there.  This preserves compatibility with
ghost-inclusive RAIJU restart/coupler arrays while preventing the adapter from
treating ghost cells as physical target bins.

For the current RAIJU configuration, the active poleward boundary should be read
from `ThetaL = 15 deg`, corresponding to:

```text
L_active_outer_edge = 1 / sin(15 deg)^2 = 14.928...
```

The previously reported `L_edge_max = 33.16` is a ghost-inclusive diagnostic
edge from approximately `theta = 10 deg`; it is not the official or active RAIJU
outer boundary.
