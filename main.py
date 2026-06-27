import history
import diagnostics
import azure_cli



def interactive_cli():
    while True:
        print("=" * 30)
        print(" " * 5 + "SRE Diagnostic Tool")
        print("=" * 30)
        
        print("1. Run Local Diagnostics")
        print("2. Deploy Azure VM")
        print("3. Run Teardown")
        print("4. View Performance History")
        print("5. Exit")
        selection = input("Select an option: ")
        match selection:
            case "1": 
                diagnostics.run_local_diagnostic()
            case "2":
                azure_cli.deploy_vm()
            case "3":
                azure_cli.run_teardown()
            case "4":
                history.view_history()
            case "5":
                exit()
            case _:
                print("Please select from 1-5")


if __name__ == "__main__":
    interactive_cli()