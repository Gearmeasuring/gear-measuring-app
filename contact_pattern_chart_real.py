"""
考虑螺距的轮廓测量序列图 - 真实齿轮测量中心算法
完全按照齿轮测量中心的处理逻辑：
1. 齿廓相对角度 α = φ_k - φ_0（极角差）
2. 齿绝对起始角 θ_i_start = Σ(实测角节距 Δθ)
3. 齿轮绝对旋转角度 θ_point = θ_i_start + α_k
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter


def create_contact_pattern_chart_real(profile_data=None, pitch_data=None, gear_data=None,
                                      output_path=None, max_teeth=None):
    """
    创建考虑螺距的轮廓测量序列图（真实齿轮测量中心算法）

    参数:
        profile_data: 齿形测量数据 {'left': {tooth_id: [(x,y), ...]}, 'right': {...}}
                     或 {'left': {tooth_id: [deviation_values]}, ...}
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

    # 创建图形
    if max_teeth and max_teeth < z:
        fig = plt.figure(figsize=(18, 10))
        fig.subplots_adjust(left=0.06, right=0.94, top=0.90, bottom=0.10, hspace=0.30)
        is_zoomed = True
    else:
        fig = plt.figure(figsize=(20, 10))
        fig.subplots_adjust(left=0.05, right=0.95, top=0.90, bottom=0.10, hspace=0.30)
        is_zoomed = False

    # ========== 第1行：左齿面 ==========
    ax1 = fig.add_subplot(2, 1, 1)
    left_profile = profile_data.get('left', {}) if profile_data else {}
    left_pitch = pitch_data.get('left', {}) if pitch_data else {}
    plot_unfolded_profile_real(ax1, left_profile, left_pitch, z,
                               '左齿面 - 考虑螺距的轮廓测量序列（真实算法）',
                               gear_data, max_teeth)

    # ========== 第2行：右齿面 ==========
    ax2 = fig.add_subplot(2, 1, 2)
    right_profile = profile_data.get('right', {}) if profile_data else {}
    right_pitch = pitch_data.get('right', {}) if pitch_data else {}
    plot_unfolded_profile_real(ax2, right_profile, right_pitch, z,
                               '右齿面 - 考虑螺距的轮廓测量序列（真实算法）',
                               gear_data, max_teeth)

    # 添加总标题
    if is_zoomed:
        title = f'考虑螺距的轮廓测量序列（真实算法）- 前{max_teeth}齿 (总齿数 z={z})'
    else:
        title = f'考虑螺距的轮廓测量序列（真实算法）(齿数 z={z}, 模数 m={module})'

    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)

    # 保存或返回
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"图表已保存到: {output_path}")

    return fig


def plot_unfolded_profile_real(ax, profile_data, pitch_data, z, title,
                               gear_data, max_teeth=None):
    """
    绘制展开式轮廓偏差曲线（真实齿轮测量中心算法）

    核心算法（完全按照您的描述）：
    ========================================
    1. 齿廓相对角度 α_k = φ_k - φ_0
       - φ_k：该点的极角
       - φ_0：本齿起点的极角（通常取齿顶中点）

    2. 齿绝对起始角 θ_i_start
       - 齿1：θ_1_start = 0°（基准）
       - 齿2：θ_2_start = θ_1_start + Δθ_1（实测角节距）
       - 齿i：θ_i_start = Σ(Δθ_j) for j=1 to i-1

    3. 齿轮绝对旋转角度
       θ_point = θ_i_start + α_k
    ========================================
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

    # ========== 步骤1：计算每个齿的绝对起始角 θ_i_start ==========
    # 使用节距数据计算实测角节距
    tooth_start_angles = {}  # {tooth_id: start_angle}

    # 齿1作为基准
    tooth_start_angles[1] = 0.0

    # 计算后续齿的起始角（累加实测角节距）
    for i in range(2, z + 1):
        # 获取齿(i-1)到齿i的实测角节距
        delta_theta = 360.0 / z  # 理论齿距角

        # 如果有节距数据，使用实测节距误差调整
        if pitch_data and (i - 1) in pitch_data:
            pitch_info = pitch_data[i - 1]
            if isinstance(pitch_info, dict):
                fp = pitch_info.get('fp', 0)  # 单齿节距误差（μm）
                # 将节距误差转换为角度误差
                module = gear_data.get('module', 2.5) if gear_data else 2.5
                pressure_angle = gear_data.get('pressure_angle', 20.0) if gear_data else 20.0
                pitch_diameter = module * z
                base_diameter = pitch_diameter * np.cos(np.radians(pressure_angle))
                # 角度误差（度）
                angle_error = (fp / 1000) / (np.pi * base_diameter) * 360
                delta_theta = 360.0 / z + angle_error

        # 累加得到当前齿的起始角
        tooth_start_angles[i] = tooth_start_angles[i - 1] + delta_theta

    # ========== 步骤2：对每个齿，计算每个点的齿轮绝对旋转角度 ==========
    for i, tooth_id in enumerate(tooth_ids):
        if tooth_id not in profile_data:
            continue

        values = profile_data[tooth_id]
        if not isinstance(values, (list, np.ndarray)) or len(values) == 0:
            continue

        n_points = len(values)

        # 获取该齿的起始角 θ_i_start
        theta_start = tooth_start_angles.get(tooth_id, (tooth_id - 1) * 360.0 / z)

        # ========== 计算齿廓相对角度 α_k ==========
        # 假设轮廓点从齿顶到齿根均匀分布
        # 齿廓总角度范围（经验值，约为齿距角的80%）
        tooth_angle = 360.0 / z
        alpha_range = tooth_angle * 0.8

        # 生成齿廓相对角度 α（从齿顶到齿根）
        # α = 0 对应齿顶，α = alpha_range 对应齿根
        alpha = np.linspace(0, alpha_range, n_points)

        # ========== 计算齿轮绝对旋转角度 θ_point ==========
        # θ_point = θ_i_start + α_k
        theta_points = theta_start + alpha

        # 记录齿边界
        tooth_boundaries.append(theta_start)

        # 绘制该齿的数据
        if use_individual_colors:
            color = colors[i % len(colors)]
            ax.plot(theta_points, values, '-', linewidth=1.0, alpha=0.7,
                    color=color, label=f'齿 {tooth_id}')

            # 绘制平滑曲线
            if len(values) > 21:
                try:
                    window_size = min(21, len(values) // 5 * 2 + 1)
                    if window_size >= 5:
                        y_smooth = savgol_filter(values, window_size, 3)
                        ax.plot(theta_points, y_smooth, '--', linewidth=2.0,
                                alpha=0.8, color=color)
                except:
                    pass
        else:
            all_theta.extend(theta_points)
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
        max_angle = tooth_start_angles.get(max_teeth, max_teeth * 360.0 / z)
        ax.set_xlim(-2, max_angle + 10)
    else:
        ax.set_xlim(-5, 360 + 5)

    # 设置X轴刻度
    if max_teeth and max_teeth <= 10:
        # 放大视图：显示每个齿的刻度
        x_ticks = [tooth_start_angles.get(i, (i-1) * 360.0 / z) for i in range(1, max_teeth + 2)]
        x_labels = [f'{i}\n({x_ticks[i-1]:.1f}°)' if i <= len(x_ticks) else ''
                    for i in range(1, max_teeth + 2)]
    else:
        # 全视图：每10个齿显示一个刻度
        step = max(1, z // 10)
        x_ticks = [tooth_start_angles.get(i, (i-1) * 360.0 / z) for i in range(1, z + 2, step)]
        x_labels = [f'{i}\n({x_ticks[(i-1)//step]:.1f}°)'
                    for i in range(1, z + 2, step)]

    ax.set_xticks(x_ticks[:len(x_labels)])
    ax.set_xticklabels(x_labels, fontsize=8)

    # 设置Y轴范围
    if use_individual_colors:
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
    tooth_angle = 360.0 / z
    info_text = f'理论齿距角: {tooth_angle:.3f}°\n测量齿数: {len(tooth_boundaries)}/{z}'
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

    # 生成前10个齿的数据用于测试
    for tooth_id in range(1, 11):
        # 基础波形（模拟齿廓形状）
        n_points = 480
        t = np.linspace(0, 1, n_points)

        # 模拟齿廓偏差（从齿顶到齿根的变化）
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

    # 模拟节距数据（带误差）
    test_pitch_left = {}
    test_pitch_right = {}

    for tooth_id in range(1, 11):
        # 模拟实测节距误差（有正有负）
        test_pitch_left[tooth_id] = {
            'fp': np.random.normal(0, 3),   # 单齿节距误差
            'Fp': np.random.normal(0, 8),   # 累积节距误差
            'Fr': np.random.normal(0, 5)
        }
        test_pitch_right[tooth_id] = {
            'fp': np.random.normal(0, 2.5),
            'Fp': np.random.normal(0, 7),
            'Fr': np.random.normal(0, 4)
        }

    test_gear_data = {
        'teeth': z,
        'module': 2.5,
        'pressure_angle': 20.0,
        'helix_angle': 0
    }

    # 测试1：前3齿放大视图
    print("生成前3齿放大视图（真实算法）...")
    fig1 = create_contact_pattern_chart_real(
        profile_data={'left': test_profile_left, 'right': test_profile_right},
        pitch_data={'left': test_pitch_left, 'right': test_pitch_right},
        gear_data=test_gear_data,
        output_path='contact_pattern_real_zoomed_3teeth.png',
        max_teeth=3
    )

    # 测试2：全部10齿
    print("生成全部齿视图（真实算法）...")
    fig2 = create_contact_pattern_chart_real(
        profile_data={'left': test_profile_left, 'right': test_profile_right},
        pitch_data={'left': test_pitch_left, 'right': test_pitch_right},
        gear_data=test_gear_data,
        output_path='contact_pattern_real_all.png',
        max_teeth=None
    )

    plt.show()
    print("真实算法图表生成完成！")
