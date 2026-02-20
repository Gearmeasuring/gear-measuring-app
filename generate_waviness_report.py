import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import cm
import io

def generate_waviness_chart():
    """
    生成旋转角范围内的波纹度图表
    """
    # 创建一个2x2的图表布局
    fig, axes = plt.subplots(4, 1, figsize=(12, 10))
    fig.suptitle('旋转角范围内的共同波纹度', fontsize=16, fontproperties='SimHei')
    
    # 生成模拟数据
    rotation_angles = np.linspace(0, 12, 100)
    
    # 第一子图：右侧齿廓和齿距
    np.random.seed(42)
    base_signal1 = 0.1 * np.sin(2 * np.pi * rotation_angles / 3)
    noise1 = 0.02 * np.random.randn(len(rotation_angles))
    signal1 = base_signal1 + noise1
    
    # 第二子图：左侧齿廓和齿距
    base_signal2 = 0.08 * np.sin(2 * np.pi * rotation_angles / 3 + 0.5)
    noise2 = 0.015 * np.random.randn(len(rotation_angles))
    signal2 = base_signal2 + noise2
    
    # 第三子图：左侧齿向和齿距
    base_signal3 = 0.07 * np.sin(2 * np.pi * rotation_angles / 3 + 1.0)
    noise3 = 0.01 * np.random.randn(len(rotation_angles))
    signal3 = base_signal3 + noise3
    
    # 第四子图：右侧齿向和齿距
    base_signal4 = 0.09 * np.sin(2 * np.pi * rotation_angles / 3 + 1.5)
    noise4 = 0.018 * np.random.randn(len(rotation_angles))
    signal4 = base_signal4 + noise4
    
    # 绘制每个子图
    axes[0].plot(rotation_angles, signal1, 'r-', label='测量曲线')
    axes[0].plot(rotation_angles, base_signal1, 'b--', label='基准曲线')
    axes[0].set_ylabel('偏差 [μm]')
    axes[0].set_title('① 右侧齿廓和齿距')
    axes[0].grid(True, linestyle='--', alpha=0.7)
    axes[0].legend()
    axes[0].text(0.02, 0.95, 'A1: 0.19\nPr: 32.22', transform=axes[0].transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.1))
    
    axes[1].plot(rotation_angles, signal2, 'r-', label='测量曲线')
    axes[1].plot(rotation_angles, base_signal2, 'b--', label='基准曲线')
    axes[1].set_ylabel('偏差 [μm]')
    axes[1].set_title('② 左侧齿廓和齿距')
    axes[1].grid(True, linestyle='--', alpha=0.7)
    axes[1].legend()
    axes[1].text(0.02, 0.95, 'A1: 0.28\nPr: 19.88', transform=axes[1].transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.1))
    
    axes[2].plot(rotation_angles, signal3, 'r-', label='测量曲线')
    axes[2].plot(rotation_angles, base_signal3, 'b--', label='基准曲线')
    axes[2].set_ylabel('偏差 [μm]')
    axes[2].set_title('③ 左侧齿向和齿距')
    axes[2].grid(True, linestyle='--', alpha=0.7)
    axes[2].legend()
    axes[2].text(0.02, 0.95, 'A1: 0.27\nPr: 62.5', transform=axes[2].transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.1))
    
    axes[3].plot(rotation_angles, signal4, 'r-', label='测量曲线')
    axes[3].plot(rotation_angles, base_signal4, 'b--', label='基准曲线')
    axes[3].set_xlabel('旋转角 [度]')
    axes[3].set_ylabel('偏差 [μm]')
    axes[3].set_title('④ 右侧齿向和齿距')
    axes[3].grid(True, linestyle='--', alpha=0.7)
    axes[3].legend()
    axes[3].text(0.02, 0.95, 'A1: 0.57\nPr: 19.19', transform=axes[3].transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.1))
    
    # 调整布局
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # 保存图表到内存
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

def generate_pdf_report(chart_buffer):
    """
    生成包含波纹度图表的PDF报表
    """
    # 创建PDF文档
    doc = SimpleDocTemplate("波纹度分析报告.pdf", pagesize=A4)
    elements = []
    
    # 获取样式
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading1']
    body_style = styles['BodyText']
    
    # 添加标题
    elements.append(Paragraph("波纹度分析报告", title_style))
    elements.append(Spacer(1, 20))
    
    # 添加章节标题
    elements.append(Paragraph("8.3.5 旋转角范围内的波纹度", heading_style))
    elements.append(Spacer(1, 10))
    
    # 添加说明文字
    description = "齿面上的每个测量点都有一个旋转角，用于在滚动时描绘其位置。\n\n"
    description += "可利用[绘制共同波纹度]按钮根据旋转角绘制所有测量点。从齿轮圆周范围内所有被测的齿产生一条测量曲线。如果测量了足够多的齿或所有齿，从而可以正确考虑重叠和间隙，即可计算该测量曲线的共同波纹度。由于在齿轮的圆周范围内确定曲线，因此该曲线是封闭的，并且只能出现整数的波纹度。\n\n"
    description += "以下示例为第一主导阶次 O(1)。"
    elements.append(Paragraph(description, body_style))
    elements.append(Spacer(1, 20))
    
    # 添加图表
    chart_image = Image(chart_buffer, width=18*cm, height=15*cm)
    elements.append(chart_image)
    elements.append(Spacer(1, 10))
    
    # 添加图表说明
    chart_note = "Fig. 58 旋转角范围内的共同波纹度"
    elements.append(Paragraph(chart_note, body_style))
    elements.append(Spacer(1, 10))
    
    # 添加图例
    legend = "① 右侧齿廓和齿距\n② 左侧齿廓和齿距\n③ 左侧齿向和齿距\n④ 右侧齿向和齿距"
    elements.append(Paragraph(legend, body_style))
    elements.append(Spacer(1, 10))
    
    # 添加特点说明
    elements.append(Paragraph("特点：", heading_style))
    features = "• 在当前的旋转角中连续显示某一侧或齿面的所有曲线。\n"
    features += "• 通过所有齿进行显示。\n"
    features += "• 如果是外齿的齿廓，则曲线在左侧齿根处开始，在右侧齿顶处开始。\n"
    features += "• 如果是齿向，则曲线在右旋情况下从上方开始，在左旋情况下从下方开始。"
    elements.append(Paragraph(features, body_style))
    elements.append(Spacer(1, 30))
    
    # 新增一页：齿轮参数分析
    elements.append(Paragraph("齿轮参数分析", heading_style))
    elements.append(Spacer(1, 10))
    
    # 添加齿轮参数计算结果
    params = "基于MKA文件的齿轮参数计算结果：\n\n"
    params += "263751-018-WAV.mka：\n"
    params += "• ep (齿形重叠率): 1.454\n"
    params += "• lo (滚长终点): 33.578 mm\n"
    params += "• lu (滚长起点): 24.775 mm\n"
    params += "• el (齿向重叠率): 2.776\n"
    params += "• zo (齿向评价上限): 18.9\n"
    params += "• zu (齿向评价下限): -18.9\n\n"
    params += "004-xiaoxiao1.mka：\n"
    params += "• ep (齿形重叠率): 1.810\n"
    params += "• lo (滚长终点): 11.822 mm\n"
    params += "• lu (滚长起点): 3.261 mm\n"
    params += "• el (齿向重叠率): 2.616\n"
    params += "• zo (齿向评价上限): 14.0\n"
    params += "• zu (齿向评价下限): -14.0"
    elements.append(Paragraph(params, body_style))
    
    # 生成PDF
    doc.build(elements)
    print("PDF报告已生成：波纹度分析报告.pdf")

if __name__ == "__main__":
    # 生成波纹度图表
    chart_buf = generate_waviness_chart()
    
    # 生成PDF报告
    generate_pdf_report(chart_buf)
