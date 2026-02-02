import time
import threading
import psutil
import os

from .logger import BotLogger

def log_usage(interval=60):
    """Log RAM and CPU usage periodically."""
    import gc
    process = psutil.Process(os.getpid())
    
    BotLogger.info(f"Monitor started (Interval: {interval}s)")
    
    while True:
        try:
            # Memory usage
            mem_info = process.memory_info()
            ram_mb = mem_info.rss / 1024 / 1024  # Convert to MB
            
            # CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            
            # Warning if approaching limit
            if ram_mb > 400:
                BotLogger.error(f"⚠️ HIGH MEMORY: {ram_mb:.0f}MB - Triggering GC")
                gc.collect()
            else:
                BotLogger.log(f"RAM: {ram_mb:.0f}MB | CPU: {cpu_percent}%")
            
            time.sleep(interval)
            
        except Exception as e:
            BotLogger.error(f"Monitor error: {e}")
            time.sleep(interval)

def start_monitoring(interval=60):
    """Start the monitoring thread."""
    t = threading.Thread(target=log_usage, args=(interval,), daemon=True)
    t.start()
