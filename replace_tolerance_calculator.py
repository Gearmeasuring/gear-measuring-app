import re
import os

# 读取文件内容
file_path = '齿轮波纹度软件2_修改版_simplified.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 定义要替换的模式和新内容
pattern = r'def open_tolerance_calculator\(self\):\n        """打开ISO1328公差计算器"""\n        try:\n            dialog = ImageViewerDialog\(self\)\n            dialog\.exec_\(\)\n        except Exception as e:\n            logger\.exception\("Error opening tolerance calculator"\)\n            QMessageBox\.warning\(self, "Error", f"Error opening tolerance calculator: {e}"\)' 

new_method = '''def open_tolerance_calculator(self):
        """打开ISO1328公差计算器"""
        # 使用 ToleranceSettingsDialog 替换原有的 ImageViewerDialog
        try:
            from ui.tolerance_dialog import ToleranceSettingsDialog
            
            # Ensure gear_data is initialized
            if self.gear_data is None:
                self.gear_data = {}
                
            # Sync data from UI tables to gear_data
            if hasattr(self, 'basic_table') and self.basic_table and self.basic_table.rowCount() > 0:
                try:
                    basic_keys = [
                        'program', 'date', 'start_time', 'end_time',
                        'operator', 'location', 'drawing_no', 'order_no', 'type',
                        'customer', 'condition', 'spindle_no', 'purpose', 'accuracy_grade'
                    ]
                    for i, key in enumerate(basic_keys):
                        if i < self.basic_table.rowCount():
                            item = self.basic_table.item(i, 1)
                            if item:
                                self.gear_data[key] = item.text()
                except Exception as e:
                    logger.warning(f"Error syncing params table: {e}")

            dialog = ToleranceSettingsDialog(self.gear_data, self)
            dialog.tolerances_updated.connect(self.update_tolerances)
            dialog.exec_()
        except ImportError as e:
            QMessageBox.warning(self, "Error", f"Could not import ToleranceSettingsDialog: {e}")
        except Exception as e:
            logger.exception("Error opening tolerance calculator")
            QMessageBox.warning(self, "Error", f"Error opening tolerance calculator: {e}")''' 

# 替换内容
new_content = re.sub(pattern, new_method, content)

# 写入文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Successfully updated open_tolerance_calculator method')