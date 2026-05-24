# SAMI3 -> RAIJU Weighting Contract Update

Date: 2026-05-24

## Goal

Make the stage-1 SAMI3 scalar-moments product explicit about whether it is a
simple smoke-test average or a prototype weighted moment.  This does not claim
to solve the final flux-tube-volume weighting problem; it makes the current
artifact self-describing so it cannot be mistaken for production physics.

## Code Snapshot

Archived under:

```text
code/kaiju_sami3_moments/scripts/sami3_moments/
code/kaiju_sami3_moments/src/voltron/modelInterfaces/
code/kaiju_sami3_moments/src/base/io_xml_input.F90
```

Active source tree:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523
```

## Change

`sami3_to_voltron_moments.py` now has an explicit weighting contract:

```text
--weight-mode simple
--weight-mode external
--weight-file /path/to/weights.dat
```

Default inference is backward compatible:

```text
no --weight-file -> weight-mode=simple
--weight-file    -> weight-mode=external
```

The first-stage HDF5 root, `/moments` group, and JSON metadata now record:

```text
moment_weighting = simple | external
physical_validity = smoke_only | prototype
```

Meaning:

```text
simple:
  unit weights along SAMI3 nz
  physical_validity=smoke_only

external:
  Fortran-unformatted weights with shape (nz,nf,nlt)
  physical_validity=prototype
  only meaningful if the file encodes ds/B, SAMI3 cell volume, or
  Voltron-equivalent flux-tube quadrature weights
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
weighting_source=unit_weights_along_sami3_nz
```

Archived logs:

```text
logs/sami3_moments_weighting_20260524/
```

## Remaining Physics Work

This update closes the metadata/contract gap only.  It does not yet implement
the final physical weighting.  The next concrete steps are:

```text
1. build or ingest a real ds/B or volume-weight file for SAMI3 nz,nf,nlt
2. add a quality summary for zero/negative/nonfinite weights
3. replace index-space resize in stage-2 with L/MLT or tube-geometry mapping
4. decide Davg number-density vs proton-equivalent mass-density mode
5. decide Pavg ion-only vs total-pressure mode and runtime blending policy
```
