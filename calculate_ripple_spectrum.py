"""
使用实际MKA文件数据计算波纹度频谱
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


def calculate_involute_angle(radius, base_radius):
    """计算渐开线极角"""
    if radius <= base_radius or base_radius <= 0:
        return 0.0
    cos_alpha = base_radius / radius
    if cos_alpha >= 1.0:
        return 0.0
    alpha = math.acos(cos_alpha)
    return math.degrees(math.tan(alpha) - alpha)


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
        all_values.extend(tooth_data)
    
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


def calculate_spectrum(angles, values, teeth_count, max_order=None):
    """计算频谱"""
    if max_order is None:
        max_order = 5 * teeth_count
    
    # 插值到均匀角度
    num_pts = max(1024, len(values) * 2)
    interp_angles = np.linspace(0, 360, num_pts, endpoint=False)
    interp_values = np.interp(interp_angles, angles, values, period=360)
    
    # 去均值
    interp_values = interp_values - np.mean(interp_values)
    
    # 最小二乘法计算各阶次幅值
    theta = np.radians(interp_angles)
    spectrum = {}
    
    for order in range(1, max_order + 1):
        cos_x = np.cos(order * theta)
        sin_x = np.sin(order * theta)
        A = np.column_stack((cos_x, sin_x))
        coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
        a, b = coeffs
        amplitude = np.sqrt(a*a + b*b)
        spectrum[order] = amplitude
    
    return spectrum


def analyze_ripple(mka_file):
    """分析波纹度"""
    print("="*70)
    print("波纹度频谱分析")
    print("="*70)
    
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
    profile_eval_start = getattr(gear_data, 'profile_eval_start', 174.822)
    profile_eval_end = getattr(gear_data, 'profile_eval_end', 180.603)
    helix_eval_start = getattr(gear_data, 'helix_eval_start', 2.1)
    helix_eval_end = getattr(gear_data, 'helix_eval_end', 39.9)
    
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
    
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    
    for idx, (side, data_type, name) in enumerate(directions):
        print(f"\n【{name}】")
        
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
        
        # 构建闭合曲线
        angles, values = build_closed_curve(
            all_tooth_data, teeth_count, base_diameter, 
            data_type, eval_start, eval_end, helix_angle, pitch_diameter
        )
        
        if angles is None or len(angles) < 100:
            print(f"  闭合曲线构建失败")
            continue
        
        print(f"  闭合曲线点数: {len(angles)}")
        print(f"  数据范围: {np.min(values):.2f} ~ {np.max(values):.2f} μm")
        
        # 绘制闭合曲线
        ax_curve = axes[0, idx]
        ax_curve.plot(angles, values, linewidth=0.5, alpha=0.8)
        ax_curve.set_xlim(0, 360)
        ax_curve.set_xlabel('Rotation Angle (°)')
        ax_curve.set_ylabel('Deviation (μm)')
        ax_curve.set_title(f'{name}\nClosed Curve')
        ax_curve.grid(True, alpha=0.3)
        
        # 计算频谱
        spectrum = calculate_spectrum(angles, values, teeth_count)
        
        # 提取高阶成分 (>= ZE)
        high_order = {k: v for k, v in spectrum.items() if k >= teeth_count}
        
        # 计算W值 (高阶总振幅)
        w_value = sum(high_order.values())
        
        # 计算RMS
        rms_value = np.sqrt(np.mean(np.array(list(high_order.values()))**2))
        
        print(f"  W值 (高阶总振幅): {w_value:.4f} μm")
        print(f"  RMS值: {rms_value:.4f} μm")
        
        # 找出前5个最大幅值阶次
        top5 = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  前5阶幅值:")
        for order, amp in top5:
            print(f"    阶次 {order}: {amp:.4f} μm")
        
        # 绘制频谱
        ax_spec = axes[1, idx]
        orders = list(spectrum.keys())
        amplitudes = list(spectrum.values())
        
        # 只显示到5*ZE
        max_display = 5 * teeth_count
        mask = np.array(orders) <= max_display
        ax_spec.bar(np.array(orders)[mask], np.array(amplitudes)[mask], 
                   width=1, alpha=0.6, color='blue')
        
        # 标记ZE位置
        ax_spec.axvline(x=teeth_count, color='red', linestyle='--', 
                       linewidth=1, alpha=0.7, label=f'ZE={teeth_count}')
        
        # 标记高阶区域
        high_orders = [o for o in orders if o >= teeth_count and o <= max_display]
        high_amps = [spectrum[o] for o in high_orders]
        ax_spec.bar(high_orders, high_amps, width=1, alpha=0.8, color='red', label='High Order')
        
        ax_spec.set_xlabel('Order')
        ax_spec.set_ylabel('Amplitude (μm)')
        ax_spec.set_title(f'{name} Spectrum\nW={w_value:.3f}μm, RMS={rms_value:.3f}μm')
        ax_spec.legend(fontsize=8)
        ax_spec.grid(True, alpha=0.3)
        
        results[name] = {
            'w_value': w_value,
            'rms_value': rms_value,
            'top5': top5,
            'spectrum': spectrum
        }
    
    plt.tight_layout()
    plt.savefig('ripple_spectrum_analysis.png', dpi=150, bbox_inches='tight')
    print(f"\n频谱分析图已保存: ripple_spectrum_analysis.png")
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
