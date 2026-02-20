"""
分析计算结果与Klingelnberg报告的差异
"""
import numpy as np

print("="*70)
print("计算结果与Klingelnberg报告差异分析")
print("="*70)

# Klingelnberg报告数据 (从PDF读取)
klingelnberg_data = {
    'Profile left': {
        'orders': [87, 261, 174, 435, 86],
        'amplitudes': [0.14, 0.14, 0.05, 0.04, 0.03],
        'w_value': None  # 报告中未直接给出
    },
    'Profile right': {
        'orders': [87, 348, 261, 174, 86, 88, 435, 522, 89],
        'amplitudes': [0.15, 0.07, 0.06, 0.05, 0.04, 0.03, 0.03, 0.03, 0.03],
        'w_value': None
    },
    'Helix left': {
        'orders': [87, 89, 86, 88, 174, 85, 348, 261],
        'amplitudes': [0.12, 0.07, 0.06, 0.05, 0.04, 0.04, 0.03, 0.02],
        'w_value': None
    },
    'Helix right': {
        'orders': [87, 174, 261, 88, 89, 86],
        'amplitudes': [0.09, 0.10, 0.05, 0.04, 0.03, 0.03],
        'w_value': None
    }
}

# 我们的计算结果
our_data = {
    'Profile left': {
        'orders': [87, 348, 174, 261, 435, 86, 347, 434, 260, 173],
        'amplitudes': [1.2485, 0.3641, 0.3545, 0.2075, 0.1036, 0.0874, 0.0691, 0.0553, 0.0542, 0.0441],
        'w_value': 2.5009
    },
    'Profile right': {
        'orders': [87, 261, 348, 174, 260, 434, 435, 173, 259, 263],
        'amplitudes': [0.9256, 0.4838, 0.4184, 0.3201, 0.1464, 0.1232, 0.1221, 0.1198, 0.1073, 0.1018],
        'w_value': 2.8685
    },
    'Helix left': {
        'orders': [87, 348, 88, 435, 261, 85, 172, 176, 263, 86],
        'amplitudes': [0.1764, 0.1236, 0.1015, 0.0939, 0.0851, 0.0811, 0.0661, 0.0622, 0.0638, 0.0577],
        'w_value': 0.7727
    },
    'Helix right': {
        'orders': [87, 348, 435, 261, 86, 175, 88, 172, 174, 176],
        'amplitudes': [0.1591, 0.1115, 0.1117, 0.1070, 0.0699, 0.0552, 0.0555, 0.0527, 0.0524, 0.0454],
        'w_value': 0.7505
    }
}

print("\n【差异对比】")
print("-"*70)

for name in klingelnberg_data.keys():
    print(f"\n{name}:")
    print("-"*50)
    
    k_data = klingelnberg_data[name]
    o_data = our_data[name]
    
    # 对比主要阶次
    print("  阶次对比 (Klingelnberg vs 我们的计算):")
    for i, (k_order, k_amp) in enumerate(zip(k_data['orders'][:5], k_data['amplitudes'][:5])):
        # 在我们的结果中查找相同阶次
        if k_order in o_data['orders']:
            idx = o_data['orders'].index(k_order)
            o_amp = o_data['amplitudes'][idx]
            ratio = o_amp / k_amp if k_amp > 0 else 0
            print(f"    阶次 {k_order:3d}: K={k_amp:.2f}μm, 我们={o_amp:.4f}μm, 比率={ratio:.1f}x")
        else:
            print(f"    阶次 {k_order:3d}: K={k_amp:.2f}μm, 我们=未找到")
    
    # 计算总幅值比
    k_total = sum(k_data['amplitudes'])
    o_total = sum(o_data['amplitudes'][:len(k_data['amplitudes'])])
    print(f"\n  总幅值对比: Klingelnberg={k_total:.2f}μm, 我们={o_total:.4f}μm, 比率={o_total/k_total:.1f}x")

print("\n" + "="*70)
print("【可能的原因分析】")
print("="*70)

reasons = """
1. 数据预处理差异:
   - Klingelnberg可能使用了不同的滤波器（报告提到"Low-pass filter RC"）
   - 鼓形和斜率剔除的方法可能不同
   - 异常值处理方式不同

2. 频谱分析方法差异:
   - Klingelnberg可能使用了FFT而不是迭代最小二乘法
   - 窗口函数的使用可能不同
   - 频谱分辨率或频率范围不同

3. 高阶评价标准差异:
   - 报告中提到"Way of evaluation: High orders"
   - 可能对高阶的定义不同（>=ZE vs >ZE）
   - 可能只显示部分高阶成分

4. 数据单位或缩放:
   - 我们的计算结果大约是报告的5-10倍
   - 可能存在单位换算问题（mm vs μm）
   - 可能存在缩放因子

5. 闭合曲线构建差异:
   - 角度映射方式可能不同
   - 重叠区域处理方式可能不同
   - 插值方法可能不同
"""

print(reasons)

print("="*70)
print("【建议检查点】")
print("="*70)

checks = """
1. 检查原始数据单位:
   - MKA文件中的数据是否已经是μm?
   - 是否需要除以某个缩放因子?

2. 检查滤波器设置:
   - 报告中的"Low-pass filter RC"是什么参数?
   - 是否需要应用相同的滤波器?

3. 检查频谱分析方法:
   - 是否应该使用FFT而不是最小二乘法?
   - 是否需要加窗处理?

4. 检查高阶定义:
   - Klingelnberg的高阶是否包含ZE阶?
   - 是否只考虑ZE的整数倍?

5. 检查闭合曲线构建:
   - ep和el的使用是否正确?
   - 角度映射公式是否正确?
"""

print(checks)
