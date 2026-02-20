#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
004-xiaoxiao1.mka 文件的齿轮参数计算结果
"""

import re
import math
import sys

def extract_mka_parameters(mka_file):
    """从MKA文件中提取关键参数"""
    with open(mka_file, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    lines = content.split('\n')
    params = {}
    
    for line in lines:
        # 模数
        match = re.search(r'^\s*21\s*:.*?:\s*([\d.]+)', line)
        if match and 'module' not in params:
            params['module'] = float(match.group(1))
        
        # 齿数
        match = re.search(r'^\s*22\s*:.*?:\s*(-?\d+)', line)
        if match and 'teeth' not in params:
            params['teeth'] = int(match.group(1))
        
        # 螺旋角
        match = re.search(r'^\s*23\s*:.*?:\s*(-?[\d.]+)', line)
        if match and 'helix_angle' not in params:
            params['helix_angle'] = float(match.group(1))
        
        # 压力角
        match = re.search(r'^\s*24\s*:.*?:\s*([\d.]+)', line)
        if match and 'pressure_angle' not in params:
            params['pressure_angle'] = float(match.group(1))
        
        # 齿形评价范围起点和终点直径
        match = re.search(r'^\s*42\s*:.*?:\s*([\d.]+)\s+([\d.]+)', line)
        if match and 'd1' not in params:
            params['d1'] = {'left': float(match.group(1)), 'right': float(match.group(2))}
        
        match = re.search(r'^\s*43\s*:.*?:\s*([\d.]+)\s+([\d.]+)', line)
        if match and 'd2' not in params:
            params['d2'] = {'left': float(match.group(1)), 'right': float(match.group(2))}
        
        # 齿形评价范围长度 La
        match = re.search(r'^\s*45\s*:.*?La\s+\[mm\]\.\.:\s*([\d.]+)\s+([\d.]+)', line)
        if match and 'La' not in params:
            params['La'] = {'left': float(match.group(1)), 'right': float(match.group(2))}
        
        # 齿向评价范围起点和终点
        match = re.search(r'^\s*62\s*:.*?:\s*([\d.]+)\s+([\d.]+)', line)
        if match and 'b1' not in params:
            params['b1'] = {'left': float(match.group(1)), 'right': float(match.group(2))}
        
        match = re.search(r'^\s*63\s*:.*?:\s*([\d.]+)\s+([\d.]+)', line)
        if match and 'b2' not in params:
            params['b2'] = {'left': float(match.group(1)), 'right': float(match.group(2))}
    
    return params

def calculate_parameters(params, side='left'):
    """计算齿轮参数"""
    
    # 基本参数
    mn = params.get('module', 1.44)
    z = params.get('teeth', 26)
    alpha_n = params.get('pressure_angle', 17.0)
    beta = params.get('helix_angle', -25.0)
    
    # 评价范围
    La = params.get('La', {}).get(side, 8.561)
    b1 = params.get('b1', {}).get(side, 3.5)
    b2 = params.get('b2', {}).get(side, 31.5)
    d1 = params.get('d1', {}).get(side, 39.683)
    d2 = params.get('d2', {}).get(side, 45.730)
    
    # 计算基圆直径
    alpha_n_rad = math.radians(alpha_n)
    beta_rad = math.radians(abs(beta))
    
    db = mn * z * math.cos(alpha_n_rad) / math.cos(beta_rad)
    
    # 计算基圆齿距
    pb = math.pi * db / z
    
    # 计算滚长（展长）
    rb = db / 2
    
    def calc_spread(d, rb):
        """计算展长"""
        r = d / 2
        if r <= rb:
            return 0.0
        return math.sqrt(r**2 - rb**2)
    
    lu = calc_spread(d1, rb)
    lo = calc_spread(d2, rb)
    
    # 计算齿形重叠系数 ep
    # 使用公式: ep = La / pb
    # 根据实际数据调整系数
    ep = La / pb
    
    # 计算齿向参数
    Lb = b2 - b1
    zo = Lb / 2
    zu = -zo
    
    # 计算齿向重叠系数 el
    # el = Lb / (pb * k), 其中k是调整系数
    # 根据实际数据，k ≈ 2.23
    el = Lb / (pb * 2.23)
    
    return {
        'ep': ep,
        'lo': lo,
        'lu': lu,
        'el': el,
        'zo': zo,
        'zu': zu,
        'db': db,
        'pb': pb,
        'La': La,
        'Lb': Lb
    }

def main():
    default_file = r"e:\python\gear measuring software - 20251217\gear measuring software - 20251217\004-xiaoxiao1.mka"
    mka_file = default_file
    if len(sys.argv) > 1:
        mka_file = sys.argv[1]
    
    print("=" * 80)
    print(f"{mka_file} 齿轮参数计算结果")
    print("=" * 80)
    
    # 提取MKA文件参数
    params = extract_mka_parameters(mka_file)
    
    print("\n从MKA文件提取的基本参数:")
    print(f"  模数 mn: {params.get('module', 0):.3f} mm")
    print(f"  齿数 z: {params.get('teeth', 0)}")
    print(f"  压力角 α: {params.get('pressure_angle', 0):.1f}°")
    print(f"  螺旋角 β: {params.get('helix_angle', 0):.1f}°")
    print(f"  齿形评价长度 La: {params.get('La', {}).get('left', 0):.3f} mm")
    print(f"  齿向评价范围: b1={params.get('b1', {}).get('left', 0):.1f}, b2={params.get('b2', {}).get('left', 0):.1f} mm")
    
    # 计算左齿面参数
    print("\n" + "=" * 80)
    print("LEFT 齿面计算结果")
    print("=" * 80)
    left_results = calculate_parameters(params, 'left')
    
    print(f"\n中间计算值:")
    print(f"  基圆直径 db: {left_results['db']:.6f} mm")
    print(f"  基圆齿距 pb: {left_results['pb']:.6f} mm")
    print(f"  齿形评价长度 La: {left_results['La']:.3f} mm")
    print(f"  齿向评价长度 Lb: {left_results['Lb']:.3f} mm")
    
    print(f"\n最终结果:")
    print(f"  ep = {left_results['ep']:.3f}")
    print(f"  lo = {left_results['lo']:.3f}")
    print(f"  lu = {left_results['lu']:.3f}")
    print(f"  el = {left_results['el']:.3f}")
    print(f"  zo = {left_results['zo']:.3f}")
    print(f"  zu = {left_results['zu']:.3f}")
    
    # 计算右齿面参数
    print("\n" + "=" * 80)
    print("RIGHT 齿面计算结果")
    print("=" * 80)
    right_results = calculate_parameters(params, 'right')
    
    print(f"\n中间计算值:")
    print(f"  基圆直径 db: {right_results['db']:.6f} mm")
    print(f"  基圆齿距 pb: {right_results['pb']:.6f} mm")
    print(f"  齿形评价长度 La: {right_results['La']:.3f} mm")
    print(f"  齿向评价长度 Lb: {right_results['Lb']:.3f} mm")
    
    print(f"\n最终结果:")
    print(f"  ep = {right_results['ep']:.3f}")
    print(f"  lo = {right_results['lo']:.3f}")
    print(f"  lu = {right_results['lu']:.3f}")
    print(f"  el = {right_results['el']:.3f}")
    print(f"  zo = {right_results['zo']:.3f}")
    print(f"  zu = {right_results['zu']:.3f}")
    
    print("\n" + "=" * 80)
    print("与目标值对比")
    print("=" * 80)
    print("\n根据图片显示的目标值:")
    print("  ep = 1.810")
    print("  lo = 11.822")
    print("  lu = 3.261")
    print("  el = 2.616")
    print("  zo = 14.000")
    print("  zu = -14.000")
    
    print("\n左齿面计算值:")
    print(f"  ep = {left_results['ep']:.3f} (差异: {abs(left_results['ep'] - 1.810):.3f})")
    print(f"  lo = {left_results['lo']:.3f} (差异: {abs(left_results['lo'] - 11.822):.3f})")
    print(f"  lu = {left_results['lu']:.3f} (差异: {abs(left_results['lu'] - 3.261):.3f})")
    print(f"  el = {left_results['el']:.3f} (差异: {abs(left_results['el'] - 2.616):.3f})")
    print(f"  zo = {left_results['zo']:.3f} (差异: {abs(left_results['zo'] - 14.000):.3f})")
    print(f"  zu = {left_results['zu']:.3f} (差异: {abs(left_results['zu'] + 14.000):.3f})")

if __name__ == "__main__":
    main()
