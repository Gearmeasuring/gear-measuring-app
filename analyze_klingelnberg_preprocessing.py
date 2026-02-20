"""
分析Klingelnberg可能使用的预处理方法

通过对比结果推断：
1. 87阶振幅接近 → 基本预处理正确
2. 174阶振幅偏高约60% → 可能使用了更强的低通滤波
3. 高阶分量偏低 → 可能使用了频域滤波

测试方向：
1. 不同强度的低通滤波器
2. 频域滤波（直接在频域去除高频分量）
3. 组合滤波方法
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy import signal

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


class PreprocessingAnalyzer:
    """预处理方法分析器"""
    
    def __init__(self, teeth_count, module, pressure_angle=20.0, 
                 helix_angle=0.0, base_diameter=0.0):
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
    
    def remove_slope_and_crowning(self, data):
        """基本预处理：去除斜率和鼓形"""
        if len(data) < 3:
            return data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        crowning_coeffs = np.polyfit(x_norm, data, 2)
        crowning_curve = np.polyval(crowning_coeffs, x_norm)
        data_after_crowning = data - crowning_curve
        
        slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
        slope_curve = np.polyval(slope_coeffs, x_norm)
        corrected_data = data_after_crowning - slope_curve
        
        return corrected_data
    
    def remove_slope_and_crowning_weighted(self, data, weight_center=True):
        """加权预处理：中心权重更高"""
        if len(data) < 3:
            return data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        # 创建权重（中心权重更高）
        if weight_center:
            weights = np.exp(-0.5 * x_norm**2)
        else:
            weights = np.ones(n)
        
        # 加权多项式拟合
        crowning_coeffs = np.polyfit(x, data, 2, w=weights)
        crowning_curve = np.polyval(crowning_coeffs, x)
        data_after_crowning = data - crowning_curve
        
        slope_coeffs = np.polyfit(x, data_after_crowning, 1, w=weights)
        slope_curve = np.polyval(slope_coeffs, x)
        corrected_data = data_after_crowning - slope_curve
        
        return corrected_data
    
    def remove_slope_and_crowning_robust(self, data):
        """鲁棒预处理：使用RANSAC抗异常值"""
        if len(data) < 3:
            return data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n)
        
        # 使用Theil-Sen估计（鲁棒线性回归）
        from scipy.stats import theilslopes
        
        # 先去除鼓形（使用中位数滤波）
        from scipy.ndimage import median_filter
        smoothed = median_filter(data, size=max(3, n//20))
        crowning_curve = smoothed - np.median(data)
        data_after_crowning = data - crowning_curve
        
        # 鲁棒斜率估计
        result = theilslopes(data_after_crowning, x, 0.95)
        slope_curve = result[0] * x + result[1]
        corrected_data = data_after_crowning - slope_curve
        
        return corrected_data
    
    def apply_lowpass_filter(self, data, cutoff_ratio, order=4):
        """应用低通滤波器"""
        if len(data) < 10:
            return data
        
        b, a = signal.butter(order, cutoff_ratio, btype='low')
        filtered = signal.filtfilt(b, a, data)
        
        return filtered
    
    def apply_frequency_domain_filter(self, data, max_order, num_points=None):
        """
        频域滤波：直接在频域去除高频分量
        
        这可能是Klingelnberg使用的方法
        """
        if num_points is None:
            num_points = len(data)
        
        # FFT
        fft_result = np.fft.fft(data, n=num_points)
        
        # 创建频域滤波器
        freqs = np.fft.fftfreq(num_points)
        orders = np.abs(freqs) * num_points  # 转换为阶次
        
        # 保留低频分量
        mask = orders <= max_order
        fft_filtered = fft_result * mask
        
        # 逆FFT
        filtered = np.real(np.fft.ifft(fft_filtered))
        
        return filtered[:len(data)]
    
    def calculate_involute_angle(self, radius):
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def build_merged_curve(self, data_dict, data_type, side,
                           eval_start, eval_end, meas_start, meas_end,
                           preprocess_method='basic'):
        """构建合并曲线"""
        if side not in data_dict or not data_dict[side]:
            return None, None
        
        side_data = data_dict[side]
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
            
            # 选择预处理方法
            if preprocess_method == 'basic':
                corrected_values = self.remove_slope_and_crowning(eval_values)
            elif preprocess_method == 'weighted':
                corrected_values = self.remove_slope_and_crowning_weighted(eval_values)
            elif preprocess_method == 'robust':
                corrected_values = self.remove_slope_and_crowning_robust(eval_values)
            else:
                corrected_values = self.remove_slope_and_crowning(eval_values)
            
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
        """迭代正弦波分解"""
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
                'phase': best_phase
            })
            
            extracted_orders.add(best_order)
            residual = residual - best_fitted
            
            if len(results) >= num_components:
                break
        
        results.sort(key=lambda x: x['amplitude'], reverse=True)
        return results[:num_components]
    
    def analyze(self, data_dict, data_type, side,
                eval_start, eval_end, meas_start, meas_end,
                preprocess_method='basic',
                apply_filter=False, filter_cutoff=None,
                apply_freq_filter=False, freq_max_order=None):
        """完整分析流程"""
        angles, values = self.build_merged_curve(
            data_dict, data_type, side,
            eval_start, eval_end, meas_start, meas_end,
            preprocess_method
        )
        
        if angles is None:
            return None
        
        # 插值
        interp_angles, interp_values = self.interpolate_curve(angles, values)
        
        # 可选：低通滤波
        if apply_filter and filter_cutoff:
            interp_values = self.apply_lowpass_filter(interp_values, filter_cutoff)
        
        # 可选：频域滤波
        if apply_freq_filter and freq_max_order:
            interp_values = self.apply_frequency_domain_filter(
                interp_values, freq_max_order, len(interp_values)
            )
        
        # 迭代分解
        results = self.iterative_decomposition(
            interp_angles, interp_values,
            max_order=5 * self.teeth_count,
            num_components=10
        )
        
        return {
            'angles': angles,
            'values': values,
            'interp_angles': interp_angles,
            'interp_values': interp_values,
            'results': results
        }


def main():
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print("="*70)
    print("分析Klingelnberg可能使用的预处理方法")
    print("="*70)
    print(f"文件: {mka_file}")
    print()
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    analyzer = PreprocessingAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    helix_meas_start = gear_data.get('helix_meas_start', 0)
    helix_meas_end = gear_data.get('helix_meas_end', 0)
    
    # Klingelnberg参考值
    klingelnberg_ref = {
        'Left Profile': {87: 0.14, 174: 0.05, 261: 0.14, 348: 0.03, 435: 0.04},
        'Right Profile': {87: 0.15, 174: 0.05, 261: 0.06, 348: 0.07, 435: 0.03},
        'Left Helix': {87: 0.12, 89: 0.07, 174: 0.06, 261: 0.05, 348: 0.03},
        'Right Helix': {87: 0.09, 174: 0.10, 261: 0.05, 348: 0.04, 435: 0.03}
    }
    
    # 测试不同的预处理组合
    configs = [
        {'name': '基本预处理', 'preprocess': 'basic', 'filter': False, 'freq_filter': False},
        {'name': '加权预处理', 'preprocess': 'weighted', 'filter': False, 'freq_filter': False},
        {'name': '鲁棒预处理', 'preprocess': 'robust', 'filter': False, 'freq_filter': False},
        {'name': '基本+低通(0.3)', 'preprocess': 'basic', 'filter': True, 'cutoff': 0.3, 'freq_filter': False},
        {'name': '基本+低通(0.2)', 'preprocess': 'basic', 'filter': True, 'cutoff': 0.2, 'freq_filter': False},
        {'name': '基本+频域滤波(300阶)', 'preprocess': 'basic', 'filter': False, 'freq_filter': True, 'freq_max': 300},
        {'name': '基本+频域滤波(200阶)', 'preprocess': 'basic', 'filter': False, 'freq_filter': True, 'freq_max': 200},
        {'name': '加权+频域滤波(250阶)', 'preprocess': 'weighted', 'filter': False, 'freq_filter': True, 'freq_max': 250},
        {'name': '鲁棒+频域滤波(250阶)', 'preprocess': 'robust', 'filter': False, 'freq_filter': True, 'freq_max': 250},
    ]
    
    print("\n" + "="*70)
    print("测试不同预处理组合")
    print("="*70)
    
    best_config = None
    best_error = float('inf')
    best_results = {}
    
    for config in configs:
        print(f"\n配置: {config['name']}")
        print("-" * 50)
        
        analyses = []
        
        for data_type, data_dict, eval_s, eval_e, meas_s, meas_e, name in [
            ('profile', profile_data, profile_eval_start, profile_eval_end, 
             profile_meas_start, profile_meas_end, 'Left Profile'),
            ('profile', profile_data, profile_eval_start, profile_eval_end, 
             profile_meas_start, profile_meas_end, 'Right Profile'),
            ('helix', flank_data, helix_eval_start, helix_eval_end, 
             helix_meas_start, helix_meas_end, 'Left Helix'),
            ('helix', flank_data, helix_eval_start, helix_eval_end, 
             helix_meas_start, helix_meas_end, 'Right Helix'),
        ]:
            side = 'left' if 'Left' in name else 'right'
            result = analyzer.analyze(
                data_dict, data_type, side,
                eval_s, eval_e, meas_s, meas_e,
                preprocess_method=config['preprocess'],
                apply_filter=config.get('filter', False),
                filter_cutoff=config.get('cutoff'),
                apply_freq_filter=config.get('freq_filter', False),
                freq_max_order=config.get('freq_max')
            )
            if result:
                analyses.append((name, result))
        
        # 计算误差
        total_error = 0
        count = 0
        
        for name, result in analyses:
            if name in klingelnberg_ref:
                ref = klingelnberg_ref[name]
                for r in result['results'][:5]:
                    order = r['order']
                    amp = r['amplitude']
                    if order in ref:
                        ref_amp = ref[order]
                        error = abs(amp - ref_amp) / ref_amp
                        total_error += error
                        count += 1
        
        avg_error = total_error / count if count > 0 else float('inf')
        print(f"平均误差: {avg_error*100:.1f}%")
        
        if avg_error < best_error:
            best_error = avg_error
            best_config = config
            for name, result in analyses:
                best_results[name] = result
    
    # 输出最佳结果
    print("\n" + "="*70)
    print(f"最佳配置: {best_config['name']}")
    print("="*70)
    
    for name in ['Left Profile', 'Right Profile', 'Left Helix', 'Right Helix']:
        if name in best_results:
            result = best_results[name]
            ref = klingelnberg_ref.get(name, {})
            
            print(f"\n{name}:")
            print(f"{'阶次':<8} {'振幅':<12} {'Klingelnberg':<12} {'误差':<10}")
            print("-" * 45)
            
            for r in result['results'][:5]:
                order = r['order']
                amp = r['amplitude']
                if order in ref:
                    ref_amp = ref[order]
                    error = (amp - ref_amp) / ref_amp * 100
                    print(f"{order:<8} {amp:<12.4f} {ref_amp:<12.4f} {error:+.1f}%")
                else:
                    print(f"{order:<8} {amp:<12.4f} {'N/A':<12} {'-':<10}")
    
    # 分析结论
    print("\n" + "="*70)
    print("分析结论")
    print("="*70)
    print()
    print("根据对比分析，Klingelnberg可能使用了以下预处理方法：")
    print()
    print("1. 预处理方法：")
    print("   - 可能使用了加权或鲁棒的鼓形/斜率去除方法")
    print("   - 中心区域的权重更高")
    print()
    print("2. 滤波方法：")
    print("   - 可能使用了频域滤波（直接在频域去除高频分量）")
    print("   - 截止阶次可能在200-300阶左右")
    print()
    print("3. 关键发现：")
    print("   - 87阶振幅匹配良好 → 基本预处理正确")
    print("   - 174阶振幅偏高 → 需要更强的滤波")
    print("   - 高阶分量偏低 → 频域滤波效果好")
    print()
    print(f"最佳配置: {best_config['name']}")
    print(f"平均误差: {best_error*100:.1f}%")


if __name__ == '__main__':
    main()
