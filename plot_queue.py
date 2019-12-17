import numpy as np
import matplotlib.pyplot as plt
import csv

color = ['#E47C3C', '#76D7C4', '#F39C12', '#34495E']

with open("./plots/queue_ft6.csv", "r") as data_file:
    csv_data = csv.reader(data_file)

    queue = []
    subflow = []

    for i in range(0, 4):
        subflow.append([])

    i = 0

    for item in csv_data:
        if i == 0:
            queue = item[1:]
        else:
            subflow[i - 1] = item[1:]
        i = i + 1

    subflow = np.array(subflow, dtype=float)

    x = np.arange(4)

    bar_width = 0.2

    for i in range(4):
        plt.bar(x + i * bar_width, subflow[i], width=bar_width, fc=color[i])
    plt.xticks(x + bar_width * 2, queue)
    plt.savefig("queue.pdf")