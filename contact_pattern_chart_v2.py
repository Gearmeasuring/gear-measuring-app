"""
考虑螺距的轮廓测量序列图 V2
按照齿轮测量中心的真实处理逻辑实现：
1. 齿廓相对角度 α（轮廓仪测的，齿内角度）
2. 齿轮绝对旋转角度 θ（节距测量确定的全局角度）
3. 公式：该点的齿轮绝对转角 = 齿起始角 θ + 齿廓相对角度 α
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter


def create_contact_pattern_chart_v2(profile_data=None, pitch_data=None, gear_data=None, 
                                     output_path=None, max_teeth=None):
    """
    创建考虑螺距的轮廓测量序列图（按真实齿轮测量逻辑）
    
    参数:
        profile_data: 齿形测量数据 {'left': {tooth_id: [points]}, 'right': {...}}
        pitch_data: 节距测量数据 {'left': {tooth_id: {'fp': x, 'Fp': y}}, 'right': {...}}
        gear_data: 齿轮基本参数 {'teeth': 齿数, 'module': 模数, ...}
        output_path: 输出文件路径
        max_teeth: 最大显示齿数（None表示显示所有齿）
    
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
    
    # 计算齿距角（每个齿对应的角度）
    tooth_angle = 360.0 / z  # 度
    
    # 创建图形
    if max_teeth and max_teeth < z:
        # 放大视图模式
        fig = plt.figure(figsize=(18, 10))
        fig.subplots_adjust(left=0.06, right=0.94, top=0.90, bottom=0.10, hspace=0.30)
        is_zoomed = True
    else:
        # 全齿视图模式
        fig = plt.figure(figsize=(20, 10))
        fig.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.10, hspace=0.30)
        is_zoomed = False
    
    # ========== 第1行：左齿面 ==========
    ax1 = fig.add_subplot(2, 1, 1)
    left_profile = profile_data.get('left', {}) if profile_data else {}
    left_pitch = pitch_data.get('left', {}) if pitch_data else {}
    plot_unfolded_profile_v2(ax1, left_profile, left_pitch, z, tooth_angle,
                              '左齿面 - 考虑螺距的轮廓测量序列', 
                              gear_data, max_teeth)
    
    # ========== 第2行：右齿面 ==========
    ax2 = fig.add_subplot(2, 1, 2)
    right_profile = profile_data.get('right', {}) if profile_data else {}
    right_pitch = pitch_data.get('right', {}) if pitch_data else {}
    plot_unfolded_profile_v2(ax2, right_profile, right_pitch, z, tooth_angle,
                              '右齿面 - 考虑螺距的轮廓测量序列', 
                              gear_data, max_teeth)
    
    # 添加总标题
    if is_zoomed:
        title = f'考虑螺距的轮廓测量序列 - 前{max_teeth}齿放大视图 (总齿数 z={z})'
    else:
        title = f'考虑螺距的轮廓测量序列 (齿数 z={z}, 模数 m={module})'
    
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    
    # 保存或返回
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"图表已保存到: {output_path}")
    
    return fig


def plot_unfolded_profile_v2(ax, profile_data, pitch_data, z, tooth_angle, title, 
                              gear_data, max_teeth=None):
    """
    绘制展开式轮廓偏差曲线（V2 - 按真实齿轮测量逻辑）
    
    核心算法：
    1. 齿廓相对角度 α：一个齿内从齿顶到齿根的角度（轮廓仪测的）
    2. 齿轮绝对旋转角度 θ：由节距测量确定
    3. 该点的齿轮绝对转角 = 齿起始角 θ + 齿廓相对角度 α
    """
    
    ax.set_facecolor('#fafafa')
    
    if not profile_data or len(profile_data) == 0:
        ax.text(0.5, 0.5, '无数据', ha='center', va='center', 
                transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        return
    
    # 获取所有齿号并排序
    all_tooth_ids = sorted([tid for tid in profile_data.keys() if isinstance(tid, int)])
    
    # 如果只显示部分齿
    if max_teeth:
        tooth_ids = [tid for tid in all_tooth_ids if tid <= max_teeth]
    else:
        tooth_ids = all_tooth_ids
    
    if len(tooth_ids) == 0:
        ax.text(0.5, 0.5, '无有效数据', ha='center', va='center', 
                transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        return
    
    # 准备数据
    all_theta = []  # 齿轮绝对旋转角度
    all_deviation = []  # 偏差值
    tooth_boundaries = []  # 齿边界（角度）
    
    # 颜色方案
    if max_teeth and max_teeth <= 5:
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        use_individual_colors = True
    else:
        use_individual_colors = False
    
    for i, tooth_id in enumerate(tooth_ids):
        if tooth_id not in profile_data:
            continue
            
        values = profile_data[tooth_id]
        if not isinstance(values, (list, np.ndarray)) or len(values) == 0:
            continue
        
        n_points = len(values)
        
        # ========== 核心算法 ==========
        # 1. 计算齿廓相对角度 α
        # 齿廓在齿轮旋转坐标系中的角度范围应该与齿距角相当或更小
        # 对于渐开线齿轮，齿廓对应的展开角度约为：齿距角 × (齿廓弧长 / 齿距)
        # 简化处理：齿廓角度范围 = 齿距角 × 0.8（占据大部分齿距，但留有空隙）
        pressure_angle = gear_data.get('pressure_angle', 20.0) if gear_data else 20.0
        alpha_range = tooth_angle * 0.8  # 齿廓总角度范围（度），约为齿距角的80%
        
        # 生成齿廓相对角度 α（从齿顶到齿根，在齿距范围内分布）
        alpha = np.linspace(0, alpha_range, n_points)
        
        # 2. 计算该齿的起始角 θ（齿轮绝对旋转角度）
        # 基础位置：齿号对应的角度
        base_theta = (tooth_id - 1) * tooth_angle
        
        # 考虑节距误差调整
        pitch_adjustment = 0
        if pitch_data and tooth_id in pitch_data:
            pitch_info = pitch_data[tooth_id]
            if isinstance(pitch_info, dict):
                fp = pitch_info.get('fp', 0)  # 单齿节距误差（μm）
                # 将节距误差转换为角度误差
                # 节距误差 / 基圆直径 * 360°
                module = gear_data.get('module', 2.5) if gear_data else 2.5
                pitch_diameter = module * z
                base_diameter = pitch_diameter * np.cos(np.radians(pressure_angle))
                # 角度误差（度）= fp(μm) / (π * base_diameter(mm)) * 360°
                pitch_adjustment = (fp / 1000) / (np.pi * base_diameter) * 360
        
        # 该齿的起始角（考虑节距误差）
        theta_start = base_theta + pitch_adjustment
        
        # 3. 计算每个点的齿轮绝对旋转角
        # θ_point = θ_start + α
        theta_point = theta_start + alpha
        
        # 记录齿边界
        tooth_boundaries.append(theta_start)
        
        # 绘制该齿的数据
        if use_individual_colors:
            color = colors[i % len(colors)]
            ax.plot(theta_point, values, '-', linewidth=1.0, alpha=0.7, 
                    color=color, label=f'齿 {tooth_id}')
            
            # 绘制平滑曲线
            if len(values) > 21:
                try:
                    window_size = min(21, len(values) // 5 * 2 + 1)
                    if window_size >= 5:
                        y_smooth = savgol_filter(values, window_size, 3)
                        ax.plot(theta_point, y_smooth, '--', linewidth=2.0, 
                                alpha=0.8, color=color)
                except:
                    pass
        else:
            all_theta.extend(theta_point)
            all_deviation.extend(values)
    
    # 如果不是单独颜色模式，统一绘制
    if not use_individual_colors and len(all_theta) > 0:
        all_theta = np.array(all_theta)
        all_deviation = np.array(all_deviation)
        
        # 按角度排序
        sort_idx = np.argsort(all_theta)
        all_theta = all_theta[sort_idx]
        all_deviation = all_deviation[sort_idx]
        
        # 绘制原始数据（红色细线）
        ax.plot(all_theta, all_deviation, 'r-', linewidth=0.6, alpha=0.6, label='轮廓偏差')
        
        # 绘制平滑曲线（蓝色粗线）
        if len(all_deviation) > 51:
            try:
                window_size = min(51, len(all_deviation) // 10 * 2 + 1)
                if window_size >= 5:
                    y_smooth = savgol_filter(all_deviation, window_size, 3)
                    ax.plot(all_theta, y_smooth, 'b-', linewidth=1.8, 
                            alpha=0.8, label='趋势曲线')
            except:
                pass
    
    # 添加齿边界标记
    for boundary in tooth_boundaries:
        ax.axvline(x=boundary, color='gray', linestyle='--', alpha=0.4, linewidth=0.8)
    
    # 添加零线
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    
    # 设置坐标轴
    ax.set_xlabel('齿轮绝对旋转角度 θ (°)', fontsize=11)
    ax.set_ylabel('偏差 (μm)', fontsize=11)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=8)
    
    # 设置X轴范围
    if max_teeth:
        ax.set_xlim(-5, max_teeth * tooth_angle + 5)
    else:
        ax.set_xlim(-5, z * tooth_angle + 5)
    
    # 设置X轴刻度
    if max_teeth and max_teeth <= 10:
        # 放大视图：显示每个齿的刻度
        x_ticks = [i * tooth_angle for i in range(max_teeth + 1)]
        x_labels = [f'{i}\n({i*tooth_angle:.1f}°)' for i in range(max_teeth + 1)]
    else:
        # 全视图：间隔显示
        step = max(1, z // 20)
        x_ticks = [i * tooth_angle for i in range(0, z + 1, step)]
        x_labels = [f'{i}\n({i*tooth_angle:.1f}°)' for i in range(0, z + 1, step)]
    
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels, fontsize=8)
    
    # 设置Y轴范围
    if use_individual_colors:
        # 放大视图模式：计算当前显示数据的范围
        y_vals = []
        for line in ax.lines:
            y_vals.extend(line.get_ydata())
        if y_vals:
            y_max = max(abs(np.min(y_vals)), abs(np.max(y_vals)))
            y_limit = max(y_max * 1.2, 3)
            ax.set_ylim(-y_limit, y_limit)
    else:
        if len(all_deviation) > 0:
            y_max = max(abs(np.min(all_deviation)), abs(np.max(all_deviation)))
            y_limit = max(y_max * 1.1, 5)
            ax.set_ylim(-y_limit, y_limit)
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 添加图例
    if use_individual_colors:
        ax.legend(loc='upper right', fontsize=9, ncol=3)
    else:
        ax.legend(loc='upper right', fontsize=9)
    
    # 添加说明文字
    info_text = f'齿距角: {tooth_angle:.3f}°\n测量齿数: {len(tooth_boundaries)}/{z}'
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=8, 
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))


# 测试函数
if __name__ == '__main__':
    # 创建测试数据
    z = 87  # 齿数
    
    # 模拟齿形数据
    test_profile_left = {}
    test_profile_right = {}
    
    np.random.seed(42)
    
    # 生成前5个齿的数据用于测试
    for tooth_id in range(1, 6):
        # 基础波形（模拟齿廓形状）
        n_points = 480
        t = np.linspace(0, 1, n_points)
        
        # 模拟齿廓偏差（从齿顶到齿根的变化）
        # 使用多项式模拟齿廓曲线
        base_shape = 5 * (4*t**2 - 4*t + 1)  # 抛物线形状
        
        # 添加波纹
        wave = (
            2 * np.sin(2*np.pi*t*3) +  # 3次波纹
            1 * np.sin(2*np.pi*t*8)    # 8次高频波纹
        )
        
        # 添加齿间差异
        tooth_variation = 1.5 * np.sin(tooth_id * 0.5)
        
        # 添加随机噪声
        noise = np.random.normal(0, 0.4, n_points)
        
        test_profile_left[tooth_id] = base_shape + wave + tooth_variation + noise
        
        # 右齿面（略有不同）
        base_shape = 4.5 * (4*t**2 - 4*t + 1)
        wave = (
            1.8 * np.sin(2*np.pi*t*3 + 0.3) +
            0.9 * np.sin(2*np.pi*t*8 + 0.5)
        )
        tooth_variation = 1.3 * np.sin(tooth_id * 0.5 + 0.2)
        noise = np.random.normal(0, 0.35, n_points)
        
        test_profile_right[tooth_id] = base_shape + wave + tooth_variation + noise
    
    # 模拟节距数据
    test_pitch_left = {}
    test_pitch_right = {}
    
    for tooth_id in range(1, 6):
        test_pitch_left[tooth_id] = {
            'fp': np.random.normal(0, 2),   # 单齿节距误差
            'Fp': np.random.normal(0, 5),   # 累积节距误差
            'Fr': np.random.normal(0, 3)
        }
        test_pitch_right[tooth_id] = {
            'fp': np.random.normal(0, 1.8),
            'Fp': np.random.normal(0, 4.5),
            'Fr': np.random.normal(0, 2.8)
        }
    
    test_gear_data = {
        'teeth': z,
        'module': 2.5,
        'pressure_angle': 20.0,  # 压力角20°
        'helix_angle': 0
    }
    
    # 测试1：前3齿放大视图
    print("生成前3齿放大视图...")
    fig1 = create_contact_pattern_chart_v2(
        profile_data={'left': test_profile_left, 'right': test_profile_right},
        pitch_data={'left': test_pitch_left, 'right': test_pitch_right},
        gear_data=test_gear_data,
        output_path='contact_pattern_v2_zoomed_3teeth.png',
        max_teeth=3
    )
    
    # 测试2：全部5齿（如果有数据的话）
    print("生成全部齿视图...")
    fig2 = create_contact_pattern_chart_v2(
        profile_data={'left': test_profile_left, 'right': test_profile_right},
        pitch_data={'left': test_pitch_left, 'right': test_pitch_right},
        gear_data=test_gear_data,
        output_path='contact_pattern_v2_all.png',
        max_teeth=None  # 显示所有齿
    )
    
    plt.show()
    print("图表生成完成！")
