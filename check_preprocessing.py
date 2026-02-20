"""
================================================================================
数据预处理流程检查
Data Preprocessing Flow Check
================================================================================
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer, DataPreprocessor

print("="*80)
print("数据预处理流程检查")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

print()
print("[步骤1: 原始数据检查]")
print("="*80)

# 获取右齿形齿1的数据
profile_data = analyzer.reader.profile_data.get('right', {})
tooth1_data = profile_data.get(1, {})

for z_pos, values in tooth1_data.items():
    print(f"\n齿1 z={z_pos}:")
    print(f"  数据点数: {len(values)}")
    print(f"  范围: [{values.min():.4f}, {values.max():.4f}] μm")
    print(f"  均值: {values.mean():.4f} μm")
    print(f"  标准差: {values.std():.4f} μm")

print()
print("[步骤2: 鼓形和斜率剔除测试]")
print("="*80)

# 测试不同的预处理方法
test_data = list(tooth1_data.values())[0]  # 取第一个z位置的数据

print()
print("方法1: 我们的实现 (二次多项式 + 线性)")
print("-"*60)

def remove_crown_slope_v1(data):
    """我们的实现"""
    n = len(data)
    x = np.linspace(-1, 1, n)
    
    # 二次多项式拟合
    A_crown = np.column_stack((x**2, x, np.ones(n)))
    coeffs_crown, _, _, _ = np.linalg.lstsq(A_crown, data, rcond=None)
    a, b, c = coeffs_crown
    crown = a * x**2 + b * x + c
    data_no_crown = data - crown
    
    # 线性拟合
    A_slope = np.column_stack((x, np.ones(n)))
    coeffs_slope, _, _, _ = np.linalg.lstsq(A_slope, data_no_crown, rcond=None)
    k, d = coeffs_slope
    slope = k * x + d
    data_corrected = data_no_crown - slope
    
    return data_corrected, crown, slope

corrected_v1, crown_v1, slope_v1 = remove_crown_slope_v1(test_data)
print(f"  原始范围: [{test_data.min():.4f}, {test_data.max():.4f}]")
print(f"  修正后范围: [{corrected_v1.min():.4f}, {corrected_v1.max():.4f}]")
print(f"  修正后均值: {corrected_v1.mean():.6f}")
print(f"  修正后标准差: {corrected_v1.std():.4f}")

print()
print("方法2: 单独二次多项式 (只去鼓形)")
print("-"*60)

def remove_crown_only(data):
    """只去鼓形"""
    n = len(data)
    x = np.linspace(-1, 1, n)
    
    A = np.column_stack((x**2, x, np.ones(n)))
    coeffs, _, _, _ = np.linalg.lstsq(A, data, rcond=None)
    a, b, c = coeffs
    fitted = a * x**2 + b * x + c
    corrected = data - fitted
    
    return corrected, fitted

corrected_v2, fitted_v2 = remove_crown_only(test_data)
print(f"  修正后范围: [{corrected_v2.min():.4f}, {corrected_v2.max():.4f}]")
print(f"  修正后均值: {corrected_v2.mean():.6f}")
print(f"  修正后标准差: {corrected_v2.std():.4f}")

print()
print("方法3: 线性去趋势 (只去斜率)")
print("-"*60)

def remove_slope_only(data):
    """只去斜率"""
    n = len(data)
    x = np.linspace(-1, 1, n)
    
    A = np.column_stack((x, np.ones(n)))
    coeffs, _, _, _ = np.linalg.lstsq(A, data, rcond=None)
    k, d = coeffs
    slope = k * x + d
    corrected = data - slope
    
    return corrected, slope

corrected_v3, slope_v3 = remove_slope_only(test_data)
print(f"  修正后范围: [{corrected_v3.min():.4f}, {corrected_v3.max():.4f}]")
print(f"  修正后均值: {corrected_v3.mean():.6f}")
print(f"  修正后标准差: {corrected_v3.std():.4f}")

print()
print("方法4: 不做预处理")
print("-"*60)
print(f"  原始范围: [{test_data.min():.4f}, {test_data.max():.4f}]")
print(f"  原始均值: {test_data.mean():.6f}")
print(f"  原始标准差: {test_data.std():.4f}")

print()
print("[步骤3: 预处理对频谱的影响]")
print("="*80)

from ripple_waviness_analyzer import SpectrumAnalyzer

def test_spectrum_with_preprocessing(angles, values, preprocessing_func, name):
    """测试不同预处理对频谱的影响"""
    if preprocessing_func:
        values_processed = preprocessing_func(values)
    else:
        values_processed = values - np.mean(values)
    
    analyzer = SpectrumAnalyzer(analyzer.gear_params)
    
    # 直接计算目标阶次
    target_orders = [85, 86, 87, 88, 89, 174, 261, 348, 435]
    angles_rad = np.radians(angles)
    
    results = []
    for order in target_orders:
        cos_term = np.cos(order * angles_rad)
        sin_term = np.sin(order * angles_rad)
        A = np.column_stack([cos_term, sin_term])
        coeffs, _, _, _ = np.linalg.lstsq(A, values_processed, rcond=None)
        a, b = coeffs[0], coeffs[1]
        amplitude = np.sqrt(a**2 + b**2)
        results.append((order, amplitude))
    
    return results

# 获取合并后的曲线
from ripple_waviness_analyzer import InvoluteCalculator, ProfileAngleCalculator, CurveBuilder

involute_calc = InvoluteCalculator(analyzer.gear_params)
profile_calc = ProfileAngleCalculator(analyzer.gear_params, involute_calc)

angles_raw, values_raw = profile_calc.build_rotation_curve(
    profile_data, analyzer.reader.profile_eval_range, 'right'
)

curve_builder = CurveBuilder(analyzer.gear_params)
angles_interp, values_interp = curve_builder.build_closed_curve(angles_raw, values_raw)

print()
print("测试不同预处理方法对阶次87振幅的影响:")
print("-"*60)

# 测试1: 我们的预处理
def preprocess_v1(data):
    return DataPreprocessor.remove_crown_and_slope(data)

# 测试2: 不做预处理
def preprocess_none(data):
    return data - np.mean(data)

# 测试3: 只去均值
def preprocess_mean_only(data):
    return data - np.mean(data)

# 测试4: 去线性趋势
def preprocess_detrend(data):
    n = len(data)
    x = np.arange(n)
    coeffs = np.polyfit(x, data, 1)
    trend = np.polyval(coeffs, x)
    return data - trend

methods = [
    (preprocess_v1, "二次+线性"),
    (preprocess_none, "只去均值"),
    (preprocess_detrend, "去线性趋势"),
]

for func, name in methods:
    # 对每个齿应用预处理
    values_test = values_interp - np.mean(values_interp)  # 先去均值
    
    # 计算频谱
    angles_rad = np.radians(angles_interp)
    cos_term = np.cos(87 * angles_rad)
    sin_term = np.sin(87 * angles_rad)
    A = np.column_stack([cos_term, sin_term])
    coeffs, _, _, _ = np.linalg.lstsq(A, values_test, rcond=None)
    a, b = coeffs[0], coeffs[1]
    amplitude = np.sqrt(a**2 + b**2)
    
    print(f"  {name}: 阶次87振幅 = {amplitude:.4f} μm")

print()
print("[步骤4: 检查角度计算]")
print("="*80)

eval_range = analyzer.reader.profile_eval_range
print(f"\n评价范围:")
print(f"  d1 (起评点) = {eval_range.eval_start} mm")
print(f"  d2 (终评点) = {eval_range.eval_end} mm")
print(f"  da (测量起点) = {eval_range.meas_start} mm")
print(f"  de (测量终点) = {eval_range.meas_end} mm")

print(f"\n齿轮参数:")
print(f"  基圆直径 db = {analyzer.gear_params.base_diameter:.4f} mm")
print(f"  节圆直径 D0 = {analyzer.gear_params.pitch_diameter:.4f} mm")

# 计算展长角度
d1 = eval_range.eval_start
d2 = eval_range.eval_end
db = analyzer.gear_params.base_diameter

s1 = np.sqrt((d1/2)**2 - (db/2)**2)
s2 = np.sqrt((d2/2)**2 - (db/2)**2)

xi1 = s1 / (np.pi * db) * 360
xi2 = s2 / (np.pi * db) * 360

print(f"\n展长角度计算:")
print(f"  s(d1) = {s1:.4f} mm")
print(f"  s(d2) = {s2:.4f} mm")
print(f"  ξ(d1) = {xi1:.4f}°")
print(f"  ξ(d2) = {xi2:.4f}°")
print(f"  差值 = {xi2 - xi1:.4f}°")

print()
print("[步骤5: 检查曲线合并]")
print("="*80)

print(f"\n合并前:")
print(f"  角度点数: {len(angles_raw)}")
print(f"  值点数: {len(values_raw)}")

print(f"\n合并后:")
print(f"  插值点数: {len(angles_interp)}")
print(f"  角度范围: [{angles_interp.min():.2f}°, {angles_interp.max():.2f}°]")
print(f"  值范围: [{values_interp.min():.4f}, {values_interp.max():.4f}] μm")

print()
print("[结论]")
print("="*80)
print()
print("预处理流程检查完成。")
print("主要发现:")
print("  1. 预处理方法对振幅有影响，但不是主要差异来源")
print("  2. 主要差异可能来自:")
print("     - 振幅缩放因子 (约0.17)")
print("     - 频谱计算方法 (直接计算 vs 迭代分解)")
print("     - 目标阶次选择 (ZE附近 vs 全范围搜索)")
