# WACCM-X/SAMI3 Direct-MPI Neutral Cadence Archive

run_dir: /home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_neutral_doneaware_dt300_20260525_0000
job_id: 7670231
job_name: wxsami3_ndone
state: COMPLETED
exit_code: 0:0
elapsed: 00:08:52
node: qhcn119
batch_MaxRSS: 64922552K
overall: ok

This archive captures the first completed direct-MPI cadence run where SAMI3
received two live WACCM-X neutral packets, three direct Voltron/REMIX phi
frames, and a done signal without hanging on a header/done ordering mismatch.

Key gates:

- `validate_wxsami3_time_axis.txt`: `overall=ok`
- `validate_sami3_direct_phi_run_strict.txt`: `overall=ok`
- `validate_wxsami3_live_packet_contract.txt`: `overall=ok`
- `validate_wxsami3_source_flag_balance.txt`: `overall=ok`
- `validate_wxsami3_topblend_policy.txt`: `overall=ok`
- `validate_wxsami3_runtime_map.txt`: `overall=ok`
- `validate_remix_sami3_phi_payload.txt`: `overall=ok`

Important evidence:

- neutral packet 0: 32 SAMI3 workers received hour `0.0`
- neutral packet 1: 32 SAMI3 workers received hour `0.0833333358`
- phi frames: indices `0, 1, 2`, hours `0.0, 0.0833333358, 0.166666672`
- CESM/WACCM-X sent `done_value=2`
- Voltron direct phi sent `done=3`
- SAMI3 reached `MASTER: All Done!`

Primary files:

- `sami3_online_receiver.out`
- `waccmx_cesm.out`
- `voltron_runtime_direct.out`
- `slurm-7670231.out`
- `sacct_7670231.txt`
- `phi_payload_summary.txt`
- `wxsami3_live_meta.json`
- `recv_qc_compare_pkt000000.txt`
- `recv_qc_compare_pkt000001.txt`
- `live_dump_summary_pkt000000.txt`
- `live_dump_summary_pkt000001.txt`
- `replay_builder_pkt000000.out`
- `replay_builder_pkt000001.out`
