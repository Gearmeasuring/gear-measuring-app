with open(r'e:\python\gear measuring software - 20251202\齿轮波纹度软件2_修改版.py.before_915_points20251127.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# Find the line with basic_info = GearBasicInfo(
start_line = 21610
end_line = start_line + 50

for i in range(start_line, min(end_line, len(lines))):
    print(f"{i+1}: {lines[i]}", end='')
