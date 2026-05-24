# SAMI3 -> RAIJU Recommended Prototype 60s Smoke

Date: 2026-05-24

## Scope

This extends the recommended short prototype to a 60 second Voltron runtime and
pairs it with a 60 second baseline/control.

Prototype settings:

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

Runtime decks:

```text
tinyCase_base_control_long60.xml
tinyCase_sami3_moments_dsB_lmlt_recommended_long60.xml
```

## Run Result

Both logs end with:

```text
Fin
```

Both logs wrote 14 RAIJU HDF5 DATA blocks and reached the final RAIJU output
near 1.083 minutes.

The prototype log confirms:

```text
KAIJU/RAIJU/moments/useStateTioteForIngest = T
SAMI3 moments ingest applied after RAIJU realtime pack
```

## Formula Checks

Final `raiCpl` restart formula checks:

```text
Pavg_formula_max_abs = 5.587935444223424e-10
Pavg_formula_max_rel = 7.109258276005708e-08
Pavg_mean = 0.0016012076243789371

Davg_formula_max_abs = 3.662109372726263e-05
Davg_formula_max_rel = 7.136261094681787e-08
Davg_mean = 99.32539397052527
```

No checked physical datasets contained non-finite values:

```text
nonfinite_physics_base_raiCpl_res = []
nonfinite_physics_proto_raiCpl_res = []
nonfinite_physics_base_raiju_res = []
nonfinite_physics_proto_raiju_res = []
nonfinite_physics_base_gam_res = []
nonfinite_physics_proto_gam_res = []
nonfinite_physics_proto_raiju_history = []
nonfinite_physics_proto_gam_history = []
```

The only non-finite history entries were performance timer cache datasets under
`timeAttributeCache/_perf_*`, not physics fields.

## Final-State Response

Prototype versus baseline/control at final restart:

```text
State/Pavg_in max_abs = 0.012184295058250428
State/Davg_in max_abs = 872.230859375
State/eta max_abs = 658578162.0162892
State/Density max_abs = 3.6291416521227333
State/Pressure max_abs = 0.003918246350490762
GAMERA/Gas0 max_abs = 3.5398510248603285
```

Mean final-state comparison:

```text
State/Davg_in proto_mean = 99.32539397052527
State/Davg_in base_mean  = 0.05433108774465307
State/Pavg_in proto_mean = 0.0016012076243789371
State/Pavg_in base_mean  = 0.00043784124116159
GAMERA/Gas0 mean_abs_delta = 0.017140940619025425
```

## Interpretation

The recommended prototype now passes a longer 60 second smoke with a matching
baseline/control, exact runtime blending formula checks, and no non-finite
physics fields.  This is still a prototype: the SAMI3 density scale remains
large relative to baseline, so the next step should be a controlled longer run
or Slurm job at the same settings before increasing any alpha.

## Evidence

Archived under:

```text
logs/sami3_dsB_lmlt_recommended_long60_20260524/
```

including both XML decks, both run logs, and `recommended_long60_summary.txt`.
