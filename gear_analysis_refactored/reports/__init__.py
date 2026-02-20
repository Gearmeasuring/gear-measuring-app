"""报告生成模块"""
from .html_generator import HTMLReportGenerator, generate_html_report
# 暂时注释掉导入klingelnberg_matplotlib，避免导入models模块的错误
# from .klingelnberg_matplotlib import KlingelnbergMatplotlibReport, generate_klingelnberg_matplotlib_report
from .klingelnberg_exact import generate_klingelnberg_exact_report
from .klingelnberg_single_page import KlingelnbergSinglePageReport

__all__ = [
    'HTMLReportGenerator', 'generate_html_report',
    # 'KlingelnbergMatplotlibReport', 'generate_klingelnberg_matplotlib_report',
    'generate_klingelnberg_exact_report', 'KlingelnbergSinglePageReport'
]
