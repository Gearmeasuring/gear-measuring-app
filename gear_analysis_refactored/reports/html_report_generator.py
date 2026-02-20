"""
HTML报告生成器
生成专业的HTML分析报告
"""
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from config.logging_config import logger


class HTMLReportGenerator:
    """生成专业的HTML分析报告"""
    def __init__(self, gear_data, deviation_results, undulation_results, pitch_results, file_path, profile_data=None, flank_data=None):
        self.gear_data = gear_data
        self.deviation_results = deviation_results
        self.undulation_results = undulation_results
        self.pitch_results = pitch_results
        self.ripple_results = undulation_results  # 兼容旧命名
        self.file_path = file_path
        self.profile_data = profile_data
        self.flank_data = flank_data
        self.report_path = os.path.splitext(file_path)[0] + "_综合分析报告.html"
        self.img_dir = os.path.splitext(self.report_path)[0] + "_images"
        os.makedirs(self.img_dir, exist_ok=True)
        self.plots = {}
        
        # 自动生成周节分析图表
        if self.pitch_results:
            self._remove_old_pitch_charts()
            self._create_pitch_bar_charts()

    def _remove_old_pitch_charts(self):
        """删除旧的周节分析图表图片"""
        chart_names = [
            "pitch_left_fp.png", "pitch_left_Fp.png",
            "pitch_right_fp.png", "pitch_right_Fp.png"
        ]
        for name in chart_names:
            path = os.path.join(self.img_dir, name)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"删除旧图失败: {path}, 错误: {e}")

    def _create_pitch_bar_charts(self):
        """自动生成四张周节偏差柱状图，保存到self.img_dir"""
        left = self.pitch_results.get('left', {})
        right = self.pitch_results.get('right', {})

        def plot_and_save(teeth, values, ylabel, title, filename):
            if not teeth or not values:
                return
            fig, ax = plt.subplots(figsize=(12, 6))
            x = np.arange(len(teeth))
            bars = ax.bar(x, values, color='skyblue', alpha=0.8, width=0.8)
            
            # 设置x轴标签为齿号
            ax.set_xticks(x)
            ax.set_xticklabels(teeth)
            
            # 添加数值标签
            for i, (tooth, value) in enumerate(zip(teeth, values)):
                ax.text(i, value + (max(values) - min(values)) * 0.01, 
                       f'{value:.1f}', ha='center', va='bottom', fontsize=8)
            
            ax.set_xlabel("齿号")
            ax.set_ylabel(ylabel)
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            ax.set_xlim(-0.5, len(teeth) - 0.5)
            # 设置Y轴范围增大一倍
            if values:
                y_min, y_max = min(values), max(values)
                y_range = y_max - y_min
                ax.set_ylim(y_min - y_range * 0.5, y_max + y_range * 0.5)
            fig.tight_layout(pad=2.0)
            save_path = os.path.join(self.img_dir, filename)
            fig.savefig(save_path)
            plt.close(fig)

        # 左面fp
        plot_and_save(
            left.get('teeth', []), left.get('fp', []),
            "fp (μm)", "左齿面 - fp (单齿周节偏差)", "pitch_left_fp.png"
        )
        # 左面Fp
        plot_and_save(
            left.get('teeth', []), left.get('Fp', []),
            "Fp (μm)", "左齿面 - Fp (累积周节偏差)", "pitch_left_Fp.png"
        )
        # 右面fp
        plot_and_save(
            right.get('teeth', []), right.get('fp', []),
            "fp (μm)", "右齿面 - fp (单齿周节偏差)", "pitch_right_fp.png"
        )
        # 右面Fp
        plot_and_save(
            right.get('teeth', []), right.get('Fp', []),
            "Fp (μm)", "右齿面 - Fp (累积周节偏差)", "pitch_right_Fp.png"
        )

    def generate(self):
        """生成HTML报告"""
        try:
            # 1. 生成所有需要的图表
            if self.deviation_results:
                logger.info("正在生成偏差分析图表...")
                self.plots['deviation_profile'] = self._create_deviation_plot('profile')
                self.plots['deviation_flank'] = self._create_deviation_plot('flank')
            
            if self.pitch_results:
                logger.info("正在生成周节偏差图表...")
                self.plots['pitch'] = self._create_pitch_plot()

            if self.ripple_results:
                logger.info("正在生成波纹度分析图表...")
                self.plots['ripple_profile'] = self._create_ripple_plot('profile')
                self.plots['ripple_flank'] = self._create_ripple_plot('flank')
                self.plots['order_profile'] = self._create_order_spectrum_plot('profile')
                self.plots['order_flank'] = self._create_order_spectrum_plot('flank')
                self.plots['waterfall_profile'] = self._create_waterfall_plot('profile')
                self.plots['waterfall_flank'] = self._create_waterfall_plot('flank')

            if self.profile_data and self.flank_data:
                logger.info("正在为报告生成3D图表...")
                side_3d, tooth_3d = self.get_first_available_tooth_for_3d()
                if side_3d and tooth_3d:
                    self.plots['3d_surface'] = self._create_3d_plot(side_3d, tooth_3d)

            # 2. 渲染HTML模板
            html_content = self.render_template()
            
            with open(self.report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML报告已生成: {self.report_path}")
            return self.report_path
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}", exc_info=True)
            return None

    def render_template(self):
        """渲染HTML模板"""
        report_title = f"齿轮综合分析报告 - {os.path.basename(self.file_path)}"
        generation_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{report_title}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Microsoft YaHei', 'SimHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                    min-height: 100vh;
                    color: #2c3e50;
                }}
                
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
                    overflow: hidden;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    padding: 40px 20px;
                    margin-bottom: 0;
                }}
                
                .header h1 {{
                    font-size: 2.8em;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    font-weight: 300;
                }}
                
                .header .subtitle {{
                    font-size: 1.2em;
                    opacity: 0.9;
                    margin-top: 10px;
                }}
                
                .content {{
                    padding: 40px;
                }}
                
                .section {{
                    margin: 40px 0;
                    background: #f8f9fa;
                    border-radius: 12px;
                    padding: 30px;
                    border-left: 5px solid #667eea;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }}
                
                .section:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
                }}
                
                .section h2 {{
                    color: #2c3e50;
                    margin-bottom: 25px;
                    font-size: 2em;
                    display: flex;
                    align-items: center;
                    font-weight: 600;
                }}
                
                .section h2::before {{
                    content: "📊";
                    margin-right: 15px;
                    font-size: 1.5em;
                }}
                
                .section h3 {{
                    color: #34495e;
                    margin: 25px 0 15px 0;
                    font-size: 1.5em;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 8px;
                    font-weight: 500;
                }}
                
                .section h4 {{
                    color: #2c3e50;
                    margin: 20px 0 10px 0;
                    font-size: 1.2em;
                    font-weight: 500;
                }}
                
                .grid-container {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
                    gap: 25px;
                    margin: 20px 0;
                }}
                
                .chart-container {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    border: 1px solid #e1e8ed;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                    transition: all 0.3s ease;
                }}
                
                .chart-container:hover {{
                    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
                    transform: translateY(-2px);
                }}
                
                .chart-container h3 {{
                    color: #2c3e50;
                    margin-bottom: 15px;
                    font-size: 1.3em;
                    font-weight: 600;
                    text-align: center;
                }}
                
                .chart-container h4 {{
                    color: #34495e;
                    margin: 15px 0 10px 0;
                    font-size: 1.1em;
                    font-weight: 500;
                }}
                
                .chart-container img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease;
                }}
                
                .chart-container img:hover {{
                    transform: scale(1.02);
                }}
                
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                }}
                
                th, td {{
                    padding: 15px 12px;
                    text-align: center;
                    border-bottom: 1px solid #ecf0f1;
                    font-size: 0.95em;
                }}
                
                th {{
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: white;
                    font-weight: 600;
                    font-size: 1em;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                    position: sticky;
                    top: 0;
                    z-index: 10;
                }}
                
                td {{
                    font-size: 0.9em;
                    transition: background-color 0.3s ease;
                }}
                
                tr:hover td {{
                    background-color: #f8f9fa;
                }}
                
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                
                .data-table-container {{
                    max-height: 400px;
                    overflow-y: auto;
                    border-radius: 10px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                }}
                
                .data-table-container::-webkit-scrollbar {{
                    width: 8px;
                }}
                
                .data-table-container::-webkit-scrollbar-track {{
                    background: #f1f1f1;
                    border-radius: 4px;
                }}
                
                .data-table-container::-webkit-scrollbar-thumb {{
                    background: #c1c1c1;
                    border-radius: 4px;
                }}
                
                .data-table-container::-webkit-scrollbar-thumb:hover {{
                    background: #a8a8a8;
                }}
                
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                
                .stat-card {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                    transition: transform 0.3s ease;
                }}
                
                .stat-card:hover {{
                    transform: translateY(-5px);
                }}
                
                .stat-card .number {{
                    font-size: 2.5em;
                    font-weight: bold;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                
                .stat-card .label {{
                    font-size: 1em;
                    opacity: 0.9;
                    font-weight: 500;
                }}
                
                .params {{
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    color: white;
                    padding: 25px;
                    border-radius: 12px;
                    margin: 20px 0;
                    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                }}
                
                .params p {{
                    margin: 12px 0;
                    font-size: 1.1em;
                }}
                
                .params strong {{
                    color: #fff;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                
                .pass {{
                    color: #27ae60;
                    font-weight: bold;
                }}
                
                .fail {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                
                .warning {{
                    color: #f39c12;
                    font-weight: bold;
                }}
                
                .diagnosis {{
                    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                    border-left: 5px solid #3498db;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                }}
                
                .diagnosis h3 {{
                    color: #2c3e50;
                    margin-bottom: 10px;
                    font-size: 1.2em;
                }}
                
                .diagnosis p {{
                    margin: 8px 0;
                    color: #34495e;
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding: 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 12px;
                }}
                
                .footer p {{
                    margin: 5px 0;
                    font-size: 1em;
                    opacity: 0.9;
                }}
                
                ul {{
                    list-style: none;
                    padding: 0;
                }}
                
                ul li {{
                    padding: 8px 0;
                    border-bottom: 1px solid #ecf0f1;
                    color: #2c3e50;
                }}
                
                ul li:last-child {{
                    border-bottom: none;
                }}
                
                ul li::before {{
                    content: "•";
                    color: #3498db;
                    font-weight: bold;
                    display: inline-block;
                    width: 1em;
                    margin-left: -1em;
                }}
                
                @media print {{
                    body {{
                        background: white;
                    }}
                    .container {{
                        box-shadow: none;
                        border-radius: 0;
                    }}
                    .section {{
                        box-shadow: none;
                        border: 1px solid #ddd;
                    }}
                }}
                
                @media (max-width: 768px) {{
                    .grid-container {{
                        grid-template-columns: 1fr;
                    }}
                    .header h1 {{
                        font-size: 2em;
                    }}
                    .content {{
                        padding: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔧 齿轮综合分析报告</h1>
                    <div class="subtitle">
                        <p>文件: {os.path.basename(self.file_path)}</p>
                        <p>生成时间: {generation_time}</p>
                        <p>分析软件: 齿轮分析系统 v1.0</p>
                    </div>
                </div>
                
                <div class="content">
                    {self._render_basic_info()}
                    {self._render_deviation_analysis()}
                    {self._render_pitch_analysis()}
                    {self._render_ripple_analysis()}
                    {self._render_3d_analysis()}
                </div>
                
                <div class="footer">
                    <p>本报告由齿轮分析系统自动生成</p>
                    <p>版权所有 © 2025 齿轮技术研究所</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _render_basic_info(self):
        """渲染基本信息"""
        if not self.gear_data:
            return ""
            
        return f"""
        <div class="section">
            <h2>基本信息</h2>
            <div class="params">
                <p><strong>模数:</strong> {self.gear_data.get('module', 'N/A')} mm</p>
                <p><strong>齿数:</strong> {self.gear_data.get('teeth', 'N/A')}</p>
                <p><strong>压力角:</strong> {self.gear_data.get('pressure_angle', 'N/A')}°</p>
                <p><strong>螺旋角:</strong> {self.gear_data.get('helix_angle', 'N/A')}°</p>
                <p><strong>齿宽:</strong> {self.gear_data.get('width', 'N/A')} mm</p>
                <p><strong>分度圆直径:</strong> {self.gear_data.get('pitch_diameter', 'N/A')} mm</p>
            </div>
        </div>
        """

    def _render_deviation_analysis(self):
        """渲染偏差分析"""
        if not self.deviation_results:
            return ""
            
        return f"""
        <div class="section">
            <h2>ISO1328偏差分析</h2>
            <div class="grid-container">
                <div class="chart-container">
                    <h3>齿形偏差分析</h3>
                    {self._get_chart_html('deviation_profile')}
                </div>
                <div class="chart-container">
                    <h3>齿向偏差分析</h3>
                    {self._get_chart_html('deviation_flank')}
                </div>
            </div>
        </div>
        """

    def _render_pitch_analysis(self):
        """渲染周节分析"""
        if not self.pitch_results:
            return ""
            
        return f"""
        <div class="section">
            <h2>周节偏差分析</h2>
            <div class="grid-container">
                <div class="chart-container">
                    <h3>左齿面周节偏差</h3>
                    <img src="{self._get_image_path('pitch_left_fp.png')}" alt="左齿面fp">
                    <img src="{self._get_image_path('pitch_left_Fp.png')}" alt="左齿面Fp">
                </div>
                <div class="chart-container">
                    <h3>右齿面周节偏差</h3>
                    <img src="{self._get_image_path('pitch_right_fp.png')}" alt="右齿面fp">
                    <img src="{self._get_image_path('pitch_right_Fp.png')}" alt="右齿面Fp">
                </div>
            </div>
        </div>
        """

    def _render_ripple_analysis(self):
        """渲染波纹度分析"""
        if not self.ripple_results:
            return ""
            
        return f"""
        <div class="section">
            <h2>波纹度分析</h2>
            <div class="grid-container">
                <div class="chart-container">
                    <h3>齿形波纹度</h3>
                    {self._get_chart_html('ripple_profile')}
                </div>
                <div class="chart-container">
                    <h3>齿向波纹度</h3>
                    {self._get_chart_html('ripple_flank')}
                </div>
                <div class="chart-container">
                    <h3>阶次谱分析</h3>
                    {self._get_chart_html('order_profile')}
                    {self._get_chart_html('order_flank')}
                </div>
                <div class="chart-container">
                    <h3>时频瀑布图</h3>
                    {self._get_chart_html('waterfall_profile')}
                    {self._get_chart_html('waterfall_flank')}
                </div>
            </div>
        </div>
        """

    def _render_3d_analysis(self):
        """渲染3D分析"""
        if '3d_surface' not in self.plots:
            return ""
            
        return f"""
        <div class="section">
            <h2>3D表面分析</h2>
            <div class="chart-container">
                <h3>表面形貌</h3>
                {self._get_chart_html('3d_surface')}
            </div>
        </div>
        """

    def _get_chart_html(self, chart_key):
        """获取图表HTML"""
        if chart_key in self.plots and self.plots[chart_key]:
            return f'<img src="{self.plots[chart_key]}" alt="{chart_key}">'
        return ""

    def _get_image_path(self, filename):
        """获取图片路径"""
        return os.path.join(self.img_dir, filename)

    def _create_deviation_plot(self, data_type):
        """创建偏差分析图表"""
        # 实现偏差分析图表生成
        return None

    def _create_pitch_plot(self):
        """创建周节分析图表"""
        # 实现周节分析图表生成
        return None

    def _create_ripple_plot(self, data_type):
        """创建波纹度分析图表"""
        # 实现波纹度分析图表生成
        return None

    def _create_order_spectrum_plot(self, data_type):
        """创建阶次谱图表"""
        # 实现阶次谱图表生成
        return None

    def _create_waterfall_plot(self, data_type):
        """创建瀑布图"""
        # 实现瀑布图生成
        return None

    def _create_3d_plot(self, side, tooth_id):
        """创建3D图表"""
        # 实现3D图表生成
        return None

    def get_first_available_tooth_for_3d(self):
        """获取第一个可用的齿用于3D分析"""
        # 实现获取可用齿的逻辑
        return None, None
