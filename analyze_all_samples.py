"""
分析两个样本的全部数据
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


def build_merged_curve(gear_data, data, side, data_type, ep_or_el):
    """构建合并曲线"""
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_radius = base_diameter / 2.0
    base_pitch = math.pi * base_diameter / teeth_count
    pitch_angle = 360.0 / teeth_count
    
    helix_angle_base = math.degrees(math.atan(
        math.tan(math.radians(helix_angle)) * math.cos(math.radians(pressure_angle))
    )) if abs(helix_angle) > 0.01 else 0.0
    
    side_data = data.get(side, {})
    if not side_data:
        return None, None
    
    sorted_teeth = sorted(side_data.keys())
    
    all_angles = []
    all_values = []
    
    if data_type == 'profile':
        eval_start = gear_data.get('profile_eval_start', 0)
        eval_end = gear_data.get('profile_eval_end', 0)
    else:
        eval_start = gear_data.get('helix_eval_start', 0)
        eval_end = gear_data.get('helix_eval_end', 0)
    
    eval_center = (eval_start + eval_end) / 2.0
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        n = len(values)
        
        corrected_values = preprocess_tooth_data(values, order=2)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        
        if data_type == 'profile':
            if eval_start > 0 and eval_end > 0:
                radii = np.linspace(eval_start/2, eval_end/2, n)
            else:
                radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, n)
            
            xi_angles = np.array([calculate_involute_angle(base_radius, r) for r in radii])
            
            if side == 'left':
                angles = tau - xi_angles
            else:
                angles = tau + xi_angles
        else:
            axial_positions = np.linspace(eval_start, eval_end, n)
            delta_z = axial_positions - eval_center
            
            eval_length = abs(ep_or_el) * base_pitch if ep_or_el != 0 else 1.0
            
            if abs(helix_angle_base) > 0.01:
                delta_phi = (delta_z / eval_length) * ep_or_el * (360.0 / teeth_count)
            else:
                delta_phi = np.zeros(n)
            
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


def analyze_all_samples(mka_files, sample_names, klingelnberg_refs, pdf_params):
    """分析所有样本"""
    
    fig, axes = plt.subplots(len(mka_files), 4, figsize=(20, 5*len(mka_files)))
    if len(mka_files) == 1:
        axes = axes.reshape(1, -1)
    
    for file_idx, (mka_file, sample_name, klingelnberg_ref) in enumerate(zip(mka_files, sample_names, klingelnberg_refs)):
        print(f"\n{'='*90}")
        print(f"Sample: {sample_name}")
        print(f"{'='*90}")
        
        parsed_data = parse_mka_file(mka_file)
        gear_data = parsed_data.get('gear_data', {})
        profile_data = parsed_data.get('profile_data', {})
        flank_data = parsed_data.get('flank_data', {})
        
        teeth_count = gear_data.get('teeth', 87)
        module = gear_data.get('module', 1.859)
        pressure_angle = gear_data.get('pressure_angle', 18.6)
        helix_angle = gear_data.get('helix_angle', 25.3)
        
        ep, el = pdf_params[file_idx]
        
        print(f"\nGear: Teeth={teeth_count}, Module={module}, Helix={helix_angle}°")
        print(f"PDF Parameters: ep={ep}, el={el}")
        
        max_order = 5 * teeth_count
        
        for col, (side, data_type) in enumerate([('right', 'profile'), ('left', 'profile'), 
                                                   ('right', 'helix'), ('left', 'helix')]):
            ax = axes[file_idx, col]
            direction = f'{side}_{data_type}'
            
            if data_type == 'profile':
                data = profile_data
                ep_or_el = ep
            else:
                data = flank_data
                ep_or_el = el
            
            angles, values = build_merged_curve(gear_data, data, side, data_type, ep_or_el)
            
            if angles is None:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'{side.capitalize()} {data_type.capitalize()}')
                continue
            
            orders, amplitudes = compute_spectrum(angles, values, max_order)
            
            ax.bar(orders, amplitudes, width=1.0, color='steelblue', alpha=0.7)
            
            for mult in range(1, 6):
                ze_order = teeth_count * mult
                if ze_order <= max_order:
                    ax.axvline(x=ze_order, color='red', linestyle='--', alpha=0.5, linewidth=1)
            
            if direction in klingelnberg_ref:
                ref = klingelnberg_ref[direction]
                scale = 0.109 if data_type == 'profile' else 0.05
                
                for order, ref_amp in ref.items():
                    if order <= max_order:
                        ax.scatter([order], [ref_amp / scale], color='green', s=100, 
                                  marker='*', zorder=5)
            
            ax.set_xlabel('Order')
            ax.set_ylabel('Amplitude (um)')
            ax.set_title(f'{side.capitalize()} {data_type.capitalize()}')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, max_order)
            
            print(f"\n{side.capitalize()} {data_type.capitalize()}:")
            print(f"  Max amplitude: {np.max(amplitudes):.4f} um at order {orders[np.argmax(amplitudes)]}")
            
            if direction in klingelnberg_ref:
                ref = klingelnberg_ref[direction]
                scale = 0.109 if data_type == 'profile' else 0.05
                
                print(f"  Comparison with Klingelnberg (scale={scale}):")
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
    
    output_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\all_samples_spectrum.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n\nSaved: {output_file}")
    
    plt.show()
    
    return output_file


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE1 = {
        'right_profile': {87: 0.1500, 174: 0.0500, 261: 0.0600, 348: 0.0700, 435: 0.0300},
        'left_profile': {87: 0.1400, 174: 0.0500, 261: 0.0600, 348: 0.0300, 435: 0.0400},
        'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300},
        'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300}
    }
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
        'left_profile': {22: 0.03, 26: 0.24, 44: 0.04, 52: 0.19, 78: 0.09, 104: 0.16, 130: 0.09, 156: 0.06, 182: 0.08},
        'right_helix': {26: 0.03, 52: 0.06, 78: 0.03, 141: 0.03, 156: 0.02},
        'left_helix': {26: 0.07, 48: 0.03, 52: 0.08, 78: 0.04, 104: 0.03, 130: 0.02, 141: 0.04, 182: 0.02}
    }
    
    # PDF参数
    PDF_PARAMS = [
        (1.454, 2.766),  # Sample1
        (1.398, 2.886),  # Sample2 (从MKA计算)
    ]
    
    analyze_all_samples(
        [sample1_file, sample2_file],
        ["Sample1 (ZE=87)", "Sample2 (ZE=26)"],
        [KLINGELNBERG_SAMPLE1, KLINGELNBERG_SAMPLE2],
        PDF_PARAMS
    )


if __name__ == "__main__":
    main()
