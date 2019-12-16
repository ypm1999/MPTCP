#!/bin/bash

# Exit on any failure
set -e

ctrlc() {
    killall -9 python
    mn -c
    exit
}

trap ctrlc SIGINT

iperf=~/iperf-patched/src/iperf
time=40
bw=1
queue_size=100
topo_to_run=(6 8)
wl_to_run=('one_to_one')
#qmon="--qmon"
#qmon_status="True"
qmon=""
qmon_status="False"

# ----- Sanity checks -----
if [ ! -f $iperf ]
then
  echo "Patched iperf not installed! ... using regular iperf"
  echo "Install patched iperf using: ./iperf_patch/build-patched-iperf.sh"
  iperf='iperf'
  sleep 10
fi

if [ ! "$(ls -A util)" ]
then
  echo "You forgot initialize submodules"
  echo "Run: git submodule init && git submodule update"
  exit 1
fi


# create directory for plot output
mkdir -p plots


queue_list=(25 50 100 200)
# ----- Run Mininet tests ------
for queue in ${queue_list[*]}
do
for k in ${topo_to_run[*]} #4 6 8 10 12
do
  for workload in ${wl_to_run[*]} #one_to_one one_to_several all_to_all
  do
      echo "-----------------Running k=$k, workload=$workload-------------------"
      # run experiment
      python mptcp_test.py \
          --bw $bw \
          --queue $queue \
          --workload $workload \
          --topology ft$k \
          --time $time \
          --iperf $iperf \
          --dir result_q$queue \
          $qmon
  done
done
done
python ./plot_queue_cmp

