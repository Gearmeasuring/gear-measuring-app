"""
旋转角度波纹分析图表
显示不同频率成分的波纹：
- A1 (f1=1): 偏心引起的低频波纹
- A2 (f2=4): 机床刀具或方坯振动引起的中频波纹  
- A3 (f3=z): 机床噪声振动引起的高频波纹
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import signal


def create_rotation_angle_ripple_chart(flank_data=None, gear_data=None, output_path=None):
    """
    创建旋转角度波纹分析图表
    
    参数:
        flank_data: 齿面数据字典
        gear_data: 齿轮参数字典
        output_path: 输出文件路径
    
    返回:
        fig: matplotlib图表对象
    """
    # 获取齿轮参数
    z = 26  # 默认齿数
    if gear_data and isinstance(gear_data, dict):
        z = gear_data.get('齿数', gear_data.get('teeth', 26))
    
    # 创建图形 - 使用更宽的布局
    fig = plt.figure(figsize=(16, 10))
    
    # 创建主布局 - 左侧标签区 + 右侧图表区
    # 使用gridspec创建3行，每行包含标签和波形图
    outer_gs = fig.add_gridspec(3, 1, hspace=0.15, left=0.08, right=0.88, top=0.92, bottom=0.08)
    
    # 生成示例数据（如果没有真实数据）
    if flank_data is None:
        raw_data, x_teeth = generate_sample_data(z)
    else:
        raw_data, x_teeth = extract_tooth_data(flank_data, z)
    
    # 计算三个频率成分
    # A1: f=1 (偏心)
    wave1, amp1 = extract_frequency_component(raw_data, 1, z)
    # A2: f=4 (机床振动)
    wave2, amp2 = extract_frequency_component(raw_data, 4, z)
    # A3: f=z (噪声)
    wave3, amp3 = extract_frequency_component(raw_data, z, z)
    
    # === 绘制三个子图 ===
    
    # A1: 偏心
    ax1 = fig.add_subplot(outer_gs[0])
    plot_ripple_row(fig, ax1, x_teeth, raw_data, wave1, amp1, z,
                    'A1', 1, 'eccentric', color='darkblue')
    
    # A2: 机床振动
    ax2 = fig.add_subplot(outer_gs[1])
    plot_ripple_row(fig, ax2, x_teeth, raw_data, wave2, amp2, z,
                    'A2', 4, 'vibration of machine tool\nor square blank', color='darkgreen')
    
    # A3: 噪声
    ax3 = fig.add_subplot(outer_gs[2])
    plot_ripple_row(fig, ax3, x_teeth, raw_data, wave3, amp3, z,
                    'A3', z, 'noise generating vibration\nof machine tool', color='darkred')
    
    # 添加总标题
    fig.suptitle(f'Ripple above the rotation angle\nProfile & pitch left    z = {z}', 
                 fontsize=14, fontweight='bold', y=0.96)
    
    # 添加顶部刻度标记
    fig.text(0.09, 0.905, '0', fontsize=10, ha='center')
    fig.text(0.87, 0.905, '2π', fontsize=10, ha='center')
    
    # 添加比例尺（在右侧）
    add_scale_indicator(fig, 0.005)
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"旋转角度波纹分析图表已保存至: {output_path}")
    
    return fig


def generate_sample_data(z=26):
    """生成示例数据 - 模拟真实齿轮波纹"""
    np.random.seed(42)
    
    # 生成齿位
    x_teeth = np.arange(1, z + 1)
    
    # 生成基础波纹数据（包含各种频率成分）
    raw_data = np.zeros(z)
    
    # 添加偏心成分 (1次谐波)
    eccentric = 0.008 * np.sin(2 * np.pi * x_teeth / z)
    
    # 添加机床振动成分 (4次谐波)
    vibration = 0.003 * np.sin(8 * np.pi * x_teeth / z)
    
    # 添加噪声成分 (z次谐波)
    noise = 0.001 * np.sin(2 * np.pi * x_teeth)
    
    # 添加随机噪声
    random_noise = np.random.normal(0, 0.0005, z)
    
    raw_data = eccentric + vibration + noise + random_noise
    
    return raw_data, x_teeth


def extract_tooth_data(flank_data, z):
    """从齿面数据中提取每个齿的代表性数值"""
    x_teeth = np.arange(1, z + 1)
    raw_data = np.zeros(z)
    
    # 优先使用左齿面数据
    side_data = flank_data.get('left', flank_data.get('right', {}))
    
    for i in range(z):
        tooth_id = i + 1
        if tooth_id in side_data:
            tooth_info = side_data[tooth_id]
            if isinstance(tooth_info, dict):
                if 'waveform' in tooth_info:
                    # 使用波形数据的标准差作为代表性数值
                    raw_data[i] = np.std(tooth_info['waveform'])
                elif 'y' in tooth_info:
                    raw_data[i] = np.std(tooth_info['y'])
                else:
                    raw_data[i] = 0.002
            elif isinstance(tooth_info, (list, np.ndarray)):
                raw_data[i] = np.std(tooth_info)
            else:
                raw_data[i] = 0.002
        else:
            # 生成模拟数据
            raw_data[i] = 0.002 + np.random.normal(0, 0.001)
    
    return raw_data, x_teeth


def extract_frequency_component(raw_data, freq_order, z):
    """
    提取特定频率成分
    
    参数:
        raw_data: 原始数据数组
        freq_order: 频率阶数
        z: 齿数
    
    返回:
        wave: 提取的频率波形
        amplitude: 振幅
    """
    # 使用FFT提取特定频率
    fft_vals = np.fft.fft(raw_data)
    n = len(raw_data)
    
    # 创建只包含目标频率的频谱
    filtered_fft = np.zeros_like(fft_vals)
    
    # 包含目标频率及其附近的一些频率（用于平滑）
    if freq_order == 1:
        # 低频：偏心，只取基频
        idx = 1
        if idx < len(fft_vals):
            filtered_fft[idx] = fft_vals[idx]
            filtered_fft[-idx] = fft_vals[-idx]
    elif freq_order == 4:
        # 中频：机床振动
        idx = 4
        if idx < len(fft_vals):
            filtered_fft[idx] = fft_vals[idx]
            filtered_fft[-idx] = fft_vals[-idx]
    else:
        # 高频：噪声，取高频区域
        idx = min(freq_order, n // 2 - 1)
        if idx < len(fft_vals):
            filtered_fft[idx] = fft_vals[idx]
            filtered_fft[-idx] = fft_vals[-idx]
    
    # 逆FFT得到时域波形
    wave = np.real(np.fft.ifft(filtered_fft))
    
    # 计算振幅
    amplitude = np.max(np.abs(wave))
    
    return wave, amplitude


def plot_ripple_row(fig, ax, x_teeth, raw_data, wave, amplitude, z,
                    label_a, freq_order, description, color='blue'):
    """
    绘制单行波纹图
    
    参数:
        fig: 图形对象
        ax: 坐标轴
        x_teeth: 齿位数组
        raw_data: 原始数据
        wave: 提取的波形
        amplitude: 振幅
        z: 齿数
        label_a: A1/A2/A3标签
        freq_order: 频率阶数
        description: 描述文字
        color: 波形颜色
    """
    # 插值以获得更平滑的曲线
    x_fine = np.linspace(1, z, 500)
    raw_fine = np.interp(x_fine, x_teeth, raw_data)
    wave_fine = np.interp(x_fine, x_teeth, wave)
    
    # 绘制原始数据（红色细线）
    ax.plot(x_fine, raw_fine, 'r-', linewidth=0.8, alpha=0.7)
    
    # 绘制提取的波形（彩色粗线）
    ax.plot(x_fine, wave_fine, color=color, linewidth=2)
    
    # 设置y轴范围 - 根据数据自动调整
    y_max = max(np.max(np.abs(raw_data)), np.max(np.abs(wave))) * 1.5
    y_min = -y_max
    ax.set_ylim(y_min, y_max)
    ax.set_xlim(0.5, z + 0.5)
    
    # 隐藏默认的y轴刻度
    ax.set_yticks([])
    
    # 添加左侧标签
    # A1/A2/A3 标签
    ax.text(-0.08, 0.5, label_a, transform=ax.transAxes, 
            fontsize=12, fontweight='bold', ha='center', va='center')
    
    # 振幅值
    ax.text(-0.08, 0.75, f'{amplitude*1000:.2f}', transform=ax.transAxes,
            fontsize=10, ha='center', va='center')
    
    # 频率标签 f1, f2, f4 等
    freq_label = f'f{freq_order}' if freq_order <= 4 else f'f{freq_order}'
    ax.text(-0.08, 0.25, freq_label, transform=ax.transAxes,
            fontsize=10, ha='center', va='center')
    
    # 描述文字（在图表下方）
    ax.text(-0.08, -0.15, description, transform=ax.transAxes,
            fontsize=9, ha='center', va='top', color=color, fontweight='bold')
    
    # 添加齿位刻度（在图表内部底部）
    for i in range(1, z + 1, 2):  # 每隔一个显示
        ax.text(i, y_min * 0.7, str(i), ha='center', va='top', 
                fontsize=8, color='gray')
    
    # 移除边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)


def add_scale_indicator(fig, scale_value):
    """在右侧添加比例尺"""
    # 创建比例尺区域
    ax_scale = fig.add_axes([0.89, 0.35, 0.02, 0.2])
    ax_scale.set_xlim(0, 1)
    ax_scale.set_ylim(0, 1)
    ax_scale.axis('off')
    
    # 绘制双向箭头
    ax_scale.annotate('', xy=(0.5, 0.9), xytext=(0.5, 0.1),
                     arrowprops=dict(arrowstyle='<->', color='red', lw=1.5))
    
    # 添加比例尺文字
    ax_scale.text(0.7, 0.5, f'{scale_value*1000:.3f} mm', 
                 fontsize=9, ha='left', va='center', color='red')


if __name__ == "__main__":
    # 测试：使用示例数据生成图表
    fig = create_rotation_angle_ripple_chart(
        flank_data=None,
        gear_data={'齿数': 26},
        output_path='rotation_angle_ripple_chart.png'
    )
    plt.show()
