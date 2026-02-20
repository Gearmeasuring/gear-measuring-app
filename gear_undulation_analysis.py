"""
齿轮波纹度分析 - 齿形和齿向数据处理
生成左齿形、右齿形、左齿向、右齿向的图表
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import MKAFileParser, parse_mka_file


def calculate_involute_polar_angle(radius: float, base_radius: float) -> float:
    """计算渐开线上某点的极角（involute function）
    
    inv(α) = tan(α) - α
    其中 α = arccos(rb/r)
    """
    if radius <= base_radius or base_radius <= 0:
        return 0.0
    
    cos_alpha = base_radius / radius
    if cos_alpha >= 1.0:
        return 0.0
    
    alpha = np.arccos(cos_alpha)
    polar_angle = np.tan(alpha) - alpha
    
    return polar_angle


def remove_slope_and_crowning(data: np.ndarray, x: np.ndarray = None) -> tuple:
    """去除斜率偏差和鼓形
    
    分两步处理：
    1. 先用二元二次多项式（抛物线）去除鼓形
    2. 再用一元一次多项式（线性）去除斜率偏差
    """
    if len(data) < 3:
        return data, (None, None)
    
    data = np.array(data, dtype=float)
    n = len(data)
    
    if x is None:
        x = np.arange(n, dtype=float)
    else:
        x = np.array(x, dtype=float)
    
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    crowning_coeffs = np.polyfit(x_norm, data, 2)
    crowning_curve = np.polyval(crowning_coeffs, x_norm)
    data_after_crowning = data - crowning_curve
    
    slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
    slope_curve = np.polyval(slope_coeffs, x_norm)
    corrected_data = data_after_crowning - slope_curve
    
    return corrected_data, (crowning_coeffs, slope_coeffs)


def fit_sine_wave_least_squares(angles: np.ndarray, values: np.ndarray, order: int) -> dict:
    """使用最小二乘法拟合指定阶次的正弦波"""
    angles = np.array(angles, dtype=float)
    values = np.array(values, dtype=float)
    
    cos_term = np.cos(order * angles)
    sin_term = np.sin(order * angles)
    
    A = np.column_stack([cos_term, sin_term])
    coeffs, residuals, rank, s = np.linalg.lstsq(A, values, rcond=None)
    
    a, b = coeffs[0], coeffs[1]
    amplitude = np.sqrt(a**2 + b**2)
    phase = np.arctan2(a, b)
    
    fitted = a * cos_term + b * sin_term
    residual = values - fitted
    
    return {
        'amplitude': amplitude,
        'phase': phase,
        'fitted': fitted,
        'residual': residual,
        'coefficients': (a, b)
    }


def find_max_amplitude_order(angles: np.ndarray, values: np.ndarray, 
                              max_order: int = 50, min_order: int = 1,
                              excluded_orders: set = None) -> dict:
    """寻找振幅最大的阶次"""
    if excluded_orders is None:
        excluded_orders = set()
    
    best_order = min_order
    best_amplitude = 0
    best_result = None
    
    for order in range(min_order, max_order + 1):
        if order in excluded_orders:
            continue
        result = fit_sine_wave_least_squares(angles, values, order)
        if result['amplitude'] > best_amplitude:
            best_amplitude = result['amplitude']
            best_order = order
            best_result = result
    
    return {
        'order': best_order,
        'amplitude': best_amplitude,
        'fit_result': best_result
    }


def iterative_sine_decomposition(angles: np.ndarray, values: np.ndarray, 
                                  num_components: int = 10, max_order: int = 50) -> dict:
    """迭代正弦波分解算法"""
    angles = np.array(angles, dtype=float)
    residual = np.array(values, dtype=float)
    
    orders = []
    amplitudes = []
    phases = []
    components = []
    extracted_orders = set()
    
    for i in range(num_components):
        result = find_max_amplitude_order(angles, residual, max_order, min_order=1,
                                          excluded_orders=extracted_orders)
        
        order = result['order']
        extracted_orders.add(order)
        
        fit_result = fit_sine_wave_least_squares(angles, residual, order)
        
        orders.append(order)
        amplitudes.append(fit_result['amplitude'])
        phases.append(fit_result['phase'])
        components.append(fit_result['fitted'])
        
        residual = fit_result['residual']
    
    reconstructed = np.zeros_like(values)
    for comp in components:
        reconstructed += comp
    
    return {
        'orders': np.array(orders),
        'amplitudes': np.array(amplitudes),
        'phases': np.array(phases),
        'components': components,
        'residual': residual,
        'original': np.array(values),
        'reconstructed': reconstructed
    }


def calculate_high_order_undulation(spectrum_result: dict, ze: int) -> dict:
    """计算高阶波纹度（波数≥ZE的分量）"""
    orders = spectrum_result['orders']
    amplitudes = spectrum_result['amplitudes']
    phases = spectrum_result['phases']
    components = spectrum_result['components']
    
    high_order_mask = orders >= ze
    
    high_order_indices = np.where(high_order_mask)[0]
    high_order_waves = orders[high_order_mask]
    high_order_amplitudes = amplitudes[high_order_mask]
    high_order_phases = phases[high_order_mask]
    
    high_order_reconstructed = np.zeros_like(spectrum_result['original'])
    for idx in high_order_indices:
        if idx < len(components):
            high_order_reconstructed += components[idx]
    
    total_amplitude = np.sum(high_order_amplitudes)
    rms = np.sqrt(np.mean(high_order_reconstructed ** 2))
    
    return {
        'high_order_indices': high_order_indices,
        'high_order_waves': high_order_waves,
        'high_order_amplitudes': high_order_amplitudes,
        'high_order_phases': high_order_phases,
        'total_high_order_amplitude': total_amplitude,
        'high_order_rms': rms,
        'high_order_reconstructed': high_order_reconstructed,
        'ze': ze
    }


def process_profile_data(profile_data: dict, side: str, teeth_count: int, module: float,
                         pressure_angle: float, base_diameter: float,
                         eval_start_diameter: float, eval_end_diameter: float,
                         meas_start_diameter: float, meas_end_diameter: float) -> dict:
    """处理齿形数据"""
    if side not in profile_data or not profile_data[side]:
        return None
    
    pitch_radius = module * teeth_count / 2.0
    if base_diameter and base_diameter > 0:
        base_radius = base_diameter / 2.0
    else:
        base_radius = pitch_radius * np.cos(np.radians(pressure_angle))
    
    pitch_angle_deg = 360.0 / teeth_count
    
    side_data = profile_data[side]
    sorted_teeth = sorted(side_data.keys())
    
    first_tooth_values = side_data[sorted_teeth[0]]
    num_points = len(first_tooth_values)
    
    if meas_start_diameter > 0 and meas_end_diameter > 0:
        meas_start_radius = meas_start_diameter / 2.0
        meas_end_radius = meas_end_diameter / 2.0
        meas_start_polar = calculate_involute_polar_angle(meas_start_radius, base_radius)
        meas_end_polar = calculate_involute_polar_angle(meas_end_radius, base_radius)
    else:
        return None
    
    if eval_start_diameter > 0 and eval_end_diameter > 0:
        eval_start_radius = eval_start_diameter / 2.0
        eval_end_radius = eval_end_diameter / 2.0
        eval_start_polar = calculate_involute_polar_angle(eval_start_radius, base_radius)
        eval_end_polar = calculate_involute_polar_angle(eval_end_radius, base_radius)
    else:
        eval_start_polar = meas_start_polar
        eval_end_polar = meas_end_polar
    
    start_polar_angle = eval_start_polar
    
    point_polar_angles = np.linspace(meas_start_polar, meas_end_polar, num_points)
    
    eval_start_idx = np.argmin(np.abs(point_polar_angles - eval_start_polar))
    eval_end_idx = np.argmin(np.abs(point_polar_angles - eval_end_polar)) + 1
    
    if eval_start_idx >= eval_end_idx:
        eval_start_idx = 0
        eval_end_idx = num_points
    
    all_angles = []
    all_values = []
    all_tooth_indices = []
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        tooth_values = np.array(tooth_values)
        actual_points = len(tooth_values)
        
        current_eval_start = int(eval_start_idx * actual_points / num_points)
        current_eval_end = int(eval_end_idx * actual_points / num_points)
        
        tooth_values = tooth_values[current_eval_start:current_eval_end]
        actual_points = len(tooth_values)
        
        corrected_values, _ = remove_slope_and_crowning(tooth_values)
        
        current_polar_angles = np.linspace(meas_start_polar, meas_end_polar, len(side_data[tooth_id]))
        current_polar_angles = current_polar_angles[current_eval_start:current_eval_end]
        current_polar_angles_deg = np.degrees(current_polar_angles - start_polar_angle)
        
        tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
        if tooth_index < 0:
            tooth_index = 0
        if tooth_index >= teeth_count:
            tooth_index = teeth_count - 1
        
        tooth_base_angle = tooth_index * pitch_angle_deg
        
        if side == 'left':
            final_angles = tooth_base_angle - current_polar_angles_deg
        else:
            final_angles = tooth_base_angle + current_polar_angles_deg
        
        all_angles.extend(final_angles.tolist())
        all_values.extend(corrected_values.tolist())
        all_tooth_indices.extend([tooth_id] * actual_points)
    
    if not all_angles:
        return None
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    all_tooth_indices = np.array(all_tooth_indices)
    
    all_angles = all_angles % 360.0
    all_angles[all_angles < 0] += 360.0
    
    sort_indices = np.argsort(all_angles)
    all_angles = all_angles[sort_indices]
    all_values = all_values[sort_indices]
    all_tooth_indices = all_tooth_indices[sort_indices]
    
    return {
        'angles': all_angles,
        'values': all_values,
        'tooth_indices': all_tooth_indices,
        'side': side,
        'type': 'profile'
    }


def process_helix_data(helix_data: dict, side: str, teeth_count: int, module: float,
                       helix_angle: float, pitch_diameter: float,
                       eval_start: float, eval_end: float,
                       meas_start: float, meas_end: float) -> dict:
    """处理齿向数据
    
    使用标准公式计算轴向旋转角度:
    Δφ = 2 × Δz × tan(β₀) / D₀
    其中:
    - Δz: 相对于评价范围中心的轴向距离
    - β₀: 节圆处的螺旋角
    - D₀: 节圆直径
    
    最终旋转角度: φ = -Δφ + τ (对于齿向，ξ = 0)
    其中 τ 是节距角 = 齿序号 × 360° / 齿数
    """
    if side not in helix_data or not helix_data[side]:
        return None
    
    pitch_angle_deg = 360.0 / teeth_count
    
    side_data = helix_data[side]
    sorted_teeth = sorted(side_data.keys())
    
    first_tooth_values = side_data[sorted_teeth[0]]
    num_points = len(first_tooth_values)
    
    if meas_start > 0 and meas_end > 0:
        meas_length = meas_end - meas_start
    else:
        meas_length = 10.0
    
    if eval_start > 0 and eval_end > 0:
        eval_length = eval_end - eval_start
        eval_start_pos = eval_start - meas_start
    else:
        eval_length = meas_length
        eval_start_pos = 0
    
    eval_start_idx = int(num_points * eval_start_pos / meas_length)
    eval_end_idx = int(num_points * (eval_start_pos + eval_length) / meas_length)
    
    if eval_start_idx >= eval_end_idx:
        eval_start_idx = 0
        eval_end_idx = num_points
    
    # 计算评价范围中心位置
    eval_center_pos = eval_start_pos + eval_length / 2.0
    
    all_angles = []
    all_values = []
    all_tooth_indices = []
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        tooth_values = np.array(tooth_values)
        actual_points = len(tooth_values)
        
        current_eval_start = int(eval_start_idx * actual_points / num_points)
        current_eval_end = int(eval_end_idx * actual_points / num_points)
        
        tooth_values = tooth_values[current_eval_start:current_eval_end]
        actual_points = len(tooth_values)
        
        corrected_values, _ = remove_slope_and_crowning(tooth_values)
        
        if abs(helix_angle) > 0.01 and pitch_diameter > 0:
            # 生成相对于评价范围起点的位置数组
            point_positions = np.linspace(eval_start_pos, eval_start_pos + eval_length, actual_points)
            # 计算相对于中心的轴向距离 Δz
            delta_z = point_positions - eval_center_pos
            # 使用标准公式计算轴向旋转角度 Δφ = 2 × Δz × tan(β₀) / D₀
            tan_beta0 = np.tan(np.radians(helix_angle))
            delta_phi_rad = 2 * delta_z * tan_beta0 / pitch_diameter
            polar_angles_deg = np.degrees(delta_phi_rad)
        else:
            polar_angles_deg = np.linspace(0, eval_length * 0.1, actual_points)
        
        tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
        if tooth_index < 0:
            tooth_index = 0
        if tooth_index >= teeth_count:
            tooth_index = teeth_count - 1
        
        # 计算节距角 τ
        tooth_base_angle = tooth_index * pitch_angle_deg
        
        # 根据公式 φ = -Δφ + τ 计算最终角度
        if side == 'left':
            final_angles = tooth_base_angle - polar_angles_deg
        else:
            final_angles = tooth_base_angle + polar_angles_deg
        
        all_angles.extend(final_angles.tolist())
        all_values.extend(corrected_values.tolist())
        all_tooth_indices.extend([tooth_id] * actual_points)
    
    if not all_angles:
        return None
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    all_tooth_indices = np.array(all_tooth_indices)
    
    all_angles = all_angles % 360.0
    all_angles[all_angles < 0] += 360.0
    
    sort_indices = np.argsort(all_angles)
    all_angles = all_angles[sort_indices]
    all_values = all_values[sort_indices]
    all_tooth_indices = all_tooth_indices[sort_indices]
    
    return {
        'angles': all_angles,
        'values': all_values,
        'tooth_indices': all_tooth_indices,
        'side': side,
        'type': 'helix'
    }


def analyze_spectrum(curve_data: dict, teeth_count: int) -> dict:
    """分析频谱"""
    if curve_data is None or len(curve_data['angles']) == 0:
        return None
    
    angles = curve_data['angles']
    values = curve_data['values']
    
    unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
    unique_values = values[unique_indices]
    
    max_order = 5 * teeth_count
    num_interp_points = max(360, 2 * max_order + 10)
    interp_angles = np.linspace(0, 360, num_interp_points)
    interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
    
    angles_rad = np.radians(interp_angles)
    
    spectrum = iterative_sine_decomposition(angles_rad, interp_values, 
                                            num_components=10, max_order=max_order)
    
    high_order = calculate_high_order_undulation(spectrum, teeth_count)
    
    return {
        'spectrum': spectrum,
        'high_order': high_order,
        'interp_angles': interp_angles,
        'interp_values': interp_values
    }


def plot_curve_and_spectrum(curve_data: dict, spectrum_data: dict, teeth_count: int,
                            title: str, output_file: str):
    """绘制曲线和频谱分析图"""
    if curve_data is None or spectrum_data is None:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(title, fontsize=14, fontweight='bold')
    
    ax_curve = axes[0, 0]
    ax_curve.scatter(curve_data['angles'], curve_data['values'], 
                    c=curve_data['tooth_indices'], cmap='tab20', s=2, alpha=0.7)
    ax_curve.set_xlabel('Rotation Angle (deg)')
    ax_curve.set_ylabel('Deviation (um)')
    ax_curve.set_title(f'Full Rotation Curve - {len(curve_data["angles"])} points')
    ax_curve.set_xlim(0, 360)
    ax_curve.grid(True, alpha=0.3)
    
    ax_spectrum = axes[0, 1]
    spectrum = spectrum_data['spectrum']
    orders = spectrum['orders']
    amplitudes = spectrum['amplitudes']
    
    bar_colors = ['red' if o >= teeth_count else 'steelblue' for o in orders]
    bars = ax_spectrum.bar(range(len(orders)), amplitudes, color=bar_colors, alpha=0.8)
    ax_spectrum.set_xlabel('Component Index')
    ax_spectrum.set_ylabel('Amplitude (um)')
    ax_spectrum.set_title(f'Top 10 Waves per Revolution\n(Red: High Order ≥{teeth_count})')
    ax_spectrum.set_xticks(range(len(orders)))
    ax_spectrum.set_xticklabels([f'{o}' for o in orders])
    ax_spectrum.grid(True, alpha=0.3, axis='y')
    
    ax_signal = axes[1, 0]
    interp_angles = spectrum_data['interp_angles']
    interp_values = spectrum_data['interp_values']
    ax_signal.plot(interp_angles, interp_values, 'b-', alpha=0.5, label='Original', linewidth=1)
    ax_signal.plot(interp_angles, spectrum['reconstructed'], 'r-', alpha=0.8, 
                  label='Reconstructed', linewidth=1.5)
    high_order = spectrum_data['high_order']
    ax_signal.plot(interp_angles, high_order['high_order_reconstructed'], 'g-', alpha=0.8,
                  label=f'High Order (≥{teeth_count})', linewidth=1.5)
    ax_signal.set_xlabel('Rotation Angle (deg)')
    ax_signal.set_ylabel('Deviation (um)')
    ax_signal.set_title('Original vs Reconstructed')
    ax_signal.set_xlim(0, 360)
    ax_signal.grid(True, alpha=0.3)
    ax_signal.legend(loc='upper right', fontsize=8)
    
    ax_info = axes[1, 1]
    ax_info.axis('off')
    
    info_text = f"""Spectrum Analysis Results:
    
Top 10 Waves:
"""
    for i, (order, amp, phase) in enumerate(zip(orders, amplitudes, spectrum['phases'])):
        info_text += f"  {order} waves/rev: {amp:.4f} um, {np.degrees(phase):.1f}°\n"
    
    info_text += f"""
High Order Undulation (≥{teeth_count}):
  Waves: {list(high_order['high_order_waves'])}
  Total Amplitude: {high_order['total_high_order_amplitude']:.4f} um
  RMS: {high_order['high_order_rms']:.4f} um
"""
    
    ax_info.text(0.1, 0.9, info_text, transform=ax_info.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_file}")


def main():
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print(f"读取文件: {mka_file}")
    
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    helix_data = parsed_data.get('flank_data', {})
    
    module = gear_data.get('module', 0)
    teeth_count = gear_data.get('teeth', 0)
    pressure_angle = gear_data.get('pressure_angle', 20)
    base_diameter = gear_data.get('base_diameter', 0)
    helix_angle = gear_data.get('helix_angle', 0)
    pitch_diameter = module * teeth_count
    
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    helix_meas_start = gear_data.get('helix_meas_start', 0)
    helix_meas_end = gear_data.get('helix_meas_end', 0)
    
    print(f"\n齿轮参数:")
    print(f"  模数: {module} mm")
    print(f"  齿数: {teeth_count}")
    print(f"  压力角: {pressure_angle}°")
    print(f"  螺旋角: {helix_angle}°")
    print(f"  基圆直径: {base_diameter} mm")
    print(f"  节圆直径: {pitch_diameter} mm")
    
    print(f"\n数据统计:")
    print(f"  齿形数据: 左{len(profile_data.get('left', {}))}齿, 右{len(profile_data.get('right', {}))}齿")
    print(f"  齿向数据: 左{len(helix_data.get('left', {}))}齿, 右{len(helix_data.get('right', {}))}齿")
    
    results = {}
    
    print(f"\n处理齿形数据...")
    
    left_profile = process_profile_data(
        profile_data, 'left', teeth_count, module, pressure_angle, base_diameter,
        profile_eval_start, profile_eval_end, profile_meas_start, profile_meas_end
    )
    if left_profile:
        results['left_profile'] = {
            'curve': left_profile,
            'spectrum': analyze_spectrum(left_profile, teeth_count)
        }
        print(f"  左齿形: {len(left_profile['angles'])} 点")
    
    right_profile = process_profile_data(
        profile_data, 'right', teeth_count, module, pressure_angle, base_diameter,
        profile_eval_start, profile_eval_end, profile_meas_start, profile_meas_end
    )
    if right_profile:
        results['right_profile'] = {
            'curve': right_profile,
            'spectrum': analyze_spectrum(right_profile, teeth_count)
        }
        print(f"  右齿形: {len(right_profile['angles'])} 点")
    
    print(f"\n处理齿向数据...")
    
    left_helix = process_helix_data(
        helix_data, 'left', teeth_count, module, helix_angle, pitch_diameter,
        helix_eval_start, helix_eval_end, helix_meas_start, helix_meas_end
    )
    if left_helix:
        results['left_helix'] = {
            'curve': left_helix,
            'spectrum': analyze_spectrum(left_helix, teeth_count)
        }
        print(f"  左齿向: {len(left_helix['angles'])} 点")
    
    right_helix = process_helix_data(
        helix_data, 'right', teeth_count, module, helix_angle, pitch_diameter,
        helix_eval_start, helix_eval_end, helix_meas_start, helix_meas_end
    )
    if right_helix:
        results['right_helix'] = {
            'curve': right_helix,
            'spectrum': analyze_spectrum(right_helix, teeth_count)
        }
        print(f"  右齿向: {len(right_helix['angles'])} 点")
    
    print(f"\n生成图表...")
    
    if 'left_profile' in results:
        plot_curve_and_spectrum(
            results['left_profile']['curve'],
            results['left_profile']['spectrum'],
            teeth_count,
            f'Left Profile (Involute) - z={teeth_count}, m={module}',
            os.path.join(current_dir, 'left_profile_analysis.png')
        )
    
    if 'right_profile' in results:
        plot_curve_and_spectrum(
            results['right_profile']['curve'],
            results['right_profile']['spectrum'],
            teeth_count,
            f'Right Profile (Involute) - z={teeth_count}, m={module}',
            os.path.join(current_dir, 'right_profile_analysis.png')
        )
    
    if 'left_helix' in results:
        plot_curve_and_spectrum(
            results['left_helix']['curve'],
            results['left_helix']['spectrum'],
            teeth_count,
            f'Left Helix - z={teeth_count}, m={module}, β={helix_angle}°',
            os.path.join(current_dir, 'left_helix_analysis.png')
        )
    
    if 'right_helix' in results:
        plot_curve_and_spectrum(
            results['right_helix']['curve'],
            results['right_helix']['spectrum'],
            teeth_count,
            f'Right Helix - z={teeth_count}, m={module}, β={helix_angle}°',
            os.path.join(current_dir, 'right_helix_analysis.png')
        )
    
    print(f"\n分析完成！")
    
    for name, data in results.items():
        if data and data.get('spectrum'):
            spectrum = data['spectrum']['spectrum']
            high_order = data['spectrum']['high_order']
            print(f"\n{name}:")
            print(f"  前3波数: {list(spectrum['orders'][:3])}")
            print(f"  前3振幅: {[f'{a:.4f}' for a in spectrum['amplitudes'][:3]]}")
            print(f"  高阶总振幅: {high_order['total_high_order_amplitude']:.4f} um")
            print(f"  高阶RMS: {high_order['high_order_rms']:.4f} um")


if __name__ == '__main__':
    main()
