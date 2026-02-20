import json
import numpy as np

# 加载解析后的数据
with open('mka_parsed_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== MKA数据详细分析 ===")

# 1. 分析齿轮基本数据
print("\n1. 齿轮基本数据分析")
gear_data = data['gear_data']
print(f"总齿数: {gear_data.get('teeth', '未知')}")
print(f"模数: {gear_data.get('module', '未知')}")
print(f"螺旋角: {gear_data.get('helix_angle', '未知')}")
print(f"压力角: {gear_data.get('pressure_angle', '未知')}")
print(f"齿宽: {gear_data.get('width', '未知')}")
print(f"齿顶圆直径: {gear_data.get('tip_diameter', '未知')}")
print(f"齿根圆直径: {gear_data.get('root_diameter', '未知')}")

# 2. 分析齿形数据
print("\n2. 齿形数据分析")
profile_data = data['profile_data']
left_teeth = profile_data['left']
right_teeth = profile_data['right']

print(f"左侧齿形数据: {len(left_teeth)} 个齿")
print(f"右侧齿形数据: {len(right_teeth)} 个齿")

# 分析第一个左侧齿的数据
if left_teeth:
    first_tooth_num = next(iter(left_teeth))
    first_tooth_data = left_teeth[first_tooth_num]
    print(f"\n左侧第一个齿({first_tooth_num})数据分析:")
    print(f"数据点数: {len(first_tooth_data)}")
    print(f"数据范围: {min(first_tooth_data):.3f} ~ {max(first_tooth_data):.3f}")
    print(f"数据平均值: {np.mean(first_tooth_data):.3f}")
    print(f"数据标准差: {np.std(first_tooth_data):.3f}")
    print(f"非零数据点: {sum(1 for x in first_tooth_data if x != 0):d}")
    print(f"零值数据点: {sum(1 for x in first_tooth_data if x == 0):d}")

# 分析第一个右侧齿的数据
if right_teeth:
    first_tooth_num = next(iter(right_teeth))
    first_tooth_data = right_teeth[first_tooth_num]
    print(f"\n右侧第一个齿({first_tooth_num})数据分析:")
    print(f"数据点数: {len(first_tooth_data)}")
    print(f"数据范围: {min(first_tooth_data):.3f} ~ {max(first_tooth_data):.3f}")
    print(f"数据平均值: {np.mean(first_tooth_data):.3f}")
    print(f"数据标准差: {np.std(first_tooth_data):.3f}")
    print(f"非零数据点: {sum(1 for x in first_tooth_data if x != 0):d}")
    print(f"零值数据点: {sum(1 for x in first_tooth_data if x == 0):d}")

# 3. 分析齿向数据
print("\n3. 齿向数据分析")
flank_data = data['flank_data']
left_flank = flank_data['left']
right_flank = flank_data['right']

print(f"左侧齿向数据: {len(left_flank)} 个齿")
print(f"右侧齿向数据: {len(right_flank)} 个齿")

# 4. 分析齿距数据
print("\n4. 齿距数据分析")
pitch_data = data['pitch_data']
left_pitch = pitch_data['left']
right_pitch = pitch_data['right']

print(f"左侧齿距数据: {len(left_pitch)} 个齿")
print(f"右侧齿距数据: {len(right_pitch)} 个齿")

# 5. 分析拓扑数据
print("\n5. 拓扑数据分析")
topography_data = data['topography_data']
print(f"拓扑数据: {len(topography_data)} 个齿")

# 分析第一个齿的拓扑数据
if topography_data:
    first_tooth_num = next(iter(topography_data))
    first_tooth_topography = topography_data[first_tooth_num]
    print(f"\n第一个齿({first_tooth_num})拓扑数据分析:")
    print(f"左侧profiles数量: {len(first_tooth_topography.get('left', {}).get('profiles', {}))}")
    print(f"左侧flank_lines数量: {len(first_tooth_topography.get('left', {}).get('flank_lines', {}))}")
    print(f"右侧profiles数量: {len(first_tooth_topography.get('right', {}).get('profiles', {}))}")
    print(f"右侧flank_lines数量: {len(first_tooth_topography.get('right', {}).get('flank_lines', {}))}")

# 6. 数据完整性检查
print("\n6. 数据完整性检查")
print(f"齿轮基本数据字段数: {len(gear_data)}")
print(f"齿形数据完整度: {len(left_teeth) + len(right_teeth)}/{gear_data.get('teeth', 0) * 2:.0f} 个齿")
print(f"齿向数据完整度: {len(left_flank) + len(right_flank)}/{gear_data.get('teeth', 0) * 2:.0f} 个齿")
print(f"齿距数据完整度: {len(left_pitch) + len(right_pitch)}/{gear_data.get('teeth', 0) * 2:.0f} 个齿")
print(f"拓扑数据完整度: {len(topography_data)}/{gear_data.get('teeth', 0):.0f} 个齿")

# 7. 检查是否有足够的数据进行波纹度分析
print("\n7. 波纹度分析数据准备检查")
if left_teeth or right_teeth:
    print("✓ 齿形数据可用，可进行波纹度分析")
else:
    print("✗ 齿形数据不可用，无法进行波纹度分析")

# 检查数据质量
print("\n8. 数据质量检查")
if left_teeth:
    # 随机选择几个齿进行数据质量检查
    sample_teeth = list(left_teeth.keys())[:3]
    for tooth_num in sample_teeth:
        tooth_data = left_teeth[tooth_num]
        non_zero_ratio = sum(1 for x in tooth_data if x != 0) / len(tooth_data)
        print(f"左侧齿 {tooth_num}: 非零数据比例 = {non_zero_ratio:.2f}")

print("\n数据分析完成!")
