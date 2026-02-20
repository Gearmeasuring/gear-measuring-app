from gear_analysis_refactored.utils.file_parser import MKAFileParser, parse_mka_file
import json

# 解析MKA文件
file_path = '263751-018-WAV.mka'

print(f"开始解析MKA文件: {file_path}")

# 使用便捷函数解析文件
try:
    # 使用便捷函数解析整个文件
    parsed_data = parse_mka_file(file_path)
    
    # 提取齿轮基本数据
    gear_data = parsed_data.get('gear_data', {})
    print("\n=== 齿轮基本数据 ===")
    print(json.dumps(gear_data, ensure_ascii=False, indent=2))
    
    # 提取齿形数据
    profile_data = parsed_data.get('profile_data', {})
    print("\n=== 齿形数据 ===")
    print(f"左侧齿形数据: {len(profile_data.get('left', {}))} 个齿")
    print(f"右侧齿形数据: {len(profile_data.get('right', {}))} 个齿")
    
    # 提取齿向数据
    flank_data = parsed_data.get('flank_data', {})
    print("\n=== 齿向数据 ===")
    print(f"左侧齿向数据: {len(flank_data.get('left', {}))} 个齿")
    print(f"右侧齿向数据: {len(flank_data.get('right', {}))} 个齿")
    
    # 提取齿距数据
    pitch_data = parsed_data.get('pitch_data', {})
    print("\n=== 齿距数据 ===")
    print(f"左侧齿距数据: {len(pitch_data.get('left', {}))} 个齿")
    print(f"右侧齿距数据: {len(pitch_data.get('right', {}))} 个齿")
    
    # 提取拓扑数据
    topography_data = parsed_data.get('topography_data', {})
    print("\n=== 拓扑数据 ===")
    print(f"拓扑数据: {len(topography_data)} 个齿")
    
    # 验证数据完整性
    print("\n=== 数据验证 ===")
    print(f"齿轮数据字段数: {len(gear_data)}")
    print(f"总齿数: {gear_data.get('teeth', '未知')}")
    print(f"模数: {gear_data.get('module', '未知')}")
    
    # 检查齿形数据是否存在
    if not profile_data['left'] and not profile_data['right']:
        print("警告: 未找到齿形数据")
    else:
        # 显示第一个齿的数据长度
        if profile_data['left']:
            first_tooth = next(iter(profile_data['left']))
            print(f"左侧第一个齿({first_tooth})的数据点数: {len(profile_data['left'][first_tooth])}")
        if profile_data['right']:
            first_tooth = next(iter(profile_data['right']))
            print(f"右侧第一个齿({first_tooth})的数据点数: {len(profile_data['right'][first_tooth])}")
    
    print("\n解析完成!")
    
    # 保存解析结果
    with open('mka_parsed_data.json', 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)
    print("\n解析结果已保存到 mka_parsed_data.json")
    
except Exception as e:
    print(f"解析错误: {e}")
    import traceback
    traceback.print_exc()
