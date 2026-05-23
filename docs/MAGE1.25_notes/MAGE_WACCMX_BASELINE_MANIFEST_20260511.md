# MAGE-WACCMX Baseline Manifest

Date: 2026-05-11

## Scope

This manifest freezes the currently recoverable MAGE-WACCMX file-bridge baseline
before promoting the Kaiju/Voltron side from `WACCMX_STUB` wording to the formal
`WACCMX_FILE` backend.

The baseline is not yet CESM mediator or in-memory MPI coupling. It is the
current operational file-mediated loop:

- `MAGE/Voltron -> WACCM-X`: `POT / AVG_ENG / NUM_FLUX`
- `WACCM-X -> MAGE/REMIX`: `SIGMAP / SIGMAH`
- `neutral_rhs / NEUTRAL_DYNAMO_RHS`: available on the experimental path, off
  for the formal runtime baseline unless explicitly enabled

## Active Local Paths

| Role | Path |
| --- | --- |
| Bridge root | `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge` |
| Long-run driver | `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/run_long_coupling_stability.sh` |
| Runtime preflight | `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/preflight_mage_waccmx_runtime.sh` |
| Forward bridge | `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/kaiju_forward_to_cesm_import.py` |
| Feedback bridge | `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/cesm_feedback_to_kaiju_feedback.py` |
| Bridge Python | `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/waccmx_bridge_venv/bin/python` |
| CESM case | `/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_qhslurm_gnu` |
| CESM executable | `/online1/jiaoy_group/jiaoy/cesm/scratch/mage_qpx2000_f19_qhslurm_gnu/bld/cesm.exe` |
| Base CESM rundir | `/home/jiaoy_group/jiaoy/data/CESM/case_output/mage_qpx2000_f19_qhslurm_gnu/run` |
| Kaiju Voltron binary | `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/kaiju_waccmx_coupling_build/bin/voltron.x` |
| Kaiju restart base | `/home/jiaoy_group/jiaoy/data/MAGE1.25/runs/gtrd_20211204_0500_0510_official` |

## Current Preflight State

Fresh runtime preflight with `WACCMX_REPAIR_OP_HOOK=0` passes:

- core bridge scripts are present
- CESM case and `cesm.exe` are present
- bridge Python imports `h5py=3.1.0` and `numpy=1.19.5`
- base CESM rundir is present
- dated `rpointer.cpl.*` and `rpointer.cam.*` are present
- latest matched restart pointer stamp is `2005-12-31-00300`
- 4 WACCM-X feedback rank-map files are present
- Op repair source is not required when the hook is off

Current size snapshot:

- base CESM rundir: about `11G`
- bridge experiment tree: about `2.6G`

## Recovered Runtime Evidence

| Job | Meaning | State | Wallclock | CPUs | Memory | Node | Notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| `4747824` | historical 12-cycle reference | `COMPLETED` | `01:09:34` | 4 | `256G`, batch MaxRSS `21856172K` | `qhcn128` | true 1 h bridge reference, `NUM_CYCLES=12` |
| `7251770` | rebuilt CESM base rundir | `COMPLETED` | `00:03:17` | 4 | `256G`, batch MaxRSS `17193708K` | `qhcn286` | restored fresh 00300 base |
| `7251807` | fresh rebuilt 1-cycle test | `COMPLETED` | `00:08:11` | 4 | `256G`, batch MaxRSS `17345140K` | `qhcn187` | `NUM_CYCLES=1`, hook off |
| `7252193` | repeated fresh short check | `COMPLETED` | `00:08:04` | 4 | `256G`, batch MaxRSS `18104712K` | `qhcn491` | `NUM_CYCLES=1`, hook off |
| `7270235` | formal `WACCMX_FILE` 1-cycle test | `COMPLETED` | `00:08:13` | 4 | `256G`, batch MaxRSS `18103168K` | `qhcn289` | `NUM_CYCLES=1`, hook off, backend `WACCMX_FILE` |
| `7270337` | formal `WACCMX_FILE` 12-cycle/1 h test | `COMPLETED` | `01:02:15` | 4 | `256G`, batch MaxRSS `20524640K` | `qhcn029` | `NUM_CYCLES=12`, hook off, backend `WACCMX_FILE` |
| `7271584` | clean-exit `WACCMX_FILE` 1-cycle test | `COMPLETED` | `00:09:11` | 4 | `256G`, batch MaxRSS `17321664K` | `qhcn514` | `NUM_CYCLES=1`, no normal-path `SIGTERM`, backend `WACCMX_FILE` |
| `7271639` | clean-exit `WACCMX_FILE` 2-cycle loop test | `COMPLETED` | `00:13:32` | 4 | `256G`, batch MaxRSS `18109072K` | `qhcn514` | `NUM_CYCLES=2`, no normal-path `SIGTERM`, backend `WACCMX_FILE` |

The fresh short-check outputs are under:

- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/fresh_rebuild_x1_c1_20260510_S7251807`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/fresh_shortcheck_x1_c1_20260510b_S7252193`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_c1_20260511_S7270235`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_1h_20260512_S7270337`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_cleanexit_c1_20260512_S7271584`
- `/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/long_runs/waccmx_file_cleanexit_c2_20260512_S7271639`

## Known Boundary

Completed and usable:

- one-cycle fresh bridge baseline with `POT / AVG_ENG / NUM_FLUX` forward and
  `SIGMAP / SIGMAH` feedback
- formal one-cycle `WACCMX_FILE` backend run with no `WACCMX_STUB` label in
  final contract or HDF5 `/Meta` producer attributes
- formal 12-cycle/1 h `WACCMX_FILE` backend run with all `cycle01` through
  `cycle12` imports, feedback packages, and Kaiju artifact directories written
- clean-exit `WACCMX_FILE` control flow: `stopAfterExport=T` makes `voltron.x`
  print `Fin` after writing the forward package, so the long-run driver no
  longer needs normal-path `kill voltron.x`
- clean-exit 1-cycle and 2-cycle driver tests both completed with
  `SIGTERM count: 0`
- historical 12-cycle/1 h bridge reference
- preflight and cloned-rundir workflow for the fresh baseline

Not yet formalized:

- the current production driver still defaults to the old backend unless
  `KAIJU_GCM_BACKEND=WACCMX_FILE` is exported
- this file bridge is not yet TIEGCM-style online MPI coupling
- this file bridge is not yet CESM/CIME mediator coupling
- `neutral_rhs / NEUTRAL_DYNAMO_RHS` remains an experimental enhancement path,
  not a hard gate for the formal `SIGMAP/SIGMAH` runtime baseline
- the old job `7270337` still contains legacy per-cycle launcher `SIGTERM`
  lines because it was run before the clean-exit control-flow patch; use
  `7271584` or `7271639` as the current clean-log reference

## Baseline Rules For Next Runs

Use the fresh path by default:

```bash
KAIJU_GCM_BACKEND=WACCMX_FILE \
WACCMX_REPAIR_OP_HOOK=0 \
NUM_CYCLES=1 \
TEST_NAME=waccmx_file_c1_20260511 \
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh
```

The one-cycle and 12-cycle `WACCMX_FILE` gates have now passed. Reproduce the
1 h baseline with:

```bash
KAIJU_GCM_BACKEND=WACCMX_FILE \
WACCMX_REPAIR_OP_HOOK=0 \
NUM_CYCLES=12 \
TEST_NAME=waccmx_file_1h_20260512 \
/home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/cesm_kaiju_bridge/slurm/submit_fresh_rebuild_plus1h.sh
```

Acceptance checks:

- `final_summary.md` reports `kaiju_gcm_backend: WACCMX_FILE`
- `waccmx_voltron_contract.txt` starts with `# WACCMX_FILE contract summary`
- `waccmx_voltron_exchange.md` starts with `# WACCMX_FILE forward exchange summary`
- HDF5 `/Meta` attributes report producer `MAGE_WACCMX_FILE`
- feedback-ingest contract shows non-default `SIGMAP/SIGMAH`

The passed 1 h run `7270337` had final contract values:

- north `SIGMAP 0.138..17.691 S`, `SIGMAH 0.136..11.636 S`
- south `SIGMAP 0.110..10.050 S`, `SIGMAH 0.157..8.838 S`
- `NEUTRAL_DYNAMO_RHS absmax 0.000 cm/s` because `nsrhs_source_mode=off`

The clean-exit loop test `7271639` had final contract values:

- north `SIGMAP 0.138..17.691 S`, `SIGMAH 0.136..11.636 S`
- south `SIGMAP 0.110..10.050 S`, `SIGMAH 0.157..8.838 S`
- `NEUTRAL_DYNAMO_RHS absmax 0.000 cm/s` because `nsrhs_source_mode=off`
- log check: `SIGTERM count: 0`; seed, `cycle01`, and `cycle02` launcher logs
  all reached `Fin`
