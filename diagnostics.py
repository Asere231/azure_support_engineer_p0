import subprocess
import re
import history

"""
ps -> current processes running
free -> memory capacity
df -> storage usage
top -> cpu/memory usage
ss -> shows ports that are listening and the processes
"""


def run_local_diagnostic():
    # one metrics needed for cpu health, then, display top 5 based on cpu usage
    current_processes = get_current_processes()

    current_memory_usage = get_memory_usage()
    current_storage_usage = get_storage_usage()
    current_top_snapshot = get_top_snapshot()

    # No metrics needed, display udp, tcp ports and external listening if needed
    current_networking_snapshot = get_networking_snapshot()

    diagnostic = diagnose(current_processes, current_memory_usage, current_storage_usage, current_top_snapshot, current_networking_snapshot)

    print_summary(diagnostic)
    print_detailed(current_processes, current_memory_usage, current_storage_usage, current_top_snapshot, current_networking_snapshot)

    history.save_report(diagnostic, current_processes, current_memory_usage, current_storage_usage, current_top_snapshot, current_networking_snapshot)
    

def get_current_processes():
    # Get top 5 processes running by CPU usage
    # USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
    # ['bryan', '358548', '3.8', '3.9', '10315056', '307456', 'pts/5', 'Sl+', '10:20', '0:55', 
    # '/home/bryan/.vscode-server/bin/fcf604774b9f2674b473065736ee75077e256353/node', '--dns-result-order=ipv4first', 
    # '/home/bryan/.vscode-server/bin/fcf604774b9f2674b473065736ee75077e256353/out/bootstrap-fork', '--type=extensionHost', 
    # '--transformURIs', '--useHostProxy=true']
    current_processes = subprocess.run(["ps", "aux", "--sort=-%cpu"], capture_output=True, text=True)
    processes_lines = current_processes.stdout.splitlines()
    processes_formatted = []
    for line in processes_lines[1:7]:
        columns = line.split()
        user = columns[0]
        pid = int(columns[1])
        cpu_percentage = float(columns[2])
        health = ""
        if cpu_percentage >= 80.0:
            health = "Critical"
        elif cpu_percentage < 80.0 and cpu_percentage > 50.0:
            health = "Watch"
        else:
            health = "Healthy"
        memory_percentage = float(columns[3])
        process_running = columns[10]
        process = {
            "user": user,
            "pid": pid,
            "cpu_percentage": cpu_percentage,
            "memory_percentage": memory_percentage,
            "process_running": process_running,
            "health": health
        }
        processes_formatted.append(process)

    return processes_formatted

def get_memory_usage():
    #  Get memory usage
    #                 total        used        free      shared  buff/cache   available
    # Mem:           7.5Gi       3.3Gi       3.9Gi       5.1Mi       528Mi       4.2Gi
    # Swap:          2.0Gi          0B       2.0Gi
    current_memory_usage = subprocess.run(["free", "-h"], capture_output=True, text=True)
    memory_usage_lines = current_memory_usage.stdout.splitlines()
    ram_columns = memory_usage_lines[1].split()
    ram_total_memory = float(re.sub("[A-Za-z]", "", ram_columns[1]))
    ram_used_memory = float(re.sub("[A-Za-z]", "", ram_columns[2]))
    ram_free_memory = float(re.sub("[A-Za-z]", "", ram_columns[3]))
    swap_columns = memory_usage_lines[2].split()
    swap_total_memory = float(re.sub("[A-Za-z]", "", swap_columns[1]))
    swap_used_memory = float(re.sub("[A-Za-z]", "", swap_columns[2]))
    swap_free_memory = float(re.sub("[A-Za-z]", "", swap_columns[3]))
    memory_usage = {
        "RAM": {
            "ram_total_memory": ram_total_memory,
            "ram_used_memory": ram_used_memory,
            "ram_free_memory": ram_free_memory
        },
        "Swap": {
            "swap_total_memory": swap_total_memory,
            "swap_used_memory": swap_used_memory,
            "swap_free_memory": swap_free_memory
        }
    }

    return memory_usage

def get_storage_usage():
    # Get Storage usage
    # Filesystem      Size  Used Avail Use% Mounted on
    # /dev/sdf       1007G  3.1G  953G   1% /
    current_disk_usage = subprocess.run(["df", "-h"], capture_output=True, text=True)
    disk_usage_lines = current_disk_usage.stdout.splitlines()
    
    disk_usage_column = None
    for line in disk_usage_lines:
        if line.startswith("/dev/"):
            disk_usage_column = line.split()
            break

    if disk_usage_column is None:
        return {
            "filesystem_disk": "unknown",
            "total_disk": 0.0,
            "used_disk": 0.0,
            "available_disk": 0.0,
            "use_percentage_disk": 0.0
        }

    filesystem_disk = disk_usage_column[0]
    total_disk = float(re.sub("[A-Za-z]", "",disk_usage_column[1]))
    used_disk = float(re.sub("[A-Za-z]", "", disk_usage_column[2]))
    available_disk = float(re.sub("[A-Za-z]", "", disk_usage_column[3]))
    use_percentage_disk = float(disk_usage_column[4].replace("%", ""))
    disk_usage = {
        "filesystem_disk": filesystem_disk,
        "total_disk": total_disk,
        "used_disk": used_disk,
        "available_disk": available_disk,
        "use_percentage_disk": use_percentage_disk
    }

    return disk_usage

def get_top_snapshot():
    # Get CPU/memory usage
    #      top -b -n 1 | head -n 12
    # top - 11:43:40 up 1 day,  2:16,  2 users,  load average: 0.05, 0.18, 0.13
    # Tasks: 100 total,   1 running,  99 sleeping,   0 stopped,   0 zombie
    # %Cpu(s):  1.2 us,  4.7 sy,  0.0 ni, 92.9 id,  0.0 wa,  0.0 hi,  1.2 si,  0.0 st 
    # MiB Mem :   7637.7 total,   3433.1 free,   3883.6 used,    516.7 buff/cache     
    # MiB Swap:   2048.0 total,   2048.0 free,      0.0 used.   3754.0 avail Mem 
    current_top_snapshot = subprocess.run(["top", "-b", "-n", "1"], capture_output=True, text=True)
    top_snapshot_lines = current_top_snapshot.stdout.splitlines()

    # ['top', '-', '12:04:32', 'up', '1', 'day,', '2:37,', '2', 'users,', 'load', 'average:', '0.04,', '0.04,', '0.06']
    load_average_columns = top_snapshot_lines[0].split()
    one_minute_load_average = float(load_average_columns[11].replace(",", ""))
    five_minute_load_average = float(load_average_columns[12].replace(",", ""))
    fifteen_minute_load_average = float(load_average_columns[13].replace(",", ""))

    # ['Tasks:', '100', 'total,', '1', 'running,', '99', 'sleeping,', '0', 'stopped,', '0', 'zombie']
    tasks_columns = top_snapshot_lines[1].split()
    task_running = int(tasks_columns[3])
    task_zombie = int(tasks_columns[9])

    # ['%Cpu(s):', '0.6', 'us,', '0.0', 'sy,', '0.0', 'ni,', '99.4', 'id,', '0.0', 'wa,', '0.0', 'hi,', '0.0', 'si,', '0.0', 'st']
    cpu_columns = top_snapshot_lines[2].split()
    cpu_idle_index = cpu_columns.index("id,") - 1
    cpu_idle = float(re.sub("[^0-9.]", "", cpu_columns[cpu_idle_index]))

    cpu_system_index = cpu_columns.index("sy,") - 1
    cpu_system = float(re.sub("[^0-9.]", "", cpu_columns[cpu_system_index]))

    top_snapshot = {
        "Load Average": {
            "one_minute_load_average": one_minute_load_average, 
            "five_minute_load_average": five_minute_load_average,
            "fifteen_minute_load_average": fifteen_minute_load_average
        },
        "Tasks": {
            "task_running": task_running,
            "task_zombie": task_zombie
        },
        "CPU%": {
            "cpu_system": cpu_system,
            "cpu_idle": cpu_idle
        }
    }

    return top_snapshot

def get_networking_snapshot():
    # Get ports that are listening
    #     ss -tuln
    # Netid           State            Recv-Q           Send-Q                      Local Address:Port                      Peer Address:Port          
    # udp             UNCONN           0                0                              127.0.0.54:53                             0.0.0.0:*             
    # udp             UNCONN           0                0                           127.0.0.53%lo:53                             0.0.0.0:*             
    # udp             UNCONN           0                0                          10.255.255.254:53                             0.0.0.0:*             
    # udp             UNCONN           0                0                               127.0.0.1:323                            0.0.0.0:*             
    # udp             UNCONN           0                0                               127.0.0.1:323                            0.0.0.0:*             
    # udp             UNCONN           0                0                                   [::1]:323                               [::]:*             
    # udp             UNCONN           0                0                                   [::1]:323                               [::]:*             
    # tcp             LISTEN           0                4096                           127.0.0.54:53                             0.0.0.0:*             
    # tcp             LISTEN           0                4096                        127.0.0.53%lo:53                             0.0.0.0:*             
    # tcp             LISTEN           0                511                             127.0.0.1:53918                          0.0.0.0:*             
    # tcp             LISTEN           0                511                             127.0.0.1:55140                          0.0.0.0:*             
    # tcp             LISTEN           0                511                             127.0.0.1:38565                          0.0.0.0:*             
    # tcp             LISTEN           0                1000                       10.255.255.254:53                             0.0.0.0:* 
    current_networking = subprocess.run(["ss", "-tuln"], capture_output=True, text=True)
    current_networking_lines = current_networking.stdout.splitlines()

    # Get all udp, tcp ports and addresses
    udp_addresses = set()
    tcp_addresses = set()
    for line in current_networking_lines[1:]:
        columns = line.split()
        if len(columns) < 5:
            continue
        if columns[0] == "udp":
            address = columns[4]
            udp_addresses.add(address)
        elif columns[0] == "tcp":
            address = columns[4]
            tcp_addresses.add(address)

    # Get all external addresses
    listening_external = set()
    for line in current_networking_lines[1:]:
        columns = line.split()
        if len(columns) < 5:
            continue
        local_address = columns[4]
        if local_address.startswith("0.0.0.0") or local_address.startswith(":::"):
            listening_external.add(local_address)

    networking = {
        "UDP Addresses": udp_addresses,
        "TCP Addresses": tcp_addresses,
        "Listening on external interface": listening_external
    }

    return networking


def diagnose(current_processes, current_memory_usage, current_storage_usage, current_top_snapshot, current_networking_snapshot):    
    # Diagnose processes
    critical_processes = []
    watch_processes = []
    healthy_processes = []
    for process in current_processes:
        if process["health"] == "Critical":
            critical_processes.append(process)
        elif process["health"] == "Watch":
            watch_processes.append(process)
        else:
            healthy_processes.append(process)


    # Diagnose RAM memory
    ram_memory_health = ""
    ram_used_memory = current_memory_usage["RAM"]["ram_used_memory"]
    ram_total_memory = current_memory_usage["RAM"]["ram_total_memory"]
    ram_percentage_memory = (ram_used_memory / ram_total_memory) * 100
    if ram_percentage_memory <= 60.0:
        ram_memory_health = "Healthy"
    elif ram_percentage_memory > 60.0 and ram_percentage_memory < 85.0:
        ram_memory_health = "Watch"
    else:
        ram_memory_health = "Critical"


    # Diagnose SWAP memory
    swap_memory_health = ""
    swap_used_memory = current_memory_usage["Swap"]["swap_used_memory"]
    swap_total_memory = current_memory_usage["Swap"]["swap_total_memory"]
    if swap_total_memory == 0:
        swap_memory_health = "Healthy"
    else:
        swap_percentage_memory = (swap_used_memory / swap_total_memory) * 100
        if swap_percentage_memory <= 60.0:
            swap_memory_health = "Healthy"
        elif swap_percentage_memory > 60.0 and swap_percentage_memory < 85.0:
            swap_memory_health = "Watch"
        else:
            swap_memory_health = "Critical"


    # Diagnose Disk storage
    disk_health = ""
    use_percentage_disk = current_storage_usage["use_percentage_disk"]
    if use_percentage_disk <= 70.0:
        disk_health = "Healthy"
    elif use_percentage_disk > 70 and use_percentage_disk < 90:
        disk_health = "Watch"
    else:
        disk_health = "Critical"


    # Diagnose Top snapshot
    load_average_health = ""
    one_minute_load_average = current_top_snapshot["Load Average"]["one_minute_load_average"]
    if one_minute_load_average <= 0.7:
        load_average_health = "Healthy"
    elif one_minute_load_average > 0.7 and one_minute_load_average < 1.0:
        load_average_health = "Watch"
    else:
        load_average_health = "Critical"

    cpu_idle_health = ""
    cpu_idle = current_top_snapshot["CPU%"]["cpu_idle"]
    if cpu_idle >= 80.0:
        cpu_idle_health = "Healthy"
    elif cpu_idle < 80.0 and cpu_idle > 50.0:
        cpu_idle_health = "Watch"
    else:
        cpu_idle_health = "Critical"

    cpu_system_health = ""
    cpu_system = current_top_snapshot["CPU%"]["cpu_system"]
    if cpu_system <= 10.0:
        cpu_system_health = "Healthy"
    elif cpu_system > 10.0 and cpu_system < 20.0:
        cpu_system_health = "Watch"
    else:
        cpu_system_health = "Critical"
    
    running_tasks_health = ""
    task_running = current_top_snapshot["Tasks"]["task_running"]
    if task_running == 1 or task_running == 2:
        running_tasks_health = "Healthy"
    elif task_running >= 3 and task_running <= 5:
        running_tasks_health = "Watch"
    else:
        running_tasks_health = "Critical"

    zombie_tasks_health = ""
    task_zombie = current_top_snapshot["Tasks"]["task_zombie"]
    if task_zombie == 0:
        zombie_tasks_health = "Healthy"
    elif task_zombie == 1 or task_zombie == 2:
        zombie_tasks_health = "Watch"
    else:
        zombie_tasks_health = "Critical"


    # Diagnose network
    network_health = ""
    listening_external = current_networking_snapshot["Listening on external interface"]
    if len(listening_external) > 0:
        network_health = "Critical"
    else:
        network_health = "Healthy"

    return {
        "Processes": {
            "healthy_processes": healthy_processes,
            "critical_processes": critical_processes,
            "watch_processes": watch_processes
        },
        "Memory": {
            "ram_memory_health": ram_memory_health,
            "swap_memory_health": swap_memory_health
        },
        "Storage": {
            "disk_health": disk_health
        },
        "CPU": {
            "load_average_health": load_average_health,
            "cpu_idle_health": cpu_idle_health,
            "cpu_system_health": cpu_system_health,
            "running_tasks_health": running_tasks_health,
            "zombie_tasks_health": zombie_tasks_health
        },
        "Network": {
            "network_health": network_health
        }
    }

def print_summary(diagnostic):
    print("=" * 40)
    print("       SYSTEM HEALTH SUMMARY")
    print("=" * 40)

    # Processes
    print("\n[ Processes ]")
    critical = diagnostic["Processes"]["critical_processes"]
    watch = diagnostic["Processes"]["watch_processes"]
    if len(critical) > 0:
        print(f"  Status: Critical — {len(critical)} process(es) consuming high CPU")
    elif len(watch) > 0:
        print(f"  Status: Watch — {len(watch)} process(es) consuming moderate CPU")
    else:
        print("  Status: Healthy")

    # Memory
    print("\n[ Memory ]")
    print(f"  RAM:  {diagnostic['Memory']['ram_memory_health']}")
    print(f"  Swap: {diagnostic['Memory']['swap_memory_health']}")

    # Storage
    print("\n[ Storage ]")
    print(f"  Disk: {diagnostic['Storage']['disk_health']}")

    # CPU
    print("\n[ CPU ]")
    print(f"  Load Average:  {diagnostic['CPU']['load_average_health']}")
    print(f"  CPU Idle:      {diagnostic['CPU']['cpu_idle_health']}")
    print(f"  CPU System:    {diagnostic['CPU']['cpu_system_health']}")
    print(f"  Running Tasks: {diagnostic['CPU']['running_tasks_health']}")
    print(f"  Zombie Tasks:  {diagnostic['CPU']['zombie_tasks_health']}")

    # Network
    print("\n[ Network ]")
    print(f"  External Exposure: {diagnostic['Network']['network_health']}")

    print("\n" + "=" * 40)


def print_detailed(current_processes, current_memory_usage, current_storage_usage, current_top_snapshot, current_networking_snapshot):
    print("=" * 40)
    print("       DETAILED SYSTEM REPORT")
    print("=" * 40)

    # Processes
    print("\n[ Top Processes by CPU Usage ]")
    print(f"  {'USER':<12} {'PID':<8} {'CPU%':<8} {'MEM%':<8} {'HEALTH':<10} COMMAND")
    print("  " + "-" * 70)
    for process in current_processes:
        print(f"  {process['user']:<12} {process['pid']:<8} {process['cpu_percentage']:<8} {process['memory_percentage']:<8} {process['health']:<10} {process['process_running']}")

    # Memory
    print("\n[ Memory Usage ]")
    ram = current_memory_usage["RAM"]
    swap = current_memory_usage["Swap"]
    print(f"  RAM  | Total: {ram['ram_total_memory']}Gi | Used: {ram['ram_used_memory']}Gi | Free: {ram['ram_free_memory']}Gi")
    print(f"  Swap | Total: {swap['swap_total_memory']}Gi | Used: {swap['swap_used_memory']}Gi | Free: {swap['swap_free_memory']}Gi")

    # Storage
    print("\n[ Storage Usage ]")
    print(f"  Filesystem: {current_storage_usage['filesystem_disk']}")
    print(f"  Total: {current_storage_usage['total_disk']}G | Used: {current_storage_usage['used_disk']}G | Available: {current_storage_usage['available_disk']}G | Use%: {current_storage_usage['use_percentage_disk']}%")

    # Top snapshot
    print("\n[ CPU Snapshot ]")
    load = current_top_snapshot["Load Average"]
    tasks = current_top_snapshot["Tasks"]
    cpu = current_top_snapshot["CPU%"]
    print(f"  Load Average  | 1min: {load['one_minute_load_average']} | 5min: {load['five_minute_load_average']} | 15min: {load['fifteen_minute_load_average']}")
    print(f"  Tasks         | Running: {tasks['task_running']} | Zombie: {tasks['task_zombie']}")
    print(f"  CPU           | Idle: {cpu['cpu_idle']}% | System: {cpu['cpu_system']}%")

    # Networking
    print("\n[ Network ]")
    tcp = sorted(current_networking_snapshot["TCP Addresses"])
    udp = sorted(current_networking_snapshot["UDP Addresses"])
    external = current_networking_snapshot["Listening on external interface"]
    print(f"  TCP Listeners: {', '.join(tcp) if tcp else 'None'}")
    print(f"  UDP Listeners: {', '.join(udp) if udp else 'None'}")
    print(f"  External Exposure: {'⚠ ' + ', '.join(external) if external else 'None detected'}")

    print("\n" + "=" * 40)
