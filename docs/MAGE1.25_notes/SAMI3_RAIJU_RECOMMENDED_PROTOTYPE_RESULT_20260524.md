# SAMI3 -> RAIJU Recommended Prototype Smoke

Date: 2026-05-24

## Scope

This is the current recommended short prototype after separate density,
pressure, and `tiote` scans:

```text
weight-mode = ds_over_B
mapping-mode = l_mlt
density-mode = num
pressure-mode = ion
alphaDavg = 0.05
alphaPavg = 0.05
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
moments/useStateTioteForIngest = T
```

The run uses the same mapped product:

```text
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_l_mlt_20260524.h5
```

## Runtime Deck

```text
tinyCase_sami3_moments_dsB_lmlt_D005_P005_stateTiote.xml
```

Log evidence:

```text
KAIJU/RAIJU/moments/useStateTioteForIngest = T (XML)
SAMI3 moments ingest enabled
SAMI3 moments ingest applied after RAIJU realtime pack
SAMI3 moments Pavg(0) min/max: 9.898480594555548e-04 1.218429505825043e-02
SAMI3 moments Davg(0) min/max: 0.361082989747654 872.230859375000
SAMI3 moments tiote min/max: 0.874837875366211 1.00044798851013
Fin
```

## Formula Checks

```text
Pavg_formula_max_abs = 5.587935444223424e-10
Pavg_formula_max_rel = 7.109258276005708e-08
Pavg_mean = 0.0016012076243789371

Davg_formula_max_abs = 3.662109372726263e-05
Davg_formula_max_rel = 7.136261094681787e-08
Davg_mean = 99.32539397052527
```

No checked runtime output contained non-finite values:

```text
nonfinite_raiCpl = []
nonfinite_raiju = []
nonfinite_gamera = []
```

## Response Summary

Relative to D005 (`alphaDavg=0.05`, `alphaPavg=0`, `alphaTiote=0`):

```text
State/Pavg_in max_abs = 0.012184295058250428
State/Davg_in max_abs = 0.0
State/eta max_abs = 445191290.0268131
State/Density max_abs = 4.5188891169032
State/Pressure max_abs = 0.0037172098709751245
GAMERA/Gas0 max_abs = 3.470269973136658
```

Relative to P005 (`alphaDavg=0.05`, `alphaPavg=0.05`, `alphaTiote=0`):

```text
State/Pavg_in max_abs = 0.0
State/Davg_in max_abs = 0.0
State/eta max_abs = 469234182.51662254
State/Density max_abs = 4.456585485572206
State/Pressure max_abs = 0.0035556669475522718
GAMERA/Gas0 max_abs = 3.418131278040273
```

Relative to state-tiote only (`alphaDavg=0.05`, `alphaPavg=0`, `alphaTiote=1`):

```text
State/Pavg_in max_abs = 0.012184295058250428
State/Davg_in max_abs = 0.0
State/eta max_abs = 300399099.6285839
State/Density max_abs = 3.5192327414045925
State/Pressure max_abs = 0.004154273056524382
GAMERA/Gas0 max_abs = 2.642839075193433
```

## Interpretation

This combined short smoke is the best current engineering prototype for the
SAMI3 -> RAIJU/GAMERA scalar-moment path.  It keeps the sensitive cold density
coupling small, adds a small cold pressure correction, disables std overwrite,
and explicitly enables gridded SAMI3 `tiote` in the H+/electron eta split.

It is still not a production physics configuration.  The next step is a longer
runtime stability scan with this prototype deck and a baseline/control pair.

## Evidence

Archived under:

```text
logs/sami3_dsB_lmlt_recommended_prototype_20260524/
```

including the XML deck, runtime log, and
`dsB_lmlt_recommended_prototype_summary.txt`.
