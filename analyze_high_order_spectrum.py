"""
分析大于等于87的阶次（高阶）的频谱特性
Analyzes spectrum characteristics of orders greater than or equal to 87 (high orders)
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser
from klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport


def analyze_high_order_spectrum():
    """
    分析大于等于87的阶次（高阶）的频谱特性
    先分解阶次最大的正弦波，从原始信号中移除，计算频谱
    然后对剩余信号重复上述过程，直到提取出第十个较大的阶次
    """
    # 读取MKA文件数据
    mka_file = '263751-018-WAV.mka'
    parser = MKAParser(mka_file)
    
    # 获取旋转图表数据
    combined_data = parser.get_combined_data(use_evaluation_range=True)
    
    # 提取所有四个曲线的数据
    datasets = {
        'Left Profile': {'angles': [], 'values': []},
        'Right Profile': {'angles': [], 'values': []},
        'Left Flank': {'angles': [], 'values': []},
        'Right Flank': {'angles': [], 'values': []}
    }
    
    # 从combined_data中提取数据
    if 'profile_left' in combined_data:
        for angle, value in combined_data['profile_left']:
            datasets['Left Profile']['angles'].append(angle)
            datasets['Left Profile']['values'].append(value)
    
    if 'profile_right' in combined_data:
        for angle, value in combined_data['profile_right']:
            datasets['Right Profile']['angles'].append(angle)
            datasets['Right Profile']['values'].append(value)
    
    if 'flank_left' in combined_data:
        for angle, value in combined_data['flank_left']:
            datasets['Left Flank']['angles'].append(angle)
            datasets['Left Flank']['values'].append(value)
    
    if 'flank_right' in combined_data:
        for angle, value in combined_data['flank_right']:
            datasets['Right Flank']['angles'].append(angle)
            datasets['Right Flank']['values'].append(value)
    
    # 创建频谱分析器
    analyzer = KlingelnbergRippleSpectrumReport()
    
    # 创建PDF报告
    output_pdf = 'high_order_spectrum_analysis_min87_v5.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4尺寸
        fig.suptitle('High Order Spectrum Analysis (≥87)', fontsize=16, fontweight='bold')
        
        # 创建子图
        gs = fig.add_gridspec(8, 1, height_ratios=[1, 1, 1, 1, 1, 1, 1, 1])
        
        colors = ['blue', 'red', 'green', 'magenta']
        
        for i, (title, dataset) in enumerate(datasets.items()):
            angles = dataset['angles']
            data = dataset['values']
            if len(data) > 0:
                ax = fig.add_subplot(gs[i*2])
                ax.set_title(f'{title} - Processed Data', fontsize=12, fontweight='bold')
                
                # 预处理数据，移除起始不稳定部分并平滑
                data_array = np.array(data)
                processed_data = analyzer._preprocess_data(data_array)
                
                # 对角度数据进行相应的处理，保持长度一致
                # 计算移除的点数（与预处理中相同的逻辑）
                remove_points = max(1, int(len(data_array) * 0.01))
                if len(data_array) > remove_points:
                    processed_angles = angles[remove_points:]
                else:
                    processed_angles = angles
                
                # 确保角度和值的长度一致
                min_length = min(len(processed_angles), len(processed_data))
                processed_angles = processed_angles[:min_length]
                processed_data = processed_data[:min_length]
                
                # 过滤异常值
                # 计算数据的均值和标准差
                mean_data = np.mean(processed_data)
                std_data = np.std(processed_data)
                threshold = 3 * std_data
                
                # 过滤掉超出阈值的数据点
                filtered_angles = []
                filtered_data = []
                for angle, value in zip(processed_angles, processed_data):
                    if abs(value - mean_data) <= threshold:
                        filtered_angles.append(angle)
                        filtered_data.append(value)
                
                # 如果过滤后的数据太少，使用原始数据
                if len(filtered_angles) < len(processed_angles) * 0.9:
                    filtered_angles = processed_angles
                    filtered_data = processed_data
                
                # 按角度排序，确保数据点按正确的顺序绘制
                sorted_indices = np.argsort(filtered_angles)
                sorted_angles = np.array(filtered_angles)[sorted_indices]
                sorted_data = np.array(filtered_data)[sorted_indices]
                
                # 归一化角度到0-1范围，保持相对比例
                if len(sorted_angles) > 0:
                    min_angle = min(sorted_angles)
                    max_angle = max(sorted_angles)
                    angle_range = max_angle - min_angle
                    if angle_range > 0:
                        normalized_angles = [(angle - min_angle) / angle_range for angle in sorted_angles]
                    else:
                        normalized_angles = np.linspace(0, 1, len(sorted_data))
                else:
                    normalized_angles = np.linspace(0, 1, len(sorted_data))
                
                # 绘制预处理后的数据，使用排序后的角度作为x轴
                ax.plot(normalized_angles, sorted_data, label='Processed Data', color=colors[i], alpha=0.7, linewidth=0.8)
                ax.set_xlabel('Normalized Rotation Position', fontsize=8)
                ax.set_ylabel('Deviation (μm)', fontsize=8)
                ax.tick_params(axis='both', labelsize=8)
                ax.grid(True, alpha=0.3, linestyle='--')
                
                # 计算频谱，只分析大于等于87的阶
                spectrum = analyzer._calculate_ripple_spectrum(np.array(data), max_harmonics=10, min_order=87, max_order=100)
                
                # 绘制频谱分析结果
                ax2 = fig.add_subplot(gs[i*2 + 1])
                ax2.set_title(f'{title} - Spectrum Analysis (≥87)', fontsize=12, fontweight='bold')
                
                # 准备频谱数据
                orders = [item['order'] for item in spectrum[:10]]
                amplitudes = [item['amplitude'] for item in spectrum[:10]]
                
                # 绘制频谱柱状图
                x_positions = np.arange(len(orders))
                ax2.bar(x_positions, amplitudes, color=colors[i], alpha=0.7)
                
                # 设置X轴标签（阶次）
                ax2.set_xticks(x_positions)
                ax2.set_xticklabels([str(int(order)) for order in orders], fontsize=8)
                
                # 添加振幅值标签
                max_amp = max(amplitudes) * 1.2 if amplitudes else 0.2
                for j, amp in enumerate(amplitudes):
                    if amp > 0:
                        ax2.text(j, amp + max_amp * 0.05, f'{amp:.2f}', 
                                ha='center', va='bottom', fontsize=7)
                
                # 设置标签
                ax2.set_xlabel('Order', fontsize=8)
                ax2.set_ylabel('Amplitude (μm)', fontsize=8)
                ax2.tick_params(axis='both', labelsize=8)
                ax2.grid(True, alpha=0.3, linestyle='--')
                
                # 隐藏右侧和顶部边框
                ax.spines['right'].set_visible(False)
                ax.spines['top'].set_visible(False)
                ax2.spines['right'].set_visible(False)
                ax2.spines['top'].set_visible(False)
            else:
                ax = fig.add_subplot(gs[i*2])
                ax.set_title(f'{title} - Original Data', fontsize=12, fontweight='bold')
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                
                ax2 = fig.add_subplot(gs[i*2 + 1])
                ax2.set_title(f'{title} - Spectrum Analysis (≥87)', fontsize=12, fontweight='bold')
                ax2.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax2.transAxes)
        
        # 添加分析总结
        summary_text = "High Order Spectrum Analysis Summary (≥87):\n"
        summary_text += "- Iterative sine wave fitting algorithm\n"
        summary_text += "- Extracts largest order sine waves first\n"
        summary_text += "- Removes extracted sine waves from original signal\n"
        summary_text += "- Repeats process for residual signal\n"
        summary_text += "- Extracts up to 10 largest orders\n"
        summary_text += "- Results sorted by amplitude\n"
        summary_text += "- Only analyzing orders ≥87"
        
        fig.text(0.5, 0.02, summary_text, ha='center', fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"High order spectrum analysis completed. Results saved to: {output_pdf}")
    
    # 打印频谱分析结果
    print("\nHigh Order Spectrum Analysis Results (≥87):")
    print("Dataset | Order | Amplitude")
    print("------------------------")
    
    for title, dataset in datasets.items():
        data = dataset['values']
        if len(data) > 0:
            spectrum = analyzer._calculate_ripple_spectrum(np.array(data), max_harmonics=10, min_order=87, max_order=100)
            print(f"\n{title}:")
            for item in spectrum[:10]:
                print(f"{item['order']:6} | {item['amplitude']:9.2f}")
        else:
            print(f"\n{title}: No data")
    
    # 分析87阶附近的成分（高阶）
    print("\n=== 87阶附近频谱分析（高阶）===")
    print("Dataset | Order | Amplitude")
    print("------------------------")
    
    for title, dataset in datasets.items():
        data = dataset['values']
        if len(data) > 0:
            target_spectrum = analyzer.analyze_target_order(np.array(data), target_order=87, order_range=5, min_order=87, max_order=100)
            print(f"\n{title}:")
            if target_spectrum:
                for item in target_spectrum:
                    print(f"{item['order']:6} | {item['amplitude']:9.2f}")
            else:
                print("  No components found near order 87 (≥87阶)")
        else:
            print(f"\n{title}: No data")


if __name__ == '__main__':
    analyze_high_order_spectrum()
