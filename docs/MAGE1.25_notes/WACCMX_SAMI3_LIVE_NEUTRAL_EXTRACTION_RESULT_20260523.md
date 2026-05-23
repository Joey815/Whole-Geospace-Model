# WACCM-X -> SAMI3 Live Neutral Extraction Result (2026-05-23)

This note records the first goal-mode implementation step after the
WACCM-X -> SAMI3 route review.  The work was done in a copied CESM case, not
in the original online-smoke case.

## Work Copy

Original case left intact:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_online
```

Implementation copy:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523
```

The copied case was reset and rebuilt with a temporary CIME HOME/Python shim,
so the original online-smoke case remains untouched.

```text
case.setup --reset: completed in the copied case
case.build --skip-provenance: completed
BUILD_COMPLETE: TRUE
```

## What Was Implemented

The CAM online sender now accepts runtime CAM physics state:

```fortran
call wxsami3_cam_send(get_nstep(), dtime_phys, phys_state)
```

and the sender module can perform a live neutral extraction diagnostic from
`physics_state(:)` when enabled.

Modified files:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523/SourceMods/src.cam/cam_comp.F90
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523/SourceMods/src.cam/wxsami3_online_stub_mod.F90
```

Runtime fields audited/extracted from `physics_state(:)`:

```text
lat    = state%lat     [radians, logged as degrees]
lon    = state%lon     [radians, logged as degrees]
cid    = state%cid     [CAM unique column id]
T      = state%t       [K]
U      = state%u       [m/s]
V      = state%v       [m/s]
OMEGA  = state%omega   [Pa/s], diagnostic only
PMID   = state%pmid    [Pa]
ZM     = state%zm      [m]
q      = state%q       [mass mixing ratio]
```

Constituent registry:

```text
O, O2, H, N, NO, N2, He
```

The code calls `cnst_get_ind(..., abort=.false.)`, logs present/missing
species, and records CAM constituent name/type/molecular weight when present.

Number-density diagnostic:

```text
n_cm3 = q * mbarv / species_mw * pmid / (kB * T) * 1e-6
```

where `mbarv` is taken from CAM `air_composition`.  This matches the WACCM-X
internal conversion pattern used around `ion_electron_temp.F90`.

## Runtime Controls

Existing file-backed controls remain:

```text
WXSAMI3_PORT_FILE
WXSAMI3_PAYLOAD_PREFIX
WXSAMI3_NUMWORKERS
WXSAMI3_SKIP_DISCONNECT
```

New optional/live controls:

```text
WXSAMI3_PAYLOAD_MODE=file|live
WXSAMI3_LIVE_MAP_FILE=/path/to/wxsami3_runtime_map_*.bin
WXSAMI3_LIVE_DIAG=1
WXSAMI3_META_FILE=/path/to/wxsami3_live_meta.json
WXSAMI3_LIVE_DUMP_PREFIX=/path/to/wxsami3_physstate_
WXSAMI3_LIVE_DUMP_MAX=1
WXSAMI3_MAX_PACKETS=-1
WXSAMI3_SEND_EVERY_NSTEPS=1
```

`WXSAMI3_PAYLOAD_MODE=file` keeps the existing file-backed payload path.
`WXSAMI3_PAYLOAD_MODE=live` builds SAMI3 worker payload arrays directly from
current CAM `physics_state(:)` in the copied f19 sender.  `WXSAMI3_LIVE_DIAG`
adds the live CAM physics column count, lat/lon coverage, column-id range,
state min/max/bad counts, constituent registry, species q statistics,
converted neutral number-density statistics, and N2 residual diagnostics.

With `WXSAMI3_LIVE_DUMP_PREFIX` set, every CAM MPI rank writes its local
`physics_state(:)` columns for the first `WXSAMI3_LIVE_DUMP_MAX` packets.  The
dump is intentionally distributed by rank; it does not pretend that the root
rank owns the full CAM state.

`WXSAMI3_MAX_PACKETS` and `WXSAMI3_SEND_EVERY_NSTEPS` control runtime send
lifetime and cadence.  The default `max_packets=-1` preserves the previous
unlimited behavior; the f19 two-packet smoke uses `WXSAMI3_MAX_PACKETS=2` so
CESM can continue to finalize after SAMI3 has consumed the intended packets.

Dump file pattern:

```text
${WXSAMI3_LIVE_DUMP_PREFIX}rankXXXX_pktYYYYYY.bin
${WXSAMI3_LIVE_DUMP_PREFIX}meta.json
```

Dump contents:

```text
header, dtime_phys, species_indices,
cid, lchnk, local column index,
lat_deg, lon_deg, ps,
profile(T, U, V, omega, pmid, zm, mbarv),
qprof(O, O2, H, N, NO, N2, He)
```

Reader/check script:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/read_wxsami3_live_dump.py
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/compare_wxsami3_recv_qc.py
```

Example:

```bash
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/read_wxsami3_live_dump.py \
  '/path/to/wxsami3_physstate_rank*_pkt000000.bin'
```

To build a single replay input from all rank-local dumps:

```bash
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/read_wxsami3_live_dump.py \
  '/path/to/wxsami3_physstate_rank*_pkt000000.bin' \
  --merged-npz /path/to/wxsami3_physstate_pkt000000_merged.npz
```

The merged NPZ is sorted by CAM `cid` when available and carries:

```text
cid, lchnk, col, lat_deg, lon_deg, ps_pa,
profile(pver, ncol, field),
qprof(pver, ncol, species),
profile_names, species, species_indices
```

Replay payload builder:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/make_wxsami3_payload_from_live_dump.c
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/make_wxsami3_payload_from_live_dump
```

Runtime-map packer for the f19 live sender:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/pack_wxsami3_runtime_map.c
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/pack_wxsami3_runtime_map
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/wxsami3_runtime_map_f19_20260523.bin
```

Runtime-map header:

```text
magic=20260524 version=1 nz=304 nf=124 nlt=96 npoints=3618816
n_s=14475264 nsource=13824
```

This converts distributed live CAM dump files back into the already validated
file-backed SAMI3 worker payload format:

```text
waccmx_neutral_rank0001.bin ... waccmx_neutral_rank0032.bin
```

Example:

```bash
module load intel/netcdf/4.7.4/gcc8.5.0_ompi5.0.3
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/make_wxsami3_payload_from_live_dump \
  '/path/to/wxsami3_physstate_rank*_pkt000000.bin' \
  /path/to/sami3_grid_dir \
  /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc \
  /path/to/replay_payload/waccmx_neutral_rank
```

With two dump patterns, the first pattern becomes the initial block and the
second pattern becomes the final block appended to each worker payload:

```bash
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/make_wxsami3_payload_from_live_dump \
  '/path/to/wxsami3_physstate_rank*_pkt000000.bin' \
  '/path/to/wxsami3_physstate_rank*_pkt000001.bin' \
  /path/to/sami3_grid_dir \
  /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc \
  /path/to/replay_payload/waccmx_neutral_rank
```

Current replay policy:

```text
CAM cid is treated as 1-based FV global column id compatible with the source
SCRIP order used by the matching ESMF weights.
The 20231013 288x192 weights are not valid for this f19 live case; a new
144x96 source SCRIP and matching weight file were generated under
`runs/esmf_regrid_f19_live_20260523`.
dump species order: O, O2, H, N, NO, N2, He
payload neutral order: H, O, NO, O2, He, N2, N
q/pmid/T/mbarv -> number density in cm^-3
U,V are converted from m/s to cm/s
W is held at 0.0
He is held at -1.0 to preserve the current SAMI3-native fallback policy
N2 uses the CAM N2 field when finite, otherwise residual closure
NaN/missing source columns or invalid samples are not silently converted to
valid floors
```

This builder is now both an offline replay/validation layer and the reference
implementation used to validate the f19 runtime sender.  The runtime sender
uses the prepacked runtime map and gathers distributed CAM state to root for
the current f19 smoke.  That gather-to-root design is acceptable for f19
prototype verification, not yet a production f09/finer-grid distributed remap.

The older metadata file from the extraction-only phase explicitly said:

```text
actual_transport = file_backed_payload_fallback
runtime_source   = CAM phys_state(:)
```

That statement applied before the runtime builder was added.  The copied f19
sender now supports `WXSAMI3_PAYLOAD_MODE=live`, where the payload sent to
SAMI3 is generated from current CAM state.

## Verification

The copied CESM case builds and runs:

```text
job       = 7640986
state     = COMPLETED
exit      = 0:0
elapsed   = 00:01:59
node      = qhcn078
```

The first live-dump smoke failed in job `7640983` with a segfault in
`wxsami3_dump_live_state`.  The cause was an incorrect `mbarv` third index:
the dump code used the assumed-shape `state(:)` loop index instead of the real
CAM chunk id.  The fixed code now uses:

```text
chunk_id = state(lchnk)%lchnk
mbarv(i,k,chunk_id)
```

The successful run wrote 16 rank-local live dump files:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_dump_20260523_0000/live_dump
```

Live dump summary:

```text
files=16 ranks=16 total_cols=13824
cid min/max/missing/unique = 1/13824/0/13824
lat range = -90.0 .. 90.0 deg
lon range = 0.0 .. 357.5 deg
T range   = 113.19272490765026 .. 1522.7628810979916 K
U range   = -925.7242161594645 .. 769.7344197674036 m/s
V range   = -845.8062460574145 .. 736.3650929706123 m/s
PMID range = 4.055140885992663e-08 .. 107321.3890267048 Pa
ZM range   = 48.56266690499009 .. 720507.7580399793 m
N2 and He were not direct CAM constituents in this run.
```

The merged live dump artifact is:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_dump_20260523_0000/live_dump/wxsami3_physstate_pkt000000_merged.npz
```

Matching f19 ESMF weights were generated here:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/waccmx_source_scrip.nc
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/sami3_dest_scrip.nc
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc
```

The f19 source SCRIP is `144 x 96 = 13824` source points.  This is why the old
`esmf_regrid_full_20231013/weights_bilinear_full.nc` file is not valid for
this run: it was built from a `288 x 192 = 55296` source grid.

The replay payload builder compiles cleanly with the local NetCDF C module:

```bash
module load intel/netcdf/4.7.4/gcc8.5.0_ompi5.0.3
gcc -O2 -Wall -Wextra $(nc-config --cflags) \
  /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/make_wxsami3_payload_from_live_dump.c \
  -o /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/make_wxsami3_payload_from_live_dump \
  $(nc-config --libs) -lm
```

The reader script passes Python compile checking:

```text
read_wxsami3_live_dump.py py_compile ok
```

One compile-time issue was found and fixed during verification:

```text
wrong: use physconst, only: mbarv
right: use air_composition, only: mbarv
```

The check is now `allocated(mbarv)`, because CAM declares `mbarv` as an
allocatable in `air_composition`.

Live-dump replay payload generated successfully:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_replay_payload_from_live_dump_20260523/waccmx_neutral_rank0001.bin
...
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_replay_payload_from_live_dump_20260523/waccmx_neutral_rank0032.bin
```

Replay payload structural check:

```text
file count = 32
per-file size = 16586260 bytes
header = 20260522, 304, 124, 5, 7
nonfinite count = 0 for denni/tni/ui/vi/wi/dennf/tnf/uf/vf/wf
valid initial samples = 4389984
invalid initial samples = 1641376
valid final samples = 4389984
invalid final samples = 1641376
```

Builder QC for the successful replay payload:

```text
samples per block = 6031360
invalid per block = 1641376
above_live_top per block = 1641376
N2 residual used per block = 4389984
N2 residual negative per block = 178219
N2 residual min = -0.053314608006139914
N2 residual max = 0.81297869253786992
```

Receiver-side online smoke with the replay payload:

```text
job       = 7641159
node      = qhcn025
state     = COMPLETED
exit      = 0:0
elapsed   = 00:01:00
evidence  = 32 worker payloads received; MASTER: All Done!; done signal received
```

Receiver-side checksum/QC was enabled with `WXSAMI3_RECV_QC=1` and compared
against the replay payload binaries:

```text
NEUTRAL_SENDER sent step=0 packet_hour=0 rank=0001 ... rank=0032
NEUTRAL_SENDER sent done signal
NEUTRAL_SENDER done
WACCMX online neutral received: taskid,step,packet_hr= 1..32, 0, 0.0
WACCMX_RECV_QC lines = 32
MASTER: All Done!
WACCMX online done signal received: 1
WACCMX_RECV_QC compare ok: ranks=32 max_abs=2.1033e+06 max_rel=4.86991e-13
no header mismatch / fatal / forrtl / NaN / Abort markers
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

The first runtime-live smoke was job `7641322`; job `7641509` repeated it after
the metadata/checksum hardening.

Runtime sender markers:

```text
WXSAMI3 payload mode: live
WXSAMI3 live runtime map loaded: npoints,n_s,nsource=3618816,14475264,13824
WXSAMI3 live runtime packet QC samples,invalid,above_top=6031360,1641376,1641376
WXSAMI3 live runtime N2 residual used,negative,min,max=4389984,178219,-0.053314608006139914,0.81297869253786992
WXSAMI3 sent live neutral packet: nstep,packet_hour,count=0,0.0,0
WXSAMI3 sent done signal to SAMI3
WXSAMI3 disconnected from SAMI3
END OF MODEL RUN
```

Runtime receiver and independent replay comparison:

```text
WACCMX online neutral received lines = 32
WACCMX_RECV_QC lines = 32
MASTER: All Done!
WACCMX online done signal received: 1
WACCMX_RECV_QC compare ok: ranks=32 max_abs=2.1033e+06 max_rel=4.86991e-13
no header mismatch / fatal / forrtl / NaN / Abort markers
```

Runtime metadata/checksum sidecar:

```text
file      = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/wxsami3_live_meta.json
version   = wxsami3-live-payload-v2
transport = runtime_live_packet
map source columns = 13824
payload species order = H,O,NO,O2,He,N2,N
source species order  = O,O2,H,N,NO,N2,He
sender valid_i/invalid_i = 4389984 / 1641376
sender valid_f/invalid_f = 4389984 / 1641376
sender sum_denni = 1.4035374655329847e20
```

Metadata sender checksum versus independent replay aggregation:

```text
valid/invalid counts match exactly
max relative sum difference = 6.933976640448014e-14
```

File-mode fallback regression after the shared sender changes:

```text
job       = 7641512
node      = qhcn423
state     = COMPLETED
exit      = 0:0
elapsed   = 00:02:42
run dir   = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_file_payload_f19_regression_20260524_0000
mode      = WXSAMI3_PAYLOAD_MODE=file
```

File-mode regression evidence:

```text
WXSAMI3 payload mode: file
WXSAMI3 sent neutral packet: nstep,packet_hour,count=0,0.0,0
WXSAMI3 sent done signal to SAMI3
WXSAMI3 disconnected from SAMI3
END OF MODEL RUN
WACCMX online neutral received lines = 32
WACCMX_RECV_QC lines = 32
WACCMX_RECV_QC compare ok: ranks=32 max_abs=1.38854e+06 max_rel=3.26946e-13
```

## 2026-05-24 P1 Source-State And Fallback Checks

A source-state comparison helper was added and built:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/scripts/compare_wxsami3_live_dump_to_cam_nc.c
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/compare_wxsami3_live_dump_to_cam_nc
```

It reads the rank-local live dump directly and compares against CAM NetCDF
history/restart files on the f19 `cid -> lat/lon` ordering.  For CAM history
species it uses:

```text
q_mass * mbarv / species_mw -> mol/mol
```

For restart/internal fields it can compare raw mass mixing ratio with:

```text
--species-mode mass
```

Output files from the first checks:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/live_vs_rh0_00000_compare.txt
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/live_vs_rh0_00300_compare.txt
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/live_vs_restart_00300_compare.txt
```

The comparison confirms that the f19 column mapping is correct:

```text
lat max_abs = 1.4210854715202004e-14
lon max_abs = 5.6843418860808015e-14
```

The `rh0.2005-12-31-00300` history file gives a useful but not bitwise
source-state sanity check because its variables have `cell_methods =
"time: mean"`.  Selected differences versus the nstep=0 live dump:

```text
T_K rms_abs       = 3.6028797635341383 K
MBARV rms_abs     = 0.010570742291359323 g/mole
O mol/mol rms_abs = 0.00084473530148310605
O2 mol/mol rms_abs = 0.00030527141914284996
H mol/mol rms_abs = 6.1457260142467061e-05
N mol/mol rms_abs = 9.9449049979920596e-05
NO mol/mol rms_abs = 3.3801448697315371e-06
```

The `rh0.2005-12-31-00000` file is not a useful physical state comparison for
the live dump; the compared 3-D history variables are zero while lat/lon are
valid.  Treat it as a coordinate-only check.

The restart file at `2005-12-31-00300` can be used only as a loose sanity
check, not an equal-source-time validation against the nstep=0 live dump.  Raw
restart/internal species comparison is available with `--species-mode mass`.

Important caveat: `state%ps` in the live dump is around `855..1610 Pa`, while
CAM history/restart `PS` is around `5.8e4..1.08e5 Pa`.  The current runtime
payload does not use `state%ps`; density conversion uses `pmid`.  Do not use
`PS` as a payload acceptance criterion until the `physics_state%ps` semantics
for this WACCM-X configuration are audited.

The SAMI3 receiver fallback policy was made explicit in the runtime log:

```text
WACCMX neutral apply policy: negative H density marker retains native SAMI3 neutral state
WACCMX neutral apply policy: He payload is ignored; SAMI3 native He is retained
```

This documents the existing behavior in `waccmx_apply_neutambt`: negative H
density markers skip the WACCM-X overwrite for that grid point, preserving the
native SAMI3 neutral state.  He is never overwritten from the payload.

After this receiver-side log addition, the copied-path file-mode regression was
rerun:

```text
job       = 7641538
node      = qhcn112
state     = COMPLETED
exit      = 0:0
elapsed   = 00:02:59
compare   = WACCMX_RECV_QC compare ok: ranks=32 max_abs=1.38854e+06 max_rel=3.26946e-13
```

The independent replay for this comparison was generated from the live dump
written during the same runtime-live job:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/live_dump
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/replay_from_runtime_dump/waccmx_neutral_rank*.bin
```

Two replay-smoke issues were fixed while adding this validation:

```text
scripts/wxsami3_neutral_sender_stub.c now sends tag_done=299.
The C sender sends the done signal to SAMI3 ranks 0..32 so the receiver
finalize path exits naturally.
```

## 2026-05-24 Multi-Packet Cadence/Termination Smoke

A first unrestricted two-packet attempt proved that the runtime payload content
was valid for packets 0 and 1, but also exposed a lifecycle bug: if CESM tries
to send another packet after SAMI3 has reached `MASTER: All Done!`, the sender
can block.  The copied CAM sender was therefore hardened with:

```text
WXSAMI3_MAX_PACKETS
WXSAMI3_SEND_EVERY_NSTEPS
```

The f19 multipacket smoke script sets:

```text
WXSAMI3_MAX_PACKETS=2
WXSAMI3_SEND_EVERY_NSTEPS=1
```

and temporarily patches the copied CESM run `nuopc.runconfig` from
`stop_n=300` to `stop_n=600`, restoring it on exit.

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

Sender lifecycle evidence:

```text
WXSAMI3 sent live neutral packet: nstep,packet_hour,count=0,0.0,0
WXSAMI3 sent live neutral packet: nstep,packet_hour,count=1,0.0833333358,1
WXSAMI3 max packets reached; skipping further sends: 2,2
WXSAMI3 sent done signal to SAMI3
WXSAMI3 disconnected from SAMI3
******* END OF MODEL RUN *******
```

Receiver evidence:

```text
WACCMX online neutral received: taskid=1..32, step=0, packet_hr=0.0
WACCMX online neutral received: taskid=1..32, step=1, packet_hr=0.0833333358
MASTER: All Done!
WACCMX online done signal received: 2
```

Independent replay/QC comparisons:

```text
pkt000000 = WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.1033e+06 max_rel=4.86991e-13
pkt000001 = WACCMX_RECV_QC compare ok: ranks=32 occurrence=1 step_set=[1] packet_hour_set=[0.0833333358] max_abs=2.70899e+06 max_rel=6.80359e-13
```

The copied run file was restored after the smoke:

```text
/home/jiaoy_group/jiaoy/data/CESM/case_output_root_online_live_neutral_20260523/mage_qpx2000_f19_sami3_live_neutral_20260523/run/nuopc.runconfig
stop_n = 300
```

File-mode fallback was then rerun with the same rebuilt CESM executable after
the cadence/max-packet controls were added.  The file-mode script does not set
the new controls, so it exercises the defaults:

```text
WXSAMI3_PAYLOAD_MODE=file
WXSAMI3_MAX_PACKETS=-1
WXSAMI3_SEND_EVERY_NSTEPS=1
job       = 7641579
node      = qhcn163
state     = COMPLETED
exit      = 0:0
elapsed   = 00:02:25
compare   = WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=1.38854e+06 max_rel=3.26946e-13
```

## Current Classification

Completed in this step:

```text
CAM phys_state(:) is passed into the WACCM-X -> SAMI3 sender hook
runtime CAM column count / lat / lon / column-id diagnostics exist
distributed per-rank live phys_state snapshot dump exists
Python 3.6-compatible dump reader/summary/merge script exists
live-dump-to-file-backed-payload replay builder exists
runtime constituent index registry exists
T/U/V/omega/pmid/zm/q diagnostics exist
q -> neutral number-density diagnostics exist
N2 residual QC exists
metadata sidecar writer exists
file-backed payload fallback remains intact at compile/interface level
matching f19 SCRIP/ESMF weights exist for this live case
live dump was converted into 32 SAMI3 worker replay payload files
SAMI3 online receiver consumed the replay payload in a smoke run
receiver-side replay checksums match the replay payload
runtime-map binary exists for the f19 live sender
WXSAMI3_PAYLOAD_MODE=live builds packets from current CAM phys_state(:)
SAMI3 online receiver consumed runtime-built live packets
runtime-live receiver checksums match independent replay from the same CAM dump
wxsami3-live-payload-v2 metadata sidecar records map, units, species order,
fallback policy, runtime QC, and sender checksum
sender checksum in metadata matches independent replay aggregation
file-mode fallback still works after live-mode metadata/checksum changes
offline source-state comparison tool exists and confirms f19 cid/lat/lon mapping
SAMI3 receiver now logs the native-fallback and He-native policy explicitly
WXSAMI3_MAX_PACKETS and WXSAMI3_SEND_EVERY_NSTEPS control sender lifetime/cadence
f19 live mode completed a two-packet clean lifecycle smoke with done/disconnect
file-mode fallback still passes with the cadence/max-packet-capable sender
```

Still not completed:

```text
strict equal-source-time offline history/restart replay versus live extraction
WACCM-X-top blending is not yet encoded in the runtime sender
vertical wind W is still intentionally not sent
REMIX -> SAMI3 potential/E-field remains unimplemented
longer-run cadence/time-interpolation behavior beyond the two-packet smoke is untested
f09/finer production scaling still needs a distributed-remap design
```

Therefore the honest status is:

```text
f19 live CAM neutral extraction/QC prototype implemented;
f19 runtime live packet builder implemented and checksum-smoked;
f19 live metadata/schema sidecar implemented and checksum-smoked;
file-mode fallback regression passed after the shared sender changes;
two-packet f19 live transport/cadence smoke passed with clean done/disconnect;
file-mode fallback regression also passed after cadence/max-packet controls;
final production live WACCM-X neutral forcing is still blocked by
strict same-source-time replay, top-boundary blending policy, N2/He/W semantics,
REMIX electrodynamic consistency, and production remap scaling.
```

## Next Goal

The next implementation target should harden the live prototype, not add more
variables:

```text
1. Compare offline history/restart replay and live extraction at the same
   source time.
2. Encode explicit WACCM-X-top blending or SAMI3-native fallback behavior.
3. Tighten N2 residual logging and keep He native/MSIS until separately
   validated.
4. Extend cadence/time-interpolation validation beyond the two-packet transport
   smoke when moving to longer runs.
5. Only after those checks, call the path production live WACCM-X neutral
   forcing.
```
