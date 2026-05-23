# MAGE-WACCMX SIGSEGV Analysis

Date:
- 2026-03-26

## Scope

This note summarizes the current root-cause judgment for the real
`MAGE <-> CESM/WACCM-X` file bridge failures seen under extreme forcing.

## What fails

The following compute-node tests fail in real `CESM/WACCM-X`:

- `stress_epot_x14`
- `stress_epot_x16`
- `stress_all_x16`

All three fail with the same signature:

- `Program received signal SIGSEGV: Segmentation fault - invalid memory reference.`
- `prterun noticed that process rank 3 ... exited on signal 11`

The crash happens after restart/history output files are opened.

## What succeeds nearby

- `stress_epot_x12` succeeds
- `stress_epot_x13` succeeds
- `stress_all_x12` succeeds

So the current practical thresholds are:

- `epot x13` succeeds, `epot x14` fails
- `all x12` succeeds, `all x16` fails

## Stack mapping

The failing addresses in `cesm.exe` were mapped with `addr2line`.

They resolve into the CAM/WACCM-X dynamics stack, not the bridge stub:

- `__tp_core_MOD_xtpv`
- `__tp_core_MOD_tp2d`
- `__tp_core_MOD_tp2c`
- `__sw_core_MOD_c_sw`
- `__sw_core_MOD_d_sw`
- `cd_core_`
- `__dyn_comp_MOD_dyn_run`
- `__stepon_MOD_stepon_run1`
- `__cam_comp_MOD_cam_run1`
- `__atm_comp_nuopc_MOD_modeladvance`

This points to a dynamics instability path, not a direct crash inside the
text/HDF5 bridge I/O layer.

## Bridge-side evidence

The WACCM-X ingest path overrides the ionospheric potential through:

- [ionosphere_interface.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/ionosphere_interface.F90)
- [dpie_coupling.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/dpie_coupling.F90)

The key implementation is:

- `d_pie_set_external_epot(epot_flat)`
- it reshapes the external `epot`
- multiplies it by `1000`
- writes it directly into `phihm`
- sets `prescribed_period = .true.`

There is currently:

- no amplitude limiter
- no smoothing
- no safety clamp before `phihm = prescr_phihm`

## Quantified forcing envelope

Using the actual generated `mage_waccmx_epot_global.txt` files:

- base `absmax(epot)` = `13.1707`
- `epot x12 absmax` = `158.0488`
- `epot x13 absmax` = `171.2195`
- `epot x14 absmax` = `184.3903`
- `all x16 absmax` = `210.7317`

Given the `* 1000` inside `d_pie_set_external_epot`, the successful and failing
cases are separated by a relatively narrow external potential window.

## Current judgment

The most likely present root cause is:

- extreme external `epot` amplitude from the MAGE bridge
- directly overrides WACCM-X electrodynamic potential
- drives the CAM/WACCM-X dynamics core unstable on rank 3

This is more consistent with a forcing-amplitude instability than with:

- file-format mismatch
- feedback-file corruption
- simple bridge array-size mismatch

That judgment is strengthened by the fact that:

- `epot x13` succeeds
- `epot x14` fails
- `all x16` also fails, but it includes `epot x16`

So the dominant trigger currently appears to be the `epot` amplitude, not the
auroral energy/flux branch.

## Recommended next step

Do not keep increasing forcing first.

The next useful engineering step is to test one of:

1. add a temporary `epot` clamp or smooth limiter before `phihm = prescr_phihm`
2. run a debug case around `x13.5`
3. add NaN/range checks immediately before and after `d_pie_set_external_epot`

## Update After Clamp And Smoothing Tests

Those follow-up tests have now been run.

Clamp-only result:

- a temporary `150`-V cap was added in
  [dpie_coupling.F90](/home/jiaoy_group/jiaoy/data/CESM/cesm_official_probe/components/cam/src/ionosphere/waccmx/dpie_coupling.F90)
- runtime logging confirmed cases like:
  `184.390 -> 150.000`
- but `stress_epot_x14_limited150` still failed

So amplitude clipping alone is not enough.

Bridge-side smoothing result:

- the bridge test driver now supports optional 2D smoothing of the generated
  `mage_waccmx_epot_global.txt`
- diagnostics are written into each test root as:
  `inputs/mage_waccmx_epot_summary.txt`

Observed outcomes:

- `stress_epot_x14_smooth1` succeeded
- `stress_epot_x14_smooth2` succeeded
- `stress_epot_x15_smooth2` did not segfault, but failed with:
  `te_map: Lagrangian levels are crossing`
  followed by `MPI_ABORT`
- `stress_epot_x16_smooth2` still failed with `SIGSEGV`
- `stress_epot_x16_smooth3` still failed with `SIGSEGV`
- `stress_all_x14_smooth2` succeeded
- `stress_all_x15_smooth2` failed with the same `te_map` crossing abort
- `stress_all_x16_smooth2` still failed with `SIGSEGV`

That shifts the practical interpretation:

- smoothing does help
- the first failure mode after smoothing is no longer only the old hard
  `SIGSEGV`
- a more physical-looking numerical instability now appears first near
  `smoothed_absmax(epot) ~= 181.8` through the `te_map` crossing abort
- by `smoothed_absmax(epot) ~= 185-194`, the old `rank 3 SIGSEGV` path still
  returns

Updated practical smoothed brackets:

- `epot x14 smooth2` succeeds, `epot x15 smooth2` aborts, `epot x16` fails
- `all x14 smooth2` succeeds, `all x15 smooth2` aborts, `all x16` fails

So the dominant issue is now better described as:

- extreme external `epot` structure and magnitude destabilize WACCM-X
- hard clipping is insufficient
- moderate smoothing materially improves robustness, but not enough to make
  `x15+` safe in the current bridge
