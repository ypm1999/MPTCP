import numpy as np
import matplotlib.pyplot as plt
import csv

with open("./plots/RTT_Thoughout__ft4.csv", "r") as data_file:
    
    csv_data = csv.reader(data_file)
    
    subflow = []
    throughput = []
    
    for item in csv_data:
        if item[0] == "subflow":
            subflow = item[1:]
        if item[0] == "iperf":
            throughput = item[1:]

    subflow = np.array(subflow, dtype=int)
    throughput = np.array(throughput, dtype=float)
    
    plt.bar(subflow, throughput)
    plt.savefig("Throughput_k4.pdf")