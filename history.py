import json
import os
import time
from datetime import datetime

HISTORY_FILE = "performance_history.json"

report_id = 0

def save_report(diagnostic, current_processes, current_memory_usage, current_storage_usage, current_top_snapshot, current_networking_snapshot):
    global report_id
    report_id += 1
    timestamp = datetime.fromtimestamp(time.time()).isoformat()

    # Flatten processes
    process_fields = {}
    for i, process in enumerate(current_processes, start=1):
        process_fields[f"process_{i}_user"] = process["user"]
        process_fields[f"process_{i}_pid"] = process["pid"]
        process_fields[f"process_{i}_cpu"] = process["cpu_percentage"]
        process_fields[f"process_{i}_mem"] = process["memory_percentage"]
        process_fields[f"process_{i}_command"] = process["process_running"]
        process_fields[f"process_{i}_health"] = process["health"]

    # Flatten networking
    tcp = ", ".join(sorted(current_networking_snapshot["TCP Addresses"]))
    udp = ", ".join(sorted(current_networking_snapshot["UDP Addresses"]))
    external = ", ".join(sorted(current_networking_snapshot["Listening on external interface"]))

    record = {
        "report_id": report_id,
        "timestamp": timestamp,

        **process_fields,

        "ram_total": current_memory_usage["RAM"]["ram_total_memory"],
        "ram_used": current_memory_usage["RAM"]["ram_used_memory"],
        "ram_free": current_memory_usage["RAM"]["ram_free_memory"],
        "ram_health": diagnostic["Memory"]["ram_memory_health"],

        "swap_total": current_memory_usage["Swap"]["swap_total_memory"],
        "swap_used": current_memory_usage["Swap"]["swap_used_memory"],
        "swap_free": current_memory_usage["Swap"]["swap_free_memory"],
        "swap_health": diagnostic["Memory"]["swap_memory_health"],

        "disk_filesystem": current_storage_usage["filesystem_disk"],
        "disk_total": current_storage_usage["total_disk"],
        "disk_used": current_storage_usage["used_disk"],
        "disk_available": current_storage_usage["available_disk"],
        "disk_use_percent": current_storage_usage["use_percentage_disk"],
        "disk_health": diagnostic["Storage"]["disk_health"],

        "load_avg_1min": current_top_snapshot["Load Average"]["one_minute_load_average"],
        "load_avg_5min": current_top_snapshot["Load Average"]["five_minute_load_average"],
        "load_avg_15min": current_top_snapshot["Load Average"]["fifteen_minute_load_average"],
        "load_avg_health": diagnostic["CPU"]["load_average_health"],
        "cpu_idle": current_top_snapshot["CPU%"]["cpu_idle"],
        "cpu_idle_health": diagnostic["CPU"]["cpu_idle_health"],
        "cpu_system": current_top_snapshot["CPU%"]["cpu_system"],
        "cpu_system_health": diagnostic["CPU"]["cpu_system_health"],
        "tasks_running": current_top_snapshot["Tasks"]["task_running"],
        "tasks_running_health": diagnostic["CPU"]["running_tasks_health"],
        "tasks_zombie": current_top_snapshot["Tasks"]["task_zombie"],
        "tasks_zombie_health": diagnostic["CPU"]["zombie_tasks_health"],

        "network_health": diagnostic["Network"]["network_health"],
        "tcp_addresses": tcp,
        "udp_addresses": udp,
        "external_listeners": external
    }

    # Load existing history or start fresh
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            history = json.load(file)

    history.append(record)

    with open(HISTORY_FILE, "w") as file:
        json.dump(history, file, indent=2)


def view_history():
    if not os.path.exists(HISTORY_FILE):
        print("No history files found!!!")
        return

    history = []
    with open(HISTORY_FILE, "r") as file:
        history = json.load(file)

    if not history:
        print("History is empty")
        return

    for report in history:
        print("=" * 40)
        print(f"  Report ID: {report['report_id']}  |  {report['timestamp']}")
        print("=" * 40)

        # Processes
        print("\n[ Top Processes ]")
        print(f"  {'USER':<12} {'PID':<8} {'CPU%':<8} {'MEM%':<8} {'HEALTH':<10} COMMAND")
        print("  " + "-" * 70)
        i = 1
        while f"process_{i}_user" in report:
            print(f"  {report[f'process_{i}_user']:<12} {report[f'process_{i}_pid']:<8} {report[f'process_{i}_cpu']:<8} {report[f'process_{i}_mem']:<8} {report[f'process_{i}_health']:<10} {report[f'process_{i}_command']}")
            i += 1

        # Memory
        print("\n[ Memory ]")
        print(f"  RAM  | Total: {report['ram_total']}Gi | Used: {report['ram_used']}Gi | Free: {report['ram_free']}Gi | Health: {report['ram_health']}")
        print(f"  Swap | Total: {report['swap_total']}Gi | Used: {report['swap_used']}Gi | Free: {report['swap_free']}Gi | Health: {report['swap_health']}")

        # Storage
        print("\n[ Storage ]")
        print(f"  Filesystem: {report['disk_filesystem']}")
        print(f"  Total: {report['disk_total']}G | Used: {report['disk_used']}G | Available: {report['disk_available']}G | Use%: {report['disk_use_percent']}% | Health: {report['disk_health']}")

        # CPU
        print("\n[ CPU ]")
        print(f"  Load Average  | 1min: {report['load_avg_1min']} | 5min: {report['load_avg_5min']} | 15min: {report['load_avg_15min']} | Health: {report['load_avg_health']}")
        print(f"  CPU Idle      | {report['cpu_idle']}% | Health: {report['cpu_idle_health']}")
        print(f"  CPU System    | {report['cpu_system']}% | Health: {report['cpu_system_health']}")
        print(f"  Running Tasks | {report['tasks_running']} | Health: {report['tasks_running_health']}")
        print(f"  Zombie Tasks  | {report['tasks_zombie']} | Health: {report['tasks_zombie_health']}")

        # Network
        print("\n[ Network ]")
        print(f"  TCP Listeners: {report['tcp_addresses'] if report['tcp_addresses'] else 'None'}")
        print(f"  UDP Listeners: {report['udp_addresses'] if report['udp_addresses'] else 'None'}")
        print(f"  External Exposure: {report['external_listeners'] if report['external_listeners'] else 'None detected'} | Health: {report['network_health']}")

        print()
