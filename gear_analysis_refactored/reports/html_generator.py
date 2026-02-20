"""
HTML报表生成器
生成格式化的HTML分析报告
"""
import os
from datetime import datetime
from typing import Dict, Any

# 尝试导入logger，如果失败则使用简单的日志记录
try:
    from config.logging_config import logger
except ImportError:
    class SimpleLogger:
        def info(self, msg):
            print(f"INFO: {msg}")
        def warning(self, msg):
            print(f"WARNING: {msg}")
        def error(self, msg, exc_info=False):
            print(f"ERROR: {msg}")
        def debug(self, msg):
            print(f"DEBUG: {msg}")
    logger = SimpleLogger()

# 定义类型别名代替导入
GearMeasurementData = Dict


class HTMLReportGenerator:
    """HTML报表生成器"""
    
    def __init__(self):
        self.output_dir = ""
        self.report_title = "齿轮分析报告"
    
    def generate_report(self, measurement_data: GearMeasurementData, 
                       tolerances: Dict[str, float],
                       output_path: str) -> bool:
        """
        生成完整的HTML报告
        
        Args:
            measurement_data: 测量数据
            tolerances: 公差数据
            output_path: 输出路径
            
        Returns:
            bool: 是否成功
        """
        try:
            html_content = self._generate_html(measurement_data, tolerances)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML报告已生成: {output_path}")
            return True
            
        except Exception as e:
            logger.exception(f"生成HTML报告失败: {e}")
            return False
    
    def _generate_html(self, data: GearMeasurementData, 
                       tolerances: Dict[str, float]) -> str:
        """生成HTML内容"""
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.report_title}</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        {self._generate_header(data)}
        {self._generate_basic_info(data)}
        {self._generate_gear_params(data)}
        {self._generate_tolerance_section(data, tolerances)}
        {self._generate_data_summary(data)}
        {self._generate_footer()}
    </div>
</body>
</html>
"""
        return html
    
    def _get_css_styles(self) -> str:
        """获取CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 20px auto;
            background: white;
            padding: 30px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            color: #7f8c8d;
            font-size: 16px;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            background-color: #34495e;
            color: white;
            padding: 10px 15px;
            font-size: 18px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        th {
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #ecf0f1;
        }
        
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        tr:hover {
            background-color: #e8f4f8;
        }
        
        .footer {
            text-align: center;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 14px;
        }
        
        .highlight {
            background-color: #fff9c4;
            font-weight: bold;
        }
        
        .success {
            color: #27ae60;
            font-weight: bold;
        }
        
        .warning {
            color: #f39c12;
            font-weight: bold;
        }
        
        .error {
            color: #e74c3c;
            font-weight: bold;
        }
        """
    
    def _generate_header(self, data: GearMeasurementData) -> str:
        """生成报告头部"""
        return f"""
        <div class="header">
            <h1>📊 {self.report_title}</h1>
            <div class="subtitle">
                齿轮分析软件 - 重构版<br>
                生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
        """
    
    def _generate_basic_info(self, data: GearMeasurementData) -> str:
        """生成基本信息部分"""
        info = data.basic_info
        
        return f"""
        <div class="section">
            <div class="section-title">📄 基本信息</div>
            <table>
                <tr>
                    <th style="width: 30%">项目</th>
                    <th>值</th>
                </tr>
                <tr><td>程序名称</td><td>{info.program}</td></tr>
                <tr><td>测量日期</td><td>{info.date}</td></tr>
                <tr><td>开始时间</td><td>{info.start_time}</td></tr>
                <tr><td>结束时间</td><td>{info.end_time}</td></tr>
                <tr><td>操作员</td><td>{info.operator}</td></tr>
                <tr><td>位置</td><td>{info.location}</td></tr>
                <tr><td>图号</td><td>{info.drawing_no}</td></tr>
                <tr><td>订单号</td><td>{info.order_no}</td></tr>
                <tr><td>客户</td><td>{info.customer}</td></tr>
            </table>
        </div>
        """
    
    def _generate_gear_params(self, data: GearMeasurementData) -> str:
        """生成齿轮参数部分"""
        info = data.basic_info
        
        return f"""
        <div class="section">
            <div class="section-title">⚙️ 齿轮参数</div>
            <table>
                <tr>
                    <th style="width: 30%">参数</th>
                    <th>值</th>
                </tr>
                <tr><td>模数</td><td class="highlight">{info.module:.3f} mm</td></tr>
                <tr><td>齿数</td><td class="highlight">{info.teeth}</td></tr>
                <tr><td>螺旋角</td><td>{info.helix_angle:.2f}°</td></tr>
                <tr><td>压力角</td><td>{info.pressure_angle:.2f}°</td></tr>
                <tr><td>变位系数</td><td>{info.modification_coeff:.4f}</td></tr>
                <tr><td>齿宽</td><td>{info.width:.2f} mm</td></tr>
                <tr><td>齿顶圆直径</td><td>{info.tip_diameter:.3f} mm</td></tr>
                <tr><td>齿根圆直径</td><td>{info.root_diameter:.3f} mm</td></tr>
                <tr><td>精度等级</td><td class="highlight">{info.accuracy_grade}级</td></tr>
            </table>
        </div>
        """
    
    def _generate_tolerance_section(self, data: GearMeasurementData, 
                                    tolerances: Dict[str, float]) -> str:
        """生成公差分析部分"""
        return f"""
        <div class="section">
            <div class="section-title">📋 ISO1328公差分析</div>
            <table>
                <tr>
                    <th style="width: 40%">公差项目</th>
                    <th>计算值 (μm)</th>
                    <th>状态</th>
                </tr>
                <tr>
                    <td><b>齿形公差 F<sub>α</sub></b></td>
                    <td class="highlight">{tolerances.get('F_alpha', 0):.2f}</td>
                    <td class="success">✓ 计算完成</td>
                </tr>
                <tr>
                    <td>齿形斜率公差 fH<sub>α</sub></td>
                    <td>{tolerances.get('fH_alpha', 0):.2f}</td>
                    <td class="success">✓ 计算完成</td>
                </tr>
                <tr>
                    <td>齿形形状公差 ff<sub>α</sub></td>
                    <td>{tolerances.get('ff_alpha', 0):.2f}</td>
                    <td class="success">✓ 计算完成</td>
                </tr>
                <tr>
                    <td><b>齿向公差 F<sub>β</sub></b></td>
                    <td class="highlight">{tolerances.get('F_beta', 0):.2f}</td>
                    <td class="success">✓ 计算完成</td>
                </tr>
                <tr>
                    <td>齿向斜率公差 fH<sub>β</sub></td>
                    <td>{tolerances.get('fH_beta', 0):.2f}</td>
                    <td class="success">✓ 计算完成</td>
                </tr>
                <tr>
                    <td>齿向形状公差 ff<sub>β</sub></td>
                    <td>{tolerances.get('ff_beta', 0):.2f}</td>
                    <td class="success">✓ 计算完成</td>
                </tr>
            </table>
        </div>
        """
    
    def _generate_data_summary(self, data: GearMeasurementData) -> str:
        """生成数据摘要部分"""
        profile = data.profile_data
        flank = data.flank_data
        
        return f"""
        <div class="section">
            <div class="section-title">📊 数据摘要</div>
            <table>
                <tr>
                    <th>数据类型</th>
                    <th>左侧齿数</th>
                    <th>右侧齿数</th>
                    <th>状态</th>
                </tr>
                <tr>
                    <td>齿形数据</td>
                    <td>{len(profile.left)}</td>
                    <td>{len(profile.right)}</td>
                    <td class="{'success' if data.has_profile_data() else 'warning'}">
                        {'✓ 有数据' if data.has_profile_data() else '⚠ 无数据'}
                    </td>
                </tr>
                <tr>
                    <td>齿向数据</td>
                    <td>{len(flank.left)}</td>
                    <td>{len(flank.right)}</td>
                    <td class="{'success' if data.has_flank_data() else 'warning'}">
                        {'✓ 有数据' if data.has_flank_data() else '⚠ 无数据'}
                    </td>
                </tr>
            </table>
        </div>
        """
    
    def _generate_footer(self) -> str:
        """生成报告尾部"""
        return f"""
        <div class="footer">
            <p>本报告由齿轮分析软件自动生成</p>
            <p>版本: 2.0 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """


def generate_html_report(measurement_data: GearMeasurementData,
                        tolerances: Dict[str, float],
                        output_path: str) -> bool:
    """
    生成HTML报告的便捷函数
    
    Args:
        measurement_data: 测量数据
        tolerances: 公差数据
        output_path: 输出路径
        
    Returns:
        bool: 是否成功
    """
    generator = HTMLReportGenerator()
    return generator.generate_report(measurement_data, tolerances, output_path)

