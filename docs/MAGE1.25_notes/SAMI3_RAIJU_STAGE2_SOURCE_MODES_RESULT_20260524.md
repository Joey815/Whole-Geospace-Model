# SAMI3 -> RAIJU Stage-2 Source Modes Result, 2026-05-24

## Scope

This step updates the stage-2 adapter:

```text
sami3_moments_to_raiju_diag.py
```

so that the MAGE-facing `Pavg/Davg` contract can be generated from either the
legacy number/ion-pressure aliases or the extended diagnostics added in stage 1.

## New Options

```text
--density-mode num
  Davg source = Davg_num if present, otherwise Davg

--density-mode massEq
  Davg source = Davg_massEq

--pressure-mode ion
  Pavg source = Pavg_i if present, otherwise Pavg

--pressure-mode total
  Pavg source = Pavg_total
```

Defaults are unchanged:

```text
--density-mode num
--pressure-mode ion
```

The selected source datasets are recorded in stage-2 metadata:

```text
density_mode
pressure_mode
moment_source_selection
std_source_warning
```

## Important Limitation

`Pstd/Dstd` still come from the existing `Pstd/Dstd` fields.  There is not yet a
mass-equivalent density std or total-pressure std.  For prototype runs using:

```text
--density-mode massEq
--pressure-mode total
```

runtime should normally use:

```text
alphaPstd=0
alphaDstd=0
```

unless matching std definitions are added later.

## Validation

Command:

```text
scripts/sami3_moments/run_sami3_mage_moments_smoke.sh
```

The smoke now validates:

```text
default nFluidIn=0, density=num, pressure=ion
default nFluidIn=1, density=num, pressure=ion
nFluidIn=1, density=massEq, pressure=total
```

Key output from the new mass-equivalent/total-pressure mode:

```text
Voltron.avgP/RAIJU.Pavg:
  min=0.009458690881729126
  max=4.586398124694824
  mean=1.6750577564385059

Voltron.avgN/RAIJU.Davg:
  min=49371.78125
  max=1816264.625
  mean=784130.8762613932

validated .../sami3_voltron_raiju_diag_stubpayload_nfluid1_massEq_total_20260524.h5
density_mode=massEq source=Davg_massEq
pressure_mode=total source=Pavg_total
SAMI3 MAGE moments smoke passed
```

The metadata confirms:

```text
moment_source_selection:
  Pavg  -> Pavg_total
  Davg  -> Davg_massEq
  Pstd  -> Pstd
  Dstd  -> Dstd
  tiote -> tiote
```

Evidence:

```text
logs/sami3_stage2_source_modes_20260524/sami3_stage2_source_modes_20260524.log
logs/sami3_stage2_source_modes_20260524/sami3_voltron_raiju_diag_stubpayload_nfluid1_massEq_total_20260524.json
```

## Operational Meaning

This provides the missing bridge between the extended SAMI3 diagnostics and the
new runtime alpha controls:

```text
Density-only prototype:
  stage 2: --density-mode massEq or num
  runtime: alphaDavg=1, alphaPavg=0, alphaPstd=0, alphaDstd=0

Cold total-pressure correction prototype:
  stage 2: --density-mode massEq --pressure-mode total
  runtime: alphaDavg=1, alphaPavg=0.0-0.2, alphaPstd=0, alphaDstd=0

Full overwrite smoke:
  stage 2: selected modes as desired
  runtime: alpha*=1
```

This is still not a production physical coupling until flux-tube-volume
weighting and L/MLT geometry mapping replace simple `nz` mean and index-space
resampling.

