# WACCM-X/SAMI3 In-Job Voltron Phi Append Result

Date: 2026-05-25

## Status

Validated one-job smoke path:

```text
Voltron/REMIX Weimer phi writer
  -> in-job binary phi payload
  -> CESM/WACCM-X live neutral sender appends phi frame
  -> SAMI3 online receiver receives neutral packet + phi frame + done tag
```

This removes the manual/static phi-file boundary from the previous phi append smoke. The SAMI3 receiver path is unchanged: one online peer still provides neutral forcing first, then optional phi frames, then the done signal.

## Launcher

```text
slurm/run_waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_append_20260525.sbatch
```

The launcher has two stages:

1. Start `voltron.x` from the existing REMIX/SAMI3 phi writer experiment and wait for a stable `remix_sami3_phi_payload_from_voltron_live_append.bin`.
2. Start the existing PRRTE DVM, SAMI3 online receiver, and CESM/WACCM-X live sender with `WXSAMI3_PHI_PAYLOAD_FILE` pointing at the in-job-generated payload.

## Smoke Result

Slurm job:

```text
7658944 COMPLETED 0:0 00:05:06
```

Generated phi payload:

```text
header=[20260524, 1, 125, 97, 1]
size=48532
min=-36.930614
max=31.483816
finite=True
nonzero=3492
```

CESM/WACCM-X sender evidence:

```text
WXSAMI3 sent live neutral packet
WXSAMI3 sent phi frame ... -36.9306145 31.4838161
WXSAMI3 sent phi payload frames: 1
WXSAMI3 sent done signal to SAMI3
END OF MODEL RUN
```

SAMI3 receiver evidence:

```text
WACCMX_PHI_RECV ... -36.9306145 31.4838161
hrutw2 = 0.00000000 1.00000002E+30
nweimer 1
MASTER: All Done!
WACCMX online done signal received: 1
```

Replay/QC:

```text
WACCMX_RECV_QC compare ok: ranks=32 occurrence=0 step_set=[0] packet_hour_set=[0.0] max_abs=2.08794e+06 max_rel=4.83248e-13
```

Archived evidence:

```text
logs/waccmx_live_neutral_voltron_phi_append_20260525/
```

## Current Interpretation

This is now a runtime/control-path prototype for:

```text
live WACCM-X neutral forcing + in-job REMIX/Voltron phi handoff into SAMI3
```

It is still not the final production physical coupling:

- The phi source is generated at smoke cadence from the Voltron/REMIX writer path, not yet advanced as a synchronized continuous multi-frame REMIX stream.
- The WACCM-X neutral path still uses the current f19 runtime map and top-blend policy.
- `N2` remains residual-derived with invalid masking for negative residuals.
- SAMI3 -> RAIJU/GAMERA plasma feedback remains the scalar moment adapter path and still needs production-scale long-run validation.

## Recommended Next Step

Move from one-frame phi append smoke to time-synchronized cycling:

1. Make the Voltron/REMIX phi writer emit a sequence of frames at coupling cadence.
2. Let the WACCM-X sender append all phi frames valid for the current SAMI3 coupling window.
3. Run a multi-cycle live neutral + phi smoke and verify:
   - monotonic frame hours,
   - SAMI3 `nweimer` increments as expected,
   - no stale frame reuse,
   - neutral receiver QC remains continuous,
   - done signal still exits cleanly.

After that, the path should be connected back to the SAMI3 -> RAIJU/GAMERA scalar moment runtime chain for a closed prototype loop.
