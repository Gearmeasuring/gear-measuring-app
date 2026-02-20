"""
尝试使用FFT方法计算振幅
关键发现：174/87比例系统性偏高，可能是振幅计算方法的问题
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
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

class FFTAmplitudeAnalyzer:
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
    
    def preprocess_tooth_data(self, values, order=2):
        if len(values) < 5:
            return values
        
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        coeffs = np.polyfit(x_norm, values, order)
        trend = np.polyval(coeffs, x_norm)
        
        return values - trend
    
    def build_merged_curve(self, side_data, data_type, side, eval_start, eval_end, meas_start, meas_end, preprocess_order=3):
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
            
            corrected_values = self.preprocess_tooth_data(eval_values, order=preprocess_order)
            
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
    
    def compute_spectrum_fft(self, angles, values, max_order=None):
        """使用FFT计算频谱"""
        if max_order is None:
            max_order = 5 * self.teeth_count
        
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        num_points = max(1024, 2 * max_order + 10)
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        # FFT计算
        fft_result = np.fft.fft(interp_values)
        
        # 计算振幅 (FFT振幅需要乘以2/N)
        n = len(interp_values)
        spectrum = {}
        
        for order in range(1, max_order + 1):
            # FFT中频率k对应的阶次
            # 频率k表示在360度内有k个完整周期
            if order < n // 2:
                amplitude = 2 * np.abs(fft_result[order]) / n
            else:
                amplitude = 0
            spectrum[order] = amplitude
        
        return spectrum, interp_angles, interp_values
    
    def compute_spectrum_lstsq(self, angles, values, max_order=None):
        """使用最小二乘拟合计算频谱"""
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
    
    def compute_spectrum_windowed(self, angles, values, max_order=None):
        """使用加窗FFT计算频谱"""
        if max_order is None:
            max_order = 5 * self.teeth_count
        
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        num_points = max(1024, 2 * max_order + 10)
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        # 应用汉宁窗
        window = np.hanning(num_points)
        windowed_values = interp_values * window
        
        # FFT计算
        fft_result = np.fft.fft(windowed_values)
        
        # 窗口校正因子
        window_correction = 2.0  # 汉宁窗的振幅校正因子
        
        n = len(interp_values)
        spectrum = {}
        
        for order in range(1, max_order + 1):
            if order < n // 2:
                amplitude = window_correction * np.abs(fft_result[order]) / n
            else:
                amplitude = 0
            spectrum[order] = amplitude
        
        return spectrum, interp_angles, interp_values

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
    print("比较不同频谱计算方法")
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
    
    analyzer = FFTAmplitudeAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"\n齿轮参数: ZE={teeth_count}, m={module}")
    
    # 分析Left Profile
    print("\n" + "=" * 90)
    print("分析 Left Profile - 比较不同频谱计算方法")
    print("=" * 90)
    
    side_data = profile_data.get('left', {})
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    meas_start = gear_data.get('profile_meas_start', 0)
    meas_end = gear_data.get('profile_meas_end', 0)
    
    angles, values = analyzer.build_merged_curve(
        side_data, 'profile', 'left', eval_start, eval_end, meas_start, meas_end
    )
    
    # 计算不同方法的频谱
    spectrum_fft, _, _ = analyzer.compute_spectrum_fft(angles, values)
    spectrum_lstsq, _, _ = analyzer.compute_spectrum_lstsq(angles, values)
    spectrum_windowed, _, _ = analyzer.compute_spectrum_windowed(angles, values)
    
    ref = Klingelnberg_REFERENCE['left_profile']
    
    print(f"\n{'阶次':<8} {'FFT':<12} {'最小二乘':<12} {'加窗FFT':<12} {'Klingelnberg':<12}")
    print("-" * 60)
    
    for order in sorted(ref.keys()):
        fft_amp = spectrum_fft.get(order, 0)
        lstsq_amp = spectrum_lstsq.get(order, 0)
        windowed_amp = spectrum_windowed.get(order, 0)
        ref_amp = ref[order]
        
        print(f"{order:<8.0f} {fft_amp:<12.4f} {lstsq_amp:<12.4f} {windowed_amp:<12.4f} {ref_amp:<12.4f}")
    
    # 计算误差
    fft_error = calculate_error(spectrum_fft, ref)
    lstsq_error = calculate_error(spectrum_lstsq, ref)
    windowed_error = calculate_error(spectrum_windowed, ref)
    
    print(f"\n平均误差:")
    print(f"  FFT: {fft_error:.1f}%")
    print(f"  最小二乘: {lstsq_error:.1f}%")
    print(f"  加窗FFT: {windowed_error:.1f}%")
    
    # 分析振幅比例
    print(f"\n振幅比例分析 (174/87):")
    print(f"  FFT: {spectrum_fft.get(174, 0)/spectrum_fft.get(87, 0) if spectrum_fft.get(87, 0) > 0 else 0:.3f}")
    print(f"  最小二乘: {spectrum_lstsq.get(174, 0)/spectrum_lstsq.get(87, 0) if spectrum_lstsq.get(87, 0) > 0 else 0:.3f}")
    print(f"  加窗FFT: {spectrum_windowed.get(174, 0)/spectrum_windowed.get(87, 0) if spectrum_windowed.get(87, 0) > 0 else 0:.3f}")
    print(f"  Klingelnberg: {ref[174]/ref[87]:.3f}")
    
    # 测试不同预处理阶数
    print("\n" + "=" * 90)
    print("测试不同预处理阶数对振幅比例的影响")
    print("=" * 90)
    
    print(f"\n{'预处理阶数':<12} {'87阶次':<10} {'174阶次':<10} {'174/87比例':<12} {'平均误差':<10}")
    print("-" * 60)
    
    best_order = None
    best_error = float('inf')
    
    for order in [1, 2, 3, 4, 5, 6]:
        angles, values = analyzer.build_merged_curve(
            side_data, 'profile', 'left', eval_start, eval_end, meas_start, meas_end,
            preprocess_order=order
        )
        
        spectrum, _, _ = analyzer.compute_spectrum_lstsq(angles, values)
        
        amp_87 = spectrum.get(87, 0)
        amp_174 = spectrum.get(174, 0)
        ratio = amp_174 / amp_87 if amp_87 > 0 else 0
        
        error = calculate_error(spectrum, ref)
        
        print(f"{order:<12} {amp_87:<10.4f} {amp_174:<10.4f} {ratio:<12.3f} {error:<10.1f}%")
        
        if error < best_error:
            best_error = error
            best_order = order
    
    print(f"\n最佳预处理阶数: {best_order} (平均误差: {best_error:.1f}%)")
    
    # 最终分析所有方向
    print("\n" + "=" * 90)
    print(f"最终分析：使用最佳配置 (预处理阶数={best_order})")
    print("=" * 90)
    
    directions = ['left_profile', 'right_profile', 'left_helix', 'right_helix']
    direction_names = {
        'left_profile': 'Left Profile',
        'right_profile': 'Right Profile',
        'left_helix': 'Left Helix',
        'right_helix': 'Right Helix'
    }
    
    total_errors = []
    
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
        
        angles, values = analyzer.build_merged_curve(
            sd, data_type, side, es, ee, ms, me, preprocess_order=best_order
        )
        
        if angles is None:
            continue
        
        spectrum, _, _ = analyzer.compute_spectrum_lstsq(angles, values)
        ref = Klingelnberg_REFERENCE[direction]
        
        print(f"\n{direction_names[direction]}:")
        print(f"  {'阶次':<8} {'我们的结果':<12} {'Klingelnberg':<12} {'误差':<10} {'状态':<8}")
        print(f"  {'-'*55}")
        
        for order in sorted(ref.keys()):
            our_amp = spectrum.get(order, 0)
            ref_amp = ref[order]
            error = abs(our_amp - ref_amp) / ref_amp * 100 if our_amp > 0 else 100
            total_errors.append(error)
            status = "✅" if error < 10 else "✓" if error < 25 else "⚠" if error < 50 else "✗"
            print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}% {status}")
    
    print("\n" + "=" * 90)
    print("总体统计")
    print("=" * 90)
    print(f"总平均误差: {np.mean(total_errors):.1f}%")
    
    excellent = sum(1 for e in total_errors if e < 10)
    good = sum(1 for e in total_errors if 10 <= e < 25)
    fair = sum(1 for e in total_errors if 25 <= e < 50)
    poor = sum(1 for e in total_errors if e >= 50)
    total = len(total_errors)
    
    print(f"\n误差分布:")
    print(f"  优秀 (<10%):    {excellent}/{total} ({excellent/total*100:.0f}%)")
    print(f"  良好 (10-25%):  {good}/{total} ({good/total*100:.0f}%)")
    print(f"  偏差 (25-50%):  {fair}/{total} ({fair/total*100:.0f}%)")
    print(f"  较大 (>50%):    {poor}/{total} ({poor/total*100:.0f}%)")

if __name__ == "__main__":
    main()
