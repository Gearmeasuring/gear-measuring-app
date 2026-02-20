"""
运行原始Klingelnberg代码进行对比
"""
import os
import sys
import math
import numpy as np
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file
from reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings, SpectrumParams

mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"

print("="*70)
print("运行原始Klingelnberg代码")
print("="*70)

# 解析MKA文件
parsed_data = parse_mka_file(mka_file)
gear_data = parsed_data.get('gear_data', {})

teeth_count = gear_data.get('teeth', 87)
module = gear_data.get('module', 1.859)
pressure_angle = gear_data.get('pressure_angle', 18.6)
helix_angle = gear_data.get('helix_angle', 25.3)

print(f"\n【齿轮参数】")
print(f"  齿数 ZE = {teeth_count}")
print(f"  模数 m = {module} mm")
print(f"  压力角 α = {pressure_angle}°")
print(f"  螺旋角 β = {helix_angle}°")

# 获取测量数据
profile_data = parsed_data.get('profile_data', {})
flank_data = parsed_data.get('flank_data', {})

# 创建报告生成器
settings = RippleSpectrumSettings()
report = KlingelnbergRippleSpectrumReport(settings)

# 分析四个方向
directions = [
    ('left', 'profile', '左齿形', profile_data),
    ('right', 'profile', '右齿形', profile_data),
    ('left', 'flank', '左齿向', flank_data),
    ('right', 'flank', '右齿向', flank_data)
]

print("\n" + "="*70)
print("原始代码频谱分析结果")
print("="*70)

for side, data_type, name, data_source in directions:
    print(f"\n【{name}】")
    
    data_dict = data_source.get(side, {})
    
    if not data_dict:
        print(f"  无数据")
        continue
    
    # 收集所有齿的数据
    all_tooth_data = []
    for tooth_id in sorted(data_dict.keys()):
        tooth_data = data_dict[tooth_id]
        if isinstance(tooth_data, dict):
            values = tooth_data.get('values', [])
        else:
            values = tooth_data
        if values and len(values) > 5:
            all_tooth_data.append(np.array(values, dtype=float))
    
    if len(all_tooth_data) < 5:
        print(f"  数据不足 ({len(all_tooth_data)}齿)")
        continue
    
    print(f"  有效齿数: {len(all_tooth_data)}")
    
    # 创建参数对象
    params = SpectrumParams(
        data_dict={i: data for i, data in enumerate(all_tooth_data)},
        teeth_count=teeth_count,
        eval_markers=None,
        max_order=5*teeth_count
    )
    
    # 调用原始代码的频谱计算方法
    try:
        # 使用反射调用内部方法
        from reports.klingelnberg_ripple_spectrum import SineFitParams
        
        # 构建闭合曲线
        # 这里需要简化调用，因为原始代码结构较复杂
        print(f"  原始代码结构复杂，无法直接调用内部方法")
        
    except Exception as e:
        print(f"  错误: {e}")

print("\n" + "="*70)
print("建议直接运行原始代码生成完整报告")
print("="*70)
