"""
分析左齿形、右齿形、左齿向、右齿向曲线的频谱特性
Analyzes spectrum characteristics of left/right profile and flank curves
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser
from klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport


def analyze_all_flank_spectrum():
    """
    分析左齿形、右齿形、左齿向、右齿向曲线的频谱特性
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
        'Left Profile': [],
        'Right Profile': [],
        'Left Flank': [],
        'Right Flank': []
    }
    
    # 从combined_data中提取数据
    if 'profile_left' in combined_data:
        for angle, value in combined_data['profile_left']:
            datasets['Left Profile'].append(value)
    
    if 'profile_right' in combined_data:
        for angle, value in combined_data['profile_right']:
            datasets['Right Profile'].append(value)
    
    if 'flank_left' in combined_data:
        for angle, value in combined_data['flank_left']:
            datasets['Left Flank'].append(value)
    
    if 'flank_right' in combined_data:
        for angle, value in combined_data['flank_right']:
            datasets['Right Flank'].append(value)
    
    # 创建频谱分析器
    analyzer = KlingelnbergRippleSpectrumReport()
    
    # 创建PDF报告
    output_pdf = 'all_flank_spectrum_analysis_max87.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4尺寸
        fig.suptitle('All Flank Spectrum Analysis', fontsize=16, fontweight='bold')
        
        # 创建子图
        gs = fig.add_gridspec(8, 1, height_ratios=[1, 1, 1, 1, 1, 1, 1, 1])
        
        colors = ['blue', 'red', 'green', 'magenta']
        
        for i, (title, data) in enumerate(datasets.items()):
            if len(data) > 0:
                ax = fig.add_subplot(gs[i*2])
                ax.set_title(f'{title} - Processed Data', fontsize=12, fontweight='bold')
                
                # 预处理数据，移除起始不稳定部分并平滑
                processed_data = analyzer._preprocess_data(np.array(data))
                
                # 绘制预处理后的数据
                x = np.linspace(0, 1, len(processed_data))
                ax.plot(x, processed_data, label='Processed Data', color=colors[i], alpha=0.7, linewidth=0.8)
                ax.set_xlabel('Normalized Rotation Position', fontsize=8)
                ax.set_ylabel('Deviation (μm)', fontsize=8)
                ax.tick_params(axis='both', labelsize=8)
                ax.grid(True, alpha=0.3, linestyle='--')
                
                # 计算频谱，只分析小于等于87的阶
                spectrum = analyzer._calculate_ripple_spectrum(processed_data, max_harmonics=10, max_order=87)
                
                # 绘制频谱分析结果
                ax2 = fig.add_subplot(gs[i*2 + 1])
                ax2.set_title(f'{title} - Spectrum Analysis', fontsize=12, fontweight='bold')
                
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
                ax2.set_title(f'{title} - Spectrum Analysis', fontsize=12, fontweight='bold')
                ax2.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax2.transAxes)
        
        # 添加分析总结
        summary_text = "Spectrum Analysis Summary:\n"
        summary_text += "- Iterative sine wave fitting algorithm\n"
        summary_text += "- Extracts largest order sine waves first\n"
        summary_text += "- Removes extracted sine waves from original signal\n"
        summary_text += "- Repeats process for residual signal\n"
        summary_text += "- Extracts up to 10 largest orders\n"
        summary_text += "- Results sorted by amplitude"
        
        fig.text(0.5, 0.02, summary_text, ha='center', fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"All flank spectrum analysis completed. Results saved to: {output_pdf}")
    
    # 打印频谱分析结果
    print("\nAll Flank Spectrum Analysis Results:")
    print("Dataset | Order | Amplitude")
    print("------------------------")
    
    for title, data in datasets.items():
        if len(data) > 0:
            processed_data = analyzer._preprocess_data(np.array(data))
            spectrum = analyzer._calculate_ripple_spectrum(processed_data, max_harmonics=10, max_order=87)
            print(f"\n{title}:")
            for item in spectrum[:10]:
                print(f"{item['order']:6} | {item['amplitude']:9.2f}")
        else:
            print(f"\n{title}: No data")
    
    # 分析87阶附近的成分
    print("\n=== 87阶附近频谱分析 ===")
    print("Dataset | Order | Amplitude")
    print("------------------------")
    
    for title, data in datasets.items():
        if len(data) > 0:
            processed_data = analyzer._preprocess_data(np.array(data))
            target_spectrum = analyzer.analyze_target_order(processed_data, target_order=87, order_range=5, max_order=87)
            print(f"\n{title}:")
            if target_spectrum:
                for item in target_spectrum:
                    print(f"{item['order']:6} | {item['amplitude']:9.2f}")
            else:
                print("  No components found near order 87")
        else:
            print(f"\n{title}: No data")
    
    # 分析87阶附近的成分（只分析小于等于87的阶）
    print("\n=== 87阶附近频谱分析（≤87阶）===")
    print("Dataset | Order | Amplitude")
    print("------------------------")
    
    for title, data in datasets.items():
        if len(data) > 0:
            processed_data = analyzer._preprocess_data(np.array(data))
            target_spectrum = analyzer.analyze_target_order(processed_data, target_order=87, order_range=5, max_order=87)
            print(f"\n{title}:")
            if target_spectrum:
                for item in target_spectrum:
                    print(f"{item['order']:6} | {item['amplitude']:9.2f}")
            else:
                print("  No components found near order 87 (≤87阶)")
        else:
            print(f"\n{title}: No data")


if __name__ == '__main__':
    analyze_all_flank_spectrum()
