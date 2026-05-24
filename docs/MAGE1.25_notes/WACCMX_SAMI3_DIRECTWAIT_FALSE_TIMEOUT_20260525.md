# WACCM-X/SAMI3 Direct-Wait False Timeout

Date: 2026-05-25

## Result

The first same-job Voltron phi writer + CESM/WACCM-X direct-wait run failed:

```text
jobid = 7661005
jobname = wxsami3_ap2w
state = FAILED
exit = 1:0
elapsed = 00:06:23
node = qhcn425
archive = logs/waccmx_append2_directwait_20260525/
```

This run did prove the launcher mode:

```text
VOLTRON_WRITER_PID=965424
DIRECT_WAIT_MODE=1
PHI_PAYLOAD_WAIT_SECONDS=240
PHI_PAYLOAD_STABLE_SECONDS=1
```

The Voltron-side payload itself was valid:

```text
payload = voltron_phi_writer/remix_sami3_phi_payload_from_voltron_live_append2.bin
size = 97044 bytes
header = [20260524, 1, 125, 97, 2]
hours = [0.0, 0.0013888889225199819]
nonzero_counts = [3492, 3492]
frame_change max_abs_diff = 3.5858945846557617
validate_remix_sami3_phi_payload = overall=ok
```

The receiver-side neutral/source flag accounting also closed:

```text
validate_wxsami3_source_flag_balance returncode = 0
validate_wxsami3_topblend_policy returncode = 0
validate_wxsami3_time_axis returncode = 0
validate_wxsami3_runtime_map returncode = 0
```

## Failure Signature

The CESM/WACCM-X sender sent the live neutral packet, then timed out while
waiting for the phi payload:

```text
WXSAMI3 sent live neutral packet: nstep,packet_hour,count=           0   0.00000000               0
WXSAMI3 phi payload wait timed out: file,size,elapsed=.../remix_sami3_phi_payload_from_voltron_live_append2.bin       97044         240
WXSAMI3 phi payload was not ready before timeout
MPI_ABORT was invoked on rank 0
```

This is a false timeout, because the payload existed at the exact expected size
and passed the independent binary contract validator.

## Root Cause

`wxsami3_send_phi_payload()` reads the binary payload as little-endian, and the
Voltron-side writer writes the same little-endian schema.  The wait loop in
`wxsami3_wait_for_phi_payload()` checked the header without
`convert='little_endian'`, so it saw the right file size but rejected the header
until the 240 second wait expired.

## Patch

The wait-loop open now matches the real payload contract:

```fortran
open(unit=122, file=trim(phi_payload_file), form='unformatted', &
     access='stream', convert='little_endian', status='old', &
     action='read', iostat=ios)
```

Patched files:

```text
code/cesm_source_mods/src.cam/wxsami3_online_stub_mod.F90
/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523/SourceMods/src.cam/wxsami3_online_stub_mod.F90
```

After patching, the CESM case was incrementally rebuilt successfully:

```text
build command:
  env HOME=/home/jiaoy_group/jiaoy/data/CESM/experiments/cime_home_v3_qhslurm_20260525 \
      PATH=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/python311_first:$PATH \
      ./case.build --skip-provenance-check

result:
  MODEL BUILD HAS FINISHED SUCCESSFULLY
  Total build time: 95.828171 seconds
```

The temporary HOME was used only to avoid the stale global
`~/.cime/config_machines.xml` v2/v3 schema conflict.  The case-local
`EXTRA_MACHDIR` was cleared in `env_case.xml` so CIME would not re-read the
`local_machines_v3/qhslurm/config_machines.xml` fragment after the root v3
machine file.

## Next Gate

Rerun the same direct-wait path.  The acceptance target is:

```text
CESM/WACCM-X sender waits until phi payload is ready
sender logs WXSAMI3 phi payload ready after wait
sender sends 2 phi frames
SAMI3 receiver logs 2 WACCMX_PHI_RECV records
receiver reaches MASTER: All Done!
archive_current_goal_mode_runs.py --target directwait returns ok
```
