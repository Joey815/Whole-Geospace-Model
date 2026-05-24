#!/bin/bash -l
#SBATCH --job-name=wxsami3_phiappend
#SBATCH --partition=intel
#SBATCH --nodes=1
#SBATCH --ntasks=49
#SBATCH --cpus-per-task=1
#SBATCH --mem=296G
#SBATCH --time=00:45:00
#SBATCH --output=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_phi_append_20260525_0000/slurm-%j.out
#SBATCH --error=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_cam_sami3_live_payload_f19_topblend_phi_append_20260525_0000/slurm-%j.err

set -eo pipefail

BASE=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official
COLLAB=/home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
SAMI_SRC=$BASE/runs/sami3_waccmx_neutral_esmf_msis_top_weimer_20231013_0000
RUN=$BASE/runs/waccmx_cam_sami3_live_payload_f19_topblend_phi_append_20260525_0000
PAY_FALLBACK=$BASE/runs/waccmx_payload_esmf_msis_top_20231013_0000/waccmx_neutral_rank
MAP=$BASE/runs/esmf_regrid_f19_live_20260523/wxsami3_runtime_map_f19_20260523.bin
WEIGHTS=$BASE/runs/esmf_regrid_f19_live_20260523/weights_bilinear_f19_live.nc
PHI_PAYLOAD=$COLLAB/logs/remix_sami3_phi_weimer_voltron_bridge_runtime_20260524/remix_sami3_phi_payload_from_voltron_bridge_7656022.bin
PORT=$RUN/waccmx_sami3_online_port.txt
DVM_URI=$RUN/prte_dvm.uri
DVM_PID=$RUN/prte_dvm.pid
CESM_WRAPPER=$RUN/run_cesm_with_env_${SLURM_JOB_ID:-manual}.sh
LIVE_DUMP_DIR=$RUN/live_dump
LIVE_DUMP_PREFIX=$LIVE_DUMP_DIR/wxsami3_physstate_

CASE=/home/jiaoy_group/jiaoy/data/CESM/cases/mage_qpx2000_f19_sami3_live_neutral_20260523
CESM_EXE=/home/jiaoy_group/jiaoy/data/CESM/case_output_root_online_live_neutral_20260523/mage_qpx2000_f19_sami3_live_neutral_20260523/bld/cesm.exe
CESM_RUNDIR=/home/jiaoy_group/jiaoy/data/CESM/case_output_root_online_live_neutral_20260523/mage_qpx2000_f19_sami3_live_neutral_20260523/run
RUNCONFIG=$CESM_RUNDIR/nuopc.runconfig
RUNCONFIG_BAK=$RUN/nuopc.runconfig.before_multipacket_topblend
CIME_HOME=/home/jiaoy_group/jiaoy/data/CESM/experiments/cime_home_v3
SPACK_GCC=/apps/support/intel_spr_rocky8.9/spack/0.22.0/opt/spack/linux-rocky8-icelake/gcc-8.5.0
WXSAMI3_LIB_COMPAT=$BASE/lib_compat
WXSAMI3_RUNTIME_LIBS=$WXSAMI3_LIB_COMPAT:$SPACK_GCC/netcdf-c-4.9.2-w7tqsh4u4adtiphnkuicfor43kjaczob/lib:$SPACK_GCC/netcdf-fortran-4.6.1-anfncsqfgewxtukoisalykmn2r6o5mgd/lib:$SPACK_GCC/parallelio-2.6.2-kqoksvmdxgeljz37sr4rrmzfkivfqklr/lib:$SPACK_GCC/openblas-0.3.26-zpdifrme2qnonxgzqyoad352gnatlbxk/lib

mkdir -p "$RUN" "$LIVE_DUMP_DIR"

restore_runconfig() {
  if [ -f "$RUNCONFIG_BAK" ]; then
    cp "$RUNCONFIG_BAK" "$RUNCONFIG"
  fi
}
trap restore_runconfig EXIT

source "$CASE/.env_mach_specific.sh"
export PATH=$CIME_HOME/bin:/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/bin/python311_first:$PATH
export LD_LIBRARY_PATH=$WXSAMI3_RUNTIME_LIBS:$LD_LIBRARY_PATH
export HOME=$CIME_HOME
export CIME_MODEL=cesm
export OMP_NUM_THREADS=1
export OMPI_MCA_mpi_yield_when_idle=1
export WXSAMI3_PORT_FILE="$PORT"
export WXSAMI3_PAYLOAD_MODE=live
export WXSAMI3_PAYLOAD_PREFIX="$PAY_FALLBACK"
export WXSAMI3_LIVE_MAP_FILE="$MAP"
export WXSAMI3_NUMWORKERS=32
export WXSAMI3_SKIP_DISCONNECT=0
export WXSAMI3_LIVE_DIAG=1
export WXSAMI3_META_FILE="$RUN/wxsami3_live_meta.json"
export WXSAMI3_LIVE_DUMP_PREFIX="$LIVE_DUMP_PREFIX"
export WXSAMI3_LIVE_DUMP_MAX=1
export WXSAMI3_MAX_PACKETS=1
export WXSAMI3_SEND_EVERY_NSTEPS=1
export WXSAMI3_N2_NEGATIVE_MODE=invalid
export WXSAMI3_PHI_PAYLOAD_FILE="$PHI_PAYLOAD"
export WXSAMI3_RECV_QC=1
export SAMI3_USE_ONLINE_PHI_WEIMER=1
export WXSAMI3_TOP_BLEND_MODE=linear
export WXSAMI3_BLEND_BOTTOM_KM=600
export WXSAMI3_BLEND_TOP_KM=720
SAMI3_RANKS=33
CESM_RANKS=16

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
if 'lwaccmx_neutral_online' not in s:
    marker = "  waccmx_neutral_prefix = '/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/waccmx_payload_esmf_msis_top_20231013_0000/waccmx_neutral_rank',"
    repl = marker + "\n  lwaccmx_neutral_online = .true.,\n  waccmx_online_port_file = '$PORT',"
    s = s.replace(marker, repl)
else:
    s = s.replace('  lwaccmx_neutral_online = .false.,', '  lwaccmx_neutral_online = .true.,')
    s = re.sub(r"\s*waccmx_online_port_file\s*=\s*'.*?',",
               "  waccmx_online_port_file = '$PORT',", s)
p.write_text(s)
PY

cp "$RUNCONFIG" "$RUNCONFIG_BAK"
python3 - <<PY
from pathlib import Path
import re
p = Path('$RUNCONFIG')
s = p.read_text()
s = re.sub(r'(\s*stop_n\s*=\s*)\d+', r'\g<1>300', s)
p.write_text(s)
PY

rm -f "$PORT" "$DVM_URI" "$DVM_PID" sami3_online_receiver.out waccmx_cesm.out
rm -f "$RUN"/live_dump_summary_pkt*.txt "$RUN"/replay_builder_pkt*.out "$RUN"/recv_qc_compare_pkt*.txt
rm -rf "$RUN"/replay_pkt000000 "$RUN"/replay_pkt000001
rm -f "$LIVE_DUMP_DIR"/wxsami3_physstate_* "$RUN/wxsami3_live_meta.json"
rm -f "$CESM_RUNDIR"/cesm.log.* "$CESM_RUNDIR"/atm.log.* "$CESM_RUNDIR"/cpl.log.* 2>/dev/null || true

echo "RUN_DIR=$RUN"
echo "CASE=$CASE"
echo "CESM_EXE=$CESM_EXE"
echo "CESM_RUNDIR=$CESM_RUNDIR"
echo "PAYLOAD_MODE=$WXSAMI3_PAYLOAD_MODE"
echo "LIVE_DUMP_MAX=$WXSAMI3_LIVE_DUMP_MAX"
echo "MAX_PACKETS=$WXSAMI3_MAX_PACKETS"
echo "SEND_EVERY_NSTEPS=$WXSAMI3_SEND_EVERY_NSTEPS"
echo "PHI_PAYLOAD=$WXSAMI3_PHI_PAYLOAD_FILE"
echo "N2_NEGATIVE_MODE=invalid"
echo "TOP_BLEND_MODE=$WXSAMI3_TOP_BLEND_MODE"
echo "BLEND_BOTTOM_KM=$WXSAMI3_BLEND_BOTTOM_KM"
echo "BLEND_TOP_KM=$WXSAMI3_BLEND_TOP_KM"
echo "RUNCONFIG_STOP_N_PATCHED_TO=300"
echo "SAMI3_USE_ONLINE_PHI_WEIMER=$SAMI3_USE_ONLINE_PHI_WEIMER"
echo "PORT=$PORT"
echo "START=$(date)"
echo "HOST=$(hostname)"
echo "PRTE=$(command -v prte)"
echo "PRUN=$(command -v prun)"

cat > "$CESM_WRAPPER" <<EOF
#!/bin/bash
source "$CASE/.env_mach_specific.sh"
export PATH="$PATH"
export LD_LIBRARY_PATH="$WXSAMI3_RUNTIME_LIBS:\$LD_LIBRARY_PATH"
export HOME="$CIME_HOME"
export CIME_MODEL=cesm
export OMP_NUM_THREADS=1
export OMPI_MCA_mpi_yield_when_idle=1
export WXSAMI3_PORT_FILE="$PORT"
export WXSAMI3_PAYLOAD_MODE=live
export WXSAMI3_PAYLOAD_PREFIX="$PAY_FALLBACK"
export WXSAMI3_LIVE_MAP_FILE="$MAP"
export WXSAMI3_NUMWORKERS=32
export WXSAMI3_SKIP_DISCONNECT=0
export WXSAMI3_LIVE_DIAG=1
export WXSAMI3_META_FILE="$RUN/wxsami3_live_meta.json"
export WXSAMI3_LIVE_DUMP_PREFIX="$LIVE_DUMP_PREFIX"
export WXSAMI3_LIVE_DUMP_MAX=1
export WXSAMI3_MAX_PACKETS=1
export WXSAMI3_SEND_EVERY_NSTEPS=1
export WXSAMI3_N2_NEGATIVE_MODE=invalid
export WXSAMI3_PHI_PAYLOAD_FILE="$PHI_PAYLOAD"
export WXSAMI3_TOP_BLEND_MODE="$WXSAMI3_TOP_BLEND_MODE"
export WXSAMI3_BLEND_BOTTOM_KM="$WXSAMI3_BLEND_BOTTOM_KM"
export WXSAMI3_BLEND_TOP_KM="$WXSAMI3_BLEND_TOP_KM"
cd "$CESM_RUNDIR"
exec "$CESM_EXE"
EOF
chmod +x "$CESM_WRAPPER"

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
  -x "SAMI3_USE_ONLINE_PHI_WEIMER=$SAMI3_USE_ONLINE_PHI_WEIMER" \
  -x "WXSAMI3_TOP_BLEND_MODE=$WXSAMI3_TOP_BLEND_MODE" \
  -x "WXSAMI3_BLEND_BOTTOM_KM=$WXSAMI3_BLEND_BOTTOM_KM" \
  -x "WXSAMI3_BLEND_TOP_KM=$WXSAMI3_BLEND_TOP_KM" \
  -n "$SAMI3_RANKS" ./sami3.x > "$RUN/sami3_online_receiver.out" 2>&1 &
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

cd "$CESM_RUNDIR"
timeout 2400s prun --dvm-uri "file:$DVM_URI" \
  -x "OMPI_MCA_mpi_yield_when_idle=$OMPI_MCA_mpi_yield_when_idle" \
  -n "$CESM_RANKS" "$CESM_WRAPPER" > "$RUN/waccmx_cesm.out" 2>&1

wait "$sami3_pid"
pterm --dvm-uri "file:$DVM_URI" || true

module load intel/netcdf/4.7.4/gcc8.5.0_ompi5.0.3 >/dev/null 2>&1
for pkt in 000000 000001; do
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
    occurrence=0
    [ "$pkt" = "000001" ] && occurrence=1
    /usr/bin/python3 "$BASE/scripts/compare_wxsami3_recv_qc.py" \
      --payload-prefix "$replay_prefix" \
      --receiver-log "$RUN/sami3_online_receiver.out" \
      --packet-occurrence "$occurrence" \
      > "$RUN/recv_qc_compare_pkt${pkt}.txt"
  fi
done

echo "--- WACCM-X sender markers"
grep -E 'WXSAMI3|ERROR|FATAL|END OF MODEL RUN' "$RUN/waccmx_cesm.out" "$CESM_RUNDIR"/*.log.* 2>/dev/null | tail -420 || true
echo "--- SAMI3 receiver markers"
grep -E 'SAMI3_USE_ONLINE_PHI_WEIMER|WACCMX_PHI_RECV|hrutw2|nweimer|WACCMX online|WACCMX_RECV_QC|WACCMX_RECV_SOURCE_FLAGS|WACCMX_APPLY_QC|WACCMX_APPLY_SOURCE_FLAGS|WACCMX_APPLY_BLEND|WACCMX neutral apply policy|WACCMX neutral top blend policy|MASTER: All Done|WACCMX online done|fatal|forrtl|NaN|Abort|header mismatch' "$RUN/sami3_online_receiver.out" | tail -420 || true
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
