import psutil
import json
import time
import websockets
import websocket
import threading
import asyncio
import os.path
import sys
import requests


def proc_by_cpu():
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    listOfProcObjects = []
    time.sleep(0.5)

    for proc in psutil.process_iter():
        try:
            # Fetch process details as dict
            pinfo = proc.as_dict(attrs=["pid", "name", "cpu_percent"])
            pinfo["vms"] = proc.memory_info().vms / (1024 * 1024)
            # Append dict to list
            listOfProcObjects.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    listOfProcObjects = sorted(
        listOfProcObjects, key=lambda procObj: procObj["cpu_percent"], reverse=True
    )

    return listOfProcObjects


def send_system_info(conf):

    d = {
        "id": conf["id"],
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
    }

    request.post("http://sih.rishav.io:8008/sysinfo", json=d)


def get_network():
    r1 = psutil.net_io_counters()
    time.sleep(1)
    r2 = psutil.net_io_counters()
    down = (r2.bytes_recv - r1.bytes_recv) / 1024.0
    up = (r2.bytes_sent - r1.bytes_sent) / 1024.0
    return {"up": up, "down": down}


async def generateData():
    # async with websockets.connect("ws://localhost:9090") as websocket:
    async with websockets.connect("ws://ws.rishav.io:9090") as websocket:
        while True:
            toSend = {}
            toSend["ts"] = time.time()
            toSend["cpu"] = psutil.cpu_percent(interval=1, percpu=True)
            toSend["mem_available"] = psutil.virtual_memory().available
            toSend["mem_total"] = psutil.virtual_memory().total
            toSend["disk_us"] = psutil.disk_usage("/")
            toSend["disk_rdwr"] = psutil.disk_io_counters(perdisk=False, nowrap=True)
            toSend["system_uptime"] = round((time.time() - psutil.boot_time()), 3)
            toSend["proc"] = proc_by_cpu()[:5]
            toSend["net"] = get_network()

            toSend = {"mtye": "live", "id": conf["id"], "data": toSend}

            await websocket.send(json.dumps(toSend))
            greeting = await websocket.recv()
            print(f"received {greeting}")
            await asyncio.sleep(2)


def register_config():
    if not os.path.exists("config.json"):
        print("config.json file not found!")
        print("please create config.json file!")
        sys.exit(0)

    with open("config.json") as f:
        conf = f.read()

    conf = json.loads(conf)
    if "id" not in conf:
        print("please provide id in conf!")
        raise KeyError
    conf["desc"] = conf.get("desc", "No descripttion provided")
    conf["os"] = conf.get("os", "No OS provided")
    conf["phone"] = conf.get("phone", "8961502938")
    conf["email"] = conf.get("email", "rishav.kundu98@gmail.com")

    f = requests.post("http://sih.rishav.io:8008/reg", json=conf)
    return conf


if __name__ == "__main__":
    conf = register_config()
    asyncio.get_event_loop().run_until_complete(generateData(conf))
