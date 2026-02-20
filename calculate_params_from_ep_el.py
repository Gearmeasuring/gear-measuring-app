"""
根据Klingelnberg论文公式，通过ep和el计算参数

公式：
- ep = lp / pb  (评价长度与基节的比值)
- el = (Ib × tan(βb)) / pb  (螺旋线相关)
- pb = π × db / ZE  (基节)
- db = d × cos(α)  (基圆直径)
- tan(βb) = tan(β) × cos(α)  (基圆螺旋角)
"""
import os
import sys
import math
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def calculate_params_from_ep_el(mka_file, ep, el):
    """通过ep和el计算参数"""
    print(f"\n{'='*90}")
    print(f"Calculate Parameters from ep={ep}, el={el}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    
    # 从MKA文件获取基本参数
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    face_width = gear_data.get('face_width', 28.0)
    
    print(f"\n基本齿轮参数 (从MKA文件):")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module}")
    print(f"  压力角 α = {pressure_angle}°")
    print(f"  螺旋角 β = {helix_angle}°")
    print(f"  齿宽 Ib = {face_width} mm")
    
    # 计算导出参数
    pitch_diameter = module * teeth_count  # 节圆直径 d = m × ZE
    pitch_radius = pitch_diameter / 2.0
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))  # 基圆直径 db = d × cos(α)
    base_radius = base_diameter / 2.0
    base_pitch = math.pi * base_diameter / teeth_count  # 基节 pb = π × db / ZE
    
    # 基圆螺旋角
    helix_angle_base = math.degrees(math.atan(
        math.tan(math.radians(helix_angle)) * math.cos(math.radians(pressure_angle))
    ))
    
    print(f"\n计算出的参数:")
    print(f"  节圆直径 d = m × ZE = {module} × {teeth_count} = {pitch_diameter:.4f} mm")
    print(f"  基圆直径 db = d × cos(α) = {pitch_diameter:.4f} × cos({pressure_angle}°) = {base_diameter:.4f} mm")
    print(f"  基节 pb = π × db / ZE = π × {base_diameter:.4f} / {teeth_count} = {base_pitch:.4f} mm")
    print(f"  基圆螺旋角 βb = arctan(tan(β) × cos(α)) = arctan(tan({helix_angle}°) × cos({pressure_angle}°)) = {helix_angle_base:.2f}°")
    
    # 通过ep计算评价长度
    lp = ep * base_pitch
    print(f"\n通过 ep 计算评价长度:")
    print(f"  ep = lp / pb")
    print(f"  lp = ep × pb = {ep} × {base_pitch:.4f} = {lp:.4f} mm")
    
    # 通过el计算
    print(f"\n通过 el 计算相关参数:")
    print(f"  el = (Ib × tan(βb)) / pb")
    
    # 验证el
    el_calculated = (face_width * math.tan(math.radians(helix_angle_base))) / base_pitch
    print(f"  计算出的 el = ({face_width} × tan({helix_angle_base:.2f}°)) / {base_pitch:.4f}")
    print(f"             = ({face_width} × {math.tan(math.radians(helix_angle_base)):.4f}) / {base_pitch:.4f}")
    print(f"             = {el_calculated:.4f}")
    
    # 反推齿宽
    Ib_from_el = (el * base_pitch) / math.tan(math.radians(helix_angle_base))
    print(f"\n  通过 el 反推齿宽:")
    print(f"  Ib = (el × pb) / tan(βb)")
    print(f"     = ({el} × {base_pitch:.4f}) / tan({helix_angle_base:.2f}°)")
    print(f"     = ({el} × {base_pitch:.4f}) / {math.tan(math.radians(helix_angle_base)):.4f}")
    print(f"     = {Ib_from_el:.4f} mm")
    
    # PDF中的参数
    print(f"\n{'='*60}")
    print(f"PDF中的参数对比:")
    print(f"{'='*60}")
    print(f"  PDF: lo = 33.578 mm (可能是评价长度)")
    print(f"  PDF: lu = 24.775 mm")
    print(f"  PDF: zo = 18.900")
    print(f"  PDF: zu = -18.900")
    
    print(f"\n  我们计算的评价长度 lp = {lp:.4f} mm")
    print(f"  PDF中的 lo = 33.578 mm")
    print(f"  差异: {abs(lp - 33.578):.4f} mm")
    
    print(f"\n  我们计算的齿宽 Ib = {face_width} mm")
    print(f"  通过el反推的齿宽 = {Ib_from_el:.4f} mm")
    print(f"  差异: {abs(face_width - Ib_from_el):.4f} mm")
    
    # 计算角度合成所需的参数
    print(f"\n{'='*60}")
    print(f"角度合成参数:")
    print(f"{'='*60}")
    
    # 齿形角度范围
    print(f"\n齿形 (Profile):")
    print(f"  评价长度 lp = {lp:.4f} mm")
    print(f"  评价起始半径 = {pitch_radius - lp/2:.4f} mm")
    print(f"  评价结束半径 = {pitch_radius + lp/2:.4f} mm")
    
    # 计算渐开线极角范围
    def involute_angle(r, rb):
        if r <= rb or rb <= 0:
            return 0
        cos_alpha = rb / r
        if cos_alpha >= 1:
            return 0
        alpha = math.acos(cos_alpha)
        return math.degrees(math.tan(alpha) - alpha)
    
    xi_start = involute_angle(pitch_radius - lp/2, base_radius)
    xi_end = involute_angle(pitch_radius + lp/2, base_radius)
    xi_range = abs(xi_end - xi_start)
    
    print(f"  渐开线极角范围: {xi_start:.2f}° 到 {xi_end:.2f}°")
    print(f"  渐开线极角跨度: {xi_range:.2f}°")
    print(f"  每齿角度跨度 = 360° / {teeth_count} = {360/teeth_count:.2f}°")
    
    # 齿向角度范围
    print(f"\n齿向 (Helix):")
    print(f"  齿宽 Ib = {face_width} mm")
    print(f"  基圆螺旋角 βb = {helix_angle_base:.2f}°")
    print(f"  tan(βb) = {math.tan(math.radians(helix_angle_base)):.4f}")
    
    # 轴向旋转角
    delta_phi_total = math.degrees(2 * face_width * math.tan(math.radians(helix_angle_base)) / pitch_diameter)
    print(f"  轴向旋转角 Δφ = 2 × Ib × tan(βb) / d")
    print(f"               = 2 × {face_width} × {math.tan(math.radians(helix_angle_base)):.4f} / {pitch_diameter:.4f}")
    print(f"               = {delta_phi_total:.2f}°")
    print(f"  每齿角度跨度 = 360° / {teeth_count} = {360/teeth_count:.2f}°")
    
    return {
        'teeth_count': teeth_count,
        'module': module,
        'pressure_angle': pressure_angle,
        'helix_angle': helix_angle,
        'pitch_diameter': pitch_diameter,
        'base_diameter': base_diameter,
        'base_pitch': base_pitch,
        'helix_angle_base': helix_angle_base,
        'lp': lp,
        'el': el,
        'xi_range': xi_range,
        'delta_phi_total': delta_phi_total
    }


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    # PDF中的参数
    ep = 1.454
    el = 2.766
    
    params = calculate_params_from_ep_el(sample1_file, ep, el)


if __name__ == "__main__":
    main()
