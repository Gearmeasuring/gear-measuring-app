"""
调整滤波参数以保留高阶谐波
测试不同截止频率对高阶谐波的影响
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy import signal
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

Klingelnberg_REFERENCE = {
    'left_profile': {87: 0.1400, 174: 0.0500, 261: 0.0600, 348: 0.0300, 435: 0.0400},
    'right_profile': {87: 0.1500, 174: 0.0500, 261: 0.0600, 348: 0.0700, 435: 0.0300},
    'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300},
    'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300}
}

class OptimizedRippleAnalyzer:
    def __init__(self, teeth_count, module, pressure_angle=20.0, helix_angle=0.0, base_diameter=0.0):
        self.teeth_count = teeth_count
        self.module = module
        self.pressure_angle = pressure_angle
        self.helix_angle = helix_angle
        
        self.pitch_diameter = module * teeth_count
        self.pitch_radius = self.pitch_diameter / 2.0
        self.pitch_angle = 360.0 / teeth_count
        
        if base_diameter > 0:
            self.base_diameter = base_diameter
        else:
            self.base_diameter = self.pitch_diameter * math.cos(math.radians(pressure_angle))
        
        self.base_radius = self.base_diameter / 2.0
    
    def preprocess_weighted(self, data, poly_order=2):
        if len(data) < 3:
            return data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        weights = np.exp(-0.5 * ((x_norm) / 1.5)**2)
        coeffs = np.polyfit(x_norm, data, poly_order, w=weights)
        trend = np.polyval(coeffs, x_norm)
        
        return data - trend
    
    def apply_filter(self, data, cutoff_ratio=0.2, order=4):
        if len(data) < 10:
            return data
        
        b, a = signal.butter(order, cutoff_ratio, btype='low')
        filtered = signal.filtfilt(b, a, data)
        
        return filtered
    
    def calculate_involute_angle(self, radius):
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def build_merged_curve(self, side_data, data_type, side, eval_start, eval_end, meas_start, meas_end):
        if not side_data:
            return None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            
            if meas_end > meas_start and eval_end > eval_start:
                eval_start_ratio = (eval_start - meas_start) / (meas_end - meas_start)
                eval_end_ratio = (eval_end - meas_start) / (meas_end - meas_start)
                start_idx = int(actual_points * max(0.0, min(1.0, eval_start_ratio)))
                end_idx = int(actual_points * max(0.0, min(1.0, eval_end_ratio)))
            else:
                start_idx = 0
                end_idx = actual_points
            
            eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
            eval_points = len(eval_values)
            
            if eval_points < 3:
                continue
            
            corrected_values = self.preprocess_weighted(eval_values)
            
            tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
            tau = tooth_index * self.pitch_angle
            
            if data_type == 'profile':
                if eval_start > 0 and eval_end > 0:
                    radii = np.linspace(eval_start/2, eval_end/2, eval_points)
                else:
                    radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, eval_points)
                
                xi_angles = np.array([math.degrees(self.calculate_involute_angle(r)) for r in radii])
                
                if side == 'left':
                    angles = tau - xi_angles
                else:
                    angles = tau + xi_angles
            else:
                if abs(self.helix_angle) > 0.01 and self.pitch_diameter > 0:
                    axial_positions = np.linspace(eval_start, eval_end, eval_points)
                    eval_center = (eval_start + eval_end) / 2.0
                    delta_z = axial_positions - eval_center
                    tan_beta0 = math.tan(math.radians(self.helix_angle))
                    delta_phi = np.degrees(2 * delta_z * tan_beta0 / self.pitch_diameter)
                else:
                    delta_phi = np.linspace(0, 1, eval_points)
                
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
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        return all_angles, all_values
    
    def interpolate_curve(self, angles, values, num_points=None):
        if num_points is None:
            num_points = max(1024, 2 * 5 * self.teeth_count + 10)
        
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        return interp_angles, interp_values
    
    def compute_full_spectrum(self, angles, values, max_order=None):
        if max_order is None:
            max_order = 5 * self.teeth_count
        
        angles_rad = np.radians(angles)
        
        spectrum = {}
        for order in range(1, max_order + 1):
            cos_term = np.cos(order * angles_rad)
            sin_term = np.sin(order * angles_rad)
            
            A = np.column_stack([cos_term, sin_term])
            coeffs, _, _, _ = np.linalg.lstsq(A, values, rcond=None)
            
            a, b = coeffs[0], coeffs[1]
            amplitude = np.sqrt(a**2 + b**2)
            phase = np.degrees(np.arctan2(a, b))
            
            spectrum[order] = {
                'amplitude': amplitude,
                'phase': phase
            }
        
        return spectrum

def analyze_direction(profile_data, flank_data, analyzer, direction, gear_data, cutoff_ratio=0.2):
    
    if direction == 'left_profile':
        side_data = profile_data.get('left', {})
        data_type = 'profile'
        side = 'left'
        eval_start = gear_data.get('profile_eval_start', 0)
        eval_end = gear_data.get('profile_eval_end', 0)
        meas_start = gear_data.get('profile_meas_start', 0)
        meas_end = gear_data.get('profile_meas_end', 0)
    elif direction == 'right_profile':
        side_data = profile_data.get('right', {})
        data_type = 'profile'
        side = 'right'
        eval_start = gear_data.get('profile_eval_start', 0)
        eval_end = gear_data.get('profile_eval_end', 0)
        meas_start = gear_data.get('profile_meas_start', 0)
        meas_end = gear_data.get('profile_meas_end', 0)
    elif direction == 'left_helix':
        side_data = flank_data.get('left', {})
        data_type = 'helix'
        side = 'left'
        eval_start = gear_data.get('helix_eval_start', 0)
        eval_end = gear_data.get('helix_eval_end', 0)
        meas_start = gear_data.get('helix_meas_start', 0)
        meas_end = gear_data.get('helix_meas_end', 0)
    elif direction == 'right_helix':
        side_data = flank_data.get('right', {})
        data_type = 'helix'
        side = 'right'
        eval_start = gear_data.get('helix_eval_start', 0)
        eval_end = gear_data.get('helix_eval_end', 0)
        meas_start = gear_data.get('helix_meas_start', 0)
        meas_end = gear_data.get('helix_meas_end', 0)
    else:
        return {}, None, None
    
    angles, values = analyzer.build_merged_curve(
        side_data, data_type, side, eval_start, eval_end, meas_start, meas_end
    )
    
    if angles is None or len(angles) < 100:
        return {}, None, None
    
    interp_angles, interp_values = analyzer.interpolate_curve(angles, values)
    
    if cutoff_ratio < 1.0:
        filtered = analyzer.apply_filter(interp_values, cutoff_ratio=cutoff_ratio)
    else:
        filtered = interp_values
    
    spectrum = analyzer.compute_full_spectrum(interp_angles, filtered)
    
    return spectrum, interp_angles, filtered

def calculate_total_error(spectrum, ref):
    errors = []
    for order, ref_amp in ref.items():
        our_amp = spectrum.get(order, {}).get('amplitude', 0)
        if our_amp > 0 and ref_amp > 0:
            error = abs(our_amp - ref_amp) / ref_amp * 100
            errors.append(error)
    return np.mean(errors) if errors else 100

def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    print("解析MKA文件...")
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    analyzer = OptimizedRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"齿轮参数: ZE={teeth_count}, m={module}, α={pressure_angle}°, β={helix_angle}°")
    
    print("\n" + "=" * 90)
    print("测试不同截止频率对高阶谐波的影响")
    print("=" * 90)
    
    max_harmonic_order = 5 * teeth_count
    print(f"需要保留的最高阶次: {max_harmonic_order} (5×ZE)")
    
    cutoff_ratios = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.5, 2.0]
    
    print(f"\n测试截止频率比: {cutoff_ratios}")
    
    directions = ['left_profile', 'right_profile', 'left_helix', 'right_helix']
    
    best_cutoff = 0.2
    best_total_error = float('inf')
    all_cutoff_results = []
    
    for cutoff in cutoff_ratios:
        total_errors = []
        
        for direction in directions:
            spectrum, _, _ = analyze_direction(profile_data, flank_data, analyzer, direction, gear_data, cutoff)
            ref = Klingelnberg_REFERENCE[direction]
            error = calculate_total_error(spectrum, ref)
            total_errors.append(error)
        
        avg_error = np.mean(total_errors)
        all_cutoff_results.append({
            'cutoff': cutoff,
            'avg_error': avg_error,
            'errors': total_errors
        })
        
        print(f"截止频率比 {cutoff}: 平均误差 {avg_error:.1f}%")
        
        if avg_error < best_total_error:
            best_total_error = avg_error
            best_cutoff = cutoff
    
    print(f"\n最佳截止频率比: {best_cutoff} (平均误差: {best_total_error:.1f}%)")
    
    print("\n" + "=" * 90)
    print("使用最佳截止频率重新分析")
    print("=" * 90)
    
    all_spectra = {}
    for direction in directions:
        spectrum, angles, filtered = analyze_direction(profile_data, flank_data, analyzer, direction, gear_data, best_cutoff)
        all_spectra[direction] = spectrum
    
    direction_names = {
        'left_profile': 'Left Profile (左齿形)',
        'right_profile': 'Right Profile (右齿形)',
        'left_helix': 'Left Helix (左齿向)',
        'right_helix': 'Right Helix (右齿向)'
    }
    
    total_errors = []
    
    for direction in directions:
        spectrum = all_spectra[direction]
        ref = Klingelnberg_REFERENCE[direction]
        
        print(f"\n{direction_names[direction]}:")
        print(f"  {'阶次':<8} {'我们的结果':<12} {'Klingelnberg':<12} {'误差':<10} {'状态':<8}")
        print(f"  {'-'*55}")
        
        for order in sorted(ref.keys()):
            ref_amp = ref[order]
            our_amp = spectrum.get(order, {}).get('amplitude', 0)
            
            if our_amp > 0:
                error = abs(our_amp - ref_amp) / ref_amp * 100
                total_errors.append(error)
                
                if error < 10:
                    status = "✅ 优秀"
                elif error < 25:
                    status = "✓ 良好"
                elif error < 50:
                    status = "⚠ 偏差"
                else:
                    status = "✗ 较大偏差"
                
                print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}% {status}")
    
    print("\n" + "=" * 90)
    print("总体统计")
    print("=" * 90)
    
    if total_errors:
        avg_total = np.mean(total_errors)
        excellent = sum(1 for e in total_errors if e < 10)
        good = sum(1 for e in total_errors if 10 <= e < 25)
        fair = sum(1 for e in total_errors if 25 <= e < 50)
        poor = sum(1 for e in total_errors if e >= 50)
        total = len(total_errors)
        
        print(f"\n总平均误差: {avg_total:.1f}%")
        print(f"\n误差分布:")
        print(f"  优秀 (<10%):    {excellent}/{total} ({excellent/total*100:.0f}%)")
        print(f"  良好 (10-25%):  {good}/{total} ({good/total*100:.0f}%)")
        print(f"  偏差 (25-50%):  {fair}/{total} ({fair/total*100:.0f}%)")
        print(f"  较大 (>50%):    {poor}/{total} ({poor/total*100:.0f}%)")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    cutoff_values = [r['cutoff'] for r in all_cutoff_results]
    avg_errors = [r['avg_error'] for r in all_cutoff_results]
    
    axes[0, 0].plot(cutoff_values, avg_errors, 'bo-', linewidth=2, markersize=8)
    axes[0, 0].axvline(x=best_cutoff, color='red', linestyle='--', label=f'最佳: {best_cutoff}')
    axes[0, 0].set_xlabel('截止频率比', fontsize=12)
    axes[0, 0].set_ylabel('平均误差 (%)', fontsize=12)
    axes[0, 0].set_title('截止频率 vs 平均误差', fontsize=14, fontweight='bold')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    for i, direction in enumerate(directions):
        direction_errors = [r['errors'][i] for r in all_cutoff_results]
        axes[0, 1].plot(cutoff_values, direction_errors, 'o-', label=direction_names[direction], linewidth=1.5)
    
    axes[0, 1].set_xlabel('截止频率比', fontsize=12)
    axes[0, 1].set_ylabel('误差 (%)', fontsize=12)
    axes[0, 1].set_title('各方向误差随截止频率变化', fontsize=14, fontweight='bold')
    axes[0, 1].legend(fontsize=9)
    axes[0, 1].grid(True, alpha=0.3)
    
    spectrum = all_spectra['left_profile']
    ref = Klingelnberg_REFERENCE['left_profile']
    
    orders = np.array(list(spectrum.keys()))
    amplitudes = np.array([spectrum[o]['amplitude'] for o in orders])
    
    axes[1, 0].bar(orders, amplitudes, width=1.0, color='steelblue', alpha=0.6, label='我们的结果')
    
    ref_orders = sorted(ref.keys())
    ref_amplitudes = [ref[o] for o in ref_orders]
    axes[1, 0].scatter(ref_orders, ref_amplitudes, color='red', s=100, zorder=5, marker='o', label='Klingelnberg')
    
    axes[1, 0].set_xlabel('阶次', fontsize=12)
    axes[1, 0].set_ylabel('振幅 (μm)', fontsize=12)
    axes[1, 0].set_title(f'Left Profile (截止频率比={best_cutoff})', fontsize=14, fontweight='bold')
    axes[1, 0].legend()
    axes[1, 0].set_xlim(0, 450)
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    x_labels = []
    all_errors = []
    
    for direction in directions:
        spectrum = all_spectra[direction]
        ref = Klingelnberg_REFERENCE[direction]
        
        for order in sorted(ref.keys()):
            ref_amp = ref[order]
            our_amp = spectrum.get(order, {}).get('amplitude', 0)
            if our_amp > 0:
                error = abs(our_amp - ref_amp) / ref_amp * 100
                x_labels.append(f"{direction.split('_')[0][0].upper()}{direction.split('_')[1][0].upper()}-{int(order)}")
                all_errors.append(error)
    
    colors = ['green' if e < 10 else 'orange' if e < 25 else 'red' for e in all_errors]
    bars = axes[1, 1].bar(range(len(all_errors)), all_errors, color=colors, alpha=0.7)
    
    axes[1, 1].axhline(y=10, color='green', linestyle='--', alpha=0.7, label='优秀阈值')
    axes[1, 1].axhline(y=25, color='orange', linestyle='--', alpha=0.7, label='良好阈值')
    
    axes[1, 1].set_xticks(range(len(all_errors)))
    axes[1, 1].set_xticklabels(x_labels, rotation=45, ha='right', fontsize=8)
    axes[1, 1].set_ylabel('误差 (%)', fontsize=12)
    axes[1, 1].set_title('所有参考阶次误差', fontsize=14, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path = os.path.join(current_dir, "cutoff_optimization.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n截止频率优化图已保存: {output_path}")
    
    return all_spectra, all_cutoff_results

if __name__ == "__main__":
    all_spectra, all_cutoff_results = main()
