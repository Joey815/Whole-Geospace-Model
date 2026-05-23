# WACCM-X -> SAMI3 Live Neutral Forcing Plan (2026-05-23)

This note absorbs the 2026-05-23 route review for the WACCM-X -> SAMI3
neutral-forcing track.  It records the current boundary between the proven
online control path and the still-missing live physical neutral forcing.

## 2026-05-23 f19 Update

The active continuation branch is the copied f19 case:

```text
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523
```

Current grid:

```text
ATM_GRID = 1.9x2.5
lat,lon  = 96,144
columns  = 13824
```

The current plan intentionally stays on f19 until the live sender path is
closed.  The older `288 x 192` ESMF weights are not valid for this f19 case.
The matching f19 weights are:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc
```

New evidence completed after the original plan:

```text
live CAM phys_state(:) extraction and distributed rank-local dump completed
f19 source SCRIP and f19->SAMI3 weights generated
live dump converted into 32 SAMI3 worker replay payload files
SAMI3 online receiver consumed the replay payload
receiver-side WXSAMI3_RECV_QC checksum comparison matches replay payload
f19 runtime live packet builder completed in the copied CAM sender
SAMI3 online receiver consumed runtime-built live packets
runtime-live receiver QC matches independent replay built from the same CAM dump
live-packet metadata sidecar upgraded to wxsami3-live-payload-v2
sender-side checksum/QC in metadata matches independent replay aggregation
file-mode fallback regression passed after live-mode metadata/checksum hardening
offline source-state comparison helper added for live dump versus CAM NetCDF
f19 cid/lat/lon ordering confirmed against CAM history/restart grids
SAMI3 receiver fallback policy logged explicitly at runtime
sender lifetime/cadence controls added with WXSAMI3_MAX_PACKETS and
WXSAMI3_SEND_EVERY_NSTEPS
two-packet f19 live-mode transport/cadence smoke completed with clean done and
disconnect
file-mode fallback rerun after cadence/max-packet controls still passed
```

Key smoke results:

```text
CESM/SAMI3 live dump job      = 7640986, COMPLETED, 0:0
Replay receiver checksum job = 7641159, COMPLETED, 0:0
Receiver compare             = WACCMX_RECV_QC compare ok, ranks=32
Runtime live-payload job      = 7641322, COMPLETED, 0:0
Runtime live compare          = WACCMX_RECV_QC compare ok, ranks=32, max_rel=4.86991e-13
Metadata/checksum rerun job   = 7641509, COMPLETED, 0:0
Metadata version              = wxsami3-live-payload-v2, actual_transport=runtime_live_packet
File-mode regression job      = 7641512, COMPLETED, 0:0
File-mode compare             = WACCMX_RECV_QC compare ok, ranks=32, max_rel=3.26946e-13
Fallback-log regression job   = 7641538, COMPLETED, 0:0
Two-packet live smoke job      = 7641573, COMPLETED, 0:0
Packet 0 replay compare        = WACCMX_RECV_QC compare ok, occurrence=0, max_rel=4.86991e-13
Packet 1 replay compare        = WACCMX_RECV_QC compare ok, occurrence=1, max_rel=6.80359e-13
Post-cadence file-mode job     = 7641579, COMPLETED, 0:0
Post-cadence file compare      = WACCMX_RECV_QC compare ok, occurrence=0, max_rel=3.26946e-13
```

## Current Classification

The current WACCM-X -> SAMI3 work should be described as:

```text
online MPI communication/runtime-control prototype with live CAM extraction,
f19 runtime neutral-packet generation, offline replay mapping, and
receiver-side checksum validation, plus two-packet cadence/done validation
```

It should not yet be described as:

```text
live WACCM-X neutral forcing
```

The reason for this wording is that the f19 runtime builder is now online and
checksum-verified, but the physical forcing contract still needs the
strict same-source-time replay, explicit top blending semantics, composition
closure policy, and electrodynamic consistency work before the result should be
used as production neutral forcing.

Already proven:

```text
CESM/WACCM-X sender SourceMod
MPI_Comm_connect / MPI intercommunicator path
file-backed neutral payload send
SAMI3 online receiver
worker-rank payload distribution
done tag and clean disconnect
two-executable smoke completion
CAM/WACCM-X runtime phys_state(:) extraction diagnostics
runtime constituent-index lookup and validation
distributed live phys_state(:) dump
f19 CAM/SAMI3 replay mapping
receiver-side replay checksum validation
f19 gather-to-root runtime packet builder
WXSAMI3_PAYLOAD_MODE=live packet transport
runtime-live receiver checksum validation against independent replay
live-packet metadata sidecar with units, species order, fallback policy, and sender checksum
file-mode fallback regression after shared sender changes
sender max-packet/cadence controls and clean two-packet done/disconnect smoke
file-mode fallback regression after sender max-packet/cadence controls
```

Still missing for live physical forcing:

```text
strict same-source-time history/restart replay versus live extraction validation
explicit WACCM-X-top blending with SAMI3 native MSIS/HWM
REMIX potential/E-field forcing into SAMI3
longer-run cadence/time-interpolation validation beyond the two-packet smoke
```

## Correct Bridge Decomposition

Keep the overall architecture split into separate, testable bridges:

```text
WACCM-X/CAM -> SAMI3 neutral forcing
REMIX -> SAMI3 potential/E-field
SAMI3 -> Voltron/RAIJU/GAMERA scalar plasma moments
WACCM-X <-> MAGE/REMIX conductance/forcing
```

This boundary is important:

```text
WACCM-X -> SAMI3: neutral composition, neutral temperature, neutral winds
REMIX -> SAMI3: high-latitude potential / E-field / convection
SAMI3 -> MAGE: scalar plasma moments through Voltron/RAIJU first
```

Do not merge neutral forcing, electrodynamic forcing, and plasma feedback into
one large untyped coupling payload.

## Phase A: Live Neutral Extraction And Replay

Phase A no longer starts from scratch.  Completed Phase A pieces are:

```text
CAM phys_state(:) is available in the sender hook
T/U/V/omega/pmid/zm/q diagnostics exist
O/O2/H/N/NO/N2/He registry exists
q*mbarv/species_mw*pmid/(kB*T) conversion is diagnosed
N2 residual QC is logged
rank-local live dump and merged NPZ exist
f19 live dump can be converted into existing SAMI3 worker payloads
receiver-side checksums match those worker payloads
```

The original Phase A/B target was to replace runtime use of:

```text
pre-generated waccmx_neutral_rank*.bin
```

with:

```text
WACCM-X/CAM runtime phys_state(:) plus constituent indices
```

This replacement has now been implemented and smoke-tested for the copied f19
case through `WXSAMI3_PAYLOAD_MODE=live`.  Keep the phrase "f19 runtime
prototype" attached to it: the implementation gathers the distributed CAM state
to the sender root and is appropriate for the current f19 smoke, not yet for
f09/finer production scaling.

Minimum runtime variables:

```text
T
U
V
O
O2
H
N
NO
PS
Z3 or pressure/height equivalent
```

`W` remains off.  It should not be enabled until coordinate definition, sign
convention, and physical meaning are verified.

## Phase B: Runtime Packet Builder

Phase B is implemented as a f19 gather-to-root prototype in the copied CAM
sender.  The validated f19 replay mapping was promoted into runtime packet
generation from current CAM `phys_state(:)`.

Minimum implementation target:

```text
1. Gather distributed CAM phys_state(:) values needed by the f19 mapper.
2. Build global source-column arrays keyed by CAM cid on the sender root, or
   implement an equivalent distributed remap.
3. Read or prepack the f19 ESMF weights and SAMI3 zaltu/glatu/glonu support
   data needed by the mapper.
4. Fill denni/tni/ui/vi/wi/dennf/tnf/uf/vf/wf directly from runtime CAM state.
5. Send those arrays through the already validated MPI tags.
6. Keep file-backed payload mode as the control-path fallback.
```

For f19, a gather-to-root prototype is acceptable as the next engineering
step, because it fixes the actual invalid assumption: root alone does not own
all `phys_state(:)`.  It should be labeled a prototype, not the final
production scaling design.  The later production version can replace the root
builder with a distributed remap if f09/finer grids or long runs require it.

Runtime builder acceptance criteria:

```text
DONE: WXSAMI3_PAYLOAD_MODE=file remains the fallback/control path
DONE: WXSAMI3_PAYLOAD_MODE=live builds packets from current CAM state
DONE: receiver WXSAMI3_RECV_QC reports 32 ranks received
DONE: live-mode receiver checksums match an independently generated replay payload
DONE: no header mismatch, NaN, fatal, forrtl, or Abort markers in smoke logs
DONE: metadata/logs record f19 grid, source time, species order, units, fallback policy, and sender checksum
DONE: independent live-dump versus CAM-NetCDF helper confirms f19 cid/lat/lon mapping
DONE: receiver log states that invalid H density retains native SAMI3 neutral and He remains native
```

Runtime smoke evidence:

```text
job       = 7641322
state     = COMPLETED
exit      = 0:0
elapsed   = 00:04:49
node      = qhcn084
run dir   = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000
mode      = WXSAMI3_PAYLOAD_MODE=live
map       = /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/esmf_regrid_f19_live_20260523/wxsami3_runtime_map_f19_20260523.bin
compare   = WACCMX_RECV_QC compare ok: ranks=32 max_abs=2.1033e+06 max_rel=4.86991e-13
metadata  = wxsami3-live-payload-v2, actual_transport=runtime_live_packet
metadata rerun job = 7641509, COMPLETED, 0:0, elapsed=00:03:33, node=qhcn065
file-mode regression job = 7641512, COMPLETED, 0:0, elapsed=00:02:42, node=qhcn423
file-mode compare = WACCMX_RECV_QC compare ok: ranks=32 max_abs=1.38854e+06 max_rel=3.26946e-13
```

## CAM Constituent Index Registry

Do not rely only on variable names or assumed constituent order.  Add a runtime
registry for the neutral species sent to SAMI3:

```text
idx_O
idx_O2
idx_H
idx_N
idx_NO
idx_N2 if available
idx_He if available
```

At startup, log a table with:

```text
constituent name
index
unit or source representation
min/max sample
whether sent to SAMI3
whether converted before send
```

The most likely failure mode is not a missing MPI send.  It is a wrong
constituent index, wrong unit, or confusing mixing ratio with number density.

## Payload Data Contract

The staged payload arrays can remain the first transfer layout:

```text
denni
tni
ui
vi
wi
dennf
tnf
uf
vf
wf
```

but the payload needs a versioned data contract rather than an implicit binary
order.  Required metadata:

```text
payload_version
source_time_start
source_time_end
coupling_cadence
grid_type
source_grid
target_grid
units
species_order
height_source
top_transition_flag
endianness
floating_precision
checksum
producer_code_version
```

Required unit clarity:

```text
neutral density: cm^-3 or m^-3
temperature: K
wind: m/s or cm/s
height: geometric height, geopotential height, or pressure-derived height
composition: number density, volume mixing ratio, or mass mixing ratio
species order: O, O2, H, N, NO, N2, ...
```

If binary payloads remain in use, write sidecars:

```text
waccmx_neutral_rank000.bin
waccmx_neutral_rank000.meta.json
```

Longer term, HDF5 or NetCDF is preferable because dimensions, units, and
attributes travel with the data.

## WACCM-X Top Treatment

Current policy is physically reasonable:

```text
above the WACCM-X valid top, retain SAMI3 native MSIS/HWM neutral state
```

but this must be explicit in payload metadata and receiver logs.  Prefer a
transition layer instead of a hard switch:

```text
X_neutral = w(z) * X_WACCMX + (1 - w(z)) * X_SAMI3_native

w = 1    below z1
w -> 0   between z1 and z2
w = 0    above z2
```

Log or output:

```text
waccmx_valid_top_km
blend_bottom_km
blend_top_km
neutral_source_flag = WACCMX / BLEND / SAMI3_NATIVE_MSIS_HWM
```

This is necessary so later SAMI3 diagnostics can distinguish actual WACCM-X
forcing from native MSIS/HWM continuation.

## N2, He, And W Policy

`N2` may be residual-derived in the first live version, but it needs closure
checks on every column/level:

```text
N2_residual > 0
sum_major_species <= total_neutral_density
N2 fraction in plausible range
finite values only
no negative density
```

If residual `N2` is negative, do not silently clip without logging.  Record:

```text
number_of_negative_N2_cells
min_N2_residual
location/time of worst cells
```

`He` should remain SAMI3 native/MSIS until WACCM-X runtime He availability,
unit, vertical behavior, and top-side reliability are separately validated.

`W` should stay off in Phase A.  It is too easy to confuse geometric vertical
velocity, pressure-coordinate omega, sign convention, or grid-relative motion.
First validate:

```text
T, U, V, composition
```

then revisit `W`.

## Offline Replay Versus Live Extraction

The key validation for live extraction is a three-way comparison:

```text
1. WACCM-X history/restart snapshot -> offline payload generator
2. live-dump replay payload -> SAMI3 receiver checksum path
3. live runtime sender packages equivalent phys_state(:) values
```

Compare at the SAMI3 receiver side:

```text
max_abs_diff
RMS_diff
relative_diff
min/max
vertical profiles
species profiles
column-integrated quantities where applicable
```

The target is not necessarily bitwise identity.  It is agreement after the
same interpolation, time selection, unit conversion, and decomposition rules
are applied.  This test separates MPI/control-path errors from CAM extraction,
unit, and coordinate errors.

2026-05-24 status: a first source-state comparison helper now exists:

```text
/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/compare_wxsami3_live_dump_to_cam_nc
```

It confirmed that live dump `cid` maps to the f19 CAM `lat,lon` grid to
roundoff precision:

```text
lat max_abs = 1.4210854715202004e-14
lon max_abs = 5.6843418860808015e-14
```

The `rh0.2005-12-31-00300` comparison is useful as a sanity check, but not as
a strict source-time acceptance test, because the history variables carry:

```text
cell_methods = time: mean
```

The `rh0.2005-12-31-00000` file has valid coordinates but zero 3-D diagnostic
fields in this run, so it is not a live-state physics comparison.  Restart
comparison with `--species-mode mass` is also only a loose sanity check unless
a matching live dump is taken at the same restart time.

One important finding is that live `physics_state%ps` does not match CAM
history/restart `PS` for this run.  The live dump has roughly `855..1610 Pa`,
while CAM history/restart `PS` is surface-pressure scale.  Current runtime
payload construction uses `pmid`, not `state%ps`, so this is not a current
payload checksum failure.  It remains a source-state semantic item to audit
before `PS` is advertised as part of live forcing.

## REMIX -> SAMI3 Electrodynamics

WACCM-X -> SAMI3 neutral forcing alone is not a fully MAGE-consistent SAMI3
run.  SAMI3 still needs MAGE-consistent electrodynamic driving:

```text
REMIX -> SAMI3: potential / E-field / high-latitude convection
```

Without this, SAMI3 plasma response may be generated under its own default or
empirical electrodynamic driver rather than the current MAGE/REMIX field.

This is a high-priority physics gap after the live neutral extraction path is
working.

## Interaction With SAMI3 -> RAIJU/GAMERA Work

The WACCM-X -> SAMI3 track and the SAMI3 -> RAIJU/GAMERA track have different
immediate P0 tasks:

```text
WACCM-X -> SAMI3 P0:
  harden the f19 runtime packet prototype with formal schema/metadata,
  offline-vs-live source-time validation, and explicit top/fallback policy

SAMI3 -> RAIJU/GAMERA P0:
  audit Pavg/Davg/Pstd/Dstd/tiote semantics before physical overwrite
```

Do not let one P0 erase the other.  They are separate track priorities.

For the SAMI3 -> MAGE feedback track, do not expand to species-resolved
feedback first.  The next physical blockers remain:

```text
simple nz mean -> true flux-tube-volume weighting
index-space resize -> L/MLT/flux-tube geometry mapping
```

## Revised WACCM-X -> SAMI3 Priority

| Priority | Task | Purpose |
| --- | --- | --- |
| DONE | live `phys_state(:)` extraction diagnostics in CAM/WACCM-X sender | prove runtime state can be audited |
| DONE | f19 live dump -> replay payload -> receiver checksum | prove f19 mapping and SAMI3 receiver consumption |
| DONE | f19 runtime packet builder from live CAM state | replace file-backed payload use inside sender for the f19 prototype |
| DONE | formal payload schema/metadata sidecar for f19 live mode | prevent order, unit, grid, fallback, and time mistakes |
| DONE | file-mode fallback regression after live-mode hardening | prove the control-path baseline still works |
| DONE/P1 | live dump versus CAM NetCDF comparison helper and f19 coordinate check | validate cid/grid ordering independent of MPI path |
| DONE/P1 | two-packet f19 live transport/cadence smoke | prove packet_hour progression, sender max-packet skip, done signal, and clean disconnect |
| DONE/P1 | file-mode regression after cadence controls | prove fallback path still works with the current sender |
| P1 | strict same-source-time history/restart replay versus live extraction comparison | validate runtime extraction values independent of MPI path |
| P1 | explicit WACCM-X-top MSIS/HWM blending | avoid hidden top boundary discontinuities |
| P1 | N2 residual, He native fallback, W-off QC logs | keep composition closure and vertical-wind semantics controlled |
| P2 | REMIX potential/E-field into SAMI3 | make SAMI3 electrodynamics MAGE-consistent |
| P2 | SAMI3 moment flux-tube-volume weighting | make feedback moments physically meaningful |
| P2 | SAMI3-to-RAIJU L/MLT geometry mapping | replace index-space resize |
| P3 | species-resolved feedback | only after bulk scalar-moment coupling is stable |

## Recommended Status Wording

Use this wording in reports:

```text
The current f19 WACCM-X -> SAMI3 work has completed online MPI control-path
validation plus live CAM phys_state(:) extraction, f19 live-dump replay mapping,
f19 runtime packet generation, and receiver-side checksum validation against an
independent replay payload.  The CESM runtime sender can now build
denni/tni/ui/vi/wi/dennf/tnf/uf/vf/wf from current CAM phys_state(:) in
WXSAMI3_PAYLOAD_MODE=live, and it writes a wxsami3-live-payload-v2 metadata
sidecar with units, species order, fallback policy, runtime QC, and sender
checksum.  The sender also has WXSAMI3_MAX_PACKETS and
WXSAMI3_SEND_EVERY_NSTEPS controls, and the f19 two-packet smoke completed
with clean done/disconnect.  File mode remains the baseline/fallback.

This is still a f19 runtime prototype, not final production live WACCM-X neutral
forcing.  The remaining physical blockers are offline-vs-live source-time
comparison at a strict equal source time, explicit WACCM-X-top MSIS/HWM
blending, N2 residual/He fallback policy, W-off policy validation, and
REMIX/SAMI3 electrodynamic consistency.  Longer cadence/time-interpolation
runs still need validation beyond the two-packet transport smoke.
```

## Checks Before Next Coding

Before promoting the runtime prototype into longer or higher-resolution runs,
verify in the current CAM SourceMods and support files:

```text
file mode remains control-path stable after live-mode additions
live mode can run more than one coupling packet with correct packet_hour/timing
sender stops cleanly when WXSAMI3_MAX_PACKETS is reached and still sends done
formal metadata sidecar contains payload version, grid, units, species order,
source time, checksum, top fallback policy, and W policy
offline history/restart replay and live extraction match at the same source time
above-top invalid samples are converted into an explicit SAMI3-native fallback
or blending policy rather than only invalid placeholders
gather-to-root memory remains acceptable for f19; f09/finer requires a separate
distributed-remap design review
```

This avoids treating a technically online sender as physically production-ready
before the source-time, top-boundary, and composition semantics are pinned down.
