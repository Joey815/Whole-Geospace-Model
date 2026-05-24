#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python}"
TREE_ROOT="${TREE_ROOT:-/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523}"
SAMI3_RUN_DIR="${SAMI3_RUN_DIR:-/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_online_stubpayload_20231013_0000}"
OUT_PREFIX="${OUT_PREFIX:-${TREE_ROOT}/analysis/sami3_moments_stubpayload_20260523}"
OUT_DSOVERB_PREFIX="${OUT_DSOVERB_PREFIX:-${TREE_ROOT}/analysis/sami3_moments_stubpayload_ds_over_B_20260524}"
DIAG_PREFIX="${DIAG_PREFIX:-${TREE_ROOT}/analysis/sami3_voltron_raiju_diag_stubpayload_20260523}"
DIAG_NFLUID1_PREFIX="${DIAG_NFLUID1_PREFIX:-${TREE_ROOT}/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_20260523}"
DIAG_MASSEQP_PREFIX="${DIAG_MASSEQP_PREFIX:-${TREE_ROOT}/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_massEq_total_20260524}"
DIAG_DSOVERB_PREFIX="${DIAG_DSOVERB_PREFIX:-${TREE_ROOT}/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_20260524}"
DIAG_LMLT_PREFIX="${DIAG_LMLT_PREFIX:-${TREE_ROOT}/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_l_mlt_20260524}"
DIAG_DSOVERB_LMLT_PREFIX="${DIAG_DSOVERB_LMLT_PREFIX:-${TREE_ROOT}/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_l_mlt_20260524}"
MAP_WEIGHTS_PREFIX="${MAP_WEIGHTS_PREFIX:-${TREE_ROOT}/analysis/sami3_to_raiju_weights_l_mlt_20260524}"
DIAG_DSOVERB_WEIGHTFILE_PREFIX="${DIAG_DSOVERB_WEIGHTFILE_PREFIX:-${TREE_ROOT}/analysis/sami3_voltron_raiju_diag_stubpayload_nfluid1_ds_over_B_weightfile_l_mlt_20260524}"
RAICPL_TEMPLATE="${RAICPL_TEMPLATE:-${TREE_ROOT}/analysis/runtime_ingest_blend_20260524/sami3_moments_base_control.raiCpl.Res.00000.h5}"

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_to_voltron_moments.py" \
  "${SAMI3_RUN_DIR}" \
  --out "${OUT_PREFIX}" \
  --format hdf5

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_to_voltron_moments.py" \
  "${SAMI3_RUN_DIR}" \
  --out "${OUT_DSOVERB_PREFIX}" \
  --format hdf5 \
  --weight-mode ds_over_B

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

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_moments_to_raiju_diag.py" \
  "${OUT_PREFIX}.h5" \
  --out "${DIAG_MASSEQP_PREFIX}" \
  --n-fluid-in 1 \
  --density-mode massEq \
  --pressure-mode total

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/validate_sami3_mage_moments.py" \
  "${OUT_PREFIX}.h5" \
  "${DIAG_MASSEQP_PREFIX}.h5" \
  --n-fluid-in 1 \
  --density-mode massEq \
  --pressure-mode total

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_moments_to_raiju_diag.py" \
  "${OUT_DSOVERB_PREFIX}.h5" \
  --out "${DIAG_DSOVERB_PREFIX}" \
  --n-fluid-in 1

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/validate_sami3_mage_moments.py" \
  "${OUT_DSOVERB_PREFIX}.h5" \
  "${DIAG_DSOVERB_PREFIX}.h5" \
  --n-fluid-in 1

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_moments_to_raiju_diag.py" \
  "${OUT_PREFIX}.h5" \
  --out "${DIAG_LMLT_PREFIX}" \
  --n-fluid-in 1 \
  --raicpl-template "${RAICPL_TEMPLATE}" \
  --mapping-mode l_mlt

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/validate_sami3_mage_moments.py" \
  "${OUT_PREFIX}.h5" \
  "${DIAG_LMLT_PREFIX}.h5" \
  --n-fluid-in 1

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_moments_to_raiju_diag.py" \
  "${OUT_DSOVERB_PREFIX}.h5" \
  --out "${DIAG_DSOVERB_LMLT_PREFIX}" \
  --n-fluid-in 1 \
  --raicpl-template "${RAICPL_TEMPLATE}" \
  --mapping-mode l_mlt

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/validate_sami3_mage_moments.py" \
  "${OUT_DSOVERB_PREFIX}.h5" \
  "${DIAG_DSOVERB_LMLT_PREFIX}.h5" \
  --n-fluid-in 1

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/build_sami3_to_raiju_weights.py" \
  "${OUT_DSOVERB_PREFIX}.h5" \
  --out "${MAP_WEIGHTS_PREFIX}" \
  --raicpl-template "${RAICPL_TEMPLATE}"

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/sami3_moments_to_raiju_diag.py" \
  "${OUT_DSOVERB_PREFIX}.h5" \
  --out "${DIAG_DSOVERB_WEIGHTFILE_PREFIX}" \
  --n-fluid-in 1 \
  --mapping-mode weights \
  --mapping-weight-file "${MAP_WEIGHTS_PREFIX}.h5"

"${PYTHON_BIN}" \
  "${TREE_ROOT}/scripts/sami3_moments/validate_sami3_mage_moments.py" \
  "${OUT_DSOVERB_PREFIX}.h5" \
  "${DIAG_DSOVERB_WEIGHTFILE_PREFIX}.h5" \
  --n-fluid-in 1

"${PYTHON_BIN}" - "${DIAG_DSOVERB_LMLT_PREFIX}.h5" "${DIAG_DSOVERB_WEIGHTFILE_PREFIX}.h5" <<'PY'
import sys

import h5py
import numpy as np

left_path, right_path = sys.argv[1:3]
paths = (
    "RaiCplMomentsOnly/Pavg",
    "RaiCplMomentsOnly/Davg",
    "RaiCplMomentsOnly/Pstd",
    "RaiCplMomentsOnly/Dstd",
    "RaiCplMomentsOnly/tiote",
)
with h5py.File(left_path, "r") as left, h5py.File(right_path, "r") as right:
    max_abs = 0.0
    max_rel = 0.0
    for path in paths:
        left_arr = left[path][:].astype(np.float64)
        right_arr = right[path][:].astype(np.float64)
        diff = left_arr - right_arr
        item_max = float(np.max(np.abs(diff)))
        item_rel = float(np.max(np.abs(diff) / np.maximum(np.abs(left_arr), 1.0)))
        print("{0} max_abs={1} max_rel={2}".format(path, item_max, item_rel))
        max_abs = max(max_abs, item_max)
        max_rel = max(max_rel, item_rel)
    if max_abs > 5.0e-3 and max_rel > 1.0e-6:
        raise SystemExit("weight-file mapping is not equivalent to inline l_mlt")
print("weight-file mapping equivalence max_abs={0} max_rel={1}".format(max_abs, max_rel))
PY

echo "SAMI3 MAGE moments smoke passed"
