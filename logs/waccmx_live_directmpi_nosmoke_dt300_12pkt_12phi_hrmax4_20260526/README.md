# WACCM-X/SAMI3 f19 direct-MPI no-smoke 12pkt/12phi run, 2026-05-26

This archive contains text logs and validators for job 7680171, the first
validated f19 direct-MPI no-smoke run with twelve CAM live-neutral packets and
twelve Voltron/REMIX direct-phi frames.

Source run directory:
`/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_12pkt_12phi_hrmax4_maxstep1400_20260526_0000`

Key runtime settings:
- `SAMI3_MAXSTEP=1400`
- `SAMI3_HRMAX=4.000000`
- `SAMI3_DT0=300.`
- `SAMI3_NEUTRAL_UPDATE_HOURS=0.08333333333333333`
- `SAMI3_NEUTRAL_SPAN_HOURS=0.08333333333333333`
- `PHI_MAX_FRAMES=12`
- `PHI_FRAME_HOUR_BASE=0.0`
- `PHI_FRAME_HOUR_STEP=0.08333333333333333`
- `PHI_VALID_HOURS=0.08333333333333333`
- `PHI_FINAL_VALID_UNTIL_HOUR=1.0e30`
- `MAX_PACKETS=12`
- `LIVE_DUMP_MAX=12`
- `CESM_STOP_N=3900`

Slurm result:
- `jobid=7680171`
- `state=COMPLETED`
- `exit=0:0`
- `elapsed=00:48:27`
- `node=qhcn343`
- `batch MaxRSS=65270560K`

Validated evidence:
- SAMI3 received all 12 neutral packet hours from `0.0` to `0.916666687`.
- SAMI3 received all 12 direct-phi frames, indices `0..11`.
- Voltron wrote a 12-frame `remix_sami3_phi_payload.v1` payload with finite,
  changing frames.
- All 12 replay/QC comparisons passed; worst archived `max_rel` is
  `1.12911e-12`.
- The launcher accepted the Voltron-side timeout only after direct-phi done and
  `MASTER: All Done!`.
- All seven validators returned `overall=ok`.

Archived text artifacts include:
- `slurm-7680171.out`
- `slurm-7680171.err`
- `sami3_online_receiver.out`
- `waccmx_cesm.out`
- `voltron_runtime_direct.out`
- `phi_payload_summary.txt`
- `validate_*.txt`
- `validate_*.json`
- `recv_qc_compare_pkt000000.txt` through `recv_qc_compare_pkt000011.txt`
- `live_dump_summary_pkt000000.txt` through `live_dump_summary_pkt000011.txt`
- `replay_builder_pkt000000.out` through `replay_builder_pkt000011.out`
- `wxsami3_live_meta.json`
- `sacct_7680171.txt`

Large binary payloads, live dumps, replay payloads, executables, and full model
outputs are intentionally not archived in Git.
