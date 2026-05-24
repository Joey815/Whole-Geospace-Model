#!/bin/bash
#SBATCH -J sami3_rai_long900
#SBATCH -p intel
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH -o /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long900_20260525/slurm-%j.out

set -euo pipefail

ROOT="/home/jiaoy_group/jiaoy/data/MAGE1.25"
SRC_DIR="${ROOT}/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long300_20260524"
RUN_DIR="${ROOT}/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_long900_20260525"
VOLTRON_EXE="${ROOT}/build_gr_sami3_moments_20260523/bin/voltron.x"

mkdir -p "${RUN_DIR}"

echo "job_id=${SLURM_JOB_ID:-manual}"
echo "partition=${SLURM_JOB_PARTITION:-manual}"
echo "node_list=${SLURM_JOB_NODELIST:-manual}"
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
for name in lfmD.h5 bcwind.h5 raijuconfig.h5; do
  target="$(readlink -f "${SRC_DIR}/${name}")"
  ln -sfn "${target}" "${name}"
done
cp -f "${SRC_DIR}/tinyCase_base_control_long300.xml" tinyCase_base_control_long900.xml
cp -f "${SRC_DIR}/tinyCase_sami3_moments_dsB_lmlt_recommended_long300.xml" tinyCase_sami3_moments_dsB_lmlt_recommended_long900.xml
perl -pi -e 's/tFin="300\.0"/tFin="900.0"/g; s/long300/long900/g' \
  tinyCase_base_control_long900.xml \
  tinyCase_sami3_moments_dsB_lmlt_recommended_long900.xml
rm -f sami3_moments_*long900*.h5 sami3_moments_*long900*.Res.XXXXX.h5 \
  base_control_long900.log dsB_lmlt_recommended_long900.log

echo "hostname=$(hostname)"
echo "python=$(command -v python)"
echo "omp_threads=${OMP_NUM_THREADS}"
echo "kmp_stacksize=${KMP_STACKSIZE}"
echo "omp_stacksize=${OMP_STACKSIZE}"
echo "ldd_missing=$(ldd ./voltron.x | grep -c 'not found' || true)"
echo

echo "===== BASELINE LONG900 ====="
./voltron.x tinyCase_base_control_long900.xml > base_control_long900.log 2>&1

echo "===== RECOMMENDED LONG900 ====="
./voltron.x tinyCase_sami3_moments_dsB_lmlt_recommended_long900.xml > dsB_lmlt_recommended_long900.log 2>&1

echo "run_complete=1"
echo "end_time=$(date '+%F %T %z')"
ls -lh sami3_moments_*long900*.h5 | sed -n '1,160p'
