"""
考虑螺距的轮廓测量序列图（图9）
展示空载啮合时齿侧沿齿根平行直线的接触情况
将所有轮廓测量数据按旋转角度排列后形成连续曲线
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.interpolate import UnivariateSpline


def create_contact_pattern_chart(profile_data=None, pitch_data=None, gear_data=None, output_path=None):
    """
    创建考虑螺距的轮廓测量序列图（展开式轮廓偏差曲线）
    
    参数:
        profile_data: 齿形测量数据 {'left': {tooth_id: [480个点]}, 'right': {...}}
        pitch_data: 节距测量数据 {'left': {tooth_id: {'fp': x, 'Fp': y, 'Fr': z}}, 'right': {...}}
        gear_data: 齿轮基本参数 {'teeth': 齿数, 'module': 模数, ...}
        output_path: 输出文件路径
    
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
    
    # 创建图形 - 2行布局
    fig = plt.figure(figsize=(16, 10))
    fig.subplots_adjust(left=0.08, right=0.92, top=0.90, bottom=0.10, hspace=0.30)
    
    # ========== 第1行：左齿面展开轮廓曲线 ==========
    ax1 = fig.add_subplot(2, 1, 1)
    left_profile = profile_data.get('left', {}) if profile_data else {}
    left_pitch = pitch_data.get('left', {}) if pitch_data else {}
    plot_unfolded_profile(ax1, left_profile, left_pitch, z, '左齿面 - 考虑螺距的轮廓测量序列', gear_data)
    
    # ========== 第2行：右齿面展开轮廓曲线 ==========
    ax2 = fig.add_subplot(2, 1, 2)
    right_profile = profile_data.get('right', {}) if profile_data else {}
    right_pitch = pitch_data.get('right', {}) if pitch_data else {}
    plot_unfolded_profile(ax2, right_profile, right_pitch, z, '右齿面 - 考虑螺距的轮廓测量序列', gear_data)
    
    # 添加总标题
    fig.suptitle(f'考虑螺距的轮廓测量序列 (齿数 z={z}, 模数 m={module})', 
                 fontsize=14, fontweight='bold', y=0.98)
    
    # 保存或返回
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"图表已保存到: {output_path}")
    
    return fig


def plot_unfolded_profile(ax, profile_data, pitch_data, z, title, gear_data):
    """
    绘制展开式轮廓偏差曲线
    
    原理：
    - 将每个齿的轮廓测量数据（480个点）按顺序连接
    - 考虑节距误差，调整每个齿的位置
    - 形成连续的展开曲线，显示整体波纹形态
    """
    
    ax.set_facecolor('#fafafa')
    
    if not profile_data or len(profile_data) == 0:
        ax.text(0.5, 0.5, '无数据', ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        return
    
    # 获取所有齿号并排序
    tooth_ids = sorted([tid for tid in profile_data.keys() if isinstance(tid, int)])
    
    if len(tooth_ids) == 0:
        ax.text(0.5, 0.5, '无有效数据', ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        return
    
    # 准备数据
    all_x = []  # 展开后的X坐标（齿号 + 点位置）
    all_y = []  # 偏差值
    tooth_boundaries = []  # 齿边界位置
    
    points_per_tooth = 480  # 每个齿的测量点数
    
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
                pitch_adjustment = pitch_info.get('fp', 0) / 1000.0  # 转换为mm或保持μm
        
        # 计算该齿的X坐标范围
        # 基础位置：齿号 - 1（0起始）
        base_position = tooth_id - 1
        
        # 添加节距误差调整
        adjusted_position = base_position + pitch_adjustment / 10.0  # 缩放调整量
        
        # 生成该齿的X坐标（在齿内均匀分布）
        n_points = min(len(values), points_per_tooth)
        x_local = np.linspace(0, 1, n_points)  # 0到1表示齿内位置
        x_global = adjusted_position + x_local  # 全局位置
        
        all_x.extend(x_global)
        all_y.extend(values[:n_points])
        
        # 记录齿边界
        tooth_boundaries.append(adjusted_position)
    
    if len(all_x) == 0:
        ax.text(0.5, 0.5, '无有效数据', ha='center', va='center', transform=ax.transAxes, fontsize=14)
        ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
        return
    
    # 转换为numpy数组
    all_x = np.array(all_x)
    all_y = np.array(all_y)
    
    # 绘制原始数据（红色细线，类似参考图中的锯齿线）
    ax.plot(all_x, all_y, 'r-', linewidth=0.8, alpha=0.7, label='轮廓偏差')
    
    # 计算平滑曲线（蓝色粗线，类似参考图中的平滑曲线）
    # 使用Savitzky-Golay滤波器进行平滑
    if len(all_y) > 51:
        try:
            # 使用较小的窗口进行平滑，保留趋势
            window_size = min(51, len(all_y) // 10 * 2 + 1)  # 确保窗口大小合适
            if window_size >= 5:
                y_smooth = savgol_filter(all_y, window_size, 3)
                ax.plot(all_x, y_smooth, 'b-', linewidth=2, alpha=0.8, label='趋势曲线')
        except Exception as e:
            print(f"平滑处理失败: {e}")
    
    # 添加齿边界标记
    for boundary in tooth_boundaries:
        ax.axvline(x=boundary, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
    
    # 添加零线
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)
    
    # 设置坐标轴
    ax.set_xlabel('齿号 / 旋转角度', fontsize=10)
    ax.set_ylabel('偏差 (μm)', fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold', pad=8)
    
    # 设置X轴刻度
    x_ticks = list(range(0, z + 1, max(1, z // 10)))
    ax.set_xticks(x_ticks)
    
    # 创建双X轴标签：齿号和旋转角度
    x_labels = [f'{t}\n({t * 360 / z:.0f}°)' for t in x_ticks]
    ax.set_xticklabels(x_labels, fontsize=8)
    
    # 设置Y轴范围（对称）
    y_max = max(abs(np.min(all_y)), abs(np.max(all_y))) if len(all_y) > 0 else 10
    y_limit = max(y_max * 1.1, 5)
    ax.set_ylim(-y_limit, y_limit)
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # 添加图例
    ax.legend(loc='upper right', fontsize=9)
    
    # 添加说明文字
    ax.text(0.02, 0.98, 
            f'测量齿数: {len(tooth_boundaries)} / {z}\n'
            f'每齿点数: {points_per_tooth}',
            transform=ax.transAxes, fontsize=8, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))


# 测试函数
if __name__ == '__main__':
    # 创建测试数据
    z = 87  # 齿数（87齿齿轮）
    
    # 模拟齿形数据（480个点 per tooth）
    test_profile_left = {}
    test_profile_right = {}
    
    np.random.seed(42)
    
    # 生成模拟的展开曲线数据
    for tooth_id in range(1, z + 1):
        # 基础波形（模拟齿轮的周期性误差）
        t = np.linspace(0, 2*np.pi, 480)
        
        # 左齿面 - 添加长周期波纹（模拟图9中的形态）
        # 使用多个正弦波模拟复杂的波纹形态
        base_wave = (
            3 * np.sin(t + tooth_id * 0.2) +  # 基础波纹
            1.5 * np.sin(3*t + tooth_id * 0.1) +  # 高频波纹
            0.5 * np.sin(8*t)  # 更高频的小波纹
        )
        
        # 添加整体趋势（模拟向左倾斜并缩放的效果）
        trend = 2 * np.sin(tooth_id * np.pi / z * 2)  # 长周期趋势
        
        # 添加随机噪声
        noise = np.random.normal(0, 0.3, 480)
        
        test_profile_left[tooth_id] = base_wave + trend + noise
        
        # 右齿面 - 略有不同的波形
        base_wave = (
            2.5 * np.sin(t + tooth_id * 0.15 + 0.5) +
            1.2 * np.sin(3*t + tooth_id * 0.12) +
            0.4 * np.sin(8*t + 1)
        )
        trend = 1.8 * np.sin(tooth_id * np.pi / z * 2 + 0.3)
        noise = np.random.normal(0, 0.25, 480)
        
        test_profile_right[tooth_id] = base_wave + trend + noise
    
    # 模拟节距数据
    test_pitch_left = {}
    test_pitch_right = {}
    
    for tooth_id in range(1, z + 1):
        test_pitch_left[tooth_id] = {
            'fp': np.random.normal(0, 2),
            'Fp': np.random.normal(0, 5),
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
        'helix_angle': 0  # 直齿轮
    }
    
    # 创建图表
    fig = create_contact_pattern_chart(
        profile_data={'left': test_profile_left, 'right': test_profile_right},
        pitch_data={'left': test_pitch_left, 'right': test_pitch_right},
        gear_data=test_gear_data,
        output_path='contact_pattern_test.png'
    )
    
    plt.show()
