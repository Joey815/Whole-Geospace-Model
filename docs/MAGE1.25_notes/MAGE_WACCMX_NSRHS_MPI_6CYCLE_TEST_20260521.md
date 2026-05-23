# MAGE-WACCMX NSRHS MPI 6-Cycle Stability Test, 2026-05-21

## Result

The D-grid MPI/NSRHS stability test completed successfully.

- Slurm job: `7515219`
- Job name: `waccmxDmpiN6`
- State: `COMPLETED`
- Exit code: `0:0`
- Wallclock: `00:34:28`
- Resources: `4` CPUs on `qhcn169`
- Test name: `waccmx_file_d_mpi_phase2_nsrhs_geo_c6_20260521`
- Cycles: `6`
- MAGE grid: `lfmD.h5`
- Kaiju launch mode: `mpi_artifact_watch`
- Kaiju MPI ranks: `2`
- WACCM-X backend: `WACCMX_FILE`
- NSRHS source mode: `geo_sidecar`
- NSRHS transform: `none`
- Bridge NSRHS scale: `1.0`
- REMIX NSRHS scale: `1.0e-8`

Run directory:

`/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_d_mpi_phase2_nsrhs_geo_c6_20260521_S7515219`

## Coupling State Tested

MAGE -> WACCM-X:

- `POT`
- `AVG_ENG`
- `NUM_FLUX`

WACCM-X -> MAGE/REMIX:

- `SIGMAP`
- `SIGMAH`
- `NSRHS`, explicit neutral-dynamo RHS slot

This run uses the isolated MPI NSRHS build:

`/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_nsrhs_mpi_build/bin/voltron_mpi.x`

## Cycle Diagnostics

No WACCM-X external-potential limiter clamp occurred in any cycle.

| Cycle | WACCM-X epot input -> limited absmax | North POT range after feedback, kV | South POT range after feedback, kV | North NSRHS absmax | South NSRHS absmax |
| --- | ---: | ---: | ---: | ---: | ---: |
| 01 | `10.763 -> 10.763` | `-16.5517` to `10.4325` | `-17.4859` to `12.9576` | `5.6645E+07` | `5.5616E+07` |
| 02 | `16.078 -> 16.078` | `-16.6547` to `10.0587` | `-17.1342` to `12.9904` | `5.6042E+07` | `5.4393E+07` |
| 03 | `15.703 -> 15.703` | `-16.6903` to `9.74006` | `-16.8303` to `12.8701` | `5.5305E+07` | `5.3060E+07` |
| 04 | `15.402 -> 15.402` | `-16.7610` to `9.44836` | `-16.6059` to `12.7226` | `5.4416E+07` | `5.1584E+07` |
| 05 | `15.465 -> 15.465` | `-16.7630` to `9.25484` | `-16.4446` to `12.5449` | `5.3463E+07` | `4.9988E+07` |
| 06 | `15.468 -> 15.468` | `-16.7649` to `9.09140` | `-16.3124` to `12.3587` | `5.2998E+07` | `4.8274E+07` |

Final contract:

- `SIGMAP` north min/max: `0.159 / 18.081 S`
- `SIGMAH` north min/max: `0.236 / 11.736 S`
- `NSRHS` north absmax: `5.2998E+07 arb`
- `SIGMAP` south min/max: `0.154 / 9.172 S`
- `SIGMAH` south min/max: `0.288 / 8.521 S`
- `NSRHS` south absmax: `4.8274E+07 arb`

## Interpretation

This is a stronger validation than the previous 2-cycle smoke test:

- The explicit `NSRHS` channel remained numerically stable for six consecutive WACCM-X/MAGE file-coupling cycles.
- The MAGE potential did not run away after repeated WACCM-X neutral-dynamo feedback.
- WACCM-X never clipped the external electrodynamic input to its `150 kV` limiter.
- `NSRHS absmax` slowly decreased from about `5.6E+07` to `4.8-5.3E+07`, rather than amplifying.

This supports using `KAIJU_NSRHS_SCALE=1e-8` as the current D-grid baseline. It still should be treated as a calibrated RHS-injection interface, not as a final physical neutral-wind unit conversion.

## Next Step

Recommended next tests:

1. Run a weaker-gain sensitivity case with `KAIJU_NSRHS_SCALE=5e-9`.
2. Run a stronger-gain sensitivity case with `KAIJU_NSRHS_SCALE=2e-8`.
3. Compare six-cycle POT growth, NSRHS trend, and WACCM-X limiter behavior against this baseline.
4. Only after the D-grid gain range is bracketed, move to a higher grid level or a deeper mediator/MPI integration.
