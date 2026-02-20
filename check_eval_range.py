"""
查看MKA文件中的齿形评价范围参数，按展长计算
"""

import os
import sys
import math
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def main():
    """主函数"""
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    print(f"读取文件: {mka_file}")
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    print(f"\n{'='*70}")
    print("齿轮基本参数")
    print("="*70)
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module} mm")
    print(f"  压力角 α = {pressure_angle}°")
    print(f"  螺旋角 β = {helix_angle}°")
    
    beta = math.radians(helix_angle)
    alpha_n = math.radians(pressure_angle)
    alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta)) if abs(beta) > 1e-6 else alpha_n
    
    pitch_diameter = teeth_count * module / math.cos(beta)
    base_diameter = pitch_diameter * math.cos(alpha_t)
    base_radius = base_diameter / 2.0
    
    print(f"\n计算参数:")
    print(f"  端面压力角 αt = {math.degrees(alpha_t):.4f}°")
    print(f"  节圆直径 D₀ = {pitch_diameter:.4f} mm")
    print(f"  基圆直径 db = {base_diameter:.4f} mm")
    print(f"  基圆半径 rb = {base_radius:.4f} mm")
    print(f"  节距角 τ = {360.0/teeth_count:.4f}°")
    
    print(f"\n{'='*70}")
    print("齿形评价范围参数（直径）")
    print("="*70)
    
    d1 = gear_data.get('profile_eval_start', 0)
    d2 = gear_data.get('profile_eval_end', 0)
    da = gear_data.get('profile_meas_start', 0)
    de = gear_data.get('profile_meas_end', 0)
    
    print(f"  起评点直径 d1 = {d1} mm")
    print(f"  终评点直径 d2 = {d2} mm")
    print(f"  起测点直径 da = {da} mm")
    print(f"  终测点直径 de = {de} mm")
    
    print(f"\n{'='*70}")
    print("齿形评价范围（展长计算）")
    print("="*70)
    
    def calc_roll_length(diameter, base_diameter):
        """计算展长"""
        radius = diameter / 2.0
        base_radius = base_diameter / 2.0
        if radius <= base_radius:
            return 0.0
        return math.sqrt(radius**2 - base_radius**2)
    
    def calc_roll_angle(diameter, base_diameter):
        """计算展长对应的角度（度）"""
        roll_length = calc_roll_length(diameter, base_diameter)
        base_circumference = math.pi * base_diameter
        if base_circumference <= 0:
            return 0.0
        return (roll_length / base_circumference) * 360.0
    
    s_d1 = calc_roll_length(d1, base_diameter)
    s_d2 = calc_roll_length(d2, base_diameter)
    xi_d1 = calc_roll_angle(d1, base_diameter)
    xi_d2 = calc_roll_angle(d2, base_diameter)
    
    print(f"\n展长计算:")
    print(f"  展长公式: s(d) = sqrt((d/2)² - (db/2)²)")
    print(f"  起评点 d1={d1}mm:")
    print(f"    展长 s(d1) = {s_d1:.4f} mm")
    print(f"    旋转角 ξ(d1) = {xi_d1:.4f}°")
    print(f"  终评点 d2={d2}mm:")
    print(f"    展长 s(d2) = {s_d2:.4f} mm")
    print(f"    旋转角 ξ(d2) = {xi_d2:.4f}°")
    print(f"  展长范围 Δs = {s_d2 - s_d1:.4f} mm")
    print(f"  角度范围 Δξ = {xi_d2 - xi_d1:.4f}°")
    
    print(f"\n{'='*70}")
    print("齿向评价范围参数")
    print("="*70)
    
    b1 = gear_data.get('helix_eval_start', 0)
    b2 = gear_data.get('helix_eval_end', 0)
    ba = gear_data.get('helix_meas_start', 0)
    be = gear_data.get('helix_meas_end', 0)
    
    print(f"  起评点轴向位置 b1 = {b1} mm")
    print(f"  终评点轴向位置 b2 = {b2} mm")
    print(f"  起测点轴向位置 ba = {ba} mm")
    print(f"  终测点轴向位置 be = {be} mm")
    
    z_center = (b1 + b2) / 2.0
    tan_beta = math.tan(math.radians(abs(helix_angle)))
    
    def calc_axial_rotation(z, z_center, pitch_diameter, helix_angle):
        """计算轴向位置产生的旋转角度"""
        delta_z = z - z_center
        tan_beta = math.tan(math.radians(abs(helix_angle)))
        delta_phi_rad = 2.0 * delta_z * tan_beta / pitch_diameter
        return math.degrees(delta_phi_rad)
    
    phi_b1 = calc_axial_rotation(b1, z_center, pitch_diameter, helix_angle)
    phi_b2 = calc_axial_rotation(b2, z_center, pitch_diameter, helix_angle)
    
    print(f"\n轴向旋转角计算:")
    print(f"  公式: Δφ = 2 × Δz × tan(β) / D₀")
    print(f"  评价范围中心 z₀ = {z_center:.4f} mm")
    print(f"  tan(β) = {tan_beta:.4f}")
    print(f"  起评点 b1={b1}mm:")
    print(f"    Δz = {b1 - z_center:.4f} mm")
    print(f"    旋转角 Δφ = {phi_b1:.4f}°")
    print(f"  终评点 b2={b2}mm:")
    print(f"    Δz = {b2 - z_center:.4f} mm")
    print(f"    旋转角 Δφ = {phi_b2:.4f}°")
    print(f"  角度范围 = {abs(phi_b2 - phi_b1):.4f}°")
    
    print(f"\n{'='*70}")
    print("数据统计")
    print("="*70)
    
    left_profile = profile_data.get('left', {})
    right_profile = profile_data.get('right', {})
    left_flank = flank_data.get('left', {})
    right_flank = flank_data.get('right', {})
    
    print(f"\n齿形数据:")
    print(f"  左齿形: {len(left_profile)} 个齿")
    print(f"  右齿形: {len(right_profile)} 个齿")
    
    if left_profile:
        first_tooth = min(left_profile.keys())
        data = left_profile[first_tooth]
        print(f"  左齿形齿{first_tooth}: {len(data)} 个数据点")
    
    print(f"\n齿向数据:")
    print(f"  左齿向: {len(left_flank)} 个齿")
    print(f"  右齿向: {len(right_flank)} 个齿")
    
    if left_flank:
        first_tooth = min(left_flank.keys())
        data = left_flank[first_tooth]
        print(f"  左齿向齿{first_tooth}: {len(data)} 个数据点")
    
    print(f"\n{'='*70}")
    print("ep 和 el 参数计算")
    print("="*70)
    
    pb = math.pi * base_diameter / teeth_count
    print(f"  基圆齿距 pb = π×db/ZE = {pb:.4f} mm")
    
    lu = calc_roll_length(d1, base_diameter)
    lo = calc_roll_length(d2, base_diameter)
    la = lo - lu
    ep = la / pb
    print(f"\n齿形参数 ep:")
    print(f"  lu = s(d1) = {lu:.4f} mm")
    print(f"  lo = s(d2) = {lo:.4f} mm")
    print(f"  la = lo - lu = {la:.4f} mm")
    print(f"  ep = la / pb = {ep:.4f}")
    
    beta_b = math.asin(math.sin(beta) * math.cos(alpha_n))
    lb = b2 - b1
    el = (lb * math.tan(beta_b)) / pb
    print(f"\n齿向参数 el:")
    print(f"  基圆螺旋角 βb = {math.degrees(beta_b):.4f}°")
    print(f"  lb = b2 - b1 = {lb:.4f} mm")
    print(f"  el = lb × tan(βb) / pb = {el:.4f}")
    
    print(f"\n齿形缩放因子 = ep × 4.5 = {ep * 4.5:.4f}")


if __name__ == '__main__':
    main()
