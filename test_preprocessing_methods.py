"""
测试更高阶多项式预处理和其他预处理策略
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

class AdvancedPreprocessor:
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
            return None, None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        all_tooth_ids = []
        
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
            all_values.extend(eval_values.tolist())
            all_tooth_ids.extend([tooth_id] * eval_points)
        
        if not all_angles:
            return None, None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        all_tooth_ids = np.array(all_tooth_ids)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        all_tooth_ids = all_tooth_ids[sort_idx]
        
        return all_angles, all_values, all_tooth_ids
    
    def preprocess_poly(self, values, order=2):
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        coeffs = np.polyfit(x_norm, values, order)
        trend = np.polyval(coeffs, x_norm)
        
        return values - trend
    
    def preprocess_savgol(self, values, window=None, order=3):
        if window is None:
            window = min(51, len(values) // 4 * 2 + 1)
        if window < 5:
            window = 5
        if window % 2 == 0:
            window += 1
        if window > len(values):
            window = len(values) - 1 if len(values) % 2 == 0 else len(values)
        
        trend = signal.savgol_filter(values, window, order)
        return values - trend
    
    def preprocess_highpass(self, values, cutoff=0.1, order=4):
        b, a = signal.butter(order, cutoff, btype='high')
        filtered = signal.filtfilt(b, a, values)
        return filtered
    
    def preprocess_detrend(self, values):
        from scipy.signal import detrend
        return detrend(values, type='linear')
    
    def preprocess_robust(self, values, order=2):
        from scipy.stats import theilslopes
        
        n = len(values)
        x = np.arange(n)
        
        if order == 1:
            slope, intercept, _, _ = theilslopes(values, x, 0.9)
            trend = slope * x + intercept
        else:
            x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
            coeffs = np.polyfit(x_norm, values, order)
            trend = np.polyval(coeffs, x_norm)
        
        return values - trend
    
    def preprocess_per_tooth(self, angles, values, tooth_ids, method='poly', **kwargs):
        unique_teeth = np.unique(tooth_ids)
        corrected_angles = []
        corrected_values = []
        
        for tooth_id in unique_teeth:
            mask = tooth_ids == tooth_id
            tooth_angles = angles[mask]
            tooth_values = values[mask]
            
            if len(tooth_values) < 5:
                continue
            
            if method == 'poly':
                corrected = self.preprocess_poly(tooth_values, **kwargs)
            elif method == 'savgol':
                corrected = self.preprocess_savgol(tooth_values, **kwargs)
            elif method == 'highpass':
                corrected = self.preprocess_highpass(tooth_values, **kwargs)
            elif method == 'detrend':
                corrected = self.preprocess_detrend(tooth_values)
            elif method == 'robust':
                corrected = self.preprocess_robust(tooth_values, **kwargs)
            else:
                corrected = tooth_values
            
            corrected_angles.extend(tooth_angles.tolist())
            corrected_values.extend(corrected.tolist())
        
        return np.array(corrected_angles), np.array(corrected_values)
    
    def compute_spectrum(self, angles, values, max_order=None):
        if max_order is None:
            max_order = 5 * self.teeth_count
        
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        num_points = max(1024, 2 * max_order + 10)
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        angles_rad = np.radians(interp_angles)
        
        spectrum = {}
        for order in range(1, max_order + 1):
            cos_term = np.cos(order * angles_rad)
            sin_term = np.sin(order * angles_rad)
            
            A = np.column_stack([cos_term, sin_term])
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
            
            a, b = coeffs[0], coeffs[1]
            amplitude = np.sqrt(a**2 + b**2)
            
            spectrum[order] = amplitude
        
        return spectrum, interp_angles, interp_values

def calculate_error(spectrum, ref):
    errors = []
    for order, ref_amp in ref.items():
        our_amp = spectrum.get(order, 0)
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
    
    preprocessor = AdvancedPreprocessor(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"齿轮参数: ZE={teeth_count}")
    
    print("\n" + "=" * 90)
    print("测试不同预处理方法组合")
    print("=" * 90)
    
    directions = ['left_profile', 'right_profile', 'left_helix', 'right_helix']
    
    preprocessing_methods = [
        ('poly_order_1', 'poly', {'order': 1}),
        ('poly_order_2', 'poly', {'order': 2}),
        ('poly_order_3', 'poly', {'order': 3}),
        ('poly_order_4', 'poly', {'order': 4}),
        ('poly_order_5', 'poly', {'order': 5}),
        ('savgol_order_2', 'savgol', {'order': 2}),
        ('savgol_order_3', 'savgol', {'order': 3}),
        ('highpass_0.1', 'highpass', {'cutoff': 0.1}),
        ('highpass_0.2', 'highpass', {'cutoff': 0.2}),
        ('detrend', 'detrend', {}),
        ('robust_order_1', 'robust', {'order': 1}),
        ('robust_order_2', 'robust', {'order': 2}),
    ]
    
    all_results = {}
    
    for method_name, method, kwargs in preprocessing_methods:
        print(f"\n测试方法: {method_name}")
        
        total_errors = []
        direction_results = {}
        
        for direction in directions:
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
            else:
                side_data = flank_data.get('right', {})
                data_type = 'helix'
                side = 'right'
                eval_start = gear_data.get('helix_eval_start', 0)
                eval_end = gear_data.get('helix_eval_end', 0)
                meas_start = gear_data.get('helix_meas_start', 0)
                meas_end = gear_data.get('helix_meas_end', 0)
            
            angles, values, tooth_ids = preprocessor.build_merged_curve(
                side_data, data_type, side, eval_start, eval_end, meas_start, meas_end
            )
            
            if angles is None:
                continue
            
            processed_angles, processed_values = preprocessor.preprocess_per_tooth(
                angles, values, tooth_ids, method=method, **kwargs
            )
            
            spectrum, _, _ = preprocessor.compute_spectrum(processed_angles, processed_values)
            
            ref = Klingelnberg_REFERENCE[direction]
            error = calculate_error(spectrum, ref)
            
            total_errors.append(error)
            direction_results[direction] = {
                'spectrum': spectrum,
                'error': error
            }
        
        avg_error = np.mean(total_errors) if total_errors else 100
        all_results[method_name] = {
            'avg_error': avg_error,
            'directions': direction_results
        }
        
        print(f"  平均误差: {avg_error:.1f}%")
    
    sorted_results = sorted(all_results.items(), key=lambda x: x[1]['avg_error'])
    
    print("\n" + "=" * 90)
    print("TOP 5 最佳预处理方法")
    print("=" * 90)
    
    for i, (method_name, result) in enumerate(sorted_results[:5]):
        print(f"\n#{i+1} {method_name}")
        print(f"  平均误差: {result['avg_error']:.1f}%")
        
        for direction, dir_data in result['directions'].items():
            ref = Klingelnberg_REFERENCE[direction]
            spectrum = dir_data['spectrum']
            
            print(f"  {direction}:")
            for order in sorted(ref.keys()):
                our_amp = spectrum.get(order, 0)
                ref_amp = ref[order]
                error = abs(our_amp - ref_amp) / ref_amp * 100 if our_amp > 0 else 100
                status = "✅" if error < 10 else "✓" if error < 25 else "⚠" if error < 50 else "✗"
                print(f"    {order}: {our_amp:.4f} vs {ref_amp:.4f} ({error:.1f}%) {status}")
    
    best_method = sorted_results[0][0]
    best_result = sorted_results[0][1]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    method_names = [r[0] for r in sorted_results]
    avg_errors = [r[1]['avg_error'] for r in sorted_results]
    
    colors = ['green' if e < 30 else 'orange' if e < 50 else 'red' for e in avg_errors]
    axes[0, 0].barh(range(len(method_names)), avg_errors, color=colors)
    axes[0, 0].set_yticks(range(len(method_names)))
    axes[0, 0].set_yticklabels(method_names, fontsize=8)
    axes[0, 0].set_xlabel('平均误差 (%)')
    axes[0, 0].set_title('所有预处理方法的平均误差')
    axes[0, 0].invert_yaxis()
    axes[0, 0].grid(True, alpha=0.3, axis='x')
    
    for idx, direction in enumerate(directions):
        ax = axes[(idx // 2) + 1, idx % 2] if idx >= 2 else axes[0, 1] if idx == 1 else axes[1, 1]
        if idx == 0:
            ax = axes[0, 1]
        elif idx == 1:
            ax = axes[1, 0]
        elif idx == 2:
            ax = axes[1, 1]
        else:
            ax = axes[0, 1]
    
    ax = axes[1, 0]
    direction = 'left_profile'
    spectrum = best_result['directions'][direction]['spectrum']
    ref = Klingelnberg_REFERENCE[direction]
    
    orders = sorted(ref.keys())
    our_amps = [spectrum.get(o, 0) for o in orders]
    ref_amps = [ref[o] for o in orders]
    
    x = np.arange(len(orders))
    width = 0.35
    
    ax.bar(x - width/2, our_amps, width, label='我们的结果', color='steelblue')
    ax.bar(x + width/2, ref_amps, width, label='Klingelnberg', color='coral')
    
    ax.set_xlabel('阶次')
    ax.set_ylabel('振幅 (μm)')
    ax.set_title(f'Left Profile - {best_method}')
    ax.set_xticks(x)
    ax.set_xticklabels([str(int(o)) for o in orders])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    ax = axes[1, 1]
    
    all_orders = list(range(1, 200))
    all_amplitudes = [spectrum.get(o, 0) for o in all_orders]
    
    ax.bar(all_orders, all_amplitudes, width=1.0, color='steelblue', alpha=0.6)
    ax.scatter(orders, ref_amps, color='red', s=100, zorder=5, label='Klingelnberg参考')
    ax.set_xlabel('阶次')
    ax.set_ylabel('振幅 (μm)')
    ax.set_title(f'完整频谱 (1-200阶次)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path = os.path.join(current_dir, "preprocessing_comparison.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n预处理对比图已保存: {output_path}")
    
    return all_results

if __name__ == "__main__":
    all_results = main()
