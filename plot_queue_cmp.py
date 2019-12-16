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

k_list = [6, 8]
flow_list = [1, 2, 4, 8]
queue_list = [25, 50, 100, 200]

for ksize in k_list:
    file_list = {}
    max_throughput = {}
    throughput = {}
    loss_rate = {}
    rtt = {}
    for i in queue_list:
        file_list[i] = {}
        throughput[i] = {}
        loss_rate[i] = {}
        rtt[i] = {}
        for j in flow_list:
            files = glob.glob("./result_q%d/ft%d/one_to_one/flows%d/*.txt" % (i, ksize, j))
            iperf_file = [file for file in files if "client_iperf" in file]
            ping_file = [file  for file in files if "client_ping" in file]
            file_list[i][j] = {"iperf": iperf_file, "ping": ping_file}
            print(len(iperf_file), len(ping_file))

            # handel iperf
            cnt = 0
            total = 0
            for file in iperf_file:
                rate = parse_iperf_client_file(file)
                if rate != None:
                    cnt += 1
                    total += rate
            if (cnt != len(iperf_file)):
                print("queue%d-ft%d-flow%d iperf is not complete %d/%d" % (i, ksize, j, cnt, len(iperf_file)))
            throughput[i][j] = total / cnt

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
                print("queue%d-ft%d-flow%d ping is not complete %d/%d" % (i, ksize, j, cnt, len(ping_file)))
            loss_rate[i][j] = total_loss / cnt
            rtt[i][j] = total_rtt / cnt

        # get max iperf
        max_file = "./result_q%d/ft%d/one_to_one/max_throughput.txt" % (i, ksize)
        max_throughput[i] = parse_iperf_client_file(max_file)

    output = open("plots/queue_ft%d.csv" % ksize, "w")
    output.write("queue, 25, 50, 100, 200\n")
    for j in flow_list:
        vals = [str(item[j] / 1024) for item in throughput.values()]
        output.write("iperf_flow%d," % j + ",".join(vals) + "\n")
    # output.write("iperf_max," + ",".join([str(i / 1024) for i in max_throughput.values()]) + "\n")

    # for j in flow_list:
    #     vals = [str(item[j]) for item in loss_rate.values()]
    #     output.write("lossRate_flow%d," % j + ",".join(vals) + "\n")
    # for j in flow_list:
    #     vals = [str(item[j]) for item in rtt.values()]
    #     output.write("RTT_flow%d," % j + ",".join(vals) + "\n")
    output.close()






