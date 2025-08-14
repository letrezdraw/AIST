# start.py - AIST Master Launcher
import subprocess
import sys
import os
import atexit
import time
import platform

# List to keep track of all child processes
child_processes = []

def cleanup_processes():
    """
    This function is registered to run at script exit.
    It ensures all child processes are terminated.
    """
    print("Shutting down all AIST components...")
    for p in child_processes:
        if p.poll() is None:  # Check if the process is still running
            print(f"Terminating process {p.pid}...")
            p.terminate()
            p.wait() # Wait for the process to terminate
    print("All components shut down.")

# Register the cleanup function to be called on exit
atexit.register(cleanup_processes)

def main():
    """
    Launches all AIST components (backend, frontend, GUI) as separate processes.
    """
    print("--- AIST Master Launcher ---")

    # Determine the correct python executable based on the OS and venv
    if platform.system() == "Windows":
        python_executable = os.path.join(sys.prefix, 'Scripts', 'python.exe')
    else:
        python_executable = os.path.join(sys.prefix, 'bin', 'python')

    if not os.path.exists(python_executable):
        print(f"Error: Could not find Python executable at {python_executable}")
        print("Please ensure you are running this script from within an activated virtual environment.")
        sys.exit(1)

    components = {
        "Backend": "run_backend.py",
        "Frontend": "main.py",
        "GUI": "gui.py"
    }

    # On Windows, use CREATE_NEW_CONSOLE to give each component its own window.
    creation_flags = subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0

    for name, script in components.items():
        if not os.path.exists(script):
            print(f"Warning: Script for component '{name}' not found at '{script}'. Skipping.")
            continue
        
        print(f"Launching {name}...")
        process = subprocess.Popen([python_executable, script], creationflags=creation_flags, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        child_processes.append(process)
        print(f"  -> {name} launched with PID: {process.pid}")

    print("\nAll AIST components have been launched in separate windows.")
    print("To shut down the entire application, close this launcher window or press Ctrl+C.")

    # Create a thread to read the output from the child processes
    def read_output(process, name):
        for line in iter(process.stdout.readline, ''):
            print(f"[{name}] {line}", end='')
        for line in iter(process.stderr.readline, ''):
            print(f"[{name}-ERROR] {line}", end='')

    import threading
    for process in child_processes:
        name = [k for k, v in components.items() if v == process.args[1]][0]
        threading.Thread(target=read_output, args=(process, name), daemon=True).start()

    print("\nAll AIST components have been launched in separate windows.")
    print("To shut down the entire application, close this launcher window or press Ctrl+C.")

    try:
        # Keep the main launcher script alive to manage child processes
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nLauncher received Ctrl+C. Initiating shutdown...")
        sys.exit(0)

if __name__ == "__main__":
    main()