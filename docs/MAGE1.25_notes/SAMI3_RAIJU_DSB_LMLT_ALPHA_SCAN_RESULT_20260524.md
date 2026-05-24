# SAMI3 -> RAIJU `ds_over_B + l_mlt` Density Alpha Scan

Date: 2026-05-24

## Scope

After validating the full `alphaDavg=1, alphaPavg=0.2` runtime smoke, this
scan isolates the density effect:

```text
alphaPavg = 0
alphaPstd = 0
alphaDstd = 0
alphaTiote = 0
alphaDavg = 0.05, 0.10, 0.20
```

The input product is the same mapped prototype:

```text
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_l_mlt_20260524.h5
```

## Runs

Runtime decks:

```text
tinyCase_sami3_moments_dsB_lmlt_D005.xml
tinyCase_sami3_moments_dsB_lmlt_D010.xml
tinyCase_sami3_moments_dsB_lmlt_D020.xml
```

All three runs show:

```text
SAMI3 moments ingest enabled
SAMI3 moments ingest applied after RAIJU realtime pack
Fin
```

No checked runtime output contained non-finite values.

## Input Scale

The mapped input remains much larger than the baseline RAIJU coupler density:

```text
input_Davg_mean_all_channels = 1985.4757080078125
base_Davg_mean_all_channels  = 0.05433108774465307
```

This is why the scan starts at small density alphas.

## Formula Checks

For all three cases, `Pavg` remained exactly baseline because `alphaPavg=0`.
`Davg` matched the runtime blending formula within float roundoff:

```text
D005 alphaDavg=0.05:
  Davg formula_max_abs = 3.662109372726263e-05
  Davg formula_max_rel = 7.136261094681787e-08
  Davg mean = 99.32539397052527

D010 alphaDavg=0.10:
  Davg formula_max_abs = 7.324218745452526e-05
  Davg formula_max_rel = 7.139196866164153e-08
  Davg mean = 198.5964568533059

D020 alphaDavg=0.20:
  Davg formula_max_abs = 0.00014648437490905053
  Davg formula_max_rel = 7.140665657897348e-08
  Davg mean = 397.13858261886713
```

## Response Summary

RAIJU `State/Davg_in` follows the alpha ramp exactly.  RAIJU density and GAMERA
`Gas0` respond continuously, while `State/eta` is the most sensitive diagnostic:

```text
D005:
  State/Density delta_max = 4.352037883696225
  State/eta delta_max = 852515660.4469385
  GAMERA/Gas0 delta_max = 4.262714108613584

D010:
  State/Density delta_max = 6.78451904931095
  State/eta delta_max = 1577045169.8438303
  GAMERA/Gas0 delta_max = 6.6941463236579315

D020:
  State/Density delta_max = 9.983316597770147
  State/eta delta_max = 2239493854.235352
  GAMERA/Gas0 delta_max = 7.627087523676051
```

All cases:

```text
nonfinite_raiCpl = []
nonfinite_raiju = []
nonfinite_gamera = []
```

## Interpretation

Engineering result:

```text
The ds_over_B + l_mlt product can be ramped into the runtime coupler.
The response is finite and continuous for alphaDavg <= 0.20 in the short smoke.
The XML and HDF5 runtime contracts remain correct.
```

Physical caution:

```text
Even alphaDavg=0.05 raises runtime Davg mean from about 0.054 to about 99.3.
```

So the density pathway should be ramped and diagnosed carefully.  The next
safe target is not `alphaDavg=1` production coupling; it is a longer smoke or
short science run around:

```text
alphaDavg = 0.05 to 0.10
alphaPavg = 0
alphaPstd = 0
alphaDstd = 0
alphaTiote = 0 or 1 in a separate scan
```

## Evidence

Archived under:

```text
logs/sami3_dsB_lmlt_alpha_scan_20260524/
```

including the XML decks, run logs, and
`dsB_lmlt_density_alpha_scan_summary.txt`.
