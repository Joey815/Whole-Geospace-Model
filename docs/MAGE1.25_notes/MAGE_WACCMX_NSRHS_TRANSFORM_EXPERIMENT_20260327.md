# MAGE-WACCMX `NSRHS` Transform Experiment on 2026-03-27

## Goal

Make the current `WACCM-X solver-scale rhs` to `TIEGCM-coupler-like NSRHS` hypothesis executable, instead of leaving it as a purely verbal conclusion.

## Added Controls

The experimental bridge now supports two explicit `NSRHS` controls:

- `--nsrhs-unfolding`
  - `none`
  - `mirror_south_folded_source_to_north`
- `--nsrhs-transform`
  - `none`
  - `solver_to_tiegcm_coupler_like`
  - `solver_to_tiegcm_coupler_crossmodel`

Updated files:

- [cesm_feedback_to_kaiju_feedback.py](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/cesm_feedback_to_kaiju_feedback.py)
- [run_bidirectional_cycle.sh](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/run_bidirectional_cycle.sh)

## Transform Definition

Current experimental transform:

- `solver_to_tiegcm_coupler_like`
- `solver_to_tiegcm_coupler_crossmodel`

Implemented as:

- `neutral_rhs_out = neutral_rhs_in * (-1 / dfac^2)`
- `neutral_rhs_out = neutral_rhs_in * (-1 / (dfac_waccm * dfac_tiegcm))`

where:

- `dfac = r0 * 1e-2`
- using local `WACCM-X` constants:
  - `SHR_CONST_REARTH = 6.37122e6 m`
  - `h0 = 9.7e6 cm = 9.7e4 m`
  - `r0 = 6.46822e6 m`
- and `TIEGCM` coupling constants:
  - `h0 = 9.0e6 cm = 9.0e4 m`
  - `r0 = 6.46122e6 m`

This transform was chosen because code-level comparison currently suggests:

- `WACCM-X rhspde rhs` is closer to `TIEGCM current.F` solver-scale `nsrhs`
- while `TIEGCM mage_ucurrent` export-side `nsrhs` applies the opposite scale/sign convention

Related code references:

- [TIEGCM current.F90](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/current.F90)
- [TIEGCM mage_coupling.F](/home/jiaoy_group/jiaoy/data/TIEGCM3.0_magecompat_min/src/mage_coupling.F)
- [WACCM-X edynamo.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/edynamo.F90)
- [MAGE_WACCMX_NSRHS_CODE_ALIGNMENT_CN.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_CODE_ALIGNMENT_CN.md)

## Generated Package

Using the existing `nsrhs_cycle_20260327d` artifacts, the following package was generated:

- [waccmx_cesm_feedback_package_coupler_like.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/waccmx_cesm_feedback_package_coupler_like.h5)
- [waccmx_cesm_feedback_package_coupler_crossmodel.h5](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/waccmx_cesm_feedback_package_coupler_crossmodel.h5)

Package metadata now records:

- `nsrhs_source=nsrhs_sidecar`
- `nsrhs_unfolding=mirror_south_folded_source_to_north`
- `nsrhs_transform=solver_to_tiegcm_coupler_like`
- `nsrhs_semantics=folded_solver_rhs_sidecar`
- `nsrhs_projection=mag_to_phys_regrid_then_bridge_regular_remap`

## Result

For the transformed package:

- North `NSRHS absmax = 1.325370994763974e-06`
- South `NSRHS absmax = 1.325370994763974e-06`

For the stricter cross-model package:

- North `NSRHS absmax = 1.326806884110e-06`
- South `NSRHS absmax = 1.326806884110e-06`

Compared to the current solver-scale mirrored package:

- previous `absmax ~ 5.54507e+07`
- transformed `absmax ~ 1.32537e-06`

This is a drop of roughly `4.19e13`, exactly consistent with the `1/dfac^2` hypothesis.

The difference between `coupler_like` and `coupler_crossmodel` is only about `0.108%`, documented in:

- [MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_DFAC_ALIGNMENT_20260327.md)

## Interpretation

This experiment does **not** prove the transform is physically correct.

What it does prove:

- the transform hypothesis is now executable
- the resulting magnitude is extremely small in the current `Kaiju NSRHS` injection path
- if this transform is physically correct, the present `Kaiju` `nsrhs_scale = 1e-8` tuning is no longer appropriate for meaningful feedback

In other words:

- `solver_to_tiegcm_coupler_like` is now a useful diagnostic branch
- `solver_to_tiegcm_coupler_crossmodel` is the stricter constant-level branch
- but it is not yet a validated production transform

## Smoke Attempt

A `step2` smoke launch was started with the transformed package in:

- [/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/step2_kaiju_feedback_coupler_like](/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs/runs/nsrhs_cycle_20260327d/step2_kaiju_feedback_coupler_like)

It was stopped before contract emission, because:

- the package-level `NSRHS` amplitude had already dropped to `~1e-6`
- under the current `Kaiju` experimental setting `nsrhs_scale = 1e-8`, the effective perturbation becomes negligible
- continuing to wait for a full smoke contract would not materially improve the interpretation of this transform branch

## Next Step

The next useful task is not more smoke runs. It is:

1. decide whether `WACCM-X rhs` should first be converted to a true `mag->geo coupler-scale` quantity before any `Kaiju` injection
2. if yes, retune `Kaiju` `NSRHS` injection scale for that transformed quantity
3. then rerun `step2` with a non-negligible but physically motivated `NSRHS` branch

## Follow-up

That retuning step has now been started and recorded separately in:

- [MAGE_WACCMX_NSRHS_SCALE_SCAN_20260327.md](/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_NSRHS_SCALE_SCAN_20260327.md)

Current practical outcome of the follow-up scan:

- the transformed branch becomes visibly active once `KAIJU_NSRHS_SCALE` enters roughly the `1e5-1e6` range
- `~4e5` is now the recommended working calibration point for the current `coupler-like` branch
