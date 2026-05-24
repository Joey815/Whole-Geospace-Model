# WACCM-X Live Neutral + In-Job Voltron Phi Append Smoke

Date: 2026-05-25
Slurm job: 7658944
Run directory: `/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append_20260525_0000`
Launcher: `slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append_20260525.sbatch`

## Result

The one-job smoke completed successfully with Slurm exit code `0:0`.

This run generated a REMIX/Voltron Weimer phi payload inside the same Slurm job, then launched the live CESM/WACCM-X sender and SAMI3 online receiver on the same PRRTE DVM. CESM sent one live neutral packet, appended the in-job-generated phi payload, and sent the done signal. SAMI3 received the neutral fields, applied the top-blend neutral policy, received the phi frame, and exited cleanly.

## Key Evidence

- Slurm: `7658944|COMPLETED|0:0|00:05:06`
- Voltron phi payload:
  - `header=[20260524, 1, 125, 97, 1]`
  - `min=-36.930614`
  - `max=31.483816`
  - `finite=True`
  - `nonzero=3492`
- CESM/WACCM-X sender:
  - `WXSAMI3 sent live neutral packet`
  - `WXSAMI3 sent phi frame ... -36.9306145 31.4838161`
  - `WXSAMI3 sent phi payload frames: 1`
  - `WXSAMI3 sent done signal to SAMI3`
  - `END OF MODEL RUN`
- SAMI3 receiver:
  - `WACCMX_PHI_RECV ... -36.9306145 31.4838161`
  - `MASTER: All Done!`
  - `WACCMX online done signal received: 1`
- Replay/QC:
  - `WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.08794e+06 max_rel=4.83248e-13`

## Notes

- The `Terminated` message in `slurm-7658944.err` is expected for this smoke: the launcher kills the long-running Voltron process after the phi payload is detected as complete and stable.
- `N2` remains residual-derived with `WXSAMI3_N2_NEGATIVE_MODE=invalid`; this smoke retained the existing invalid-mask behavior and did not solve the underlying composition closure issue.
- This validates the runtime control/data path. It is still a smoke/prototype path, not a full production physical coupling.

## Archived Artifacts

- `slurm-7658944.out`
- `slurm-7658944.err`
- `sacct_7658944.txt`
- `phi_payload_summary.txt`
- `live_phi_payload_writer_voltron_append.out`
- `remix_sami3_phi_payload_from_voltron_live_append.bin`
- `waccmx_cesm.out`
- `sami3_online_receiver.out`
- `live_dump_summary_pkt000000.txt`
- `replay_builder_pkt000000.out`
- `recv_qc_compare_pkt000000.txt`
- `wxsami3_live_meta.json`
