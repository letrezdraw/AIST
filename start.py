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

    python_executable = sys.executable

    components = {
        "Backend": {"script": "run_backend.py"},
        "Frontend": {"script": "main.py"},
        "GUI": {"script": "gui.py"}
    }

    for name, info in components.items():
        script = info["script"]
        if not os.path.exists(script):
            print(f"Warning: Script for component '{name}' not found at '{script}'. Skipping.")
            continue
        
        print(f"Launching {name}...")
        
        executable = python_executable
        creation_flags = 0

        if platform.system() == "Windows":
            if name in ["Backend", "Frontend"]:
                creation_flags = subprocess.CREATE_NEW_CONSOLE
            elif name == "GUI":
                # Try to use pythonw.exe for the GUI to avoid a console window
                pythonw_path = python_executable.replace("python.exe", "pythonw.exe")
                if os.path.exists(pythonw_path):
                    executable = pythonw_path
                else:
                    print("Warning: pythonw.exe not found. GUI may open with a console window.")
        
        process = subprocess.Popen([executable, script], creationflags=creation_flags)
        child_processes.append(process)
        print(f"  -> {name} launched with PID: {process.pid}")

    print("\nAll AIST components have been launched.")
    print("To shut down the entire application, close this launcher window or press Ctrl+C.")

    try:
        # Keep the main launcher script alive to manage child processes
        while True:
            # Check if any process has terminated unexpectedly
            for p in child_processes:
                if p.poll() is not None:
                    print(f"\nProcess {p.pid} has terminated. Shutting down all components.")
                    sys.exit(1) # Exit the launcher, which will trigger the cleanup
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nLauncher received Ctrl+C. Initiating shutdown...")
        sys.exit(0)

if __name__ == "__main__":
    main()