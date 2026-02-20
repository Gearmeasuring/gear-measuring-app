"""
检查原始数据，查看是否存在突变
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser


def check_raw_data():
    """
    检查原始数据，查看是否存在突变
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
    
    # 创建PDF报告
    output_pdf = 'raw_data_check.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4尺寸
        fig.suptitle('Raw Data Check', fontsize=16, fontweight='bold')
        
        # 创建子图
        gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, 1])
        
        colors = ['blue', 'red', 'green', 'magenta']
        
        for i, (title, dataset) in enumerate(datasets.items()):
            angles = dataset['angles']
            values = dataset['values']
            
            if len(values) > 0:
                ax = fig.add_subplot(gs[i])
                ax.set_title(f'{title} - Raw Data', fontsize=12, fontweight='bold')
                
                # 按角度排序
                sorted_indices = np.argsort(angles)
                sorted_angles = np.array(angles)[sorted_indices]
                sorted_values = np.array(values)[sorted_indices]
                
                # 归一化角度到0-1范围
                if len(sorted_angles) > 0:
                    min_angle = min(sorted_angles)
                    max_angle = max(sorted_angles)
                    angle_range = max_angle - min_angle
                    if angle_range > 0:
                        normalized_angles = [(angle - min_angle) / angle_range for angle in sorted_angles]
                    else:
                        normalized_angles = np.linspace(0, 1, len(sorted_values))
                else:
                    normalized_angles = np.linspace(0, 1, len(sorted_values))
                
                # 绘制原始数据
                ax.plot(normalized_angles, sorted_values, label='Raw Data', color=colors[i], alpha=0.7, linewidth=0.8)
                ax.set_xlabel('Normalized Rotation Position', fontsize=8)
                ax.set_ylabel('Deviation (μm)', fontsize=8)
                ax.tick_params(axis='both', labelsize=8)
                ax.grid(True, alpha=0.3, linestyle='--')
                
                # 检测突变点
                if len(sorted_values) > 1:
                    # 计算相邻数据点的差值
                    differences = np.abs(np.diff(sorted_values))
                    # 计算均值和标准差
                    mean_diff = np.mean(differences)
                    std_diff = np.std(differences)
                    # 阈值设为3倍标准差
                    threshold = 3 * std_diff
                    # 找出突变点
                    jump_indices = np.where(differences > threshold)[0]
                    
                    if len(jump_indices) > 0:
                        print(f"{title} 中发现 {len(jump_indices)} 个突变点")
                        # 标记突变点
                        for idx in jump_indices:
                            ax.axvline(x=normalized_angles[idx], color='black', linestyle='--', alpha=0.5)
                            ax.axvline(x=normalized_angles[idx+1], color='black', linestyle='--', alpha=0.5)
            else:
                ax = fig.add_subplot(gs[i])
                ax.set_title(f'{title} - Raw Data', fontsize=12, fontweight='bold')
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                ax.set_xlabel('Normalized Rotation Position', fontsize=8)
                ax.set_ylabel('Deviation (μm)', fontsize=8)
        
        # 添加分析总结
        summary_text = "Raw Data Check Summary:\n"
        summary_text += "- This report shows the raw data without any preprocessing\n"
        summary_text += "- Data is sorted by rotation angle\n"
        summary_text += "- Vertical lines indicate potential jump points\n"
        summary_text += "- Jump points are detected based on 3σ threshold\n"
        
        fig.text(0.5, 0.02, summary_text, ha='center', fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"Raw data check completed. Results saved to: {output_pdf}")
    
    # 打印每个数据集的基本信息
    print("\nRaw Data Statistics:")
    print("Dataset | Points | Min Value | Max Value | Mean | Std")
    print("--------------------------------------------------")
    
    for title, dataset in datasets.items():
        values = np.array(dataset['values'])
        if len(values) > 0:
            print(f"{title} | {len(values):6} | {np.min(values):9.2f} | {np.max(values):9.2f} | {np.mean(values):5.2f} | {np.std(values):4.2f}")
        else:
            print(f"{title} | {'0':6} | {'N/A':9} | {'N/A':9} | {'N/A':5} | {'N/A':4}")


if __name__ == '__main__':
    check_raw_data()
