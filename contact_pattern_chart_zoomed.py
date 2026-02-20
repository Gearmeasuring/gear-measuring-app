"""
考虑螺距的轮廓测量序列图 - 前3齿放大视图
展示空载啮合时齿侧沿齿根平行直线的接触情况（局部放大）
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter


def create_zoomed_contact_pattern_chart(profile_data=None, pitch_data=None, gear_data=None, 
                                        output_path=None, max_teeth=3):
    """
    创建考虑螺距的轮廓测量序列图（前N齿放大视图）
    
    参数:
        profile_data: 齿形测量数据 {'left': {tooth_id: [480个点]}, 'right': {...}}
        pitch_data: 节距测量数据 {'left': {tooth_id: {'fp': x, 'Fp': y, 'Fr': z}}, 'right': {...}}
        gear_data: 齿轮基本参数 {'teeth': 齿数, 'module': 模数, ...}
        output_path: 输出文件路径
        max_teeth: 显示的最大齿数（默认前3齿）
    
    返回:
        fig: matplotlib图形对象
    """
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 获取齿轮参数
    z = gear_data.get('teeth', 0) if gear_data else 0
    if z <= 0:
        z = 87  # 默认87齿
    
    module = gear_data.get('module', 2.5) if gear_data else 2.5
    
    # 创建图形 - 2行布局，更宽的比例以便放大显示
    fig = plt.figure(figsize=(18, 10))
    fig.subplots_adjust(left=0.06, right=0.94, top=0.90, bottom=0.10, hspace=0.30)
    
    # ========== 第1行：左齿面展开轮廓曲线（放大视图） ==========
    ax1 = fig.add_subplot(2, 1, 1)
    left_profile = profile_data.get('left', {}) if profile_data else {}
    left_pitch = pitch_data.get('left', {}) if pitch_data else {}
    plot_zoomed_unfolded_profile(ax1, left_profile, left_pitch, z, 
                                  f'左齿面 - 前{max_teeth}齿放大视图', 
                                  gear_data, max_teeth=max_teeth)
    
    # ========== 第2行：右齿面展开轮廓曲线（放大视图） ==========
    ax2 = fig.add_subplot(2, 1, 2)
    right_profile = profile_data.get('right', {}) if profile_data else {}
    right_pitch = pitch_data.get('right', {}) if pitch_data else {}
    plot_zoomed_unfolded_profile(ax2, right_profile, right_pitch, z, 
                                  f'右齿面 - 前{max_teeth}齿放大视图', 
                                  gear_data, max_teeth=max_teeth)
    
    # 添加总标题
    fig.suptitle(f'考虑螺距的轮廓测量序列 - 前{max_teeth}齿放大视图 (总齿数 z={z}, 模数 m={module})', 
                 fontsize=14, fontweight='bold', y=0.98)
    
    # 保存或返回
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"图表已保存到: {output_path}")
    
    return fig


def plot_zoomed_unfolded_profile(ax, profile_data, pitch_data, z, title, gear_data, max_teeth=3):
    """
    绘制展开式轮廓偏差曲线的放大视图（只显示前N个齿）
    
    参数:
        ax: matplotlib轴对象
        profile_data: 齿形测量数据
        pitch_data: 节距测量数据
        z: 总齿数
        title: 图表标题
        gear_data: 齿轮基本参数
        max_teeth: 显示的最大齿数
    """
    
    ax.set_facecolor('#fafafa')
    
    if not profile_data or len(profile_data) == 0:
        ax.text(0.5, 0.5, '无数据', ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        return
    
    # 获取所有齿号并排序，只取前max_teeth个齿
    all_tooth_ids = sorted([tid for tid in profile_data.keys() if isinstance(tid, int)])
    tooth_ids = [tid for tid in all_tooth_ids if tid <= max_teeth]
    
    if len(tooth_ids) == 0:
        ax.text(0.5, 0.5, '无有效数据', ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        return
    
    # 准备数据
    all_x = []  # 展开后的X坐标（齿号 + 点位置）
    all_y = []  # 偏差值
    tooth_boundaries = []  # 齿边界位置
    tooth_centers = []  # 齿中心位置（用于标注）
    
    points_per_tooth = 480  # 每个齿的测量点数
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # 不同齿使用不同颜色
    
    for i, tooth_id in enumerate(tooth_ids):
        if tooth_id not in profile_data:
            continue
            
        values = profile_data[tooth_id]
        if not isinstance(values, (list, np.ndarray)) or len(values) == 0:
            continue
        
        # 获取节距误差调整
        pitch_adjustment = 0
        if pitch_data and tooth_id in pitch_data:
            pitch_info = pitch_data[tooth_id]
            if isinstance(pitch_info, dict):
                pitch_adjustment = pitch_info.get('fp', 0) / 1000.0
        
        # 计算该齿的X坐标范围
        base_position = tooth_id - 1
        adjusted_position = base_position + pitch_adjustment / 10.0
        
        # 生成该齿的X坐标
        n_points = min(len(values), points_per_tooth)
        x_local = np.linspace(0, 1, n_points)
        x_global = adjusted_position + x_local
        
        y_values = values[:n_points]
        
        # 绘制该齿的数据（使用不同颜色）
        color = colors[i % len(colors)]
        ax.plot(x_global, y_values, '-', linewidth=1.2, alpha=0.8, 
                color=color, label=f'齿 {tooth_id}')
        
        # 计算平滑曲线
        if len(y_values) > 21:
            try:
                window_size = min(21, len(y_values) // 5 * 2 + 1)
                if window_size >= 5:
                    y_smooth = savgol_filter(y_values, window_size, 3)
                    ax.plot(x_global, y_smooth, '-', linewidth=2.5, alpha=0.9, 
                            color=color, linestyle='--')
            except:
                pass
        
        all_x.extend(x_global)
        all_y.extend(y_values)
        tooth_boundaries.append(adjusted_position)
        tooth_centers.append(adjusted_position + 0.5)
    
    if len(all_x) == 0:
        ax.text(0.5, 0.5, '无有效数据', ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        return
    
    # 添加齿边界标记
    for boundary in tooth_boundaries:
        ax.axvline(x=boundary, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    # 添加零线
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    
    # 设置坐标轴
    ax.set_xlabel('齿号 / 旋转角度', fontsize=11)
    ax.set_ylabel('偏差 (μm)', fontsize=11)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=8)
    
    # 设置X轴范围（只显示前max_teeth个齿的范围）
    ax.set_xlim(-0.1, max_teeth + 0.1)
    
    # 设置X轴刻度
    x_ticks = list(range(0, max_teeth + 1))
    ax.set_xticks(x_ticks)
    
    # 创建双X轴标签
    x_labels = []
    for t in x_ticks:
        angle = t * 360 / z
        x_labels.append(f'{t}\n({angle:.1f}°)')
    ax.set_xticklabels(x_labels, fontsize=9)
    
    # 设置Y轴范围（对称）
    all_y = np.array(all_y)
    y_max = max(abs(np.min(all_y)), abs(np.max(all_y))) if len(all_y) > 0 else 10
    y_limit = max(y_max * 1.2, 3)
    ax.set_ylim(-y_limit, y_limit)
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 添加图例
    ax.legend(loc='upper right', fontsize=10, ncol=3)
    
    # 在每个齿的中心添加齿号标注
    for i, (center, tooth_id) in enumerate(zip(tooth_centers, tooth_ids)):
        if center <= max_teeth:
            ax.annotate(f'齿{tooth_id}', xy=(center, ax.get_ylim()[1]), 
                       xytext=(center, ax.get_ylim()[1] * 0.9),
                       ha='center', fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))


# 测试函数
if __name__ == '__main__':
    # 创建测试数据
    z = 87  # 齿数（87齿齿轮）
    
    # 模拟齿形数据（480个点 per tooth）
    test_profile_left = {}
    test_profile_right = {}
    
    np.random.seed(42)
    
    # 生成模拟的展开曲线数据（只生成前5个齿的数据用于测试）
    for tooth_id in range(1, 6):  # 只生成前5个齿
        # 基础波形
        t = np.linspace(0, 2*np.pi, 480)
        
        # 左齿面
        base_wave = (
            3 * np.sin(t + tooth_id * 0.3) +
            1.5 * np.sin(3*t + tooth_id * 0.2) +
            0.5 * np.sin(8*t)
        )
        trend = 1.5 * np.sin(tooth_id * np.pi / 5)
        noise = np.random.normal(0, 0.3, 480)
        
        test_profile_left[tooth_id] = base_wave + trend + noise
        
        # 右齿面
        base_wave = (
            2.5 * np.sin(t + tooth_id * 0.25 + 0.5) +
            1.2 * np.sin(3*t + tooth_id * 0.15) +
            0.4 * np.sin(8*t + 1)
        )
        trend = 1.3 * np.sin(tooth_id * np.pi / 5 + 0.3)
        noise = np.random.normal(0, 0.25, 480)
        
        test_profile_right[tooth_id] = base_wave + trend + noise
    
    # 模拟节距数据
    test_pitch_left = {}
    test_pitch_right = {}
    
    for tooth_id in range(1, 6):
        test_pitch_left[tooth_id] = {
            'fp': np.random.normal(0, 1.5),
            'Fp': np.random.normal(0, 4),
            'Fr': np.random.normal(0, 2.5)
        }
        test_pitch_right[tooth_id] = {
            'fp': np.random.normal(0, 1.3),
            'Fp': np.random.normal(0, 3.5),
            'Fr': np.random.normal(0, 2.2)
        }
    
    test_gear_data = {
        'teeth': z,
        'module': 2.5,
        'helix_angle': 0
    }
    
    # 创建放大视图图表（前3齿）
    fig = create_zoomed_contact_pattern_chart(
        profile_data={'left': test_profile_left, 'right': test_profile_right},
        pitch_data={'left': test_pitch_left, 'right': test_pitch_right},
        gear_data=test_gear_data,
        output_path='contact_pattern_zoomed_3teeth.png',
        max_teeth=3
    )
    
    plt.show()
    print("前3齿放大视图已生成！")
