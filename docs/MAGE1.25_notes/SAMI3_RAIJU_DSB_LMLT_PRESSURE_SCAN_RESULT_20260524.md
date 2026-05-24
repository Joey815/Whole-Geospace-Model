# SAMI3 -> RAIJU `ds_over_B + l_mlt` Pressure Alpha Scan

Date: 2026-05-24

## Scope

This scan follows the density-only `D005` case and turns on a small cold
pressure correction while holding density fixed:

```text
alphaDavg = 0.05
alphaPavg = 0.05, 0.10
alphaPstd = 0
alphaDstd = 0
alphaTiote = 0
```

The input product is:

```text
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_l_mlt_20260524.h5
```

It uses:

```text
weight-mode   = ds_over_B
mapping-mode  = l_mlt
density-mode  = num
pressure-mode = ion
```

## Runs

Runtime decks:

```text
tinyCase_sami3_moments_dsB_lmlt_D005_P005.xml
tinyCase_sami3_moments_dsB_lmlt_D005_P010.xml
```

Both runs show:

```text
SAMI3 moments ingest enabled
SAMI3 moments ingest applied after RAIJU realtime pack
Fin
```

No checked runtime output contained non-finite values.

## Input Scale

```text
input_Pavg_mean_all_channels = 0.023705169558525085
base_Pavg_mean_all_channels  = 0.00043784124116159
input_Davg_mean_all_channels = 1985.4757080078125
base_Davg_mean_all_channels  = 0.05433108774465307
```

## Formula Checks

The runtime `Pavg` and `Davg` outputs match the expected blending formula within
float roundoff:

```text
P005 alphaPavg=0.05 alphaDavg=0.05:
  Pavg formula_max_abs = 5.587935444223424e-10
  Pavg formula_max_rel = 7.109258276005708e-08
  Pavg mean = 0.0016012076243789371
  Davg formula_max_abs = 3.662109372726263e-05
  Davg formula_max_rel = 7.136261094681787e-08
  Davg mean = 99.32539397052527

P010 alphaPavg=0.10 alphaDavg=0.05:
  Pavg formula_max_abs = 1.1175870888446848e-09
  Pavg formula_max_rel = 7.109258276005708e-08
  Pavg mean = 0.002764574007596285
  Davg formula_max_abs = 3.662109372726263e-05
  Davg formula_max_rel = 7.136261094681787e-08
  Davg mean = 99.32539397052527
```

All cases:

```text
nonfinite_raiCpl = []
nonfinite_raiju = []
nonfinite_gamera = []
```

## Response Summary

Relative to D005, `State/Davg_in` remains exactly unchanged while `State/Pavg_in`
increases as expected.  RAIJU eta and GAMERA gas respond continuously:

```text
P005 vs D005:
  State/Pavg_in max_abs = 0.012184295058250428
  State/Davg_in max_abs = 0.0
  State/eta max_abs = 223298863.16261744
  State/Density max_abs = 2.479753703459802
  State/Pressure max_abs = 0.0008338934223119376
  GAMERA/Gas0 max_abs = 1.182041161268213

P010 vs D005:
  State/Pavg_in max_abs = 0.024368590116500857
  State/Davg_in max_abs = 0.0
  State/eta max_abs = 223512627.2457647
  State/Density max_abs = 3.563959603434949
  State/Pressure max_abs = 0.0020288003824552314
  GAMERA/Gas0 max_abs = 1.8024580576901137
```

## Interpretation

Engineering result:

```text
Small SAMI3 cold-pressure corrections can be blended into the RAIJU runtime
coupler on top of alphaDavg=0.05 without non-finite values in this short smoke.
The runtime blending formula remains correct.
```

Physical caution:

```text
This is still a cold ion-pressure correction test, not confirmation that the
original RAIJU/RCM pressure population should be overwritten.
```

The next safer prototype setting is:

```text
alphaDavg = 0.05
alphaPavg = 0.05
alphaPstd = 0
alphaDstd = 0
alphaTiote = 0 for control
```

Then run a separate tiote-enabled variant with:

```text
moments/useStateTioteForIngest = T
alphaTiote = 1
```

## Evidence

Archived under:

```text
logs/sami3_dsB_lmlt_pressure_scan_20260524/
```

including both XML decks, both run logs, and
`dsB_lmlt_pressure_alpha_scan_summary.txt`.
