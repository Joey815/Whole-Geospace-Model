# SAMI3 -> RAIJU/GAMERA Longrun Archive Summary

run_dir: /online1/jiaoy_group/jiaoy/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_tiote_long1800_20260526
label: long1800_exclude_lmax_dens005_tiote
job_id: 7678667
validator_returncode: 0
summary_returncode: 0
summary_validation_returncode: 0
mapping_product_returncode: 0
copied_files: 5
overall: ok

Validator text output:

- validate_sami3_raiju_longrun.txt
- validate_sami3_raiju_summary.txt
- validate_sami3_raiju_mapping_product.txt
- validate_sami3_raiju_tiote_hook.txt
- tiote_vs_density_only_comparison.txt
- validate_sami3_raiju_production_contract_diagnostic.txt
- validate_sami3_raiju_production_contract_production.txt
- run_exclude_lmax_density_tiote_long1800.sbatch

Production-contract guardrail:

- `diagnostic-contract` mode passes and classifies this product as
  `diagnostic_only`.
- `production-readiness` mode intentionally fails because
  `source_domain_skipped_above_lmax_bvol_fraction=0.999595965103914`.
