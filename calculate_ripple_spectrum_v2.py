"""
波纹度频谱分析 V2
1. 剔除鼓形（二元二次多项式）和斜率偏差（一元一次多项式）
2. 迭代最小二乘法提取前10个最大阶次的正弦波
3. 高阶评价（>= ZE）
"""
import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def remove_crown_and_slope(data, x_coords=None):
    """
    剔除鼓形（二元二次多项式）和斜率偏差（一元一次多项式）
    """
    n = len(data)
    if x_coords is None:
        x_coords = np.linspace(-1, 1, n)
    
    y = np.array(data, dtype=float)
    x = np.array(x_coords, dtype=float)
    
    # 1. 剔除鼓形 - 二元二次多项式拟合: y = a*x^2 + b*x + c
    # 这里简化为只考虑x方向的一元二次（鼓形）
    A_crown = np.column_stack((x**2, x, np.ones(n)))
    coeffs_crown, _, _, _ = np.linalg.lstsq(A_crown, y, rcond=None)
    a, b, c = coeffs_crown
    crown = a * x**2 + b * x + c
    y_no_crown = y - crown
    
    # 2. 剔除斜率偏差 - 一元一次多项式: y = k*x + d
    A_slope = np.column_stack((x, np.ones(n)))
    coeffs_slope, _, _, _ = np.linalg.lstsq(A_slope, y_no_crown, rcond=None)
    k, d = coeffs_slope
    slope = k * x + d
    y_corrected = y_no_crown - slope
    
    return y_corrected, crown, slope


def iterative_sine_decomposition(angles, values, teeth_count, max_components=10):
    """
    迭代最小二乘法提取前N个最大阶次的正弦波
    
    算法步骤:
    1. 在剩余信号中找到幅值最大的正弦波（最小二乘法拟合）
    2. 从信号中移除该正弦波
    3. 重复步骤1-2，直到提取出指定数量的分量
    """
    theta = np.radians(angles)
    residual = np.array(values, dtype=float)
    
    # 去均值
    residual = residual - np.mean(residual)
    
    components = []
    max_order = 5 * teeth_count
    
    for iteration in range(max_components):
        best_amplitude = 0
        best_order = 0
        best_coeffs = None
        
        # 搜索所有阶次，找到幅值最大的
        for order in range(1, max_order + 1):
            cos_x = np.cos(order * theta)
            sin_x = np.sin(order * theta)
            A = np.column_stack((cos_x, sin_x))
            
            try:
                coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                a, b = coeffs
                amplitude = np.sqrt(a*a + b*b)
                
                if amplitude > best_amplitude:
                    best_amplitude = amplitude
                    best_order = order
                    best_coeffs = coeffs
            except:
                continue
        
        if best_coeffs is None or best_amplitude < 1e-10:
            break
        
        a, b = best_coeffs
        # 重构该阶次的正弦波
        fitted_wave = a * np.cos(best_order * theta) + b * np.sin(best_order * theta)
        
        # 计算相位
        phase = np.arctan2(a, b)
        
        components.append({
            'order': best_order,
            'amplitude': best_amplitude,
            'phase': np.degrees(phase),
            'a': a,
            'b': b
        })
        
        # 从剩余信号中移除该正弦波
        residual = residual - fitted_wave
    
    return components, residual


def build_closed_curve(all_tooth_data, teeth_count, base_diameter, data_type='profile', 
                       eval_start=0, eval_end=0, helix_angle=0, pitch_diameter=0):
    """构建闭合曲线"""
    if not all_tooth_data:
        return None, None
    
    angle_per_tooth = 360.0 / teeth_count
    base_circumference = math.pi * base_diameter
    
    all_angles = []
    all_values = []
    
    for tooth_idx, tooth_data in enumerate(all_tooth_data):
        if tooth_data is None or len(tooth_data) < 5:
            continue
        
        tooth_center = tooth_idx * angle_per_tooth
        n_points = len(tooth_data)
        
        # 生成x坐标（-1到1）用于剔除鼓形和斜率
        x_coords = np.linspace(-1, 1, n_points)
        
        # 剔除鼓形和斜率偏差
        corrected_data, crown, slope = remove_crown_and_slope(tooth_data, x_coords)
        
        if data_type == 'profile':
            # Profile: 展长 → 旋转角
            roll_start = math.sqrt(max(0, (eval_start/2)**2 - (base_diameter/2)**2))
            roll_end = math.sqrt(max(0, (eval_end/2)**2 - (base_diameter/2)**2))
            roll_range = np.linspace(roll_start, roll_end, n_points)
            local_angles = (roll_range / base_circumference) * 360.0
            local_angles = local_angles - (local_angles[-1] - local_angles[0]) / 2
        else:
            # Helix: 轴向位置 → 旋转角
            axial_range = np.linspace(eval_start, eval_end, n_points)
            z0 = (eval_start + eval_end) / 2
            tan_beta = math.tan(math.radians(helix_angle))
            local_angles = np.degrees((2.0 * (axial_range - z0) * tan_beta) / pitch_diameter)
        
        global_angles = (tooth_center + local_angles) % 360.0
        
        all_angles.extend(global_angles)
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
    print("波纹度频谱分析 V2")
    print("="*70)
    print("\n算法流程:")
    print("1. 剔除鼓形（二元二次多项式）和斜率偏差（一元一次多项式）")
    print("2. 迭代最小二乘法提取前10个最大阶次的正弦波")
    print("3. 高阶评价（>= ZE）")
    
    # 解析MKA文件
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
    
    print(f"\n【齿轮参数】")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module} mm")
    print(f"  压力角 α = {pressure_angle}°")
    print(f"  螺旋角 β = {helix_angle}°")
    print(f"  节圆直径 d = {pitch_diameter:.4f} mm")
    print(f"  基圆直径 db = {base_diameter:.4f} mm")
    
    # 获取评价范围
    profile_eval_start = 174.822
    profile_eval_end = 180.603
    helix_eval_start = 2.1
    helix_eval_end = 39.9
    
    # 获取测量数据
    measurements = parsed_data.get('measurements', {})
    
    results = {}
    
    # 分析四个方向
    directions = [
        ('left', 'profile', '左齿形'),
        ('right', 'profile', '右齿形'),
        ('left', 'flank', '左齿向'),
        ('right', 'flank', '右齿向')
    ]
    
    fig = plt.figure(figsize=(20, 14))
    
    for idx, (side, data_type, name) in enumerate(directions):
        print(f"\n{'='*70}")
        print(f"【{name}】")
        print('='*70)
        
        # 获取数据
        if data_type == 'profile':
            data_dict = measurements.get('profile', {}).get(side, {})
            eval_start = profile_eval_start
            eval_end = profile_eval_end
        else:
            data_dict = measurements.get('flank', {}).get(side, {})
            eval_start = helix_eval_start
            eval_end = helix_eval_end
        
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
        
        # 构建闭合曲线（已包含鼓形和斜率剔除）
        angles, values = build_closed_curve(
            all_tooth_data, teeth_count, base_diameter, 
            data_type, eval_start, eval_end, helix_angle, pitch_diameter
        )
        
        if angles is None or len(angles) < 100:
            print(f"  闭合曲线构建失败")
            continue
        
        print(f"  闭合曲线点数: {len(angles)}")
        print(f"  数据范围: {np.min(values):.2f} ~ {np.max(values):.2f} μm")
        
        # 迭代最小二乘法提取前10个最大阶次
        print(f"\n  迭代提取前10个最大阶次正弦波...")
        components, residual = iterative_sine_decomposition(angles, values, teeth_count, max_components=10)
        
        print(f"\n  提取的10个最大阶次:")
        for i, comp in enumerate(components, 1):
            print(f"    {i}. 阶次 {comp['order']:3d}: 幅值 = {comp['amplitude']:.4f} μm, 相位 = {comp['phase']:.1f}°")
        
        # 计算高阶成分 (>= ZE)
        high_order_components = [c for c in components if c['order'] >= teeth_count]
        
        # 计算W值（高阶总振幅）
        w_value = sum(c['amplitude'] for c in high_order_components)
        
        # 计算RMS
        if high_order_components:
            rms_value = np.sqrt(np.mean([c['amplitude']**2 for c in high_order_components]))
        else:
            rms_value = 0
        
        print(f"\n  【高阶评价结果 (>= ZE={teeth_count})】")
        print(f"  高阶分量数: {len(high_order_components)}")
        print(f"  W值 (高阶总振幅): {w_value:.4f} μm")
        print(f"  RMS值: {rms_value:.4f} μm")
        
        # 绘制图形
        # 1. 闭合曲线
        ax1 = fig.add_subplot(4, 4, idx*4 + 1)
        ax1.plot(angles, values, 'b-', linewidth=0.5, alpha=0.7, label='Original')
        ax1.set_xlim(0, 360)
        ax1.set_xlabel('Rotation Angle (°)')
        ax1.set_ylabel('Deviation (μm)')
        ax1.set_title(f'{name}\nClosed Curve (After Crown/Slope Removal)')
        ax1.grid(True, alpha=0.3)
        
        # 2. 频谱图（前10个最大阶次）
        ax2 = fig.add_subplot(4, 4, idx*4 + 2)
        orders = [c['order'] for c in components]
        amplitudes = [c['amplitude'] for c in components]
        colors = ['red' if o >= teeth_count else 'blue' for o in orders]
        ax2.bar(range(1, 11), amplitudes, color=colors, alpha=0.7)
        ax2.set_xlabel('Rank')
        ax2.set_ylabel('Amplitude (μm)')
        ax2.set_title(f'Top 10 Components\n(Red: High Order >= {teeth_count})')
        ax2.set_xticks(range(1, 11))
        ax2.grid(True, alpha=0.3)
        
        # 3. 重构信号
        ax3 = fig.add_subplot(4, 4, idx*4 + 3)
        theta = np.radians(angles)
        reconstructed = np.zeros_like(values)
        for comp in components:
            reconstructed += comp['a'] * np.cos(comp['order'] * theta) + comp['b'] * np.sin(comp['order'] * theta)
        ax3.plot(angles, values, 'b-', linewidth=0.5, alpha=0.5, label='Original')
        ax3.plot(angles, reconstructed, 'r-', linewidth=1, alpha=0.8, label='Reconstructed (Top 10)')
        ax3.set_xlim(0, 360)
        ax3.set_xlabel('Rotation Angle (°)')
        ax3.set_ylabel('Deviation (μm)')
        ax3.set_title(f'Signal Reconstruction\n(W={w_value:.3f}μm)')
        ax3.legend(fontsize=8)
        ax3.grid(True, alpha=0.3)
        
        # 4. 残差
        ax4 = fig.add_subplot(4, 4, idx*4 + 4)
        ax4.plot(angles, residual, 'g-', linewidth=0.5, alpha=0.7)
        ax4.set_xlim(0, 360)
        ax4.set_xlabel('Rotation Angle (°)')
        ax4.set_ylabel('Deviation (μm)')
        ax4.set_title(f'Residual Signal\nRMS={rms_value:.3f}μm')
        ax4.grid(True, alpha=0.3)
        
        results[name] = {
            'w_value': w_value,
            'rms_value': rms_value,
            'components': components,
            'high_order_components': high_order_components
        }
    
    plt.tight_layout()
    plt.savefig('ripple_spectrum_analysis_v2.png', dpi=150, bbox_inches='tight')
    print(f"\n\n频谱分析图已保存: ripple_spectrum_analysis_v2.png")
    plt.show()
    
    return results


def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    results = analyze_ripple(mka_file)
    
    # 打印汇总
    print("\n" + "="*70)
    print("波纹度分析汇总")
    print("="*70)
    for name, data in results.items():
        print(f"\n{name}:")
        print(f"  W值: {data['w_value']:.4f} μm")
        print(f"  RMS: {data['rms_value']:.4f} μm")
        print(f"  高阶分量数: {len(data['high_order_components'])}")


if __name__ == "__main__":
    main()
