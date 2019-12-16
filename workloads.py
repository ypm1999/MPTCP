#!/usr/bin/env python

from random import choice, shuffle
from subprocess import Popen, PIPE
from mininet.util import pmonitor
from time import time, sleep
import sys
import termcolor as T
from mininet.cli import CLI
from collections import defaultdict, Counter
from monitor import monitor_qlen
from multiprocessing import Process
from util.helper import *

def median(l):
    "Compute median from an unsorted list of values"
    s = sorted(l)
    if len(s) % 2 == 1:
        return s[(len(l) + 1) / 2 - 1]
    else:
        lower = s[len(l) / 2 - 1]
        upper = s[len(l) / 2]
        return float(lower + upper) / 2

def progress(t):
    while t > 0:
        print T.colored('  %3d seconds left             \r' % (t), 'cyan'),
        t -= 1
        sys.stdout.flush()
        sleep(1)
    print '\r\n'

class Workload():
    def __init__(self, net, iperf, seconds):
        self.iperf = iperf
        self.seconds = seconds
        self.mappings = []
        self.net = net

    def run(self, output_dir, qmon_status):
        servers = list(set([mapping[0] for mapping in self.mappings]))

        interfaces = []
        for node in self.net.switches:
            for intf in node.intfList():
                if intf.link:
                    interfaces.append(intf.link.intf1.name)
                    interfaces.append(intf.link.intf2.name)

        serverIperfProcs = []
        for server in servers:
            serverIperfProcs.append(server.popen("%s -s -p %s > %s/server_iperf-%s.txt" %
                         (self.iperf, 5001, output_dir, server.name), shell=True))

        # start CPU monitor
        Popen('mpstat 2 %d > %s/cpu_utilization.txt' % (self.seconds/2 + 10,
                                                        output_dir), shell=True)
        print("-->Start running processes")
        procs = []
        for mapping in self.mappings:
            server, client = mapping
            num_pings = self.seconds // 2
            ping = client.popen("ping -c %d -i 2 %s > %s/client_ping-%s-%s.txt"
                         % (num_pings, server.IP(), output_dir, client.name,
                            server.name), shell=True, stdout=PIPE, stderr=PIPE)
            iperf = client.popen(
                    "%s -c %s -p %s -t %d -yc -i 10 > %s/client_iperf-%s-%s.txt" %
                    (self.iperf, server.IP(), 5001, self.seconds,
                     output_dir, client.name, server.name), shell=True, stdout=PIPE, stderr=PIPE)
            procs.append([(str(server), str(client)), iperf, ping])

        if qmon_status:
            qmons = []
            switch_names = [switch.name for switch in self.net.switches]
            for iface in interfaces:
                if iface.split('-')[0] in switch_names:
                    qmons.append(start_qmon(iface,
                                            outfile="%s/queue_size-%s.txt"
                                            % (output_dir, iface)))

        print("-->Start taking utilization samples")
        # take utilization samples
        get_rates(interfaces, output_dir)
        # print("-->Finish taking utilization samples")


        progress(self.seconds - 10) # remove some time for get_rates
        print "waiting proc[%d]: " % len(procs),
        sys.stdout.flush()
        sleep_cnt = 5 + len(self.mappings) // 10

        while (len(procs) > 0 and sleep_cnt > 0):
            cnt = 0
            for i, proc in enumerate(procs[:]):
                if (proc[1].returncode == None or proc[2].returncode == None):
                    cnt += 1
                    # print "%d," % i,
                    # sys.stdout.flush()
                    continue
                procs.remove(proc)
                server, client = proc[0]
                out1, err1 = proc[1].communicate()
                out2, err2 = proc[2].communicate()
                if not(out1 == "" and err1 == "" and proc[1].returncode == 0):
                    print("[ERROR] Iperf from {} to {} return {}, out=\"{}\", err=\"{}\"".
                          format(server, client, proc[1].returncode, out1, err1))
                if not (out2 == "" and err2 == "" and proc[2].returncode == 0):
                    print("[ERROR] Ping from {} to {} return {}, out=\"{}\", err=\"{}\"".
                          format(server, client, proc[2].returncode, out2, err2))
            print " %s processes" % cnt
            sleep_cnt -= 1
            if (len(procs) > 0):
                print "sleep 10 sec to wait"
                sleep(10)
        for i, proc in enumerate(procs[:]):
            if (proc[1].returncode == None or proc[2].returncode == None):
                if (proc[1].returncode == None):
                    proc[1].terminate()
                    print "iperf(%d), " % i,
                if (proc[2].returncode == None):
                    proc[2].terminate()
                    print "ping(%d), " % i,
                sys.stdout.flush()
                continue
            server, client = proc[0]
            out1, err1 = proc[1].communicate()
            out2, err2 = proc[2].communicate()
            if not (out1 == "" and err1 == "" and proc[1].returncode == 0):
                print("[ERROR] Iperf from {} to {} return {}, out=\"{}\", err=\"{}\"".
                      format(server, client, proc[1].returncode, out1, err1))
            if not (out2 == "" and err2 == "" and proc[2].returncode == 0):
                print("[ERROR] Ping from {} to {} return {}, out=\"{}\", err=\"{}\"".
                      format(server, client, proc[2].returncode, out2, err2))
        print("-->Finished, kill iperf servers")
        # for proc in serverIperfProcs:
        #     proc.terminate()

        if qmon_status:
            for qmon in qmons:
                qmon.terminate()

class OneToOneWorkload(Workload):
    def __init__(self, net, iperf, seconds):
        Workload.__init__(self, net, iperf, seconds)
        hosts = list(net.hosts)
        shuffle(hosts)
        group1, group2 = hosts, hosts[1:]
        group2.append(hosts[0])
        self.create_mappings(group1, group2)
        # self.create_mappings(group2, group1)

    def create_mappings(self, group1, group2):
        print("create maping")
        # print([str(i) for i in group1])
        # print([str(i) for i in group2])
        for i in range(len(group1)):
            server = group1[i]
            client = group2[i]
            print "[%s, %s]" % (str(client), str(server))
            self.mappings.append((server, client))
        print "\r\n"


class OneToSeveralWorkload(Workload):
    def __init__(self, net, iperf, seconds, num_conn=4):
        Workload.__init__(self, net, iperf, seconds)
        self.create_mappings(net.hosts, num_conn)

    def create_mappings(self, group, num_conn):
        for server in group:
            clients = list(group)
            clients.remove(server)
            shuffle(clients)
            for client in clients[:num_conn]:
                self.mappings.append((server, client))

class AllToAllWorkload(Workload):
    def __init__(self, net, iperf, seconds):
        Workload.__init__(self, net, iperf, seconds)
        self.create_mappings(net.hosts)

    def create_mappings(self, group):
        for server in group:
            for client in group:
                if client != server:
                    self.mappings.append((server, client))


def get_txbytes(iface):
    f = open('/proc/net/dev', 'r')
    lines = f.readlines()
    for line in lines:
        if iface in line:
            break
    f.close()
    if not line:
        raise Exception("could not find iface %s in /proc/net/dev:%s" %
                        (iface, lines))
    # Extract TX bytes from:
    #Inter-|   Receive                                                |  Transmit
    # face |bytes    packets errs drop fifo frame compressed multicast|bytes packets errs drop fifo colls carrier compressed
# lo: 6175728   53444    0    0    0     0          0         0  6175728   53444 0    0    0     0       0          0
    return float(line.split()[9])

NSAMPLES = 3
SAMPLE_PERIOD_SEC = 1
SAMPLE_WAIT_SEC = 1.0

def get_rates(ifaces, output_dir, nsamples=NSAMPLES, period=SAMPLE_PERIOD_SEC,
              wait=SAMPLE_WAIT_SEC):
    """Returns the interface @iface's current utilization in Mb/s.  It
    returns @nsamples samples, and each sample is the average
    utilization measured over @period time.  Before measuring it waits
    for @wait seconds to 'warm up'."""
    # Returning nsamples requires one extra to start the timer.
    nsamples += 1
    last_time = 0
    last_txbytes = Counter()
    ret = []
    sleep(wait)
    txbytes = Counter()
    ret = defaultdict(list)
    times = []
    while nsamples:
        nsamples -= 1
        for iface in ifaces:
            txbytes[iface] = get_txbytes(iface)
        now = time()
        elapsed = now - last_time
        #if last_time:                                                                 
        #    print "elapsed: %0.4f" % (now - last_time)                                
        last_time = now
        # Get rate in Mbps; correct for elapsed time.
        for iface in txbytes:
            rate = (txbytes[iface] - last_txbytes[iface]) * 8.0 / 1e6 / elapsed
            if last_txbytes[iface] != 0:
                # Wait for 1 second sample
                ret[iface].append(rate)
        last_txbytes = txbytes.copy()
        print '.',
        sys.stdout.flush()
        sleep(period)
    f = open("%s/link_util.txt" % output_dir, 'w')
    for iface in ret:
        f.write("%f\n" % median(ret[iface]))
    f.close()

def start_qmon(iface, interval_sec=1.0, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor
