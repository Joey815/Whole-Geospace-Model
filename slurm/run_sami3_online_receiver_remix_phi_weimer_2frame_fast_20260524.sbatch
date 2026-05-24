#!/bin/bash -l
#SBATCH --job-name=sami3_phi2fast
#SBATCH --partition=intel
#SBATCH --nodes=1
#SBATCH --ntasks=34
#SBATCH --cpus-per-task=1
#SBATCH --time=00:20:00
#SBATCH --output=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/sami3_online_receiver_remix_phi_weimer_2frame_fast_20260524_0000/slurm-%j.out
#SBATCH --error=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official/runs/sami3_online_receiver_remix_phi_weimer_2frame_fast_20260524_0000/slurm-%j.err

set -eo pipefail

export PATH=/apps/support/intel_spr_rocky8.9/openmpi/5.0.3/gcc8.5.0/bin:$PATH
export LD_LIBRARY_PATH=/apps/support/intel_spr_rocky8.9/openmpi/5.0.3/gcc8.5.0/lib:$LD_LIBRARY_PATH
export WXSAMI3_RECV_QC=1
export SAMI3_USE_EXISTING_PHI_WEIMER=1

BASE=/home/jiaoy_group/jiaoy/data/waccmx-sami3_official
COLLAB=/home/jiaoy_group/jiaoy/data/MAGE1.25/waccmx-sami3-collab-20260524
SRC=$BASE/runs/sami3_waccmx_neutral_esmf_msis_top_weimer_20231013_0000
SAMI_WORK=$BASE/work/sami3-3.22_online_mpi_openmpi_remix_phi_20260524
RUN=$BASE/runs/sami3_online_receiver_remix_phi_weimer_2frame_fast_20260524_0000
PAY=$BASE/runs/waccmx_replay_payload_from_live_dump_20260523/waccmx_neutral_rank
PHI_SRC=$COLLAB/logs/remix_sami3_phi_weimer_transition_runtime_20260524/phi_weimer_remix_north_2frame_fast.inp
PORT=$RUN/waccmx_sami3_online_port.txt
SENDER=$BASE/bin/wxsami3_neutral_sender_live_replay_openmpi
SENDER_SRC=$COLLAB/scripts/wxsami3_neutral_sender_stub.c
DVM_URI=$RUN/prte_dvm.uri
DVM_PID=$RUN/prte_dvm.pid

mkdir -p "$RUN" "$BASE/bin"

if [ ! -f "$RUN/.prepared_from_msis_top_smoke" ]; then
  rsync -a \
    --exclude='slurm-*' \
    --exclude='*.out' \
    "$SRC"/ "$RUN"/
  touch "$RUN/.prepared_from_msis_top_smoke"
fi

mpicc -O2 -o "$SENDER" "$SENDER_SRC"

cp "$SAMI_WORK/sami3.x" "$RUN/sami3.x"
cp "$SAMI_WORK/waccmx_neutral_mod.f90" "$RUN/waccmx_neutral_mod.f90"
cp "$SAMI_WORK/namelist_mod.f90" "$RUN/namelist_mod.f90"
cp "$SAMI_WORK/sami3-3.22.f90" "$RUN/sami3-3.22.f90"
cp "$PHI_SRC" "$RUN/phi_weimer.inp"

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

rm -f "$PORT" "$DVM_URI" "$DVM_PID" sami3_online_receiver.out neutral_sender.out recv_qc_compare.txt

echo "RUN_DIR=$RUN"
echo "PAYLOAD_PREFIX=$PAY"
echo "PHI_SRC=$PHI_SRC"
echo "PORT=$PORT"
echo "START=$(date)"
echo "HOST=$(hostname)"
echo "MPICC=$(command -v mpicc)"
echo "PRTE=$(command -v prte)"
echo "PRUN=$(command -v prun)"
echo "WXSAMI3_RECV_QC=$WXSAMI3_RECV_QC"
echo "SAMI3_USE_EXISTING_PHI_WEIMER=$SAMI3_USE_EXISTING_PHI_WEIMER"
echo "NAMELIST fast phi transition: maxstep=20 hrmax=.020000 tphi=1."
od -An -t u4 -N 120 "$RUN/phi_weimer.inp"

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
  -x "SAMI3_USE_EXISTING_PHI_WEIMER=$SAMI3_USE_EXISTING_PHI_WEIMER" \
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

timeout 900s prun --dvm-uri "file:$DVM_URI" -n 1 "$SENDER" "$PORT" "$PAY" 0 0.0 > "$RUN/neutral_sender.out" 2>&1
wait "$sami3_pid"

pterm --dvm-uri "file:$DVM_URI" || true

/usr/bin/python3 "$BASE/scripts/compare_wxsami3_recv_qc.py" \
  --payload-prefix "$PAY" \
  --receiver-log "$RUN/sami3_online_receiver.out" \
  > "$RUN/recv_qc_compare.txt"

echo "--- neutral sender tail"
tail -80 "$RUN/neutral_sender.out"
echo "--- sami3 online receiver markers"
grep -E 'SAMI3_USE_EXISTING_PHI_WEIMER|hrutw2|nweimer|calling potpphi|WACCMX online|WACCMX_RECV_QC|WACCMX_RECV_SOURCE_FLAGS|MASTER: All Done|fatal|forrtl|NaN|Abort|EOF|header mismatch' "$RUN/sami3_online_receiver.out" | tail -260 || true
echo "--- receiver QC compare"
cat "$RUN/recv_qc_compare.txt"
echo "END=$(date)"
