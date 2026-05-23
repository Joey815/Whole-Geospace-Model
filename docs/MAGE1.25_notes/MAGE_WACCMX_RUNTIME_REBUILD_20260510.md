# MAGE-WACCMX Runtime Rebuild - 2026-05-10

## Scope

This rebuild reconstructed the runnable wrapper environment after the previous
conversation state was lost and after cleanup had removed several heavy runtime
directories.

The target is the file-bridge MAGE-WACCMX workflow:

- MAGE/Voltron -> WACCM-X: `POT / AVG_ENG / NUM_FLUX`
- WACCM-X -> MAGE/REMIX: `SIGMAP / SIGMAH`
- `neutral_rhs / NSRHS`: kept off for this formal runtime path

## Evidence Read

Main evidence used:

- `MAGE_WACCMX_COMPUTE_NODE_PARALLEL_TESTS.md`
- `MAGE_WACCMX_REAL_FILE_COUPLING_STATUS.md`
- `MAGE_WACCMX_RESTART_TRANSPLANT_MATRIX_20260329.md`
- `MAGE_WACCMX_SAFE_CLEANUP_KEEP_1H_20260331.md`
- `experiments/cesm_kaiju_bridge/slurm/waccmx-1h-4747824.out`
- retained lightweight evidence under:
  `experiments/cesm_kaiju_bridge/retained_reference_evidence_20260331`

## Initial State Found

Still present:

- active bridge Python scripts:
  - `kaiju_forward_to_cesm_import.py`
  - `cesm_feedback_to_kaiju_feedback.py`
- active long-run driver:
  - `run_long_coupling_stability.sh`
- active CESM case:
  - `/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_qhslurm_gnu`
- active CESM executable:
  - `/online1/jiaoy_group/jiaoy/cesm/scratch/mage_qpx2000_f19_qhslurm_gnu/bld/cesm.exe`
- active bridge Python env:
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/waccmx_bridge_venv`
- active Voltron binary:
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_build/bin/voltron.x`

Missing before rebuild:

- `experiments/cesm_kaiju_bridge/long_runs`
- `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run`
- `experiments/cesm_kaiju_bridge/patched_restart_sets/maincase_op_repaired_from_success_20260329j`

Important interpretation:

- The old exact `4747824` path with `Op repair hook=1` cannot be exactly
  re-run until the missing `maincase_op_repaired_from_success_20260329j`
  source is restored or regenerated.
- A fresh startup baseline can be run with `Op repair hook=0`; this has now
  been tested.

## Scripts Rebuilt / Updated

Added:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/preflight_mage_waccmx_runtime.sh`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/rebuild_cesm_base_rundir.sbatch`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_rebuild_cesm_base_rundir.sh`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh`

Updated:

- `run_live_repair_plus1h.sbatch`
  - default memory changed to `256G`
  - default test name changed to `live_repair_x1_plus1h_compute_m256`
  - strict runtime preflight added before cloning the base CESM rundir
- `submit_live_repair_plus1h.sh`
  - exports the known successful `x1/x1/x1`, `NUM_CYCLES=12`, `NSRHS=off`
    defaults
  - runs strict preflight before submit
- `run_long_coupling_stability.sh`
  - hard-coded paths now have environment-variable overrides

## Rebuild Job

CESM base rundir rebuild:

- Slurm job: `7251770`
- node: `qhcn286`
- state: `COMPLETED`
- elapsed: `00:03:17`
- requested memory: `256G`
- batch MaxRSS: `17193708K`
- output:
  `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/waccmx-base-7251770.out`

Restored base runtime files:

- `rpointer.cam.2005-12-31-00300`
- `rpointer.cpl.2005-12-31-00300`
- `mage_qpx2000_f19_qhslurm_gnu.cam.r.2005-12-31-00300.nc`
- `mage_waccmx_feedback_rank000000.txt` through `rank000003.txt`

Current restored rundir size:

- `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run`
- about `11G`

## Smoke Test

Fresh rebuilt baseline 1-cycle test:

- Slurm job: `7251807`
- node: `qhcn187`
- state: `COMPLETED`
- elapsed: `00:08:11`
- requested memory: `256G`
- batch MaxRSS: `17345140K`
- test name: `fresh_rebuild_x1_c1_20260510`
- `NUM_CYCLES=1`
- forcing: `epot x1, avg_eng x1, num_flux x1`
- `WACCMX_REPAIR_OP_HOOK=0`
- `WACCMX_NSRHS_SOURCE_MODE=off`

Result root:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/fresh_rebuild_x1_c1_20260510_S7251807`

Key result:

- `LONG_STABILITY_DONE fresh_rebuild_x1_c1_20260510`
- CESM crossed the `00300` continuation with fresh baseline and `hook=0`
- WACCM-X feedback was converted to a Kaiju feedback package
- final Kaiju feedback ingestion succeeded

Final contract values:

- North `SIGMAP`: `0.138 .. 17.676 S`
- North `SIGMAH`: `0.136 .. 11.635 S`
- South `SIGMAP`: `0.109 .. 10.063 S`
- South `SIGMAH`: `0.157 .. 8.839 S`
- `NEUTRAL_DYNAMO_RHS absmax`: `0.000 cm/s`

## Current Operational Recommendation

Use the fresh-rebuild path for the next full 1H run:

```bash
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh
```

This submits:

- `NUM_CYCLES=12`
- `x1/x1/x1`
- `NSRHS=off`
- `Op repair hook=0`
- `256G`

Use the historical repair-hook path only after restoring:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/maincase_op_repaired_from_success_20260329j
```

## Quick Checks

Fresh path preflight:

```bash
WACCMX_REPAIR_OP_HOOK=0 \
  /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/preflight_mage_waccmx_runtime.sh \
  --mode live-1h --strict
```

Historical repair-hook path preflight:

```bash
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/preflight_mage_waccmx_runtime.sh \
  --mode live-1h --non-strict
```

As of this rebuild, the historical path still reports the missing
`Op repair source`; the fresh path passes.
