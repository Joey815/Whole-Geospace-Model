#!/bin/bash -l
#SBATCH --job-name=wxsami3_dmpi
#SBATCH --partition=intel
#SBATCH --nodes=1
#SBATCH --ntasks=50
#SBATCH --cpus-per-task=1
#SBATCH --mem=296G
#SBATCH --time=00:40:00
#SBATCH --output=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525_0000/slurm-%j.out
#SBATCH --error=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525_0000/slurm-%j.err

set -eo pipefail

BASE=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official
COLLAB=/home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
MAGE=/home/jiaoy_group/jiaoy/data/MAGE1.25
SAMI_SRC=$BASE/runs/sami3_waccmx_neutral_esmf_msis_top_weimer_20231013_0000
RUN=${WXSAMI3_DIRECTMPI_RUN_DIR:-$BASE/runs/waccmx_cam_sami3_live_payload_f19_topblend_voltron_phi_directmpi_20260525_0000}
PAY_FALLBACK=$BASE/runs/waccmx_payload_esmf_msis_top_20231013_0000/waccmx_neutral_rank
MAP=$BASE/runs/esmf_regrid_f19_live_20260523/wxsami3_runtime_map_f19_20260523.bin
WEIGHTS=$BASE/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc
VOLTRON_TEMPLATE=$MAGE/experiments/remix_sami3_live_phi_payload_writer_20260524
VOLTRON_RUN=$RUN/voltron_runtime_direct_phi
VOLTRON_EXE=$MAGE/build_gr_sami3_phi_direct_openmpi_20260525/bin/voltron.x
VOLTRON_XML=gtrd_20211204_0500_0510-waccmxfile-smoke.xml
WEIMER_GRID=$BASE/runs/waccmx_cam_sami3_live_payload_f19_20260523_0000/weimer_grid.dat
PHI_PAYLOAD=$VOLTRON_RUN/remix_sami3_phi_payload_runtime_direct_openmpi.bin
NEUTRAL_PORT=$RUN/waccmx_sami3_online_port.txt
PHI_PORT=$RUN/sami3_direct_phi_port.txt
DVM_URI=$RUN/prte_dvm.uri
DVM_PID=$RUN/prte_dvm.pid
CESM_WRAPPER=$RUN/run_cesm_with_env_${SLURM_JOB_ID:-manual}.sh
LIVE_DUMP_DIR=$RUN/live_dump
LIVE_DUMP_PREFIX=$LIVE_DUMP_DIR/wxsami3_physstate_

CASE=/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523
CESM_EXE=/home/jiaoy_group/jiaoy/data/CESM/case_output_root_online_live_neutral_20260523/mage_qpx2000_f19_sami3_live_neutral_20260523/bld/cesm.exe
CESM_RUNDIR=/home/jiaoy_group/jiaoy/data/CESM/case_output_root_online_live_neutral_20260523/mage_qpx2000_f19_sami3_live_neutral_20260523/run
RUNCONFIG=$CESM_RUNDIR/nuopc.runconfig
RUNCONFIG_BAK=$RUN/nuopc.runconfig.before_voltron_phi_directmpi
CIME_HOME=/home/jiaoy_group/jiaoy/data/CESM/experiments/cime_home_v3
SPACK_GCC=/apps/support/intel_spr_rocky8.9/spack/0.22.0/opt/spack/linux-rocky8-icelake/gcc-8.5.0
WXSAMI3_LIB_COMPAT=$BASE/lib_compat
WXSAMI3_RUNTIME_LIBS=$WXSAMI3_LIB_COMPAT:$SPACK_GCC/netcdf-c-4.9.2-w7tqsh4u4adtiphnkuicfor43kjaczob/lib:$SPACK_GCC/netcdf-fortran-4.6.1-anfncsqfgewxtukoisalykmn2r6o5mgd/lib:$SPACK_GCC/parallelio-2.6.2-kqoksvmdxgeljz37sr4rrmzfkivfqklr/lib:$SPACK_GCC/openblas-0.3.26-zpdifrme2qnonxgzqyoad352gnatlbxk/lib

SAMI3_RANKS=33
CESM_RANKS=16
VOLTRON_RANKS=1
SAMI3_MAXSTEP=${WXSAMI3_DIRECTMPI_SAMI3_MAXSTEP:-20}
SAMI3_HRMAX=${WXSAMI3_DIRECTMPI_SAMI3_HRMAX:-.020000}
SAMI3_TPHI=${WXSAMI3_DIRECTMPI_SAMI3_TPHI:-1.}
SAMI3_DT0=${WXSAMI3_DIRECTMPI_SAMI3_DT0:-}
SAMI3_NEUTRAL_UPDATE_HOURS=${WXSAMI3_DIRECTMPI_SAMI3_NEUTRAL_UPDATE_HOURS:-0.25}
SAMI3_NEUTRAL_SPAN_HOURS=${WXSAMI3_DIRECTMPI_SAMI3_NEUTRAL_SPAN_HOURS:-$SAMI3_NEUTRAL_UPDATE_HOURS}
VOLTRON_TFIN=${WXSAMI3_DIRECTMPI_VOLTRON_TFIN:-10.25}
VOLTRON_DTCOUPLE=${WXSAMI3_DIRECTMPI_VOLTRON_DTCOUPLE:-5.0}
VOLTRON_TIMEOUT_SECONDS=${WXSAMI3_DIRECTMPI_VOLTRON_TIMEOUT_SECONDS:-1200}
ALLOW_VOLTRON_TIMEOUT_AFTER_DONE=${WXSAMI3_DIRECTMPI_ALLOW_VOLTRON_TIMEOUT_AFTER_DONE:-1}
REQUIRE_CACHE_AFTER_DONE=${WXSAMI3_DIRECTMPI_REQUIRE_CACHE_AFTER_DONE:-0}
PHI_MAX_FRAMES=${WXSAMI3_DIRECTMPI_PHI_MAX_FRAMES:-2}
PHI_FRAME_HOUR_BASE=${WXSAMI3_DIRECTMPI_PHI_FRAME_HOUR_BASE:-}
PHI_FRAME_HOUR_STEP=${WXSAMI3_DIRECTMPI_PHI_FRAME_HOUR_STEP:-}
PHI_FRAME_HOUR_OFFSET=${WXSAMI3_DIRECTMPI_PHI_FRAME_HOUR_OFFSET:-}
if [ -z "$PHI_FRAME_HOUR_OFFSET" ]; then
  if [ -n "$PHI_FRAME_HOUR_BASE" ] || [ -n "$PHI_FRAME_HOUR_STEP" ]; then
    PHI_FRAME_HOUR_OFFSET=0.0
  else
    PHI_FRAME_HOUR_OFFSET=0.0013888889
  fi
fi
PHI_VALID_HOURS=${WXSAMI3_DIRECTMPI_PHI_VALID_HOURS:-0.0013888889}
PHI_FINAL_VALID_UNTIL_HOUR=${WXSAMI3_DIRECTMPI_PHI_FINAL_VALID_UNTIL_HOUR:-1.0e30}
PHI_STOP_AFTER_DONE=${WXSAMI3_DIRECTMPI_PHI_STOP_AFTER_DONE:-0}
SAMI3_PHI_SKIP_AFTER_FINAL=${WXSAMI3_DIRECTMPI_SAMI3_PHI_SKIP_AFTER_FINAL:-0}
MAX_PACKETS=${WXSAMI3_DIRECTMPI_MAX_PACKETS:-1}
LIVE_DUMP_MAX=${WXSAMI3_DIRECTMPI_LIVE_DUMP_MAX:-$MAX_PACKETS}
SEND_EVERY_NSTEPS=${WXSAMI3_DIRECTMPI_SEND_EVERY_NSTEPS:-1}
CESM_STOP_N=${WXSAMI3_DIRECTMPI_STOP_N:-300}

mkdir -p "$RUN" "$LIVE_DUMP_DIR" "$VOLTRON_RUN"

cleanup() {
  if [ -n "${voltron_pid:-}" ]; then kill "$voltron_pid" 2>/dev/null || true; fi
  if [ -n "${cesm_pid:-}" ]; then kill "$cesm_pid" 2>/dev/null || true; fi
  if [ -n "${sami3_pid:-}" ]; then kill "$sami3_pid" 2>/dev/null || true; fi
  if [ -s "${DVM_URI:-}" ]; then pterm --dvm-uri "file:$DVM_URI" >/dev/null 2>&1 || true; fi
  if [ -f "$RUNCONFIG_BAK" ]; then cp "$RUNCONFIG_BAK" "$RUNCONFIG"; fi
}
trap cleanup EXIT

echo "RUN_DIR=$RUN"
echo "VOLTRON_RUN=$VOLTRON_RUN"
echo "VOLTRON_EXE=$VOLTRON_EXE"
echo "PHI_PAYLOAD=$PHI_PAYLOAD"
echo "NEUTRAL_PORT=$NEUTRAL_PORT"
echo "PHI_PORT=$PHI_PORT"
echo "CASE=$CASE"
echo "CESM_EXE=$CESM_EXE"
echo "CESM_RUNDIR=$CESM_RUNDIR"
echo "START=$(date)"
echo "HOST=$(hostname)"
echo "DIRECT_PHI_MODE=1"
echo "SAMI3_MAXSTEP=$SAMI3_MAXSTEP"
echo "SAMI3_HRMAX=$SAMI3_HRMAX"
echo "SAMI3_TPHI=$SAMI3_TPHI"
echo "SAMI3_DT0=${SAMI3_DT0:-<namelist-default>}"
echo "SAMI3_NEUTRAL_UPDATE_HOURS=$SAMI3_NEUTRAL_UPDATE_HOURS"
echo "SAMI3_NEUTRAL_SPAN_HOURS=$SAMI3_NEUTRAL_SPAN_HOURS"
echo "VOLTRON_TFIN=$VOLTRON_TFIN"
echo "VOLTRON_DTCOUPLE=$VOLTRON_DTCOUPLE"
echo "VOLTRON_TIMEOUT_SECONDS=$VOLTRON_TIMEOUT_SECONDS"
echo "ALLOW_VOLTRON_TIMEOUT_AFTER_DONE=$ALLOW_VOLTRON_TIMEOUT_AFTER_DONE"
echo "REQUIRE_CACHE_AFTER_DONE=$REQUIRE_CACHE_AFTER_DONE"
echo "PHI_MAX_FRAMES=$PHI_MAX_FRAMES"
echo "PHI_FRAME_HOUR_BASE=${PHI_FRAME_HOUR_BASE:-<runtime>}"
echo "PHI_FRAME_HOUR_STEP=${PHI_FRAME_HOUR_STEP:-<runtime>}"
echo "PHI_FRAME_HOUR_OFFSET=$PHI_FRAME_HOUR_OFFSET"
echo "PHI_VALID_HOURS=$PHI_VALID_HOURS"
echo "PHI_FINAL_VALID_UNTIL_HOUR=$PHI_FINAL_VALID_UNTIL_HOUR"
echo "PHI_STOP_AFTER_DONE=$PHI_STOP_AFTER_DONE"
echo "CESM_STOP_N=$CESM_STOP_N"

source /etc/profile.d/modules.sh >/dev/null 2>&1 || true
module purge >/dev/null 2>&1 || true
source "$CASE/.env_mach_specific.sh"

export PATH=$CIME_HOME/bin:/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/python311_first:$PATH
export LD_LIBRARY_PATH=$WXSAMI3_RUNTIME_LIBS:${LD_LIBRARY_PATH:-}
export HOME=$CIME_HOME
export CIME_MODEL=cesm
export OMP_NUM_THREADS=1
export OMPI_MCA_mpi_yield_when_idle=1
export WXSAMI3_PORT_FILE="$NEUTRAL_PORT"
export WXSAMI3_PAYLOAD_MODE=live
export WXSAMI3_PAYLOAD_PREFIX="$PAY_FALLBACK"
export WXSAMI3_LIVE_MAP_FILE="$MAP"
export WXSAMI3_NUMWORKERS=32
export WXSAMI3_SKIP_DISCONNECT=0
export WXSAMI3_LIVE_DIAG=1
export WXSAMI3_META_FILE="$RUN/wxsami3_live_meta.json"
export WXSAMI3_LIVE_DUMP_PREFIX="$LIVE_DUMP_PREFIX"
export WXSAMI3_LIVE_DUMP_MAX="$LIVE_DUMP_MAX"
export WXSAMI3_MAX_PACKETS="$MAX_PACKETS"
export WXSAMI3_SEND_EVERY_NSTEPS="$SEND_EVERY_NSTEPS"
export WXSAMI3_N2_NEGATIVE_MODE=invalid
export WXSAMI3_RECV_QC=1
export WXSAMI3_NEUTRAL_UPDATE_HOURS="$SAMI3_NEUTRAL_UPDATE_HOURS"
export WXSAMI3_NEUTRAL_SPAN_HOURS="$SAMI3_NEUTRAL_SPAN_HOURS"
export SAMI3_USE_ONLINE_PHI_WEIMER=1
export SAMI3_PHI_DIRECT_PORT_FILE="$PHI_PORT"
export SAMI3_PHI_SKIP_MADALA_AFTER_FINAL="$SAMI3_PHI_SKIP_AFTER_FINAL"
export WXSAMI3_TOP_BLEND_MODE=linear
export WXSAMI3_BLEND_BOTTOM_KM=600
export WXSAMI3_BLEND_TOP_KM=720
unset WXSAMI3_PHI_PAYLOAD_FILE
unset WXSAMI3_PHI_PAYLOAD_WAIT_SECONDS
unset WXSAMI3_PHI_PAYLOAD_STABLE_SECONDS

echo "PAYLOAD_MODE=$WXSAMI3_PAYLOAD_MODE"
echo "LIVE_DUMP_MAX=$WXSAMI3_LIVE_DUMP_MAX"
echo "MAX_PACKETS=$WXSAMI3_MAX_PACKETS"
echo "SEND_EVERY_NSTEPS=$WXSAMI3_SEND_EVERY_NSTEPS"
echo "PHI_DIRECT_PORT=$SAMI3_PHI_DIRECT_PORT_FILE"
echo "PHI_PAYLOAD_FILE_FOR_VOLTRON_ONLY=$PHI_PAYLOAD"
echo "N2_NEGATIVE_MODE=$WXSAMI3_N2_NEGATIVE_MODE"
echo "NEUTRAL_UPDATE_HOURS=$WXSAMI3_NEUTRAL_UPDATE_HOURS"
echo "NEUTRAL_SPAN_HOURS=$WXSAMI3_NEUTRAL_SPAN_HOURS"
echo "TOP_BLEND_MODE=$WXSAMI3_TOP_BLEND_MODE"
echo "BLEND_BOTTOM_KM=$WXSAMI3_BLEND_BOTTOM_KM"
echo "BLEND_TOP_KM=$WXSAMI3_BLEND_TOP_KM"
echo "SAMI3_USE_ONLINE_PHI_WEIMER=$SAMI3_USE_ONLINE_PHI_WEIMER"
echo "SAMI3_PHI_SKIP_MADALA_AFTER_FINAL=$SAMI3_PHI_SKIP_MADALA_AFTER_FINAL"
echo "PRTE=$(command -v prte)"
echo "PRUN=$(command -v prun)"
echo "ldd_missing_voltron=$(ldd "$VOLTRON_EXE" | grep -c 'not found' || true)"

if [ ! -f "$RUN/.prepared_sami3" ]; then
  rsync -a \
    --exclude='slurm-*' \
    --exclude='*.out' \
    "$SAMI_SRC"/ "$RUN"/
  touch "$RUN/.prepared_sami3"
fi

cp "$BASE/work/sami3-3.22_online_mpi_openmpi_remix_phi_20260524/sami3.x" "$RUN/sami3.x"
cp "$BASE/work/sami3-3.22_online_mpi_openmpi_remix_phi_20260524/waccmx_neutral_mod.f90" "$RUN/waccmx_neutral_mod.f90"
cp "$BASE/work/sami3-3.22_online_mpi_openmpi_remix_phi_20260524/namelist_mod.f90" "$RUN/namelist_mod.f90"
cp "$BASE/work/sami3-3.22_online_mpi_openmpi_remix_phi_20260524/potential.f90" "$RUN/potential.f90"
cp "$BASE/work/sami3-3.22_online_mpi_openmpi_remix_phi_20260524/sami3-3.22.f90" "$RUN/sami3-3.22.f90"

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
s = s.replace('<time tFin="6.0" />', '<time tFin="$VOLTRON_TFIN" />')
s = s.replace('dtCouple="5.0"', 'dtCouple="$VOLTRON_DTCOUPLE"')
s = s.replace('stopAfterExport="T"', 'stopAfterExport="F"')
p.write_text(s)
PY

cd "$RUN"
python3 - <<PY
from pathlib import Path
import re
p = Path('sami3-3.22.namelist')
s = p.read_text()
s = re.sub(r'^\\s*maxstep\\s*=.*?,', '  maxstep  =   $SAMI3_MAXSTEP,', s, flags=re.MULTILINE)
s = re.sub(r'^\\s*hrmax\\s*=.*?,', '  hrmax = $SAMI3_HRMAX,', s, flags=re.MULTILINE)
s = re.sub(r'^\\s*tphi\\s*=.*?,', '  tphi       = $SAMI3_TPHI,', s, flags=re.MULTILINE)
dt0 = "$SAMI3_DT0"
if dt0:
    s = re.sub(r'^\\s*dt0\\s*=.*?,', f'  dt0      =   {dt0},', s, flags=re.MULTILINE)
s = s.replace('  lwaccmx_neutral = .false.,', '  lwaccmx_neutral = .true.,')
if 'lwaccmx_neutral_online' not in s:
    marker = "  waccmx_neutral_prefix = '/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_payload_esmf_msis_top_20231013_0000/waccmx_neutral_rank',"
    repl = marker + "\\n  lwaccmx_neutral_online = .true.,\\n  waccmx_online_port_file = '$NEUTRAL_PORT',"
    s = s.replace(marker, repl)
else:
    s = s.replace('  lwaccmx_neutral_online = .false.,', '  lwaccmx_neutral_online = .true.,')
    s = re.sub(r"\\s*waccmx_online_port_file\\s*=\\s*'.*?',",
               "  waccmx_online_port_file = '$NEUTRAL_PORT',", s)
p.write_text(s)
PY

cp "$RUNCONFIG" "$RUNCONFIG_BAK"
python3 - <<PY
from pathlib import Path
import re
p = Path('$RUNCONFIG')
s = p.read_text()
s = re.sub(r'(\\s*stop_n\\s*=\\s*)\\d+', r'\\g<1>$CESM_STOP_N', s)
p.write_text(s)
PY

cat > "$CESM_WRAPPER" <<EOF
#!/bin/bash
source "$CASE/.env_mach_specific.sh"
export PATH="$PATH"
export LD_LIBRARY_PATH="$WXSAMI3_RUNTIME_LIBS:\${LD_LIBRARY_PATH:-}"
export HOME="$CIME_HOME"
export CIME_MODEL=cesm
export OMP_NUM_THREADS=1
export OMPI_MCA_mpi_yield_when_idle=1
export WXSAMI3_PORT_FILE="$NEUTRAL_PORT"
export WXSAMI3_PAYLOAD_MODE=live
export WXSAMI3_PAYLOAD_PREFIX="$PAY_FALLBACK"
export WXSAMI3_LIVE_MAP_FILE="$MAP"
export WXSAMI3_NUMWORKERS=32
export WXSAMI3_SKIP_DISCONNECT=0
export WXSAMI3_LIVE_DIAG=1
export WXSAMI3_META_FILE="$RUN/wxsami3_live_meta.json"
export WXSAMI3_LIVE_DUMP_PREFIX="$LIVE_DUMP_PREFIX"
export WXSAMI3_LIVE_DUMP_MAX="$LIVE_DUMP_MAX"
export WXSAMI3_MAX_PACKETS="$MAX_PACKETS"
export WXSAMI3_SEND_EVERY_NSTEPS="$SEND_EVERY_NSTEPS"
export WXSAMI3_N2_NEGATIVE_MODE=invalid
export WXSAMI3_TOP_BLEND_MODE="$WXSAMI3_TOP_BLEND_MODE"
export WXSAMI3_BLEND_BOTTOM_KM="$WXSAMI3_BLEND_BOTTOM_KM"
export WXSAMI3_BLEND_TOP_KM="$WXSAMI3_BLEND_TOP_KM"
unset WXSAMI3_PHI_PAYLOAD_FILE
unset WXSAMI3_PHI_PAYLOAD_WAIT_SECONDS
unset WXSAMI3_PHI_PAYLOAD_STABLE_SECONDS
cd "$CESM_RUNDIR"
exec "$CESM_EXE"
EOF
chmod +x "$CESM_WRAPPER"

rm -f "$NEUTRAL_PORT" "$PHI_PORT" "$DVM_URI" "$DVM_PID" \
  sami3_online_receiver.out waccmx_cesm.out voltron_runtime_direct.out \
  phi_payload_summary.txt validate_remix_sami3_phi_payload.* \
  validate_sami3_direct_phi_run_strict.* validate_wxsami3_time_axis.* \
  validate_wxsami3_live_packet_contract.* validate_wxsami3_source_flag_balance.* \
  validate_wxsami3_topblend_policy.* validate_wxsami3_runtime_map.*
rm -f "$RUN"/live_dump_summary_pkt*.txt "$RUN"/replay_builder_pkt*.out "$RUN"/recv_qc_compare_pkt*.txt
rm -rf "$RUN"/replay_pkt*
rm -f "$LIVE_DUMP_DIR"/wxsami3_physstate_* "$RUN/wxsami3_live_meta.json"
rm -f "$CESM_RUNDIR"/cesm.log.* "$CESM_RUNDIR"/atm.log.* "$CESM_RUNDIR"/cpl.log.* 2>/dev/null || true

prte --daemonize --report-uri "$DVM_URI" --report-pid "$DVM_PID" --host "$(hostname)" \
  -x "PATH=$PATH" -x "LD_LIBRARY_PATH=$LD_LIBRARY_PATH" \
  -x "OMPI_MCA_mpi_yield_when_idle=$OMPI_MCA_mpi_yield_when_idle"
for i in $(seq 1 60); do
  [ -s "$DVM_URI" ] && break
  sleep 1
done
if [ ! -s "$DVM_URI" ]; then
  echo "ERROR: PRRTE DVM did not create URI file: $DVM_URI" >&2
  exit 30
fi

timeout 2400s prun --dvm-uri "file:$DVM_URI" \
  -x "PATH=$PATH" -x "LD_LIBRARY_PATH=$LD_LIBRARY_PATH" \
  -x "OMPI_MCA_mpi_yield_when_idle=$OMPI_MCA_mpi_yield_when_idle" \
  -x "WXSAMI3_RECV_QC=$WXSAMI3_RECV_QC" \
  -x "WXSAMI3_NEUTRAL_UPDATE_HOURS=$WXSAMI3_NEUTRAL_UPDATE_HOURS" \
  -x "WXSAMI3_NEUTRAL_SPAN_HOURS=$WXSAMI3_NEUTRAL_SPAN_HOURS" \
  -x "SAMI3_USE_ONLINE_PHI_WEIMER=$SAMI3_USE_ONLINE_PHI_WEIMER" \
  -x "SAMI3_PHI_DIRECT_PORT_FILE=$PHI_PORT" \
  -x "SAMI3_PHI_SKIP_MADALA_AFTER_FINAL=$SAMI3_PHI_SKIP_MADALA_AFTER_FINAL" \
  -x "WXSAMI3_TOP_BLEND_MODE=$WXSAMI3_TOP_BLEND_MODE" \
  -x "WXSAMI3_BLEND_BOTTOM_KM=$WXSAMI3_BLEND_BOTTOM_KM" \
  -x "WXSAMI3_BLEND_TOP_KM=$WXSAMI3_BLEND_TOP_KM" \
  -n "$SAMI3_RANKS" ./sami3.x > "$RUN/sami3_online_receiver.out" 2>&1 &
sami3_pid=$!

for i in $(seq 1 180); do
  [ -s "$NEUTRAL_PORT" ] && break
  sleep 1
done
if [ ! -s "$NEUTRAL_PORT" ]; then
  echo "ERROR: SAMI3 did not create neutral port file: $NEUTRAL_PORT" >&2
  exit 20
fi

cd "$CESM_RUNDIR"
timeout 2400s prun --dvm-uri "file:$DVM_URI" \
  -x "OMPI_MCA_mpi_yield_when_idle=$OMPI_MCA_mpi_yield_when_idle" \
  -n "$CESM_RANKS" "$CESM_WRAPPER" > "$RUN/waccmx_cesm.out" 2>&1 &
cesm_pid=$!

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
  export WACCMX_SAMI3_PHI_FRAME_HOUR_BASE="$PHI_FRAME_HOUR_BASE"
  export WACCMX_SAMI3_PHI_FRAME_HOUR_STEP="$PHI_FRAME_HOUR_STEP"
  export WACCMX_SAMI3_PHI_FRAME_HOUR_OFFSET="$PHI_FRAME_HOUR_OFFSET"
  export WACCMX_SAMI3_PHI_VALID_HOURS="$PHI_VALID_HOURS"
  export WACCMX_SAMI3_PHI_MAX_FRAMES="$PHI_MAX_FRAMES"
  export WACCMX_SAMI3_PHI_FINAL_VALID_UNTIL_HOUR="$PHI_FINAL_VALID_UNTIL_HOUR"
  export WACCMX_SAMI3_PHI_STOP_AFTER_DONE="$PHI_STOP_AFTER_DONE"
  export OMP_NUM_THREADS=8
  echo "voltron_exe=$VOLTRON_EXE"
  echo "weimer_grid=$WEIMER_GRID"
  echo "phi_payload=$PHI_PAYLOAD"
  echo "direct_phi_port=$PHI_PORT"
  echo "phi_max_frames=$WACCMX_SAMI3_PHI_MAX_FRAMES"
  echo "phi_frame_hour_base=${WACCMX_SAMI3_PHI_FRAME_HOUR_BASE:-<runtime>}"
  echo "phi_frame_hour_step=${WACCMX_SAMI3_PHI_FRAME_HOUR_STEP:-<runtime>}"
  echo "ldd_missing=$(ldd ./voltron.x | grep -c 'not found' || true)"
  timeout "${VOLTRON_TIMEOUT_SECONDS}s" prun --dvm-uri "file:$DVM_URI" \
    -x "WACCMX_SAMI3_PHI_PAYLOAD_FILE=$WACCMX_SAMI3_PHI_PAYLOAD_FILE" \
    -x "WACCMX_SAMI3_PHI_DIRECT_PORT_FILE=$WACCMX_SAMI3_PHI_DIRECT_PORT_FILE" \
    -x "WACCMX_SAMI3_WEIMER_GRID=$WACCMX_SAMI3_WEIMER_GRID" \
    -x "WACCMX_SAMI3_PHI_HEMI=$WACCMX_SAMI3_PHI_HEMI" \
    -x "WACCMX_SAMI3_PHI_FRAME_HOUR_BASE=$WACCMX_SAMI3_PHI_FRAME_HOUR_BASE" \
    -x "WACCMX_SAMI3_PHI_FRAME_HOUR_STEP=$WACCMX_SAMI3_PHI_FRAME_HOUR_STEP" \
    -x "WACCMX_SAMI3_PHI_FRAME_HOUR_OFFSET=$WACCMX_SAMI3_PHI_FRAME_HOUR_OFFSET" \
    -x "WACCMX_SAMI3_PHI_VALID_HOURS=$WACCMX_SAMI3_PHI_VALID_HOURS" \
    -x "WACCMX_SAMI3_PHI_MAX_FRAMES=$WACCMX_SAMI3_PHI_MAX_FRAMES" \
    -x "WACCMX_SAMI3_PHI_FINAL_VALID_UNTIL_HOUR=$WACCMX_SAMI3_PHI_FINAL_VALID_UNTIL_HOUR" \
    -x "WACCMX_SAMI3_PHI_STOP_AFTER_DONE=$WACCMX_SAMI3_PHI_STOP_AFTER_DONE" \
    -x "OMP_NUM_THREADS=$OMP_NUM_THREADS" \
    -n "$VOLTRON_RANKS" ./voltron.x "$VOLTRON_XML"
) > "$RUN/voltron_runtime_direct.out" 2>&1 &
voltron_pid=$!

wait "$cesm_pid"
cesm_pid=
wait "$sami3_pid"
sami3_pid=
voltron_status=0
wait "$voltron_pid" || voltron_status=$?
voltron_pid=
if [ "$voltron_status" -ne 0 ]; then
  if [ "$ALLOW_VOLTRON_TIMEOUT_AFTER_DONE" != "0" ] && \
     grep -q 'WACCMX_SAMI3_PHI_DIRECT sent done=' "$RUN/voltron_runtime_direct.out" && \
     grep -q 'MASTER: All Done!' "$RUN/sami3_online_receiver.out"; then
    echo "INFO: accepting Voltron nonzero exit after direct phi done and SAMI3 completion: status=$voltron_status"
  else
    echo "ERROR: Voltron exited nonzero before validated direct phi/SAMI3 completion: status=$voltron_status" >&2
    exit "$voltron_status"
  fi
fi
pterm --dvm-uri "file:$DVM_URI" || true

{
  echo "--- CESM component markers appended for validators"
  grep -h -E 'WXSAMI3|END OF MODEL RUN|FATAL|forrtl|Abort|header mismatch' \
    "$CESM_RUNDIR"/atm.log.* "$CESM_RUNDIR"/cpl.log.* "$CESM_RUNDIR"/cesm.log.* \
    2>/dev/null || true
} >> "$RUN/waccmx_cesm.out"

python3 - <<PY > "$RUN/phi_payload_summary.txt"
from pathlib import Path
import math
import struct

p = Path("$PHI_PAYLOAD")
raw = p.read_bytes()
magic, version, nlat, nlon, nframes = struct.unpack_from("<5i", raw, 0)
off = 20
prev = None
print(f"path={p}")
print(f"size={p.stat().st_size}")
print(f"header={[magic, version, nlat, nlon, nframes]}")
for iframe in range(nframes):
    frame_index = struct.unpack_from("<i", raw, off)[0]
    off += 4
    hour, valid_until = struct.unpack_from("<2f", raw, off)
    off += 8
    nphi = nlat*nlon
    phi = struct.unpack_from("<" + "f"*nphi, raw, off)
    off += 4*nphi
    finite = all(math.isfinite(x) for x in phi)
    nonzero = sum(1 for x in phi if x != 0.0)
    print(f"frame={iframe} frame_index={frame_index} hour={hour:.8g} valid_until={valid_until:.8g} min={min(phi):.8g} max={max(phi):.8g} finite={finite} nonzero={nonzero}")
    if prev is not None:
        diff = [a-b for a, b in zip(phi, prev)]
        rms = math.sqrt(sum(x*x for x in diff)/len(diff))
        print(f"frame{iframe}_minus_frame{iframe-1}_max_abs={max(abs(x) for x in diff):.8g}")
        print(f"frame{iframe}_minus_frame{iframe-1}_rms={rms:.8g}")
    prev = phi
PY
cat "$RUN/phi_payload_summary.txt"

for pkt_idx in $(seq 0 $((MAX_PACKETS - 1))); do
  pkt=$(printf "%06d" "$pkt_idx")
  pattern="$LIVE_DUMP_DIR/wxsami3_physstate_rank*_pkt${pkt}.bin"
  replay_dir="$RUN/replay_pkt${pkt}"
  replay_prefix="$replay_dir/waccmx_neutral_rank"
  mkdir -p "$replay_dir"
  if compgen -G "$pattern" > /dev/null; then
    /usr/bin/python3 "$BASE/scripts/read_wxsami3_live_dump.py" "$pattern" \
      > "$RUN/live_dump_summary_pkt${pkt}.txt"
    "$BASE/bin/make_wxsami3_payload_from_live_dump" \
      "$pattern" \
      "$RUN" \
      "$WEIGHTS" \
      "$replay_prefix" \
      > "$RUN/replay_builder_pkt${pkt}.out" 2>&1
    /usr/bin/python3 "$BASE/scripts/compare_wxsami3_recv_qc.py" \
      --payload-prefix "$replay_prefix" \
      --receiver-log "$RUN/sami3_online_receiver.out" \
      --packet-occurrence "$pkt_idx" \
      > "$RUN/recv_qc_compare_pkt${pkt}.txt"
  fi
done

/usr/bin/python3 "$COLLAB/scripts/validate_remix_sami3_phi_payload.py" \
  --payload "$PHI_PAYLOAD" \
  --expected-frames "$PHI_MAX_FRAMES" \
  --require-changing-phi-frames \
  --json-output "$RUN/validate_remix_sami3_phi_payload.json" \
  > "$RUN/validate_remix_sami3_phi_payload.txt"

/usr/bin/python3 "$COLLAB/scripts/validate_sami3_direct_phi_run.py" \
  --receiver-log "$RUN/sami3_online_receiver.out" \
  --phi-sender-log "$RUN/voltron_runtime_direct.out" \
  --recv-qc-compare "$RUN/recv_qc_compare_pkt000000.txt" \
  --expected-frames "$PHI_MAX_FRAMES" \
  --require-changing-phi \
  $( [ "$REQUIRE_CACHE_AFTER_DONE" != "0" ] && printf '%s' '--require-cache-after-done' ) \
  --json-output "$RUN/validate_sami3_direct_phi_run_strict.json" \
  > "$RUN/validate_sami3_direct_phi_run_strict.txt"

/usr/bin/python3 "$COLLAB/scripts/validate_wxsami3_live_packet_contract.py" \
  --run-dir "$RUN" \
  --expected-packets "$MAX_PACKETS" \
  --expected-source-columns 13824 \
  --expected-receiver-ranks 32 \
  --expected-payload-nz 304 \
  --expected-payload-nf 124 \
  --expected-payload-nl 5 \
  --expected-payload-nneut 7 \
  --expected-n2-mode invalid \
  --expect-n2-residual \
  --expect-he-native \
  --require-zero-unknown-source-flags \
  --json-output "$RUN/validate_wxsami3_live_packet_contract.json" \
  > "$RUN/validate_wxsami3_live_packet_contract.txt"

/usr/bin/python3 "$COLLAB/scripts/validate_wxsami3_source_flag_balance.py" \
  --run-dir "$RUN" \
  --expected-sami3-workers 32 \
  --expected-nl 5 \
  --min-total-blend-cells 1 \
  --json-output "$RUN/validate_wxsami3_source_flag_balance.json" \
  > "$RUN/validate_wxsami3_source_flag_balance.txt"

/usr/bin/python3 "$COLLAB/scripts/validate_wxsami3_time_axis.py" \
  --run-dir "$RUN" \
  --phi-payload "$PHI_PAYLOAD" \
  --expected-neutral-packets "$MAX_PACKETS" \
  --expected-phi-frames "$PHI_MAX_FRAMES" \
  --expected-sami3-workers 32 \
  --allow-overlap-phi-validity \
  --json-output "$RUN/validate_wxsami3_time_axis.json" \
  > "$RUN/validate_wxsami3_time_axis.txt"

/usr/bin/python3 "$COLLAB/scripts/validate_wxsami3_topblend_policy.py" \
  --run-dir "$RUN" \
  --expect-top-blend-mode linear \
  --expect-bottom-km 600 \
  --expect-top-km 720 \
  --min-total-blend-cells 1 \
  --require-zero-unknown-source-flags \
  --require-he-native \
  --require-w-zero \
  --json-output "$RUN/validate_wxsami3_topblend_policy.json" \
  > "$RUN/validate_wxsami3_topblend_policy.txt"

/home/jiaoy_group/jiaoy/.venvs/mage-vis/bin/python "$COLLAB/scripts/validate_wxsami3_runtime_map.py" \
  --runtime-map "$MAP" \
  --weights-nc "$WEIGHTS" \
  --expected-nsource 13824 \
  --json-output "$RUN/validate_wxsami3_runtime_map.json" \
  > "$RUN/validate_wxsami3_runtime_map.txt"

echo "--- Direct phi validator"
cat "$RUN/validate_sami3_direct_phi_run_strict.txt"
echo "--- Phi payload validator"
cat "$RUN/validate_remix_sami3_phi_payload.txt"
echo "--- Live packet validator"
cat "$RUN/validate_wxsami3_live_packet_contract.txt"
echo "--- Source flag validator"
cat "$RUN/validate_wxsami3_source_flag_balance.txt"
echo "--- Time axis validator"
cat "$RUN/validate_wxsami3_time_axis.txt"
echo "--- Topblend validator"
cat "$RUN/validate_wxsami3_topblend_policy.txt"
echo "--- Runtime map validator"
cat "$RUN/validate_wxsami3_runtime_map.txt"
echo "--- WACCM-X sender markers"
grep -E 'WXSAMI3|ERROR|FATAL|END OF MODEL RUN' "$RUN/waccmx_cesm.out" "$CESM_RUNDIR"/*.log.* 2>/dev/null | tail -420 || true
echo "--- Voltron direct phi markers"
grep -E 'WACCMX_SAMI3_PHI|ERROR|FATAL|forrtl|NaN|Abort' "$RUN/voltron_runtime_direct.out" | tail -240 || true
echo "--- SAMI3 receiver markers"
grep -E 'SAMI3 direct phi|SAMI3_USE_ONLINE_PHI_WEIMER|WACCMX_PHI_RECV|SAMI3_PHI_SKIP|hrutw2|nweimer|WACCMX online|WACCMX_RECV_QC|WACCMX_RECV_SOURCE_FLAGS|WACCMX_APPLY_QC|WACCMX_APPLY_SOURCE_FLAGS|WACCMX_APPLY_BLEND|WACCMX neutral apply policy|WACCMX neutral top blend policy|MASTER: All Done|WACCMX online done|fatal|forrtl|NaN|Abort|header mismatch' "$RUN/sami3_online_receiver.out" | tail -420 || true
echo "--- Packet summaries and compares"
for pkt in 000000 000001; do
  echo "### pkt${pkt} summary"
  cat "$RUN/live_dump_summary_pkt${pkt}.txt" 2>/dev/null || true
  echo "### pkt${pkt} replay builder"
  cat "$RUN/replay_builder_pkt${pkt}.out" 2>/dev/null || true
  echo "### pkt${pkt} receiver QC compare"
  cat "$RUN/recv_qc_compare_pkt${pkt}.txt" 2>/dev/null || true
done
echo "END=$(date)"
