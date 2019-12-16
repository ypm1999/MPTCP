import argparse, glob
import numpy as np

def parse_iperf_client_file(f):
    lines = open(f).readlines()
    if (len(lines) < 4):
        print(f"{f} is not used because to short")
        return None
    line = lines[-1].split(",")
    length = line[-3].split("-")
    if (float(length[0]) != 0 or float(length[1]) < 30):
        print(f"{f} is not used because error last line")
        return None
    rate = float(line[-1])
    return rate
'''
PING 10.0.1.3 (10.0.1.3) 56(84) bytes of data.
64 bytes from 10.0.1.3: icmp_req=1 ttl=64 time=296 ms
64 bytes from 10.0.1.3: icmp_req=2 ttl=64 time=1.08 ms
64 bytes from 10.0.1.3: icmp_req=3 ttl=64 time=0.049 ms
64 bytes from 10.0.1.3: icmp_req=4 ttl=64 time=0.077 ms
64 bytes from 10.0.1.3: icmp_req=5 ttl=64 time=94.3 ms
64 bytes from 10.0.1.3: icmp_req=6 ttl=64 time=252 ms
64 bytes from 10.0.1.3: icmp_req=7 ttl=64 time=533 ms
64 bytes from 10.0.1.3: icmp_req=9 ttl=64 time=426 ms
64 bytes from 10.0.1.3: icmp_req=10 ttl=64 time=183 ms
64 bytes from 10.0.1.3: icmp_req=11 ttl=64 time=44.6 ms
64 bytes from 10.0.1.3: icmp_req=12 ttl=64 time=47.9 ms
64 bytes from 10.0.1.3: icmp_req=13 ttl=64 time=102 ms
64 bytes from 10.0.1.3: icmp_req=14 ttl=64 time=552 ms
64 bytes from 10.0.1.3: icmp_req=15 ttl=64 time=550 ms
64 bytes from 10.0.1.3: icmp_req=16 ttl=64 time=204 ms
64 bytes from 10.0.1.3: icmp_req=17 ttl=64 time=47.0 ms
64 bytes from 10.0.1.3: icmp_req=18 ttl=64 time=177 ms
64 bytes from 10.0.1.3: icmp_req=19 ttl=64 time=371 ms
64 bytes from 10.0.1.3: icmp_req=20 ttl=64 time=616 ms

--- 10.0.1.3 ping statistics ---
20 packets transmitted, 19 received, 5% packet loss, time 28536ms
rtt min/avg/max/mdev = 0.049/236.954/616.464/206.403 ms
'''
def parse_ping(fname):
    lines = open(fname).readlines()
    if not ("ping statistics ---" in lines[-3]):
        print(f"{fname} is not used because not finished")
        return None, None
    loss_rate = 0
    rtt = 0
    for line in lines:
        if 'packets transmitted' in line:
            tmp = line.split(", ")[-2]
            sete = tmp.split(" ")[0]
            loss_rate = float(sete[:-1]) / 100

        if "min/avg/max/mdev" in line:
            vals = line.split(" = ")[1].split(" ")[0]
            vals = [float(val) for val in vals.split("/")]
            rtt = vals[1]
    return rtt, loss_rate

src = "./one_to_several/"
output_name = "./plots/one_to_several"

k_list = [4, 6, 8]
flow_list = [1, 2, 4, 6, 8]

for ksize in k_list:
    file_list = {}
    max_throughput = {}
    throughput = {}
    loss_rate = {}
    rtt = {}
    for j in flow_list:
        print(src + "ft%d/one_to_several/flows%d/*.txt" % (ksize, j))
        files = glob.glob(src + "ft%d/one_to_several/flows%d/*.txt" % (ksize, j))
        iperf_file = [file for file in files if "client_iperf" in file]
        ping_file = [file  for file in files if "client_ping" in file]
        file_list[j] = {"iperf": iperf_file, "ping": ping_file}

        # handel iperf
        cnt = 0
        total = 0
        for file in iperf_file:
            rate = parse_iperf_client_file(file)
            if rate != None:
                cnt += 1
                total += rate
        if (cnt != len(iperf_file)):
            print("subflows-ft%d-flow%d iperf is not complete %d/%d" % (ksize, j, cnt, len(iperf_file)))
        throughput[j] = total / cnt

        # handel ping
        cnt = 0
        total_loss = 0
        total_rtt = 0
        for file in ping_file:
            rtt_now, loss = parse_ping(file)
            if not (rtt_now == None or loss == None):
                cnt += 1
                total_loss += loss
                total_rtt += rtt_now
        if (cnt != len(ping_file)):
            print("subflows-ft%d-flow%d ping is not complete %d/%d" % (ksize, j, cnt, len(ping_file)))
        loss_rate[j] = total_loss / cnt
        rtt[j] = total_rtt / cnt

    # get max iperf
    max_file = src + "/ft%d/one_to_several/max_throughput.txt" % (ksize)
    max_throughput = [parse_iperf_client_file(max_file)] * len(flow_list)

    output = open(output_name + "_ft%d.csv" % ksize, "w")
    output.write("subflow, %s\n" % ",".join([str(i) for i in flow_list]))

    vals = [str(item / 1024) for item in throughput.values()]
    output.write("iperf," + ",".join(vals) + "\n")

    # output.write("iperf_max," + ",".join([str(i / 1024) for i in max_throughput]) + "\n")
    #
    # vals = [str(item) for item in loss_rate.values()]
    # output.write("lossRate," + ",".join(vals) + "\n")

    # vals = [str(item) for item in rtt.values()]
    # output.write("RTT," + ",".join(vals) + "\n")
    output.close()






