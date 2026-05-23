# MAGE-WACCMX `NSRHS` Coupler-Like Scale Scan on 2026-03-27

## Goal

After introducing the experimental transform

- `nsrhs_transform=solver_to_tiegcm_coupler_like`

the `NSRHS` package amplitude dropped from `~5.5e7` to `~1.3e-6`.

This scan was used to answer one practical question:

- **At what `Kaiju NSRHS` injection scale does the transformed `NSRHS` begin to produce a visible `POT` response?**

## Setup

Feedback package:

- [waccmx_cesm_feedback_package_coupler_like.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/waccmx_cesm_feedback_package_coupler_like.h5)

Binary:

- [voltron.x](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_nsrhs_phase2_build/bin/voltron.x)

Runner:

- [run_one_nsrhs_scale_probe.sh](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/run_one_nsrhs_scale_probe.sh)

`Slurm` array:

- [run_nsrhs_scale_probe_array.sbatch](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/slurm/run_nsrhs_scale_probe_array.sbatch)
- job id: `4727826`

Matrix:

- [nsrhs_scale_probe_matrix.tsv](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/slurm/nsrhs_scale_probe_matrix.tsv)

Result root:

- [scale_probe_runs](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs)

Auto summary:

- [nsrhs_scale_scan_summary_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/scale_probe_runs/nsrhs_scale_scan_summary_20260327.md)

## Results

All six array tasks completed successfully on `qhcn215`.

### Raw scan table

| Scale | H1/H2 `NSRHS absmax` | North `POT` min/max (kV) | South `POT` min/max (kV) |
| --- | ---: | --- | --- |
| `0` | `1.3254e-06` | `-13.1088 / 10.9896` | `-15.7939 / 12.8570` |
| `1e4` | `1.3254e-06` | `-13.2092 / 10.9250` | `-15.7360 / 12.9350` |
| `1e5` | `1.3254e-06` | `-14.1279 / 10.3508` | `-15.2253 / 13.6557` |
| `4.18378699684e5` | `1.3254e-06` | `-17.5505 / 14.2636` | `-14.5545 / 16.3842` |
| `1e6` | `1.3254e-06` | `-25.0750 / 29.8424` | `-30.3332 / 23.3673` |
| `1e7` | `1.3254e-06` | `-257.376 / 274.286` | `-277.711 / 245.467` |

### Interpretation

- `scale=0` gives the transformed-package control run.
- `scale=1e4` produces only very small deviations from control.
- `scale=1e5` already gives a modest but visible `POT` shift.
- `scale=4.18e5` is the first point clearly in the same response neighborhood as the previous solver-scale mirrored tuning target.
- `scale=1e6` gives a strong but still bounded response.
- `scale=1e7` is numerically survivable in this smoke run, but the resulting `POT` amplitude is clearly too large for a calibration baseline.

## Practical Conclusion

For the current

- `mirror_south_folded_source_to_north`
- `solver_to_tiegcm_coupler_like`

experimental branch, the useful first calibration corridor is:

- **`KAIJU_NSRHS_SCALE ~ 1e5` to `1e6`**

with

- **`~4e5` as the most natural first detailed calibration point**

because it is the scale predicted from the previous solver-scale mirrored branch, and the scan confirms that it lands in a visible-but-not-yet-explosive response regime.

## What This Solves

This scan answers the tuning question raised by the transform experiment:

- the coupler-like transform does not make `NSRHS` unusably small
- it simply requires a much larger `Kaiju` injection scale than the old hard-coded `1e-8`

## What It Does Not Solve

This scan does **not** validate the transform physically.

It still does not prove:

- sign correctness relative to `TIEGCM mage_ucurrent`
- final scaling relative to `TIEGCM gnsrhs`
- whether bridge-side mirror unfolding should remain in Python or be moved upstream into `WACCM-X`

## Recommended Next Step

Do **not** continue blind scale scans.

Next step should be:

1. take `KAIJU_NSRHS_SCALE ~ 4e5` as the working experimental point
2. compare this branch explicitly against `TIEGCM nsrhs/gnsrhs` sign and amplitude conventions
3. only then decide whether to keep or revise the current coupler-like transform
