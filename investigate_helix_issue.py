"""
深入分析齿向数据的问题
对比齿形和齿向的预处理效果
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

class HelixAnalyzer:
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
    
    def preprocess_tooth_data(self, values, order=3):
        if len(values) < 5:
            return values
        
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        coeffs = np.polyfit(x_norm, values, order)
        trend = np.polyval(coeffs, x_norm)
        
        return values - trend
    
    def analyze_helix_tooth(self, tooth_values, eval_start, eval_end, side, tooth_id):
        """详细分析单个齿的齿向数据"""
        if tooth_values is None or len(tooth_values) == 0:
            return None
        
        actual_points = len(tooth_values)
        eval_values = np.array(tooth_values, dtype=float)
        
        # 原始数据统计
        raw_mean = np.mean(eval_values)
        raw_std = np.std(eval_values)
        raw_range = np.max(eval_values) - np.min(eval_values)
        
        # 预处理后数据统计
        corrected_values = self.preprocess_tooth_data(eval_values)
        corr_mean = np.mean(corrected_values)
        corr_std = np.std(corrected_values)
        corr_range = np.max(corrected_values) - np.min(corrected_values)
        
        # 计算轴向角度
        axial_positions = np.linspace(eval_start, eval_end, actual_points)
        eval_center = (eval_start + eval_end) / 2.0
        delta_z = axial_positions - eval_center
        
        if abs(self.helix_angle) > 0.01 and self.pitch_diameter > 0:
            tan_beta0 = math.tan(math.radians(self.helix_angle))
            delta_phi = np.degrees(2 * delta_z * tan_beta0 / self.pitch_diameter)
        else:
            delta_phi = np.linspace(0, 1, actual_points)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * self.pitch_angle
        
        if side == 'left':
            angles = tau - delta_phi
        else:
            angles = tau + delta_phi
        
        # 计算该齿的频谱
        spectrum = self.compute_single_tooth_spectrum(angles, corrected_values)
        
        return {
            'tooth_id': tooth_id,
            'raw_stats': {'mean': raw_mean, 'std': raw_std, 'range': raw_range},
            'corr_stats': {'mean': corr_mean, 'std': corr_std, 'range': corr_range},
            'angles': angles,
            'values': corrected_values,
            'spectrum': spectrum,
            'delta_phi_range': (np.min(delta_phi), np.max(delta_phi))
        }
    
    def compute_single_tooth_spectrum(self, angles, values, max_order=200):
        """计算单个齿的频谱"""
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
        
        return spectrum
    
    def build_merged_curve(self, side_data, side, eval_start, eval_end):
        """构建合并曲线"""
        if not side_data:
            return None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            eval_values = np.array(tooth_values, dtype=float)
            corrected_values = self.preprocess_tooth_data(eval_values)
            
            actual_points = len(corrected_values)
            
            # 计算轴向角度
            axial_positions = np.linspace(eval_start, eval_end, actual_points)
            eval_center = (eval_start + eval_end) / 2.0
            delta_z = axial_positions - eval_center
            
            if abs(self.helix_angle) > 0.01 and self.pitch_diameter > 0:
                tan_beta0 = math.tan(math.radians(self.helix_angle))
                delta_phi = np.degrees(2 * delta_z * tan_beta0 / self.pitch_diameter)
            else:
                delta_phi = np.linspace(0, 1, actual_points)
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * self.pitch_angle
            
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
        
        return all_angles[sort_idx], all_values[sort_idx]

def analyze_helix_detailed(mka_file, sample_name):
    """详细分析齿向数据"""
    print(f"\n{'='*90}")
    print(f"详细齿向分析: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    pressure_angle = gear_data.get('pressure_angle', 17.0)
    helix_angle = gear_data.get('helix_angle', -25.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    eval_start = gear_data.get('helix_eval_start', 0)
    eval_end = gear_data.get('helix_eval_end', 0)
    
    print(f"\n齿轮参数:")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module}")
    print(f"  压力角 α = {pressure_angle}°")
    print(f"  螺旋角 β = {helix_angle}°")
    print(f"  评估范围: {eval_start:.2f} ~ {eval_end:.2f} mm")
    
    analyzer = HelixAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    # 分析右齿向
    right_data = flank_data.get('right', {})
    if right_data:
        print(f"\n{'='*60}")
        print("右齿向详细分析")
        print(f"{'='*60}")
        
        # 分析前3个齿
        sorted_teeth = sorted(right_data.keys())[:3]
        
        for tooth_id in sorted_teeth:
            tooth_values = right_data[tooth_id]
            result = analyzer.analyze_helix_tooth(tooth_values, eval_start, eval_end, 'right', tooth_id)
            
            if result:
                print(f"\n齿 {tooth_id}:")
                print(f"  原始数据: mean={result['raw_stats']['mean']:.4f}, std={result['raw_stats']['std']:.4f}, range={result['raw_stats']['range']:.4f}")
                print(f"  预处理后: mean={result['corr_stats']['mean']:.4f}, std={result['corr_stats']['std']:.4f}, range={result['corr_stats']['range']:.4f}")
                print(f"  Δφ 范围: {result['delta_phi_range'][0]:.4f}° ~ {result['delta_phi_range'][1]:.4f}°")
                
                # 显示主要频谱成分
                spectrum = result['spectrum']
                top_orders = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)[:5]
                print(f"  主要频谱成分:")
                for order, amp in top_orders:
                    print(f"    阶次 {order}: {amp:.4f}")
        
        # 合并曲线分析
        print(f"\n{'='*60}")
        print("合并曲线频谱分析")
        print(f"{'='*60}")
        
        angles, values = analyzer.build_merged_curve(right_data, 'right', eval_start, eval_end)
        if angles is not None:
            spectrum = analyzer.compute_single_tooth_spectrum(angles, values, max_order=200)
            
            # 显示ZE的倍数阶次
            print(f"\n右齿向 - ZE={teeth_count} 倍数阶次:")
            for mult in range(1, 8):
                order = mult * teeth_count
                amp = spectrum.get(order, 0)
                print(f"  阶次 {order} ({mult}×ZE): {amp:.4f}")
            
            # 显示所有主要成分
            print(f"\n右齿向 - 所有主要频谱成分 (前10):")
            top_orders = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)[:10]
            for order, amp in top_orders:
                print(f"  阶次 {order}: {amp:.4f}")
    
    # 分析左齿向
    left_data = flank_data.get('left', {})
    if left_data:
        print(f"\n{'='*60}")
        print("左齿向详细分析")
        print(f"{'='*60}")
        
        angles, values = analyzer.build_merged_curve(left_data, 'left', eval_start, eval_end)
        if angles is not None:
            spectrum = analyzer.compute_single_tooth_spectrum(angles, values, max_order=200)
            
            print(f"\n左齿向 - ZE={teeth_count} 倍数阶次:")
            for mult in range(1, 8):
                order = mult * teeth_count
                amp = spectrum.get(order, 0)
                print(f"  阶次 {order} ({mult}×ZE): {amp:.4f}")
            
            print(f"\n左齿向 - 所有主要频谱成分 (前10):")
            top_orders = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)[:10]
            for order, amp in top_orders:
                print(f"  阶次 {order}: {amp:.4f}")

def main():
    # 分析样本2 (齿数=26)
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    analyze_helix_detailed(sample2_file, "样本2 (ZE=26)")
    
    # 对比分析样本1 (齿数=87)
    print(f"\n\n{'='*90}")
    print("对比分析样本1 (齿数=87)")
    print(f"{'='*90}")
    
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    parsed_data = parse_mka_file(sample1_file)
    gear_data = parsed_data.get('gear_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    eval_start = gear_data.get('helix_eval_start', 0)
    eval_end = gear_data.get('helix_eval_end', 0)
    
    analyzer = HelixAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    right_data = flank_data.get('right', {})
    if right_data:
        angles, values = analyzer.build_merged_curve(right_data, 'right', eval_start, eval_end)
        if angles is not None:
            spectrum = analyzer.compute_single_tooth_spectrum(angles, values, max_order=500)
            
            print(f"\n样本1 右齿向 - ZE={teeth_count} 倍数阶次:")
            for mult in range(1, 6):
                order = mult * teeth_count
                amp = spectrum.get(order, 0)
                print(f"  阶次 {order} ({mult}×ZE): {amp:.4f}")

if __name__ == "__main__":
    main()
