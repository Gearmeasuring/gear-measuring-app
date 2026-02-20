"""
波纹度频谱分析 V4 - 修正版
使用与Klingelnberg一致的方法：
1. RC低通滤波器
2. 只使用ZE整数倍作为候选阶次
3. 正确的闭合曲线构建
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


def apply_rc_low_pass_filter(data, fs=10000.0, ratio=1500.0):
    """
    Klingelnberg RC 低通滤波器
    
    Args:
        data: 输入数据
        fs: 采样频率 (默认10000)
        ratio: RC比值 (默认1500，对应报告中的100000:1的低通滤波)
    
    Returns:
        滤波后的数据
    """
    if data is None or len(data) <= 1:
        return data
    
    data = np.array(data, dtype=float)
    n = len(data)
    
    # 计算截止频率
    fc = fs / ratio  # fc = 10000 / 1500 ≈ 6.67 Hz
    
    # 计算RC时间常数
    dt = 1.0 / fs
    rc = 1.0 / (2.0 * np.pi * fc)
    
    # 计算滤波系数
    alpha = dt / (rc + dt)
    alpha = min(1.0, max(0.0, alpha))
    
    # 应用IIR滤波器
    y = np.zeros_like(data)
    y[0] = data[0]
    for i in range(1, n):
        y[i] = alpha * data[i] + (1.0 - alpha) * y[i - 1]
    
    return y


def remove_crown_and_slope(data):
    """
    剔除鼓形（二次多项式）和斜率偏差（一次多项式）
    """
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


def iterative_sine_fit_ze_multiples(angles, values, teeth_count, max_components=10):
    """
    迭代最小二乘法提取前N个最大阶次的正弦波
    **只使用ZE整数倍作为候选阶次** (与Klingelnberg一致)
    """
    theta = np.radians(angles)
    residual = np.array(values, dtype=float)
    residual = residual - np.mean(residual)
    
    components = []
    max_ze_multiple = 10  # 只考虑ZE的1-10倍
    
    for iteration in range(max_components):
        best_amplitude = 0
        best_order = 0
        best_coeffs = None
        
        # 只使用ZE整数倍作为候选阶次 (关键差异!)
        candidate_orders = [teeth_count * mult for mult in range(1, max_ze_multiple + 1)]
        
        for order in candidate_orders:
            if order in [c['order'] for c in components]:
                continue
            
            sin_x = np.sin(2.0 * np.pi * order * theta)
            cos_x = np.cos(2.0 * np.pi * order * theta)
            A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
            
            try:
                coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                a, b, c = coeffs
                amplitude = np.sqrt(a*a + b*b)
                
                if amplitude > best_amplitude:
                    best_amplitude = amplitude
                    best_order = order
                    best_coeffs = (a, b, c)
            except:
                continue
        
        if best_coeffs is None or best_amplitude < 0.001:
            break
        
        a, b, c = best_coeffs
        fitted_wave = a * np.sin(2.0 * np.pi * best_order * theta) + b * np.cos(2.0 * np.pi * best_order * theta) + c
        
        components.append({
            'order': best_order,
            'amplitude': best_amplitude,
            'a': a,
            'b': b
        })
        
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
        
        # 剔除鼓形和斜率偏差
        corrected_data = remove_crown_and_slope(tooth_data)
        
        tooth_center = tooth_idx * angle_per_tooth
        n_points = len(corrected_data)
        
        if data_type == 'profile':
            # Profile: 展长 → 旋转角
            roll_start = math.sqrt(max(0, (eval_start/2)**2 - (base_diameter/2)**2))
            roll_end = math.sqrt(max(0, (eval_end/2)**2 - (base_diameter/2)**2))
            roll_range = np.linspace(roll_start, roll_end, n_points)
            
            # 计算滚动角 ξ
            xi = (roll_range / base_circumference) * 360.0
            # 以齿中心为基准
            xi = xi - (xi[-1] - xi[0]) / 2
            
            # 添加齿位置偏移 tau
            tau = tooth_center
            alpha = xi + tau
        else:
            # Helix: 轴向位置 → 旋转角
            axial_range = np.linspace(eval_start, eval_end, n_points)
            z0 = (eval_start + eval_end) / 2
            tan_beta = math.tan(math.radians(helix_angle))
            
            # 计算轴向角度差 α₂ = 2×Δz×tan(β₀)/D₀
            alpha2 = np.degrees((2.0 * (axial_range - z0) * tan_beta) / pitch_diameter)
            
            # 滚动角 ξ = 0
            xi = 0.0
            # 添加齿位置偏移 tau
            tau = tooth_center
            alpha = xi + alpha2 + tau
        
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
    print("波纹度频谱分析 V4 (修正版)")
    print("="*70)
    print("\n修正内容:")
    print("1. 添加RC低通滤波器 (ratio=1500)")
    print("2. 只使用ZE整数倍作为候选阶次")
    print("3. 正确的闭合曲线构建")
    
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
    
    # 获取评价范围
    profile_eval_start = gear_data.get('profile_eval_start', 174.822)
    profile_eval_end = gear_data.get('profile_eval_end', 180.603)
    helix_eval_start = gear_data.get('helix_eval_start', 2.1)
    helix_eval_end = gear_data.get('helix_eval_end', 39.9)
    
    print(f"\n【齿轮参数】")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module} mm")
    print(f"  压力角 α = {pressure_angle}°")
    print(f"  螺旋角 β = {helix_angle}°")
    print(f"  节圆直径 d = {pitch_diameter:.4f} mm")
    print(f"  基圆直径 db = {base_diameter:.4f} mm")
    
    # 获取测量数据
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    results = {}
    
    # 分析四个方向
    directions = [
        ('left', 'profile', '左齿形', profile_data),
        ('right', 'profile', '右齿形', profile_data),
        ('left', 'flank', '左齿向', flank_data),
        ('right', 'flank', '右齿向', flank_data)
    ]
    
    fig = plt.figure(figsize=(20, 14))
    
    for idx, (side, data_type, name, data_source) in enumerate(directions):
        print(f"\n{'='*70}")
        print(f"【{name}】")
        print('='*70)
        
        # 获取数据
        if data_type == 'profile':
            data_dict = data_source.get(side, {})
            eval_start = profile_eval_start
            eval_end = profile_eval_end
        else:
            data_dict = data_source.get(side, {})
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
        
        # 构建闭合曲线
        angles, values = build_closed_curve(
            all_tooth_data, teeth_count, base_diameter, 
            data_type, eval_start, eval_end, helix_angle, pitch_diameter
        )
        
        if angles is None or len(angles) < 100:
            print(f"  闭合曲线构建失败")
            continue
        
        print(f"  闭合曲线点数: {len(angles)}")
        print(f"  数据范围 (滤波前): {np.min(values):.2f} ~ {np.max(values):.2f} μm")
        
        # 应用RC低通滤波器 (关键修正!)
        filtered_values = apply_rc_low_pass_filter(values, fs=10000.0, ratio=1500.0)
        print(f"  数据范围 (滤波后): {np.min(filtered_values):.2f} ~ {np.max(filtered_values):.2f} μm")
        
        # 迭代最小二乘法提取前10个最大阶次 (只使用ZE整数倍)
        print(f"\n  迭代提取前10个最大阶次正弦波 (只使用ZE整数倍)...")
        components, residual = iterative_sine_fit_ze_multiples(angles, filtered_values, teeth_count, max_components=10)
        
        print(f"\n  提取的阶次 (ZE整数倍):")
        for i, comp in enumerate(components, 1):
            print(f"    {i}. 阶次 {comp['order']:3d} (ZE×{comp['order']//teeth_count}): 幅值 = {comp['amplitude']:.4f} μm")
        
        # 计算W值（高阶总振幅）
        w_value = sum(c['amplitude'] for c in components)
        
        # 计算RMS
        if components:
            rms_value = np.sqrt(np.mean([c['amplitude']**2 for c in components]))
        else:
            rms_value = 0
        
        print(f"\n  【评价结果】")
        print(f"  W值 (总振幅): {w_value:.4f} μm")
        print(f"  RMS值: {rms_value:.4f} μm")
        
        # 绘制图形
        ax1 = fig.add_subplot(4, 4, idx*4 + 1)
        ax1.plot(angles, values, 'b-', linewidth=0.5, alpha=0.7, label='Before Filter')
        ax1.plot(angles, filtered_values, 'r-', linewidth=0.5, alpha=0.7, label='After RC Filter')
        ax1.set_xlim(0, 360)
        ax1.set_xlabel('Rotation Angle (°)')
        ax1.set_ylabel('Deviation (μm)')
        ax1.set_title(f'{name}\nClosed Curve')
        ax1.legend(fontsize=7)
        ax1.grid(True, alpha=0.3)
        
        # 频谱图
        ax2 = fig.add_subplot(4, 4, idx*4 + 2)
        ze_multiples = [c['order'] // teeth_count for c in components]
        amplitudes = [c['amplitude'] for c in components]
        ax2.bar(range(1, len(amplitudes)+1), amplitudes, color='blue', alpha=0.7)
        ax2.set_xlabel('ZE Multiple')
        ax2.set_ylabel('Amplitude (μm)')
        ax2.set_title(f'Spectrum (ZE Multiples Only)')
        ax2.set_xticks(range(1, len(amplitudes)+1))
        ax2.set_xticklabels([f'{m}×ZE' for m in ze_multiples], fontsize=7)
        ax2.grid(True, alpha=0.3)
        
        # 重构信号
        ax3 = fig.add_subplot(4, 4, idx*4 + 3)
        theta = np.radians(angles)
        reconstructed = np.zeros_like(filtered_values)
        for comp in components:
            reconstructed += comp['a'] * np.sin(2.0 * np.pi * comp['order'] * theta) + comp['b'] * np.cos(2.0 * np.pi * comp['order'] * theta)
        ax3.plot(angles, filtered_values, 'b-', linewidth=0.5, alpha=0.5, label='Filtered')
        ax3.plot(angles, reconstructed, 'r-', linewidth=1, alpha=0.8, label='Reconstructed')
        ax3.set_xlim(0, 360)
        ax3.set_xlabel('Rotation Angle (°)')
        ax3.set_ylabel('Deviation (μm)')
        ax3.set_title(f'Signal Reconstruction\n(W={w_value:.3f}μm)')
        ax3.legend(fontsize=7)
        ax3.grid(True, alpha=0.3)
        
        # 残差
        ax4 = fig.add_subplot(4, 4, idx*4 + 4)
        ax4.plot(angles, residual, 'g-', linewidth=0.5, alpha=0.7)
        ax4.set_xlim(0, 360)
        ax4.set_xlabel('Rotation Angle (°)')
        ax4.set_ylabel('Deviation (μm)')
        ax4.set_title(f'Residual Signal')
        ax4.grid(True, alpha=0.3)
        
        results[name] = {
            'w_value': w_value,
            'rms_value': rms_value,
            'components': components
        }
    
    plt.tight_layout()
    plt.savefig('ripple_spectrum_analysis_v4.png', dpi=150, bbox_inches='tight')
    print(f"\n\n频谱分析图已保存: ripple_spectrum_analysis_v4.png")
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


if __name__ == "__main__":
    main()
