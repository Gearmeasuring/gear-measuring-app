"""
自适应正弦波分解频谱分析
使用最小二乘法逐步提取最大阶次的正弦波成分
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contact_pattern_chart_mka import extract_data_from_mka


def adaptive_sine_decomposition(signal, z, max_harmonics=10):
    """
    自适应正弦波分解
    
    算法步骤：
    1. 在频谱中搜索最大幅值的频率成分
    2. 用最小二乘法拟合该频率的正弦波（幅值+相位）
    3. 从原始信号中减去拟合的正弦波
    4. 对剩余信号重复步骤1-3
    5. 直到提取出max_harmonics个正弦波
    
    参数:
        signal: 输入信号（已合并所有齿，代表齿轮旋转一周）
        z: 齿数（用于显示阶数）
        max_harmonics: 提取的最大谐波数量
    
    返回:
        harmonics: [{order, amplitude, phase, frequency}, ...]
    """
    
    n = len(signal)
    remaining_signal = signal.copy()
    harmonics = []
    
    # 采样点对应的角度（0到2π，代表齿轮旋转一周）
    x = np.linspace(0, 2 * np.pi, n, endpoint=False)
    
    # 要搜索的谐波阶数范围
    # 1ZE = 齿轮旋转一周出现1个波 = frequency=1
    # 2ZE = 齿轮旋转一周出现2个波 = frequency=2
    search_orders = list(range(1, max_harmonics + 1))
    
    for iteration in range(max_harmonics):
        best_harmonic = None
        best_residual = np.inf
        
        # 在当前剩余信号中搜索最大幅值的谐波
        for order in search_orders:
            # 该阶谐波的频率（齿轮旋转一周出现的波数）
            # 1ZE → frequency=1, 2ZE → frequency=2, ...
            frequency = order
            
            # 定义正弦波模型: A * sin(frequency * x + phase)
            def sine_model(params, x):
                A, phase = params
                return A * np.sin(frequency * x + phase)
            
            # 定义残差函数
            def residual(params):
                return remaining_signal - sine_model(params, x)
            
            # 使用最小二乘法拟合
            # 初始猜测：幅值为信号标准差，相位为0
            initial_guess = [np.std(remaining_signal), 0]
            
            try:
                result = least_squares(residual, initial_guess, method='lm')
                
                if result.success:
                    A_fit, phase_fit = result.x
                    
                    # 计算拟合后的残差
                    fitted_signal = sine_model(result.x, x)
                    residual_norm = np.sum((remaining_signal - fitted_signal) ** 2)
                    
                    # 选择幅值最大的谐波
                    if abs(A_fit) > (best_harmonic['amplitude'] if best_harmonic else 0):
                        best_harmonic = {
                            'order': order,
                            'amplitude': abs(A_fit),
                            'phase': phase_fit,
                            'frequency': frequency,
                            'fitted_signal': fitted_signal
                        }
                        best_residual = residual_norm
                        
            except Exception as e:
                continue
        
        if best_harmonic is None:
            break
        
        # 保存提取的谐波
        harmonics.append(best_harmonic)
        
        # 从剩余信号中减去该谐波
        remaining_signal = remaining_signal - best_harmonic['fitted_signal']
        
        # 从搜索列表中移除已提取的阶数
        if best_harmonic['order'] in search_orders:
            search_orders.remove(best_harmonic['order'])
        
        print(f"  提取第{iteration+1}个谐波: 阶数={best_harmonic['order']}ZE, "
              f"幅值={best_harmonic['amplitude']:.4f}μm")
    
    return harmonics


def create_spectrum_adaptive_chart(file_path, output_path=None, max_harmonics=10):
    """
    创建自适应正弦波分解频谱图
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
    
    print(f"齿轮参数: 齿数 z={z}")
    print(f"提取前{max_harmonics}个最大谐波成分...")
    
    # 分析左齿面
    print("\n分析左齿面...")
    left_signal = prepare_signal(profile_data.get('left', {}), gear_data, pitch_data.get('left', {}))
    if left_signal is not None:
        left_harmonics = adaptive_sine_decomposition(left_signal, z, max_harmonics)
    else:
        left_harmonics = []
    
    # 分析右齿面
    print("\n分析右齿面...")
    right_signal = prepare_signal(profile_data.get('right', {}), gear_data, pitch_data.get('right', {}))
    if right_signal is not None:
        right_harmonics = adaptive_sine_decomposition(right_signal, z, max_harmonics)
    else:
        right_harmonics = []
    
    # 创建图形 - 4行布局：合并曲线 + 频谱图
    fig = plt.figure(figsize=(16, 14))
    fig.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.08, hspace=0.35)
    
    # 第1行：左齿面合并曲线
    ax1 = fig.add_subplot(4, 1, 1)
    if left_signal is not None:
        plot_merged_signal(ax1, left_signal, z, '左齿面合并曲线 (Profile left)')
    
    # 第2行：右齿面合并曲线
    ax2 = fig.add_subplot(4, 1, 2)
    if right_signal is not None:
        plot_merged_signal(ax2, right_signal, z, '右齿面合并曲线 (Profile right)')
    
    # 第3行：左齿面频谱
    ax3 = fig.add_subplot(4, 1, 3)
    plot_adaptive_spectrum(ax3, left_harmonics, z, '左齿面频谱 (Profile left)')
    
    # 第4行：右齿面频谱
    ax4 = fig.add_subplot(4, 1, 4)
    plot_adaptive_spectrum(ax4, right_harmonics, z, '右齿面频谱 (Profile right)')
    
    # 添加总标题
    file_name = os.path.basename(file_path)
    fig.suptitle(f'自适应正弦波分解频谱分析\n文件: {file_name} | 齿数 z={z}',
                 fontsize=14, fontweight='bold', y=0.98)
    
    # 保存
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"\n图表已保存到: {output_path}")
    
    return fig


def plot_merged_signal(ax, signal, z, title):
    """绘制合并后的信号曲线"""
    
    ax.set_facecolor('#fafafa')
    
    n = len(signal)
    # X轴：旋转角度（0到360度）
    x = np.linspace(0, 360, n)
    
    # 绘制信号
    ax.plot(x, signal, 'b-', linewidth=0.3, alpha=0.7, label='合并信号')
    
    # 添加零线
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    
    # 添加齿边界（每隔一个齿距角）
    tooth_angle = 360.0 / z
    for i in range(z + 1):
        ax.axvline(x=i * tooth_angle, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
    
    # 设置坐标轴
    ax.set_xlabel('旋转角度 (°)', fontsize=10)
    ax.set_ylabel('偏差 (μm)', fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=8)
    
    # 设置X轴范围和刻度
    ax.set_xlim(0, 360)
    x_ticks = np.arange(0, 361, 60)
    ax.set_xticks(x_ticks)
    
    # 设置Y轴范围
    y_max = max(abs(np.min(signal)), abs(np.max(signal)))
    y_limit = max(y_max * 1.1, 5)
    ax.set_ylim(-y_limit, y_limit)
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 添加信息文字
    info_text = f'数据点: {n}\n齿数: {z}'
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))


def prepare_signal(profile_data, gear_data=None, pitch_data=None):
    """
    准备信号数据 - 完整齿轮测量中心算法
    
    步骤：
    1. 用轮廓算：每个点在齿内的相对角 α
    2. 用节距算：每个齿在齿轮上的绝对起始角 θ_i_start
    3. 对每个点：θ_point = θ_i_start + α
    4. 所有点按 θ_point 从小到大排序
    5. 去除鼓形和斜率偏差
    6. 去除直流分量
    """
    if not profile_data or len(profile_data) == 0:
        return None
    
    # 获取评价范围
    eval_start = gear_data.get('eval_start', 0) if gear_data else 0
    eval_end = gear_data.get('eval_end', 42) if gear_data else 42
    measure_end = gear_data.get('measure_end', 42) if gear_data else 42
    
    # 获取齿轮参数
    z = gear_data.get('teeth', 87) if gear_data else 87
    module = gear_data.get('module', 2.5) if gear_data else 2.5
    pressure_angle = gear_data.get('pressure_angle', 20.0) if gear_data else 20.0
    
    # 计算基圆半径
    pitch_diameter = module * z
    base_diameter = pitch_diameter * np.cos(np.radians(pressure_angle))
    rb = base_diameter / 2
    
    # 计算评价范围对应的点索引
    points_per_tooth = 480
    point_spacing = measure_end / points_per_tooth
    
    eval_start_idx = int(eval_start / point_spacing)
    eval_end_idx = int(eval_end / point_spacing)
    
    eval_start_idx = max(0, eval_start_idx)
    eval_end_idx = min(points_per_tooth, eval_end_idx)
    
    points_in_eval = eval_end_idx - eval_start_idx
    
    # 步骤1：计算齿廓相对角度 α（渐开线极角）
    d1 = gear_data.get('d1', eval_start * 4.2) if gear_data else eval_start * 4.2
    d2 = gear_data.get('d2', eval_end * 4.2) if gear_data else eval_end * 4.2
    
    # 齿廓相对角度 α（弧度）
    alpha_angles = calculate_involute_polar_angles(d1, d2, rb, points_in_eval)
    # 转换为度
    alpha_deg = np.degrees(alpha_angles)
    # 归一化：起点为0
    alpha_relative = alpha_deg - alpha_deg[0]
    
    print(f"  评价范围: {eval_start}mm ~ {eval_end}mm")
    print(f"  评价范围点索引: {eval_start_idx} ~ {eval_end_idx} (共{points_in_eval}点/齿)")
    print(f"  齿廓相对角度 α: {alpha_relative[0]:.4f}° ~ {alpha_relative[-1]:.4f}°")
    
    # 步骤2：计算每个齿的绝对起始角 θ_i_start（使用节距数据）
    tooth_start_angles = calculate_tooth_start_angles(z, pitch_data, gear_data)
    
    print(f"  齿起始角范围: {tooth_start_angles.get(1, 0):.4f}° ~ {tooth_start_angles.get(z, 0):.4f}°")
    
    # 收集所有点的数据
    all_points = []  # [(theta_point, deviation), ...]
    tooth_ids = sorted([tid for tid in profile_data.keys() if isinstance(tid, int)])
    
    print(f"  预处理 {len(tooth_ids)} 个齿的数据...")
    
    # 步骤3：对每个齿的每个点计算 θ_point = θ_i_start + α
    for tooth_id in tooth_ids:
        values = profile_data[tooth_id]
        if not isinstance(values, (list, np.ndarray)) or len(values) == 0:
            continue
        
        tooth_data_full = np.array(values, dtype=float)
        
        # 截取评价范围内的点
        if len(tooth_data_full) >= eval_end_idx:
            tooth_data = tooth_data_full[eval_start_idx:eval_end_idx]
        else:
            tooth_data = tooth_data_full
        
        # 去除斜率和鼓形偏差
        tooth_data = remove_slope_deviation(tooth_data)
        tooth_data = remove_crown_deviation(tooth_data)
        
        # 获取该齿的绝对起始角
        theta_start = tooth_start_angles.get(tooth_id, (tooth_id - 1) * 360.0 / z)
        
        # 对每个点计算 θ_point = θ_i_start + α
        for i, (deviation, alpha) in enumerate(zip(tooth_data, alpha_relative)):
            theta_point = theta_start + alpha
            all_points.append((theta_point, deviation))
    
    if len(all_points) == 0:
        return None
    
    # 步骤4：按 θ_point 从小到大排序
    all_points.sort(key=lambda x: x[0])
    
    # 提取排序后的数据
    theta_sorted = np.array([p[0] for p in all_points])
    signal = np.array([p[1] for p in all_points])
    
    print(f"  合并后信号长度: {len(signal)} 点")
    print(f"  旋转角度范围: {theta_sorted[0]:.4f}° ~ {theta_sorted[-1]:.4f}°")
    
    # 步骤5：去除直流分量
    signal = signal - np.mean(signal)
    
    print(f"  最终信号长度: {len(signal)} 点")
    return signal


def calculate_tooth_start_angles(z, pitch_data, gear_data):
    """
    计算每个齿的绝对起始角 θ_i_start
    
    使用节距数据累加：
    - 齿1：θ_1_start = 0°（基准）
    - 齿2：θ_2_start = θ_1_start + Δθ_1
    - 齿i：θ_i_start = Σ(Δθ_j) for j=1 to i-1
    
    参数:
        z: 齿数
        pitch_data: 节距数据 {tooth_id: {'fp': x, 'Fp': y}}
        gear_data: 齿轮参数
    
    返回:
        {tooth_id: start_angle}
    """
    tooth_start_angles = {}
    
    # 齿1作为基准
    tooth_start_angles[1] = 0.0
    
    # 理论齿距角
    theoretical_pitch_angle = 360.0 / z
    
    # 齿轮参数
    module = gear_data.get('module', 2.5) if gear_data else 2.5
    pressure_angle = gear_data.get('pressure_angle', 20.0) if gear_data else 20.0
    pitch_diameter = module * z
    base_diameter = pitch_diameter * np.cos(np.radians(pressure_angle))
    
    # 累加计算每个齿的起始角
    for i in range(2, z + 1):
        # 理论齿距角
        delta_theta = theoretical_pitch_angle
        
        # 如果有节距数据，使用实测节距误差调整
        if pitch_data and (i - 1) in pitch_data:
            pitch_info = pitch_data[i - 1]
            if isinstance(pitch_info, dict):
                fp = pitch_info.get('fp', 0)  # 单齿节距误差（μm）
                # 将节距误差转换为角度误差
                # 角度误差 = (fp / 1000) / (π × 基圆直径) × 360
                angle_error = (fp / 1000) / (np.pi * base_diameter) * 360
                delta_theta = theoretical_pitch_angle + angle_error
        
        # 累加得到当前齿的起始角
        tooth_start_angles[i] = tooth_start_angles[i - 1] + delta_theta
    
    return tooth_start_angles


def calculate_involute_polar_angles(d_start, d_end, rb, n_points):
    """
    根据渐开线理论计算极角
    
    参数:
        d_start: 起始直径 (mm)
        d_end: 终止直径 (mm)
        rb: 基圆半径 (mm)
        n_points: 点数
    
    返回:
        polar_angles: 极角数组 (弧度)
    """
    # 直径从 d_start 到 d_end
    diameters = np.linspace(d_start, d_end, n_points)
    
    polar_angles = []
    for d in diameters:
        r = d / 2  # 半径
        if r > rb:
            # 压力角
            alpha = np.arccos(rb / r)
            # 渐开线函数 inv(alpha) = tan(alpha) - alpha
            inv_alpha = np.tan(alpha) - alpha
            # 极角 = inv(alpha)
            polar_angles.append(inv_alpha)
        else:
            polar_angles.append(0)
    
    return np.array(polar_angles)


def remove_slope_deviation(data):
    """
    剔除斜率偏差
    使用线性回归去除线性趋势
    """
    n = len(data)
    x = np.arange(n)
    
    # 线性拟合: y = a * x + b
    A = np.vstack([x, np.ones(n)]).T
    a, b = np.linalg.lstsq(A, data, rcond=None)[0]
    
    # 去除线性趋势
    linear_trend = a * x + b
    data_corrected = data - linear_trend
    
    return data_corrected


def remove_crown_deviation(data):
    """
    剔除鼓形偏差
    使用抛物线拟合去除二次趋势
    """
    n = len(data)
    x = np.arange(n)
    
    # 抛物线拟合: y = a * x^2 + b * x + c
    # 使用最小二乘法拟合二次曲线
    A = np.vstack([x**2, x, np.ones(n)]).T
    a, b, c = np.linalg.lstsq(A, data, rcond=None)[0]
    
    # 去除抛物线趋势
    parabolic_trend = a * x**2 + b * x + c
    data_corrected = data - parabolic_trend
    
    return data_corrected


def plot_adaptive_spectrum(ax, harmonics, z, title):
    """绘制自适应频谱图"""
    
    ax.set_facecolor('#fafafa')
    
    if not harmonics or len(harmonics) == 0:
        ax.text(0.5, 0.5, '无数据', ha='center', va='center',
                transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=11, fontweight='bold')
        return
    
    # 提取数据
    orders = [h['order'] for h in harmonics]
    amplitudes = [h['amplitude'] for h in harmonics]
    
    # 按阶数排序（从小到大）
    sorted_data = sorted(zip(orders, amplitudes), key=lambda x: x[0])
    orders_sorted = [d[0] for d in sorted_data]
    amplitudes_sorted = [d[1] for d in sorted_data]
    
    # 绘制柱状图 - X轴直接显示阶数
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    bars = ax.bar(orders_sorted, amplitudes_sorted, 
                  color=[colors[(o-1) % len(colors)] for o in orders_sorted],
                  alpha=0.7, edgecolor='black', linewidth=0.5, width=0.8)
    
    # 添加数值标签
    y_max_val = max(amplitudes_sorted)
    for order, amp in zip(orders_sorted, amplitudes_sorted):
        # 在柱子上方显示幅值
        ax.text(order, amp + y_max_val * 0.02, f'{amp:.3f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold', color='blue')
    
    # 添加网格线
    ax.grid(True, axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 设置坐标轴
    ax.set_xlabel('圆周内波数', fontsize=10)
    ax.set_ylabel('幅值 (μm)', fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10)
    
    # 设置X轴刻度 - 显示波数和对应的频率（阶数O = 波数 × 齿数）
    ax.set_xticks(orders_sorted)
    x_labels = [f'{o}\n(O={o*z})' for o in orders_sorted]
    ax.set_xticklabels(x_labels, fontsize=8)
    
    # 设置Y轴范围
    y_max = y_max_val * 1.2
    ax.set_ylim(-y_max * 0.05, y_max)
    
    # 添加零线
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    
    # 添加说明文字
    info_text = f'波数 × {z} = 阶数(O)'
    ax.text(0.98, 0.98, info_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))


# 测试函数
if __name__ == '__main__':
    import glob
    
    # 查找目录中的MKA文件
    mka_files = glob.glob('*.mka')
    
    if not mka_files:
        print("错误: 未找到MKA文件")
        sys.exit(1)
    
    # 使用指定的MKA文件
    target_file = '263751-018-WAV.mka'
    if target_file in mka_files:
        mka_file = target_file
    else:
        mka_file = mka_files[0]
    
    print(f"\n处理文件: {mka_file}")
    
    # 生成自适应频谱分析图
    fig = create_spectrum_adaptive_chart(
        mka_file,
        output_path='spectrum_adaptive.png',
        max_harmonics=10
    )
    
    if fig:
        plt.show()
        print("\n自适应频谱分析图生成完成！")
    else:
        print("\n频谱分析图生成失败")
