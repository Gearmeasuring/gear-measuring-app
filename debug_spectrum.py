#!/usr/bin/env python3
"""
调试脚本：分析MKA文件数据和候选阶次
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.utils.file_parser import parse_mka_file
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings, SpectrumParams

# 设置输出编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 查找MKA文件
mka_files = [
    "263751-018-WAV.mka",
    "004-xiaoxiao1.mka"
]

mka_file = None
for file in mka_files:
    if os.path.exists(file):
        mka_file = file
        break

if mka_file is None:
    print("错误：未找到MKA文件")
    sys.exit(1)

print(f"使用MKA文件: {mka_file}")

# 解析MKA文件
try:
    mka_data = parse_mka_file(mka_file)
    print(f"MKA文件解析成功")
except Exception as e:
    print(f"解析MKA文件失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 提取数据
gear_data = mka_data['gear_data']
profile_data = mka_data['profile_data']
flank_data = mka_data['flank_data']
pitch_data = mka_data.get('pitch_data', {})

# 创建报告生成器
settings = RippleSpectrumSettings()
report = KlingelnbergRippleSpectrumReport(settings)

# 分析Profile Right数据
print("\n=== 分析 Profile Right 数据 ===")
profile_right_data = profile_data.get('right', {})
if profile_right_data:
    first_tooth_id = list(profile_right_data.keys())[0]
    first_tooth_data = profile_right_data[first_tooth_id]
    print(f"第一个齿号: {first_tooth_id}")
    print(f"第一个齿数据长度: {len(first_tooth_data)}")
    print(f"第一个齿数据前10个点: {first_tooth_data[:10]}")
    print(f"第一个齿数据统计: min={np.min(first_tooth_data):.3f}, max={np.max(first_tooth_data):.3f}, mean={np.mean(first_tooth_data):.3f}")

    # 测试单位转换
    vals_mm = np.array(first_tooth_data, dtype=float)
    vals_um = report._values_to_um(vals_mm)
    print(f"\n单位转换测试:")
    print(f"原始数据（可能是mm）: {vals_mm[:5]}")
    print(f"转换后数据（μm）: {vals_um[:5]}")
    print(f"转换后统计: min={np.min(vals_um):.3f}, max={np.max(vals_um):.3f}, mean={np.mean(vals_um):.3f}")

    # 分析候选阶次
    ze = gear_data.get('teeth', 87)
    max_order = 500
    print(f"\n=== 候选阶次分析 ===")
    print(f"齿数ZE: {ze}")
    print(f"最大阶次: {max_order}")

    # 生成候选阶次
    candidate_orders = set()

    # 1. 添加ZE及其倍数（1ZE, 2ZE, 3ZE, 4ZE, 5ZE, 6ZE）
    ze_multiples = []
    for multiple in range(1, 7):
        order = ze * multiple
        if 1 <= order <= max_order:
            candidate_orders.add(order)
            ze_multiples.append(order)

    print(f"\nZE倍数阶次: {ze_multiples}")

    # 2. 添加ZE倍数附近的阶次（±10范围内）
    for multiple in range(1, 7):
        center_order = ze * multiple
        for offset in range(-10, 11):
            order = center_order + offset
            if 1 <= order <= max_order:
                candidate_orders.add(order)

    # 3. 添加ZE附近的阶次（±15范围内）
    for offset in range(-15, 16):
        order = ze + offset
        if 1 <= order <= max_order:
            candidate_orders.add(order)

    # 4. 添加参考数据中的重要阶次
    reference_specific_orders = [86, 88, 89, 435, 522]
    for order in reference_specific_orders:
        if 1 <= order <= max_order:
            candidate_orders.add(order)

    # 转换为排序后的列表
    candidate_orders = sorted(candidate_orders)
    print(f"候选阶次总数: {len(candidate_orders)}")
    print(f"候选阶次前20个: {candidate_orders[:20]}")
    print(f"候选阶次后20个: {candidate_orders[-20:]}")

    # 测试单个阶次的拟合
    print(f"\n=== 测试单个阶次的拟合 ===")
    n = len(vals_um)
    x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)

    # 测试ZE倍数阶次
    for order in ze_multiples:
        try:
            sin_x = np.sin(float(order) * x)
            cos_x = np.cos(float(order) * x)
            A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))

            coeffs, _, _, _ = np.linalg.lstsq(A, vals_um, rcond=None)
            a, b, c = coeffs
            amplitude = float(np.sqrt(a * a + b * b))

            print(f"阶次 {order}（{order/ze:.1f}ZE）: 幅值 = {amplitude:.6f} μm")
        except Exception as e:
            print(f"阶次 {order} 拟合失败: {e}")

    # 测试其他候选阶次
    print(f"\n=== 测试其他候选阶次的拟合 ===")
    test_orders = [72, 73, 74, 75, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445]
    for order in test_orders:
        try:
            sin_x = np.sin(float(order) * x)
            cos_x = np.cos(float(order) * x)
            A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))

            coeffs, _, _, _ = np.linalg.lstsq(A, vals_um, rcond=None)
            a, b, c = coeffs
            amplitude = float(np.sqrt(a * a + b * b))

            print(f"阶次 {order}: 幅值 = {amplitude:.6f} μm")
        except Exception as e:
            print(f"阶次 {order} 拟合失败: {e}")

print("\n=== 调试完成 ===")
