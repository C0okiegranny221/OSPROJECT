import psutil
import csv

CSV_FILE = "process_metrics.csv"  # Output file

def get_process_metrics(pid):
    try:
        p = psutil.Process(pid)
        with p.oneshot():  # Optimize fetching multiple attributes
            cpu_times = p.cpu_times()
            mem_info = p.memory_info()
            ctx_switches = p.num_ctx_switches()

            # Handle missing I/O counters safely
            read_bytes = write_bytes = 0
            if hasattr(p, "io_counters"):
                try:
                    io_counters = p.io_counters()
                    read_bytes = io_counters.read_bytes
                    write_bytes = io_counters.write_bytes
                except psutil.AccessDenied:
                    pass  # Ignore permission errors

            return {
                "PID": pid,
                "CPU_Percent": p.cpu_percent(interval=0.1),
                "CPU_User_Time": cpu_times.user,
                "CPU_System_Time": cpu_times.system,
                "Memory_MB": mem_info.rss / (1024 * 1024),  # Convert to MB
                "IO_Read_MB": read_bytes / (1024 * 1024),  # Convert to MB
                "IO_Write_MB": write_bytes / (1024 * 1024),
                "Voluntary_Ctx_Switches": ctx_switches.voluntary,
                "Involuntary_Ctx_Switches": ctx_switches.involuntary
            }

    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
        return None  # Skip inaccessible processes

def save_to_csv(process_data):
    """Save the collected process data to a CSV file."""
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=process_data[0].keys())
        writer.writeheader()
        writer.writerows(process_data)

def main():
    process_list = []

    for proc in psutil.process_iter(attrs=['pid']):
        metrics = get_process_metrics(proc.info['pid'])
        if metrics:
            process_list.append(metrics)

    if process_list:
        save_to_csv(process_list)
        print(f"✅ Data saved to {CSV_FILE} successfully!")
    else:
        print("⚠ No process data collected.")

if __name__ == "__main__":
    main()

