#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用GearOverlapCalculator从MKA文件计算齿轮参数
"""

import sys
sys.path.append(r'e:\python\gear measuring software - 20251217\gear measuring software - 20251217')

from gear_analysis_refactored.utils.gear_overlap_calculator import GearOverlapCalculator

def main():
    mka_file = r"e:\python\gear measuring software - 20251217\gear measuring software - 20251217\004-xiaoxiao1.mka"
    
    print("=" * 80)
    print("齿轮参数计算程序 (使用GearOverlapCalculator)")
    print("=" * 80)
    print(f"MKA文件: {mka_file}")
    print()
    
    # 创建计算器
    calculator = GearOverlapCalculator()
    
    # 从MKA文件读取数据
    data = calculator.read_from_mka_file(mka_file)
    
    gear_data = data['gear_data']
    profile_data = data['profile_data']
    flank_data = data['flank_data']
    
    print("\n" + "=" * 80)
    print("计算结果")
    print("=" * 80)
    
    # 计算左右齿面的参数
    for side in ['left', 'right']:
        print(f"\n{'='*40}")
        print(f"{side.upper()} 齿面")
        print(f"{'='*40}")
        
        # 添加side参数到gear_data
        gear_data_with_side = gear_data.copy()
        gear_data_with_side['side'] = side
        
        # 计算齿形参数
        profile_params = calculator.calculate_profile_parameters(gear_data_with_side, profile_data)
        
        # 计算齿向参数
        helix_params = calculator.calculate_helix_parameters(gear_data_with_side, flank_data)
        
        # 打印结果
        print(f"\nep (齿形重叠系数) = {profile_params['ep']:.3f}")
        print(f"lo (滚长终评点)   = {profile_params['lo']:.3f}")
        print(f"lu (滚长起评点)   = {profile_params['lu']:.3f}")
        print(f"\nel (齿向重叠系数) = {helix_params['el']:.3f}")
        print(f"zo (齿向评估+半)   = {helix_params['zo']:.3f}")
        print(f"zu (齿向评估-半)   = {helix_params['zu']:.3f}")

if __name__ == "__main__":
    main()
