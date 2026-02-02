import time
import threading
import psutil
import os

def log_usage(interval=60):
    """Log RAM and CPU usage periodically."""
    process = psutil.Process(os.getpid())
    
    print(f"[MONITOR] Starting resource monitoring (Interval: {interval}s)")
    
    while True:
        try:
            # Memory usage
            mem_info = process.memory_info()
            ram_mb = mem_info.rss / 1024 / 1024  # Convert to MB
            
            # CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            
            print(f"[MONITOR] RAM: {ram_mb:.2f} MB | CPU: {cpu_percent}%")
            
            time.sleep(interval)
            
        except Exception as e:
            print(f"[MONITOR] Error: {e}")
            time.sleep(interval)

def start_monitoring(interval=60):
    """Start the monitoring thread."""
    t = threading.Thread(target=log_usage, args=(interval,), daemon=True)
    t.start()
