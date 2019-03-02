import time
import psutil
import os
import json


def stream_host_stats():
    while True:
        net = psutil.net_io_counters(pernic=True)
        time.sleep(1)
        net1 = psutil.net_io_counters(pernic=True)
        net_stat_download = {}
        net_stat_upload = {}
        print("hello")
        for k, v in net.items():
            for k1, v1 in net1.items():
                if k1 == k:
                    net_stat_download[k] = (v1.bytes_recv - v.bytes_recv) / 1000.0
                    net_stat_upload[k] = (v1.bytes_sent - v.bytes_sent) / 1000.0
                    print(json.dumps(net_stat_download))
                    print(json.dumps(net_stat_upload))


stream_host_stats()
