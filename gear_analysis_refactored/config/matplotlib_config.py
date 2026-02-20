"""
Matplotlib配置模块
"""
import matplotlib as mpl
import matplotlib.font_manager as fm
import platform
import logging
import warnings

def setup_matplotlib():
    """
    配置matplotlib的字体和显示设置
    """
    # 设置后端
    mpl.use('Qt5Agg')
    
    # 根据系统类型设置字体
    if platform.system() == 'Windows':
        chinese_fonts = [
            'SimHei',           # 黑体
            'Microsoft YaHei',   # 微软雅黑
            'SimSun',           # 宋体
            'KaiTi',            # 楷体
            'FangSong',         # 仿宋
            'LiSu',             # 隶书
            'YouYuan',          # 幼圆
            'Microsoft JhengHei', # 微软正黑体
            'DengXian',         # 等线
            'NSimSun'           # 新宋体
        ]
    elif platform.system() == 'Darwin':  # macOS
        chinese_fonts = [
            'PingFang SC',      # 苹方
            'Heiti SC',         # 黑体
            'STHeiti',          # 华文黑体
            'Songti SC',        # 宋体
            'Kaiti SC',         # 楷体
            'Arial Unicode MS'
        ]
    else:  # Linux
        chinese_fonts = [
            'DejaVu Sans',
            'WenQuanYi Micro Hei',
            'WenQuanYi Zen Hei',
            'Noto Sans CJK SC',
            'Source Han Sans SC'
        ]
    
    # 设置字体配置
    mpl.rcParams['font.sans-serif'] = chinese_fonts
    mpl.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    mpl.rcParams['figure.max_open_warning'] = 0  # 关闭警告
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['font.size'] = 10
    
    # 设置matplotlib的日志级别，减少字体警告
    matplotlib_logger = logging.getLogger('matplotlib.font_manager')
    matplotlib_logger.setLevel(logging.ERROR)
    
    # 过滤掉字体警告
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib.font_manager')
    warnings.filterwarnings('ignore', category=RuntimeWarning, module='matplotlib.backends.backend_agg')
    
    # 创建字体缺失警告过滤器
    def filter_font_warnings(record):
        message = record.getMessage()
        if 'Glyph' in message and 'missing from current font' in message:
            return False
        return True
    
    # 添加过滤器到matplotlib相关的日志器
    for logger_name in ['matplotlib', 'matplotlib.font_manager', 'matplotlib.backends.backend_agg']:
        font_logger = logging.getLogger(logger_name)
        font_logger.addFilter(filter_font_warnings)
        font_logger.setLevel(logging.ERROR)

# 执行配置
try:
    setup_matplotlib()
except Exception as e:
    print(f"Matplotlib配置警告: {e}")
    # 使用基本配置作为后备
    mpl.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    mpl.rcParams['axes.unicode_minus'] = False

