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
topo_to_run=(4 6 8)
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

# ----- Get arguments ------
#get topo
if [ "$1" = "all" ]
then
  topo_to_run=(4 6 8 10 12)
else
  if [ -n "$1" ] && [ $1 -ge 4 ]
  then
    topo_to_run=$1
  fi
fi

# get workload
if [ -n "$2" ]
then
  wl_to_run=$2
fi
if [ "$2" = "all" ]
then
  wl_to_run=('one_to_one' 'one_to_several' 'all_to_all')
fi

#get qmon
if [ -n "$3" ]
then
  qmon="--qmon"
  qmon_status="True"
fi

echo "Experiments to run..."
print_topo=''
for i in ${topo_to_run[*]}
do
  print_topo="$print_topo $i"
done
echo "Fat Tree topologies: k = $print_topo"

print_wl=''
for i in ${wl_to_run[*]}
do
  print_wl="$print_wl $i"
done
echo "Workloads: $print_wl"
echo "Queue monitoring enabled: $qmon_status"
echo

# create directory for plot output
mkdir -p plots


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
          --dir result_RTT_Thoughout \
          $qmon

       # plot RTT
#       python plot_ping.py -k $k -w $workload -f results/ft$k/$workload/*/client_ping* -o plots/ft$k-$workload-rtt.png
       # plot throughput
 #      python plot_hist.py -k $k -w $workload -t $time -f results/ft$k/$workload/*/client_iperf* results/ft$k/$workload/max_throughput.txt -o plots/ft$k-$workload-throughput.png
       # plot link util
#       python plot_link_util.py -k $k -w $workload -f results/ft$k/$workload/*/link_util* -o plots/ft$k-$workload-link_util.png
       # plot queue size
#       if [ -n "$qmon" ]
#       then
#         for f in 1 4 8
#         do
#             #python plot_queue.py -k $k -w $workload -f result_q$queue/ft$k/$workload/flows$f/queue_size* -o plots/ft$k-q$queue-$workload-flows$f-queue_size.png
#         done
#       fi
  done
done

python ./plot_subflow_cmp.py
python ./plot_subflow_sort_cmp.py