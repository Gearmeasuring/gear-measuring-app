#!/usr/bin/env python3
"""
调试脚本：查看从topography_data中提取齿向数据的结果
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
        topography_data = parsed_data.get('topography_data', {})
        
        print(f"\n=== 调试信息 ===")
        print(f"topography_data 类型: {type(topography_data)}")
        print(f"topography_data 包含的齿数: {len(topography_data)}")
        
        # 从topography_data中提取齿向数据
        def extract_flank_data_from_topography(topography_data, side):
            """从topography_data中提取齿向数据"""
            flank_data = {}
            for tooth_num, tooth_data in topography_data.items():
                if side in tooth_data:
                    flank_lines = tooth_data[side].get('flank_lines', {})
                    if flank_lines:
                        # 取中间位置的齿向数据（idx=2）
                        if 2 in flank_lines:
                            flank_data[tooth_num] = flank_lines[2].get('values', [])
                        elif 1 in flank_lines:
                            flank_data[tooth_num] = flank_lines[1].get('values', [])
                        elif 3 in flank_lines:
                            flank_data[tooth_num] = flank_lines[3].get('values', [])
            return flank_data
        
        # 提取齿向数据
        helix_left = extract_flank_data_from_topography(topography_data, 'left')
        helix_right = extract_flank_data_from_topography(topography_data, 'right')
        
        print(f"\n从topography_data提取的左齿向数据长度: {len(helix_left)}")
        print(f"从topography_data提取的右齿向数据长度: {len(helix_right)}")
        
        # 查看第一个齿的数据
        if helix_left:
            first_tooth = list(helix_left.keys())[0]
            print(f"\n第一个齿 ({first_tooth}) 的左齿向数据长度: {len(helix_left[first_tooth])}")
            print(f"数据示例: {helix_left[first_tooth][:5]}...{helix_left[first_tooth][-5:]}")
        
        if helix_right:
            first_tooth = list(helix_right.keys())[0]
            print(f"\n第一个齿 ({first_tooth}) 的右齿向数据长度: {len(helix_right[first_tooth])}")
            print(f"数据示例: {helix_right[first_tooth][:5]}...{helix_right[first_tooth][-5:]}")
        
    else:
        print("无法从MKA文件读取数据")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
