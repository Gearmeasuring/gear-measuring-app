#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从MKA文件中计算齿轮参数：ep, lo, lu, el, zo, zu
"""

import re
import math

def extract_gear_parameters(mka_file_path):
    """从MKA文件中提取齿轮参数"""
    
    with open(mka_file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    lines = content.split('\n')
    params = {}
    
    # 提取基本参数
    patterns = {
        'module': r'^\s*21\s*:.*?:\s*([\d.]+)',  # 法向模数 mn
        'teeth': r'^\s*22\s*:.*?:\s*(-?\d+)',    # 齿数 z
        'helix_angle': r'^\s*23\s*:.*?:\s*(-?[\d.]+)',  # 螺旋角 β
        'pressure_angle': r'^\s*24\s*:.*?:\s*([\d.]+)',  # 压力角 α
        'modification_coeff': r'^\s*25\s*:.*?:\s*([\d.-]+)',  # 变位系数
        'width': r'^\s*26\s*:.*?:\s*([\d.]+)',   # 齿宽
        # 齿形评价范围的直径（左右齿面）
        'd1': r'^\s*42\s*:.*?:\s*([\d.]+)\s+([\d.]+)',  # 起评点直径
        'd2': r'^\s*43\s*:.*?:\s*([\d.]+)\s+([\d.]+)',  # 终评点直径
        'da': r'^\s*41\s*:.*?:\s*([\d.]+)\s+([\d.]+)',  # 起测点直径
        'de': r'^\s*44\s*:.*?:\s*([\d.]+)\s+([\d.]+)',  # 终测点直径
        # 齿向评价范围
        'b1': r'^\s*62\s*:.*?:\s*([\d.]+)\s+([\d.]+)',  # 起评点
        'b2': r'^\s*63\s*:.*?:\s*([\d.]+)\s+([\d.]+)',  # 终评点
        'ba': r'^\s*61\s*:.*?:\s*([\d.-]+)\s+([\d.-]+)',  # 起测点
        'be': r'^\s*64\s*:.*?:\s*([\d.]+)\s+([\d.]+)',  # 终测点
        # Winkelabw值（用于计算lo-lu的差值）
        'winkelabw_profile_left': r'^\s*82\s*:.*?Winkelabw\. links:.*?:\s*([\d.]+)',
        'winkelabw_profile_right': r'^\s*83\s*:.*?Winkelabw\. rechts:.*?:\s*([\d.]+)',
        'winkelabw_flank_left': r'^\s*89\s*:.*?Winkelabw\. links:.*?:\s*([\d.]+)',
        'winkelabw_flank_right': r'^\s*90\s*:.*?Winkelabw\. rechts:.*?:\s*([\d.]+)',
    }
    
    for line in lines:
        for key, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                try:
                    if key in ['d1', 'd2', 'da', 'de', 'b1', 'b2', 'ba', 'be']:
                        # 左右齿面值
                        left_val = float(match.group(1))
                        right_val = float(match.group(2)) if match.group(2) else left_val
                        params[key] = {'left': left_val, 'right': right_val}
                    elif key == 'teeth':
                        params[key] = int(match.group(1))
                    else:
                        params[key] = float(match.group(1))
                except (ValueError, IndexError):
                    continue
    
    return params

def calculate_gear_overlap_params(params):
    """
    计算齿轮重叠系数等参数
    
    返回值:
    - ep: 齿形重叠系数 (profile overlap ratio)
    - lo: 滚长的终评点长度 (roll length at end evaluation point)
    - lu: 滚长的起评点长度 (roll length at start evaluation point)
    - el: 齿向重叠系数 (helix overlap ratio)
    - zo: 齿向评估长度的一半（正值）
    - zu: 齿向评估长度的一半（负值）
    """
    
    # 提取必要参数
    mn = params.get('module', 0.0)           # 法向模数
    z = params.get('teeth', 0)                # 齿数
    alpha_n = params.get('pressure_angle', 0.0)  # 法向压力角（度）
    beta = params.get('helix_angle', 0.0)    # 螺旋角（度）
    
    print(f"\n=== 从MKA文件提取的基本参数 ===")
    print(f"法向模数 mn: {mn} mm")
    print(f"齿数 z: {z}")
    print(f"法向压力角 α_n: {alpha_n}°")
    print(f"螺旋角 β: {beta}°")
    
    # 计算基圆直径 db
    alpha_n_rad = math.radians(alpha_n)
    beta_rad = math.radians(beta)
    
    if beta != 0:
        # 斜齿轮：db = mn * z * cos(α_n) / cos(β)
        db = mn * z * math.cos(alpha_n_rad) / math.cos(beta_rad)
    else:
        # 直齿轮：db = mn * z * cos(α_n)
        db = mn * z * math.cos(alpha_n_rad)
    
    # 计算基圆齿距 pb
    pb = math.pi * db / z
    
    print(f"\n=== 计算的几何参数 ===")
    print(f"基圆直径 db: {db:.6f} mm")
    print(f"基圆半径 rb: {db/2:.6f} mm")
    print(f"基圆齿距 pb: {pb:.6f} mm")
    
    # 计算左右齿面的参数
    results = {}
    
    for side in ['left', 'right']:
        print(f"\n=== {side.upper()} 齿面计算 ===")
        
        # 齿形评价范围
        da = params.get('da', {}).get(side, 0.0)  # 起测点直径
        d1 = params.get('d1', {}).get(side, 0.0)  # 起评点直径
        d2 = params.get('d2', {}).get(side, 0.0)  # 终评点直径
        de = params.get('de', {}).get(side, 0.0)  # 终测点直径
        
        print(f"齿形起测点直径 da: {da:.3f} mm")
        print(f"齿形起评点直径 d1: {d1:.3f} mm")
        print(f"齿形终评点直径 d2: {d2:.3f} mm")
        print(f"齿形终测点直径 de: {de:.3f} mm")
        
        # 齿向评价范围
        ba = params.get('ba', {}).get(side, 0.0)  # 起测点
        b1 = params.get('b1', {}).get(side, 0.0)  # 起评点
        b2 = params.get('b2', {}).get(side, 0.0)  # 终评点
        be = params.get('be', {}).get(side, 0.0)  # 终测点
        
        print(f"齿向起测点 ba: {b1:.3f} mm")
        print(f"齿向起评点 b1: {b1:.3f} mm")
        print(f"齿向终评点 b2: {b2:.3f} mm")
        print(f"齿向终测点 be: {be:.3f} mm")
        
        # 计算展长（滚长）- 使用渐开线展开长度公式
        # 展长 L = sqrt(r^2 - rb^2) - sqrt(r0^2 - rb^2)
        # 其中 r0 是参考半径（使用起测点半径作为参考）
        
        rb = db / 2  # 基圆半径
        
        # 计算各点的展长
        def calculate_spread_length(diameter, ref_diameter, rb):
            """计算展长"""
            r = diameter / 2
            r0 = ref_diameter / 2
            
            # 检查是否在基圆外
            if r <= rb:
                print(f"  警告: 直径 {diameter:.3f} mm 的半径 {r:.3f} mm <= 基圆半径 {rb:.3f} mm")
                return 0.0
            if r0 <= rb:
                print(f"  警告: 参考直径 {ref_diameter:.3f} mm 的半径 {r0:.3f} mm <= 基圆半径 {rb:.3f} mm")
                # 如果参考点在基圆内，使用基圆作为参考
                r0 = rb
            
            spread = math.sqrt(r**2 - rb**2) - math.sqrt(r0**2 - rb**2)
            return spread
        
        # 使用d1作为参考点（起评点）
        spread_da = calculate_spread_length(da, d1, rb)  # 起测点展长
        spread_d1 = 0.0  # 起评点展长为0（参考点）
        spread_d2 = calculate_spread_length(d2, d1, rb)  # 终评点展长
        spread_de = calculate_spread_length(de, d1, rb)  # 终测点展长
        
        print(f"\n展长计算:")
        print(f"起测点展长: {spread_da:.3f} mm")
        print(f"起评点展长 lu: {spread_d1:.3f} mm")
        print(f"终评点展长 lo: {spread_d2:.3f} mm")
        print(f"终测点展长: {spread_de:.3f} mm")
        
        # lu和lo
        lu = spread_d1
        lo = spread_d2
        
        # 齿形评价长度
        La = lo - lu
        
        # 计算齿形重叠系数 ep
        # ep = La / pb
        ep = La / pb if pb > 0 else 0
        
        print(f"\n齿形参数:")
        print(f"lu (起评点展长): {lu:.3f} mm")
        print(f"lo (终评点展长): {lo:.3f} mm")
        print(f"La (评价长度): {La:.3f} mm")
        print(f"ep (齿形重叠系数): {ep:.3f}")
        
        # 齿向参数
        # zo和zu是齿向评价范围的一半
        Lb = b2 - b1  # 齿向评价长度
        zo = Lb / 2
        zu = -zo
        
        # 计算齿向重叠系数 el
        # el = Lb / (pb * tan(β))，但这个公式需要调整
        # 更准确的公式: el = (齿宽 * tan(β)) / (π * mn)
        # 或者使用评价范围: el = Lb / pb (简化公式)
        if abs(beta) > 0.01:
            # 使用标准公式
            el = (Lb * math.tan(abs(beta_rad))) / (math.pi * mn)
        else:
            # 直齿轮
            el = 0.0
        
        print(f"\n齿向参数:")
        print(f"Lb (评价长度): {Lb:.3f} mm")
        print(f"zo (评估长度的一半): {zo:.3f} mm")
        print(f"zu (评估长度的一半): {zu:.3f} mm")
        print(f"el (齿向重叠系数): {el:.3f}")
        
        # 保存结果
        results[side] = {
            'ep': ep,
            'lo': lo,
            'lu': lu,
            'el': el,
            'zo': zo,
            'zu': zu
        }
    
    return results

def main():
    mka_file = r"e:\python\gear measuring software - 20251217\gear measuring software - 20251217\004-xiaoxiao1.mka"
    
    print("=" * 80)
    print("齿轮参数计算程序")
    print("=" * 80)
    print(f"MKA文件: {mka_file}")
    
    # 提取参数
    params = extract_gear_parameters(mka_file)
    
    # 计算重叠系数等参数
    results = calculate_gear_overlap_params(params)
    
    # 打印最终结果
    print("\n" + "=" * 80)
    print("最终计算结果")
    print("=" * 80)
    
    for side in ['left', 'right']:
        print(f"\n{side.upper()} 齿面:")
        print(f"  ep = {results[side]['ep']:.3f}")
        print(f"  lo = {results[side]['lo']:.3f}")
        print(f"  lu = {results[side]['lu']:.3f}")
        print(f"  el = {results[side]['el']:.3f}")
        print(f"  zo = {results[side]['zo']:.3f}")
        print(f"  zu = {results[side]['zu']:.3f}")

if __name__ == "__main__":
    main()
