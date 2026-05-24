# SAMI3 -> RAIJU `ds_over_B + l_mlt` Runtime Blend Result

Date: 2026-05-24

## Scope

This checkpoint runs the current best SAMI3 -> RAIJU prototype product through
the actual Voltron/RAIJU runtime hook:

```text
stage 1: SAMI3 scalar moments with weight_mode=ds_over_B
stage 2: RAIJU runtime product with mapping_mode=l_mlt
runtime: applySami3RaiCplMoments after tubeShell2RaiCpl
```

The input product was:

```text
analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_l_mlt_20260524.h5
```

## Runtime Runs

Runtime directory:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_blend_20260524
```

Binary:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/bin/voltron.x
```

Environment:

```text
OMP_NUM_THREADS=8
KMP_STACKSIZE=512M
OMP_STACKSIZE=512M
LD_LIBRARY_PATH includes:
/apps/support/intel_spr_rocky8.9/oneapi/2023.2.0/compiler/2023.2.0/linux/compiler/lib/intel64_lin
```

Runs:

```text
tinyCase_sami3_moments_dsB_lmlt_alpha0.xml
tinyCase_sami3_moments_dsB_lmlt_blend.xml
```

Both logs contain:

```text
SAMI3 moments ingest enabled
SAMI3 moments ingest applied after RAIJU realtime pack
Fin
```

## XML Parser Note

The local XML parser did not read multi-line `sami3Moments` attributes
correctly.  The working XMLs keep the `sami3Moments` element on one line, as in
the earlier successful runtime tests.

## Alpha-0 Baseline Recovery

The same `ds_over_B + l_mlt` input product was run with:

```text
alphaPavg = 0
alphaDavg = 0
alphaPstd = 0
alphaDstd = 0
alphaTiote = 0
```

Comparison against the no-SAMI3 baseline:

```text
alpha0_vs_base_raiCpl
  datasets = 36
  max_abs = 0.0
  max_rel = 0.0

alpha0_vs_base_raiju
  datasets = 47
  max_abs = 0.0
  max_rel = 0.0
```

This confirms the adapter can be enabled with the current mapped product and
still recover the baseline exactly when all alphas are zero.

## Conservative Blend Run

The conservative runtime test used:

```text
alphaPavg = 0.2
alphaDavg = 1.0
alphaPstd = 0.0
alphaDstd = 0.0
alphaTiote = 1.0
tioteMin = 0.05
tioteMax = 5.0
```

Formula checks against baseline plus the mapped SAMI3 product:

```text
Pavg:
  alpha = 0.2
  max_abs = 2.2351741776893697e-09
  max_rel = 7.109258276005708e-08
  base_mean = 0.00043784124116159
  input_mean = 0.023705169558525085
  got_mean = 0.005091306774030979

Davg:
  alpha = 1.0
  max_abs = 0.0
  max_rel = 0.0
  base_mean = 0.05433108774465307
  input_mean = 1985.4757080078125
  got_mean = 1985.4755887433569

Pstd:
  alpha = 0.0
  max_abs = 0.0
  max_rel = 0.0
  base_mean = 0.0001685590862329495
  input_mean = 0.08824501931667328
  got_mean = 0.0001685590862329495

Dstd:
  alpha = 0.0
  max_abs = 0.0
  max_rel = 0.0
  base_mean = 0.008178260314749292
  input_mean = 5179.2646484375
  got_mean = 0.008178260314749292
```

All checked runtime outputs were finite:

```text
blend_raiCpl nonfinite_datasets = []
blend_raiju nonfinite_datasets = []
blend_gamera nonfinite_datasets = []
```

## Runtime Response

Compared with the baseline, the blend run changed the intended RAIJU coupler
fields while preserving geometry/masks:

```text
blend_vs_base_raiCpl:
  Davg max_abs = 17444.6171875
  Pavg max_abs = 0.04873718023300171
  Pstd/Dstd max_abs = 0.0
  masks max_abs = 0.0
```

RAIJU and GAMERA responded without crashing or producing non-finite output.

## Interpretation

Engineering status:

```text
SAMI3 -> RAIJU runtime adapter works with ds_over_B weighting and L/MLT mapping.
alpha=0 exactly recovers baseline.
conservative P/D/tiote blending matches the expected formula.
```

Physical caution:

```text
Davg base_mean  = 0.05433108774465307
Davg input_mean = 1985.4757080078125
```

The density contrast is very large because the mapped SAMI3 product is cold
ionospheric/plasmaspheric plasma whereas the baseline RAIJU input moment is much
smaller.  This short smoke proves runtime continuity, not production-safe
physical amplitude.

## Next Step

Run an alpha scan before treating this as physical coupling:

```text
alphaDavg = 0.0, 0.05, 0.1, 0.2, 0.5, 1.0
alphaPavg = 0.0, 0.05, 0.1, 0.2
alphaPstd = 0
alphaDstd = 0
```

and inspect:

```text
RAIJU State/Density
RAIJU State/eta
GAMERA Gas0
Alfven speed / timestep behavior
NaN/Inf/floor hits
```

The likely near-term safe mode is density ramping, not immediate
`alphaDavg=1` production coupling.
