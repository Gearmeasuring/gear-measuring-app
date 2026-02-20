"""
旋转角度波纹频谱分析图表
显示齿形和齿向的频谱分析结果
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def create_rotation_angle_spectrum_chart(flank_data=None, profile_data=None, gear_data=None, output_path=None):
    """
    创建旋转角度波纹频谱分析图表
    
    参数:
        flank_data: 齿面数据字典（齿向）
        profile_data: 齿形数据字典
        gear_data: 齿轮参数字典
        output_path: 输出文件路径
    
    返回:
        fig: matplotlib图表对象
    """
    # 获取齿轮参数
    z = 33  # 默认齿数
    if gear_data and isinstance(gear_data, dict):
        z = gear_data.get('齿数', gear_data.get('teeth', 33))
    
    # 创建图形
    fig = plt.figure(figsize=(18, 10))
    
    # 提取真实数据（不再使用模拟数据）
    data = extract_real_data(flank_data, profile_data, z)
    
    # 创建4个子图
    gs = fig.add_gridspec(4, 1, hspace=0.1, left=0.08, right=0.92, top=0.92, bottom=0.08)
    
    # 第1行：Profile & pitch right
    ax1 = fig.add_subplot(gs[0])
    plot_spectrum_row(ax1, data['profile_right'], z, 'Profile & pitch right', show_xlabel=False)
    
    # 第2行：Profile & pitch left
    ax2 = fig.add_subplot(gs[1])
    plot_spectrum_row(ax2, data['profile_left'], z, 'Profile & pitch left', show_xlabel=False)
    
    # 第3行：Helix & pitch right
    ax3 = fig.add_subplot(gs[2])
    plot_spectrum_row(ax3, data['helix_right'], z, 'Helix & pitch right', show_xlabel=False, show_2fz=True)
    
    # 第4行：Helix & pitch left
    ax4 = fig.add_subplot(gs[3])
    plot_spectrum_row(ax4, data['helix_left'], z, 'Helix & pitch left', show_xlabel=True, show_2fz=True)
    
    # 添加总标题
    fig.suptitle('Ripple above the rotation angle', fontsize=16, fontweight='bold', y=0.96)
    
    # 添加齿数标记
    fig.text(0.02, 0.96, f'z = {z}', fontsize=12, color='gray')
    
    # 添加比例尺（在右下角）
    add_scale_bar(fig)
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"旋转角度波纹频谱分析图表已保存至: {output_path}")
    
    return fig


def generate_sample_data(z=33):
    """生成示例频谱数据"""
    np.random.seed(42)
    
    # 生成低频谐波数据 (1-5次)
    def generate_low_freq():
        # 递减的振幅
        amps = [10.0, 5.0, 3.0, 2.0, 1.0]
        return amps
    
    # 生成fz和2fz数据
    def generate_high_freq():
        return {'fz': 2.0, '2fz': 1.0}
    
    data = {
        'profile_right': {
            'low_freq': generate_low_freq(),
            'high_freq': {'fz': 1.5}
        },
        'profile_left': {
            'low_freq': generate_low_freq(),
            'high_freq': {'fz': 1.8}
        },
        'helix_right': {
            'low_freq': generate_low_freq(),
            'high_freq': generate_high_freq()
        },
        'helix_left': {
            'low_freq': generate_low_freq(),
            'high_freq': generate_high_freq()
        }
    }
    
    return data


def extract_real_data(flank_data, profile_data, z):
    """从真实数据中提取频谱"""
    data = {}
    
    # 处理齿形数据 (Profil)
    for side in ['right', 'left']:
        key = f'profile_{side}'
        if profile_data and side in profile_data and profile_data[side]:
            side_data = profile_data[side]
            # 计算FFT获取频谱
            spectrum = calculate_spectrum_from_mka_data(side_data, z)
            data[key] = spectrum
        else:
            # 如果没有数据，使用空频谱
            data[key] = {'low_freq': [0.0, 0.0, 0.0, 0.0, 0.0], 'high_freq': {'fz': 0.0, '2fz': 0.0}}
    
    # 处理齿向数据 (Flankenlinie/Helix)
    for side in ['right', 'left']:
        key = f'helix_{side}'
        if flank_data and side in flank_data and flank_data[side]:
            side_data = flank_data[side]
            spectrum = calculate_spectrum_from_mka_data(side_data, z)
            data[key] = spectrum
        else:
            # 如果没有数据，使用空频谱
            data[key] = {'low_freq': [0.0, 0.0, 0.0, 0.0, 0.0], 'high_freq': {'fz': 0.0, '2fz': 0.0}}
    
    return data


def calculate_spectrum_from_mka_data(side_data, z):
    """
    从MKA数据计算频谱
    
    MKA数据结构:
    side_data = {
        tooth_id_1: [value1, value2, value3, ...],  # 480或915个点的列表
        tooth_id_2: [value1, value2, value3, ...],
        ...
    }
    """
    # 提取所有齿的数据 - 使用每个齿的波形数据的标准差
    tooth_values = []
    
    for tooth_id in range(1, z + 1):
        if tooth_id in side_data:
            wave_data = side_data[tooth_id]
            if isinstance(wave_data, (list, np.ndarray)):
                # 计算该齿波形数据的标准差作为代表性数值
                tooth_values.append(np.std(wave_data))
            else:
                tooth_values.append(0.0)
        else:
            # 如果该齿没有数据，使用0或插值
            tooth_values.append(0.0)
    
    tooth_values = np.array(tooth_values)
    
    # 如果所有值都是0，返回空频谱
    if np.all(tooth_values == 0):
        return {
            'low_freq': [0.0, 0.0, 0.0, 0.0, 0.0],
            'high_freq': {'fz': 0.0, '2fz': 0.0}
        }
    
    # 计算FFT
    fft_vals = np.fft.fft(tooth_values)
    fft_amps = np.abs(fft_vals) / len(tooth_values) * 2
    
    # 提取低频成分 (1-5次谐波)
    low_freq = []
    for i in range(1, 6):
        if i < len(fft_amps):
            low_freq.append(fft_amps[i])
        else:
            low_freq.append(0.0)
    
    # 提取fz和2fz (对应FFT的第1和第2个频率成分)
    high_freq = {
        'fz': fft_amps[1] if 1 < len(fft_amps) else 0.0,
        '2fz': fft_amps[2] if 2 < len(fft_amps) else 0.0
    }
    
    return {
        'low_freq': low_freq,
        'high_freq': high_freq
    }


def plot_spectrum_row(ax, data, z, title, show_xlabel=False, show_2fz=False):
    """
    绘制单行频谱图
    
    参数:
        ax: 坐标轴
        data: 频谱数据
        z: 齿数
        title: 标题
        show_xlabel: 是否显示x轴标签
        show_2fz: 是否显示2fz
    """
    # 清空坐标轴
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 15)
    ax.axis('off')
    
    # 获取数据
    low_freq = data['low_freq']
    high_freq = data['high_freq']
    
    # 绘制标题（右侧）
    ax.text(60, 12, title, fontsize=11, ha='center', va='center')
    
    # === 左侧：低频谐波 (1-5次) ===
    bar_width = 3
    bar_spacing = 5
    start_x = 5
    
    for i, amp in enumerate(low_freq[:5]):
        x = start_x + i * (bar_width + bar_spacing)
        height = min(amp * 1.5, 12)  # 缩放并限制高度
        
        # 绘制频谱条
        rect = Rectangle((x, 2), bar_width, height, 
                        facecolor='red', edgecolor='darkred', linewidth=0.5)
        ax.add_patch(rect)
        
        # 添加频率标签
        ax.text(x + bar_width/2, 0.5, str(i+1), fontsize=9, ha='center', va='top')
    
    # 添加frequency标签（只在最后一行）
    if show_xlabel:
        ax.text(start_x + 20, -2, 'frequency', fontsize=10, ha='center', va='top')
    
    # === 中间：fz频率 ===
    fz_x = 40
    fz_height = min(high_freq.get('fz', 0) * 1.5, 12)
    
    rect = Rectangle((fz_x - 1.5, 2), 3, fz_height,
                    facecolor='red', edgecolor='darkred', linewidth=0.5)
    ax.add_patch(rect)
    
    # fz标签
    ax.text(fz_x, 0.5, 'fz', fontsize=9, ha='center', va='top')
    
    # === 右侧：2fz频率（仅齿向数据）===
    if show_2fz:
        f2z_x = 75
        f2z_height = min(high_freq.get('2fz', 0) * 1.5, 12)
        
        rect = Rectangle((f2z_x - 1.5, 2), 3, f2z_height,
                        facecolor='red', edgecolor='darkred', linewidth=0.5)
        ax.add_patch(rect)
        
        # 2fz标签
        ax.text(f2z_x, 0.5, '2fz', fontsize=9, ha='center', va='top')
    
    # 绘制基线
    ax.plot([0, 95], [2, 2], 'k-', linewidth=1)


def add_scale_bar(fig):
    """添加比例尺"""
    # 在右下角添加比例尺
    ax_scale = fig.add_axes([0.88, 0.05, 0.08, 0.05])
    ax_scale.set_xlim(0, 1)
    ax_scale.set_ylim(0, 1)
    ax_scale.axis('off')
    
    # 绘制双向箭头
    ax_scale.annotate('', xy=(0.3, 0.5), xytext=(0.1, 0.5),
                     arrowprops=dict(arrowstyle='<->', color='red', lw=2))
    
    # 比例尺数值
    ax_scale.text(0.6, 0.5, '0.002 mm', fontsize=10, ha='left', va='center', color='red')


if __name__ == "__main__":
    # 测试：使用示例数据生成图表
    fig = create_rotation_angle_spectrum_chart(
        flank_data=None,
        profile_data=None,
        gear_data={'齿数': 33},
        output_path='rotation_angle_spectrum_chart.png'
    )
    plt.show()
