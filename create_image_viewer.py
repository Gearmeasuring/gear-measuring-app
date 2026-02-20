import re
import os

file_path = r'e:\python\gear measuring software - 20251217\齿轮波纹度软件2_修改版_simplified.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 创建一个新的ImageViewerDialog类
image_viewer_class = '''class ImageViewerDialog(QDialog):
    """图片查看器对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ISO1328 公差设置")
        self.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 创建图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 添加滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # 加载并显示图片
        self.load_image()

        # 按钮框
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_image(self):
        """加载图片"""
        try:
            # 使用示例图片路径（请替换为实际图片路径）
            # 这里假设图片文件名为 "iso1328_tolerance_settings.png"，位于当前目录
            image_path = "iso1328_tolerance_settings.png"
            
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    self.image_label.setPixmap(pixmap)
                    self.image_label.setScaledContents(True)
                else:
                    self.image_label.setText("无法加载图片")
            else:
                self.image_label.setText(f"图片文件不存在: {image_path}")
        except Exception as e:
            self.image_label.setText(f"加载图片错误: {str(e)}")
'''

# 2. 在ToleranceCalculatorDialog类之前插入ImageViewerDialog类
insert_pos = content.find('class ToleranceCalculatorDialog(QDialog):')
if insert_pos != -1:
    content = content[:insert_pos] + image_viewer_class + '\n\n' + content[insert_pos:]

# 3. 修改open_tolerance_calculator方法
content = re.sub(r'def open_tolerance_calculator\(self\):\n        """打开ISO1328公差计算器"""\n        try:\n            dialog = ToleranceCalculatorDialog\(self\)\n            dialog\.exec_\(\)\n        except Exception as e:\n            logger\.exception\("Error opening tolerance calculator"\)\n            QMessageBox\.warning\(self, "Error", f"Error opening tolerance calculator: {e}"\)', 
                'def open_tolerance_calculator(self):\n        """打开ISO1328公差计算器"""\n        try:\n            dialog = ImageViewerDialog(self)\n            dialog.exec_()\n        except Exception as e:\n            logger.exception("Error opening tolerance calculator")\n            QMessageBox.warning(self, "Error", f"Error opening tolerance calculator: {e}")', 
                content)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Successfully created ImageViewerDialog and updated open_tolerance_calculator method')
