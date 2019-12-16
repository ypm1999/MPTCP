#!/bin/bash

# Exit on any failure
set -e

ctrlc() {
    killall -9 python
    mn -c
    exit
}

trap ctrlc SIGINT

mkdir -p plots

sudo bash ./run_one2several.sh
sudo bash ./run_queue.sh
sudo bash ./run_RTT_Thoughout.sh
sudo bash ./run_plots.sh