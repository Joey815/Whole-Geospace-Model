#!/bin/bash -l
#SBATCH --job-name=sami3_phi_bridge
#SBATCH --partition=intel
#SBATCH --nodes=1
#SBATCH --ntasks=34
#SBATCH --cpus-per-task=1
#SBATCH --mem=296G
#SBATCH --time=00:35:00
#SBATCH --output=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/sami3_online_receiver_remix_phi_weimer_voltron_bridge_20260524_0000/slurm-%j.out
#SBATCH --error=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/sami3_online_receiver_remix_phi_weimer_voltron_bridge_20260524_0000/slurm-%j.err

set -eo pipefail

BASE=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official
COLLAB=/home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
MAGE=/home/jiaoy_group/jiaoy/data/MAGE1.25
SRC=$BASE/runs/sami3_waccmx_neutral_esmf_msis_top_weimer_20231013_0000
SAMI_WORK=$BASE/work/sami3-3.22_online_mpi_openmpi_remix_phi_20260524
RUN=$BASE/runs/sami3_online_receiver_remix_phi_weimer_voltron_bridge_20260524_0000
PAY=$BASE/runs/waccmx_replay_payload_from_live_dump_20260523/waccmx_neutral_rank
VOLTRON_TEMPLATE=$MAGE/experiments/remix_sami3_live_phi_payload_writer_20260524
VOLTRON_RUN=$RUN/voltron_phi_writer
VOLTRON_EXE=$MAGE/build_gr_sami3_moments_20260523/bin/voltron.x
VOLTRON_XML=gtrd_20211204_0500_0510-waccmxfile-smoke.xml
WEIMER_GRID=$BASE/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/weimer_grid.dat
PHI_PAYLOAD=$VOLTRON_RUN/remix_sami3_phi_payload_from_voltron_bridge.bin
PORT=$RUN/waccmx_sami3_online_port.txt
SENDER=$BASE/bin/wxsami3_neutral_phi_sender_openmpi
SENDER_SRC=$COLLAB/scripts/wxsami3_neutral_phi_sender_stub.c
DVM_URI=$RUN/prte_dvm.uri
DVM_PID=$RUN/prte_dvm.pid

mkdir -p "$RUN" "$VOLTRON_RUN" "$BASE/bin"

cleanup() {
  if [ -n "${sami3_pid:-}" ]; then
    kill "$sami3_pid" 2>/dev/null || true
  fi
  if [ -s "${DVM_URI:-}" ]; then
    pterm --dvm-uri "file:$DVM_URI" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "RUN_DIR=$RUN"
echo "VOLTRON_RUN=$VOLTRON_RUN"
echo "PAYLOAD_PREFIX=$PAY"
echo "PHI_PAYLOAD=$PHI_PAYLOAD"
echo "PORT=$PORT"
echo "START=$(date)"
echo "HOST=$(hostname)"

echo "--- stage 1: Voltron/REMIX phi payload generation"
source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
module purge >/dev/null 2>&1 || true
module load intel/oneapi/2023.2.0
module load intel/hdf5/1.13.0/intel2023.2_impi2023.2

source "$MAGE/tools/bootstrap_kaipy_minimal_env.sh" "$MAGE" "$MAGE/kaipy"
source "$MAGE/kaiju/scripts/setupEnvironment.sh"

export OMP_NUM_THREADS=8
export MPI_TYPE_DEPTH="${MPI_TYPE_DEPTH:-32}"
export KMP_STACKSIZE="${KMP_STACKSIZE:-512M}"
export OMP_STACKSIZE="${OMP_STACKSIZE:-512M}"
export MKL_NUM_THREADS=1
export LD_LIBRARY_PATH="/apps/support/intel_spr_rocky8.9/oneapi/2023.2.0/compiler/2023.2.0/linux/compiler/lib/intel64_lin:${LD_LIBRARY_PATH:-}"
export WACCMX_SAMI3_PHI_PAYLOAD_FILE="$PHI_PAYLOAD"
export WACCMX_SAMI3_WEIMER_GRID="$WEIMER_GRID"
export WACCMX_SAMI3_PHI_HEMI=NORTH
export WACCMX_SAMI3_PHI_FRAME_HOUR=0.0
export WACCMX_SAMI3_PHI_VALID_UNTIL_HOUR=1.0e30

rsync -a \
  --exclude='slurm-*' \
  --exclude='*.out' \
  --exclude='remix_sami3_phi_payload*.bin' \
  --exclude='waccmx_voltron_forward_package.h5' \
  --exclude='waccmx_voltron_feedback_package.h5' \
  "$VOLTRON_TEMPLATE"/ "$VOLTRON_RUN"/
ln -sfn "$VOLTRON_EXE" "$VOLTRON_RUN/voltron.x"
rm -f "$PHI_PAYLOAD" "$VOLTRON_RUN"/waccmx_voltron_forward_package.h5 "$VOLTRON_RUN"/waccmx_voltron_feedback_package.h5

(
  cd "$VOLTRON_RUN"
  echo "voltron_exe=$VOLTRON_EXE"
  echo "weimer_grid=$WEIMER_GRID"
  echo "omp_threads=$OMP_NUM_THREADS"
  echo "ldd_missing=$(ldd ./voltron.x | grep -c 'not found' || true)"
  ./voltron.x "$VOLTRON_XML"
) > "$VOLTRON_RUN/live_phi_payload_writer_bridge.out" 2>&1 &
voltron_pid=$!

phi_ready=0
for i in $(seq 1 180); do
  if [ -s "$PHI_PAYLOAD" ]; then
    size1=$(stat -c '%s' "$PHI_PAYLOAD")
    sleep 1
    size2=$(stat -c '%s' "$PHI_PAYLOAD")
    if [ "$size1" = "$size2" ] && [ "$size2" -gt 48000 ]; then
      phi_ready=1
      break
    fi
  fi
  if ! kill -0 "$voltron_pid" 2>/dev/null; then
    break
  fi
  sleep 1
done

if [ "$phi_ready" != 1 ]; then
  echo "ERROR: Voltron did not produce a stable phi payload: $PHI_PAYLOAD" >&2
  tail -160 "$VOLTRON_RUN/live_phi_payload_writer_bridge.out" >&2 || true
  wait "$voltron_pid" || true
  exit 40
fi

kill "$voltron_pid" 2>/dev/null || true
sleep 2
if kill -0 "$voltron_pid" 2>/dev/null; then
  kill -9 "$voltron_pid" 2>/dev/null || true
fi
wait "$voltron_pid" 2>/dev/null || true

/usr/bin/python3 - <<PY > "$RUN/phi_payload_summary.txt"
from pathlib import Path
import struct
import numpy as np
p = Path("$PHI_PAYLOAD")
raw = p.read_bytes()
magic, version, nlat, nlon, nframes = struct.unpack_from("<5i", raw, 0)
off = 20
for iframe in range(nframes):
    frame_index = struct.unpack_from("<i", raw, off)[0]
    off += 4
    hour, valid_until = struct.unpack_from("<2f", raw, off)
    off += 8
    phi = np.frombuffer(raw, dtype="<f4", count=nlat*nlon, offset=off)
    off += 4*nlat*nlon
    print(f"path={p}")
    print(f"size={p.stat().st_size}")
    print(f"header={[magic, version, nlat, nlon, nframes]}")
    print(f"frame={iframe} frame_index={frame_index} hour={hour:.8g} valid_until={valid_until:.8g} min={float(phi.min()):.8g} max={float(phi.max()):.8g} finite={bool(np.isfinite(phi).all())} nonzero={int(np.count_nonzero(phi))}")
PY
cat "$RUN/phi_payload_summary.txt"

echo "--- stage 2: SAMI3 online receiver plus single-peer neutral+phi sender"
module purge >/dev/null 2>&1 || true
export PATH=/apps/support/intel_spr_rocky8.9/openmpi/5.0.3/gcc8.5.0/bin:$PATH
export LD_LIBRARY_PATH=/apps/support/intel_spr_rocky8.9/openmpi/5.0.3/gcc8.5.0/lib:${LD_LIBRARY_PATH:-}
export OMP_NUM_THREADS=1
export WXSAMI3_RECV_QC=1
export SAMI3_USE_ONLINE_PHI_WEIMER=1

if [ ! -f "$RUN/.prepared_from_msis_top_smoke" ]; then
  rsync -a \
    --exclude='slurm-*' \
    --exclude='*.out' \
    "$SRC"/ "$RUN"/
  touch "$RUN/.prepared_from_msis_top_smoke"
fi

mpicc -O2 -Wall -Wextra -o "$SENDER" "$SENDER_SRC"

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
s = re.sub(r'^\s*maxstep\s*=.*?,', '  maxstep  =   20,', s, flags=re.MULTILINE)
s = re.sub(r'^\s*hrmax\s*=.*?,', '  hrmax = .020000,', s, flags=re.MULTILINE)
s = re.sub(r'^\s*tphi\s*=.*?,', '  tphi       = 1.,', s, flags=re.MULTILINE)
s = s.replace('  lwaccmx_neutral = .false.,', '  lwaccmx_neutral = .true.,')
s = re.sub(r"\s*waccmx_neutral_prefix\s*=\s*'.*?',",
           "  waccmx_neutral_prefix = '$PAY',", s)
if 'lwaccmx_neutral_online' not in s:
    marker = "  waccmx_neutral_prefix = '$PAY',"
    repl = marker + "\n  lwaccmx_neutral_online = .true.,\n  waccmx_online_port_file = '$PORT',"
    s = s.replace(marker, repl)
else:
    s = s.replace('  lwaccmx_neutral_online = .false.,', '  lwaccmx_neutral_online = .true.,')
    s = re.sub(r"\s*waccmx_online_port_file\s*=\s*'.*?',",
               "  waccmx_online_port_file = '$PORT',", s)
p.write_text(s)
PY

rm -f "$PORT" "$DVM_URI" "$DVM_PID" sami3_online_receiver.out neutral_phi_sender.out \
  recv_qc_compare.txt phi_weimer.inp

echo "MPICC=$(command -v mpicc)"
echo "PRTE=$(command -v prte)"
echo "PRUN=$(command -v prun)"
echo "WXSAMI3_RECV_QC=$WXSAMI3_RECV_QC"
echo "SAMI3_USE_ONLINE_PHI_WEIMER=$SAMI3_USE_ONLINE_PHI_WEIMER"
echo "NAMELIST MPI phi Voltron bridge: maxstep=20 hrmax=.020000 tphi=1."

prte --daemonize --report-uri "$DVM_URI" --report-pid "$DVM_PID" --host "$(hostname)"
for i in $(seq 1 60); do
  [ -s "$DVM_URI" ] && break
  sleep 1
done
if [ ! -s "$DVM_URI" ]; then
  echo "ERROR: PRRTE DVM did not create URI file: $DVM_URI" >&2
  exit 30
fi

timeout 900s prun --dvm-uri "file:$DVM_URI" \
  -x "WXSAMI3_RECV_QC=$WXSAMI3_RECV_QC" \
  -x "SAMI3_USE_ONLINE_PHI_WEIMER=$SAMI3_USE_ONLINE_PHI_WEIMER" \
  -n 33 ./sami3.x > "$RUN/sami3_online_receiver.out" 2>&1 &
sami3_pid=$!

for i in $(seq 1 180); do
  [ -s "$PORT" ] && break
  sleep 1
done

if [ ! -s "$PORT" ]; then
  echo "ERROR: SAMI3 did not create port file: $PORT" >&2
  kill "$sami3_pid" 2>/dev/null || true
  wait "$sami3_pid" || true
  pterm --dvm-uri "file:$DVM_URI" || true
  exit 20
fi

timeout 900s prun --dvm-uri "file:$DVM_URI" -n 1 "$SENDER" "$PORT" "$PAY" 0 0.0 "$PHI_PAYLOAD" > "$RUN/neutral_phi_sender.out" 2>&1
wait "$sami3_pid"
sami3_pid=

pterm --dvm-uri "file:$DVM_URI" || true

/usr/bin/python3 "$BASE/scripts/compare_wxsami3_recv_qc.py" \
  --payload-prefix "$PAY" \
  --receiver-log "$RUN/sami3_online_receiver.out" \
  > "$RUN/recv_qc_compare.txt"

echo "--- neutral+phi sender tail"
tail -120 "$RUN/neutral_phi_sender.out"
echo "--- sami3 online receiver markers"
grep -E 'SAMI3_USE_ONLINE_PHI_WEIMER|WACCMX_PHI_RECV|hrutw2|nweimer|calling potpphi|WACCMX online|WACCMX_RECV_QC|WACCMX_RECV_SOURCE_FLAGS|MASTER: All Done|fatal|forrtl|NaN|Abort|EOF|header mismatch' "$RUN/sami3_online_receiver.out" | tail -320 || true
echo "--- receiver QC compare"
cat "$RUN/recv_qc_compare.txt"
echo "END=$(date)"
