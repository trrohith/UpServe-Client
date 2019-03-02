import psutil
import json
import time
import websockets
import websocket
import threading
import asyncio


def getListOfProcessSortedByMemory():
    """
    Get list of running process sorted by Memory Usage
    """
    threading.Timer(5.0, getListOfProcessSortedByMemory).start()
    listOfProcObjects = []
    # Iterate over the list
    for proc in psutil.process_iter():
        try:
            # Fetch process details as dict
            pinfo = proc.as_dict(attrs=["pid", "name", "cpu_percent"])
            pinfo["vms"] = proc.memory_info().vms / (1024 * 1024)
            # Append dict to list
            listOfProcObjects.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Sort list of dict by key vms i.e. memory usage
    listOfProcObjects = sorted(
        listOfProcObjects, key=lambda procObj: procObj["vms"], reverse=True
    )

    return listOfProcObjects


"""listOfRunningProcess = getListOfProcessSortedByMemory()

for elem in listOfRunningProcess[:5] :
    print(json.dumps(elem))"""


async def generateData():
    async with websockets.connect("ws://ws.rishav.io:9090") as websocket:
        toSend = {}
        toSend["ts"] = time.time()
        toSend["cpu"] = psutil.cpu_percent(interval=1, percpu=True)
        toSend["mem_available"] = psutil.virtual_memory().available
        toSend["mem_total"] = psutil.virtual_memory().total
        toSend["disk_us"] = psutil.disk_usage("/")
        toSend["disk_rdwr"] = psutil.disk_io_counters(perdisk=False, nowrap=True)
        toSend["system_uptime"] = round((time.time() - psutil.boot_time()), 3)
        toSend = json.dumps(toSend)
        toSend = '{"mtype":"live","id":"1","data": ' + toSend + "}"
        await websocket.send(toSend)
        greeting = await websocket.recv()
        print(f"<{greeting}")
        await asyncio.sleep(2)
        await generateData()


asyncio.get_event_loop().run_until_complete(generateData())
