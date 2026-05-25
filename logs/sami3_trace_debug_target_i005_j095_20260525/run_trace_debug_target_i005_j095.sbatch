#!/bin/bash
#SBATCH -J trace_i5j95
#SBATCH -p intel
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=01:00:00
#SBATCH -o /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_trace_debug_target_i005_j095_20260525/slurm-%j.out

set -euo pipefail

ROOT="/home/jiaoy_group/jiaoy/data/MAGE1.25"
RUN_DIR="/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_trace_debug_target_i005_j095_20260525"
VOLTRON_EXE="/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/bin/voltron.x"

source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
module purge >/dev/null 2>&1
module load intel/oneapi/2023.2.0
module load intel/hdf5/1.13.0/intel2023.2_impi2023.2

source "${ROOT}/tools/bootstrap_kaipy_minimal_env.sh" "${ROOT}" "${ROOT}/kaipy"
source "${ROOT}/kaiju/scripts/setupEnvironment.sh"

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-8}"
export MPI_TYPE_DEPTH="${MPI_TYPE_DEPTH:-32}"
export KMP_STACKSIZE="${KMP_STACKSIZE:-512M}"
export OMP_STACKSIZE="${OMP_STACKSIZE:-512M}"
export MKL_NUM_THREADS=1
export LD_LIBRARY_PATH="/apps/support/intel_spr_rocky8.9/oneapi/2023.2.0/compiler/2023.2.0/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"

export VOLTRON_TRACE_DEBUG_FILE="${RUN_DIR}/sami3_trace_debug_target_i005_j095.traceDebug.h5"
export VOLTRON_TRACE_DEBUG_MAX_TUBES=8
export VOLTRON_TRACE_DEBUG_SOURCE_I=5
export VOLTRON_TRACE_DEBUG_SOURCE_J=95

cd "${RUN_DIR}"
ln -sfn "${VOLTRON_EXE}" ./voltron.x

echo "job_id=${SLURM_JOB_ID}"
echo "node_list=${SLURM_JOBNODELIST:-${SLURM_JOB_NODELIST}}"
echo "start_time=$(date '+%F %T %z')"
echo "voltron_exe=${VOLTRON_EXE}"
echo "trace_debug_file=${VOLTRON_TRACE_DEBUG_FILE}"
echo "trace_debug_max_tubes=${VOLTRON_TRACE_DEBUG_MAX_TUBES}"
echo "trace_debug_source_i=${VOLTRON_TRACE_DEBUG_SOURCE_I}"
echo "trace_debug_source_j=${VOLTRON_TRACE_DEBUG_SOURCE_J}"
echo "ldd_missing=$(ldd ./voltron.x | grep -c 'not found' || true)"

echo "===== TRACE DEBUG TARGET I005 J095 ====="
./voltron.x tinyCase_sami3_trace_debug_target_i005_j095.xml > trace_debug_target_i005_j095.log 2>&1

echo "run_complete=1"
echo "end_time=$(date '+%F %T %z')"
ls -lh sami3_trace_debug_target_i005_j095.traceDebug.h5 sami3_moments_active_bvol_ledger_smoke2*.h5 | sed -n '1,160p'
