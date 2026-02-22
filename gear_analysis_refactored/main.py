#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
齿轮分析软件 - 重构版 - 主程序入口

使用方法:
    python main.py
"""

import sys
from PyQt5.QtWidgets import QApplication

# 导入配置模块
from config import setup_logging, setup_matplotlib, logger
from gear_analysis_refactored.config.settings import UIConfig

# 导入主窗口
from ui import GearDataViewer


def main():
    """主程序入口"""
    try:
        print("=" * 60)
        print("齿轮分析软件 - 重构版")
        print("=" * 60)
        
        # 初始化日志
        setup_logging()
        logger.info("程序启动...")
        
        # 初始化matplotlib
        setup_matplotlib()
        logger.info("Matplotlib配置完成")
        
        # 创建Qt应用程序
        app = QApplication(sys.argv)
        
        # 设置应用程序信息
        app.setApplicationName(UIConfig.WINDOW_TITLE)
        app.setApplicationVersion("2.0")
        app.setOrganizationName("齿轮分析团队")
        
        # 设置应用程序样式
        app.setStyle('Fusion')
        
        logger.info("Qt应用程序初始化完成")
        
        # USB软件狗许可证验证
        try:
            from utils.license_manager import verify_license_on_startup
            logger.info("开始验证USB软件狗许可证...")
            
            if not verify_license_on_startup():
                logger.warning("许可证验证失败，程序退出")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    None,
                    "许可证验证失败",
                    "未检测到有效的USB软件狗，程序无法启动。\n\n请确保：\n"
                    "1. USB软件狗已正确插入\n"
                    "2. 已安装相应的驱动程序\n"
                    "3. 软件狗未被其他程序占用"
                )
                return 1
                
            logger.info("许可证验证成功")
        except ImportError as e:
            logger.warning(f"无法导入许可证管理模块: {e}，跳过验证")
        except Exception as e:
            logger.error(f"许可证验证过程出错: {e}")
            # 根据需求决定是否在验证失败时退出
            # 如果希望严格验证，可以取消下面的注释
            # return 1
        
        # 创建并显示主窗口
        logger.info("创建主窗口...")
        main_window = GearDataViewer()
        main_window.show()
        
        logger.info("程序启动完成，进入主循环")
        
        # 运行应用程序
        return app.exec_()
        
    except ImportError as e:
        error_msg = f"导入错误: {e}\n请确保所有依赖模块已正确安装。"
        print(f"错误: {error_msg}")
        if logger:
            logger.error(error_msg)
        return 1
        
    except Exception as e:
        error_msg = f"程序启动失败: {e}"
        print(f"错误: {error_msg}")
        if logger:
            logger.exception("程序启动异常")
        return 1


if __name__ == "__main__":
    sys.exit(main())

