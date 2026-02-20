"""
显示左齿面的齿形和齿向评价区域中的曲线
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser


def display_left_flank_curves():
    """
    显示左齿面的齿形和齿向评价区域中的曲线
    """
    # 读取MKA文件数据
    mka_file = '004-xiaoxiao1.mka'
    parser = MKAParser(mka_file)
    
    # 获取齿轮齿数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 26  # Fallback to 26 if not found
    
    print(f"Gear teeth count: {teeth_count}")
    
    # 获取旋转图表数据，只使用评价区域内的数据
    combined_data = parser.get_combined_data(use_evaluation_range=True)
    
    # 提取左齿面的齿形和齿向数据
    left_profile_data = []
    left_flank_data = []
    
    if 'profile_left' in combined_data:
        left_profile_data = combined_data['profile_left']
        print(f"Left Profile data points: {len(left_profile_data)}")
    
    if 'flank_left' in combined_data:
        left_flank_data = combined_data['flank_left']
        print(f"Left Flank data points: {len(left_flank_data)}")
    
    # 创建PDF报告
    output_pdf = 'left_flank_curves_analysis_v2.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4尺寸
        fig.suptitle(f'Left Flank Curves Analysis (Teeth Count: {teeth_count})', fontsize=16, fontweight='bold')
        
        # 创建子图
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 1])
        
        # 绘制左齿形曲线
        if left_profile_data:
            # 提取角度和值
            angles = [item[0] for item in left_profile_data]
            values = [item[1] for item in left_profile_data]
            
            # 按角度排序
            sorted_indices = np.argsort(angles)
            sorted_angles = np.array(angles)[sorted_indices]
            sorted_values = np.array(values)[sorted_indices]
            
            # 归一化角度到0-1范围
            min_angle = np.min(sorted_angles)
            max_angle = np.max(sorted_angles)
            angle_range = max_angle - min_angle
            if angle_range > 0:
                normalized_angles = (sorted_angles - min_angle) / angle_range
            else:
                normalized_angles = np.linspace(0, 1, len(sorted_values))
            
            ax1 = fig.add_subplot(gs[0])
            ax1.set_title('Left Profile - Evaluation Range', fontsize=12, fontweight='bold')
            ax1.plot(normalized_angles, sorted_values, label='Left Profile Data', color='blue', alpha=0.7, linewidth=0.8)
            ax1.set_xlabel('Normalized Rotation Position', fontsize=8)
            ax1.set_ylabel('Deviation (μm)', fontsize=8)
            ax1.tick_params(axis='both', labelsize=8)
            ax1.grid(True, alpha=0.3, linestyle='--')
            ax1.legend(fontsize=8, loc='upper right')
            
            # 隐藏右侧和顶部边框
            ax1.spines['right'].set_visible(False)
            ax1.spines['top'].set_visible(False)
        else:
            ax1 = fig.add_subplot(gs[0])
            ax1.set_title('Left Profile - Evaluation Range', fontsize=12, fontweight='bold')
            ax1.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_xlabel('Normalized Rotation Position', fontsize=8)
            ax1.set_ylabel('Deviation (μm)', fontsize=8)
        
        # 绘制左齿向曲线
        if left_flank_data:
            # 提取角度和值
            angles = [item[0] for item in left_flank_data]
            values = [item[1] for item in left_flank_data]
            
            # 按角度排序
            sorted_indices = np.argsort(angles)
            sorted_angles = np.array(angles)[sorted_indices]
            sorted_values = np.array(values)[sorted_indices]
            
            # 归一化角度到0-1范围
            min_angle = np.min(sorted_angles)
            max_angle = np.max(sorted_angles)
            angle_range = max_angle - min_angle
            if angle_range > 0:
                normalized_angles = (sorted_angles - min_angle) / angle_range
            else:
                normalized_angles = np.linspace(0, 1, len(sorted_values))
            
            ax2 = fig.add_subplot(gs[1])
            ax2.set_title('Left Flank - Evaluation Range', fontsize=12, fontweight='bold')
            ax2.plot(normalized_angles, sorted_values, label='Left Flank Data', color='green', alpha=0.7, linewidth=0.8)
            ax2.set_xlabel('Normalized Rotation Position', fontsize=8)
            ax2.set_ylabel('Deviation (μm)', fontsize=8)
            ax2.tick_params(axis='both', labelsize=8)
            ax2.grid(True, alpha=0.3, linestyle='--')
            ax2.legend(fontsize=8, loc='upper right')
            
            # 隐藏右侧和顶部边框
            ax2.spines['right'].set_visible(False)
            ax2.spines['top'].set_visible(False)
        else:
            ax2 = fig.add_subplot(gs[1])
            ax2.set_title('Left Flank - Evaluation Range', fontsize=12, fontweight='bold')
            ax2.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_xlabel('Normalized Rotation Position', fontsize=8)
            ax2.set_ylabel('Deviation (μm)', fontsize=8)
        
        # 添加分析总结
        summary_text = f"Left Flank Curves Analysis Summary:\n"
        summary_text += f"- Gear teeth count: {teeth_count}\n"
        summary_text += "- Only showing data within evaluation range\n"
        summary_text += f"- Left Profile data points: {len(left_profile_data)}\n"
        summary_text += f"- Left Flank data points: {len(left_flank_data)}\n"
        summary_text += "- Data sorted by rotation angle\n"
        summary_text += "- X-axis: Normalized rotation position (0-1)"
        
        fig.text(0.5, 0.02, summary_text, ha='center', fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"Left flank curves analysis completed. Results saved to: {output_pdf}")


if __name__ == '__main__':
    display_left_flank_curves()
