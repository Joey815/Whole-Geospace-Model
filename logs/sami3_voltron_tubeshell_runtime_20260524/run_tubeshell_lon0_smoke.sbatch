#!/bin/bash
#SBATCH -J sami3_tubeshell_smoke
#SBATCH -p intel
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=01:00:00
#SBATCH -o /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_voltron_tubeshell_20260524/slurm-%j.out

set -euo pipefail

ROOT="/home/jiaoy_group/jiaoy/data/MAGE1.25"
RUN_DIR="/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_voltron_tubeshell_20260524"
VOLTRON_EXE="/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/bin/voltron.x"

echo "job_id=${SLURM_JOB_ID}"
echo "partition=${SLURM_JOB_PARTITION}"
echo "node_list=${SLURM_JOB_NODELIST}"
echo "start_time=$(date '+%F %T %z')"
echo "run_dir=${RUN_DIR}"
echo "voltron_exe=${VOLTRON_EXE}"

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

cd "${RUN_DIR}"
ln -sfn "${VOLTRON_EXE}" ./voltron.x

echo "hostname=$(hostname)"
echo "python=$(command -v python)"
echo "omp_threads=${OMP_NUM_THREADS}"
echo "kmp_stacksize=${KMP_STACKSIZE}"
echo "omp_stacksize=${OMP_STACKSIZE}"
echo "ldd_missing=$(ldd ./voltron.x | grep -c 'not found' || true)"
echo

echo "===== BASELINE TUBESHELL SMOKE ====="
./voltron.x tinyCase_base_control_tubeshell.xml > base_control_tubeshell.log 2>&1

echo "===== VOLTRON TUBESHELL LON0 PRODUCT SMOKE ====="
./voltron.x tinyCase_sami3_moments_tubeshell_lon0_D005_P005_stateTiote.xml > tubeshell_lon0_D005_P005_stateTiote.log 2>&1

echo "run_complete=1"
echo "end_time=$(date '+%F %T %z')"
ls -lh sami3_moments_*tubeshell*.h5 | sed -n '1,120p'
