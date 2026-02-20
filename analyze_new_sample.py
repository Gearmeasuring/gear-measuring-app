"""
分析新的MKA文件 (004-xiaoxiao1.mka)
提取Klingelnberg图表中的参考数据，对比找出规律
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

# 从图表中提取的Klingelnberg参考数据 (004-xiaoxiao1.mka)
# 注意：这个齿轮的齿数不同，需要根据图表中的阶次重新分析
KLINGELNBERG_NEW_SAMPLE = {
    'right_profile': {
        # 齿形右齿面 - 从图表读取
        26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08
    },
    'left_profile': {
        # 齿形左齿面 - 从图表读取
        22: 0.03, 26: 0.24, 44: 0.04, 52: 0.19, 78: 0.09, 104: 0.16, 
        130: 0.09, 156: 0.06, 182: 0.08
    },
    'right_helix': {
        # 齿向右齿面 - 从图表读取
        26: 0.03, 52: 0.06, 78: 0.03, 141: 0.03, 156: 0.02
    },
    'left_helix': {
        # 齿向左齿面 - 从图表读取
        26: 0.07, 48: 0.03, 52: 0.08, 78: 0.04, 104: 0.03, 
        130: 0.02, 141: 0.04, 182: 0.02
    }
}

class NewSampleAnalyzer:
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
    
    def preprocess_tooth_data(self, values, order=3):
        if len(values) < 5:
            return values
        
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        coeffs = np.polyfit(x_norm, values, order)
        trend = np.polyval(coeffs, x_norm)
        
        return values - trend
    
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
            
            if eval_points < 5:
                continue
            
            corrected_values = self.preprocess_tooth_data(eval_values)
            
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

def analyze_sample(mka_file, sample_name, klingelnberg_ref):
    """分析单个样本"""
    print(f"\n{'='*90}")
    print(f"分析样本: {sample_name}")
    print(f"{'='*90}")
    
    print(f"\n解析MKA文件: {mka_file}")
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    print(f"\n齿轮参数:")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module}")
    print(f"  压力角 α = {pressure_angle}°")
    print(f"  螺旋角 β = {helix_angle}°")
    
    analyzer = NewSampleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    # 分析各方向
    directions = [
        ('right_profile', profile_data.get('right', {}), 'profile', 'right'),
        ('left_profile', profile_data.get('left', {}), 'profile', 'left'),
        ('right_helix', flank_data.get('right', {}), 'helix', 'right'),
        ('left_helix', flank_data.get('left', {}), 'helix', 'left'),
    ]
    
    direction_names = {
        'right_profile': 'Right Profile (齿形右齿面)',
        'left_profile': 'Left Profile (齿形左齿面)',
        'right_helix': 'Right Helix (齿向右齿面)',
        'left_helix': 'Left Helix (齿向左齿面)'
    }
    
    total_errors = []
    
    for direction, side_data, data_type, side in directions:
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        # 获取评估参数
        if data_type == 'profile':
            eval_start = gear_data.get('profile_eval_start', 0)
            eval_end = gear_data.get('profile_eval_end', 0)
            meas_start = gear_data.get('profile_meas_start', 0)
            meas_end = gear_data.get('profile_meas_end', 0)
        else:
            eval_start = gear_data.get('helix_eval_start', 0)
            eval_end = gear_data.get('helix_eval_end', 0)
            meas_start = gear_data.get('helix_meas_start', 0)
            meas_end = gear_data.get('helix_meas_end', 0)
        
        angles, values = analyzer.build_merged_curve(
            side_data, data_type, side, eval_start, eval_end, meas_start, meas_end
        )
        
        if angles is None:
            continue
        
        spectrum, _, _ = analyzer.compute_spectrum(angles, values)
        
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
    
    avg_error = np.mean(total_errors) if total_errors else 100
    print(f"\n样本平均误差: {avg_error:.1f}%")
    
    return {
        'teeth_count': teeth_count,
        'avg_error': avg_error,
        'errors': total_errors
    }

def main():
    # 分析两个样本
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    # 第一个样本的参考数据
    KLINGELNBERG_SAMPLE1 = {
        'left_profile': {87: 0.1400, 174: 0.0500, 261: 0.0600, 348: 0.0300, 435: 0.0400},
        'right_profile': {87: 0.1500, 174: 0.0500, 261: 0.0600, 348: 0.0700, 435: 0.0300},
        'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300},
        'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300}
    }
    
    # 分析样本1
    result1 = analyze_sample(sample1_file, "样本1 (263751-018-WAV)", KLINGELNBERG_SAMPLE1)
    
    # 分析样本2
    result2 = analyze_sample(sample2_file, "样本2 (004-xiaoxiao1)", KLINGELNBERG_NEW_SAMPLE)
    
    # 对比分析
    print(f"\n{'='*90}")
    print("两个样本对比分析")
    print(f"{'='*90}")
    
    print(f"\n样本1:")
    print(f"  齿数: {result1['teeth_count']}")
    print(f"  平均误差: {result1['avg_error']:.1f}%")
    
    print(f"\n样本2:")
    print(f"  齿数: {result2['teeth_count']}")
    print(f"  平均误差: {result2['avg_error']:.1f}%")
    
    # 分析规律
    print(f"\n{'='*90}")
    print("规律分析")
    print(f"{'='*90}")
    
    if result1['avg_error'] < 30 and result2['avg_error'] < 30:
        print("\n✅ 算法在两个样本上都表现良好，说明实现正确")
    elif result1['avg_error'] < 30:
        print("\n⚠ 算法在样本1上表现良好，但在样本2上存在偏差")
        print("  可能原因：")
        print("  1. 样本2的数据特性不同")
        print("  2. Klingelnberg图表读取的参考值可能有误差")
        print("  3. 算法需要针对不同齿数进行参数调整")
    else:
        print("\n⚠ 算法在两个样本上都存在偏差")
        print("  可能原因：")
        print("  1. 振幅计算方法需要调整")
        print("  2. 预处理方法需要优化")
        print("  3. 需要获取Klingelnberg的详细算法")

if __name__ == "__main__":
    main()
