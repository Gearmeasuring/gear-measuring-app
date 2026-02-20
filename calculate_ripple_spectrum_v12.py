"""
波纹度频谱分析 V12 - 使用正确的展长到角度映射

关键算法：
1. Profile: 展长 s(d) = sqrt((d/2)^2 - (db/2)^2) → 旋转角 ξ = s / (π×db) × 360°
2. Helix: 轴向位置 z → 旋转角 α₂ = 2×Δz×tan(β₀)/D₀ (度)
3. 合并所有齿的数据形成360°闭合曲线
4. 对闭合曲线进行迭代最小二乘法频谱分析
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


def remove_crown_and_slope(data):
    """剔除鼓形和斜率偏差"""
    n = len(data)
    y = np.array(data, dtype=float)
    x = np.linspace(-1, 1, n)
    
    # 剔除鼓形 - 二次多项式拟合
    A_crown = np.column_stack((x**2, x, np.ones(n)))
    coeffs_crown, _, _, _ = np.linalg.lstsq(A_crown, y, rcond=None)
    a, b, c = coeffs_crown
    crown = a * x**2 + b * x + c
    y_no_crown = y - crown
    
    # 剔除斜率偏差 - 一次多项式
    A_slope = np.column_stack((x, np.ones(n)))
    coeffs_slope, _, _, _ = np.linalg.lstsq(A_slope, y_no_crown, rcond=None)
    k, d = coeffs_slope
    slope = k * x + d
    y_corrected = y_no_crown - slope
    
    return y_corrected


def iterative_sine_fit(curve_data, teeth_count, max_components=10):
    """迭代最小二乘法提取频谱（只使用ZE整数倍）"""
    n = len(curve_data)
    if n < 8:
        return {}
    
    x = np.linspace(0.0, 1.0, n, dtype=float)
    residual = np.array(curve_data, dtype=float)
    residual = residual - np.mean(residual)
    spectrum_results = {}
    
    max_iterations = 15
    amplitude_threshold = 0.001
    
    for iteration in range(max_iterations):
        candidate_orders = set()
        max_ze_multiple = 10
        for mult in range(1, max_ze_multiple + 1):
            freq = teeth_count * mult
            if freq not in spectrum_results:
                candidate_orders.add(freq)
        
        candidate_orders = sorted(candidate_orders)
        if len(candidate_orders) == 0:
            break
        
        best_order = None
        best_amplitude = 0.0
        best_coeffs = None
        
        for order in candidate_orders:
            try:
                sin_x = np.sin(2.0 * np.pi * order * x)
                cos_x = np.cos(2.0 * np.pi * order * x)
                A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                
                coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                a, b, c = coeffs
                amplitude = np.sqrt(a*a + b*b)
                
                if amplitude > 10.0:
                    continue
                
                if amplitude > best_amplitude:
                    best_amplitude = amplitude
                    best_order = order
                    best_coeffs = (a, b, c)
            except:
                continue
        
        if best_order is None or best_amplitude < amplitude_threshold:
            break
        
        spectrum_results[int(best_order)] = best_amplitude
        
        a, b, c = best_coeffs
        fitted_wave = a * np.sin(2.0 * np.pi * best_order * x) + b * np.cos(2.0 * np.pi * best_order * x) + c
        residual = residual - fitted_wave
        
        if len(spectrum_results) >= max_components:
            break
    
    return spectrum_results


def build_closed_curve_with_roll_angle(all_tooth_data, teeth_count, base_diameter, data_type='profile', 
                                        eval_start=0, eval_end=0, helix_angle=0, pitch_diameter=0):
    """
    构建闭合曲线 - 使用正确的展长到角度映射
    
    Profile: 展长 s(d) = sqrt((d/2)^2 - (db/2)^2)
             旋转角 ξ = s / (π×db) × 360°
    
    Helix: 轴向位置 z → 旋转角 α₂ = 2×Δz×tan(β₀)/D₀ (度)
    """
    if not all_tooth_data:
        return None, None
    
    angle_per_tooth = 360.0 / teeth_count
    base_circumference = math.pi * base_diameter
    
    all_angles = []
    all_values = []
    
    for tooth_idx, tooth_data in enumerate(all_tooth_data):
        if tooth_data is None or len(tooth_data) < 5:
            continue
        
        # 剔除鼓形和斜率偏差
        corrected_data = remove_crown_and_slope(tooth_data)
        
        tooth_center = tooth_idx * angle_per_tooth
        n_points = len(corrected_data)
        
        if data_type == 'profile':
            # Profile: 展长 → 旋转角
            # 计算展长范围
            roll_start = math.sqrt(max(0, (eval_start/2)**2 - (base_diameter/2)**2))
            roll_end = math.sqrt(max(0, (eval_end/2)**2 - (base_diameter/2)**2))
            roll_range = np.linspace(roll_start, roll_end, n_points)
            
            # 展长 → 旋转角 ξ
            xi = (roll_range / base_circumference) * 360.0
            # 以齿中心为基准
            xi = xi - (xi[-1] - xi[0]) / 2
            
            # 最终旋转角 α = ξ + τ (τ是齿位置偏移)
            alpha = xi + tooth_center
        else:
            # Helix: 轴向位置 → 旋转角
            axial_range = np.linspace(eval_start, eval_end, n_points)
            z0 = (eval_start + eval_end) / 2
            tan_beta = math.tan(math.radians(helix_angle))
            
            # 轴向角度差 α₂ = 2×Δz×tan(β₀)/D₀ (度)
            alpha2 = np.degrees((2.0 * (axial_range - z0) * tan_beta) / pitch_diameter)
            
            # 对于Helix，滚动角 ξ = 0
            # 最终旋转角 α = ξ + α₂ + τ
            alpha = alpha2 + tooth_center
        
        all_angles.extend(alpha)
        all_values.extend(corrected_data)
    
    # 排序并处理重叠
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    sort_idx = np.argsort(all_angles)
    all_angles = all_angles[sort_idx]
    all_values = all_values[sort_idx]
    
    # 对重叠角度进行平均
    unique_angles = np.unique(np.round(all_angles, 2))
    avg_values = []
    for angle in unique_angles:
        mask = np.abs(all_angles - angle) < 0.05
        if np.any(mask):
            avg_values.append(np.mean(all_values[mask]))
    
    return unique_angles, np.array(avg_values)


def analyze_ripple(mka_file):
    """分析波纹度"""
    print("="*70)
    print("波纹度频谱分析 V12 (展长到角度映射)")
    print("="*70)
    print("\n关键算法:")
    print("1. Profile: 展长 s(d) → 旋转角 ξ = s/(π×db)×360°")
    print("2. Helix: 轴向位置 z → 旋转角 α₂ = 2×Δz×tan(β₀)/D₀")
    print("3. 合并所有齿形成360°闭合曲线")
    print("4. 迭代最小二乘法频谱分析")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    # 计算基础参数
    beta = math.radians(helix_angle)
    alpha_n = math.radians(pressure_angle)
    alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
    pitch_diameter = teeth_count * module / math.cos(beta)
    base_diameter = pitch_diameter * math.cos(alpha_t)
    
    # 计算ep和el
    d1, d2 = 174.822, 180.603
    b1, b2 = 2.1, 39.9
    pb = math.pi * base_diameter / teeth_count
    beta_b = math.asin(math.sin(beta) * math.cos(alpha_n))
    
    lu = math.sqrt(max(0, (d1/2)**2 - (base_diameter/2)**2))
    lo = math.sqrt(max(0, (d2/2)**2 - (base_diameter/2)**2))
    la = lo - lu
    ep = la / pb
    
    lb = b2 - b1
    el = (lb * math.tan(beta_b)) / pb
    
    print(f"\n【齿轮参数】")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module} mm")
    print(f"  压力角 α = {pressure_angle}°")
    print(f"  螺旋角 β = {helix_angle}°")
    print(f"  节圆直径 d = {pitch_diameter:.4f} mm")
    print(f"  基圆直径 db = {base_diameter:.4f} mm")
    print(f"\n【评价参数】")
    print(f"  ep = {ep:.4f}")
    print(f"  el = {el:.4f}")
    
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    results = {}
    
    directions = [
        ('left', 'profile', '左齿形', profile_data, d1, d2),
        ('right', 'profile', '右齿形', profile_data, d1, d2),
        ('left', 'flank', '左齿向', flank_data, b1, b2),
        ('right', 'flank', '右齿向', flank_data, b1, b2)
    ]
    
    print(f"\nKlingelnberg报告参考值:")
    print(f"  左齿形 87阶: 0.14 μm")
    print(f"  右齿形 87阶: 0.15 μm")
    print(f"  左齿向 87阶: 0.12 μm")
    print(f"  右齿向 87阶: 0.09 μm")
    
    for side, data_type, name, data_source, eval_start, eval_end in directions:
        print(f"\n{'='*70}")
        print(f"【{name}】")
        print('='*70)
        
        data_dict = data_source.get(side, {})
        
        if not data_dict:
            print(f"  无数据")
            continue
        
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
        
        # 使用展长到角度映射构建闭合曲线
        angles, values = build_closed_curve_with_roll_angle(
            all_tooth_data, teeth_count, base_diameter, 
            data_type, eval_start, eval_end, helix_angle, pitch_diameter
        )
        
        if angles is None or len(angles) < 100:
            print(f"  闭合曲线构建失败")
            continue
        
        print(f"  闭合曲线点数: {len(angles)}")
        print(f"  角度范围: {np.min(angles):.2f}° ~ {np.max(angles):.2f}°")
        print(f"  数据范围: {np.min(values):.2f} ~ {np.max(values):.2f} μm")
        
        # 计算频谱
        spectrum = iterative_sine_fit(values, teeth_count, max_components=10)
        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n  提取的阶次 (ZE整数倍):")
        for i, (order, amp) in enumerate(sorted_spectrum[:5], 1):
            print(f"    {i}. 阶次 {order:3d} (ZE×{order//teeth_count}): 幅值 = {amp:.4f} μm")
        
        order_87_amp = spectrum.get(87, 0)
        print(f"\n  87阶幅值: {order_87_amp:.4f} μm")
        
        results[name] = {
            'order_87': order_87_amp,
            'spectrum': sorted_spectrum
        }
    
    # 打印对比汇总
    print("\n" + "="*70)
    print("对比汇总")
    print("="*70)
    print(f"\n{'曲线':<10} {'我们的结果':<15} {'Klingelnberg':<15} {'比率':<10}")
    print("-"*50)
    
    klingelnberg_values = {
        '左齿形': 0.14,
        '右齿形': 0.15,
        '左齿向': 0.12,
        '右齿向': 0.09
    }
    
    for name, data in results.items():
        our_val = data['order_87']
        k_val = klingelnberg_values.get(name, 0)
        ratio = our_val / k_val if k_val > 0 else 0
        print(f"{name:<10} {our_val:<15.4f} {k_val:<15.2f} {ratio:<10.2f}x")
    
    return results


def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    analyze_ripple(mka_file)


if __name__ == "__main__":
    main()
