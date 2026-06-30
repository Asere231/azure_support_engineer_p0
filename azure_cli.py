import subprocess
import os
import sys
# from dotenv import load_dotenv

# load_dotenv()

# SP_CLIENT_ID = os.getenv("SP_CLIENT_ID") # appId
# SP_CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET") # password
# SP_TENANT_ID = os.getenv("SP_TENANT_ID") # tenant


rg_name = ""
vm_name = ""

# def az_sp_login():
#     env = os.environ.copy()
#     env["AZURE_CONFIG_DIR"] = "/home/bryan/.azure"
#     env["HOME"] = "/home/bryan"
#     result = subprocess.run(
#         ["/opt/az/bin/python3", "-Im", "azure.cli", "login",
#          "--service-principal",
#          "--username", SP_CLIENT_ID,
#          "--password", SP_CLIENT_SECRET,
#          "--tenant", SP_TENANT_ID],
#         capture_output=True,
#         text=True,
#         env=env
#     )
#     if result.returncode != 0:
#         print(f"SP login failed: {result.stderr}")
#         sys.exit(1)
#     print("Authenticated via service principal")

def run_az_command(command):
    """Utility function to safely execute an Azure CLI command array"""
    if command[0] == "az":
        command = ["/opt/az/bin/python3", "-Im", "azure.cli"] + command[1:]

    print(f"Executing command: {' '.join(command)}")
    try:
        env = os.environ.copy()
        env["AZURE_CONFIG_DIR"] = "/home/bryan/.azure"
        env["HOME"] = "/home/bryan"
        result = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
        if result.stdout:
            print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] command line failed to execute with return code; {e.returncode}", file=sys.stderr)
        print(f"\nMore Details: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def create_vm_and_deploy():
    global rg_name, vm_name
    # az_sp_login()
    print("=== Azure SRE Docker Compose Automated Deployment Pipeline using Python ===")

    rg_name = input("Enter Resource Group [rg-compute-prod-01]: ").strip() or "rg-compute-prod-01"
    vm_name = input("Enter VM Name [vm-appserver-prod-01]: ").strip() or "vm-appserver-prod-01"
    location = input("Enter Region [koreasouth]: ").strip() or "koreasouth"
    port = "8081"

    print(f"\nConfiguration: ")
    print(f"Resource Group: {rg_name}")
    print(f"VM Name: {vm_name}")
    print(f"Location: {location}")
    print(f"Port: {port}")

    print("======= Create Resource Group =======")
    create_rg_command = ["az", "group", "create", "--name", rg_name, "--location", location, "--output", "table"]
    run_az_command(create_rg_command)

    print("======== Create VM ========")
    check_vm_command = ["az", "vm", "list", "-g", rg_name, "--query", f"[?name=='{vm_name}'].name", "-o", "tsv"]
    checked_vm = run_az_command(check_vm_command)

    if not checked_vm:
        print(f"VM {vm_name} Not found. Provisioning now...")
        create_vm_command = [
            "az", "vm", "create", 
            "--resource-group", rg_name,
            "--name", vm_name,
            "--image", "Ubuntu2204",
            "--size", "Standard_B2ats_v2",
            "--storage-sku", "Standard_LRS",
            "--boot-diagnostics-storage", "",
            "--admin-username", "azureuser",
            "--generate-ssh-keys",
            "--location", location,
            "--output", "table"
        ]
        run_az_command(create_vm_command)
    else:
        print(f"VM {vm_name} already exists")

    print("======= Setting Auto-Shutdown =======")
    auto_shutdown_command = [
        "az", "vm", "auto-shutdown",
        "--resource-group", rg_name,
        "--name", vm_name,
        "--time", "1800"
    ]
    run_az_command(auto_shutdown_command)
    
    print("====== Opening Port 8081 Inbound =======")
    create_nsg_command = [
        "az", "network", "nsg", "rule", "create",
        "--resource-group", rg_name,
        "--nsg-name", f"{vm_name}NSG",
        "--name", "Allow_8081_Inbound",
        "--priority", "1010",
        "--destination-port-ranges", port,
        "--direction", "Inbound",
        "--access", "Allow",
        "--protocol", "Tcp",
        "--description", "Allow FastAPI web traffic on port 8081",
        "--output", "table"
    ]
    run_az_command(create_nsg_command)

    print("===== Reading Script from File ======")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_script_path = os.path.join(script_dir, "bootstrap_docker_compose.sh")

    if not os.path.exists(source_script_path):
        print(f"Error, source script file not found at {source_script_path}", file=sys.stderr)
        sys.exit(1)
    print(f"Reading file at {source_script_path}")

    print("======= Invoking Azure VM Run-Command ========")
    run_cmd = [
        "az", "vm", "run-command", "invoke",
        "--command-id", "RunShellScript", 
        "--resource-group", rg_name,
        "--name", vm_name,
        "--scripts", f"@{source_script_path}",
        "--query", "value[0].message",
        "--output", "table"
    ]
    run_az_command(run_cmd)

    print("======= Fetching VM Public IP Endpoint =======")
    get_ip_cmd = [
        "az", "vm", "list-ip-addresses",
        "-g", rg_name,
        "-n", vm_name,
        "--query", "[0].virtualMachine.network.publicIpAddresses[0].ipAddress",
        "-o", "tsv"
    ]
    vm_ip = run_az_command(get_ip_cmd).strip().replace("\r", "")
    print(f"Deployment Complete: API Endpoint - http://{vm_ip}:{port}")

def run_teardown():
    # az_sp_login()
    print(f"\n=== Running VM '{vm_name}' Teardown ===")
    print("Temporarily stopping the VM and suspend compute billing (deallocate VM):")
    stop_vm_command = ["az", "vm", "deallocate", "--name", vm_name, "--resource-group", rg_name, "--no-wait"]
    run_az_command(stop_vm_command)

    print("\nPermanently deleting the VM, disk, networks, and the resource group:")
    delete_rg_command = ["az", "group", "delete", "--name", rg_name, "--no-wait", "--yes"]
    run_az_command(delete_rg_command)