# SAMI3 Receiver With Voltron Append2 Offset Phi Payload

- Date: 2026-05-25
- Job: 7659750
- State: COMPLETED, exit 0:0
- Launcher: `slurm/run_sami3_online_receiver_voltron_phi_append2_offset_20260525.sbatch`
- Phi payload: `logs/voltron_phi_append_writer_2frame_offset_20260525/remix_sami3_phi_payload_append_writer_2frame_offset.bin`

Result:

```text
NEUTRAL_PHI_SENDER phi_payload_format=remix_sami3_phi_payload.v1 nframes=2
NEUTRAL_PHI_SENDER sent phi frame=0/2 hour=0 valid_until=0.00138889
NEUTRAL_PHI_SENDER sent phi frame=1/2 hour=0.00138889 valid_until=1e+30

WACCMX_PHI_RECV 0 2 hrut=0 frame_hour=0 valid_until=1.38888892E-03 min=-36.9306145 max=31.4838161
hrutw2 = 0 1.38888892E-03
WACCMX_PHI_RECV 1 2 hrut=2.22222228E-03 frame_hour=1.38888892E-03 valid_until=1.00000002E+30 min=-37.6830177 max=31.8911915
hrutw2 = 2.22222228E-03 1.00000002E+30

WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.1033e+06 max_rel=4.86991e-13
MASTER: All Done!
```

Conclusion:

```text
The SAMI3 online receiver consumes the real Voltron append2 MPI phi payload and
advances from the first frame to the second frame through the existing hrut/hrutw2
time gate. This validates the receiver side independently of the queued full
CESM/WACCM-X live sender integration.
```
