# SAMI3 -> RAIJU Exclude-Lmax Runtime Smoke

Date: 2026-05-26 CST

## Purpose

The schema v7 `exclude_above_target_lmax` weight and stage-2 product already
passed offline mapping and closure gates.  This checkpoint verifies that the
generated `/RaiCplMomentsOnly` product can still be ingested by the RAIJU
runtime hook without changing default behavior unexpectedly.

The runtime smoke covers two short cases:

```text
alpha=0 baseline recovery:
  alphaPavg=0
  alphaDavg=0
  alphaPstd=0
  alphaDstd=0
  alphaTiote=0

density-only response:
  alphaPavg=0
  alphaDavg=0.05
  alphaPstd=0
  alphaDstd=0
  alphaTiote=0
```

## Archive

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_smoke_20260526
```

Collaboration archive:

```text
logs/sami3_exclude_lmax_runtime_smoke_20260526/
```

The archive contains the Slurm launcher, four XML files, Voltron logs, Slurm
stdout, and summary/validator JSON/TXT outputs.  Large runtime HDF5 outputs are
kept in the active analysis directory and are not committed to the collaboration
repository.

## Job Result

Submitted job:

```text
jobid = 7678065
jobname = sami3_exlmax_smk
node = qhcn067
state = COMPLETED
exit = 0:0
elapsed = 00:04:10
batch MaxRSS = 1033140K
```

The job ran four cases sequentially:

```text
tinyCase_base_control_exclude_lmax_alpha0_smoke.xml
tinyCase_sami3_moments_dsB_lmlt_recommended_exclude_lmax_alpha0_smoke.xml
tinyCase_base_control_exclude_lmax_dens005_smoke.xml
tinyCase_sami3_moments_dsB_lmlt_recommended_exclude_lmax_dens005_smoke.xml
```

## Alpha-Zero Result

Summary:

```text
exclude_lmax_alpha0_smoke_summary.json
validate_exclude_lmax_alpha0_smoke_summary.json
```

Validator:

```text
overall = ok
Pavg_formula_max_abs = 0
Davg_formula_max_abs = 0
Pstd_formula_max_abs = 0
Dstd_formula_max_abs = 0
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
history_last_steps = Step#3 / Step#3
```

The final recommended and baseline restarts are identical for checked RAIJU and
GAMERA fields:

```text
State/Pavg_in max_abs = 0
State/Davg_in max_abs = 0
State/eta max_abs = 0
State/Density max_abs = 0
State/Pressure max_abs = 0
Gas0 max_abs = 0
```

This is the baseline-recovery gate for the schema v7 exclude-Lmax product.

## Density-Only Result

Summary:

```text
exclude_lmax_dens005_smoke_summary.json
validate_exclude_lmax_dens005_smoke_summary.json
```

Validator:

```text
overall = ok
Pavg_formula_max_abs = 0
Davg_formula_max_abs = 0
Pstd_formula_max_abs = 0
Dstd_formula_max_abs = 0
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
history_last_steps = Step#3 / Step#3
```

The density-only alpha changes the expected fields while pressure inputs remain
unchanged at the direct coupler level:

```text
State/Pavg_in max_abs = 0
State/Davg_in max_abs = 870.24472656250009
State/Density max_abs = 4.3658608802500751
State/Pressure max_abs = 0.0030697298556502939
Gas0 max_abs = 4.2673096857777404
```

The `Pavg_in` direct formula remains unchanged because `alphaPavg=0`.  Downstream
pressure fields can still respond indirectly through the coupled RAIJU/GAMERA
state evolution.

## Interpretation

The schema v7 exclude-Lmax stage-2 product now has both offline and runtime
acceptance evidence:

```text
offline mapping product validator: ok
target-admissible closure validator: ok
runtime alpha=0 baseline recovery: ok
runtime alphaDavg=0.05 density-only smoke: ok
```

This validates the runtime hook and density-only adapter behavior for the
explicit source-domain policy product.  It still does not turn the product into
production physics coupling, because the source-domain accounting shows that
almost all positive active Voltron source bVol lies above the current RAIJU
target outer L edge.
