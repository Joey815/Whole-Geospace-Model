# Reproduce And Revalidate

Set the collaboration root:

```bash
cd /online1/jiaoy_group/jiaoy/MAGE1.25/waccmx-sami3-collab-20260524
```

Revalidate the WACCM-X -> SAMI3 live packet contract:

```bash
python3 scripts/validate_wxsami3_live_packet_contract.py \
  --run-dir /online1/jiaoy_group/jiaoy/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_directmpi_nosmoke_dt300_24pkt_24phi_hrmax8_maxstep2800_20260526_0000 \
  --expected-packets 24 \
  --expected-source-columns 13824 \
  --expected-receiver-ranks 32 \
  --expected-n2-mode invalid \
  --expect-n2-residual \
  --expect-he-native \
  --require-zero-unknown-source-flags
```

Revalidate the SAMI3 -> RAIJU/GAMERA long-run smoke:

```bash
python3 scripts/validate_sami3_raiju_longrun.py \
  --run-dir /online1/jiaoy_group/jiaoy/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_tiote_long1800_20260526 \
  --label long1800_exclude_lmax_dens005 \
  --expect-slurm
```

The HDF5 mapping-product and summary validators require a Python environment with `h5py`; archived outputs are under `validators/raiju_density_*` and `validators/raiju_density_tiote_*`.

Regenerate this archive:

```bash
python3 scripts/archive_integrated_prototype_result.py
```
