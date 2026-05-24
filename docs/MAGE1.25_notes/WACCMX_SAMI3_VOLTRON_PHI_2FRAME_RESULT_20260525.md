# WACCM-X/SAMI3 Two-Frame Voltron Phi Time-Control Result

Date: 2026-05-25

## Status

Validated a two-frame online phi payload through the live WACCM-X -> SAMI3 peer:

```text
in-job Voltron/REMIX POT export
  -> two-frame remix_sami3_phi_payload.v1 binary
  -> CESM/WACCM-X live neutral sender appends both phi frames
  -> SAMI3 online receiver advances from frame 0 to frame 1 by hrut/hrutw2
```

This is a time-control smoke. Both frames use the same mapped Voltron POT field with different timing metadata. It proves the MPI multi-frame carrier and SAMI3 time gate, not physical time variation of the REMIX potential.

## Launcher

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_2frame_20260525.sbatch
```

## Smoke Result

Slurm:

```text
7659383 COMPLETED 0:0 00:05:02
```

Generated phi payload:

```text
header=[20260524, 1, 125, 97, 2]
frame=0 frame_index=0 hour=0 valid_until=0.001 min=-36.930614 max=31.483816 finite=True nonzero=3492
frame=1 frame_index=1 hour=0.001 valid_until=1e+30 min=-36.930614 max=31.483816 finite=True nonzero=3492
```

CESM/WACCM-X sender:

```text
WXSAMI3 sent live neutral packet
WXSAMI3 sent phi frame: iframe,nframes,... = 0 2 ... valid_until=1.00000005E-03
WXSAMI3 sent phi frame: iframe,nframes,... = 1 2 ... valid_until=1.00000002E+30
WXSAMI3 sent phi payload frames: 2
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

SAMI3 receiver:

```text
WACCMX_PHI_RECV 0 2 hrut=0.0 frame_hour=0.0 valid_until=1.00000005E-03
nweimer 1
WACCMX_PHI_RECV 1 2 hrut=2.22222228E-03 frame_hour=1.00000005E-03 valid_until=1.00000002E+30
MASTER: All Done!
WACCMX online done signal received: 1
```

Neutral replay/QC:

```text
WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.08794e+06 max_rel=4.83248e-13
```

Evidence directory:

```text
logs/waccmx_live_neutral_voltron_phi_2frame_20260525/
```

## Current Meaning

Completed control-path levels:

```text
1. Live CAM/WACCM-X neutral extraction and send: validated
2. SAMI3 online receiver, worker distribution, done tag: validated
3. WACCM-X top-blend neutral apply policy: validated in smoke
4. In-job Voltron/REMIX phi handoff: validated for one physical frame
5. Multi-frame online phi carrier and SAMI3 time-gated advance: validated by duplicate-frame time-control smoke
```

Still not complete:

```text
1. Real multi-time Voltron/REMIX phi writer or live REMIX stream
2. Synchronized neutral/phi cadence over multiple coupling cycles
3. Physical N2 residual closure instead of invalid masking
4. Production SAMI3 -> RAIJU/GAMERA feedback validation with long runs
```

## Recommended Next Step

Implement a real multi-frame Voltron/REMIX phi writer path:

```text
Voltron/REMIX time t0 -> frame 0
Voltron/REMIX time t1 -> frame 1
...
```

The writer should append frames to `remix_sami3_phi_payload.v1`, update `nframes`, and assign:

```text
frame_hour = Voltron time / 3600
valid_until = next frame hour, or final sentinel for the last available frame
```

Then rerun the same live WACCM-X/SAMI3 smoke with physically distinct frames.
