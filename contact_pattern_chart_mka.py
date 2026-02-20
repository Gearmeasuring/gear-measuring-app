"""
考虑螺距的轮廓测量序列图 - 使用真实MKA文件数据
完全按照齿轮测量中心的处理逻辑：
1. 读取MKA文件中的真实轮廓数据
2. 读取MKA文件中的真实节距数据
3. 处理全部齿的数据
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import sys
import os

# 添加主程序目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_contact_pattern_chart_from_mka(file_path, output_path=None, max_teeth=None):
    """
    从MKA文件创建考虑螺距的轮廓测量序列图

    参数:
        file_path: MKA文件路径
        output_path: 输出文件路径（可选）
        max_teeth: 最大显示齿数（None表示显示所有齿）

    返回:
        fig: matplotlib图形对象
    """

    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    # 从MKA文件提取数据
    print(f"正在读取MKA文件: {file_path}")
    gear_data, profile_data, pitch_data = extract_data_from_mka(file_path)

    if not gear_data:
        print("错误: 无法从MKA文件提取齿轮数据")
        return None

    z = gear_data.get('teeth', 0)
    if z <= 0:
        print("错误: 无法获取齿数")
        return None

    module = gear_data.get('module', 2.5)

    print(f"齿轮参数: 齿数={z}, 模数={module}")
    print(f"左齿面轮廓数据: {len(profile_data.get('left', {}))} 个齿")
    print(f"右齿面轮廓数据: {len(profile_data.get('right', {}))} 个齿")
    print(f"左齿面节距数据: {len(pitch_data.get('left', {}))} 个齿")
    print(f"右齿面节距数据: {len(pitch_data.get('right', {}))} 个齿")

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
    left_profile = profile_data.get('left', {})
    left_pitch = pitch_data.get('left', {})
    plot_unfolded_profile_mka(ax1, left_profile, left_pitch, z,
                              f'左齿面 - 真实MKA数据 (文件: {os.path.basename(file_path)})',
                              gear_data, max_teeth)

    # ========== 第2行：右齿面 ==========
    ax2 = fig.add_subplot(2, 1, 2)
    right_profile = profile_data.get('right', {})
    right_pitch = pitch_data.get('right', {})
    plot_unfolded_profile_mka(ax2, right_profile, right_pitch, z,
                              f'右齿面 - 真实MKA数据 (文件: {os.path.basename(file_path)})',
                              gear_data, max_teeth)

    # 添加总标题
    if is_zoomed:
        title = f'考虑螺距的轮廓测量序列 - 前{max_teeth}齿 (总齿数 z={z})'
    else:
        title = f'考虑螺距的轮廓测量序列 - 全部齿 (齿数 z={z}, 模数 m={module})'

    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)

    # 保存或返回
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"图表已保存到: {output_path}")

    return fig


def extract_data_from_mka(file_path):
    """
    从MKA文件提取齿轮数据、轮廓数据和节距数据

    返回:
        gear_data: 齿轮基本参数
        profile_data: {'left': {tooth_id: [values]}, 'right': {...}}
        pitch_data: {'left': {tooth_id: {'fp': x, 'Fp': y}}, 'right': {...}}
    """

    gear_data = {}
    profile_data = {'left': {}, 'right': {}}
    pitch_data = {'left': {}, 'right': {}}

    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # 提取齿轮基本参数
        gear_data = extract_gear_basic_data(content)

        # 提取轮廓数据（Profil）
        profile_data['left'] = extract_profile_data(content, 'links')
        profile_data['right'] = extract_profile_data(content, 'rechts')

        # 提取节距数据
        pitch_data['left'], pitch_data['right'] = extract_pitch_data(content)

    except Exception as e:
        print(f"读取MKA文件失败: {e}")
        import traceback
        traceback.print_exc()

    return gear_data, profile_data, pitch_data


def extract_gear_basic_data(content):
    """提取齿轮基本参数"""
    gear_data = {}

    import re

    # 齿数
    patterns = [
        (r'Zähnezahl[^:]*:\s*(-?\d+)', 'teeth', int),
        (r'No\. of teeth[^:]*:\s*(-?\d+)', 'teeth', int),
        (r'22\s*:.*?:\s*(-?\d+)$', 'teeth', int),
    ]

    for pattern, key, dtype in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                gear_data[key] = dtype(match.group(1))
                break
            except:
                pass

    # 模数
    patterns = [
        (r'Normalmodul[^:]*:\s*([\d.]+)', 'module', float),
        (r'21\s*:.*?:\s*([\d.]+)', 'module', float),
    ]

    for pattern, key, dtype in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                gear_data[key] = dtype(match.group(1))
                break
            except:
                pass

    # 压力角
    patterns = [
        (r'Eingriffswinkel[^:]*:\s*([\d.]+)', 'pressure_angle', float),
        (r'24\s*:.*?:\s*([\d.]+)', 'pressure_angle', float),
    ]

    for pattern, key, dtype in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
        if match:
            try:
                gear_data[key] = dtype(match.group(1))
                break
            except:
                pass

    # 评价范围 (Auswertestrecke)
    # Auswerteanfang (b1) - 评价起点
    b1_patterns = [
        r'Auswerteanfang[^:]*:\s*([\d.]+)',
        r'62\s*:.*?b1\s*\[mm\]\.\.\.:\s*([\d.]+)',
    ]
    for pattern in b1_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                gear_data['eval_start'] = float(match.group(1))
                break
            except:
                pass

    # Auswerteende (b2) - 评价终点
    b2_patterns = [
        r'Auswerteende[^:]*:\s*([\d.]+)',
        r'63\s*:.*?b2\s*\[mm\]\.\.\.:\s*([\d.]+)',
    ]
    for pattern in b2_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                gear_data['eval_end'] = float(match.group(1))
                break
            except:
                pass

    # Messende (be) - 测量终点
    be_patterns = [
        r'Messende[^:]*:\s*([\d.]+)',
        r'64\s*:.*?be\s*\[mm\]\.\.\.:\s*([\d.]+)',
    ]
    for pattern in be_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                gear_data['measure_end'] = float(match.group(1))
                break
            except:
                pass

    # 评价范围直径参数
    # Start der Auswertestrecke (d1) - 评价起始直径
    d1_patterns = [
        r'Start der Auswertestrecke[^:]*:\s*d1\s*\[mm\]\.\.\.:\s*([\d.]+)',
        r'42\s*:.*?d1\s*\[mm\]\.\.\.:\s*([\d.]+)',
    ]
    for pattern in d1_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                gear_data['d1'] = float(match.group(1))
                break
            except:
                pass

    # Ende der Auswertestrecke (d2) - 评价终止直径
    d2_patterns = [
        r'Ende der Auswertestrecke[^:]*:\s*d2\s*\[mm\]\.\.\.:\s*([\d.]+)',
        r'43\s*:.*?d2\s*\[mm\]\.\.\.:\s*([\d.]+)',
    ]
    for pattern in d2_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                gear_data['d2'] = float(match.group(1))
                break
            except:
                pass

    # 默认值
    if 'teeth' not in gear_data:
        gear_data['teeth'] = 87
    if 'module' not in gear_data:
        gear_data['module'] = 2.5
    if 'pressure_angle' not in gear_data:
        gear_data['pressure_angle'] = 20.0

    return gear_data


def extract_profile_data(content, side):
    """
    提取轮廓数据

    参数:
        content: MKA文件内容
        side: 'links'（左）或 'rechts'（右）

    返回:
        {tooth_id: [values]}
    """
    profile_data = {}

    import re

    # 查找所有Profil数据块
    # 格式: "Profil:  Zahn-Nr.: X rechts / 480 Werte  / z= 17.5"
    profil_pattern = re.compile(
        r'Profil:\s+Zahn-Nr\.:\s*(\d+)\s*' + side + r'\s*/\s*480\s*Werte\s*/\s*z=\s*([-\d.]+)',
        re.IGNORECASE
    )

    matches = list(profil_pattern.finditer(content))
    print(f"  找到 {len(matches)} 个{side}齿面轮廓数据块")

    for match in matches:
        try:
            tooth_id = int(match.group(1))
            start_pos = match.end()

            # 查找接下来的480个数值
            # 数据通常在匹配后的40行内（每行12个数值）
            data_text = content[start_pos:start_pos + 8000]

            # 提取数值（浮点数）
            values = []
            # 匹配浮点数格式：1.676, 1.862 等
            float_pattern = r'[-+]?\d+\.\d+'
            numbers = re.findall(float_pattern, data_text)

            for num_str in numbers[:480]:
                try:
                    val = float(num_str)
                    values.append(val)
                except:
                    pass

            if len(values) == 480:
                profile_data[tooth_id] = values
                print(f"    齿 {tooth_id}: {len(values)} 个数据点")
            else:
                print(f"    齿 {tooth_id}: 数据点不足 ({len(values)}/480)")

        except Exception as e:
            print(f"    提取齿 {match.group(1)} 数据失败: {e}")
            continue

    return profile_data


def extract_pitch_data(content):
    """
    提取节距数据

    返回:
        pitch_left: {tooth_id: {'fp': x, 'Fp': y, 'Fr': z}}
        pitch_right: {tooth_id: {'fp': x, 'Fp': y, 'Fr': z}}
    """
    pitch_left = {}
    pitch_right = {}

    import re

    # 查找节距数据块
    # 左齿面
    left_pattern = r'linke Zahnflanke\s*\n\s*Zahn-Nr\.\s+fp\s+Fp\s+Fr\s*\n((?:\s*\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s*\n?)+)'
    left_match = re.search(left_pattern, content, re.IGNORECASE)

    if left_match:
        data_text = left_match.group(1)
        lines = data_text.strip().split('\n')
        for line in lines:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    tooth_id = int(parts[0])
                    fp = float(parts[1])
                    Fp = float(parts[2])
                    Fr = float(parts[3])
                    pitch_left[tooth_id] = {'fp': fp, 'Fp': Fp, 'Fr': Fr}
                except:
                    pass

    # 右齿面
    right_pattern = r'rechte Zahnflanke\s*\n\s*Zahn-Nr\.\s+fp\s+Fp\s+Fr\s*\n((?:\s*\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s*\n?)+)'
    right_match = re.search(right_pattern, content, re.IGNORECASE)

    if right_match:
        data_text = right_match.group(1)
        lines = data_text.strip().split('\n')
        for line in lines:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    tooth_id = int(parts[0])
                    fp = float(parts[1])
                    Fp = float(parts[2])
                    Fr = float(parts[3])
                    pitch_right[tooth_id] = {'fp': fp, 'Fp': Fp, 'Fr': Fr}
                except:
                    pass

    return pitch_left, pitch_right


def plot_unfolded_profile_mka(ax, profile_data, pitch_data, z, title,
                              gear_data, max_teeth=None):
    """
    绘制展开式轮廓偏差曲线（使用真实MKA数据）

    核心算法：
    θ_point = θ_i_start + α_k
    """

    ax.set_facecolor('#fafafa')

    if not profile_data or len(profile_data) == 0:
        ax.text(0.5, 0.5, '无轮廓数据', ha='center', va='center',
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

    print(f"  绘制 {len(tooth_ids)} 个齿的数据")

    # 准备数据
    all_theta = []
    all_deviation = []
    tooth_boundaries = []

    # 颜色方案
    if max_teeth and max_teeth <= 5:
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        use_individual_colors = True
    else:
        use_individual_colors = False

    # 计算每个齿的绝对起始角
    tooth_start_angles = {}
    tooth_start_angles[1] = 0.0

    for i in range(2, z + 1):
        delta_theta = 360.0 / z

        if pitch_data and (i - 1) in pitch_data:
            pitch_info = pitch_data[i - 1]
            if isinstance(pitch_info, dict):
                fp = pitch_info.get('fp', 0)
                module = gear_data.get('module', 2.5)
                pressure_angle = gear_data.get('pressure_angle', 20.0)
                pitch_diameter = module * z
                base_diameter = pitch_diameter * np.cos(np.radians(pressure_angle))
                angle_error = (fp / 1000) / (np.pi * base_diameter) * 360
                delta_theta = 360.0 / z + angle_error

        tooth_start_angles[i] = tooth_start_angles[i - 1] + delta_theta

    # 绘制每个齿的数据
    for i, tooth_id in enumerate(tooth_ids):
        if tooth_id not in profile_data:
            continue

        values = profile_data[tooth_id]
        if not isinstance(values, (list, np.ndarray)) or len(values) == 0:
            continue

        n_points = len(values)
        theta_start = tooth_start_angles.get(tooth_id, (tooth_id - 1) * 360.0 / z)

        # 计算齿廓相对角度
        tooth_angle = 360.0 / z
        alpha_range = tooth_angle * 0.8
        alpha = np.linspace(0, alpha_range, n_points)

        # 计算齿轮绝对旋转角度
        theta_points = theta_start + alpha

        tooth_boundaries.append(theta_start)

        # 绘制
        if use_individual_colors:
            color = colors[i % len(colors)]
            ax.plot(theta_points, values, '-', linewidth=1.0, alpha=0.7,
                    color=color, label=f'齿 {tooth_id}')

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

    # 统一绘制
    if not use_individual_colors and len(all_theta) > 0:
        all_theta = np.array(all_theta)
        all_deviation = np.array(all_deviation)

        sort_idx = np.argsort(all_theta)
        all_theta = all_theta[sort_idx]
        all_deviation = all_deviation[sort_idx]

        # 绘制原始数据
        ax.plot(all_theta, all_deviation, 'r-', linewidth=0.5, alpha=0.5, label='轮廓偏差')

        # 绘制平滑曲线
        if len(all_deviation) > 101:
            try:
                window_size = min(101, len(all_deviation) // 20 * 2 + 1)
                if window_size >= 5:
                    y_smooth = savgol_filter(all_deviation, window_size, 3)
                    ax.plot(all_theta, y_smooth, 'b-', linewidth=1.5,
                            alpha=0.8, label='趋势曲线')
            except:
                pass

    # 添加齿边界
    for boundary in tooth_boundaries:
        ax.axvline(x=boundary, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)

    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)

    ax.set_xlabel('齿轮绝对旋转角度 θ (°)', fontsize=11)
    ax.set_ylabel('偏差 (μm)', fontsize=11)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=8)

    # 设置X轴范围
    if max_teeth:
        max_angle = tooth_start_angles.get(max_teeth, max_teeth * 360.0 / z)
        ax.set_xlim(-2, max_angle + 10)
    else:
        ax.set_xlim(-5, 360 + 5)

    # 设置X轴刻度
    if max_teeth and max_teeth <= 10:
        x_ticks = [tooth_start_angles.get(i, (i-1) * 360.0 / z) for i in range(1, max_teeth + 2)]
        x_labels = [f'{i}\n({x_ticks[i-1]:.1f}°)' if i <= len(x_ticks) else ''
                    for i in range(1, max_teeth + 2)]
    else:
        step = max(1, z // 20)
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

    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)

    if use_individual_colors:
        ax.legend(loc='upper right', fontsize=9, ncol=3)
    else:
        ax.legend(loc='upper right', fontsize=9)

    tooth_angle = 360.0 / z
    info_text = f'理论齿距角: {tooth_angle:.3f}°\n测量齿数: {len(tooth_boundaries)}/{z}'
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))


# 测试函数
if __name__ == '__main__':
    import glob

    # 查找目录中的MKA文件
    mka_files = glob.glob('*.mka')

    if not mka_files:
        print("错误: 未找到MKA文件")
        print("请确保当前目录中有.mka文件")
        sys.exit(1)

    # 使用第一个MKA文件
    mka_file = mka_files[0]
    print(f"找到MKA文件: {mka_file}")

    # 生成全部齿的图表
    print("\n生成全部齿图表...")
    fig = create_contact_pattern_chart_from_mka(
        mka_file,
        output_path='contact_pattern_mka_all.png',
        max_teeth=None  # 显示所有齿
    )

    if fig:
        plt.show()
        print("图表生成完成！")
    else:
        print("图表生成失败")
