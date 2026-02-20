"""
生成全部阶次的频谱图
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
        
        spectrum = []
        for order in range(1, max_order + 1):
            cos_term = np.cos(order * angles_rad)
            sin_term = np.sin(order * angles_rad)
            
            A = np.column_stack([cos_term, sin_term])
            coeffs, _, _, _ = np.linalg.lstsq(A, values, rcond=None)
            
            a, b = coeffs[0], coeffs[1]
            amplitude = np.sqrt(a**2 + b**2)
            phase = np.degrees(np.arctan2(a, b))
            
            spectrum.append({
                'order': order,
                'amplitude': amplitude,
                'phase': phase
            })
        
        return spectrum

def analyze_direction(profile_data, flank_data, analyzer, direction, gear_data):
    
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
        return [], None, None
    
    angles, values = analyzer.build_merged_curve(
        side_data, data_type, side, eval_start, eval_end, meas_start, meas_end
    )
    
    if angles is None or len(angles) < 100:
        return [], None, None
    
    interp_angles, interp_values = analyzer.interpolate_curve(angles, values)
    
    filtered = analyzer.apply_filter(interp_values)
    
    spectrum = analyzer.compute_full_spectrum(interp_angles, filtered)
    
    return spectrum, interp_angles, filtered

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
    
    print("\n计算全部阶次频谱...")
    
    directions = ['left_profile', 'right_profile', 'left_helix', 'right_helix']
    all_spectra = {}
    
    for direction in directions:
        spectrum, angles, filtered = analyze_direction(profile_data, flank_data, analyzer, direction, gear_data)
        all_spectra[direction] = spectrum
        print(f"  {direction}: {len(spectrum)} 阶次")
    
    print("\n生成频谱图...")
    
    direction_names = {
        'left_profile': 'Left Profile (左齿形)',
        'right_profile': 'Right Profile (右齿形)',
        'left_helix': 'Left Helix (左齿向)',
        'right_helix': 'Right Helix (右齿向)'
    }
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    
    for idx, direction in enumerate(directions):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]
        
        spectrum = all_spectra[direction]
        ref = Klingelnberg_REFERENCE[direction]
        
        orders = np.array([s['order'] for s in spectrum])
        amplitudes = np.array([s['amplitude'] for s in spectrum])
        
        ax.bar(orders, amplitudes, width=1.0, color='steelblue', alpha=0.7, edgecolor='none')
        
        ref_orders = list(ref.keys())
        ref_amplitudes = list(ref.values())
        ax.scatter(ref_orders, ref_amplitudes, color='red', s=100, zorder=5, marker='o', label='Klingelnberg参考值')
        
        for o, a in zip(ref_orders, ref_amplitudes):
            ax.axvline(x=o, color='red', linestyle='--', alpha=0.3, linewidth=0.8)
            ax.annotate(f'{o}: {a:.3f}', xy=(o, a), xytext=(o+10, a+0.01),
                       fontsize=8, color='red', ha='left')
        
        ax.axvline(x=teeth_count, color='green', linestyle='-', alpha=0.5, linewidth=1.5, label=f'ZE={teeth_count}')
        
        ax.set_xlabel('阶次', fontsize=11)
        ax.set_ylabel('振幅 (μm)', fontsize=11)
        ax.set_title(direction_names[direction], fontsize=13, fontweight='bold')
        ax.set_xlim(0, 5 * teeth_count)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend(loc='upper right', fontsize=9)
    
    plt.tight_layout()
    output_path = os.path.join(current_dir, "full_spectrum_all_orders.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"全阶次频谱图已保存: {output_path}")
    
    fig2, axes2 = plt.subplots(2, 2, figsize=(18, 12))
    
    for idx, direction in enumerate(directions):
        row = idx // 2
        col = idx % 2
        ax = axes2[row, col]
        
        spectrum = all_spectra[direction]
        ref = Klingelnberg_REFERENCE[direction]
        
        orders = np.array([s['order'] for s in spectrum])
        amplitudes = np.array([s['amplitude'] for s in spectrum])
        
        ax.semilogy(orders, amplitudes, 'b-', linewidth=0.8, alpha=0.8)
        ax.fill_between(orders, amplitudes, alpha=0.3)
        
        ref_orders = list(ref.keys())
        ref_amplitudes = list(ref.values())
        ax.scatter(ref_orders, ref_amplitudes, color='red', s=100, zorder=5, marker='o', label='Klingelnberg参考值')
        
        for o, a in zip(ref_orders, ref_amplitudes):
            ax.axvline(x=o, color='red', linestyle='--', alpha=0.3, linewidth=0.8)
        
        ax.axvline(x=teeth_count, color='green', linestyle='-', alpha=0.5, linewidth=1.5, label=f'ZE={teeth_count}')
        
        ax.set_xlabel('阶次', fontsize=11)
        ax.set_ylabel('振幅 (μm) - 对数刻度', fontsize=11)
        ax.set_title(f'{direction_names[direction]} - 对数频谱', fontsize=13, fontweight='bold')
        ax.set_xlim(0, 5 * teeth_count)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=9)
    
    plt.tight_layout()
    output_path2 = os.path.join(current_dir, "full_spectrum_log_scale.png")
    plt.savefig(output_path2, dpi=150, bbox_inches='tight')
    print(f"对数频谱图已保存: {output_path2}")
    
    fig3, axes3 = plt.subplots(4, 1, figsize=(18, 16))
    
    for idx, direction in enumerate(directions):
        ax = axes3[idx]
        
        spectrum = all_spectra[direction]
        ref = Klingelnberg_REFERENCE[direction]
        
        orders = np.array([s['order'] for s in spectrum])
        amplitudes = np.array([s['amplitude'] for s in spectrum])
        
        ax.bar(orders, amplitudes, width=0.8, color='steelblue', alpha=0.7, edgecolor='none')
        
        ref_orders = list(ref.keys())
        ref_amplitudes = list(ref.values())
        ax.scatter(ref_orders, ref_amplitudes, color='red', s=150, zorder=5, marker='o', label='Klingelnberg参考值')
        
        for o, a in zip(ref_orders, ref_amplitudes):
            our_amp = next((s['amplitude'] for s in spectrum if abs(s['order'] - o) < 0.5), 0)
            if our_amp > 0:
                error = abs(our_amp - a) / a * 100
                ax.annotate(f'{o}: {our_amp:.3f}\n({error:.1f}%)', 
                           xy=(o, a), xytext=(o+5, a+0.01),
                           fontsize=9, color='red', ha='left',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))
        
        ax.axvline(x=teeth_count, color='green', linestyle='-', alpha=0.7, linewidth=2, label=f'ZE={teeth_count}')
        ax.axvline(x=2*teeth_count, color='orange', linestyle='--', alpha=0.5, linewidth=1, label=f'2×ZE={2*teeth_count}')
        ax.axvline(x=3*teeth_count, color='purple', linestyle='--', alpha=0.5, linewidth=1, label=f'3×ZE={3*teeth_count}')
        
        ax.set_xlabel('阶次', fontsize=11)
        ax.set_ylabel('振幅 (μm)', fontsize=11)
        ax.set_title(direction_names[direction], fontsize=13, fontweight='bold')
        ax.set_xlim(0, 300)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend(loc='upper right', fontsize=9)
    
    plt.tight_layout()
    output_path3 = os.path.join(current_dir, "full_spectrum_detail.png")
    plt.savefig(output_path3, dpi=150, bbox_inches='tight')
    print(f"详细频谱图已保存: {output_path3}")
    
    print("\n" + "=" * 80)
    print("各阶次振幅数据 (前20个)")
    print("=" * 80)
    
    for direction in directions:
        spectrum = all_spectra[direction]
        ref = Klingelnberg_REFERENCE[direction]
        
        print(f"\n{direction_names[direction]}:")
        print(f"  {'阶次':<6} {'振幅':<10} {'Klingelnberg':<12} {'误差':<10}")
        print(f"  {'-'*40}")
        
        sorted_spectrum = sorted(spectrum, key=lambda x: x['amplitude'], reverse=True)
        
        for s in sorted_spectrum[:20]:
            order = s['order']
            amp = s['amplitude']
            
            if order in ref:
                ref_amp = ref[order]
                error = abs(amp - ref_amp) / ref_amp * 100
                print(f"  {order:<6.0f} {amp:<10.4f} {ref_amp:<12.4f} {error:<10.1f}% ★")
            else:
                print(f"  {order:<6.0f} {amp:<10.4f}")
    
    return all_spectra

if __name__ == "__main__":
    all_spectra = main()
