"""
按PDF参数合并曲线后计算频谱并可视化
"""
import os
import sys
import numpy as np
import math
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def calculate_involute_angle(base_radius, radius):
    """计算渐开线极角"""
    if radius <= base_radius or base_radius <= 0:
        return 0.0
    cos_alpha = base_radius / radius
    if cos_alpha >= 1.0:
        return 0.0
    alpha = math.acos(cos_alpha)
    return math.degrees(math.tan(alpha) - alpha)


def preprocess_tooth_data(values, order=2):
    """预处理"""
    if len(values) < order + 1:
        return values - np.mean(values)
    
    n = len(values)
    x = np.arange(n)
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    coeffs = np.polyfit(x_norm, values, order)
    trend = np.polyval(coeffs, x_norm)
    
    return values - trend


def build_profile_curve_with_ep(gear_data, profile_data, side, ep):
    """使用ep参数构建齿形合并曲线"""
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_radius = base_diameter / 2.0
    base_pitch = math.pi * base_diameter / teeth_count
    pitch_angle = 360.0 / teeth_count
    
    side_data = profile_data.get(side, {})
    if not side_data:
        return None, None
    
    sorted_teeth = sorted(side_data.keys())
    
    all_angles = []
    all_values = []
    
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        n = len(values)
        
        corrected_values = preprocess_tooth_data(values, order=2)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        
        if eval_start > 0 and eval_end > 0:
            radii = np.linspace(eval_start/2, eval_end/2, n)
        else:
            radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, n)
        
        xi_angles = np.array([calculate_involute_angle(base_radius, r) for r in radii])
        
        if side == 'left':
            angles = tau - xi_angles
        else:
            angles = tau + xi_angles
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    if not all_angles:
        return None, None
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    
    all_angles = all_angles % 360.0
    sort_idx = np.argsort(all_angles)
    
    return all_angles[sort_idx], all_values[sort_idx]


def build_helix_curve_with_el(gear_data, flank_data, side, el):
    """使用el参数构建齿向合并曲线"""
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    pitch_diameter = module * teeth_count
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_pitch = math.pi * base_diameter / teeth_count
    pitch_angle = 360.0 / teeth_count
    
    helix_angle_base = math.degrees(math.atan(
        math.tan(math.radians(helix_angle)) * math.cos(math.radians(pressure_angle))
    ))
    
    eval_length = abs(el) * base_pitch
    
    side_data = flank_data.get(side, {})
    if not side_data:
        return None, None
    
    sorted_teeth = sorted(side_data.keys())
    
    all_angles = []
    all_values = []
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    eval_center = (helix_eval_start + helix_eval_end) / 2.0
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        n = len(values)
        
        corrected_values = preprocess_tooth_data(values, order=2)
        
        axial_positions = np.linspace(helix_eval_start, helix_eval_end, n)
        delta_z = axial_positions - eval_center
        
        if abs(helix_angle_base) > 0.01:
            delta_phi = (delta_z / eval_length) * el * (360.0 / teeth_count)
        else:
            delta_phi = np.zeros(n)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        
        if side == 'left':
            angles = tau - delta_phi
        else:
            angles = tau + delta_phi
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    if not all_angles:
        return None, None
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    
    all_angles = all_angles % 360.0
    sort_idx = np.argsort(all_angles)
    
    return all_angles[sort_idx], all_values[sort_idx]


def compute_spectrum(angles, values, max_order):
    """计算频谱"""
    if angles is None or values is None:
        return None, None
    
    unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
    unique_values = values[unique_indices]
    
    num_points = 2048
    interp_angles = np.linspace(0, 360, num_points, endpoint=False)
    interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
    
    theta = np.radians(interp_angles)
    
    orders = np.arange(1, max_order + 1)
    amplitudes = []
    
    for order in orders:
        cos_x = np.cos(order * theta)
        sin_x = np.sin(order * theta)
        A = np.column_stack((cos_x, sin_x))
        coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
        a, b = coeffs
        amplitude = np.sqrt(a*a + b*b)
        amplitudes.append(amplitude)
    
    return orders, np.array(amplitudes)


def plot_spectrum_with_pdf_params(mka_file, sample_name, klingelnberg_ref):
    """使用PDF参数计算并绘制频谱"""
    print(f"\n{'='*90}")
    print(f"Spectrum Analysis with PDF Parameters: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    ep = 1.454
    el = 2.766
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}, Helix={helix_angle}°")
    print(f"PDF Parameters: ep={ep}, el={el}")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{sample_name} - Spectrum Analysis (PDF params: ep={ep}, el={el})', fontsize=14)
    
    max_order = 5 * teeth_count
    
    for idx, (side, ax_row) in enumerate(zip(['right', 'left'], axes)):
        for col, (data_type, ax) in enumerate(zip(['profile', 'helix'], ax_row)):
            direction = f'{side}_{data_type}'
            
            if data_type == 'profile':
                angles, values = build_profile_curve_with_ep(gear_data, profile_data, side, ep)
                title = f'{side.capitalize()} Profile Spectrum'
            else:
                angles, values = build_helix_curve_with_el(gear_data, flank_data, side, el)
                title = f'{side.capitalize()} Helix Spectrum'
            
            if angles is None:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(title)
                continue
            
            orders, amplitudes = compute_spectrum(angles, values, max_order)
            
            # 绘制频谱
            ax.bar(orders, amplitudes, width=1.0, color='steelblue', alpha=0.7)
            
            # 标记ZE整数倍的阶次
            for mult in range(1, 6):
                ze_order = teeth_count * mult
                if ze_order <= max_order:
                    ax.axvline(x=ze_order, color='red', linestyle='--', alpha=0.5, linewidth=1)
                    ax.text(ze_order, ax.get_ylim()[1] * 0.95, f'{ze_order}', 
                           ha='center', fontsize=8, color='red')
            
            # 标记Klingelnberg参考值
            if direction in klingelnberg_ref:
                ref = klingelnberg_ref[direction]
                scale = 0.109 if data_type == 'profile' else 0.05
                
                for order, ref_amp in ref.items():
                    if order <= max_order:
                        ax.scatter([order], [ref_amp / scale], color='green', s=100, 
                                  marker='*', zorder=5, label='Klingelnberg' if order == list(ref.keys())[0] else '')
            
            ax.set_xlabel('Order')
            ax.set_ylabel('Amplitude (um)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, max_order)
            
            # 显示统计信息
            print(f"\n{title}:")
            print(f"  Max amplitude: {np.max(amplitudes):.4f} um at order {orders[np.argmax(amplitudes)]}")
            print(f"  Mean amplitude: {np.mean(amplitudes):.4f} um")
            
            # 显示Klingelnberg参考值对比
            if direction in klingelnberg_ref:
                ref = klingelnberg_ref[direction]
                scale = 0.109 if data_type == 'profile' else 0.05
                
                print(f"  Comparison with Klingelnberg:")
                print(f"    {'Order':<8} {'Ours':<12} {'Scaled':<12} {'Klingelnberg':<12} {'Error':<10}")
                for order in sorted(ref.keys()):
                    if order <= max_order:
                        idx = order - 1
                        our_amp = amplitudes[idx]
                        scaled_amp = our_amp * scale
                        ref_amp = ref[order]
                        error = abs(scaled_amp - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
                        print(f"    {order:<8} {our_amp:<12.4f} {scaled_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")
    
    plt.tight_layout()
    
    output_file = mka_file.replace('.mka', '_spectrum.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nSaved: {output_file}")
    
    plt.show()
    
    return output_file


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    KLINGELNBERG_SAMPLE1 = {
        'right_profile': {87: 0.1500, 174: 0.0500, 261: 0.0600, 348: 0.0700, 435: 0.0300},
        'left_profile': {87: 0.1400, 174: 0.0500, 261: 0.0600, 348: 0.0300, 435: 0.0400},
        'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300},
        'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300}
    }
    
    plot_spectrum_with_pdf_params(sample1_file, "Sample1 (ZE=87)", KLINGELNBERG_SAMPLE1)


if __name__ == "__main__":
    main()
