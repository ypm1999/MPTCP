import numpy as np
import matplotlib.pyplot as plt
import csv

color = ['#E47C3C', '#76D7C4', '#34495E', '#F39C12']

data_file4 = open("./plots/one_to_several_ft4.csv", "r")
data_file6 = open("./plots/one_to_several_ft6.csv", "r")
data_file8 = open("./plots/one_to_several_ft8.csv", "r")

csv_data4 = csv.reader(data_file4)
csv_data6 = csv.reader(data_file6)
csv_data8 = csv.reader(data_file8)


subflow = [1, 2, 4, 6, 8]
throughput = []

for i in range(0, 3):
    throughput.append([])

for item in csv_data4:
    if item[0] == 'iperf':
        throughput[0] = item[1:]

for item in csv_data6:
    if item[0] == 'iperf':
        throughput[1] = item[1:]

for item in csv_data8:
    if item[0] == 'iperf':
        throughput[2] = item[1:]

throughput = np.array(throughput, dtype=float)

x = np.arange(5)

bar_width = 0.3

for i in range(3):
    plt.bar(x + i * bar_width, throughput[i], width=bar_width, fc=color[i])
plt.xticks(x + bar_width * 2, subflow)
plt.savefig("one_to_several.pdf")
data_file4.close()
data_file6.close()
data_file8.close()