import subprocess

"""
ps -> current processes running
free -> memory capacity
df -> storage usage
top -> cpu/memory usage
ss -> shows ports that are listening and the processes
"""


def run_local_diagnostic():
    # no metrics needed, display top 5 based on cpu usage
    current_processes = get_current_processes()

    current_memory_usage = get_memory_usage()
    current_storage_usage = get_storage_usage()
    current_top_snapshot = get_top_snapshot()

    # No metrics needed, display udp, tcp ports and external listening if needed
    current_networking_snapshot = get_networking_snapshot()
    

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
        pid = columns[1]
        cpu_percentage = columns[2]
        memory_percentage = columns[3]
        process_running = columns[10]
        process = {
            "user": user,
            "pid": pid,
            "cpu_percentage": cpu_percentage,
            "memory_percentage": memory_percentage,
            "process_running": process_running
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
    ram_total_memory = ram_columns[1]
    ram_used_memory = ram_columns[2]
    ram_free_memory = ram_columns[3]
    swap_columns = memory_usage_lines[2].split()
    swap_total_memory = swap_columns[1]
    swap_used_memory = swap_columns[2]
    swap_free_memory = swap_columns[3]
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
    disk_usage_line = current_disk_usage.stdout.splitlines()
    disk_usage_column = disk_usage_line[1].split()
    filesystem_disk = disk_usage_column[0]
    total_disk = disk_usage_column[1]
    used_disk = disk_usage_column[2]
    available_disk = disk_usage_column[3]
    use_percentage_disk = disk_usage_column[4]
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
    one_minute_load_average = load_average_columns[11].replace(",", "")
    five_minute_load_average = load_average_columns[12].replace(",", "")
    fifteen_minute_load_average = load_average_columns[13].replace(",", "")

    # ['Tasks:', '100', 'total,', '1', 'running,', '99', 'sleeping,', '0', 'stopped,', '0', 'zombie']
    tasks_columns = top_snapshot_lines[1].split()
    task_running = tasks_columns[3]
    task_zombie = tasks_columns[9]

    # ['%Cpu(s):', '0.6', 'us,', '0.0', 'sy,', '0.0', 'ni,', '99.4', 'id,', '0.0', 'wa,', '0.0', 'hi,', '0.0', 'si,', '0.0', 'st']
    cpu_columns = top_snapshot_lines[2].split()
    cpu_system = cpu_columns[3]
    cpu_idle = cpu_columns[7]

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
