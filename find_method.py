
file_path = r"e:\python\gear measuring software - 20251202\齿轮波纹度软件2_修改版.py.before_915_points20251127.py"

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f):
        if "def init_report_tab" in line:
            print(f"Line {i+1}: {line.strip()}")
