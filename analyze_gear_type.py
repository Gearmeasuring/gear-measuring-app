"""
分析齿轮类型（内齿 vs 外齿）及其对波纹度算法的影响
"""
import os
import sys
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def analyze_gear_type(mka_file, sample_name):
    """分析齿轮类型"""
    print(f"\n{'='*90}")
    print(f"Gear Type Analysis: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    pressure_angle = gear_data.get('pressure_angle', 17.0)
    helix_angle = gear_data.get('helix_angle', -25.0)
    tip_diameter = gear_data.get('tip_diameter', 0)
    root_diameter = gear_data.get('root_diameter', 0)
    
    pitch_diameter = module * teeth_count
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    
    print(f"\nGear Parameters:")
    print(f"  Teeth ZE = {teeth_count}")
    print(f"  Module m = {module}")
    print(f"  Pressure Angle alpha = {pressure_angle}")
    print(f"  Helix Angle beta = {helix_angle}")
    
    print(f"\nDiameter Analysis:")
    print(f"  Pitch Diameter d = m * ZE = {pitch_diameter:.3f} mm")
    print(f"  Base Diameter db = d * cos(alpha) = {base_diameter:.3f} mm")
    print(f"  Tip Diameter da = {tip_diameter:.3f} mm")
    print(f"  Root Diameter df = {root_diameter:.3f} mm")
    
    print(f"\nGear Type Determination:")
    if tip_diameter > pitch_diameter:
        print(f"  da ({tip_diameter:.2f}) > d ({pitch_diameter:.2f})")
        print(f"  -> This is typically an EXTERNAL gear")
    else:
        print(f"  da ({tip_diameter:.2f}) < d ({pitch_diameter:.2f})")
        print(f"  -> This is typically an INTERNAL gear")
    
    print(f"\nKey Differences for Internal Gears:")
    print(f"  1. Involute direction is reversed")
    print(f"  2. Profile angle synthesis formula changes:")
    print(f"     External: phi = -xi + tau (right) or phi = +xi + tau (left)")
    print(f"     Internal: phi = +xi + tau (right) or phi = -xi + tau (left)")
    print(f"  3. Helix angle synthesis may also differ")
    
    return {
        'teeth_count': teeth_count,
        'module': module,
        'pitch_diameter': pitch_diameter,
        'tip_diameter': tip_diameter,
        'is_internal': tip_diameter < pitch_diameter
    }


def compare_internal_external_formulas():
    """对比内齿和外齿的公式差异"""
    print(f"\n{'='*90}")
    print("Formula Comparison: Internal vs External Gears")
    print(f"{'='*90}")
    
    print("""
External Gear (Außenverzahnung):
  Profile Angle Synthesis:
    Right flank: phi = tau + xi    (tooth rotation + involute angle)
    Left flank:  phi = tau - xi    (tooth rotation - involute angle)
  
  Helix Angle Synthesis:
    Right flank: phi = tau + delta_phi
    Left flank:  phi = tau - delta_phi

Internal Gear (Innenverzahnung):
  Profile Angle Synthesis:
    Right flank: phi = tau - xi    (REVERSED from external)
    Left flank:  phi = tau + xi    (REVERSED from external)
  
  Helix Angle Synthesis:
    Right flank: phi = tau - delta_phi  (REVERSED from external)
    Left flank:  phi = tau + delta_phi  (REVERSED from external)

Key Insight:
  For internal gears, the involute and helix angle contributions are 
  SUBTRACTED where they would be ADDED for external gears, and vice versa.
""")


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    info1 = analyze_gear_type(sample1_file, "Sample1 (263751-018-WAV)")
    info2 = analyze_gear_type(sample2_file, "Sample2 (004-xiaoxiao1)")
    
    compare_internal_external_formulas()
    
    print(f"\n{'='*90}")
    print("SUMMARY")
    print(f"{'='*90}")
    
    print(f"\nSample1: {'INTERNAL' if info1['is_internal'] else 'EXTERNAL'} gear")
    print(f"Sample2: {'INTERNAL' if info2['is_internal'] else 'EXTERNAL'} gear")
    
    print(f"""
If Sample2 is actually an internal gear (despite file annotation),
the angle synthesis formulas need to be reversed for proper analysis.
This could explain the large errors we observed in the helix data.
""")


if __name__ == "__main__":
    main()
