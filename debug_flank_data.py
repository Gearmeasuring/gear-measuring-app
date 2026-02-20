#!/usr/bin/env python3
"""
调试脚本：查看 flank_data 的内容
"""

from gear_analysis_refactored.utils.file_parser import parse_mka_file

# MKA文件路径
mka_file_path = "263751-018-WAV.mka"

try:
    # 从MKA文件读取数据
    print(f"读取MKA文件: {mka_file_path}")
    parsed_data = parse_mka_file(mka_file_path)
    
    if parsed_data:
        # 提取测量数据
        profile_data = parsed_data.get('profile_data', {})
        flank_data = parsed_data.get('flank_data', {})
        topography_data = parsed_data.get('topography_data', {})
        
        print(f"\n=== 调试信息 ===")
        print(f"profile_data 类型: {type(profile_data)}")
        print(f"profile_data 键: {list(profile_data.keys())}")
        print(f"left 齿形数据长度: {len(profile_data.get('left', {}))}")
        print(f"right 齿形数据长度: {len(profile_data.get('right', {}))}")
        
        print(f"\nflank_data 类型: {type(flank_data)}")
        print(f"flank_data 键: {list(flank_data.keys())}")
        print(f"left 齿向数据长度: {len(flank_data.get('left', {}))}")
        print(f"right 齿向数据长度: {len(flank_data.get('right', {}))}")
        
        print(f"\ntopography_data 类型: {type(topography_data)}")
        print(f"topography_data 包含的齿数: {len(topography_data)}")
        
        # 检查第一个齿的数据
        if topography_data:
            first_tooth = list(topography_data.keys())[0]
            tooth_data = topography_data[first_tooth]
            print(f"\n第一个齿 ({first_tooth}) 的数据:")
            print(f"  left 侧: {tooth_data.get('left', {})}")
            print(f"  right 侧: {tooth_data.get('right', {})}")
            
    else:
        print("无法从MKA文件读取数据")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
