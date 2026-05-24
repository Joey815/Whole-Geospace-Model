#!/bin/bash -l
#SBATCH --job-name=sami3_vrtd
#SBATCH --partition=intel
#SBATCH --nodes=1
#SBATCH --ntasks=35
#SBATCH --cpus-per-task=1
#SBATCH --time=00:30:00
#SBATCH --output=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/sami3_intelmpi_voltron_runtime_direct_phi_20260525_0000/slurm-%j.out
#SBATCH --error=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/sami3_intelmpi_voltron_runtime_direct_phi_20260525_0000/slurm-%j.err

set -eo pipefail

source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
module purge >/dev/null 2>&1 || true
module load intel/oneapi/2023.2.0
module load intel/hdf5/1.13.0/intel2023.2_impi2023.2

BASE=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official
COLLAB=/home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
MAGE=/home/jiaoy_group/jiaoy/data/MAGE1.25
SRC=$BASE/runs/sami3_waccmx_neutral_esmf_msis_top_weimer_20231013_0000
SAMI_WORK=$BASE/work/sami3-3.22_online_mpi_intelmpi_direct_phi_20260525
RUN=$BASE/runs/sami3_intelmpi_voltron_runtime_direct_phi_20260525_0000
PAY=$BASE/runs/waccmx_replay_payload_from_live_dump_20260523/waccmx_neutral_rank
VOLTRON_TEMPLATE=$MAGE/experiments/remix_sami3_live_phi_payload_writer_20260524
VOLTRON_RUN=$RUN/voltron_runtime_direct_phi
VOLTRON_EXE=$MAGE/build_gr_sami3_phi_direct_mpi_ifort_20260525/bin/voltron.x
VOLTRON_XML=gtrd_20211204_0500_0510-waccmxfile-smoke.xml
WEIMER_GRID=$BASE/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/weimer_grid.dat
PHI_PAYLOAD=$VOLTRON_RUN/remix_sami3_phi_payload_runtime_direct.bin
NEUTRAL_PORT=$RUN/waccmx_sami3_online_port.txt
PHI_PORT=$RUN/sami3_direct_phi_port.txt
NEUTRAL_SENDER=$BASE/bin/wxsami3_neutral_sender_intelmpi

export WXSAMI3_RECV_QC=1
export SAMI3_USE_ONLINE_PHI_WEIMER=1
export SAMI3_PHI_DIRECT_PORT_FILE=$PHI_PORT
export I_MPI_HYDRA_BOOTSTRAP=slurm
export I_MPI_FABRICS=shm:ofi
export I_MPI_SPAWN=on
export FI_MLX_NS_ENABLE=1
export OMP_NUM_THREADS=1
export KMP_STACKSIZE=512M
export OMP_STACKSIZE=512M
export MKL_NUM_THREADS=1
export LD_LIBRARY_PATH=/apps/support/intel_spr_rocky8.9/oneapi/2023.2.0/compiler/2023.2.0/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}

mkdir -p "$RUN" "$VOLTRON_RUN"

cleanup() {
  if [ -n "${neutral_pid:-}" ]; then kill "$neutral_pid" 2>/dev/null || true; fi
  if [ -n "${voltron_pid:-}" ]; then kill "$voltron_pid" 2>/dev/null || true; fi
  if [ -n "${sami3_pid:-}" ]; then kill "$sami3_pid" 2>/dev/null || true; fi
}
trap cleanup EXIT

if [ ! -f "$RUN/.prepared_from_msis_top_smoke" ]; then
  rsync -a \
    --exclude='slurm-*' \
    --exclude='*.out' \
    "$SRC"/ "$RUN"/
  touch "$RUN/.prepared_from_msis_top_smoke"
fi

rsync -a \
  --exclude='slurm-*' \
  --exclude='*.out' \
  --exclude='remix_sami3_phi_payload*.bin' \
  --exclude='waccmx_voltron_forward_package.h5' \
  --exclude='waccmx_voltron_feedback_package.h5' \
  "$VOLTRON_TEMPLATE"/ "$VOLTRON_RUN"/
ln -sfn "$VOLTRON_EXE" "$VOLTRON_RUN/voltron.x"
rm -f "$PHI_PAYLOAD" "$VOLTRON_RUN"/waccmx_voltron_forward_package.h5 \
  "$VOLTRON_RUN"/waccmx_voltron_feedback_package.h5

python3 - <<PY
from pathlib import Path
p = Path("$VOLTRON_RUN/$VOLTRON_XML")
s = p.read_text()
s = s.replace('<time tFin="6.0" />', '<time tFin="10.25" />')
s = s.replace('stopAfterExport="T"', 'stopAfterExport="F"')
p.write_text(s)
PY

rm -f "$RUN/sami3.x"
cp "$SAMI_WORK/sami3.x" "$RUN/sami3.x"
cp "$SAMI_WORK/waccmx_neutral_mod.f90" "$RUN/waccmx_neutral_mod.f90"
cp "$SAMI_WORK/namelist_mod.f90" "$RUN/namelist_mod.f90"
cp "$SAMI_WORK/potential.f90" "$RUN/potential.f90"
cp "$SAMI_WORK/sami3-3.22.f90" "$RUN/sami3-3.22.f90"

cd "$RUN"
python3 - <<PY
from pathlib import Path
import re
p = Path('sami3-3.22.namelist')
s = p.read_text()
s = re.sub(r'^\\s*maxstep\\s*=.*?,', '  maxstep  =   20,', s, flags=re.MULTILINE)
s = re.sub(r'^\\s*hrmax\\s*=.*?,', '  hrmax = .020000,', s, flags=re.MULTILINE)
s = re.sub(r'^\\s*tphi\\s*=.*?,', '  tphi       = 1.,', s, flags=re.MULTILINE)
s = s.replace('  lwaccmx_neutral = .false.,', '  lwaccmx_neutral = .true.,')
s = re.sub(r"\\s*waccmx_neutral_prefix\\s*=\\s*'.*?',",
           "  waccmx_neutral_prefix = '$PAY',", s)
if 'lwaccmx_neutral_online' not in s:
    marker = "  waccmx_neutral_prefix = '$PAY',"
    repl = marker + "\\n  lwaccmx_neutral_online = .true.,\\n  waccmx_online_port_file = '$NEUTRAL_PORT',"
    s = s.replace(marker, repl)
else:
    s = s.replace('  lwaccmx_neutral_online = .false.,', '  lwaccmx_neutral_online = .true.,')
    s = re.sub(r"\\s*waccmx_online_port_file\\s*=\\s*'.*?',",
               "  waccmx_online_port_file = '$NEUTRAL_PORT',", s)
p.write_text(s)
PY

rm -f "$NEUTRAL_PORT" "$PHI_PORT" sami3_online_receiver.out neutral_sender.out \
  voltron_runtime_direct.out recv_qc_compare.txt

echo "RUN_DIR=$RUN"
echo "VOLTRON_RUN=$VOLTRON_RUN"
echo "VOLTRON_EXE=$VOLTRON_EXE"
echo "PAYLOAD_PREFIX=$PAY"
echo "PHI_PAYLOAD=$PHI_PAYLOAD"
echo "NEUTRAL_PORT=$NEUTRAL_PORT"
echo "PHI_PORT=$PHI_PORT"
echo "START=$(date)"
echo "HOST=$(hostname)"
echo "MPI=$(command -v mpirun)"
echo "SAMI3_EXE=$RUN/sami3.x"
echo "NEUTRAL_SENDER=$NEUTRAL_SENDER"
echo "SAMI3_USE_ONLINE_PHI_WEIMER=$SAMI3_USE_ONLINE_PHI_WEIMER"
echo "SAMI3_PHI_DIRECT_PORT_FILE=$SAMI3_PHI_DIRECT_PORT_FILE"

mpirun -n 33 ./sami3.x > "$RUN/sami3_online_receiver.out" 2>&1 &
sami3_pid=$!

for i in $(seq 1 180); do
  [ -s "$NEUTRAL_PORT" ] && break
  sleep 1
done
if [ ! -s "$NEUTRAL_PORT" ]; then
  echo "ERROR: SAMI3 did not create neutral port file: $NEUTRAL_PORT" >&2
  exit 20
fi

mpirun -n 1 "$NEUTRAL_SENDER" "$NEUTRAL_PORT" "$PAY" 0 0.0 \
  > "$RUN/neutral_sender.out" 2>&1 &
neutral_pid=$!

for i in $(seq 1 300); do
  [ -s "$PHI_PORT" ] && break
  sleep 1
done
if [ ! -s "$PHI_PORT" ]; then
  echo "ERROR: SAMI3 did not create direct phi port file: $PHI_PORT" >&2
  exit 21
fi

(
  cd "$VOLTRON_RUN"
  export WACCMX_SAMI3_PHI_PAYLOAD_FILE="$PHI_PAYLOAD"
  export WACCMX_SAMI3_PHI_DIRECT_PORT_FILE="$PHI_PORT"
  export WACCMX_SAMI3_WEIMER_GRID="$WEIMER_GRID"
  export WACCMX_SAMI3_PHI_HEMI=NORTH
  export WACCMX_SAMI3_PHI_FRAME_HOUR_OFFSET=0.0013888889
  export WACCMX_SAMI3_PHI_VALID_HOURS=0.0013888889
  export WACCMX_SAMI3_PHI_MAX_FRAMES=2
  export WACCMX_SAMI3_PHI_FINAL_VALID_UNTIL_HOUR=1.0e30
  export OMP_NUM_THREADS=8
  export KMP_STACKSIZE=512M
  export OMP_STACKSIZE=512M
  echo "voltron_exe=$VOLTRON_EXE"
  echo "weimer_grid=$WEIMER_GRID"
  echo "phi_payload=$PHI_PAYLOAD"
  echo "direct_phi_port=$PHI_PORT"
  echo "ldd_missing=$(ldd ./voltron.x | grep -c 'not found' || true)"
  mpirun -n 1 ./voltron.x "$VOLTRON_XML"
) > "$RUN/voltron_runtime_direct.out" 2>&1 &
voltron_pid=$!

wait "$sami3_pid"
wait "$neutral_pid"
wait "$voltron_pid"

/usr/bin/python3 "$BASE/scripts/compare_wxsami3_recv_qc.py" \
  --payload-prefix "$PAY" \
  --receiver-log "$RUN/sami3_online_receiver.out" \
  > "$RUN/recv_qc_compare.txt"

echo "--- neutral sender tail"
tail -80 "$RUN/neutral_sender.out"
echo "--- voltron runtime direct tail"
tail -160 "$RUN/voltron_runtime_direct.out"
echo "--- sami3 runtime direct markers"
grep -E 'SAMI3 direct phi|WACCMX_PHI_RECV|SAMI3_USE_ONLINE_PHI_WEIMER|WACCMX online|WACCMX_RECV_QC|WACCMX_RECV_SOURCE_FLAGS|MASTER: All Done|fatal|forrtl|NaN|Abort|EOF|header mismatch' "$RUN/sami3_online_receiver.out" | tail -360 || true
echo "--- recv qc compare"
cat "$RUN/recv_qc_compare.txt"
echo "END=$(date)"
