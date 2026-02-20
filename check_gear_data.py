#!/usr/bin/env python3
"""
检查齿轮基本数据的脚本
"""

from gear_analysis_refactored.utils.file_parser import parse_mka_file

def main():
    # 解析MKA文件
    mka_file = "263751-018-WAV.mka"
    print(f"解析文件: {mka_file}")
    parsed_data = parse_mka_file(mka_file)
    
    if parsed_data:
        # 提取齿轮基本数据
        gear_data = parsed_data.get('gear_data', {})
        print("\n齿轮基本数据:")
        for key, value in gear_data.items():
            print(f"{key}: {value}")
        
        # 提取测量数据信息
        profile_data = parsed_data.get('profile_data', {})
        print("\n齿形数据:")
        print(f"左侧齿数: {len(profile_data.get('left', {}))}")
        print(f"右侧齿数: {len(profile_data.get('right', {}))}")
        
        topography_data = parsed_data.get('topography_data', {})
        print("\n齿向数据:")
        print(f"总齿数: {len(topography_data)}")

if __name__ == "__main__":
    main()
