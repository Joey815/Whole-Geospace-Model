#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python}"
TREE_ROOT="${TREE_ROOT:-/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523}"
SAMI3_RUN_DIR="${SAMI3_RUN_DIR:-/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000}"
OUT_PREFIX="${OUT_PREFIX:-${TREE_ROOT}/analysis/sami3_moments_stubpayload_20260523}"
DIAG_PREFIX="${DIAG_PREFIX:-${TREE_ROOT}/analysis/sami3_voltron_raiju_diag_stubpayload_20260523}"
DIAG_NFLUID1_PREFIX="${DIAG_NFLUID1_PREFIX:-${TREE_ROOT}/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_20260523}"

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_to_voltron_moments.py" \
  "${SAMI3_RUN_DIR}" \
  --out "${OUT_PREFIX}" \
  --format hdf5

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_moments_to_raiju_diag.py" \
  "${OUT_PREFIX}.h5" \
  --out "${DIAG_PREFIX}" \
  --n-fluid-in 0

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/validate_sami3_mage_moments.py" \
  "${OUT_PREFIX}.h5" \
  "${DIAG_PREFIX}.h5" \
  --n-fluid-in 0

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_moments_to_raiju_diag.py" \
  "${OUT_PREFIX}.h5" \
  --out "${DIAG_NFLUID1_PREFIX}" \
  --n-fluid-in 1

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/validate_sami3_mage_moments.py" \
  "${OUT_PREFIX}.h5" \
  "${DIAG_NFLUID1_PREFIX}.h5" \
  --n-fluid-in 1

echo "SAMI3 MAGE moments smoke passed"
