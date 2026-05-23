# MAGE1.25-WACCMX handoff, 2026-05-23

This file is a compact continuation note for the broken Codex thread:

- UI title: `MAGE1.25-WACCMX`
- thread id: `019d2071-7fe7-74e1-9447-97ff7fb80aa4`
- rollout: `/home/jiaoy_group/jiaoy/.codex/sessions/2026/03/24/rollout-2026-03-24T23-23-22-019d2071-7fe7-74e1-9447-97ff7fb80aa4.jsonl`
- break reason: remote compact fails with `context_length_exceeded`; compact request was about 18 MB. The JSONL itself is valid.

Do not continue heavy work in that old thread. Start a new thread and attach/read this handoff plus the status files below.

## Current Status

The latest working direction is WACCM-X/CAM plus SAMI3 online MPI coupling as a separate local proof toward the broader MAGE/WACCM-X/SAMI3 architecture.

Completed:

- Official SAMI3 3.22 builds and runs locally.
- Offline/staged WACCM-X neutral forcing into SAMI3 works.
- ESMF-style WACCM-X-to-SAMI3 payloads were tested.
- He is no longer forced from a placeholder; SAMI3 native MSIS He is retained.
- Above WACCM-X top now retains SAMI3 native MSIS/HWM state instead of using simple topside extrapolation.
- SAMI3 online receiver mode works with MPI intercommunicator.
- A real two-executable smoke with CESM/WACCM-X plus SAMI3 completed cleanly.

Not completed:

- The WACCM/CAM sender still sends pre-generated `waccmx_neutral_rank*.bin` payloads, not live `phys_state` arrays.
- It does not yet send a packet every WACCM-X timestep from runtime state.
- `REMIX -> SAMI3` high-latitude potential/E-field forcing is not implemented.
- `SAMI3 -> GAMERA/REMIX` plasma feedback is not implemented.
- WACCM-X is not receiving SAMI3 plasma moments back.

## Key Evidence

Main plan/status file:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/WACCMX_SAMI3_ONLINE_MPI_PLAN_20260522.md
```

Successful real two-executable smoke:

```text
job       = 7532381
node      = qhcn066
state     = COMPLETED
elapsed   = 00:02:11
exit      = 0:0
layout    = 1 node, 49 CPUs total
SAMI3     = 33 ranks
CESM      = 16 ranks
```

Key log markers:

```text
WXSAMI3 online sender enabled
WXSAMI3 connected to SAMI3
WXSAMI3 sent neutral packet: nstep,packet_hour,count=0 0.0 0
WXSAMI3 sent done signal to SAMI3
WXSAMI3 disconnected from SAMI3
WACCMX online done signal received: 1
******* END OF MODEL RUN *******
```

Evidence files:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000/slurm-7532381.out
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000/sami3_online_receiver.out
/home/jiaoy_group/jiaoy/data/CESM/case_output_root_online/mage_qpx2000_f19_sami3_online/run/atm.log.260522-053406
```

## Important Code Paths

WACCM/CAM SourceMods case:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_online
```

WACCM/CAM online sender SourceMod:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_online/SourceMods/src.cam/wxsami3_online_stub_mod.F90
```

Current sender behavior:

- Reads `WXSAMI3_PORT_FILE`, `WXSAMI3_PAYLOAD_PREFIX`, `WXSAMI3_NUMWORKERS`, and `WXSAMI3_SKIP_DISCONNECT`.
- Connects to SAMI3 by `MPI_Comm_connect`.
- Sends per-worker neutral payload arrays read from file-backed payloads.
- Sends explicit `tag_done = 299`.
- Calls `MPI_Comm_disconnect`.
- Sets both `is_connected = .false.` and `is_enabled = .false.` after finalize to avoid accidental reconnect later in CAM shutdown.

CAM hook location:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_online/SourceMods/src.cam/cam_comp.F90
```

Important hook facts:

- `phys_state(:)` is available in `cam_comp.F90`.
- `wxsami3_cam_finalize()` is called in `cam_run4` when `nlend` is true, before heavy history/restart output.
- The next production sender should extract live neutral fields from `phys_state(:)` and CAM constituent indices instead of reading `waccmx_neutral_rank*.bin`.

SAMI3 online work tree:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/work/sami3-3.22_online_mpi_openmpi
```

SAMI3 online receiver module:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/work/sami3-3.22_online_mpi_openmpi/waccmx_neutral_mod.f90
```

## Variables Currently In Scope

WACCM-X -> SAMI3 neutral forcing should include:

- neutral temperature: `T`
- horizontal neutral winds: `U`, `V`
- optional later vertical wind: `W`, only if runtime availability and physical meaning are validated
- neutral composition: `O`, `O2`, `H`, `N`, `NO`
- pressure/height support: `PS`, `Z3` or runtime equivalent

Current local policy:

- `N2` can remain residual-derived initially.
- `He` should remain SAMI3 native/MSIS unless runtime WACCM-X He is found and validated.
- Above the WACCM-X top, keep SAMI3 native MSIS/HWM neutral state.

MPI payload currently sent by the file-backed smoke:

- `denni`
- `tni`
- `ui`
- `vi`
- `wi`
- `dennf`
- `tnf`
- `uf`
- `vf`
- `wf`

These represent initial/final neutral states in the same format already validated by the staged payload bridge.

## MAGE Interpretation

The current local MAGE-WACCMX path already proves a separate stable REMIX/WACCM-X exchange:

```text
MAGE/REMIX -> WACCM-X: POT, AVG_ENG, NUM_FLUX
WACCM-X -> MAGE/REMIX: SIGMAP, SIGMAH, NSRHS
```

The WACCM-X/SAMI3 path currently proves:

```text
WACCM-X/CAM can send a file-backed staged neutral payload to SAMI3 through an
online MPI control path
```

It does not yet prove live WACCM-X neutral forcing from runtime
`phys_state(:)`.

The missing official-style bridges are:

```text
live WACCM-X/CAM phys_state neutral extraction -> SAMI3
REMIX potential or E-field -> SAMI3
SAMI3 plasma moments -> GAMERA / MAGE feedback
```

For SAMI3 plasma feedback, do not feed full raw SAMI3 3D arrays directly into GAMERA. The better route is:

```text
SAMI3 -> Voltron moments adapter -> GAMERA/RAIJU
```

Use the existing MAGE/Voltron moment semantics where possible:

- `Pavg`: flux-tube-averaged pressure, `nPa`
- `Davg`: flux-tube-averaged density, `#/cc`
- `Pstd`: pressure spread or normalized standard deviation
- `Dstd`: density spread or normalized standard deviation
- `tiote`: ion/electron temperature ratio

SAMI3 source variables likely needed for that adapter:

- ion densities: `deni(:,:,:,1:7)`
- electron density: `ne`
- ion temperatures: `ti(:,:,:,1:7)`
- electron temperature: `te`
- parallel velocities / flows: `vsi`, possibly `vpi`

The local SAMI3 ion order previously confirmed in source is:

```text
H+, O+, NO+, O2+, He+, N2+, N+
```

## Next Action

Current restored baseline and next plan are archived here:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/MAGE_WACCMX_SAMI3_BASELINE_RESTORED_AND_VOLTRON_PLAN_20260523.md
```

Goal-mode Phase 1/2 interface contract is here:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/SAMI3_VOLTRON_MOMENTS_CONTRACT_20260523.md
```

## 2026-05-23 Update: WACCM-X -> SAMI3 Live Neutral Extraction P0

A copied CESM case now contains the first live neutral extraction/QC
implementation.  The original online-smoke case was left untouched.

Implementation copy:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523
```

Result note:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/WACCMX_SAMI3_LIVE_NEUTRAL_EXTRACTION_RESULT_20260523.md
```

Completed in the copy:

```text
cam_comp.F90 now calls wxsami3_cam_send(get_nstep(), dtime_phys, phys_state)
wxsami3_online_stub_mod.F90 can inspect CAM physics_state(:)
runtime constituent registry logs O, O2, H, N, NO, N2, He indices
runtime CAM column count, lat/lon coverage, and column-id range diagnostics
optional per-rank live phys_state snapshot dump via WXSAMI3_LIVE_DUMP_PREFIX
T/U/V/omega/pmid/zm/q min/max/bad diagnostics are available
q -> neutral number density cm^-3 diagnostics are available
N2 residual closure diagnostics are available
optional metadata sidecar can be written with WXSAMI3_META_FILE
```

Verification:

```text
wxsami3_online_stub_mod.F90 compiles to .mod/.o against the existing
GNU/OpenMPI CAM build products.

The modified cam_comp.F90 passes syntax/module checking against the new sender
module.
```

The live-dump replay payload builder compiles cleanly with:

```bash
module load intel/netcdf/4.7.4/gcc8.5.0_ompi5.0.3
gcc -O2 -Wall -Wextra $(nc-config --cflags) \
  /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/make_wxsami3_payload_from_live_dump.c \
  -o /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/make_wxsami3_payload_from_live_dump \
  $(nc-config --libs) -lm
```

The live-dump reader passes `python3 -m py_compile`.

Replay helper:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/read_wxsami3_live_dump.py
```

It can summarize rank-local dump files and optionally write a merged global
snapshot:

```bash
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/read_wxsami3_live_dump.py \
  '/path/to/wxsami3_physstate_rank*_pkt000000.bin' \
  --merged-npz /path/to/wxsami3_physstate_pkt000000_merged.npz
```

Replay payload builder:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/make_wxsami3_payload_from_live_dump.c
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/make_wxsami3_payload_from_live_dump
```

It converts all rank-local live CAM dump files into the existing staged
SAMI3 worker payload format:

```bash
module load intel/netcdf/4.7.4/gcc8.5.0_ompi5.0.3
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/make_wxsami3_payload_from_live_dump \
  '/path/to/wxsami3_physstate_rank*_pkt000000.bin' \
  /path/to/sami3_grid_dir \
  /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc \
  /path/to/replay_payload/waccmx_neutral_rank
```

If two dump patterns are provided, the first is written as the initial neutral
state and the second is appended as the final neutral state.  The output is:

```text
waccmx_neutral_rank0001.bin ... waccmx_neutral_rank0032.bin
```

Current replay policy:

```text
CAM cid -> matching ESMF source SCRIP column order
species dump order O,O2,H,N,NO,N2,He -> payload order H,O,NO,O2,He,N2,N
q/mbarv/pmid/T -> neutral number density cm^-3
U,V m/s -> cm/s
W = 0.0
He = -1.0 to keep the current SAMI3 native fallback policy
N2 = CAM N2 when finite, otherwise residual closure
invalid samples are marked invalid rather than silently floored
```

Historical caveat before the late runtime-builder update:

```text
At this earlier checkpoint, the actual SAMI3 transport path was still the
existing file-backed payload fallback.  That caveat was superseded later on
2026-05-23 by the copied f19 WXSAMI3_PAYLOAD_MODE=live runtime-packet smoke
recorded below.
```

Remaining blocker before calling it production live WACCM-X neutral forcing:

```text
The live-dump replay payload has been run on real CAM dump output, and the f19
runtime sender has also sent runtime-built live packets directly to SAMI3.
Receiver-side checksum comparison matches independent replay.  The remaining
blockers are formal schema/metadata, offline-vs-live source-time validation,
top/fallback policy, N2/He/W semantics, REMIX electrodynamics, and production
distributed remap scaling.
```

Additional evidence from the continuation work:

```text
CESM/SAMI3 live-dump smoke:
job       = 7640986
state     = COMPLETED
exit      = 0:0
elapsed   = 00:01:59
node      = qhcn078

Live dump:
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_dump_20260523_0000/live_dump
files     = 16 rank-local dump files
columns   = 13824 unique CAM cid values, no missing cid

Merged live dump:
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_dump_20260523_0000/live_dump/wxsami3_physstate_pkt000000_merged.npz

Matching f19 ESMF weights:
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc
source    = 144 x 96 = 13824 WACCM-X/CAM columns
dest      = 3618816 SAMI3 points

Replay payload:
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_replay_payload_from_live_dump_20260523/waccmx_neutral_rank0001.bin ... rank0032.bin
header    = 20260522, 304, 124, 5, 7
files     = 32
size      = 16586260 bytes each

Builder QC per initial/final block:
samples              = 6031360
invalid              = 1641376
above_live_top       = 1641376
N2 residual used     = 4389984
N2 residual negative = 178219
N2 residual min/max  = -0.053314608006139914 / 0.81297869253786992

Replay receiver checksum smoke:
job       = 7641159
state     = COMPLETED
exit      = 0:0
elapsed   = 00:01:00
evidence  = 32 WACCMX online neutral received markers + 32 WACCMX_RECV_QC markers + MASTER: All Done! + done signal received
compare   = WACCMX_RECV_QC compare ok: ranks=32 max_abs=2.1033e+06 max_rel=4.86991e-13
```

SAMI3 -> Voltron/RAIJU diagnostic adapter result is here:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/SAMI3_VOLTRON_RAIJU_MOMENTS_ADAPTER_RESULT_20260523.md
```

Physics review and revised next-step rules for the SAMI3 -> RAIJU/GAMERA
part are here:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/SAMI3_RAIJU_GAMERA_PHYSICS_REVIEW_20260523.md
```

Live-neutral-forcing plan for the WACCM-X -> SAMI3 part is here:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/WACCMX_SAMI3_LIVE_NEUTRAL_PLAN_20260523.md
```

Important route correction from this plan: the current WACCM-X -> SAMI3 path is
still an online MPI communication/control prototype with a file-backed staged
neutral payload.  It now has live CAM phys_state extraction/dump/replay
evidence, but it is not yet live WACCM-X neutral forcing.  The remaining
WACCM-X -> SAMI3 priority is:

```text
P0: promote live-dump replay mapping into distributed runtime sender packet build
P0: add payload schema, units, species order, timing, and checksum metadata to runtime path
P1: validate offline history/restart replay versus live extraction at the SAMI3 receiver
P1: make WACCM-X-top MSIS/HWM blending explicit
P1: add N2 residual, He native fallback, and W-off QC logging
P2: connect REMIX potential/E-field to SAMI3
```

Important route correction from this review: the current adapter should be
treated as a diagnostic/runtime scalar-moment adapter, not production physical
coupling.  The engineering hook is still the right path:

```text
packRaijuCoupler_RT
  -> tubeShell2RaiCpl
  -> applySami3RaiCplMoments
  -> raiCpl2RAIJU
```

Do not add more SAMI3 variables before the moment semantics are audited.  The
next priority is:

```text
P0: audit RAIJU/GAMERA semantics for Pavg/Davg/Pstd/Dstd/tiote
P1: extend stage-1 diagnostics with Davg_num, Davg_massEq, mu_eff,
    Pavg_i, Pavg_e, Pavg_total, species fractions, and deneu QC
P2: replace simple nz mean with flux-tube-volume weighting
P3: replace index-space resize with L/MLT/flux-tube geometry mapping
P4: add runtime alpha blending, floors, and per-component switches
```

Implementation was done only in the copied kaiju tree:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523
```

Current adapter implementation files:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/src/voltron/modelInterfaces/sami3MomentsAdapter.F90
```

The current smoke/validation command is:

```bash
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/scripts/sami3_moments/run_sami3_mage_moments_smoke.sh
```

The RAIJU runtime hook is default-off.  It is enabled only by adding this under
`Kaiju/RAIJU`:

```xml
<sami3Moments doIngest="true"
              file="/path/to/sami3_voltron_raiju_diag.h5"
              group="/RaiCplMomentsOnly"/>
```

The copied tree has also been configured and built through `voltron.x` here:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523
```

Build evidence:

```text
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/modules/sami3momentsadapter.mod
/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/bin/voltron.x
```

Historical cleanup note: do not continue the earlier accidental WACCM-X ->
SAMI3 live neutral-payload branch in the original online-smoke case or present
it as completed live forcing.  If WACCM-X -> SAMI3 live extraction is resumed,
keep it in a clearly named copy and preserve the file-backed smoke as the
control-path baseline.

The post-cleanup control-path baseline is the file-backed smoke:

```text
job       = 7632147
state     = COMPLETED
exit      = 0:0
elapsed   = 00:02:37
node      = qhcn062
mode      = file-backed waccmx_neutral_rank*.bin sender
```

Recommended next engineering step:

1. Keep `7532381` and `7632147` as the WACCM-X -> SAMI3 online MPI control-path baselines.
2. Use the new contract above as the source of truth for `SAMI3 -> Voltron/GAMERA plasma moments adapter`.
3. Use existing MAGE/Voltron moment fields as the integration target:
   `Pavg`, `Davg`, `Pstd`, `Dstd`, `tiote`.
4. Continue from the copied-tree runtime adapter, not the original `kaiju` tree:
   `/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523`.
5. Do not feed raw SAMI3 3-D arrays directly into GAMERA.
6. Do not alter GAMERA main equations until diagnostic moments have plausible units, ranges, masks, and spatial structure.

Latest copied-tree runtime result:

```text
Runtime smoke directory:
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_smoke_20260523

Runtime moments product:
/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_runtime_20260523.h5

Enabled XML:
runtime_ingest_smoke_20260523/tinyCase_sami3_moments.xml

Runtime proof:
model.log contains "SAMI3 moments ingest applied after RAIJU realtime pack" and "Fin".
Pavg/Davg/Pstd/Dstd in sami3_moments_smoke.raiCpl.Res.00000.h5 match the input
/RaiCplMomentsOnly arrays with max_abs_diff = 0.0.
```

Important implementation notes:

```text
src/base/io_xml_input.F90
  Set_Str now assigns the parsed XML string directly so absolute paths and
  groups beginning with "/" do not fall back to defaults.

src/base/types/volttypes.F90
  raijuCoupler_T stores default-off sami3Moments config.

src/voltron/modelInterfaces/raijuCplHelper.F90
  applySami3RaiCplMoments runs after tubeShell2RaiCpl and before raiCpl2RAIJU.

scripts/sami3_moments/sami3_moments_to_raiju_diag.py
  --raicpl-template / --target-raicpl-shape can write /RaiCplMomentsOnly in
  runtime ReadInSGV HDF5 order: (channel, j, i).
```

Useful verification commands:

```bash
sacct -j 7532381 --format=JobID,JobName%30,Partition,State,ExitCode,Elapsed,NNodes,NCPUS
grep -n "WXSAMI3\\|END OF MODEL RUN" /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000/slurm-7532381.out
grep -n "WACCMX online neutral received\\|WACCMX online done signal received\\|MASTER: All Done" /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000/sami3_online_receiver.out
```

## 2026-05-23 Late Update: f19 WACCM-X -> SAMI3 Runtime Live Packet Prototype

The WACCM-X -> SAMI3 live-neutral branch was resumed only in a copied f19 CESM
case:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523
```

The original online case remains the control-path source and was not edited:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_online
```

Current f19 grid and map artifacts:

```text
ATM_GRID = 1.9x2.5
lat,lon  = 96,144
columns  = 13824
weights  = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc
rt map   = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/wxsami3_runtime_map_f19_20260523.bin
```

SourceMod/runtime builder status:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523/SourceMods/src.cam/cam_comp.F90
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523/SourceMods/src.cam/wxsami3_online_stub_mod.F90
```

The CAM hook passes `phys_state(:)` into `wxsami3_cam_send`.  The sender now
supports:

```text
WXSAMI3_PAYLOAD_MODE=file
WXSAMI3_PAYLOAD_MODE=live
WXSAMI3_LIVE_MAP_FILE=/path/to/wxsami3_runtime_map_f19_20260523.bin
WXSAMI3_LIVE_DIAG=1
WXSAMI3_RECV_QC=1
```

Important implementation detail: runtime vertical interpolation no longer
clips all fields to nonnegative.  U/V can remain negative.  Only species
mixing ratios are clamped after interpolation when finite.

Build evidence:

```text
case.build --skip-provenance completed after live-mode edits
MODEL BUILD HAS FINISHED SUCCESSFULLY
```

Runtime live-payload smoke:

```text
job       = 7641509
node      = qhcn065
state     = COMPLETED
exit      = 0:0
elapsed   = 00:03:33
run dir   = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000
mode      = WXSAMI3_PAYLOAD_MODE=live
```

The previous runtime-live smoke was job `7641322`; job `7641509` repeated it
after adding `wxsami3-live-payload-v2` metadata and sender checksum output.

Key evidence:

```text
WXSAMI3 payload mode: live
WXSAMI3 live runtime map loaded: npoints,n_s,nsource=3618816,14475264,13824
WXSAMI3 live runtime packet QC samples,invalid,above_top=6031360,1641376,1641376
WXSAMI3 live runtime N2 residual used,negative,min,max=4389984,178219,-0.053314608006139914,0.81297869253786992
WXSAMI3 sent live neutral packet
WXSAMI3 sent done signal to SAMI3
WXSAMI3 disconnected from SAMI3
END OF MODEL RUN
WACCMX online neutral received lines = 32
WACCMX_RECV_QC lines = 32
MASTER: All Done!
WACCMX online done signal received: 1
WACCMX_RECV_QC compare ok: ranks=32 max_abs=2.1033e+06 max_rel=4.86991e-13
```

Metadata/checksum sidecar:

```text
file      = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/wxsami3_live_meta.json
version   = wxsami3-live-payload-v2
transport = runtime_live_packet
source_columns = 13824
payload_species_order = H,O,NO,O2,He,N2,N
source_species_order  = O,O2,H,N,NO,N2,He
sender valid_i/invalid_i = 4389984 / 1641376
sender valid_f/invalid_f = 4389984 / 1641376
sender checksum max relative difference versus replay aggregation = 6.933976640448014e-14
```

File-mode fallback regression after the same sender changes:

```text
job       = 7641512
node      = qhcn423
state     = COMPLETED
exit      = 0:0
elapsed   = 00:02:42
run dir   = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_file_payload_f19_regression_20260524_0000
mode      = WXSAMI3_PAYLOAD_MODE=file
compare   = WACCMX_RECV_QC compare ok: ranks=32 max_abs=1.38854e+06 max_rel=3.26946e-13
```

The independent replay used for the checksum was generated from the same
runtime live dump:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/live_dump
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/replay_from_runtime_dump/waccmx_neutral_rank*.bin
```

Current honest classification:

```text
f19 online runtime live neutral-packet prototype, checksum-smoked against
independent replay, with live-payload-v2 metadata/schema sidecar and
two-packet clean transport/cadence smoke.  Not yet production live WACCM-X
neutral forcing.
```

Remaining blockers before production wording:

```text
offline history/restart replay versus live extraction at the same source time
explicit WACCM-X-top blending or SAMI3-native fallback policy
N2 residual and He fallback policy hardening
longer-run cadence/time-interpolation validation beyond the two-packet smoke
REMIX -> SAMI3 potential/E-field
distributed remap design for f09/finer production scaling
```

Next WACCM-X -> SAMI3 task:

```text
Harden the f19 live runtime prototype: run strict same-source-time
offline-vs-live comparison, then make top/fallback policy explicit.
```

## Late Update 2026-05-24 00:36 CST

P1 validation was advanced without modifying the original CESM online-smoke
case.

New source-state comparison helper:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/compare_wxsami3_live_dump_to_cam_nc.c
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/compare_wxsami3_live_dump_to_cam_nc
```

Comparison artifacts:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/live_vs_rh0_00000_compare.txt
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/live_vs_rh0_00300_compare.txt
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/live_vs_restart_00300_compare.txt
```

Confirmed:

```text
f19 live dump cid -> CAM lat/lon ordering matches to roundoff
lat max_abs = 1.4210854715202004e-14
lon max_abs = 5.6843418860808015e-14
```

The `rh0.2005-12-31-00300` comparison is a useful source-state sanity check,
but not a strict acceptance test because the compared history variables are
`cell_methods=time: mean`.  The `rh0.2005-12-31-00000` file has valid
coordinates but zero 3-D fields in this run, so it is coordinate-only for this
purpose.  Restart comparison can use `--species-mode mass`, but remains a loose
sanity check unless a live dump is taken at the same restart source time.

Important finding:

```text
live physics_state%ps range       = about 855..1610 Pa
CAM history/restart PS range      = surface-pressure scale, about 5.8e4..1.08e5 Pa
runtime payload density uses pmid = yes
runtime payload uses state%ps     = no
```

So `PS` should not be advertised as a validated live forcing variable yet.
Audit `physics_state%ps` semantics before putting it into the formal data
contract.

The SAMI3 receiver fallback policy was made explicit in logs:

```text
WACCMX neutral apply policy: negative H density marker retains native SAMI3 neutral state
WACCMX neutral apply policy: He payload is ignored; SAMI3 native He is retained
```

Rebuilt SAMI3 receiver:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/work/sami3-3.22_online_mpi_openmpi/sami3.x
```

Regression after fallback-log change:

```text
job       = 7641538
node      = qhcn112
state     = COMPLETED
exit      = 0:0
elapsed   = 00:02:59
mode      = WXSAMI3_PAYLOAD_MODE=file
compare   = WACCMX_RECV_QC compare ok: ranks=32 max_abs=1.38854e+06 max_rel=3.26946e-13
```

Next recommended step:

```text
Use the compare helper only on a genuinely matching history/restart/live
source time.  Do not treat rh0 time-mean files as strict runtime phys_state
snapshots.
```

## Late Update 2026-05-24 01:03 CST

The copied CAM sender now has explicit send lifetime/cadence controls:

```text
WXSAMI3_MAX_PACKETS
WXSAMI3_SEND_EVERY_NSTEPS
```

Implementation path:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523/SourceMods/src.cam/wxsami3_online_stub_mod.F90
```

Defaults preserve previous behavior:

```text
WXSAMI3_MAX_PACKETS=-1
WXSAMI3_SEND_EVERY_NSTEPS=1
```

The multipacket smoke script sets `WXSAMI3_MAX_PACKETS=2` and temporarily
patches copied-run `nuopc.runconfig` from `stop_n=300` to `stop_n=600`,
restoring it on exit.

Verified clean run:

```text
script    = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/run_waccmx_cam_sami3_live_payload_f19_multipacket_20260524.sbatch
run dir   = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_multipacket_20260524_0000
job       = 7641573
node      = qhcn163
state     = COMPLETED
exit      = 0:0
elapsed   = 00:04:16
```

Sender/receiver lifecycle evidence:

```text
WXSAMI3 sent live neutral packet: nstep,packet_hour,count=0,0.0,0
WXSAMI3 sent live neutral packet: nstep,packet_hour,count=1,0.0833333358,1
WXSAMI3 max packets reached; skipping further sends: 2,2
WXSAMI3 sent done signal to SAMI3
WXSAMI3 disconnected from SAMI3
******* END OF MODEL RUN *******
MASTER: All Done!
WACCMX online done signal received: 2
```

Independent replay/QC comparisons:

```text
pkt000000 = WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.1033e+06 max_rel=4.86991e-13
pkt000001 = WACCMX_RECV_QC compare ok: ranks=32 occurrence=1 step_set=[1] packet_hour_set=[0.0833333358] max_abs=2.70899e+06 max_rel=6.80359e-13
```

File-mode fallback was rerun with the same rebuilt CESM executable after the
cadence/max-packet sender controls:

```text
job       = 7641579
node      = qhcn163
state     = COMPLETED
exit      = 0:0
elapsed   = 00:02:25
mode      = WXSAMI3_PAYLOAD_MODE=file
defaults  = WXSAMI3_MAX_PACKETS=-1, WXSAMI3_SEND_EVERY_NSTEPS=1
compare   = WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=1.38854e+06 max_rel=3.26946e-13
```

Post-run sanity:

```text
/home/jiaoy_group/jiaoy/data/CESM/case_output_root_online_live_neutral_20260523/mage_qpx2000_f19_sami3_live_neutral_20260523/run/nuopc.runconfig
stop_n = 300
```

Updated next recommended step:

```text
Do not add more neutral variables next.  Move to strict same-source-time
offline-vs-live source-state validation and explicit WACCM-X-top fallback or
blending policy.  Longer cadence/time-interpolation validation remains needed
before any production neutral-forcing wording.
```
