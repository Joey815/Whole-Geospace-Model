# SAMI3 -> RAIJU Extended Moment Diagnostics

Date: 2026-05-24

## Goal

Keep the existing RAIJU ingest path stable while exposing the diagnostic fields
needed to decide the physical meaning of `Davg` and `Pavg`.

The runtime fields remain:

```text
Davg = Davg_num     # total ion number density [#/cc]
Pavg = Pavg_i       # total ion pressure [nPa]
```

New stage-1 diagnostics:

```text
Davg_num
Davg_massEq
mu_eff
Pavg_i
Pavg_e
Pavg_total
f_H, f_O, f_NO, f_O2, f_He, f_N2, f_N
f_molecular
```

Ion mass numbers:

```text
H+=1, O+=16, NO+=30, O2+=32, He+=4, N2+=28, N+=14
```

Definitions:

```text
Davg_massEq = <sum_i A_i n_i>
mu_eff      = Davg_massEq / Davg_num
Pavg_i      = <sum_i n_i kB Ti_i>
Pavg_e      = <ne kB Te>
Pavg_total  = Pavg_i + Pavg_e
```

## Validation

Command:

```text
scripts/sami3_moments/run_sami3_mage_moments_smoke.sh
```

Result:

```text
SAMI3 MAGE moments smoke passed
moment_weighting=simple
physical_validity=smoke_only
```

Selected diagnostics from the smoke run:

```text
Davg_massEq: min=49371.78125 max=1816264.625 mean=784130.9375
mu_eff: min=14.785135269165039 max=30.46857261657715 mean=18.80472755432129
Pavg_e: min=0.004729345440864563 max=2.561614751815796 mean=0.8920273184776306
Pavg_total: min=0.009458690881729126 max=4.586398124694824 mean=1.6750576496124268
f_molecular: min=0.029179219156503677 max=1.0 mean=0.2600126564502716
```

The validator now also checks:

```text
Pavg_total = Pavg + Pavg_e
Davg_massEq >= Davg
mu_eff >= 1
units on the new diagnostic datasets
```

Archived logs:

```text
logs/sami3_moments_extended_diagnostics_20260524/
```

## Interpretation

This update prevents the next coupling decisions from being hidden inside a
single overloaded `Davg/Pavg` pair.  The production runtime can later choose:

```text
Davg_num versus Davg_massEq
Pavg_i versus Pavg_total
```

without changing the stage-1 reader again.

## Remaining Decisions

The code still leaves the live RAIJU ingest default as the old scalar contract.
The next runtime-side work is to add explicit options for:

```text
density-mode number | massEq
pressure-mode ion | total | original_plus_cold
runtime alpha blending per field
floors and finite-value guards
```
