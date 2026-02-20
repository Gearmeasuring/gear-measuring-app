"""
改进版波纹度分析器 - 匹配Klingelnberg结果

改进内容：
1. 预处理：使用更精确的鼓形/斜率去除方法
2. 低通滤波器：模拟Klingelnberg的RC滤波器
3. 迭代算法：改进收敛条件和提取策略
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy import signal
from scipy.ndimage import uniform_filter1d

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


class ImprovedRippleAnalyzer:
    """改进版波纹度分析器"""
    
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
        
        print(f"齿轮参数:")
        print(f"  齿数 ZE = {teeth_count}")
        print(f"  模数 m = {module} mm")
        print(f"  压力角 α = {pressure_angle}°")
        print(f"  螺旋角 β₀ = {helix_angle}°")
        print(f"  节圆直径 D₀ = {self.pitch_diameter:.3f} mm")
        print(f"  基圆直径 db = {self.base_diameter:.3f} mm")
        print(f"  节距角 τ = {self.pitch_angle:.4f}°")
    
    def remove_crowning_improved(self, data, method='polynomial'):
        """
        改进的鼓形去除方法
        
        方法：
        1. polynomial: 多项式拟合（默认）
        2. spline: 样条拟合
        3. moving_average: 移动平均
        """
        if len(data) < 5:
            return data, data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n)
        
        if method == 'polynomial':
            # 使用更高阶多项式拟合鼓形
            # 先尝试2阶，如果残差大则尝试更高阶
            best_coeffs = np.polyfit(x, data, 2)
            crowning_curve = np.polyval(best_coeffs, x)
            
            # 检查残差，如果太大则使用3阶
            residual = data - crowning_curve
            if np.std(residual) > 0.5 * np.std(data):
                best_coeffs = np.polyfit(x, data, 3)
                crowning_curve = np.polyval(best_coeffs, x)
        
        elif method == 'spline':
            from scipy.interpolate import UnivariateSpline
            # 使用样条拟合
            spline = UnivariateSpline(x, data, k=3, s=len(data) * 0.1)
            crowning_curve = spline(x)
        
        elif method == 'moving_average':
            # 移动平均
            window = max(5, n // 10)
            crowning_curve = uniform_filter1d(data, size=window, mode='nearest')
        
        else:
            crowning_curve = np.zeros_like(data)
        
        return data - crowning_curve, crowning_curve
    
    def remove_slope_improved(self, data, method='linear'):
        """
        改进的斜率去除方法
        
        方法：
        1. linear: 线性拟合（默认）
        2. robust: 鲁棒拟合（抗异常值）
        3. detrend: scipy去趋势
        """
        if len(data) < 3:
            return data, data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n)
        
        if method == 'linear':
            coeffs = np.polyfit(x, data, 1)
            slope_curve = np.polyval(coeffs, x)
        
        elif method == 'robust':
            # 使用RANSAC或Theil-Sen估计
            from scipy.stats import theilslopes
            result = theilslopes(data, x, 0.95)
            slope_curve = result[0] * x + result[1]
        
        elif method == 'detrend':
            from scipy.signal import detrend
            slope_curve = data - detrend(data)
        
        else:
            slope_curve = np.zeros_like(data)
        
        return data - slope_curve, slope_curve
    
    def apply_lowpass_filter(self, data, cutoff_ratio=0.5):
        """
        应用低通滤波器
        
        模拟Klingelnberg的"Low-pass filter RC 100000:1"
        
        Args:
            data: 输入数据
            cutoff_ratio: 截止频率比例（相对于奈奎斯特频率）
        """
        if len(data) < 10:
            return data
        
        # 使用Butterworth低通滤波器
        nyquist = 0.5 * len(data)
        cutoff = cutoff_ratio * nyquist
        
        if cutoff <= 0:
            return data
        
        # 设计滤波器
        b, a = signal.butter(2, cutoff_ratio, btype='low')
        
        # 应用滤波器（正向和反向，避免相位偏移）
        filtered = signal.filtfilt(b, a, data)
        
        return filtered
    
    def preprocess_data(self, data, crowning_method='polynomial', 
                        slope_method='linear', apply_filter=False):
        """
        完整的数据预处理流程
        
        1. 去除鼓形
        2. 去除斜率
        3. 可选：低通滤波
        """
        # 去除鼓形
        data_after_crowning, crowning = self.remove_crowning_improved(data, crowning_method)
        
        # 去除斜率
        data_after_slope, slope = self.remove_slope_improved(data_after_crowning, slope_method)
        
        # 可选：低通滤波
        if apply_filter:
            data_final = self.apply_lowpass_filter(data_after_slope)
        else:
            data_final = data_after_slope
        
        return data_final, crowning, slope
    
    def calculate_involute_angle(self, radius):
        """计算渐开线极角"""
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def build_merged_curve(self, data_dict, data_type, side,
                           eval_start, eval_end, meas_start, meas_end,
                           crowning_method='polynomial', slope_method='linear'):
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
            
            if eval_points < 5:
                continue
            
            # 使用改进的预处理
            corrected_values, _, _ = self.preprocess_data(
                eval_values, crowning_method, slope_method
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
    
    def interpolate_curve(self, angles, values, num_points=None):
        """插值到均匀采样"""
        if num_points is None:
            num_points = max(360, 2 * 5 * self.teeth_count + 10)
        
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        return interp_angles, interp_values
    
    def fit_sine_wave(self, angles_rad, values, order):
        """使用最小二乘法拟合正弦波"""
        cos_term = np.cos(order * angles_rad)
        sin_term = np.sin(order * angles_rad)
        
        A = np.column_stack([cos_term, sin_term])
        coeffs, residuals, rank, s = np.linalg.lstsq(A, values, rcond=None)
        
        a, b = coeffs[0], coeffs[1]
        amplitude = np.sqrt(a**2 + b**2)
        phase = np.degrees(np.arctan2(a, b))
        
        fitted = a * cos_term + b * sin_term
        
        return amplitude, phase, fitted
    
    def iterative_decomposition_improved(self, angles, values, max_order=None, 
                                          num_components=10, convergence_threshold=0.001):
        """
        改进的迭代正弦波分解算法
        
        改进：
        1. 添加收敛阈值
        2. 允许重复提取同一阶次（如果振幅仍然较大）
        3. 使用全局优化
        """
        if max_order is None:
            max_order = 5 * self.teeth_count
        
        angles_rad = np.radians(angles)
        residual = np.array(values, dtype=float)
        
        results = []
        extracted_orders = {}  # 记录每个阶次被提取的次数
        
        for iteration in range(num_components * 2):  # 允许更多迭代
            # 寻找振幅最大的阶次
            best_order = 0
            best_amplitude = 0
            best_phase = 0
            best_fitted = None
            
            for order in range(1, max_order + 1):
                # 检查该阶次是否已被提取多次
                if extracted_orders.get(order, 0) >= 2:
                    continue
                
                amplitude, phase, fitted = self.fit_sine_wave(angles_rad, residual, order)
                
                if amplitude > best_amplitude:
                    best_amplitude = amplitude
                    best_order = order
                    best_phase = phase
                    best_fitted = fitted
            
            # 检查收敛
            if best_amplitude < convergence_threshold:
                break
            
            # 检查是否已经提取过该阶次
            if extracted_orders.get(best_order, 0) > 0:
                # 如果已经提取过，检查振幅是否显著
                prev_amp = results[extracted_orders[best_order] - 1]['amplitude']
                if best_amplitude < prev_amp * 0.1:  # 新振幅小于之前的10%
                    break
            
            # 记录结果
            results.append({
                'order': best_order,
                'amplitude': best_amplitude,
                'phase': best_phase,
                'fitted': best_fitted
            })
            
            # 更新残差
            residual = residual - best_fitted
            
            # 更新提取记录
            extracted_orders[best_order] = len(results)
            
            if len(results) >= num_components:
                break
        
        # 按振幅排序
        results.sort(key=lambda x: x['amplitude'], reverse=True)
        
        return results[:num_components]
    
    def analyze(self, data_dict, data_type, side,
                eval_start, eval_end, meas_start, meas_end,
                crowning_method='polynomial', slope_method='linear'):
        """完整分析流程"""
        angles, values = self.build_merged_curve(
            data_dict, data_type, side,
            eval_start, eval_end, meas_start, meas_end,
            crowning_method, slope_method
        )
        
        if angles is None:
            return None
        
        # 插值
        interp_angles, interp_values = self.interpolate_curve(angles, values)
        
        # 改进的迭代分解
        results = self.iterative_decomposition_improved(
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


def compare_methods():
    """比较不同预处理方法的效果"""
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print("="*70)
    print("改进版波纹度分析 - 匹配Klingelnberg结果")
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
    
    analyzer = ImprovedRippleAnalyzer(
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
    
    # 测试不同预处理方法组合
    methods = [
        ('polynomial', 'linear'),
        ('polynomial', 'robust'),
        ('spline', 'linear'),
        ('moving_average', 'linear')
    ]
    
    print("\n" + "="*70)
    print("测试不同预处理方法组合")
    print("="*70)
    
    best_results = {}
    
    for crowning_method, slope_method in methods:
        print(f"\n预处理方法: 鼓形={crowning_method}, 斜率={slope_method}")
        print("-" * 50)
        
        analyses = []
        
        # 左齿形
        result = analyzer.analyze(
            profile_data, 'profile', 'left',
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end,
            crowning_method, slope_method
        )
        if result:
            analyses.append(('Left Profile', result))
        
        # 右齿形
        result = analyzer.analyze(
            profile_data, 'profile', 'right',
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end,
            crowning_method, slope_method
        )
        if result:
            analyses.append(('Right Profile', result))
        
        # 左齿向
        result = analyzer.analyze(
            flank_data, 'helix', 'left',
            helix_eval_start, helix_eval_end,
            helix_meas_start, helix_meas_end,
            crowning_method, slope_method
        )
        if result:
            analyses.append(('Left Helix', result))
        
        # 右齿向
        result = analyzer.analyze(
            flank_data, 'helix', 'right',
            helix_eval_start, helix_eval_end,
            helix_meas_start, helix_meas_end,
            crowning_method, slope_method
        )
        if result:
            analyses.append(('Right Helix', result))
        
        # 计算与Klingelnberg的匹配度
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
        
        # 保存最佳结果
        if crowning_method == 'polynomial' and slope_method == 'linear':
            for name, result in analyses:
                best_results[name] = result
    
    # 输出最终结果对比
    print("\n" + "="*70)
    print("最终结果对比（使用polynomial+linear）")
    print("="*70)
    
    for name in ['Left Profile', 'Right Profile', 'Left Helix', 'Right Helix']:
        if name in best_results:
            result = best_results[name]
            ref = klingelnberg_ref.get(name, {})
            
            print(f"\n{name}:")
            print(f"{'阶次':<8} {'我们的结果':<12} {'Klingelnberg':<12} {'误差':<10}")
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
    
    print("\n" + "="*70)
    print("完成！")
    print("="*70)


if __name__ == '__main__':
    compare_methods()
