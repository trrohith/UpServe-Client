import psutil
import json
import time
import websockets
import websocket
import threading
import asyncio


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

            toSend = {"mtye": "live", "id": 1, "data": toSend}

            await websocket.send(json.dumps(toSend))
            greeting = await websocket.recv()
            print(f"received {greeting}")
            await asyncio.sleep(2)


asyncio.get_event_loop().run_until_complete(generateData())
