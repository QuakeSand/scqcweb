# -*- coding: utf-8 -*-
"""
Created on Wed Jun  4 15:50:07 2025

@author: nnovoa
"""

import os
import psutil
import sqlite3

db_path = os.path.join('/opt','scqcweb', 'listeners', 'system_monitor.db')

# Step 1: Set up SQLite database
def setup_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cpu_percent REAL,
            memory_percent REAL,
            root_disk_usage REAL,
            var_disk_usage REAL,
            data_disk_usage REAL,
            opt_disk_usage REAL,
            home_disk_usage REAL,
            load_avg_1min REAL,
            load_avg_5min REAl,
            load_avg_15min REAL
        )
    """)
    conn.commit()
    return conn

# Step 2: Collect system stats using psutil
def collect_system_stats():
    # Get CPU usage percentage
    cpu_percent = psutil.cpu_percent(interval=1)
    #print(f"CPU Usage: {cpu_percent}%")

    # Get CPU core count
    #cpu_cores = psutil.cpu_count(logical=True)
    #print(f"Logical CPU Cores: {cpu_cores}")

    # Get virtual memory details
    memory_percent = psutil.virtual_memory().percent
    #print(f"Total Memory: {memory.total / (1024 ** 3):.2f} GB")
    #print(f"Available Memory: {memory.available / (1024 ** 3):.2f} GB")
    #print(f"Memory Usage: {memory_percent}%")

    # Get disk usage for the root directory and other partitions
    root_disk_usage = psutil.disk_usage('/').percent
    var_disk_usage = psutil.disk_usage('/var').percent
    data_disk_usage = psutil.disk_usage('/data').percent
    opt_disk_usage = psutil.disk_usage('/opt').percent
    home_disk_usage = psutil.disk_usage('/home').percent
    #print(f"Total Disk Space: {disk_usage.total / (1024 ** 3):.2f} GB")
    #print(f"Used Disk Space: {disk_usage.used / (1024 ** 3):.2f} GB")
    #print(f"Free Disk Space: {disk_usage.free / (1024 ** 3):.2f} GB")
    #print(f"Disk Usage: {root_disk_usage}%")

    #1, 5, and 15 minutes
    load_avg = psutil.getloadavg()
    #print(f"Load Average (1 min): {load_avg[0]}")
    #print(f"Load Average (5 min): {load_avg[1]}")
    #print(f"Load Average (15 min): {load_avg[2]}")
    return cpu_percent, memory_percent, root_disk_usage, var_disk_usage, data_disk_usage, opt_disk_usage, home_disk_usage, load_avg[0], load_avg[1], load_avg[2]

# Step 3: Insert data into the database
def insert_stats(conn, stats):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO system_stats (timestamp, cpu_percent, memory_percent, root_disk_usage, var_disk_usage, data_disk_usage, opt_disk_usage, home_disk_usage, load_avg_1min, load_avg_5min, load_avg_15min)
        VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, stats)
    conn.commit()

# Step 4: Main loop to monitor and log stats
def main():
    conn = setup_database()
    try:
        stats = collect_system_stats()
        insert_stats(conn, stats)
        #print(f"Logged stats: {stats}")
    except KeyboardInterrupt:
        print("Monitoring stopped.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
