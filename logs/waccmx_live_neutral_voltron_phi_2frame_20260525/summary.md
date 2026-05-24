# WACCM-X Live Neutral + Two-Frame Voltron Phi Time-Control Smoke

Date: 2026-05-25
Slurm job: 7659383
Run directory: `/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_2frame_20260525_0000`
Launcher: `slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_2frame_20260525.sbatch`

## Result

The two-frame time-control smoke completed successfully with Slurm exit code `0:0`.

This run generated a one-frame Voltron/REMIX POT export inside the same Slurm job, then repacked the in-job Voltron HDF5 export into a two-frame MPI phi payload with explicit timing metadata:

```text
frame 0: hour=0.0, valid_until=0.001 h
frame 1: hour=0.001 h, valid_until=1e30 h
```

The two frames use the same mapped POT field. This is intentional: the run validates MPI frame sequencing and SAMI3 time-gated frame advance, not physical time evolution of the REMIX potential.

## Key Evidence

- Slurm: `7659383|COMPLETED|0:0|00:05:02`
- Two-frame payload:
  - `header=[20260524, 1, 125, 97, 2]`
  - `frame=0 hour=0 valid_until=0.001`
  - `frame=1 hour=0.001 valid_until=1e+30`
  - both frames finite, min/max `-36.930614 / 31.483816`
- CESM/WACCM-X sender:
  - `WXSAMI3 sent live neutral packet`
  - `WXSAMI3 sent phi frame ... 0 2 ... valid_until=1.00000005E-03`
  - `WXSAMI3 sent phi frame ... 1 2 ... valid_until=1.00000002E+30`
  - `WXSAMI3 sent phi payload frames: 2`
  - `WXSAMI3 sent done signal to SAMI3`
  - `END OF MODEL RUN`
- SAMI3 receiver:
  - `WACCMX_PHI_RECV 0 2 ... valid_until=1.00000005E-03`
  - `WACCMX_PHI_RECV 1 2 hrut=2.22222228E-03 ... valid_until=1.00000002E+30`
  - `MASTER: All Done!`
  - `WACCMX online done signal received: 1`
- Replay/QC:
  - `WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.08794e+06 max_rel=4.83248e-13`

## Interpretation

This validates that the current live WACCM-X sender and SAMI3 online receiver can carry more than one REMIX/SAMI3 phi frame through the same online peer and that SAMI3 can advance to the next frame when `hrut >= hrutw2`.

The next physical step is to replace the duplicate-frame repack with a real multi-frame Voltron/REMIX writer or a synchronized REMIX stream so each frame is produced from a distinct coupling time.

## Archived Artifacts

- `slurm-7659383.out`
- `slurm-7659383.err`
- `sacct_7659383.txt`
- `phi_payload_summary.txt`
- `phi_payload_2frame_builder.out`
- `live_phi_payload_writer_voltron_append.out`
- `remix_sami3_phi_payload_from_voltron_live_append_oneframe.bin`
- `remix_sami3_phi_payload_from_voltron_live_append_2frame.bin`
- `remix_sami3_phi_payload_from_voltron_live_append_2frame.json`
- `phi_weimer_from_voltron_live_append_2frame.inp`
- `waccmx_cesm.out`
- `sami3_online_receiver.out`
- `live_dump_summary_pkt000000.txt`
- `replay_builder_pkt000000.out`
- `recv_qc_compare_pkt000000.txt`
- `wxsami3_live_meta.json`
