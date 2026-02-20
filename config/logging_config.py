"""
简单的日志配置
"""

import logging

# 创建logger
logger = logging.getLogger('gear_analysis')
logger.setLevel(logging.INFO)

# 创建控制台处理器
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加格式化器到处理器
ch.setFormatter(formatter)

# 添加处理器到logger
logger.addHandler(ch)

# 防止日志重复
logger.propagate = False
