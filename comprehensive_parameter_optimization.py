"""
全面优化波纹度分析参数 - 修复版
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
    'left_profile': {87: 0.1400},
    'right_profile': {87: 0.1500},
    'left_helix': {87: 0.1200, 89: 0.0700},
    'right_helix': {87: 0.0900}
}

class ParameterizedRippleAnalyzer:
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
    
    def preprocess_data(self, data, method='polynomial', poly_order=2):
        if len(data) < 3:
            return data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        if method == 'polynomial':
            coeffs = np.polyfit(x_norm, data, poly_order)
            trend = np.polyval(coeffs, x_norm)
        elif method == 'weighted':
            weights = np.exp(-0.5 * ((x_norm) / 1.5)**2)
            coeffs = np.polyfit(x_norm, data, poly_order, w=weights)
            trend = np.polyval(coeffs, x_norm)
        elif method == 'savgol':
            window = min(51, n // 4 * 2 + 1)
            if window < 5:
                window = 5
            if window % 2 == 0:
                window += 1
            trend = signal.savgol_filter(data, window, min(poly_order, window-1))
        else:
            trend = np.zeros_like(data)
        
        return data - trend
    
    def apply_filter(self, data, filter_type='butterworth', cutoff_ratio=0.2, order=4):
        if len(data) < 10:
            return data
        
        try:
            if filter_type == 'butterworth':
                b, a = signal.butter(order, cutoff_ratio, btype='low')
                filtered = signal.filtfilt(b, a, data)
            elif filter_type == 'chebyshev1':
                b, a = signal.cheby1(order, 0.5, cutoff_ratio, btype='low')
                filtered = signal.filtfilt(b, a, data)
            elif filter_type == 'bessel':
                b, a = signal.bessel(order, cutoff_ratio, btype='low')
                filtered = signal.filtfilt(b, a, data)
            elif filter_type == 'savgol':
                window = min(51, len(data) // 4 * 2 + 1)
                if window < 5:
                    window = 5
                if window % 2 == 0:
                    window += 1
                filtered = signal.savgol_filter(data, window, order)
            else:
                filtered = data
        except Exception:
            filtered = data
        
        return filtered
    
    def calculate_involute_angle(self, radius):
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def build_merged_curve(self, side_data, data_type, side, eval_start, eval_end, meas_start, meas_end,
                          preprocess_method='polynomial', poly_order=2):
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
            
            corrected_values = self.preprocess_data(eval_values, method=preprocess_method, poly_order=poly_order)
            
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
    
    def iterative_decomposition(self, angles, values, max_order=None, num_components=10):
        if max_order is None:
            max_order = 5 * self.teeth_count
        
        angles_rad = np.radians(angles)
        residual = np.array(values, dtype=float)
        
        results = []
        extracted_orders = set()
        
        for _ in range(num_components * 2):
            best_order = 0
            best_amplitude = 0
            best_phase = 0
            best_fitted = None
            
            for order in range(1, max_order + 1):
                if order in extracted_orders:
                    continue
                
                cos_term = np.cos(order * angles_rad)
                sin_term = np.sin(order * angles_rad)
                
                A = np.column_stack([cos_term, sin_term])
                coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                
                a, b = coeffs[0], coeffs[1]
                amplitude = np.sqrt(a**2 + b**2)
                
                if amplitude > best_amplitude:
                    best_amplitude = amplitude
                    best_order = order
                    best_phase = np.degrees(np.arctan2(a, b))
                    best_fitted = a * cos_term + b * sin_term
            
            if best_amplitude < 0.001 or best_order == 0:
                break
            
            results.append({
                'order': best_order,
                'amplitude': best_amplitude,
                'phase': best_phase,
                'fitted': best_fitted
            })
            
            extracted_orders.add(best_order)
            residual = residual - best_fitted
            
            if len(results) >= num_components:
                break
        
        results.sort(key=lambda x: x['amplitude'], reverse=True)
        return results[:num_components]

def analyze_direction(profile_data, flank_data, analyzer, direction, preprocess_method, poly_order,
                     filter_type, cutoff_ratio, filter_order, gear_data):
    
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
        return []
    
    angles, values = analyzer.build_merged_curve(
        side_data, data_type, side, eval_start, eval_end, meas_start, meas_end,
        preprocess_method=preprocess_method, poly_order=poly_order
    )
    
    if angles is None or len(angles) < 100:
        return []
    
    interp_angles, interp_values = analyzer.interpolate_curve(angles, values)
    
    filtered = analyzer.apply_filter(interp_values, filter_type=filter_type, 
                                    cutoff_ratio=cutoff_ratio, order=filter_order)
    
    components = analyzer.iterative_decomposition(interp_angles, filtered)
    
    return components

def calculate_error(our_result, klingelnberg_ref):
    errors = []
    for order, ref_amp in klingelnberg_ref.items():
        our_amp = next((c['amplitude'] for c in our_result if abs(c['order'] - order) < 0.5), 0)
        if our_amp > 0:
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
    
    analyzer = ParameterizedRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"齿轮参数: ZE={teeth_count}, m={module}, α={pressure_angle}°, β={helix_angle}°")
    print(f"Profile数据: 左侧{len(profile_data.get('left', {}))}齿, 右侧{len(profile_data.get('right', {}))}齿")
    print(f"Flank数据: 左侧{len(flank_data.get('left', {}))}齿, 右侧{len(flank_data.get('right', {}))}齿")
    
    print("\n" + "=" * 80)
    print("全面参数优化测试")
    print("=" * 80)
    
    preprocess_methods = ['polynomial', 'weighted', 'savgol']
    poly_orders = [2, 3]
    filter_types = ['butterworth', 'chebyshev1', 'bessel', 'savgol']
    cutoff_ratios = [0.1, 0.15, 0.2, 0.25, 0.3]
    filter_orders = [2, 3, 4]
    
    best_config = None
    best_error = float('inf')
    all_results = []
    
    test_count = 0
    total_tests = len(preprocess_methods) * len(poly_orders) * len(filter_types) * len(cutoff_ratios) * len(filter_orders)
    print(f"总测试数: {total_tests}")
    
    for pre_method in preprocess_methods:
        for poly_order in poly_orders:
            for filt_type in filter_types:
                for cutoff in cutoff_ratios:
                    for filt_order in filter_orders:
                        test_count += 1
                        
                        try:
                            lp = analyze_direction(profile_data, flank_data, analyzer, 'left_profile',
                                pre_method, poly_order, filt_type, cutoff, filt_order, gear_data)
                            
                            rp = analyze_direction(profile_data, flank_data, analyzer, 'right_profile',
                                pre_method, poly_order, filt_type, cutoff, filt_order, gear_data)
                            
                            lh = analyze_direction(profile_data, flank_data, analyzer, 'left_helix',
                                pre_method, poly_order, filt_type, cutoff, filt_order, gear_data)
                            
                            rh = analyze_direction(profile_data, flank_data, analyzer, 'right_helix',
                                pre_method, poly_order, filt_type, cutoff, filt_order, gear_data)
                            
                            lp_error = calculate_error(lp, Klingelnberg_REFERENCE['left_profile'])
                            rp_error = calculate_error(rp, Klingelnberg_REFERENCE['right_profile'])
                            lh_error = calculate_error(lh, Klingelnberg_REFERENCE['left_helix'])
                            rh_error = calculate_error(rh, Klingelnberg_REFERENCE['right_helix'])
                            
                            avg_error = (lp_error + rp_error + lh_error + rh_error) / 4
                            
                            result = {
                                'preprocess': pre_method,
                                'poly_order': poly_order,
                                'filter_type': filt_type,
                                'cutoff_ratio': cutoff,
                                'filter_order': filt_order,
                                'lp_error': lp_error,
                                'rp_error': rp_error,
                                'lh_error': lh_error,
                                'rh_error': rh_error,
                                'avg_error': avg_error,
                                'lp': lp,
                                'rp': rp,
                                'lh': lh,
                                'rh': rh
                            }
                            
                            all_results.append(result)
                            
                            if avg_error < best_error:
                                best_error = avg_error
                                best_config = result.copy()
                                print(f"[{test_count}/{total_tests}] 新最佳! 平均误差: {avg_error:.1f}%")
                                print(f"  配置: pre={pre_method}, poly={poly_order}, filt={filt_type}, cutoff={cutoff}, order={filt_order}")
                            
                        except Exception as e:
                            pass
    
    all_results.sort(key=lambda x: x['avg_error'])
    
    print("\n" + "=" * 80)
    print("TOP 10 最佳配置")
    print("=" * 80)
    
    for i, r in enumerate(all_results[:10]):
        print(f"\n#{i+1} 平均误差: {r['avg_error']:.1f}%")
        print(f"  预处理: {r['preprocess']} (多项式阶数: {r['poly_order']})")
        print(f"  滤波器: {r['filter_type']} (截止: {r['cutoff_ratio']}, 阶数: {r['filter_order']})")
        print(f"  各方向误差: LP={r['lp_error']:.1f}%, RP={r['rp_error']:.1f}%, LH={r['lh_error']:.1f}%, RH={r['rh_error']:.1f}%")
    
    print("\n" + "=" * 80)
    print("最佳配置详细结果")
    print("=" * 80)
    
    if best_config:
        print(f"\n最佳配置:")
        print(f"  预处理方法: {best_config['preprocess']}")
        print(f"  多项式阶数: {best_config['poly_order']}")
        print(f"  滤波器类型: {best_config['filter_type']}")
        print(f"  截止频率比: {best_config['cutoff_ratio']}")
        print(f"  滤波器阶数: {best_config['filter_order']}")
        print(f"\n平均误差: {best_config['avg_error']:.1f}%")
        
        print("\n各方向结果对比:")
        for direction, ref_key, result_key in [
            ('Left Profile', 'left_profile', 'lp'),
            ('Right Profile', 'right_profile', 'rp'),
            ('Left Helix', 'left_helix', 'lh'),
            ('Right Helix', 'right_helix', 'rh')
        ]:
            components = best_config[result_key]
            ref = Klingelnberg_REFERENCE[ref_key]
            
            print(f"\n{direction}:")
            print(f"  {'阶次':<8} {'我们的结果':<12} {'Klingelnberg':<12} {'误差':<10}")
            print(f"  {'-'*42}")
            
            for order, ref_amp in ref.items():
                our_amp = next((c['amplitude'] for c in components if abs(c['order'] - order) < 0.5), 0)
                if our_amp > 0:
                    error = abs(our_amp - ref_amp) / ref_amp * 100
                    status = "✅" if error < 10 else "✓" if error < 25 else "⚠"
                    print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}% {status}")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    cutoff_values = sorted(set(r['cutoff_ratio'] for r in all_results))
    cutoff_errors = []
    for c in cutoff_values:
        errors = [r['avg_error'] for r in all_results if r['cutoff_ratio'] == c]
        cutoff_errors.append(np.mean(errors))
    
    axes[0, 0].plot(cutoff_values, cutoff_errors, 'bo-', linewidth=2, markersize=8)
    axes[0, 0].set_xlabel('Cutoff Ratio', fontsize=12)
    axes[0, 0].set_ylabel('Average Error (%)', fontsize=12)
    axes[0, 0].set_title('Cutoff Ratio vs Error', fontsize=14)
    axes[0, 0].grid(True, alpha=0.3)
    
    filter_errors = {}
    for r in all_results:
        ft = r['filter_type']
        if ft not in filter_errors:
            filter_errors[ft] = []
        filter_errors[ft].append(r['avg_error'])
    
    filter_names = list(filter_errors.keys())
    filter_means = [np.mean(filter_errors[ft]) for ft in filter_names]
    
    axes[0, 1].bar(filter_names, filter_means, color=['blue', 'green', 'red', 'orange'])
    axes[0, 1].set_xlabel('Filter Type', fontsize=12)
    axes[0, 1].set_ylabel('Average Error (%)', fontsize=12)
    axes[0, 1].set_title('Filter Type vs Error', fontsize=14)
    axes[0, 1].tick_params(axis='x', rotation=45)
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    pre_errors = {}
    for r in all_results:
        pm = r['preprocess']
        if pm not in pre_errors:
            pre_errors[pm] = []
        pre_errors[pm].append(r['avg_error'])
    
    pre_names = list(pre_errors.keys())
    pre_means = [np.mean(pre_errors[pm]) for pm in pre_names]
    
    axes[1, 0].bar(pre_names, pre_means, color=['purple', 'cyan', 'magenta'])
    axes[1, 0].set_xlabel('Preprocess Method', fontsize=12)
    axes[1, 0].set_ylabel('Average Error (%)', fontsize=12)
    axes[1, 0].set_title('Preprocess Method vs Error', fontsize=14)
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    order_errors = {}
    for r in all_results:
        fo = r['filter_order']
        if fo not in order_errors:
            order_errors[fo] = []
        order_errors[fo].append(r['avg_error'])
    
    order_names = [str(k) for k in sorted(order_errors.keys())]
    order_means = [np.mean(order_errors[int(k)]) for k in order_names]
    
    axes[1, 1].bar(order_names, order_means, color=['brown', 'pink', 'gray'])
    axes[1, 1].set_xlabel('Filter Order', fontsize=12)
    axes[1, 1].set_ylabel('Average Error (%)', fontsize=12)
    axes[1, 1].set_title('Filter Order vs Error', fontsize=14)
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path = os.path.join(current_dir, "parameter_optimization_analysis.png")
    plt.savefig(output_path, dpi=150)
    print(f"\n参数优化分析图已保存: {output_path}")
    
    return best_config, all_results

if __name__ == "__main__":
    best_config, all_results = main()
