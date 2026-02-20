"""
根据PDF中的实际参数验证计算
PDF参数：
- ep = 1.454
- lo = 33.578
- lu = 24.775
- el = 2.766
- zo = 18.900
- zu = -18.900
"""
import os
import sys
import numpy as np
import math
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def verify_pdf_parameters(mka_file, sample_name):
    """验证PDF参数"""
    print(f"\n{'='*90}")
    print(f"Verify PDF Parameters: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 25.3)
    face_width = gear_data.get('face_width', 28.0)
    
    # 基本参数计算
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_radius = base_diameter / 2.0
    base_pitch = math.pi * base_diameter / teeth_count
    
    # 基圆螺旋角
    helix_angle_base = math.degrees(math.atan(
        math.tan(math.radians(helix_angle)) * math.cos(math.radians(pressure_angle))
    ))
    
    # 评价长度
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    eval_length_profile = profile_eval_end - profile_eval_start if profile_eval_end > profile_eval_start else 0
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    eval_length_helix = helix_eval_end - helix_eval_start if helix_eval_end > helix_eval_start else 0
    
    # 计算ep和el
    ep_calculated = eval_length_profile / base_pitch if base_pitch > 0 else 0
    el_calculated = (face_width * math.tan(math.radians(helix_angle_base))) / base_pitch if base_pitch > 0 else 0
    
    print(f"\nGear Parameters from MKA:")
    print(f"  Teeth ZE = {teeth_count}")
    print(f"  Module m = {module}")
    print(f"  Pressure Angle α = {pressure_angle}°")
    print(f"  Helix Angle β = {helix_angle}°")
    print(f"  Face Width = {face_width} mm")
    print(f"  Profile Eval Length = {eval_length_profile:.3f} mm")
    print(f"  Helix Eval Length = {eval_length_helix:.3f} mm")
    
    print(f"\nCalculated Parameters:")
    print(f"  Pitch Diameter = {pitch_diameter:.3f} mm")
    print(f"  Base Diameter = {base_diameter:.3f} mm")
    print(f"  Base Pitch pb = {base_pitch:.4f} mm")
    print(f"  Base Helix Angle βb = {helix_angle_base:.2f}°")
    print(f"  ep (calculated) = {ep_calculated:.4f}")
    print(f"  el (calculated) = {el_calculated:.4f}")
    
    print(f"\nPDF Parameters:")
    print(f"  ep = 1.454")
    print(f"  lo = 33.578")
    print(f"  lu = 24.775")
    print(f"  el = 2.766")
    print(f"  zo = 18.900")
    print(f"  zu = -18.900")
    
    print(f"\nComparison:")
    print(f"  ep: PDF=1.454, Calculated={ep_calculated:.4f}, Diff={abs(1.454-ep_calculated):.4f}")
    print(f"  el: PDF=2.766, Calculated={el_calculated:.4f}, Diff={abs(2.766-el_calculated):.4f}")
    
    # 反推评价长度
    lo_from_pdf = 1.454 * base_pitch
    print(f"\n  lo from PDF ep: {lo_from_pdf:.3f} mm (PDF: 33.578 mm)")
    
    # 反推齿宽
    Ib_from_pdf = (2.766 * base_pitch) / math.tan(math.radians(helix_angle_base)) if abs(helix_angle_base) > 0.01 else 0
    print(f"  Ib from PDF el: {Ib_from_pdf:.3f} mm (Face Width: {face_width} mm)")


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    verify_pdf_parameters(sample1_file, "Sample1 (ZE=87)")


if __name__ == "__main__":
    main()
