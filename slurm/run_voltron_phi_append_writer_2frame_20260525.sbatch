#!/bin/bash -l
#SBATCH --job-name=vphi_ap2
#SBATCH --partition=intel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=00:20:00
#SBATCH --output=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/voltron_phi_append_writer_2frame_20260525_0000/slurm-%j.out
#SBATCH --error=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/voltron_phi_append_writer_2frame_20260525_0000/slurm-%j.err

set -eo pipefail

BASE=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official
MAGE=/home/jiaoy_group/jiaoy/data/MAGE1.25
RUN=$BASE/runs/voltron_phi_append_writer_2frame_20260525_0000
VOLTRON_TEMPLATE=$MAGE/experiments/remix_sami3_live_phi_payload_writer_20260524
VOLTRON_RUN=$RUN/voltron_phi_writer
VOLTRON_EXE=$MAGE/build_gr_sami3_phi_append_20260525/bin/voltron.x
VOLTRON_XML=gtrd_20211204_0500_0510-waccmxfile-smoke.xml
WEIMER_GRID=$BASE/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/weimer_grid.dat
PHI_PAYLOAD=$VOLTRON_RUN/remix_sami3_phi_payload_append_writer_2frame.bin

mkdir -p "$RUN" "$VOLTRON_RUN"

echo "RUN_DIR=$RUN"
echo "VOLTRON_RUN=$VOLTRON_RUN"
echo "VOLTRON_EXE=$VOLTRON_EXE"
echo "PHI_PAYLOAD=$PHI_PAYLOAD"
echo "START=$(date)"
echo "HOST=$(hostname)"

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
export WACCMX_SAMI3_PHI_VALID_HOURS=0.0013888889
export WACCMX_SAMI3_PHI_MAX_FRAMES=2
export WACCMX_SAMI3_PHI_FINAL_VALID_UNTIL_HOUR=1.0e30

rsync -a \
  --exclude='slurm-*' \
  --exclude='*.out' \
  --exclude='remix_sami3_phi_payload*.bin' \
  --exclude='waccmx_voltron_forward_package.h5' \
  --exclude='waccmx_voltron_feedback_package.h5' \
  "$VOLTRON_TEMPLATE"/ "$VOLTRON_RUN"/
ln -sfn "$VOLTRON_EXE" "$VOLTRON_RUN/voltron.x"
rm -f "$PHI_PAYLOAD" "$VOLTRON_RUN"/waccmx_voltron_forward_package.h5 "$VOLTRON_RUN"/waccmx_voltron_feedback_package.h5

python3 - <<PY
from pathlib import Path
p = Path("$VOLTRON_RUN/$VOLTRON_XML")
s = p.read_text()
s = s.replace('<time tFin="6.0" />', '<time tFin="14.0" />')
s = s.replace('stopAfterExport="T"', 'stopAfterExport="F"')
p.write_text(s)
PY

(
  cd "$VOLTRON_RUN"
  echo "ldd_missing=$(ldd ./voltron.x | grep -c 'not found' || true)"
  ./voltron.x "$VOLTRON_XML"
) > "$VOLTRON_RUN/live_phi_payload_writer_voltron_append.out" 2>&1 &
voltron_pid=$!

phi_ready=0
for i in $(seq 1 180); do
  if [ -s "$PHI_PAYLOAD" ]; then
    nframes=$(python3 - <<PY
from pathlib import Path
import struct
p = Path("$PHI_PAYLOAD")
if p.exists() and p.stat().st_size >= 20:
    print(struct.unpack_from("<5i", p.read_bytes(), 0)[4])
else:
    print(0)
PY
)
    size1=$(stat -c '%s' "$PHI_PAYLOAD")
    sleep 1
    size2=$(stat -c '%s' "$PHI_PAYLOAD")
    if [ "$nframes" -ge 2 ] && [ "$size1" = "$size2" ] && [ "$size2" -gt 96000 ]; then
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
  echo "ERROR: Voltron did not produce a stable two-frame phi payload." >&2
  tail -180 "$VOLTRON_RUN/live_phi_payload_writer_voltron_append.out" >&2 || true
  wait "$voltron_pid" || true
  exit 40
fi

kill "$voltron_pid" 2>/dev/null || true
sleep 2
if kill -0 "$voltron_pid" 2>/dev/null; then
  kill -9 "$voltron_pid" 2>/dev/null || true
fi
wait "$voltron_pid" 2>/dev/null || true

module purge >/dev/null 2>&1 || true
module load intel/anaconda/2024.10
python - <<PY > "$RUN/phi_payload_summary.txt"
from pathlib import Path
import struct
import numpy as np
p = Path("$PHI_PAYLOAD")
raw = p.read_bytes()
magic, version, nlat, nlon, nframes = struct.unpack_from("<5i", raw, 0)
off = 20
phis = []
print(f"path={p}")
print(f"size={p.stat().st_size}")
print(f"header={[magic, version, nlat, nlon, nframes]}")
for iframe in range(nframes):
    frame_index = struct.unpack_from("<i", raw, off)[0]
    off += 4
    hour, valid_until = struct.unpack_from("<2f", raw, off)
    off += 8
    phi = np.frombuffer(raw, dtype="<f4", count=nlat*nlon, offset=off).copy()
    off += 4*nlat*nlon
    phis.append(phi)
    print(f"frame={iframe} frame_index={frame_index} hour={hour:.8g} valid_until={valid_until:.8g} min={float(phi.min()):.8g} max={float(phi.max()):.8g} finite={bool(np.isfinite(phi).all())} nonzero={int(np.count_nonzero(phi))}")
if len(phis) >= 2:
    diff = phis[1] - phis[0]
    print(f"frame1_minus_frame0_max_abs={float(np.max(np.abs(diff))):.8g}")
    print(f"frame1_minus_frame0_rms={float(np.sqrt(np.mean(diff*diff))):.8g}")
PY

cat "$RUN/phi_payload_summary.txt"
grep -E 'WACCMX_SAMI3_PHI_PAYLOAD wrote|ERROR|FATAL|Abort|forrtl' "$VOLTRON_RUN/live_phi_payload_writer_voltron_append.out" | tail -80 || true
echo "END=$(date)"
