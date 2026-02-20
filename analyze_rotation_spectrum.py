"""
分析旋转图表数据的频谱特性
Analyzes spectrum characteristics of rotation chart data
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser
from klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport


def analyze_rotation_spectrum():
    """
    分析旋转图表数据的频谱特性
    使用图片上的四个曲线：左侧齿形、右侧齿形、左侧齿向、右侧齿向
    """
    # 读取MKA文件数据
    mka_file = '263751-018-WAV.mka'
    parser = MKAParser(mka_file)
    
    # 获取旋转图表数据
    combined_data = parser.get_combined_data(use_evaluation_range=True)
    
    # 提取四个曲线的数据
    datasets = {
        'Profile Left': [],
        'Profile Right': [],
        'Flank Left': [],
        'Flank Right': []
    }
    
    # 从combined_data中提取数据
    if 'profile_left' in combined_data:
        for angle, value in combined_data['profile_left']:
            datasets['Profile Left'].append(value)
    
    if 'profile_right' in combined_data:
        for angle, value in combined_data['profile_right']:
            datasets['Profile Right'].append(value)
    
    if 'flank_left' in combined_data:
        for angle, value in combined_data['flank_left']:
            datasets['Flank Left'].append(value)
    
    if 'flank_right' in combined_data:
        for angle, value in combined_data['flank_right']:
            datasets['Flank Right'].append(value)
    
    # 创建频谱分析器
    analyzer = KlingelnbergRippleSpectrumReport()
    
    # 创建PDF报告
    output_pdf = 'rotation_spectrum_analysis.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4尺寸
        fig.suptitle('Rotation Data Spectrum Analysis', fontsize=16, fontweight='bold')
        
        # 创建子图
        gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, 1])
        
        colors = ['blue', 'red', 'green', 'magenta']
        
        for i, (title, data) in enumerate(datasets.items()):
            if len(data) > 0:
                ax = fig.add_subplot(gs[i])
                ax.set_title(title, fontsize=12, fontweight='bold')
                
                # 计算频谱
                spectrum = analyzer._calculate_ripple_spectrum(np.array(data))
                
                # 准备x轴数据
                x = np.linspace(0, 1, len(data))
                
                # 绘制原始数据
                ax.plot(x, data, label='Original Data', color='gray', alpha=0.5, linewidth=0.5)
                
                # 绘制前3个主导频率的正弦波
                for j in range(min(3, len(spectrum))):
                    harmonic = spectrum[j]
                    ax.plot(x, harmonic['fitted_sine'], 
                            label=f'Harmonic {j+1}: Amp={harmonic["amplitude"]:.2f}, Order={harmonic["order"]:.1f}', 
                            color=colors[i], alpha=0.7, linewidth=0.8)
                
                # 绘制频谱
                ax2 = ax.twinx()
                orders = [item['order'] for item in spectrum[:10]]
                amplitudes = [item['amplitude'] for item in spectrum[:10]]
                ax2.bar(range(1, len(orders) + 1), amplitudes, alpha=0.3, color=colors[i])
                ax2.set_ylabel('Amplitude', fontsize=8)
                
                # 设置图例和标签
                ax.legend(fontsize=8, loc='upper right')
                ax.set_xlabel('Normalized Rotation Position', fontsize=8)
                ax.set_ylabel('Deviation (μm)', fontsize=8)
                ax.tick_params(axis='both', labelsize=8)
                ax2.tick_params(axis='y', labelsize=8)
                ax.grid(True, alpha=0.3, linestyle='--')
            else:
                ax = fig.add_subplot(gs[i])
                ax.set_title(title, fontsize=12, fontweight='bold')
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                ax.set_xlabel('Normalized Rotation Position', fontsize=8)
                ax.set_ylabel('Deviation (μm)', fontsize=8)
        
        # 添加分析总结
        summary_text = "Spectrum Analysis Summary:\n"
        summary_text += "- Iterative sine wave fitting algorithm\n"
        summary_text += "- Extracts 10 dominant frequencies\n"
        summary_text += "- Amplitude-based frequency ranking\n"
        summary_text += "- Each harmonic is removed before next iteration\n"
        summary_text += "- Analysis based on rotation chart data"
        
        fig.text(0.5, 0.02, summary_text, ha='center', fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"Spectrum analysis completed. Results saved to: {output_pdf}")
    
    # 打印频谱分析结果
    print("\nSpectrum Analysis Results:")
    print("Dataset | Top 3 Harmonics (Amplitude, Order)")
    print("------------------------------------------")
    
    for title, data in datasets.items():
        if len(data) > 0:
            spectrum = analyzer._calculate_ripple_spectrum(np.array(data))
            harmonics = []
            for j in range(min(3, len(spectrum))):
                harmonic = spectrum[j]
                harmonics.append(f"Amp={harmonic['amplitude']:.2f}, Order={harmonic['order']:.1f}")
            print(f"{title:<12} | {', '.join(harmonics)}")
        else:
            print(f"{title:<12} | No data")


if __name__ == '__main__':
    analyze_rotation_spectrum()
