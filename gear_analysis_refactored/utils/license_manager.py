"""
许可证管理模块
集成USB软件狗验证功能
"""
import logging
from typing import Optional, Tuple
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt

from utils.usb_dongle import USBDongleChecker, SimpleDongleChecker

logger = logging.getLogger(__name__)


class LicenseManager:
    """许可证管理器"""
    
    def __init__(self):
        self.dongle_checker = USBDongleChecker()
        self.license_valid = False
        self.license_info = {}
        
    def check_license(self) -> Tuple[bool, str]:
        """
        检查软件许可证
        
        Returns:
            (是否有效, 消息)
        """
        try:
            # 首先检查USB软件狗
            dongle_detected = self.dongle_checker.check_dongle_available()
            
            if not dongle_detected:
                # 尝试使用简化检测器
                if not SimpleDongleChecker.check_dongle():
                    return False, "未检测到USB软件狗\n\n请确保：\n1. USB软件狗已正确插入\n2. 已安装相应的驱动程序\n3. 软件狗未被其他程序占用"
            
            # 验证授权
            authorized, msg = self.dongle_checker.verify_license()
            
            if authorized:
                self.license_valid = True
                self.license_info = self.dongle_checker.get_dongle_info()
                logger.info("许可证验证成功")
                return True, "许可证验证成功"
            else:
                self.license_valid = False
                return False, msg
                
        except Exception as e:
            logger.error(f"检查许可证时出错: {e}")
            return False, f"许可证检查失败: {str(e)}"
    
    def is_licensed(self) -> bool:
        """检查是否已授权"""
        return self.license_valid
    
    def get_license_info(self) -> dict:
        """获取许可证信息"""
        return self.license_info.copy()


class LicenseDialog(QDialog):
    """许可证验证对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("许可证验证")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.license_manager = LicenseManager()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title_label = QLabel("USB软件狗验证")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # 状态标签
        self.status_label = QLabel("正在检测USB软件狗...")
        self.status_label.setStyleSheet("padding: 10px;")
        layout.addWidget(self.status_label)
        
        # 信息标签
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("padding: 10px; color: #666;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # 按钮
        button_layout = QVBoxLayout()
        
        self.check_button = QPushButton("重新检测")
        self.check_button.clicked.connect(self.check_license)
        button_layout.addWidget(self.check_button)
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setEnabled(False)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("退出")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # 初始检测
        self.check_license()
    
    def check_license(self):
        """检查许可证"""
        self.status_label.setText("正在检测USB软件狗...")
        self.info_label.setText("")
        self.ok_button.setEnabled(False)
        
        valid, msg = self.license_manager.check_license()
        
        if valid:
            self.status_label.setText("✓ 许可证验证成功")
            self.status_label.setStyleSheet("padding: 10px; color: green; font-weight: bold;")
            
            info = self.license_manager.get_license_info()
            if info:
                info_text = "设备信息：\n"
                for key, value in info.items():
                    info_text += f"  {key}: {value}\n"
                self.info_label.setText(info_text)
            
            self.ok_button.setEnabled(True)
        else:
            self.status_label.setText("✗ 许可证验证失败")
            self.status_label.setStyleSheet("padding: 10px; color: red; font-weight: bold;")
            self.info_label.setText(msg)
            self.ok_button.setEnabled(False)


def verify_license_on_startup(parent=None) -> bool:
    """
    程序启动时验证许可证
    
    Args:
        parent: 父窗口
        
    Returns:
        如果验证通过返回True，否则返回False
    """
    manager = LicenseManager()
    valid, msg = manager.check_license()
    
    if not valid:
        # 显示验证对话框
        dialog = LicenseDialog(parent)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            return manager.is_licensed()
        else:
            # 用户选择退出
            if parent:
                QMessageBox.warning(
                    parent,
                    "许可证验证失败",
                    "未检测到有效的USB软件狗，程序将退出。\n\n" + msg
                )
            return False
    
    return True


if __name__ == "__main__":
    # 测试代码
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    dialog = LicenseDialog()
    result = dialog.exec_()
    
    print(f"对话框结果: {result}")
    sys.exit(app.exec_())

