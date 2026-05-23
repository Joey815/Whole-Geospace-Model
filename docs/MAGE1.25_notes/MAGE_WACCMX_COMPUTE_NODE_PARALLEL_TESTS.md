# MAGE-WACCMX Compute-Node Parallel Tests

Date:
- 2026-03-26

## Goal

把原先在 `login01` 直接发起的 `MAGE <-> CESM/WACCM-X` 文件桥 aggressive
tests，迁移到 `Slurm` 计算节点上并行执行。

## Scripts

Core scripts:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_one_aggressive_test.sh`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling/scripts/waccmx_stub/run_voltron_smoke.sh`

New compute-node helpers:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/prepare_cesm_rundir_clone.sh`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/aggressive_test_matrix.tsv`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/aggressive_test_matrix_extreme.tsv`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/aggressive_test_matrix_bracket.tsv`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/aggressive_test_matrix_followup.tsv`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/run_aggressive_parallel_array.sbatch`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_aggressive_parallel.sh`

Key behavior changes:
- `run_one_aggressive_test.sh` now accepts `CESM_RUNDIR_OVERRIDE`
- `run_one_aggressive_test.sh` now accepts `CESM_EXE_OVERRIDE`
- `run_one_aggressive_test.sh` now accepts `CESM_MPI_NP`
- `run_voltron_smoke.sh` now accepts `VOLTRON_BIN_OVERRIDE`
- parallel jobs reuse the prebuilt
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_build/bin/voltron.x`
  instead of rebuilding in every task
- each array task first clones the base CESM run directory into node-local scratch
  so the tests do not collide through a shared rundir

## Resource Model

Per array task:
- partition: `intel`
- nodes: `1`
- MPI tasks: `4`
- OpenMP threads per task: `1`
- requested memory: `64G`
- walltime request: `00:25:00`

## First Attempt

Initial array submission:
- `job 4721803`

Result:
- all four tasks reached the real CESM run
- all four tasks were killed by Slurm with `OUT_OF_MEMORY`
- requested memory at that point was `32G`

Evidence:
- Slurm outputs under
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/waccmx-aggr-4721803_*.out`
- accounting shows `OUT_OF_MEMORY`

Observed batch `MaxRSS`:
- about `16G` to `22G`

Practical conclusion:
- `32G` is not safe for this compute-node parallel setup
- `CESM` writing restart/history files pushes the batch memory footprint high enough
  that the cgroup limit is exceeded

## Second Attempt

Updated array submission:
- `job 4721810`

Change:
- increased `#SBATCH --mem` from `32G` to `64G`

Result:
- all four array tasks completed successfully
- no `size mismatch`
- no `rc = 51`
- no `MPI_ABORT`

Accounting summary:
- `4721810_0` completed in `00:06:14`
- `4721810_1` completed in `00:06:13`
- `4721810_2` completed in `00:06:13`
- `4721810_3` completed in `00:06:11`

## Completed Compute-Node Result Roots

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute/epot_only_true_A4721810_T0`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute/aurora_only_true_A4721810_T1`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute/stress_epot_x8_A4721810_T2`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute/stress_all_x4_A4721810_T3`

## Third Attempt

Extreme-forcing array submission:
- `job 4725083`

Matrix:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/aggressive_test_matrix_extreme.tsv`

Result:
- `stress_all_x8` completed successfully in `00:06:06`
- `stress_epot_x16` failed in `00:03:35` with exit `11:0`

Interpretation:
- the current real bridge remains stable for at least `all x8`
- pure `epot` forcing at `x16` triggers a real CESM-side `SIGSEGV`
- this is not a Slurm memory kill; batch `MaxRSS` was about `17G`

Result roots:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_all_x8_A4725083_T1`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_extreme/stress_epot_x16_A4725083_T0`

## Fourth Attempt

Bracket-search array submission:
- `job 4725184`

Matrix:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/aggressive_test_matrix_bracket.tsv`

Accounting summary:
- `4725184_0` `stress_epot_x10` completed in `00:05:19`
- `4725184_1` `stress_epot_x12` completed in `00:06:05`
- `4725184_2` `stress_epot_x14` failed in `00:03:32` with exit `11:0`
- `4725184_3` `stress_all_x12` completed in `00:05:13`

Interpretation:
- the practical `epot` stability threshold is now bracketed between `x12` and `x14`
- combined forcing remains stable at least through `all x12`
- the observed failure mode is again a CESM-side `SIGSEGV` on `rank 3`

Result roots:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x10_A4725184_T0`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x12_A4725184_T1`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_epot_x14_A4725184_T2`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_bracket/stress_all_x12_A4725184_T3`

## Fifth Attempt

Follow-up array submission:
- `job 4725248`

Matrix:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/aggressive_test_matrix_followup.tsv`

Accounting summary:
- `4725248_0` `stress_epot_x13` completed in `00:06:20`
- `4725248_1` `stress_all_x16` failed in `00:02:43` with exit `11:0`

Interpretation:
- the practical `epot` stability threshold is now tighter:
  `x13` succeeds, `x14` fails
- the practical combined-forcing threshold is now bracketed:
  `all x12` succeeds, `all x16` fails
- the observed failure mode is again a CESM-side `SIGSEGV` on `rank 3`

Result roots:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_epot_x13_A4725248_T0`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_followup/stress_all_x16_A4725248_T1`

## Sixth Attempt

Mainline-worktree probe submission:
- `job 4726857`

Matrix:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/aggressive_test_matrix_mainline_probe.tsv`

Override:
- `VOLTRON_BIN_OVERRIDE=/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_mainline/build/bin/voltron.x`

Accounting summary:
- `4726857_0` `mainline_geo_probe` completed in `00:06:08` on `qhcn185`

Interpretation:
- the compute-node path also works with the isolated mainline-style
  `voltron.x` worktree
- this is not limited to the older `kaiju_waccmx_coupling` binary
- the step 2 contract again shows nonzero GEO feedback:
  `NEUTRAL_DYNAMO_RHS absmax = 41591.066 / 43965.227 cm/s`

Result root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests_compute_mainline/mainline_geo_probe_A4726857_T0`

Each successful result root contains:
- `manual_cesm_*.log`
- `waccmx_cesm_feedback_package.h5`
- `step2_kaiju_feedback/waccmx_voltron_contract.txt`
- `step2_kaiju_feedback/waccmx_voltron_exchange.md`
- `step2_kaiju_feedback/waccmx_voltron_forward_package.h5`

## Reuse

To resubmit the same parallel batch:

```bash
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_aggressive_parallel.sh
```

To change the test matrix, edit:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/aggressive_test_matrix.tsv
```

The current setup is suitable for short aggressive regression tests on compute nodes.

## Seventh Attempt

Full `1H` live-coupling runtime test on a compute node:
- `job 4747776`
- `job 4747788`
- `job 4747824`

Script:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/run_live_repair_plus1h.sbatch`

Target run:
- `test_name=live_repair_x1_plus1h_compute_m256`
- `num_cycles=12`
- forcing: `epot x1, avg_eng x1, num_flux x1`
- simulated time: `3600 s = 1 hour`

Result summary:
- `64G` attempt `4747776` failed with `OUT_OF_MEMORY` in `00:04:32`
- `128G` attempt `4747788` failed with `OUT_OF_MEMORY` in `00:17:59`
- `256G` attempt `4747824` completed successfully in `01:09:34`

Successful compute-node result root:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/live_repair_x1_plus1h_compute_m256_S4747824`

Key outputs:
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/live_repair_x1_plus1h_compute_m256_S4747824/final_summary.md`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/live_repair_x1_plus1h_compute_m256_S4747824/cycle12_summary.txt`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/waccmx-1h-4747824.out`

Observed timing:
- Slurm start time: `2026-03-31 23:58:54 +0800`
- Slurm end time: `2026-04-01 01:08:18 +0800`
- accounting elapsed: `01:09:34`
- wall/sim ratio: `4174 / 3600 = 1.159`
- sim/wall ratio: `3600 / 4174 = 0.862`

Interpretation:
- the `1H` MAGE-WACCMX live-repair run is now verified on the `intel`
  compute partition
- a safe memory request for this full `1H` workflow is currently `256G`
- on this node/queue configuration, the run is slightly slower than real time
  by about `15.9%`
