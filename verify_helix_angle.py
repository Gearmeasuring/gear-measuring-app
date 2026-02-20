"""
验证齿向角度计算的正确性
对比不同螺旋角下的角度合成
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

def analyze_helix_angle_calculation(mka_file, sample_name):
    """详细分析齿向角度计算"""
    print(f"\n{'='*90}")
    print(f"齿向角度计算验证: {sample_name}")
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
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    pitch_angle = 360.0 / teeth_count
    
    print(f"\n齿轮参数:")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module}")
    print(f"  分度圆直径 D₀ = {pitch_diameter:.4f} mm")
    print(f"  螺旋角 β₀ = {helix_angle}°")
    print(f"  齿距角 τ = {pitch_angle:.4f}°")
    print(f"  评估范围: {eval_start:.2f} ~ {eval_end:.2f} mm")
    print(f"  评估宽度: {eval_end - eval_start:.2f} mm")
    
    # 计算理论轴向角度范围
    eval_width = eval_end - eval_start
    tan_beta0 = math.tan(math.radians(abs(helix_angle)))
    delta_phi_total = math.degrees(eval_width * tan_beta0 / pitch_diameter)
    
    print(f"\n理论计算:")
    print(f"  tan(β₀) = {tan_beta0:.6f}")
    print(f"  单齿Δφ范围 = ±{delta_phi_total/2:.4f}°")
    print(f"  单齿Δφ总范围 = {delta_phi_total:.4f}°")
    
    # 分析实际数据
    right_data = flank_data.get('right', {})
    if right_data:
        sorted_teeth = sorted(right_data.keys())[:3]
        
        print(f"\n实际数据分析 (前3齿):")
        for tooth_id in sorted_teeth:
            tooth_values = right_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            axial_positions = np.linspace(eval_start, eval_end, actual_points)
            eval_center = (eval_start + eval_end) / 2.0
            delta_z = axial_positions - eval_center
            
            # 计算Δφ
            delta_phi = np.degrees(2 * delta_z * tan_beta0 / pitch_diameter)
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * pitch_angle
            
            angles = tau + delta_phi  # 右齿面
            
            print(f"\n  齿 {tooth_id}:")
            print(f"    数据点数: {actual_points}")
            print(f"    τ (齿距角) = {tau:.4f}°")
            print(f"    Δφ 范围: {np.min(delta_phi):.4f}° ~ {np.max(delta_phi):.4f}°")
            print(f"    合成角度范围: {np.min(angles):.4f}° ~ {np.max(angles):.4f}°")
            print(f"    角度跨度: {np.max(angles) - np.min(angles):.4f}°")
    
    # 计算合并曲线的总角度覆盖
    if right_data:
        all_angles = []
        sorted_teeth = sorted(right_data.keys())
        
        for tooth_id in sorted_teeth:
            tooth_values = right_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            axial_positions = np.linspace(eval_start, eval_end, actual_points)
            eval_center = (eval_start + eval_end) / 2.0
            delta_z = axial_positions - eval_center
            delta_phi = np.degrees(2 * delta_z * tan_beta0 / pitch_diameter)
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * pitch_angle
            angles = tau + delta_phi
            
            all_angles.extend(angles.tolist())
        
        if all_angles:
            all_angles = np.array(all_angles)
            print(f"\n合并曲线统计:")
            print(f"  总数据点数: {len(all_angles)}")
            print(f"  总角度范围: {np.min(all_angles):.4f}° ~ {np.max(all_angles):.4f}°")
            print(f"  理论360°周期数: {(np.max(all_angles) - np.min(all_angles)) / 360:.2f}")
            
            # 检查角度覆盖的均匀性
            all_angles_mod = all_angles % 360.0
            hist, bins = np.histogram(all_angles_mod, bins=36)  # 每10°一个bin
            print(f"  角度覆盖均匀性 (每10°bin的数据点数):")
            print(f"    最小: {np.min(hist)}, 最大: {np.max(hist)}, 平均: {np.mean(hist):.1f}")
            print(f"    变异系数: {np.std(hist)/np.mean(hist)*100:.1f}%")

def compare_two_samples():
    """对比两个样本的齿向特性"""
    print(f"\n{'='*90}")
    print("两个样本对比")
    print(f"{'='*90}")
    
    samples = [
        (r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka", "样本1 (ZE=87)"),
        (r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka", "样本2 (ZE=26)")
    ]
    
    print(f"\n{'参数':<25} {'样本1':<20} {'样本2':<20}")
    print(f"{'-'*65}")
    
    for mka_file, sample_name in samples:
        parsed_data = parse_mka_file(mka_file)
        gear_data = parsed_data.get('gear_data', {})
        
        teeth_count = gear_data.get('teeth', 0)
        module = gear_data.get('module', 0)
        helix_angle = gear_data.get('helix_angle', 0)
        eval_start = gear_data.get('helix_eval_start', 0)
        eval_end = gear_data.get('helix_eval_end', 0)
        
        pitch_diameter = module * teeth_count
        eval_width = eval_end - eval_start
        
        if abs(helix_angle) > 0.01:
            tan_beta0 = math.tan(math.radians(abs(helix_angle)))
            delta_phi_total = math.degrees(eval_width * tan_beta0 / pitch_diameter)
        else:
            delta_phi_total = 0
        
        if '样本1' in sample_name:
            print(f"{'齿数 ZE':<25} {teeth_count:<20}")
            print(f"{'模数 m':<25} {module:<20}")
            print(f"{'螺旋角 beta':<25} {helix_angle:<20}")
            print(f"{'分度圆直径 D0':<25} {pitch_diameter:<20.3f}")
            print(f"{'评估宽度':<25} {eval_width:<20.2f}")
            print(f"{'单齿Delta_phi范围':<25} {delta_phi_total:<20.2f}")
        else:
            print(f"{'齿数 ZE':<25} {'':<20} {teeth_count:<20}")
            print(f"{'模数 m':<25} {'':<20} {module:<20}")
            print(f"{'螺旋角 beta':<25} {'':<20} {helix_angle:<20}")
            print(f"{'分度圆直径 D0':<25} {'':<20} {pitch_diameter:<20.3f}")
            print(f"{'评估宽度':<25} {'':<20} {eval_width:<20.2f}")
            print(f"{'单齿Delta_phi范围':<25} {'':<20} {delta_phi_total:<20.2f}")
        print()

if __name__ == "__main__":
    # 对比两个样本
    compare_two_samples()
    
    # 详细分析样本2
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    analyze_helix_angle_calculation(sample2_file, "样本2 (ZE=26, β=-25°)")
    
    # 详细分析样本1
    print(f"\n\n{'='*90}")
    print("样本1分析 (螺旋角接近0°)")
    print(f"{'='*90}")
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    parsed_data = parse_mka_file(sample1_file)
    gear_data = parsed_data.get('gear_data', {})
    helix_angle = gear_data.get('helix_angle', 0)
    print(f"样本1螺旋角: {helix_angle}° (接近0°，所以齿向数据相对简单)")
