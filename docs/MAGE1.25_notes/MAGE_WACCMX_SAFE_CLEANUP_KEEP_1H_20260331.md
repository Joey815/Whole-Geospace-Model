# MAGE-WACCMX Safe Cleanup Plan

This note defines a conservative cleanup set that preserves:

- the current `1H` live run
- the current `MAGE-WACCMX` bridge runtime path
- the full `NSRHS` experiment tree
- the shared live `CESM` run directory

It is intentionally more conservative than the earlier space-minimization plan.

## Preserved

- Current `1H` run and all other `long_runs`:
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs`
- Real bridge run artifacts:
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/runs`
- Full `NSRHS` experiment tree:
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge_nsrhs`
- Shared live `CESM` run directory:
  - `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run`
- Required `Op` repair source:
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/maincase_op_repaired_from_success_20260329j`
- Active bridge scripts:
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_long_coupling_stability.sh`
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_bidirectional_cycle.sh`
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/op_repair_hook.sh`
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/kaiju_forward_to_cesm_import.py`
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cesm_feedback_to_kaiju_feedback.py`

## Cleanup Candidates

The dry-run cleanup script targets these archived experiment directories:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_existing_restart_continue` about `453G`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/isolated_seed_continue` about `66G`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/causal_replays` about `21G`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327a` about `11G`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327b` about `4.8G`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327c` about `11G`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/calibration_neutral_rhs_20260327d` about `21G`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/aggressive_tests` and archived compute variants about `~2.6G`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/neutral_rhs_probe_compute` about `296M`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/pure_continuation_checks` about `9.2M`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/compat_checks_20260330` about `5.3M`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/repaired_isolated_formal_loop_20260330a` about `880M`
- feedback/input scratch directories under `cesm_kaiju_bridge` that are no longer on the active runtime path
- all subdirectories under:
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets`
  except:
  - `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/patched_restart_sets/maincase_op_repaired_from_success_20260329j`

Estimated reclaimable space from this conservative plan is about `691G`.

## Evidence Archiving

Before deleting any candidate directory, the cleanup script archives lightweight reference evidence into:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/retained_reference_evidence_20260331`

Archived evidence patterns:

- `final_summary.md`
- `cycle*_summary.txt`
- `summary.txt`
- `manual_cesm*.log`
- `waccmx_voltron_contract.txt`
- `waccmx_voltron_exchange.md`
- `waccmx_voltron_forward_package.h5`
- `waccmx_voltron_feedback_package.h5`
- `waccmx_cesm_feedback_package*.h5`

## Cleanup Script

Dry-run cleanup script:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/safe_cleanup_preserve_1h_and_runtime.sh`

Defaults:

- `DRY_RUN=1`

To preview actions:

```bash
bash /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/safe_cleanup_preserve_1h_and_runtime.sh
```

To actually execute:

```bash
DRY_RUN=0 bash /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/safe_cleanup_preserve_1h_and_runtime.sh
```
