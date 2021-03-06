import psutil
import json
import time
import websockets
import threading
import asyncio
import os.path
import sys
import requests
import threading
import subprocess


def proc_by_cpu():
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    listOfProcObjects = []
    time.sleep(0.1)

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
        "total_memory": psutil.virtual_memory().total,
    }

    requests.post("http://sih.rishav.io:8008/sysinfo", json=d)


def get_network():
    r1 = psutil.net_io_counters()
    time.sleep(0.5)
    r2 = psutil.net_io_counters()
    down = (r2.bytes_recv - r1.bytes_recv) / 1024.0
    up = (r2.bytes_sent - r1.bytes_sent) / 1024.0
    return {"up": up, "down": down}


def get_docker_stats():
    try:
        lines = subprocess.check_output(
            ["docker", "stats", "--no-stream"], universal_newlines=True
        ).splitlines()
        store = []
        for line in lines[1:]:
            line = line.split()
            store.append(
                {"cid": line[0], "name": line[1], "cpu": line[2], "mem": line[6]}
            )
        return store
    except FileNotFoundError:
        return []


def getJAVA():
    try:
        response = subprocess.check_output(
            "c:\\Program Files\\Java\\jdk1.8.0_201\\bin\\jps.exe",
            universal_newlines=True,
        )
        values = response.split()
        store = []
        for i in range(len(values)):
            if i % 2 != 0 and values[i] != "Jps":
                p = psutil.Process(pid=int(values[i - 1]))
                d = {
                    "id": str(values[i - 1]),
                    "name": values[i],
                    "cpu": p.cpu_percent(interval=0.1),
                    "mem": p.memory_percent(),
                }
                store.append(d)
        return store
    except FileNotFoundError:
        return []


async def generateData():
    # async with websockets.connect("ws://localhost:9090") as websocket:
    cnt = 0
    prev_docker = []
    async with websockets.connect("ws://ws.rishav.io:9090") as websocket:
        while True:
            print("generating")
            toSend = {}
            toSend["ts"] = time.time()
            toSend["cpu"] = psutil.cpu_percent(interval=0.1, percpu=True)
            toSend["mem_total"] = psutil.virtual_memory().total
            toSend["mem_available"] = psutil.virtual_memory().available
            toSend["disk_us"] = psutil.disk_usage("/")
            toSend["disk_rdwr"] = psutil.disk_io_counters(perdisk=False, nowrap=True)
            toSend["system_uptime"] = round((time.time() - psutil.boot_time()), 3)
            toSend["proc"] = proc_by_cpu()[:5]
            toSend["net"] = get_network()
            if cnt % 10 == 0:
                prev_docker = get_docker_stats()
            toSend["docker"] = prev_docker
            print(toSend["docker"])
            cnt += 1
            toSend["java"] = getJAVA()

            toSend = {"mtye": "live", "id": conf["id"], "data": toSend}
            print("done generating")
            await websocket.send(json.dumps(toSend))
            greeting = await websocket.recv()
            print(f"received {greeting}")


running_proc = []


async def check_running_procs(conf):
    to_monitor = conf["proc"]
    while True:
        print("checking procs!", running_proc)
        to_monitor = conf["proc"]
        cur_procs = proc_by_cpu()
        for monitor in to_monitor:
            if monitor in [x["name"] for x in cur_procs]:
                if monitor not in running_proc:
                    print("started " + monitor)
                    requests.post(
                        "http://sih.rishav.io:8008/notif",
                        json={"id": conf["id"], "msg": f"{monitor} started!"},
                    )
                    running_proc.append(monitor)
            else:
                if monitor in running_proc:
                    print("stopped " + monitor)
                    requests.post(
                        "http://sih.rishav.io:8008/notif",
                        json={"id": conf["id"], "msg": f"{monitor} stopped!"},
                    )
                    running_proc.remove(monitor)
        await asyncio.sleep(60)


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
    conf["proc"] = conf.get("proc", [])

    f = requests.post("http://sih.rishav.io:8008/reg", json=conf)
    return conf


if __name__ == "__main__":
    conf = register_config()
    send_system_info(conf)
    asyncio.get_event_loop().create_task(check_running_procs(conf))
    # asyncio.get_event_loop().run_forever()
    asyncio.get_event_loop().run_until_complete(generateData())
