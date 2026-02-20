"""
重新实现频谱分析，确保数据处理和绘制正确
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser
from klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport


def rebuild_spectrum_analysis():
    """
    重新实现频谱分析，确保数据处理和绘制正确
    """
    # 读取MKA文件数据
    mka_file = '004-xiaoxiao1.mka'
    parser = MKAParser(mka_file)
    
    # 获取齿轮齿数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 26  # Fallback to 26 if not found
    
    print(f"Gear teeth count: {teeth_count}")
    
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
    output_pdf = 'rebuilt_spectrum_analysis_004-xiaoxiao1_orders_1plus_v2.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(12, 16), dpi=200)  # 增大图表尺寸和分辨率
        fig.suptitle('Detailed Spectrum Analysis: Each Tooth Visible', fontsize=16, fontweight='bold')
        
        # 创建子图
        gs = fig.add_gridspec(4, 2, height_ratios=[1, 1, 1, 1])
        
        colors = ['blue', 'red', 'green', 'magenta']
        
        for i, (title, dataset) in enumerate(datasets.items()):
            angles = np.array(dataset['angles'])
            values = np.array(dataset['values'])
            
            if len(values) > 0:
                # 1. 确保数据按角度排序（重新排序，确保顺序正确）
                sorted_indices = np.argsort(angles)
                sorted_angles = angles[sorted_indices]
                sorted_values = values[sorted_indices]
                
                # 2. 预处理数据
                processed_data = analyzer._preprocess_data(sorted_values)
                
                # 3. 确保处理后的数据长度与角度一致
                min_length = min(len(sorted_angles), len(processed_data))
                sorted_angles = sorted_angles[:min_length]
                processed_data = processed_data[:min_length]
                
                # 4. 归一化角度到0-1范围
                min_angle = np.min(sorted_angles)
                max_angle = np.max(sorted_angles)
                angle_range = max_angle - min_angle
                if angle_range > 0:
                    normalized_angles = (sorted_angles - min_angle) / angle_range
                else:
                    normalized_angles = np.linspace(0, 1, len(processed_data))
                
                # 5. 绘制预处理后的数据
                ax1 = fig.add_subplot(gs[i, 0])
                ax1.set_title(f'{title} - Processed Data', fontsize=12, fontweight='bold')
                ax1.plot(normalized_angles, processed_data, label='Processed Data', color=colors[i], alpha=0.7, linewidth=0.8)
                ax1.set_xlabel('Normalized Rotation Position', fontsize=8)
                ax1.set_ylabel('Deviation (μm)', fontsize=8)
                ax1.tick_params(axis='both', labelsize=8)
                ax1.grid(True, alpha=0.3, linestyle='--')
                
                # 6. 计算频谱，分析从1开始的所有阶次
                full_spectrum = analyzer._calculate_ripple_spectrum(sorted_values, max_harmonics=20, min_order=1, max_order=156)  # 26*6=156
                
                # 使用所有阶次的成分，按振幅排序
                spectrum = full_spectrum[:10]
                
                # 7. 绘制频谱分析结果
                ax2 = fig.add_subplot(gs[i, 1])
                ax2.set_title(f'{title} - Spectrum Analysis (Orders 1+)', fontsize=12, fontweight='bold')
                
                # 准备频谱数据
                if spectrum:
                    orders = [item['order'] for item in spectrum[:10]]
                    amplitudes = [item['amplitude'] for item in spectrum[:10]]
                    
                    # 绘制频谱柱状图
                    x_positions = np.arange(len(orders))
                    ax2.bar(x_positions, amplitudes, alpha=0.7, color=colors[i])
                    
                    # 设置X轴标签（阶次）
                    ax2.set_xticks(x_positions)
                    ax2.set_xticklabels([str(int(order)) for order in orders], fontsize=8)
                    
                    # 添加振幅值标签
                    max_amp = max(amplitudes) * 1.2 if amplitudes else 0.2
                    for j, amp in enumerate(amplitudes):
                        if amp > 0:
                            ax2.text(j, amp + max_amp * 0.05, f'{amp:.2f}', 
                                    ha='center', va='bottom', fontsize=7)
                
                ax2.set_ylabel('Amplitude (μm)', fontsize=8)
                ax2.tick_params(axis='both', labelsize=8)
                ax2.grid(True, alpha=0.3, linestyle='--')
                
                # 隐藏右侧和顶部边框
                ax1.spines['right'].set_visible(False)
                ax1.spines['top'].set_visible(False)
                ax2.spines['right'].set_visible(False)
                ax2.spines['top'].set_visible(False)
            else:
                # 无数据时的处理
                ax1 = fig.add_subplot(gs[i, 0])
                ax1.set_title(f'{title} - Processed Data', fontsize=12, fontweight='bold')
                ax1.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax1.transAxes)
                ax1.set_xlabel('Normalized Rotation Position', fontsize=8)
                ax1.set_ylabel('Deviation (μm)', fontsize=8)
                
                ax2 = fig.add_subplot(gs[i, 1])
                ax2.set_title(f'{title} - Spectrum Analysis (≥87)', fontsize=12, fontweight='bold')
                ax2.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_ylabel('Amplitude (μm)', fontsize=8)
        
        # 添加分析总结
        summary_text = f"Spectrum Analysis Summary: Orders 1+\n"
        summary_text += "- Iterative sine wave fitting algorithm\n"
        summary_text += "- Extracts largest order sine waves first\n"
        summary_text += "- Removes extracted sine waves from original signal\n"
        summary_text += "- Repeats process for residual signal\n"
        summary_text += "- Extracts up to 10 largest orders\n"
        summary_text += "- Results sorted by amplitude\n"
        summary_text += "- Analyzing orders from 1 onwards\n"
        summary_text += f"- Gear teeth count: {teeth_count}"
        
        fig.text(0.5, 0.02, summary_text, ha='center', fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"Rebuilt spectrum analysis completed. Results saved to: {output_pdf}")
    
    # 打印频谱分析结果
    print(f"\nSpectrum Analysis Results: Orders 1+")
    print("Dataset | Order | Amplitude")
    print("------------------------")
    
    for title, dataset in datasets.items():
        values = np.array(dataset['values'])
        if len(values) > 0:
            # 确保数据按角度排序
            angles = np.array(dataset['angles'])
            sorted_indices = np.argsort(angles)
            sorted_values = values[sorted_indices]
            
            # 分析从1开始的所有阶次
            full_spectrum = analyzer._calculate_ripple_spectrum(sorted_values, max_harmonics=20, min_order=1, max_order=156)
            # 使用所有阶次的成分，按振幅排序
            spectrum = full_spectrum[:10]
            
            print(f"\n{title}:")
            for item in spectrum[:10]:
                print(f"{item['order']:6} | {item['amplitude']:9.2f}")
        else:
            print(f"\n{title}: No data")


if __name__ == '__main__':
    rebuild_spectrum_analysis()
