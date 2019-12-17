import numpy as np
import matplotlib.pyplot as plt
import csv

with open("./plots/Rank__ft8.csv", "r") as data_file:
    
    csv_data = csv.reader(data_file)
    
    rank = []
    flow = []

    for i in range(0, 8):
        flow.append([])

    i = 0

    for item in csv_data:
        if i == 0:
            rank = item[1:]
        else:
            flow[i-1] = item[1:]
        i = i + 1

    rank = np.array(rank, dtype=int)
    flow = np.array(flow, dtype=float)

    for fl in flow:
        plt.plot(rank, fl)
    plt.savefig("rank_k8.pdf")