"""
继续改进波纹度分析算法

改进方向：
1. 使用FFT直接计算频谱（而不是迭代分解）
2. 添加更强的低通滤波器
3. 尝试不同的窗函数
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy import signal
from scipy.fft import fft, fftfreq

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


class FFTBasedRippleAnalyzer:
    """基于FFT的波纹度分析器"""
    
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
    
    def remove_slope_and_crowning(self, data):
        """去除斜率和鼓形"""
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
    
    def calculate_involute_angle(self, radius):
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def build_merged_curve(self, data_dict, data_type, side,
                           eval_start, eval_end, meas_start, meas_end):
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
        """插值到均匀采样"""
        if num_points is None:
            num_points = max(1024, 2 * 5 * self.teeth_count + 10)
        
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        return interp_angles, interp_values
    
    def apply_lowpass_filter(self, values, cutoff_order, num_points):
        """
        应用低通滤波器
        
        Args:
            values: 输入信号
            cutoff_order: 截止阶次（waves/rev）
            num_points: 采样点数
        """
        # 设计低通滤波器
        nyquist = num_points / 2  # 奈奎斯特频率（对应num_points/2阶）
        cutoff_ratio = cutoff_order / nyquist
        
        if cutoff_ratio >= 1:
            return values
        
        # 使用Butterworth滤波器
        b, a = signal.butter(4, cutoff_ratio, btype='low')
        filtered = signal.filtfilt(b, a, values)
        
        return filtered
    
    def compute_spectrum_fft(self, values, window='hann'):
        """
        使用FFT计算频谱
        
        Args:
            values: 输入信号
            window: 窗函数类型
        """
        n = len(values)
        
        # 应用窗函数
        if window == 'hann':
            w = np.hanning(n)
        elif window == 'hamming':
            w = np.hamming(n)
        elif window == 'blackman':
            w = np.blackman(n)
        elif window == 'flattop':
            w = signal.windows.flattop(n)
        else:
            w = np.ones(n)
        
        windowed = values * w
        
        # FFT
        fft_result = fft(windowed)
        
        # 计算频率（阶次）
        orders = fftfreq(n, d=1.0/n)
        
        # 计算振幅（单边谱）
        # 使用窗函数的等效噪声带宽进行校正
        if window == 'hann':
            enbw = 1.5  # 等效噪声带宽
        elif window == 'hamming':
            enbw = 1.36
        elif window == 'blackman':
            enbw = 1.73
        elif window == 'flattop':
            enbw = 3.77
        else:
            enbw = 1.0
        
        amplitudes = 2.0 * np.abs(fft_result) / (n * np.mean(w))
        
        # 只取正频率部分
        positive_mask = orders >= 0
        orders = orders[positive_mask]
        amplitudes = amplitudes[positive_mask]
        
        return orders, amplitudes
    
    def extract_peaks(self, orders, amplitudes, max_order, num_peaks=10):
        """提取频谱峰值"""
        # 只考虑正整数阶次
        valid_mask = (orders >= 1) & (orders <= max_order)
        valid_orders = orders[valid_mask]
        valid_amplitudes = amplitudes[valid_mask]
        
        # 找峰值
        peak_indices = signal.find_peaks(valid_amplitudes, height=0.001, distance=5)[0]
        
        if len(peak_indices) == 0:
            return []
        
        # 按振幅排序
        peak_amplitudes = valid_amplitudes[peak_indices]
        sorted_indices = np.argsort(peak_amplitudes)[::-1][:num_peaks]
        
        results = []
        for idx in sorted_indices:
            peak_idx = peak_indices[idx]
            order = int(round(valid_orders[peak_idx]))
            amplitude = valid_amplitudes[peak_idx]
            results.append({
                'order': order,
                'amplitude': amplitude
            })
        
        return results
    
    def analyze_with_fft(self, data_dict, data_type, side,
                         eval_start, eval_end, meas_start, meas_end,
                         apply_filter=False, cutoff_order=None,
                         window='hann'):
        """使用FFT方法分析"""
        angles, values = self.build_merged_curve(
            data_dict, data_type, side,
            eval_start, eval_end, meas_start, meas_end
        )
        
        if angles is None:
            return None
        
        # 插值
        interp_angles, interp_values = self.interpolate_curve(angles, values)
        num_points = len(interp_values)
        
        # 可选：低通滤波
        if apply_filter and cutoff_order:
            interp_values = self.apply_lowpass_filter(interp_values, cutoff_order, num_points)
        
        # FFT频谱
        orders, amplitudes = self.compute_spectrum_fft(interp_values, window)
        
        # 提取峰值
        max_order = 5 * self.teeth_count
        peaks = self.extract_peaks(orders, amplitudes, max_order, num_peaks=10)
        
        return {
            'angles': angles,
            'values': values,
            'interp_angles': interp_angles,
            'interp_values': interp_values,
            'fft_orders': orders,
            'fft_amplitudes': amplitudes,
            'peaks': peaks
        }


def main():
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print("="*70)
    print("基于FFT的波纹度分析 - 匹配Klingelnberg结果")
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
    
    analyzer = FFTBasedRippleAnalyzer(
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
    
    # 测试不同配置
    configs = [
        {'window': 'hann', 'apply_filter': False, 'name': 'Hann窗'},
        {'window': 'hamming', 'apply_filter': False, 'name': 'Hamming窗'},
        {'window': 'blackman', 'apply_filter': False, 'name': 'Blackman窗'},
        {'window': 'flattop', 'apply_filter': False, 'name': 'Flat-top窗'},
        {'window': 'hann', 'apply_filter': True, 'cutoff_order': 435, 'name': 'Hann窗+低通(435阶)'},
        {'window': 'hann', 'apply_filter': True, 'cutoff_order': 300, 'name': 'Hann窗+低通(300阶)'},
    ]
    
    print("\n" + "="*70)
    print("测试不同FFT配置")
    print("="*70)
    
    best_config = None
    best_error = float('inf')
    best_results = {}
    
    for config in configs:
        print(f"\n配置: {config['name']}")
        print("-" * 50)
        
        analyses = []
        
        # 分析四个方向
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
            result = analyzer.analyze_with_fft(
                data_dict, data_type, side,
                eval_s, eval_e, meas_s, meas_e,
                apply_filter=config.get('apply_filter', False),
                cutoff_order=config.get('cutoff_order'),
                window=config['window']
            )
            if result:
                analyses.append((name, result))
        
        # 计算误差
        total_error = 0
        count = 0
        
        for name, result in analyses:
            if name in klingelnberg_ref:
                ref = klingelnberg_ref[name]
                for peak in result['peaks'][:5]:
                    order = peak['order']
                    amp = peak['amplitude']
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
            print(f"{'阶次':<8} {'FFT振幅':<12} {'Klingelnberg':<12} {'误差':<10}")
            print("-" * 45)
            
            for peak in result['peaks'][:5]:
                order = peak['order']
                amp = peak['amplitude']
                if order in ref:
                    ref_amp = ref[order]
                    error = (amp - ref_amp) / ref_amp * 100
                    print(f"{order:<8} {amp:<12.4f} {ref_amp:<12.4f} {error:+.1f}%")
                else:
                    print(f"{order:<8} {amp:<12.4f} {'N/A':<12} {'-':<10}")
    
    # 生成频谱图
    print("\n" + "="*70)
    print("生成频谱图...")
    print("="*70)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'FFT Spectrum Analysis (Best Config: {best_config["name"]})\nZE={teeth_count}, m={module}', 
                fontsize=14, fontweight='bold')
    
    for idx, name in enumerate(['Left Profile', 'Right Profile', 'Left Helix', 'Right Helix']):
        if name not in best_results:
            continue
        
        result = best_results[name]
        ax = axes[idx // 2, idx % 2]
        
        # 只显示前200阶
        max_order_plot = 200
        mask = (result['fft_orders'] >= 0) & (result['fft_orders'] <= max_order_plot)
        orders = result['fft_orders'][mask]
        amplitudes = result['fft_amplitudes'][mask]
        
        # 标记高阶分量
        colors = ['red' if o >= teeth_count else 'steelblue' for o in orders]
        
        ax.bar(orders, amplitudes, color=colors, alpha=0.7, width=0.8)
        
        # 标记关键阶次
        for order in [87, 174, 261]:
            ax.axvline(x=order, color='green', linestyle='--', alpha=0.5, linewidth=1)
        
        ax.set_xlabel('Order (waves/rev)', fontsize=10)
        ax.set_ylabel('Amplitude (μm)', fontsize=10)
        ax.set_title(f'{name}', fontsize=11, fontweight='bold')
        ax.set_xlim(0, max_order_plot)
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_file = os.path.join(current_dir, 'fft_spectrum_best_config.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"保存: {output_file}")
    plt.close()
    
    print("\n" + "="*70)
    print("完成！")
    print("="*70)


if __name__ == '__main__':
    main()
