"""
应用程序配置和常量
"""

# 数据点配置
class DataPointsConfig:
    """数据点数量配置"""
    EXPECTED_POINTS_915 = 915
    EXPECTED_POINTS_183 = 183
    EXPECTED_POINTS_101 = 101
    SEGMENT_SIZE = 100

# 分析配置
class AnalysisConfig:
    """分析算法配置"""
    DEFAULT_FILTER_ORDER = 4
    DEFAULT_CUTOFF_FREQ = 0.1
    MAX_ORDER_SPECTRUM = 50
    DOMINANT_ORDER_THRESHOLD = 0.1

# ISO1328公差配置
class ToleranceConfig:
    """ISO1328公差计算配置"""
    ACCURACY_GRADES = [5, 6, 7, 8, 9]
    GRADE_FACTORS = {5: 1.0, 6: 1.6, 7: 2.5, 8: 4.0, 9: 6.0}
    
    # 参数范围
    MODULE_RANGE = (0.5, 50.0)
    TEETH_RANGE = (5, 500)
    WIDTH_RANGE = (5, 1000)
    
    # 公差系数
    PROFILE_SLOPE_RATIO = 0.7  # 齿形斜率公差比例
    PROFILE_SHAPE_RATIO = 0.4  # 齿形形状公差比例
    FLANK_SLOPE_RATIO = 0.7    # 齿向斜率公差比例
    FLANK_SHAPE_RATIO = 0.4    # 齿向形状公差比例

# 文件配置
class FileConfig:
    """文件处理配置"""
    SUPPORTED_EXTENSIONS = ['.mka', '.MKA']
    DEFAULT_ENCODING = 'latin-1'
    BACKUP_ENCODING = 'utf-8'
    MAX_FILE_SIZE_MB = 100

# UI配置
class UIConfig:
    """用户界面配置"""
    WINDOW_TITLE = "齿轮波纹度分析软件"
    WINDOW_SIZE = (1400, 900)
    MIN_WINDOW_SIZE = (1024, 768)
    FONT_SIZE = 9
    TABLE_ROW_HEIGHT = 25

# 报告配置
class ReportConfig:
    """报告生成配置"""
    IMAGE_DPI = 300
    IMAGE_FORMAT = 'png'
    PDF_PAGE_SIZE = 'A4'
    IMAGE_DIR_SUFFIX = '_images'
    BACKUP_DIR_SUFFIX = '_PNG备份'

