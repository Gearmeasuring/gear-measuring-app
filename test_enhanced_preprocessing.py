"""
================================================================================
加强去鼓形和倾斜的影响分析
Enhanced Crown and Slope Removal Analysis
================================================================================
"""

import sys
import os
import numpy as np
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import (
    RippleWavinessAnalyzer, GearParameters, EvaluationRange,
    InvoluteCalculator, ProfileAngleCalculator, CurveBuilder,
    SpectrumAnalyzer, HighOrderEvaluator, DataPreprocessor
)

print("="*80)
print("加强去鼓形和倾斜的影响分析")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

print()
print("[预处理方法对比]")
print("-"*80)

# 方法1: 原始方法 (二次+线性)
def remove_crown_slope_v1(data):
    """原始方法: 二次多项式 + 线性"""
    n = len(data)
    x = np.linspace(-1, 1, n)
    
    # 二次多项式拟合
    A = np.column_stack((x**2, x, np.ones(n)))
    coeffs, _, _, _ = np.linalg.lstsq(A, data, rcond=None)
    a, b, c = coeffs
    fitted = a * x**2 + b * x + c
    data_no_crown = data - fitted
    
    # 线性拟合
    A = np.column_stack((x, np.ones(n)))
    coeffs, _, _, _ = np.linalg.lstsq(A, data_no_crown, rcond=None)
    k, d = coeffs
    slope = k * x + d
    corrected = data_no_crown - slope
    
    return corrected

# 方法2: 加强去鼓形 (四次多项式)
def remove_crown_slope_v2(data):
    """加强方法: 四次多项式拟合"""
    n = len(data)
    x = np.linspace(-1, 1, n)
    
    # 四次多项式拟合
    A = np.column_stack((x**4, x**3, x**2, x, np.ones(n)))
    coeffs, _, _, _ = np.linalg.lstsq(A, data, rcond=None)
    fitted = np.polyval(coeffs[::-1], x)
    corrected = data - fitted
    
    return corrected

# 方法3: 多次迭代去趋势
def remove_crown_slope_v3(data, iterations=3):
    """多次迭代去趋势"""
    corrected = np.array(data, dtype=float)
    n = len(data)
    x = np.linspace(-1, 1, n)
    
    for _ in range(iterations):
        # 二次多项式
        A = np.column_stack((x**2, x, np.ones(n)))
        coeffs, _, _, _ = np.linalg.lstsq(A, corrected, rcond=None)
        a, b, c = coeffs
        fitted = a * x**2 + b * x + c
        corrected = corrected - fitted
    
    return corrected

# 方法4: 高阶多项式 (六次)
def remove_crown_slope_v4(data):
    """高阶方法: 六次多项式拟合"""
    n = len(data)
    x = np.linspace(-1, 1, n)
    
    # 六次多项式拟合
    A = np.column_stack((x**6, x**5, x**4, x**3, x**2, x, np.ones(n)))
    coeffs, _, _, _ = np.linalg.lstsq(A, data, rcond=None)
    fitted = np.polyval(coeffs[::-1], x)
    corrected = data - fitted
    
    return corrected

# 获取测试数据
profile_data = analyzer.reader.profile_data.get('right', {})
tooth1_data = profile_data.get(1, {})
test_data = list(tooth1_data.values())[0]

print()
print("原始数据统计:")
print(f"  范围: [{test_data.min():.4f}, {test_data.max():.4f}] um")
print(f"  均值: {test_data.mean():.4f} um")
print(f"  标准差: {test_data.std():.4f} um")

methods = [
    (remove_crown_slope_v1, "V1: 二次+线性 (原始)"),
    (remove_crown_slope_v2, "V2: 四次多项式"),
    (remove_crown_slope_v3, "V3: 三次迭代"),
    (remove_crown_slope_v4, "V4: 六次多项式"),
]

print()
print("预处理效果对比:")
print("-"*80)
print(f"{'方法':<25} {'范围':<20} {'均值':<15} {'标准差':<10}")
print("-"*80)

for func, name in methods:
    corrected = func(test_data)
    print(f"{name:<25} [{corrected.min():>7.4f}, {corrected.max():>7.4f}] {corrected.mean():>10.6f} {corrected.std():>10.4f}")

print()
print("="*80)
print("频谱分析对比")
print("="*80)

def analyze_with_preprocessing(analyzer, profile_data, eval_range, side, preprocess_func):
    """使用指定预处理方法进行分析"""
    involute_calc = InvoluteCalculator(analyzer.gear_params)
    profile_calc = ProfileAngleCalculator(analyzer.gear_params, involute_calc)
    
    all_angles = []
    all_values = []
    
    sorted_teeth = sorted(profile_data.keys())
    
    for tooth_id in sorted_teeth:
        tooth_profiles = profile_data[tooth_id]
        
        for z_pos, values in tooth_profiles.items():
            if len(values) < 3:
                continue
            
            corrected_values = preprocess_func(values)
            
            num_points = len(corrected_values)
            polar_angles = profile_calc.calculate_profile_polar_angles(eval_range, num_points, side)
            
            tooth_index = tooth_id - 1
            tau = tooth_index * analyzer.gear_params.pitch_angle
            
            if side == 'right':
                final_angles = tau + polar_angles
            else:
                final_angles = tau - polar_angles
            
            all_angles.extend(final_angles.tolist())
            all_values.extend(corrected_values.tolist())
    
    if not all_angles:
        return None
    
    angles = np.array(all_angles)
    values = np.array(all_values)
    
    # 构建闭合曲线
    curve_builder = CurveBuilder(analyzer.gear_params)
    interp_angles, interp_values = curve_builder.build_closed_curve(angles, values)
    
    if interp_angles is None:
        return None
    
    # 频谱分析
    spectrum_analyzer = SpectrumAnalyzer(analyzer.gear_params)
    components = spectrum_analyzer.iterative_decomposition(
        interp_angles, interp_values, num_components=10, verbose=False
    )
    
    # 高阶评价
    high_order_eval = HighOrderEvaluator(analyzer.gear_params)
    total_amp, rms, high_waves, reconstructed = high_order_eval.evaluate(
        components, interp_angles
    )
    
    return {
        'angles': interp_angles,
        'values': interp_values,
        'components': components,
        'high_order_amplitude': total_amp,
        'high_order_rms': rms,
        'high_order_waves': high_waves
    }

# 分析右齿形
print()
print("[右齿形 profile_right]")
print("-"*80)

for func, name in methods:
    result = analyze_with_preprocessing(
        analyzer, profile_data, analyzer.reader.profile_eval_range, 'right', func
    )
    
    if result:
        print(f"\n{name}:")
        print(f"  前5个阶次: {[c.order for c in result['components'][:5]]}")
        print(f"  前5个振幅: {[f'{c.amplitude:.4f}' for c in result['components'][:5]]}")
        print(f"  高阶总振幅 W = {result['high_order_amplitude']:.4f} um")
        print(f"  高阶 RMS = {result['high_order_rms']:.4f} um")

# 分析左齿形
print()
print("[左齿形 profile_left]")
print("-"*80)

profile_data_left = analyzer.reader.profile_data.get('left', {})

for func, name in methods:
    result = analyze_with_preprocessing(
        analyzer, profile_data_left, analyzer.reader.profile_eval_range, 'left', func
    )
    
    if result:
        print(f"\n{name}:")
        print(f"  前5个阶次: {[c.order for c in result['components'][:5]]}")
        print(f"  前5个振幅: {[f'{c.amplitude:.4f}' for c in result['components'][:5]]}")
        print(f"  高阶总振幅 W = {result['high_order_amplitude']:.4f} um")
        print(f"  高阶 RMS = {result['high_order_rms']:.4f} um")

print()
print("="*80)
print("结论")
print("="*80)
print("""
1. 预处理方法对振幅有影响，但主要阶次基本一致
2. 高阶多项式拟合会去除更多低频成分
3. 迭代方法可以更彻底地去除趋势
4. 建议根据实际需求选择合适的预处理方法
""")
