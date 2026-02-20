from gear_analysis_refactored.utils.file_parser import parse_mka_file
import json
import numpy as np

# 解析两个MKA文件
file1 = '263751-018-WAV.mka'  # 已分析的文件
file2 = '004-xiaoxiao1.mka'   # 要对比的文件

print(f"=== MKA文件对比分析 ===")
print(f"文件1: {file1}")
print(f"文件2: {file2}")

# 解析两个文件
try:
    data1 = parse_mka_file(file1)
    data2 = parse_mka_file(file2)
    
    print("\n=== 齿轮基本数据对比 ===")
    gear1 = data1['gear_data']
    gear2 = data2['gear_data']
    
    # 对比关键参数
    key_params = ['teeth', 'module', 'helix_angle', 'pressure_angle', 'width', 
                  'tip_diameter', 'root_diameter']
    
    for param in key_params:
        val1 = gear1.get(param, '未知')
        val2 = gear2.get(param, '未知')
        status = "✓" if val1 == val2 else "✗"
        print(f"{status} {param}: {val1} vs {val2}")
    
    # 对比齿形数据
    print("\n=== 齿形数据对比 ===")
    profile1 = data1['profile_data']
    profile2 = data2['profile_data']
    
    left1 = profile1['left']
    left2 = profile2['left']
    right1 = profile1['right']
    right2 = profile2['right']
    
    print(f"左侧齿形数据: {len(left1)} vs {len(left2)} 个齿")
    print(f"右侧齿形数据: {len(right1)} vs {len(right2)} 个齿")
    
    # 对比第一个左侧齿的数据
    if left1 and left2:
        tooth1 = next(iter(left1))
        tooth2 = next(iter(left2))
        
        data1_points = left1[tooth1]
        data2_points = left2[tooth2]
        
        print(f"\n左侧第一个齿数据分析对比:")
        print(f"数据点数: {len(data1_points)} vs {len(data2_points)}")
        print(f"数据范围: {min(data1_points):.3f}~{max(data1_points):.3f} vs {min(data2_points):.3f}~{max(data2_points):.3f}")
        print(f"数据平均值: {np.mean(data1_points):.3f} vs {np.mean(data2_points):.3f}")
        print(f"数据标准差: {np.std(data1_points):.3f} vs {np.std(data2_points):.3f}")
    
    # 对比齿向数据
    print("\n=== 齿向数据对比 ===")
    flank1 = data1['flank_data']
    flank2 = data2['flank_data']
    
    print(f"左侧齿向数据: {len(flank1['left'])} vs {len(flank2['left'])} 个齿")
    print(f"右侧齿向数据: {len(flank1['right'])} vs {len(flank2['right'])} 个齿")
    
    # 对比齿距数据
    print("\n=== 齿距数据对比 ===")
    pitch1 = data1['pitch_data']
    pitch2 = data2['pitch_data']
    
    print(f"左侧齿距数据: {len(pitch1['left'])} vs {len(pitch2['left'])} 个齿")
    print(f"右侧齿距数据: {len(pitch1['right'])} vs {len(pitch2['right'])} 个齿")
    
    # 对比拓扑数据
    print("\n=== 拓扑数据对比 ===")
    topo1 = data1['topography_data']
    topo2 = data2['topography_data']
    
    print(f"拓扑数据: {len(topo1)} vs {len(topo2)} 个齿")
    
    # 数据质量对比
    print("\n=== 数据质量对比 ===")
    
    # 计算齿形数据的完整性
    total_teeth = max(gear1.get('teeth', 0), gear2.get('teeth', 0))
    profile_completeness1 = (len(left1) + len(right1)) / (total_teeth * 2) * 100
    profile_completeness2 = (len(left2) + len(right2)) / (total_teeth * 2) * 100
    
    print(f"齿形数据完整性: {profile_completeness1:.1f}% vs {profile_completeness2:.1f}%")
    
    # 计算非零数据比例
    if left1:
        tooth = next(iter(left1))
        data_points = left1[tooth]
        non_zero_ratio1 = sum(1 for x in data_points if x != 0) / len(data_points) * 100
    else:
        non_zero_ratio1 = 0
    
    if left2:
        tooth = next(iter(left2))
        data_points = left2[tooth]
        non_zero_ratio2 = sum(1 for x in data_points if x != 0) / len(data_points) * 100
    else:
        non_zero_ratio2 = 0
    
    print(f"非零数据比例: {non_zero_ratio1:.1f}% vs {non_zero_ratio2:.1f}%")
    
    print("\n=== 对比总结 ===")
    if gear1.get('teeth') == gear2.get('teeth') and gear1.get('module') == gear2.get('module'):
        print("✓ 两个文件包含相同齿轮的测量数据")
    else:
        print("✗ 两个文件包含不同齿轮的测量数据")
    
    if profile_completeness1 > 90 and profile_completeness2 > 90:
        print("✓ 两个文件都包含完整的测量数据")
    else:
        print("✗ 至少有一个文件数据不完整")
    
    # 保存对比结果
    with open('mka_compare_result.json', 'w', encoding='utf-8') as f:
        json.dump({
            'file1': file1,
            'file2': file2,
            'gear_data_compare': {
                'file1': gear1,
                'file2': gear2
            },
            'data_completeness': {
                'file1': {
                    'profile_left': len(left1),
                    'profile_right': len(right1),
                    'flank_left': len(flank1['left']),
                    'flank_right': len(flank1['right']),
                    'pitch_left': len(pitch1['left']),
                    'pitch_right': len(pitch1['right']),
                    'topography': len(topo1)
                },
                'file2': {
                    'profile_left': len(left2),
                    'profile_right': len(right2),
                    'flank_left': len(flank2['left']),
                    'flank_right': len(flank2['right']),
                    'pitch_left': len(pitch2['left']),
                    'pitch_right': len(pitch2['right']),
                    'topography': len(topo2)
                }
            }
        }, f, ensure_ascii=False, indent=2)
    
    print("\n对比结果已保存到 mka_compare_result.json")
    
except Exception as e:
    print(f"对比分析错误: {e}")
    import traceback
    traceback.print_exc()
