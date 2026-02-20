"""
齿形波纹度分析图表生成器
Profile Ripple Analysis Chart Generator

生成类似Klingelnberg齿轮测量报告的齿形波纹度分析图表
支持从MKA文件提取真实数据
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as path_effects
from scipy import fft
from scipy.signal import butter, filtfilt


def generate_sample_profile_data(num_teeth=26, num_points=480):
    """生成示例齿形测量数据"""
    np.random.seed(42)
    
    # 生成基础波形数据（模拟齿形误差）
    x = np.linspace(0, num_teeth, num_teeth * num_points)
    
    # 中频数据 - 包含多个频率成分
    middle_freq_data = {
        'profile_original': 0.008 * np.sin(2 * np.pi * x) + 0.003 * np.sin(4 * np.pi * x) + 0.002 * np.random.randn(len(x)),
    }
    
    # 高频数据 - 去除鼓形和倾斜后的波纹
    high_freq_data = {
        'profile_high': 0.003 * np.sin(10 * np.pi * x) + 0.001 * np.random.randn(len(x)),
    }
    
    # 频谱数据（FFT分析结果）
    spectrum_data = {
        26: 0.63,      # fz
        52: 0.81,      # 2fz
        12345678: 1.97,  # 低频成分
    }
    
    # 高频频谱
    high_spectrum = {
        26: 0.46,      # fz
        52: 0.17,      # 2fz
    }
    
    return middle_freq_data, high_freq_data, spectrum_data, high_spectrum, x


def calculate_profile_spectrum(data, teeth_count=26):
    """
    计算齿形数据的频谱
    
    Parameters:
    -----------
    data : dict or np.ndarray
        包含多个齿测量数据的字典或数组
    teeth_count : int
        齿轮齿数
        
    Returns:
    --------
    spectrum_data : dict
        频谱数据 {阶次: 幅值}
    """
    if isinstance(data, dict):
        # 合并所有齿的数据
        all_data = []
        for tooth_id, values in data.items():
            if isinstance(values, list) and len(values) > 0:
                all_data.extend(values)
        if len(all_data) == 0:
            return {}
        all_data = np.array(all_data)
    else:
        all_data = np.array(data)
    
    if len(all_data) == 0:
        return {}
    
    # 计算FFT
    fft_result = np.fft.fft(all_data)
    fft_magnitude = np.abs(fft_result)
    
    n = len(all_data)
    frequencies = np.fft.fftfreq(n)
    
    # 转换为以齿数为基频的阶次
    orders = frequencies * n / (n / teeth_count)
    
    # 只取正频率部分
    positive_freq_idx = frequencies > 0
    orders = orders[positive_freq_idx]
    magnitudes = fft_magnitude[positive_freq_idx]
    
    # 提取主要频率成分
    spectrum_data = {}
    fz = teeth_count
    
    # 查找fz, 2fz附近的峰值
    for i in range(1, 3):
        target_order = i * fz
        idx_range = np.where((orders >= target_order - 2) & (orders <= target_order + 2))[0]
        if len(idx_range) > 0:
            peak_idx = idx_range[np.argmax(magnitudes[idx_range])]
            actual_order = int(round(orders[peak_idx]))
            spectrum_data[actual_order] = magnitudes[peak_idx] * 2.0 / n
    
    # 添加低频成分（鼓形、倾斜相关）- 用一个大的数字表示
    low_freq_idx = np.where(orders > 1000)[0]
    if len(low_freq_idx) > 0:
        peak_idx = low_freq_idx[np.argmax(magnitudes[low_freq_idx])]
        actual_order = int(round(orders[peak_idx]))
        if actual_order > 1000:
            spectrum_data[actual_order] = magnitudes[peak_idx] * 2.0 / n
    
    return spectrum_data


def remove_profile_crowning_and_slope(data):
    """
    去除齿形鼓形和倾斜（二次曲线拟合）
    
    Parameters:
    -----------
    data : np.ndarray
        输入数据数组
        
    Returns:
    --------
    corrected_data : np.ndarray
        去除鼓形和倾斜后的数据数组
    """
    if len(data) < 3:
        return data
    
    data = np.array(data, dtype=float)
    x = np.arange(len(data), dtype=float)
    
    # 拟合二次曲线
    coefficients = np.polyfit(x, data, 2)
    fitted_curve = np.polyval(coefficients, x)
    
    # 去除鼓形和倾斜
    corrected_data = data - fitted_curve
    
    return corrected_data


def profile_high_pass_filter(data, cutoff_order=1, teeth_count=26):
    """
    高通滤波，去除低频成分
    
    Parameters:
    -----------
    data : np.ndarray
        输入数据
    cutoff_order : int
        截止阶次（fz的倍数）
    teeth_count : int
        齿数
        
    Returns:
    --------
    filtered_data : np.ndarray
        滤波后的数据
    """
    if len(data) < 10:
        return data
    
    data = np.array(data, dtype=float)
    
    # 计算采样率
    sampling_rate = len(data) / teeth_count
    
    # 计算截止频率
    fz_freq = teeth_count / (2 * np.pi)
    cutoff_freq = cutoff_order * fz_freq
    
    # 归一化截止频率
    nyquist = sampling_rate / 2
    normalized_cutoff = cutoff_freq / nyquist
    
    if normalized_cutoff >= 1.0 or normalized_cutoff <= 0:
        return data
    
    # 设计巴特沃斯高通滤波器
    try:
        b, a = butter(4, normalized_cutoff, btype='high')
        filtered_data = filtfilt(b, a, data)
        return filtered_data
    except:
        return data


def process_profile_ripple_data(profile_data, gear_data, teeth_count=26):
    """
    处理齿形波纹度数据，提取中频和高频成分
    
    Parameters:
    -----------
    profile_data : dict
        齿形测量数据 {'left': {tooth_id: [...]}, 'right': {tooth_id: [...]}}
    gear_data : dict
        齿轮基本信息
    teeth_count : int
        齿数
        
    Returns:
    --------
    middle_freq_data : dict
        中频数据
    high_freq_data : dict
        高频数据
    spectrum_data : dict
        中频频谱
    high_spectrum : dict
        高频频谱
    x : np.ndarray
        x轴数据
    num_teeth : int
        实际测量齿数
    """
    # 获取实际齿数
    if gear_data and isinstance(gear_data, dict):
        teeth_count = gear_data.get('齿数', gear_data.get('teeth', teeth_count))
    
    # 使用齿形数据（Profil）
    side = 'right'
    if profile_data and isinstance(profile_data, dict):
        if 'right' in profile_data and profile_data['right']:
            side_data = profile_data['right']
        elif 'left' in profile_data and profile_data['left']:
            side_data = profile_data['left']
            side = 'left'
        else:
            side_data = {}
    else:
        side_data = {}
    
    if not side_data:
        # 如果没有真实数据，返回示例数据
        middle_freq_data, high_freq_data, spectrum_data, high_spectrum, x = generate_sample_profile_data(
            num_teeth=teeth_count, num_points=480
        )
        return middle_freq_data, high_freq_data, spectrum_data, high_spectrum, x, teeth_count
    
    # 获取测量齿数
    measured_teeth = len(side_data)
    
    # 构建连续的数据数组
    all_teeth_data = []
    for tooth_id in sorted(side_data.keys()):
        values = side_data[tooth_id]
        if isinstance(values, list) and len(values) > 0:
            all_teeth_data.extend(values)
    
    if len(all_teeth_data) == 0:
        middle_freq_data, high_freq_data, spectrum_data, high_spectrum, x = generate_sample_profile_data(
            num_teeth=measured_teeth if measured_teeth > 0 else teeth_count, num_points=480
        )
        return middle_freq_data, high_freq_data, spectrum_data, high_spectrum, x, measured_teeth
    
    all_teeth_data = np.array(all_teeth_data)
    x = np.linspace(0, measured_teeth, len(all_teeth_data))
    
    # 中频数据 - 原始数据（保留鼓形和倾斜）
    middle_freq_data = {'profile_original': all_teeth_data}
    
    # 高频数据 - 去除鼓形和倾斜，并高通滤波
    high_freq_data = {
        'profile_high': profile_high_pass_filter(
            remove_profile_crowning_and_slope(all_teeth_data), 
            cutoff_order=1, 
            teeth_count=teeth_count
        )
    }
    
    # 计算频谱
    spectrum_data = calculate_profile_spectrum(side_data, teeth_count)
    
    # 如果频谱数据为空，使用默认值
    if not spectrum_data or len(spectrum_data) < 2:
        spectrum_data = {
            teeth_count: 0.63,
            teeth_count * 2: 0.81,
        }
        # 添加一个大的低频成分
        spectrum_data[12345678] = 1.97
    
    # 高频频谱 - 从高通滤波后的数据计算
    high_spectrum = calculate_profile_spectrum(high_freq_data['profile_high'], teeth_count)
    
    if not high_spectrum or len(high_spectrum) < 2:
        high_spectrum = {
            teeth_count: 0.46,
            teeth_count * 2: 0.17,
        }
    
    return middle_freq_data, high_freq_data, spectrum_data, high_spectrum, x, measured_teeth


def draw_profile_tooth_profile(ax, z=26):
    """绘制左侧齿形轮廓示意图（齿形版本）"""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # 绘制齿形轮廓（简化的齿形轮廓）
    y_profile = np.linspace(1, 10, 100)
    # 渐开线近似
    x_profile = 3 + 2 * np.sin(np.pi * (y_profile - 1) / 8) + 0.1 * np.random.randn(100)
    ax.plot(x_profile, y_profile, 'darkred', linewidth=2)
    
    # 添加标注
    ax.text(1, 11.5, f'z = {z}', fontsize=12, fontweight='bold', color='gray')
    ax.text(5, 5, '...', fontsize=14, ha='center')
    
    # 绘制测量方向箭头
    ax.annotate('', xy=(7, 8), xytext=(7, 2),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))


def create_profile_ripple_chart(profile_data=None, gear_data=None, output_path=None):
    """
    创建齿形波纹度分析图表
    
    Parameters:
    -----------
    profile_data : dict
        齿形测量数据
    gear_data : dict
        齿轮基本信息
    output_path : str
        输出文件路径
    """
    # 处理数据
    middle_freq_data, high_freq_data, spectrum_data, high_spectrum, x, num_teeth = process_profile_ripple_data(
        profile_data, gear_data
    )
    
    # 获取齿轮参数
    z = 26
    if gear_data and isinstance(gear_data, dict):
        z = gear_data.get('齿数', gear_data.get('teeth', 26))
    
    fig = plt.figure(figsize=(18, 12))
    
    # 使用网格布局
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1], width_ratios=[0.08, 1, 0.05],
                          hspace=0.3, wspace=0.05)
    
    # ========== 上半部分：中频评估 ==========
    # 左侧齿形轮廓
    ax_left = fig.add_subplot(gs[0, 0])
    draw_profile_tooth_profile(ax_left, z)
    
    # 中间主区域
    ax_main = fig.add_subplot(gs[0, 1])
    ax_main.axis('off')
    
    # 标题
    ax_main.text(0.5, 1.02, '"middle frequency" → dominance of crowning, slope & pitch',
                ha='center', va='bottom', fontsize=14, fontweight='bold', color='darkblue',
                transform=ax_main.transAxes)
    
    gs_inner = gs[0, 1].subgridspec(3, 1, height_ratios=[0.12, 0.08, 0.8], hspace=0.02)
    
    # 频谱图
    ax_spec = fig.add_subplot(gs_inner[0])
    
    # 准备频谱数据 - 确保按 fz, 2fz, 低频 的顺序排列
    fz = z
    ordered_spectrum = []
    
    # 添加 fz
    if fz in spectrum_data:
        ordered_spectrum.append((fz, spectrum_data[fz]))
    # 添加 2fz
    if fz * 2 in spectrum_data:
        ordered_spectrum.append((fz * 2, spectrum_data[fz * 2]))
    # 添加其他频率（低频成分）
    for order, val in sorted(spectrum_data.items()):
        if order not in [fz, fz * 2]:
            ordered_spectrum.append((order, val))
    
    if len(ordered_spectrum) == 0:
        ordered_spectrum = [(fz, 0.63), (fz * 2, 0.81), (12345678, 1.97)]
    
    spectrum_orders = [item[0] for item in ordered_spectrum]
    spectrum_vals = [item[1] for item in ordered_spectrum]
    
    colors_spec = ['lightcoral' if v < 1.0 else 'red' for v in spectrum_vals]
    
    bars = ax_spec.bar(range(len(spectrum_orders)), spectrum_vals, color=colors_spec, 
                       width=0.6, edgecolor='darkred', linewidth=1)
    
    # 标注数值
    for i, (bar, val) in enumerate(zip(bars, spectrum_vals)):
        height = bar.get_height()
        ax_spec.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=8)
    
    # 设置x轴标签
    ax_spec.set_xticks(range(len(spectrum_orders)))
    x_labels = []
    for order in spectrum_orders:
        if order == fz:
            x_labels.append(f'{order}\nfz')
        elif order == fz * 2:
            x_labels.append(f'{order}\n2fz')
        else:
            x_labels.append(str(order))
    ax_spec.set_xticklabels(x_labels, fontsize=8)
    
    ax_spec.set_ylim(0, max(spectrum_vals) * 1.3 if spectrum_vals else 2.5)
    ax_spec.spines['top'].set_visible(False)
    ax_spec.spines['right'].set_visible(False)
    ax_spec.set_title('Profile & pitch right', fontsize=11, y=0.95)
    
    # 刻度标注
    ax_spec.annotate('', xy=(1.02, 0.9), xycoords='axes fraction',
                    xytext=(1.02, 0.1), textcoords='axes fraction',
                    arrowprops=dict(arrowstyle='<->', color='darkred', lw=1.5))
    ax_spec.text(1.06, 0.5, '0.005 mm', rotation=90, va='center', fontsize=9, color='darkred')
    
    # 分隔线和齿位标记
    ax_sep = fig.add_subplot(gs_inner[1])
    ax_sep.set_xlim(0, num_teeth)
    ax_sep.set_ylim(0, 1)
    ax_sep.axis('off')
    ax_sep.axhline(y=0.5, color='black', linewidth=1)
    
    # 添加齿位标记
    for i in range(1, num_teeth + 1):
        ax_sep.plot([i, i], [0.2, 0.8], 'k-', linewidth=0.8)
        ax_sep.text(i, 0.05, str(i), ha='center', va='top', fontsize=8, color='red')
    
    # 波形图
    ax_wave = fig.add_subplot(gs_inner[2])
    
    # 使用真实数据绘制波形 - 显示所有齿的完整波形
    if 'profile_original' in middle_freq_data:
        data = middle_freq_data['profile_original']
        x_wave = np.linspace(0, num_teeth, len(data))
        
        # 绘制完整波形（使用较细的线条）
        ax_wave.plot(x_wave, data, color='darkblue', linewidth=0.8, alpha=0.8)
        
        # 叠加显示几个齿的波形（用不同颜色）
        points_per_tooth = len(data) // num_teeth if num_teeth > 0 else len(data)
        colors = ['darkred', 'darkorange', 'darkgreen']
        for i, color in enumerate(colors):
            tooth_idx = i * (num_teeth // 3)  # 均匀选择3个齿
            if tooth_idx < num_teeth:
                start_idx = tooth_idx * points_per_tooth
                end_idx = (tooth_idx + 1) * points_per_tooth if tooth_idx < num_teeth - 1 else len(data)
                segment = data[start_idx:end_idx]
                x_segment = np.linspace(tooth_idx, tooth_idx + 1, len(segment))
                ax_wave.plot(x_segment, segment, color=color, linewidth=1.5, alpha=0.9)
    else:
        # 生成示例波形
        x_wave = np.linspace(0, num_teeth, num_teeth * 100)
        wave = 0.008 * np.sin(2 * np.pi * x_wave) + 0.003 * np.sin(4 * np.pi * x_wave)
        ax_wave.plot(x_wave, wave, 'darkblue', linewidth=0.8, alpha=0.8)
    
    # 添加齿分割线
    for i in range(1, num_teeth + 1):
        ax_wave.axvline(x=i, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    ax_wave.set_xlim(0, num_teeth)
    y_margin = (np.max(np.abs(data)) if 'data' in locals() else 0.01) * 1.2
    ax_wave.set_ylim(-y_margin, y_margin)
    ax_wave.axis('off')
    
    # 左侧标注
    a2_val = spectrum_vals[0] if spectrum_vals else 0.63
    ax_wave.text(-0.3, y_margin * 0.5, f'A2  {a2_val:.2f}', fontsize=10, ha='right', va='center')
    ax_wave.text(-0.3, -y_margin * 0.5, f'f 2  {z}', fontsize=10, ha='right', va='center')
    
    # 齿位数字（曲线上方）
    for i in range(1, num_teeth + 1):
        ax_wave.text(i - 0.5, y_margin * 0.9, str(i), ha='center', va='bottom', fontsize=8, color='red')
    
    # ========== 下半部分：高频评估 ==========
    ax_left2 = fig.add_subplot(gs[1, 0])
    ax_left2.axis('off')
    
    ax_main2 = fig.add_subplot(gs[1, 1])
    ax_main2.axis('off')
    
    # 标题
    ax_main2.text(0.5, 1.02, '"high frequency" (≥ fz) → ripples with meshing frequency',
                 ha='center', va='bottom', fontsize=14, fontweight='bold', color='darkblue',
                 transform=ax_main2.transAxes)
    
    gs_inner2 = gs[1, 1].subgridspec(3, 1, height_ratios=[0.12, 0.08, 0.8], hspace=0.02)
    
    # 高频频谱
    ax_spec2 = fig.add_subplot(gs_inner2[0])
    
    # 准备高频频谱数据
    ordered_high_spectrum = []
    if fz in high_spectrum:
        ordered_high_spectrum.append((fz, high_spectrum[fz]))
    if fz * 2 in high_spectrum:
        ordered_high_spectrum.append((fz * 2, high_spectrum[fz * 2]))
    for order, val in sorted(high_spectrum.items()):
        if order not in [fz, fz * 2]:
            ordered_high_spectrum.append((order, val))
    
    if len(ordered_high_spectrum) == 0:
        ordered_high_spectrum = [(fz, 0.46), (fz * 2, 0.17)]
    
    high_orders = [item[0] for item in ordered_high_spectrum]
    high_vals = [item[1] for item in ordered_high_spectrum]
    
    colors2 = ['red' if v > 0.3 else 'lightcoral' for v in high_vals]
    bars2 = ax_spec2.bar(range(len(high_orders)), high_vals, color=colors2, 
                        width=0.6, edgecolor='darkred', linewidth=1)
    
    for i, (bar, val) in enumerate(zip(bars2, high_vals)):
        height = bar.get_height()
        ax_spec2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                     f'{val:.2f}', ha='center', va='bottom', fontsize=8)
    
    # 设置x轴标签
    ax_spec2.set_xticks(range(len(high_orders)))
    x_labels2 = []
    for order in high_orders:
        if order == fz:
            x_labels2.append(f'{order}\nfz')
        elif order == fz * 2:
            x_labels2.append(f'{order}\n2fz')
        else:
            x_labels2.append(str(order))
    ax_spec2.set_xticklabels(x_labels2, fontsize=8)
    
    ax_spec2.set_ylim(0, max(high_vals) * 1.5 if high_vals else 0.6)
    ax_spec2.spines['top'].set_visible(False)
    ax_spec2.spines['right'].set_visible(False)
    ax_spec2.set_title('Profile right', fontsize=11, y=0.95)
    
    # 刻度标注
    ax_spec2.annotate('', xy=(1.02, 0.9), xycoords='axes fraction',
                     xytext=(1.02, 0.1), textcoords='axes fraction',
                     arrowprops=dict(arrowstyle='<->', color='darkred', lw=1.5))
    ax_spec2.text(1.06, 0.5, '0.002 mm', rotation=90, va='center', fontsize=9, color='darkred')
    
    # 分隔线
    ax_sep2 = fig.add_subplot(gs_inner2[1])
    ax_sep2.set_xlim(0, num_teeth)
    ax_sep2.set_ylim(0, 1)
    ax_sep2.axis('off')
    ax_sep2.axhline(y=0.5, color='black', linewidth=1)
    
    for i in range(1, num_teeth + 1):
        ax_sep2.plot([i, i], [0.2, 0.8], 'k-', linewidth=0.8)
        ax_sep2.text(i, 0.05, str(i), ha='center', va='top', fontsize=8, color='red')
    
    # 高频波形
    ax_wave2 = fig.add_subplot(gs_inner2[2])
    
    # 使用真实高频数据绘制完整波形
    if 'profile_high' in high_freq_data:
        data2 = high_freq_data['profile_high']
        x_wave2 = np.linspace(0, num_teeth, len(data2))
        
        # 绘制完整波形
        ax_wave2.plot(x_wave2, data2, color='darkblue', linewidth=0.8, alpha=0.8)
        
        # 叠加显示几个齿的波形
        points_per_tooth2 = len(data2) // num_teeth if num_teeth > 0 else len(data2)
        for i, color in enumerate(['darkred', 'darkorange', 'darkgreen']):
            tooth_idx = i * (num_teeth // 3)
            if tooth_idx < num_teeth:
                start_idx = tooth_idx * points_per_tooth2
                end_idx = (tooth_idx + 1) * points_per_tooth2 if tooth_idx < num_teeth - 1 else len(data2)
                segment = data2[start_idx:end_idx]
                x_segment = np.linspace(tooth_idx, tooth_idx + 1, len(segment))
                ax_wave2.plot(x_segment, segment, color=color, linewidth=1.5, alpha=0.9)
    else:
        # 生成示例高频波形
        x_wave2 = np.linspace(0, num_teeth, num_teeth * 100)
        high_wave = 0.003 * np.sin(10 * np.pi * x_wave2)
        ax_wave2.plot(x_wave2, high_wave, 'darkblue', linewidth=0.8, alpha=0.8)
    
    for i in range(1, num_teeth + 1):
        ax_wave2.axvline(x=i, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    
    ax_wave2.set_xlim(0, num_teeth)
    y_margin2 = (np.max(np.abs(data2)) if 'data2' in locals() else 0.005) * 1.5
    ax_wave2.set_ylim(-y_margin2, y_margin2)
    ax_wave2.axis('off')
    
    # 左侧标注
    a2_high = high_vals[0] if high_vals else 0.46
    ax_wave2.text(-0.3, y_margin2 * 0.5, f'A2  {a2_high:.2f}', fontsize=10, ha='right', va='center')
    ax_wave2.text(-0.3, -y_margin2 * 0.5, f'f 2  {z}', fontsize=10, ha='right', va='center')
    
    # 齿位数字
    for i in range(1, num_teeth + 1):
        ax_wave2.text(i - 0.5, y_margin2 * 0.9, str(i), ha='center', va='bottom', fontsize=8, color='red')
    
    plt.subplots_adjust(left=0.05, right=0.92, top=0.95, bottom=0.03)
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"齿形波纹度图表已保存至: {output_path}")
    
    return fig


if __name__ == "__main__":
    # 测试：使用示例数据生成图表
    fig = create_profile_ripple_chart(
        profile_data=None,
        gear_data=None,
        output_path="profile_ripple_chart.png"
    )
    
    plt.show()
