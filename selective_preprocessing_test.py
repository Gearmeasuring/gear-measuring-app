"""
尝试选择性预处理方法
关键发现：4阶多项式预处理的174/87比例太低(0.101)，而原始数据的比例(0.410)反而更接近Klingelnberg(0.357)
新策略：选择性预处理 - 只去除低频趋势，保留高阶谐波
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

class SelectivePreprocessor:
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
    
    def selective_preprocess(self, values, low_cutoff=10, high_cutoff=None):
        """
        选择性预处理：只去除低频分量，保留高阶谐波
        low_cutoff: 保留的最低阶次（低于此阶次的将被去除）
        """
        if len(values) < 10:
            return values
        
        n = len(values)
        x = np.linspace(0, 2*np.pi, n, endpoint=False)
        
        # 计算FFT
        fft_result = np.fft.fft(values)
        freqs = np.fft.fftfreq(n, d=1/n)
        
        # 创建滤波器：去除低频，保留高频
        if high_cutoff is None:
            high_cutoff = n // 2
        
        # 创建选择性滤波器
        filter_mask = np.ones(n)
        for i, freq in enumerate(freqs):
            abs_freq = abs(freq)
            if abs_freq < low_cutoff:
                filter_mask[i] = 0  # 去除低频
        
        # 应用滤波器
        filtered_fft = fft_result * filter_mask
        filtered_values = np.real(np.fft.ifft(filtered_fft))
        
        return filtered_values
    
    def preprocess_tooth_data(self, values, method='poly', order=2):
        if len(values) < 5:
            return values
        
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        if method == 'poly':
            coeffs = np.polyfit(x_norm, values, order)
            trend = np.polyval(coeffs, x_norm)
        elif method == 'weighted_poly':
            weights = np.exp(-0.5 * ((x_norm) / 1.5)**2)
            coeffs = np.polyfit(x_norm, values, order, w=weights)
            trend = np.polyval(coeffs, x_norm)
        else:
            return values
        
        return values - trend
    
    def build_merged_curve(self, side_data, data_type, side, eval_start, eval_end, 
                          meas_start, meas_end, preprocess_method='poly', preprocess_order=2,
                          selective_filter=False, low_cutoff=10):
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
            
            if eval_points < 5:
                continue
            
            if selective_filter:
                corrected_values = self.selective_preprocess(eval_values, low_cutoff=low_cutoff)
            else:
                corrected_values = self.preprocess_tooth_data(
                    eval_values, method=preprocess_method, order=preprocess_order
                )
            
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
    
    def compute_full_spectrum(self, angles, values, max_order=None):
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
    
    def iterative_decomposition(self, angles, values, n_cycles=10):
        angles_rad = np.radians(angles)
        residual = values.copy()
        
        components = []
        
        for cycle in range(n_cycles):
            best_order = 0
            best_amplitude = 0
            best_fitted = None
            
            for order in range(1, 5 * self.teeth_count + 1):
                if any(abs(c['order'] - order) < 0.5 for c in components):
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
                    best_fitted = a * cos_term + b * sin_term
            
            if best_amplitude < 0.001 or best_order == 0:
                break
            
            components.append({
                'order': best_order,
                'amplitude': best_amplitude,
                'cycle': cycle + 1
            })
            
            residual = residual - best_fitted
        
        components.sort(key=lambda x: x['amplitude'], reverse=True)
        return components

def calculate_error(our_result, klingelnberg_ref):
    errors = []
    for order, ref_amp in klingelnberg_ref.items():
        our_amp = our_result.get(order, 0)
        if our_amp > 0:
            error = abs(our_amp - ref_amp) / ref_amp * 100
            errors.append(error)
    return np.mean(errors) if errors else 100

def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    print("=" * 90)
    print("选择性预处理方法测试")
    print("=" * 90)
    
    print("\n解析MKA文件...")
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    preprocessor = SelectivePreprocessor(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"\n齿轮参数: ZE={teeth_count}, m={module}")
    
    # 测试选择性滤波器
    print("\n" + "=" * 90)
    print("测试选择性滤波器（只去除低频，保留高阶谐波）")
    print("=" * 90)
    
    side_data = profile_data.get('left', {})
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    meas_start = gear_data.get('profile_meas_start', 0)
    meas_end = gear_data.get('profile_meas_end', 0)
    
    # 测试不同的低频截止值
    low_cutoffs = [5, 10, 15, 20, 30, 40, 50, 60, 70, 80]
    
    print(f"\n{'截止频率':<12} {'87阶次':<10} {'174阶次':<10} {'174/87比例':<12} {'误差':<10}")
    print("-" * 55)
    
    best_cutoff = None
    best_ratio_error = float('inf')
    
    for low_cutoff in low_cutoffs:
        angles, values = preprocessor.build_merged_curve(
            side_data, 'profile', 'left', eval_start, eval_end, meas_start, meas_end,
            selective_filter=True, low_cutoff=low_cutoff
        )
        
        spectrum, _, _ = preprocessor.compute_full_spectrum(angles, values)
        
        amp_87 = spectrum.get(87, 0)
        amp_174 = spectrum.get(174, 0)
        ratio = amp_174 / amp_87 if amp_87 > 0 else 0
        
        # 计算与Klingelnberg比例的误差
        target_ratio = 0.0500 / 0.1400  # 0.357
        ratio_error = abs(ratio - target_ratio) / target_ratio * 100
        
        print(f"{low_cutoff:<12} {amp_87:<10.4f} {amp_174:<10.4f} {ratio:<12.3f} {ratio_error:<10.1f}%")
        
        if ratio_error < best_ratio_error:
            best_ratio_error = ratio_error
            best_cutoff = low_cutoff
    
    print(f"\n最佳截止频率: {best_cutoff} (比例误差: {best_ratio_error:.1f}%)")
    
    # 测试混合预处理方法
    print("\n" + "=" * 90)
    print("测试混合预处理方法（多项式 + 选择性滤波）")
    print("=" * 90)
    
    # 组合测试
    combinations = [
        ('poly_2 + selective_20', 'poly', 2, True, 20),
        ('poly_2 + selective_30', 'poly', 2, True, 30),
        ('poly_3 + selective_20', 'poly', 3, True, 20),
        ('poly_3 + selective_30', 'poly', 3, True, 30),
        ('poly_4 + selective_10', 'poly', 4, True, 10),
        ('weighted_2 + selective_20', 'weighted_poly', 2, True, 20),
    ]
    
    print(f"\n{'方法':<25} {'87阶次':<10} {'174阶次':<10} {'174/87比例':<12} {'平均误差':<10}")
    print("-" * 70)
    
    best_config = None
    best_avg_error = float('inf')
    
    for config_name, method, order, use_selective, cutoff in combinations:
        # 先多项式预处理，再选择性滤波
        angles, values = preprocessor.build_merged_curve(
            side_data, 'profile', 'left', eval_start, eval_end, meas_start, meas_end,
            preprocess_method=method, preprocess_order=order
        )
        
        if angles is not None and use_selective:
            # 对合并后的曲线应用选择性滤波
            spectrum_before, _, interp_values = preprocessor.compute_full_spectrum(angles, values)
            
            # 应用选择性滤波
            n = len(interp_values)
            x = np.linspace(0, 2*np.pi, n, endpoint=False)
            fft_result = np.fft.fft(interp_values)
            freqs = np.fft.fftfreq(n, d=1/n)
            
            filter_mask = np.ones(n)
            for i, freq in enumerate(freqs):
                if abs(freq) < cutoff:
                    filter_mask[i] = 0
            
            filtered_fft = fft_result * filter_mask
            filtered_values = np.real(np.fft.ifft(filtered_fft))
            
            # 重新计算频谱
            angles_rad = np.radians(np.linspace(0, 360, n, endpoint=False))
            spectrum = {}
            for o in [87, 174, 261, 348, 435]:
                cos_term = np.cos(o * angles_rad)
                sin_term = np.sin(o * angles_rad)
                A = np.column_stack([cos_term, sin_term])
                coeffs, _, _, _ = np.linalg.lstsq(A, filtered_values, rcond=None)
                a, b = coeffs[0], coeffs[1]
                spectrum[o] = np.sqrt(a**2 + b**2)
        else:
            spectrum, _, _ = preprocessor.compute_full_spectrum(angles, values)
        
        amp_87 = spectrum.get(87, 0)
        amp_174 = spectrum.get(174, 0)
        ratio = amp_174 / amp_87 if amp_87 > 0 else 0
        
        # 计算所有参考阶次的平均误差
        ref = Klingelnberg_REFERENCE['left_profile']
        errors = []
        for o, ref_amp in ref.items():
            our_amp = spectrum.get(o, 0)
            if our_amp > 0:
                error = abs(our_amp - ref_amp) / ref_amp * 100
                errors.append(error)
        avg_error = np.mean(errors) if errors else 100
        
        print(f"{config_name:<25} {amp_87:<10.4f} {amp_174:<10.4f} {ratio:<12.3f} {avg_error:<10.1f}%")
        
        if avg_error < best_avg_error:
            best_avg_error = avg_error
            best_config = config_name
    
    print(f"\n最佳配置: {best_config} (平均误差: {best_avg_error:.1f}%)")
    
    # 最终分析：使用最佳配置分析所有方向
    print("\n" + "=" * 90)
    print("最终分析：使用选择性滤波方法分析所有方向")
    print("=" * 90)
    
    directions = ['left_profile', 'right_profile', 'left_helix', 'right_helix']
    direction_names = {
        'left_profile': 'Left Profile',
        'right_profile': 'Right Profile',
        'left_helix': 'Left Helix',
        'right_helix': 'Right Helix'
    }
    
    for direction in directions:
        if direction == 'left_profile':
            sd = profile_data.get('left', {})
            data_type = 'profile'
            side = 'left'
            es = gear_data.get('profile_eval_start', 0)
            ee = gear_data.get('profile_eval_end', 0)
            ms = gear_data.get('profile_meas_start', 0)
            me = gear_data.get('profile_meas_end', 0)
        elif direction == 'right_profile':
            sd = profile_data.get('right', {})
            data_type = 'profile'
            side = 'right'
            es = gear_data.get('profile_eval_start', 0)
            ee = gear_data.get('profile_eval_end', 0)
            ms = gear_data.get('profile_meas_start', 0)
            me = gear_data.get('profile_meas_end', 0)
        elif direction == 'left_helix':
            sd = flank_data.get('left', {})
            data_type = 'helix'
            side = 'left'
            es = gear_data.get('helix_eval_start', 0)
            ee = gear_data.get('helix_eval_end', 0)
            ms = gear_data.get('helix_meas_start', 0)
            me = gear_data.get('helix_meas_end', 0)
        else:
            sd = flank_data.get('right', {})
            data_type = 'helix'
            side = 'right'
            es = gear_data.get('helix_eval_start', 0)
            ee = gear_data.get('helix_eval_end', 0)
            ms = gear_data.get('helix_meas_start', 0)
            me = gear_data.get('helix_meas_end', 0)
        
        # 使用选择性滤波
        angles, values = preprocessor.build_merged_curve(
            sd, data_type, side, es, ee, ms, me,
            selective_filter=True, low_cutoff=best_cutoff
        )
        
        if angles is None:
            continue
        
        spectrum, _, _ = preprocessor.compute_full_spectrum(angles, values)
        ref = Klingelnberg_REFERENCE[direction]
        
        print(f"\n{direction_names[direction]}:")
        print(f"  {'阶次':<8} {'我们的结果':<12} {'Klingelnberg':<12} {'误差':<10}")
        print(f"  {'-'*45}")
        
        for order in sorted(ref.keys()):
            our_amp = spectrum.get(order, 0)
            ref_amp = ref[order]
            error = abs(our_amp - ref_amp) / ref_amp * 100 if our_amp > 0 else 100
            status = "✅" if error < 10 else "✓" if error < 25 else "⚠" if error < 50 else "✗"
            print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}% {status}")

if __name__ == "__main__":
    main()
