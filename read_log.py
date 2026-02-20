
import os

log_file = r"e:\python\gear measuring software - 20251202\gear_viewer.log"
try:
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        print("".join(lines[-200:]))
except Exception as e:
    print(f"Error reading log: {e}")
