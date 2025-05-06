import psutil
import platform
import json
import os
import pprint

def document_psutil_return_values():
    """Create reference documentation of psutil return values."""
    results = {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "psutil_version": psutil.__version__,
        "examples": {}
    }
    
    # Document basic Process attributes and methods
    try:
        # Use current process
        current_process = psutil.Process()
        process_data = {
            "pid": current_process.pid,
            "name": current_process.name(),
            "exe": current_process.exe(),
            "cmdline": current_process.cmdline(),
            "status": current_process.status(),
            "username": current_process.username(),
            "create_time": current_process.create_time(),
            "cpu_percent": current_process.cpu_percent(),
            "memory_percent": current_process.memory_percent(),
            "memory_info": str(current_process.memory_info()),
            "num_threads": current_process.num_threads(),
            "connections": str(current_process.connections())
        }
        
        # Try to add some methods that might raise AccessDenied
        try:
            process_data["cwd"] = current_process.cwd()
        except (psutil.AccessDenied, psutil.Error):
            process_data["cwd"] = "Access Denied"
            
        try:
            process_data["environ"] = str(current_process.environ())
        except (psutil.AccessDenied, psutil.Error):
            process_data["environ"] = "Access Denied"
        
        results["examples"]["current_process"] = process_data
        
        # Document a few other processes - get first 3 processes that aren't the current one
        other_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.pid != current_process.pid:
                other_processes.append(proc.pid)
                if len(other_processes) >= 3:
                    break
        
        for i, pid in enumerate(other_processes):
            try:
                proc = psutil.Process(pid)
                process_data = {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "exe": proc.exe(),
                    "status": proc.status()
                }
                results["examples"][f"other_process_{i+1}"] = process_data
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                results["examples"][f"other_process_{i+1}"] = f"Could not access process {pid}"
    
    except Exception as e:
        results["error"] = str(e)
    
    # Save results
    os.makedirs("test_data", exist_ok=True)
    file_path = f"test_data/psutil_reference_{platform.system().lower()}.json"
    with open(file_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Saved reference data to {file_path}")
    print("Sample data:")
    pprint.pprint(results["examples"].get("current_process", {}))
    
    return results

if __name__ == "__main__":
    document_psutil_return_values()