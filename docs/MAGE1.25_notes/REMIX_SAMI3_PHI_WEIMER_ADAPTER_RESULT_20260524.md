# REMIX -> SAMI3 Phi-Weimer Adapter Result

Date: 2026-05-24 CST

## Goal

Start the REMIX -> SAMI3 electric-potential path without changing SAMI3's main
transport equations.  The first implementation targets SAMI3's existing
external-potential route:

```text
MAGE/REMIX POT[kV]
-> SAMI3 phi_weimer.inp
-> potential.f90:weimer
-> potpphi
-> exb(hrut, phi)
```

This is an offline adapter plus static-file runtime validator.  It is not yet
live REMIX forcing inside the online MPI loop.

## Source-Code Audit Result

Relevant SAMI3 code path:

```text
sami3-3.22.f90:
  master receives hipcp/hihcm/hipcphi/hid* from workers
  master calls potpphi(...) and sends phi(nnx,nny) back to workers
  workers call exb(hrut, phi)

potential.f90:
  potpphi adds dphi + corotation + Volland/Stern + phi_weimer
  if lweimer is true, weimer(...) reads phi_weimer.inp

exb_transport.f90:
  exb calls vexb_phi(phi), applies altitude taper and vexb_max clipping,
  then uses vexbp/vexbs/vexbh for perpendicular transport
```

So the least invasive REMIX entry is `phi_weimer.inp`, not a direct overwrite
of `vexb_*`.

## Added Adapter

New script:

```text
scripts/remix_sami3/remix_pot_to_sami3_phi_weimer.py
```

Input:

```text
waccmx_voltron_forward_package.h5:/NORTH_APEX/POT
units: kV
source grid: 45 x 360 REMIX/APEX high-latitude grid
theta range: 0..45 deg colatitude
magnetic latitude range: 45..90 deg
```

Target:

```text
SAMI3 weimer_grid.dat
nlat = nfp1 = 125
nlon = nlt + 1 = 97
target mlat range = 1.87674153..88.9908981 deg
target mlon range = 0..360 deg
```

Mapping policy:

```text
longitude: periodic interpolation
latitude: interpolation from REMIX magnetic latitude to SAMI3 Weimer latitude
target latitudes below the REMIX source minimum are set to zero by default
unit conversion: phi_statV = POT_kV * 1000 / 300
binary format: gfortran-style sequential unformatted records
static packet records: hour0, phi(nfp1,nlt+1), valid_until_hour
```

The low-latitude zero fill is intentional for this prototype because the REMIX
export package only carries the high-latitude shell-grid cap.  It avoids
extrapolating high-latitude potential deep into SAMI3's lower-latitude Weimer
grid.

## Validation Run

Command:

```text
/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python \
  scripts/remix_sami3/remix_pot_to_sami3_phi_weimer.py \
  --input /home/jiaoy_group/jiaoy/data/MAGE1.25/experiments/voltron_waccmx_file_clean_exit/waccmx_file_clean_exit_20260512a/waccmx_voltron_forward_package.h5 \
  --group NORTH_APEX \
  --weimer-grid /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/weimer_grid.dat \
  --output logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static.inp \
  --summary-json logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static.json \
  --diagnostic-h5 logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static_diag.h5
```

Outputs:

```text
logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static.inp
logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static.json
logs/remix_sami3_phi_weimer_20260524/phi_weimer_remix_north_static_diag.h5
logs/remix_sami3_phi_weimer_20260524/run_remix_pot_to_sami3_phi_weimer.log
```

Checks:

```text
phi_kV shape: 125 x 97
phi_kV min/max/mean: -13.046549885448659 / 10.838320313501898 / -0.07204556894533992
phi_statV min/max/mean: -43.4884996181622 / 36.12773437833966 / -0.24015189648446636
finite count: 12125
NaN count: 0
low-lat zero-filled target rows: 89
readback hour0: 0.0
readback valid_until_hour: 1.0000000150474662e+30
readback phi max_abs_diff: 1.8859540276139342e-06 statV
```

The first record markers also match the expected sequential-unformatted layout:

```text
record 1 length = 4 bytes
record 2 length = 48500 bytes = 125 * 97 * 4
```

## SAMI3 Runtime Smoke

A copied SAMI3 OpenMPI work tree was patched with:

```text
code/sami3_receiver/patches/use_existing_phi_weimer.patch
```

This adds `SAMI3_USE_EXISTING_PHI_WEIMER=1`, which tells SAMI3 not to run
`test_w05sc` over the externally generated `phi_weimer.inp`.

Runtime launcher:

```text
slurm/run_sami3_online_receiver_remix_phi_weimer_20260524.sbatch
```

The first run, job 7651322, timed out because the replay sender compiled by
the launcher did not send the receiver's current `source_flags` payload
(`tag=212`).  That blocked workers in `waccmx_recv_neutral_online`; it was not
a REMIX-phi file-format failure.

The sender stub was updated to send fallback source flags derived from the
first neutral-density species:

```text
scripts/wxsami3_neutral_sender_stub.c
source_flag = WACCMX_VALID if denni[0:nlocal] >= 0
source_flag = OTHER_INVALID otherwise
```

Validated rerun:

```text
job: 7651485
state: COMPLETED
exit: 0:0
elapsed: 00:01:18
node: qhcn025
MaxRSS: 39601304K
```

Runtime evidence:

```text
SAMI3_USE_EXISTING_PHI_WEIMER: using preexisting phi_weimer.inp
hrutw2 = 0.00000000  1.00000002E+30
WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0]
packet_hour_set=[0.0] max_abs=2.1033e+06 max_rel=4.86991e-13
MASTER: All Done!
WACCMX online done signal received: 1
```

No `fatal`, `forrtl`, `NaN`, `Abort`, `EOF`, or `header mismatch` markers were
found in the runtime logs.

Archived evidence:

```text
logs/remix_sami3_phi_weimer_runtime_20260524/sacct_7651485.txt
logs/remix_sami3_phi_weimer_runtime_20260524/receiver_markers_7651485.txt
logs/remix_sami3_phi_weimer_runtime_20260524/recv_qc_compare_7651485.txt
logs/remix_sami3_phi_weimer_runtime_20260524/sami3_online_receiver_7651485.out
logs/remix_sami3_phi_weimer_runtime_20260524/neutral_sender_7651485.out
logs/remix_sami3_phi_weimer_runtime_20260524/slurm_7651485.out
logs/remix_sami3_phi_weimer_runtime_20260524/slurm_7651485.err
```

## Time-Series Replay Contract

The adapter now also accepts multiple `waccmx_voltron_forward_package.h5`
inputs and writes SAMI3's native multi-frame `phi_weimer.inp` record sequence:

```text
hour0, phi0, hour1, phi1, ..., phiN, valid_until_hour
```

If the input files contain strictly increasing `Meta/mjd`, frame hours are
derived from that.  The current long-run packages used for this test still
carry identical `Meta/mjd`, so the two-frame artifact uses an explicit
cadence:

```text
--cadence-hours 0.08333333333333333
```

Prototype artifact:

```text
logs/remix_sami3_phi_weimer_timeseries_20260524/phi_weimer_remix_north_2frame.inp
logs/remix_sami3_phi_weimer_timeseries_20260524/phi_weimer_remix_north_2frame.json
logs/remix_sami3_phi_weimer_timeseries_20260524/phi_weimer_remix_north_2frame_diag.h5
logs/remix_sami3_phi_weimer_timeseries_20260524/phi_weimer_remix_north_2frame_record_summary.txt
logs/remix_sami3_phi_weimer_timeseries_20260524/run_remix_pot_to_sami3_phi_weimer_2frame.out
```

Checks:

```text
nframes: 2
frame_hours: [0.0, 0.08333333333333333]
readback_hours: [0.0, 0.0833333358168602, 1.0000000150474662e+30]
readback_hour_max_abs_diff: 0.0
readback_phi_max_abs_diff_statV: 1.888117893145136e-06
phi_kV shape: 2 x 125 x 97
phi_kV min/max/mean: -13.07980127883359 / 10.72937314195538 / -0.07636781304572414
```

The selected cycle01/cycle02 source packages are not identical:

```text
NORTH_APEX/POT max_abs_diff: 0.32675565522934047 kV
NORTH_APEX/POT rms_diff: 0.1271580700463197 kV
```

Record parser output confirms the SAMI3 reader contract:

```text
0 ('hour', 4, 0.0)
1 ('phi', 48500, None)
2 ('hour', 4, 0.0833333358168602)
3 ('phi', 48500, None)
4 ('hour', 4, 1.0000000150474662e+30)
```

## Current Limitation

This adapter proves the file-format bridge and static SAMI3 runtime ingestion
path, plus a two-frame time-series replay file contract.  It does not yet
prove production REMIX -> SAMI3 electrodynamic consistency.

Known limitations:

```text
uses NORTH_APEX only by default
time sequence replay is supported from multiple files, but not yet live update
does not yet handle southern-hemisphere sign/mirroring policy
uses direct mlat/mlon interpolation, not a full SAMI3 field-line mapping
sets target mlat < 45 deg to zero because the source package is high-lat only
```

## Next Step

The next implementation step is a controlled runtime test that forces SAMI3 to
read the second `phi_weimer` frame, then replacing replay files with a live
REMIX potential feed:

```text
REMIX/POT time sequence
-> versioned phi payload or regenerated phi_weimer.inp sidecar
-> SAMI3 potential.f90:weimer read/update at coupling cadence
-> exb(hrut, phi)
```

Keep the static-file path as the replay baseline.  For the physical path, add
time metadata, hemisphere policy, and a validation comparison against the
current Weimer baseline (`phiu.dat` and E x B diagnostics if enabled).
