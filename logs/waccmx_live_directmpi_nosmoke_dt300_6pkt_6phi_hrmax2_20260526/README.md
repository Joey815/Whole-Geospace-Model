# WACCM-X/SAMI3 f19 direct-MPI no-smoke 6pkt/6phi run, 2026-05-26

This archive contains text logs and validators for job 7678504, the first validated f19 direct-MPI no-smoke run with six CAM live-neutral packets and six Voltron/REMIX direct-phi frames.

Source run directory:
`/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_6pkt_6phi_hrmax2_maxstep400_20260526_0000`

Key runtime settings:
- `SAMI3_MAXSTEP=400`
- `SAMI3_HRMAX=2.000000`
- `SAMI3_DT0=300.`
- `SAMI3_NEUTRAL_UPDATE_HOURS=0.08333333333333333`
- `SAMI3_NEUTRAL_SPAN_HOURS=0.08333333333333333`
- `PHI_MAX_FRAMES=6`
- `PHI_FRAME_HOUR_BASE=0.0`
- `PHI_FRAME_HOUR_STEP=0.08333333333333333`
- `PHI_VALID_HOURS=0.08333333333333333`
- `MAX_PACKETS=6`
- `LIVE_DUMP_MAX=6`
- `CESM_STOP_N=2100`

The successful setting came after failed short attempts with `HRMAX=.700000` and too-small effective `ntmmax`; those attempts proved the six-packet cadence needs a larger `hrmax`, not just a larger `maxstep`.
