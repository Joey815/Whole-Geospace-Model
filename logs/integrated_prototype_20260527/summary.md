# MAGE WACCM-X SAMI3 RAIJU GAMERA Integrated Prototype Evidence

- Generated: `2026-05-27T11:59:53+08:00`
- Classification: `integrated_prototype_evidence_not_production_full_coupling`
- This is a unified evidence archive from validated component/prototype runs.
- It is not a claim of production physical full coupling.

## Source Evidence

### WACCM-X -> SAMI3 Neutral + REMIX/Voltron -> SAMI3 Phi

- Job: `7697673`
- Run dir: `/online1/jiaoy_group/jiaoy/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_24pkt_24phi_hrmax8_maxstep2800_20260526_0000`
- Runtime source: `CAM phys_state(:)`
- Transport: `runtime_live_packet`
- Neutral packets: `24`
- Phi frames: `24`
- Payload version: `wxsami3-live-payload-v2`
- Last packet hour: `1.91666663`

### SAMI3 -> RAIJU/GAMERA Density-Only 1800s

- Job: `7678667`
- Run dir: `/online1/jiaoy_group/jiaoy/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_tiote_long1800_20260526`
- Last history steps: `{'gam': 'Step#361', 'raiju': 'Step#361'}`
- Formula checks: `{'Davg': {'alpha': 0.05, 'formula_max_abs': 0.0, 'formula_max_rel': 0.0, 'mask_true': 8100, 'mask_total': 16920}, 'Dstd': {'alpha': 0.0, 'formula_max_abs': 0.0, 'formula_max_rel': 0.0, 'mask_true': 8100, 'mask_total': 16920}, 'Pavg': {'alpha': 0.0, 'formula_max_abs': 0.0, 'formula_max_rel': 0.0, 'mask_true': 8100, 'mask_total': 16920}, 'Pstd': {'alpha': 0.0, 'formula_max_abs': 0.0, 'formula_max_rel': 0.0, 'mask_true': 8100, 'mask_total': 16920}}`
- Non-finite checked fields: `{'base_gam_res': [], 'base_raiju_res': [], 'proto_gam_res': [], 'proto_raiju_res': []}`

### SAMI3 -> RAIJU/GAMERA Density + Tiote 1800s

- Job: `7678667`
- Run dir: `/online1/jiaoy_group/jiaoy/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_tiote_long1800_20260526`
- Last history steps: `{'gam': 'Step#361', 'raiju': 'Step#361'}`
- Formula checks: `{'Davg': {'alpha': 0.05, 'formula_max_abs': 0.0, 'formula_max_rel': 0.0, 'mask_true': 8100, 'mask_total': 16920}, 'Dstd': {'alpha': 0.0, 'formula_max_abs': 0.0, 'formula_max_rel': 0.0, 'mask_true': 8100, 'mask_total': 16920}, 'Pavg': {'alpha': 0.0, 'formula_max_abs': 0.0, 'formula_max_rel': 0.0, 'mask_true': 8100, 'mask_total': 16920}, 'Pstd': {'alpha': 0.0, 'formula_max_abs': 0.0, 'formula_max_rel': 0.0, 'mask_true': 8100, 'mask_total': 16920}}`
- Non-finite checked fields: `{'base_gam_res': [], 'base_raiju_res': [], 'proto_gam_res': [], 'proto_raiju_res': []}`

## Validator Snapshot

- `raiju_density_long1800/validate_sami3_raiju_longrun.txt`: `ok`
- `raiju_density_long1800/validate_sami3_raiju_mapping_product.txt`: `ok`
- `raiju_density_long1800/validate_sami3_raiju_summary.txt`: `ok`
- `raiju_density_tiote_long1800/validate_sami3_raiju_longrun.txt`: `ok`
- `raiju_density_tiote_long1800/validate_sami3_raiju_mapping_product.txt`: `ok`
- `raiju_density_tiote_long1800/validate_sami3_raiju_production_contract_diagnostic.txt`: `ok`
- `raiju_density_tiote_long1800/validate_sami3_raiju_production_contract_production.txt`: `FAIL`
- `raiju_density_tiote_long1800/validate_sami3_raiju_summary.txt`: `ok`
- `raiju_density_tiote_long1800/validate_sami3_raiju_tiote_hook.txt`: `ok`
- `waccmx_sami3_phi_24pkt/validate_remix_sami3_phi_payload.txt`: `ok`
- `waccmx_sami3_phi_24pkt/validate_sami3_direct_phi_run_strict.txt`: `ok`
- `waccmx_sami3_phi_24pkt/validate_wxsami3_live_packet_contract.txt`: `ok`
- `waccmx_sami3_phi_24pkt/validate_wxsami3_runtime_map.txt`: `ok`
- `waccmx_sami3_phi_24pkt/validate_wxsami3_source_flag_balance.txt`: `ok`
- `waccmx_sami3_phi_24pkt/validate_wxsami3_time_axis.txt`: `ok`
- `waccmx_sami3_phi_24pkt/validate_wxsami3_topblend_policy.txt`: `ok`

## Production Contract

- Diagnostic contract: `ok`
- Production-readiness gate: `FAIL`
- Source bVol skipped above target Lmax: `0.999595965103914`
- Runtime valid fraction: `0.9574468085106383`

## Bottom Line

The archive supports a fast integrated-prototype statement:

```text
WACCM-X CAM phys_state(:) live neutral packets reach SAMI3.
REMIX/Voltron runtime POT reaches SAMI3 as direct-MPI phi frames.
SAMI3-derived scalar moments can be ingested by RAIJU/GAMERA with conservative blending.
The current downstream adapter remains diagnostic/prototype because of the RAIJU target-domain source-volume issue.
```
