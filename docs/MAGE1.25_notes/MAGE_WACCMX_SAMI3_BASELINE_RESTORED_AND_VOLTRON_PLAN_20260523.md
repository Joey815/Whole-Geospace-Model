# MAGE1.25-WACCMX / WACCM-X-SAMI3 Baseline Restored And Voltron Plan, 2026-05-23

Timestamp: `2026-05-23 03:54 CST`

## Restored Baseline

The accidental WACCM-X -> SAMI3 live neutral-payload branch has been removed.
The current controlled baseline is again the file-backed online MPI smoke:

```text
WACCM-X/CAM sender -> pre-generated waccmx_neutral_rank*.bin -> SAMI3 online receiver
```

Files restored/cleaned:

- `/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_online/SourceMods/src.cam/wxsami3_online_stub_mod.F90`
  - file-backed sender only
  - reads `WXSAMI3_PORT_FILE`, `WXSAMI3_PAYLOAD_PREFIX`, `WXSAMI3_NUMWORKERS`, `WXSAMI3_SKIP_DISCONNECT`
  - keeps the verified `tag_done = 299`
  - keeps `MPI_Comm_disconnect`
  - disables the sender after disconnect to avoid reconnecting to finalized SAMI3
- `/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_online/SourceMods/src.cam/cam_comp.F90`
  - restored call: `call wxsami3_cam_send(get_nstep(), dtime_phys)`
  - no longer passes `phys_state(:)` into this neutral sender
- Removed accidental live artifacts:
  - `/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/run_waccmx_cam_sami3_online_livepayload_20231013.sbatch`
  - `/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_livepayload_20231013_0000`

Static check:

- no `WXSAMI3_PAYLOAD_MODE`
- no `WXSAMI3_GRID_DIR`
- no `use_live_payload`
- no live neutral grid sampling routines in the current sender path

## Verification

Build after cleanup:

```text
case      = /home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_online
command   = HOME=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/tmp/cime_home_empty PATH=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/python311_first:$PATH ./case.build --skip-provenance
result    = MODEL BUILD HAS FINISHED SUCCESSFULLY
```

Post-cleanup file-backed smoke:

```text
job       = 7632147
node      = qhcn062
state     = COMPLETED
elapsed   = 00:02:37
exit      = 0:0
layout    = 1 node, 49 CPUs total
SAMI3     = 33 ranks
CESM      = 16 ranks
script    = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/run_waccmx_cam_sami3_online_stubpayload_20231013.sbatch
```

CAM markers:

```text
WXSAMI3 online sender enabled
WXSAMI3 payload prefix: /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_payload_esmf_msis_top_20231013_0000/waccmx_neutral_rank
WXSAMI3 sent neutral packet: nstep,packet_hour,count=0 0.0 0
WXSAMI3 sent done signal to SAMI3
WXSAMI3 disconnected from SAMI3
******* END OF MODEL RUN *******
```

SAMI3 markers:

```text
WACCMX online sender connected
WACCMX online neutral received: taskid,step,packet_hr=1..32 0 0.0
MASTER: All Done!
WACCMX online done signal received: 1
```

Current queue state after verification:

```text
no active user jobs
```

## Current Goal

Do not continue the WACCM-X -> SAMI3 live neutral-payload path now.

The next engineering goal is:

```text
SAMI3 plasma state -> Voltron moments adapter -> GAMERA/RAIJU diagnostic path
```

Use the existing MAGE/Voltron moments interface as the main integration target:

```text
Pavg, Davg, Pstd, Dstd, tiote
```

The adapter should not feed full raw SAMI3 3-D arrays directly into GAMERA.
The first milestone is diagnostic coupling only, not feedback into GAMERA main
equations.

## Acceptance Criteria

The next phase is successful when all of the following are true:

1. SAMI3 source variables, dimensions, units, and ion ordering are documented from code.
2. The mapping from SAMI3 variables to `Pavg/Davg/Pstd/Dstd/tiote` is explicit and unit-checked.
3. A minimal adapter produces finite diagnostic moments on a MAGE/Voltron-compatible grid or file schema.
4. Voltron/RAIJU can ingest or read the diagnostic moments without changing GAMERA physics.
5. Output contains inspectable `Pavg`, `Davg`, `Pstd`, `Dstd`, and `tiote` fields with plausible ranges.

## Plan

Phase 1: inspect and freeze interfaces.

- Confirm SAMI3 arrays: `deni`, `ne`, `ti`, `te`, `vsi`, and possibly `vpi`.
- Confirm ion order: `H+`, `O+`, `NO+`, `O2+`, `He+`, `N2+`, `N+`.
- Confirm MAGE/Voltron fields and units in `voltCplTypes.F90` and `raijuCplHelper.F90`.

Phase 2: define the moment contract.

- `Davg`: flux-tube or mapped-shell density average in `#/cc`.
- `Pavg`: pressure derived from density and temperature, converted to `nPa`.
- `Dstd`: density spread, normalized consistently with existing RAIJU handling.
- `Pstd`: pressure spread, normalized consistently with existing RAIJU handling.
- `tiote`: representative ion/electron temperature ratio.

Phase 3: build a diagnostic adapter first.

- Start offline or sidecar-style from SAMI3 output/restart fields, not live feedback.
- Produce a small, inspectable artifact with the five moment fields.
- Validate finite values, ranges, masks, and species aggregation.

Phase 4: connect to Voltron/RAIJU diagnostics.

- Reuse existing read/write helpers where possible.
- Add the smallest hook needed to ingest or compare the diagnostic fields.
- Do not alter GAMERA main equations in this phase.

Phase 5: decide feedback only after diagnostics pass.

- If diagnostics are stable, choose whether moments should affect inner boundary,
  plasmasphere mass loading, or remain a diagnostic product.

