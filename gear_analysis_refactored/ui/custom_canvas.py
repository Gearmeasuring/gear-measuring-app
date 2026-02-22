"""
自定义画布类
提供右键菜单、保存、打印等功能
"""
import os
from PyQt5.QtWidgets import QMenu, QAction, QMessageBox, QFileDialog, QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from gear_analysis_refactored.config.logging_config import logger


class CustomFigureCanvas(FigureCanvas):
    """自定义Matplotlib画布，支持右键菜单、保存、打印等功能"""
    
    def __init__(self, figure, parent=None):
        super().__init__(figure)
        self.parent = parent
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        context_menu = QMenu(self)
        
        # 添加保存图片动作
        save_action = QAction("保存图片", self)
        save_action.triggered.connect(self.save_figure)
        context_menu.addAction(save_action)
        
        # 添加复制到剪贴板动作
        copy_action = QAction("复制到剪贴板", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        context_menu.addAction(copy_action)
        
        context_menu.addSeparator()
        
        # 添加打印预览动作
        preview_action = QAction("打印预览", self)
        preview_action.triggered.connect(self.print_preview)
        context_menu.addAction(preview_action)
        
        # 添加打印动作
        print_action = QAction("打印", self)
        print_action.triggered.connect(self.print_figure)
        context_menu.addAction(print_action)
        
        # 显示菜单
        context_menu.exec_(self.mapToGlobal(position))
    
    def save_figure(self):
        """保存图片"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存图片", "", 
            "PNG文件 (*.png);;JPEG文件 (*.jpg);;PDF文件 (*.pdf);;SVG文件 (*.svg)"
        )
        
        if not file_path:
            return
        
        try:
            # 确保文件扩展名正确
            if not file_path.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.svg')):
                file_path += '.png'
            
            # 创建目录（如果不存在）
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # 使用截图方法保存（更可靠）
            try:
                pixmap = self.grab()
                if pixmap.save(file_path):
                    logger.info(f"图片保存成功: {file_path}")
                    QMessageBox.information(self, "保存成功", 
                        f"图片已保存到:\n{file_path}\n大小: {os.path.getsize(file_path)} 字节")
                else:
                    raise Exception("截图保存失败")
            except Exception as e:
                # 备用方法：使用matplotlib保存
                logger.warning(f"截图保存失败，尝试matplotlib保存: {e}")
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                logger.info(f"Matplotlib保存成功: {file_path}")
                QMessageBox.information(self, "保存成功", f"图片已保存到:\n{file_path}")
                
        except Exception as e:
            logger.exception(f"保存图片失败: {e}")
            QMessageBox.critical(self, "保存错误", f"保存失败: {str(e)}")
    
    def copy_to_clipboard(self):
        """复制图表到剪贴板"""
        try:
            import tempfile
            from PyQt5.QtWidgets import QApplication
            
            # 保存为临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_file.close()
            
            # 保存图片
            self.figure.savefig(temp_file.name, dpi=150, bbox_inches='tight')
            
            # 复制到剪贴板
            pixmap = QPixmap(temp_file.name)
            QApplication.clipboard().setPixmap(pixmap)
            
            # 清理临时文件
            os.unlink(temp_file.name)
            
            logger.info("图表已复制到剪贴板")
            QMessageBox.information(self, "复制成功", "图表已复制到剪贴板")
            
        except Exception as e:
            logger.exception(f"复制到剪贴板失败: {e}")
            QMessageBox.critical(self, "复制失败", f"复制到剪贴板失败: {str(e)}")
    
    def print_preview(self):
        """打印预览"""
        QMessageBox.information(self, "打印预览", 
                              "打印预览功能在当前环境中不可用。\n\n"
                              "替代方案：\n"
                              "1. 使用'保存图片'功能保存图表\n"
                              "2. 用图片查看器打开保存的文件\n"
                              "3. 使用Ctrl+P进行打印\n\n"
                              "这样可以获得更好的打印质量和更多控制选项。")
    
    def print_figure(self):
        """打印图表"""
        try:
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec_() == QDialog.Accepted:
                # 提供保存选项，避免打印兼容性问题
                reply = QMessageBox.question(self, "打印", 
                                           "由于matplotlib版本兼容性问题，建议使用保存图片功能。\n\n"
                                           "是否要保存图片文件进行打印？",
                                           QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.save_figure()
                        
        except ImportError:
            self.print_preview()
        except Exception as e:
            logger.exception(f"打印失败: {e}")
            error_msg = f"打印失败: {str(e)}"
            if "dpi" in str(e).lower():
                error_msg = "打印失败: matplotlib版本兼容性问题，请使用保存图片功能"
            QMessageBox.critical(self, "错误", error_msg)
            self.print_preview()
