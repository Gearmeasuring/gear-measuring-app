"""
日志配置模块
"""
import logging
import os

# 全局logger实例
logger = None

def setup_logging(log_file='gear_viewer.log', level=logging.DEBUG):
    """
    配置日志系统
    
    Args:
        log_file: 日志文件路径
        level: 日志级别
    
    Returns:
        logging.Logger: 配置好的logger实例
    """
    global logger
    
    # 创建logger
    logger = logging.getLogger('GearDataViewer')
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建文件处理器
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
    except TypeError:
        file_handler = logging.FileHandler(log_file)
        file_handler.encoding = 'utf-8'
    
    file_handler.setLevel(logging.DEBUG)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化logger
if logger is None:
    logger = setup_logging()

