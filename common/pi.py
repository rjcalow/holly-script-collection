import os
import sys
import psutil
import time
from datetime import datetime
import subprocess


def pitemp():
    # Read the temperature
    cpu_temp = os.popen("vcgencmd measure_temp").readline()
    cpu_temp = cpu_temp.replace("temp=", "").strip("\n").strip("'C")
    # now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # ex: 2022/06/24 12:07:18
    return cpu_temp


def pimemory():
    memory = psutil.virtual_memory()
    total = str(round(memory.total / 1000000))
    return str(round(memory.used / 1000000)) + " / " + total + " MB"


def pidisk():
    disk = psutil.disk_usage("/")
    total = str(round(disk.total / 1000000000, 2)) + " GB"

    return str(round(disk.used / 1000000000, 2)) + " / " + total


def picpuusage():
    cpuusage = psutil.cpu_percent(interval=1)
    return str(cpuusage) + "%"


def piuptime():
    output = os.popen("uptime -p").readline()
    return str(output)

def restart():
    subprocess.call("/home/holly/start.sh", shell=True)