"""
寻找最佳振幅缩放因子
测试不同的缩放方法
"""
import os
import sys
import numpy as np
import math
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


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


def compute_raw_spectrum(angles, values, target_orders):
    """计算原始频谱（无缩放）"""
    if angles is None or values is None:
        return {}
    
    unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
    unique_values = values[unique_indices]
    
    num_points = max(360, 2 * 5 * len(target_orders) + 10)
    interp_angles = np.linspace(0, 360, num_points, endpoint=False)
    interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
    
    theta = np.radians(interp_angles)
    
    spectrum = {}
    for order in target_orders:
        cos_x = np.cos(order * theta)
        sin_x = np.sin(order * theta)
        A = np.column_stack((cos_x, sin_x))
        coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
        a, b = coeffs
        amplitude = np.sqrt(a*a + b*b)
        spectrum[order] = amplitude
    
    return spectrum


def find_best_scale(mka_file, sample_name, klingelnberg_ref):
    """寻找最佳缩放因子"""
    print(f"\n{'='*90}")
    print(f"Find Best Scale Factor: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    pressure_angle = gear_data.get('pressure_angle', 17.0)
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_radius = base_diameter / 2.0
    pitch_angle = 360.0 / teeth_count
    
    # 计算ep
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    eval_length = eval_end - eval_start if eval_end > eval_start else 0
    base_pitch = math.pi * base_diameter / teeth_count
    ep = eval_length / base_pitch if base_pitch > 0 else 1.0
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}")
    print(f"Base Pitch pb = {base_pitch:.4f} mm")
    print(f"Eval Length = {eval_length:.3f} mm")
    print(f"ep = {ep:.4f}")
    print(f"sqrt(ep) = {np.sqrt(ep):.4f}")
    print(f"1/ep = {1/ep:.4f}")
    print(f"1/sqrt(ep) = {1/np.sqrt(ep):.4f}")
    
    for side in ['right', 'left']:
        side_data = profile_data.get(side, {})
        direction = f'{side}_profile'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        # 构建合并曲线
        all_angles = []
        all_values = []
        
        for tooth_id in sorted(side_data.keys()):
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            values = np.array(tooth_values, dtype=float)
            n = len(values)
            
            corrected_values = preprocess_tooth_data(values, order=2)
            
            if eval_start > 0 and eval_end > 0:
                radii = np.linspace(eval_start/2, eval_end/2, n)
            else:
                radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, n)
            
            xi_angles = np.array([calculate_involute_angle(base_radius, r) for r in radii])
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * pitch_angle
            
            if side == 'left':
                angles = tau - xi_angles
            else:
                angles = tau + xi_angles
            
            all_angles.extend(angles.tolist())
            all_values.extend(corrected_values.tolist())
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        # 计算原始频谱
        raw_spectrum = compute_raw_spectrum(all_angles, all_values, list(ref.keys()))
        
        print(f"\n{side.upper()} Profile:")
        print(f"  Raw amplitudes: {[f'{raw_spectrum[o]:.2f}' for o in sorted(ref.keys())]}")
        print(f"  Klingelnberg:   {[f'{ref[o]:.2f}' for o in sorted(ref.keys())]}")
        
        # 测试不同的缩放方法
        print(f"\n  Testing different scale methods:")
        
        methods = [
            ("No scale", 1.0),
            ("1/ep", 1/ep),
            ("1/sqrt(ep)", 1/np.sqrt(ep)),
            ("ep", ep),
            ("sqrt(ep)", np.sqrt(ep)),
            ("1/ZE", 1/teeth_count),
            ("1/sqrt(ZE)", 1/np.sqrt(teeth_count)),
        ]
        
        for method_name, scale in methods:
            errors = []
            for order in ref.keys():
                our_amp = raw_spectrum[order] * scale
                ref_amp = ref[order]
                error = abs(our_amp - ref_amp) / ref_amp * 100
                errors.append(error)
            avg_error = np.mean(errors)
            print(f"    {method_name:<15} (scale={scale:.4f}): avg error = {avg_error:.1f}%")
        
        # 寻找最佳线性缩放因子
        print(f"\n  Finding best linear scale factor:")
        best_scale = None
        best_error = float('inf')
        
        for scale in np.linspace(0.01, 0.5, 100):
            errors = []
            for order in ref.keys():
                our_amp = raw_spectrum[order] * scale
                ref_amp = ref[order]
                error = abs(our_amp - ref_amp) / ref_amp * 100
                errors.append(error)
            avg_error = np.mean(errors)
            if avg_error < best_error:
                best_error = avg_error
                best_scale = scale
        
        print(f"    Best scale: {best_scale:.4f}, error: {best_error:.1f}%")
        
        # 显示最佳结果
        print(f"\n  Best Results (scale={best_scale:.4f}):")
        print(f"    {'Order':<8} {'Ours':<12} {'Klingelnberg':<12} {'Error':<10}")
        for order in sorted(ref.keys()):
            our_amp = raw_spectrum[order] * best_scale
            ref_amp = ref[order]
            error = abs(our_amp - ref_amp) / ref_amp * 100
            print(f"    {order:<8} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
        'left_profile': {22: 0.03, 26: 0.24, 44: 0.04, 52: 0.19, 78: 0.09, 104: 0.16, 130: 0.09, 156: 0.06, 182: 0.08},
    }
    
    find_best_scale(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
