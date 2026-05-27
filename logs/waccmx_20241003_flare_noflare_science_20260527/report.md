# WACCM-X 2024-10-03 X9 Flare/No-Flare Science Evidence

- Generated: `2026-05-27T13:23:00+08:00`
- Classification: `waccmx_flare_noflare_science_pair_evidence`
- Event: `NOAA AR3842 X9.0 flare`, peak `2024-10-03T12:18:00Z`
- Analysis window: `2024-10-03T12:00:00Z/2024-10-03T13:00:00Z`
- Flare case: `waccmx_fism2_flare_f09_20241003_x9_r5_5min`
- No-flare case: `waccmx_fism2_noflare_f09_20241003_x9_r5_5min`

## Control Difference

The paired WACCM-X cases use the same history-output settings.  The controlling science difference is `solar_euv_data_file`:

- Flare: `/home/jiaoy_group/jiaoy/data/WACCMX/inputdata/solar/fism2_20241003_x9/fism2_flare_bands_20241003_x9_waccmx.nc`
- No-flare: `/home/jiaoy_group/jiaoy/data/WACCMX/inputdata/solar/fism2_20241003_x9/fism2_noflare_bands_20241003_x9_removed_waccmx.nc`

The local FISM2 pair summary states that the no-flare forcing replaces the observed 12:08-13:08 UTC flare window with per-band linear interpolation, which corresponds to 12:10-13:05 UTC samples at 5-minute cadence.

## Available Model Products

- Both cases have CAM `h1`, `h2`, `h3`, `h4`, and `h6` history streams.
- The history products are recorded in `manifests/hist_inventory.tsv` and not copied into this archive.
- Existing quicklook products cover the requested 12:00-13:00 UTC interval.

## Included Key Frames

- Window mean: `quicklook_keyframes/window_mean/` for 12:10-13:05 UTC.
- 12:30 UTC snapshots near the flare peak response:
  `global_T_TEC_with_fism`, `electron_density_altitudes`, `temperature_altitudes`, and `T250_TEC`.
- Full 5-minute local quicklook paths are recorded in `manifests/source_paths.tsv` and summarized in `quicklook_indexes/`.

## Current Interpretation

This package is enough for the first-stage science comparison: a controlled WACCM-X flare/no-flare pair driven by FISM2, with existing 5-minute quicklooks through the requested interval.

It does not yet prove the same 2024-10-03 interval has been run through the live WACCM-X -> SAMI3 -> RAIJU/GAMERA prototype.  That should be the next integration step after this WACCM-X-only science comparison is accepted.
