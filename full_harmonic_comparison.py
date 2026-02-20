"""
完整对比所有Klingelnberg参考阶次
包括主要分量和高阶谐波
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
        return {}, None, None
    
    angles, values = analyzer.build_merged_curve(
        side_data, data_type, side, eval_start, eval_end, meas_start, meas_end
    )
    
    if angles is None or len(angles) < 100:
        return {}, None, None
    
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
    
    print("\n" + "=" * 90)
    print("完整Klingelnberg参考值对比")
    print("=" * 90)
    
    direction_names = {
        'left_profile': 'Left Profile (左齿形)',
        'right_profile': 'Right Profile (右齿形)',
        'left_helix': 'Left Helix (左齿向)',
        'right_helix': 'Right Helix (右齿向)'
    }
    
    total_errors = []
    all_comparison_data = []
    
    for direction in directions:
        spectrum = all_spectra[direction]
        ref = Klingelnberg_REFERENCE[direction]
        
        print(f"\n{direction_names[direction]}:")
        print(f"  {'阶次':<8} {'我们的结果':<12} {'Klingelnberg':<12} {'误差':<10} {'状态':<8} {'备注':<15}")
        print(f"  {'-'*70}")
        
        direction_errors = []
        direction_data = []
        
        for order in sorted(ref.keys()):
            ref_amp = ref[order]
            our_amp = spectrum.get(order, {}).get('amplitude', 0)
            
            if our_amp > 0:
                error = abs(our_amp - ref_amp) / ref_amp * 100
                direction_errors.append(error)
                total_errors.append(error)
                
                if error < 10:
                    status = "✅ 优秀"
                elif error < 25:
                    status = "✓ 良好"
                elif error < 50:
                    status = "⚠ 偏差"
                else:
                    status = "✗ 较大偏差"
                
                harmonic = ""
                if order == teeth_count:
                    harmonic = "ZE (基频)"
                elif order == 2 * teeth_count:
                    harmonic = "2×ZE (2次谐波)"
                elif order == 3 * teeth_count:
                    harmonic = "3×ZE (3次谐波)"
                elif order == 4 * teeth_count:
                    harmonic = "4×ZE (4次谐波)"
                elif order == 5 * teeth_count:
                    harmonic = "5×ZE (5次谐波)"
                elif order == teeth_count + 2:
                    harmonic = "ZE+2"
                
                print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}% {status:<8} {harmonic}")
                
                direction_data.append({
                    'order': order,
                    'our_amp': our_amp,
                    'ref_amp': ref_amp,
                    'error': error,
                    'status': status,
                    'harmonic': harmonic
                })
        
        all_comparison_data.append({
            'direction': direction,
            'data': direction_data
        })
        
        if direction_errors:
            avg_error = np.mean(direction_errors)
            print(f"  {'-'*70}")
            print(f"  方向平均误差: {avg_error:.1f}%")
    
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
    
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    
    for idx, direction in enumerate(directions):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]
        
        spectrum = all_spectra[direction]
        ref = Klingelnberg_REFERENCE[direction]
        
        orders = np.array(list(spectrum.keys()))
        amplitudes = np.array([spectrum[o]['amplitude'] for o in orders])
        
        ax.bar(orders, amplitudes, width=1.0, color='steelblue', alpha=0.6, edgecolor='none', label='我们的结果')
        
        ref_orders = sorted(ref.keys())
        ref_amplitudes = [ref[o] for o in ref_orders]
        our_at_ref = [spectrum.get(o, {}).get('amplitude', 0) for o in ref_orders]
        
        ax.scatter(ref_orders, ref_amplitudes, color='red', s=120, zorder=5, marker='o', label='Klingelnberg参考值')
        ax.scatter(ref_orders, our_at_ref, color='green', s=80, zorder=6, marker='s', label='我们在参考阶次的值')
        
        for o, ref_a, our_a in zip(ref_orders, ref_amplitudes, our_at_ref):
            error = abs(our_a - ref_a) / ref_a * 100
            color = 'green' if error < 10 else 'orange' if error < 25 else 'red'
            ax.annotate(f'{int(o)}\n{error:.0f}%', 
                       xy=(o, max(ref_a, our_a) + 0.005),
                       ha='center', fontsize=8, color=color, fontweight='bold')
        
        ax.axvline(x=teeth_count, color='green', linestyle='-', alpha=0.5, linewidth=1.5)
        ax.axvline(x=2*teeth_count, color='orange', linestyle='--', alpha=0.5, linewidth=1)
        ax.axvline(x=3*teeth_count, color='purple', linestyle='--', alpha=0.5, linewidth=1)
        ax.axvline(x=4*teeth_count, color='brown', linestyle='--', alpha=0.5, linewidth=1)
        ax.axvline(x=5*teeth_count, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        
        ax.set_xlabel('阶次', fontsize=11)
        ax.set_ylabel('振幅 (μm)', fontsize=11)
        ax.set_title(direction_names[direction], fontsize=13, fontweight='bold')
        ax.set_xlim(0, 5 * teeth_count + 20)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend(loc='upper right', fontsize=9)
    
    plt.tight_layout()
    output_path = os.path.join(current_dir, "full_harmonic_comparison.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n完整谐波对比图已保存: {output_path}")
    
    fig2, ax2 = plt.subplots(figsize=(16, 8))
    
    x_positions = np.arange(len(total_errors))
    colors = ['green' if e < 10 else 'orange' if e < 25 else 'red' for e in total_errors]
    
    bars = ax2.bar(x_positions, total_errors, color=colors, alpha=0.7, edgecolor='black')
    
    ax2.axhline(y=10, color='green', linestyle='--', alpha=0.7, label='优秀阈值 (10%)')
    ax2.axhline(y=25, color='orange', linestyle='--', alpha=0.7, label='良好阈值 (25%)')
    
    labels = []
    for comp in all_comparison_data:
        for d in comp['data']:
            labels.append(f"{comp['direction'].split('_')[0][0].upper()}{comp['direction'].split('_')[1][0].upper()}-{int(d['order'])}")
    
    ax2.set_xticks(x_positions)
    ax2.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax2.set_ylabel('误差 (%)', fontsize=12)
    ax2.set_title('所有Klingelnberg参考阶次误差对比', fontsize=14, fontweight='bold')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3, axis='y')
    
    for i, (bar, error) in enumerate(zip(bars, total_errors)):
        ax2.annotate(f'{error:.1f}%', 
                    xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                    xytext=(0, 3), textcoords='offset points',
                    ha='center', fontsize=8, fontweight='bold')
    
    plt.tight_layout()
    output_path2 = os.path.join(current_dir, "error_comparison_all.png")
    plt.savefig(output_path2, dpi=150, bbox_inches='tight')
    print(f"误差对比图已保存: {output_path2}")
    
    csv_path = os.path.join(current_dir, "full_comparison_results.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("方向,阶次,我们的振幅,Klingelnberg振幅,误差(%),状态,谐波类型\n")
        
        for comp in all_comparison_data:
            direction_name = direction_names[comp['direction']]
            for d in comp['data']:
                f.write(f"{direction_name},{int(d['order'])},{d['our_amp']:.4f},{d['ref_amp']:.4f},{d['error']:.1f},{d['status']},{d['harmonic']}\n")
    
    print(f"CSV数据已保存: {csv_path}")
    
    return all_spectra, all_comparison_data

if __name__ == "__main__":
    all_spectra, all_comparison_data = main()
