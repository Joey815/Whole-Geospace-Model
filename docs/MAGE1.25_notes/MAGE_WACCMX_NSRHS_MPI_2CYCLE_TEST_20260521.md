# MAGE-WACCMX NSRHS MPI 2-Cycle Test, 2026-05-21

## Purpose

This test checks a safer WACCM-X neutral-dynamics feedback path into REMIX:

- Keep the established MAGE -> WACCM-X fields: `POT`, `AVG_ENG`, `NUM_FLUX`.
- Keep the established WACCM-X -> MAGE fields: `SIGMAP`, `SIGMAH`.
- Add WACCM-X neutral-dynamo forcing into an explicit REMIX field `NSRHS`, not into the older `NEUTRAL_WIND` slot.

The point is to avoid treating WACCM-X `edynamo` RHS-like output as a physical neutral wind. The raw WACCM-X sidecar is still large, so REMIX applies a controlled runtime gain through `KAIJU_NSRHS_SCALE`.

## Source And Build

- Isolated source copy: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_nsrhs_mpi`
- Isolated build: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_nsrhs_mpi_build`
- Binary used: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_nsrhs_mpi_build/bin/voltron_mpi.x`

Modified files in the isolated source copy:

- `src/base/defs/mixdefs.F90`: increased `nVars` and added `NSRHS`.
- `src/remix/mixio.F90`: added `NSRHS` name/unit and excluded it from normal dump selection.
- `src/remix/mixsolver.F90`: added `KAIJU_NSRHS_SCALE` and applies `NSRHS` directly in the REMIX RHS.
- `src/remix/waccmx_stub_backend.F90`: maps WACCM-X feedback into `NSRHS` and writes contract diagnostics.

The original successful source tree was not edited.

## Run Configuration

- Slurm job: `7515022`
- Job name: `waccmxDmpiN2`
- State: `COMPLETED`, exit code `0:0`
- Wallclock: `00:15:47`
- Resources: `4` CPUs on `qhcn008`
- Test name: `waccmx_file_d_mpi_phase2_nsrhs_geo_c2_20260521`
- Cycles: `2`
- MAGE grid: `lfmD.h5`
- MAGE partition: `1 x 1 x 1`
- Kaiju launch mode: `mpi_artifact_watch`
- Kaiju MPI ranks: `2`
- WACCM-X backend: `WACCMX_FILE`
- NSRHS source mode: `geo_sidecar`
- NSRHS transform: `none`
- Bridge NSRHS scale: `1.0`
- REMIX NSRHS scale: `1.0e-8`

Run directory:

`/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_phase2_nsrhs_geo_c2_20260521_S7515022`

## Evidence

WACCM-X external potential limiter did not clamp:

- Cycle 01: `d_pie_set_external_epot: input/limited absmax 10.763 -> 10.763`
- Cycle 02: `d_pie_set_external_epot: input/limited absmax 16.078 -> 16.078`

Final WACCM-X -> REMIX contract:

- Fields: `SIGMAP`, `SIGMAH`, `NSRHS`.
- Configured REMIX NSRHS scale: `1.0000E-08`.
- Hemisphere 1 `NSRHS absmax`: `5.6042E+07 arb`.
- Hemisphere 2 `NSRHS absmax`: `5.4393E+07 arb`.

MAGE -> WACCM-X potential after NSRHS feedback stayed in a safe range:

- Seed POT north: `-9.83992E+00` to `8.13701E+00` kV.
- Cycle 01 feedback POT north: `-1.65517E+01` to `1.04325E+01` kV.
- Cycle 02 feedback POT north: `-1.66547E+01` to `1.00587E+01` kV.
- Cycle 02 feedback POT south: `-1.71342E+01` to `1.29904E+01` kV.

Main result files:

- `final_summary.md`
- `cycle01_summary.txt`
- `cycle02_summary.txt`
- `cycle01_kaiju/waccmx_voltron_contract.txt`
- `cycle02_kaiju/waccmx_voltron_contract.txt`
- `cycle01_kaiju/waccmx_voltron_exchange.md`
- `cycle02_kaiju/waccmx_voltron_exchange.md`

## Interpretation

This validates the engineering direction:

- WACCM-X neutral-dynamics feedback can be routed into REMIX through an explicit `NSRHS` channel.
- The old unsafe behavior, where large neutral-RHS-like values could push MAGE POT outside WACCM-X limits, is avoided in this 2-cycle D-grid test.
- The raw WACCM-X sidecar magnitude is still about `5e7`, so the current interface is not a final physical unit conversion. It is a controlled RHS-injection interface.

This is not yet a final physics-complete neutral-wind coupling. The next step is to decide whether `NSRHS` should remain a calibrated RHS source term, or whether WACCM-X should instead provide physical neutral winds/conductance terms that REMIX converts internally using a documented electrodynamic formula.

## Recommended Next Step

Use this successful D-grid 2-cycle MPI run as the baseline for a longer stability test:

1. Repeat with `NUM_CYCLES=6` using the same binary and `KAIJU_NSRHS_SCALE=1e-8`.
2. Compare POT, `SIGMAP`, `SIGMAH`, and `NSRHS absmax` across cycles.
3. If stable, test sensitivity with `KAIJU_NSRHS_SCALE=5e-9` and `2e-8`.
4. Only after D-grid stability is established, revisit higher grid levels or native mediator/MPI integration.
