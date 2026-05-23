# MAGE-WACCMX O-resolution MPI Reference

Date: 2026-05-12

## Reference Sources

This note records the evidence used for the next O-resolution WACCMX_FILE MPI smoke test.

## Official O-resolution MAGE side

Local official-style O smoke directory:

`/home/jiaoy_group/jiaoy/data/MAGE1.25/runs/gtrd_20140820_1400_1410_officialO_smoke_fast`

The active O XML uses:

- runid: `gtrd_20140820_1400_1410_officialO_smoke_fast`
- grid: `lfmO.h5`
- GAMERA partition: `iPdir=8`, `jPdir=8`, `kPdir=1`
- GAMERA ranks: `64`
- VOLTRON helpers: `numHelpers=4`, `useHelpers=T`, `doSquishHelp=T`
- VOLTRON total MAGE ranks for MPI-only run: `64 GAMERA + 1 VOLTRON + 4 helpers = 69`
- O restart files are block-decomposed: `*_0008_0008_0001_*.gam.Res.00000.h5`

This means O-resolution cannot be run with non-MPI `voltron.x`, because non-MPI Voltron expects a single `*.gam.Res.00000.h5` file.

## Official TIEGCM-MAGE launch pattern

The D-resolution official GTR PBS reference launches TIEGCM and Voltron in one MPI world:

- TIEGCM ranks: `288`
- Voltron ranks: `5`
- Command pattern: `mpiexec -n 288 tiegcm.x ... : -n 5 pinCpuCores.sh voltron_mpi.x ...`

The O-resolution compact Slurm attempt used the same split idea:

- TIEGCM ranks: `288`, placed as `6 nodes x 48 ranks`
- Voltron ranks: `69`, placed across `34 nodes` with mostly `2 ranks/node`, last node `3 ranks`
- Total ranks: `357`
- Slurm allocation observed for job `7276962`: `40 nodes`, `2560 CPUs`, elapsed before cancellation `00:15:24`

For WACCMX_FILE export-only, the TIEGCM side is intentionally absent. Therefore the strict MAGE-side reference is the O Voltron slice only: `69` MPI ranks with O block restarts.

An even more compressed 7-node O smoke job was also present:

- job: `7279304`
- script: `/home/jiaoy_group/jiaoy/data/MAGE1.25/slurm/run_gtrd_officialO_gtr_compact7_smoke.sbatch`
- layout: `288` TIEGCM ranks on `6` nodes plus all `69` MAGE ranks on `1` node
- observed issue: `taskset ... Invalid argument`

That failure mode is consistent with overpacking `69` MAGE ranks on a single 64-core node while using the official pinning helper. It is therefore not a safe template for the WACCMX_FILE O test.

## Validated WACCMX_FILE D-resolution bridge

Validated D-resolution file-backend run:

`/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_formal_1h_clean_20260512_S7276927`

It completed `12` bridge cycles with:

- backend: `WACCMX_FILE`
- MAGE -> WACCM-X fields: `POT`, `AVG_ENG`, `NUM_FLUX`
- WACCM-X -> MAGE/REMIX fields: `SIGMAP`, `SIGMAH`
- `NEUTRAL_DYNAMO_RHS` present in contract but disabled for the clean formal run
- D grid: `lfmD.h5`
- D partition: `1x1x1`
- non-MPI `voltron.x`

This validates the file payload/contract path, but not O-resolution MPI startup.

## Failed O non-MPI probe

Failed O probe:

`/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_O_c1_probe_20260512_S7279187`

Failure mechanism:

- The script copied the correct O block restart files.
- The launcher still used non-MPI `voltron.x`.
- `voltron.x` searched for `gtrd_20140820_1400_1410_officialO_smoke_fast.gam.Res.00000.h5`.
- O-resolution only has block restart files, so no forward package was produced.

Conclusion: the next valid O test must use `voltron_mpi.x`.

## Current MPI WACCMX_FILE patch status

MPI build completed:

`/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_mpi_build/bin/voltron_mpi.x`

The local MPI driver now allows `doGCM=T` without an external GCM rank when `gcmBackend=WACCMX_FILE` or `WACCMX_STUB`. This is only for file/stub backends; normal TIEGCM MPI coupling remains external-rank based.

## Next Test Rule

The next test should be:

- O-resolution
- `voltron_mpi.x`
- `WACCMX_FILE`
- export-only with `stopAfterExport=T`
- no TIEGCM ranks
- no CESM cycling yet
- `69` MAGE ranks
- use official O XML values for grid, partition, helpers, restart files, and output cadence

If this produces `waccmx_voltron_forward_package.h5`, the O-resolution MAGE side of the WACCMX_FILE bridge is validated. Only after that should the CESM/WACCM-X feedback cycle be reattached.

## Practical queue fallback

The strict 34-node Voltron-slice job was submitted as `7279401`, but Slurm estimated a start time near `2026-05-22`, so it was cancelled before running.

The practical fallback keeps the same O grid, O partition, O restart files, O helper count, and `69` MPI ranks, but spreads the `69` ranks over `7` exclusive nodes as:

`10,10,10,10,10,10,9`

This avoids the known bad `69 ranks on one node` compact7 layout while keeping the test interactive enough to validate MPI WACCMX_FILE startup.

The 7-node fallback was also too slow to start in the current queue, so the immediate startup test uses a `compactN` script with the same O-resolution MAGE rank count but a smaller node count. The first submitted `compactN` target is `2` exclusive nodes with rank layout:

`35,34`

This is not a performance or production layout. It is only a startup/package-generation test for the MPI WACCMX_FILE backend at O grid resolution.

The first compactN attempt, job `7279447`, failed before copying inputs because the batch script had already sourced oneAPI and `run_voltron_smoke.sh` sourced `setvars.sh` a second time. The internal source now uses `setvars.sh --force`, so the environment setup no longer exits early when nested under Slurm scripts.

## CompactN MPI result and official-source comparison

The next compactN attempt, job `7279491`, ran on two exclusive nodes with the intended O-resolution MAGE rank layout:

- nodes: `qhcn818`, `qhcn819`
- rank layout: `35,34`
- total ranks: `69`
- O inputs prepared: `lfmO.h5`, `raijuconfig.h5`, `bcwind.h5`, O block GAMERA restarts, VOLTRON/RAIJU/REMIX restart files
- backend recognized: `VOLTRON: Using local file GCM backend: WACCMX_FILE`

This means the failure was not the earlier non-MPI O restart problem and not the WACCMX_FILE backend gate. The run failed before package generation during REMIX shell-grid construction:

```text
KAIJU/REMIX/grid/Np : 720
KAIJU/REMIX/grid/Nt : 90
Inside shell grid generator (GenShellGrid).
Phi array should be in the range [0,2*PI]. Quitting...
```

The official-style O spinup logs under:

`/home/jiaoy_group/jiaoy/data/MAGE1.25/runs/gtrd_20140820_1400_1410_officialO_smoke_fast`

also use `Np=720`, `Nt=90`, and advance normally. Therefore `Np=720` itself is not an invalid O-resolution setting.

The relevant source difference is:

- current local main MAGE source tree: `/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju/src/remix/mixgeom.F90`
- WACCMX experiment source: `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling/src/remix/mixgeom.F90`

The local main MAGE source tree currently clamps the periodic endpoint:

```fortran
p_periodic(Np+1) = 2.0_rp*pi
```

This is not in the clean `MAGE_1.25.1` git tag. `git blame` marks this line as `Not Committed Yet`, and `git describe` reports `MAGE_1.25.1-dirty`. The clean tag still uses the older extrapolated endpoint.

The WACCMX experiment source still uses the older extrapolated endpoint:

```fortran
p_periodic(Np+1) = 2*p(Np,1) - p(Np-1,1)
```

For `Np=360`, that expression lands exactly on `2*pi` in double precision in the tested environment; for `Np=720`, it produces `2*pi + 8.88e-16`, which triggers the strict `Phi > 2*PI` check in `shellGrid.F90`. This explains why the D-resolution bridge works while the O-resolution WACCMX MPI test fails at REMIX initialization.

The next source update should be limited to carrying this already-tested local `mixgeom.F90` endpoint fix into the WACCMX experiment source, then rebuilding only the WACCMX MPI binary and rerunning the same compactN O test. This is a lower-risk correction than changing O grid dimensions, changing REMIX defaults, or increasing node count.
