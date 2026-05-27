#!/bin/bash
#SBATCH -J sami3_exl_tiote
#SBATCH -p intel
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=03:00:00
#SBATCH -o /home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_tiote_long1800_20260526/slurm-%j.out

set -euo pipefail

ROOT="/home/jiaoy_group/jiaoy/data/MAGE1.25"
RUN_DIR="/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvol_overlap_exclude_lmax_tiote_long1800_20260526"
BASELINE_SOURCE_DIR="/home/jiaoy_group/jiaoy/data/MAGE1.25/kaiju_sami3_voltron_moments_20260523/analysis/runtime_ingest_tubeshell_bin_bvolcc_conservative_long1800_20260525"
VOLTRON_EXE="/home/jiaoy_group/jiaoy/data/MAGE1.25/build_gr_sami3_moments_20260523/bin/voltron.x"

LABEL_DENS="long1800_exclude_lmax_dens005"
LABEL_TIOTE="long1800_exclude_lmax_dens005_tiote"

echo "job_id=${SLURM_JOB_ID}"
echo "partition=${SLURM_JOB_PARTITION}"
echo "node_list=${SLURM_JOB_NODELIST}"
echo "start_time=$(date '+%F %T %z')"
echo "run_dir=${RUN_DIR}"
echo "voltron_exe=${VOLTRON_EXE}"
echo "mode=tubeshell_bin_bvol_overlap_exclude_lmax_density_then_tiote_long1800"
echo "baseline_reused_from=${BASELINE_SOURCE_DIR}"
echo "density_label=${LABEL_DENS}"
echo "tiote_label=${LABEL_TIOTE}"
echo "alphaDavg=0.05"
echo "alphaPavg=0.0"
echo "alphaPstd=0.0"
echo "alphaDstd=0.0"
echo "density_alphaTiote=0.0"
echo "tiote_alphaTiote=1.0"
echo "tiote_useStateTioteForIngest=T"

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

echo "===== BASELINE LONG1800 REUSED ====="
ls -lh "base_control_${LABEL_DENS}.log" "sami3_moments_base_control_${LABEL_DENS}.raiCpl.Res.00000.h5"
ls -lh "base_control_${LABEL_TIOTE}.log" "sami3_moments_base_control_${LABEL_TIOTE}.raiCpl.Res.00000.h5"

echo "===== SAMI3 EXCLUDE-LMAX DENSITY-ONLY LONG1800 ====="
./voltron.x "tinyCase_sami3_moments_dsB_lmlt_recommended_${LABEL_DENS}.xml" > "dsB_lmlt_recommended_${LABEL_DENS}.log" 2>&1

echo "===== SAMI3 EXCLUDE-LMAX DENSITY+TIOTE LONG1800 ====="
./voltron.x "tinyCase_sami3_moments_dsB_lmlt_recommended_${LABEL_TIOTE}.xml" > "dsB_lmlt_recommended_${LABEL_TIOTE}.log" 2>&1

echo "run_complete=1"
echo "end_time=$(date '+%F %T %z')"
ls -lh sami3_moments_*long1800_exclude_lmax*.h5 | sed -n '1,220p'
