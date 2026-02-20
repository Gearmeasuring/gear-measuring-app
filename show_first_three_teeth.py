"""
显示左齿形前三个齿的合并曲线
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def remove_slope_and_crowning(data):
    """去除斜率和鼓形"""
    if len(data) < 3:
        return data
    data = np.array(data, dtype=float)
    x = np.arange(len(data), dtype=float)
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    # 去除鼓形
    crowning_coeffs = np.polyfit(x_norm, data, 2)
    crowning_curve = np.polyval(crowning_coeffs, x_norm)
    data_after_crowning = data - crowning_curve
    
    # 去除斜率
    slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
    slope_curve = np.polyval(slope_coeffs, x_norm)
    corrected_data = data_after_crowning - slope_curve
    
    return corrected_data


def calculate_involute_polar_angle(radius, base_radius):
    """计算渐开线极角"""
    if radius <= base_radius or base_radius <= 0:
        return 0.0
    cos_alpha = base_radius / radius
    if cos_alpha >= 1.0:
        return 0.0
    alpha = np.arccos(cos_alpha)
    return np.tan(alpha) - alpha


def process_first_three_teeth(profile_data, gear_data):
    """处理前三个齿的数据"""
    if 'left' not in profile_data or not profile_data['left']:
        return None
    
    module = gear_data.get('module', gear_data.get('模数', 0))
    teeth_count = gear_data.get('teeth', gear_data.get('齿数', 0))
    pressure_angle = gear_data.get('pressure_angle', gear_data.get('压力角', 20))
    
    pitch_radius = module * teeth_count / 2.0
    base_radius = pitch_radius * np.cos(np.radians(pressure_angle))
    pitch_angle_deg = 360.0 / teeth_count
    
    side_data = profile_data['left']
    sorted_teeth = sorted(side_data.keys())[:3]  # 只取前三个齿
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'左齿形 - 前三个齿的合并曲线 (z={teeth_count})', fontsize=14, fontweight='bold')
    
    colors = ['blue', 'green', 'red']
    
    for idx, tooth_id in enumerate(sorted_teeth):
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        tooth_values = np.array(tooth_values)
        corrected_values = remove_slope_and_crowning(tooth_values)
        
        # 计算极角（简化：使用线性分布）
        actual_points = len(tooth_values)
        polar_angles_deg = np.linspace(0, 1.1, actual_points)
        
        # 计算 tooth_index
        tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else idx
        
        # 计算最终角度
        tooth_base_angle = tooth_index * pitch_angle_deg
        final_angles = tooth_base_angle - polar_angles_deg  # 左齿形用减号
        
        # 归一化到0-360
        final_angles = final_angles % 360.0
        final_angles[final_angles < 0] += 360.0
        
        # 按角度排序
        sort_idx = np.argsort(final_angles)
        final_angles = final_angles[sort_idx]
        corrected_values = corrected_values[sort_idx]
        
        # 绘制
        color = colors[idx % len(colors)]
        
        # 子图1: 原始数据点
        ax1 = axes[0, 0]
        ax1.scatter(final_angles, corrected_values, c=color, s=1, alpha=0.5, label=f'齿{tooth_id}')
        
        # 子图2: 连线
        ax2 = axes[0, 1]
        ax2.plot(final_angles, corrected_values, color=color, alpha=0.7, linewidth=0.8, label=f'齿{tooth_id}')
        
        # 子图3: 角度位置示意
        ax3 = axes[1, 0]
        ax3.axvline(x=tooth_base_angle, color=color, linestyle='--', alpha=0.7, label=f'齿{tooth_id}基角={tooth_base_angle:.1f}°')
        
        # 子图4: 极角范围
        ax4 = axes[1, 1]
        ax4.plot(range(actual_points), polar_angles_deg, color=color, alpha=0.7, label=f'齿{tooth_id}极角')
    
    # 设置子图1
    axes[0, 0].set_xlabel('旋转角度 (°)')
    axes[0, 0].set_ylabel('偏差 (μm)')
    axes[0, 0].set_title('前三个齿的数据点分布')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 设置子图2
    axes[0, 1].set_xlabel('旋转角度 (°)')
    axes[0, 1].set_ylabel('偏差 (μm)')
    axes[0, 1].set_title('前三个齿的曲线')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 设置子图3
    axes[1, 0].set_xlabel('角度 (°)')
    axes[1, 0].set_ylabel('')
    axes[1, 0].set_title('各齿的节距角位置')
    axes[1, 0].set_xlim(0, 360)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 设置子图4
    axes[1, 1].set_xlabel('测量点索引')
    axes[1, 1].set_ylabel('极角 (°)')
    axes[1, 1].set_title('各齿的极角变化')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = os.path.join(current_dir, 'first_three_teeth_left_profile.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f'Saved: {output_file}')
    plt.close()
    
    return sorted_teeth


def main():
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print(f'读取文件: {mka_file}')
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
    teeth_count = gear_data.get('teeth', gear_data.get('齿数', 0))
    module = gear_data.get('module', gear_data.get('模数', 0))
    
    print(f'\n齿轮参数:')
    print(f'  齿数: {teeth_count}')
    print(f'  模数: {module} mm')
    print(f'  节距角: {360.0/teeth_count:.2f}°')
    
    print(f'\n左齿形数据: {len(profile_data.get("left", {}))}个齿')
    
    first_three = process_first_three_teeth(profile_data, gear_data)
    
    if first_three:
        print(f'\n前三个齿: {first_three}')
        print(f'  齿1基角: {(int(first_three[0])-1) * 360.0/teeth_count:.2f}°')
        print(f'  齿2基角: {(int(first_three[1])-1) * 360.0/teeth_count:.2f}°')
        print(f'  齿3基角: {(int(first_three[2])-1) * 360.0/teeth_count:.2f}°')


if __name__ == '__main__':
    main()
