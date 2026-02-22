"""
高级对话框模块
包含阶次分析滤波器对话框等高级对话框
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QLabel, QDialogButtonBox, QDoubleSpinBox, QSpinBox,
    QCheckBox, QTextEdit, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from gear_analysis_refactored.config.logging_config import logger


class OrderAnalysisFilterDialog(QDialog):
    """阶次分析滤波设置对话框"""
    
    def __init__(self, parent=None, analysis_type="专业阶次分析"):
        super().__init__(parent)
        self.analysis_type = analysis_type
        self.setWindowTitle(f"{analysis_type}滤波设置")
        self.setGeometry(300, 300, 600, 700)
        self.setMinimumSize(500, 600)
        
        # 初始化滤波参数
        self.filter_params = {
            'filter_type': '无滤波',
            'lowpass_freq': 1.0,
            'highpass_freq': 0.01,
            'bandpass_low': 0.1,
            'bandpass_high': 5.0,
            'filter_order': 4,
            'window_type': '汉宁窗',
            'custom_filter': ''
        }
        
        # 设置UI
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI控件"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 1. 滤波器设置标签页
        filter_tab = QWidget()
        filter_layout = QVBoxLayout(filter_tab)
        
        # 滤波器类型
        filter_group = QGroupBox("滤波器类型")
        filter_form = QFormLayout()
        
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["无滤波", "低通滤波", "高通滤波", "带通滤波", "自定义"])
        self.filter_type_combo.currentTextChanged.connect(self.on_filter_type_changed)
        filter_form.addRow("滤波器类型:", self.filter_type_combo)
        
        # 低通频率
        self.lowpass_spin = QDoubleSpinBox()
        self.lowpass_spin.setRange(0.01, 100.0)
        self.lowpass_spin.setValue(1.0)
        self.lowpass_spin.setSuffix(" Hz")
        self.lowpass_spin.setDecimals(2)
        filter_form.addRow("低通截止频率:", self.lowpass_spin)
        
        # 高通频率
        self.highpass_spin = QDoubleSpinBox()
        self.highpass_spin.setRange(0.001, 10.0)
        self.highpass_spin.setValue(0.01)
        self.highpass_spin.setSuffix(" Hz")
        self.highpass_spin.setDecimals(3)
        filter_form.addRow("高通截止频率:", self.highpass_spin)
        
        # 带通低频
        self.bandpass_low_spin = QDoubleSpinBox()
        self.bandpass_low_spin.setRange(0.01, 50.0)
        self.bandpass_low_spin.setValue(0.1)
        self.bandpass_low_spin.setSuffix(" Hz")
        self.bandpass_low_spin.setDecimals(2)
        filter_form.addRow("带通低频:", self.bandpass_low_spin)
        
        # 带通高频
        self.bandpass_high_spin = QDoubleSpinBox()
        self.bandpass_high_spin.setRange(0.1, 100.0)
        self.bandpass_high_spin.setValue(5.0)
        self.bandpass_high_spin.setSuffix(" Hz")
        self.bandpass_high_spin.setDecimals(2)
        filter_form.addRow("带通高频:", self.bandpass_high_spin)
        
        # 滤波器阶数
        self.filter_order_spin = QSpinBox()
        self.filter_order_spin.setRange(1, 10)
        self.filter_order_spin.setValue(4)
        filter_form.addRow("滤波器阶数:", self.filter_order_spin)
        
        filter_group.setLayout(filter_form)
        filter_layout.addWidget(filter_group)
        
        # 2. 窗口函数设置
        window_group = QGroupBox("窗口函数")
        window_form = QFormLayout()
        
        self.window_type_combo = QComboBox()
        self.window_type_combo.addItems([
            "汉宁窗", "汉明窗", "布莱克曼窗", "矩形窗", "三角窗", "巴特利特窗"
        ])
        window_form.addRow("窗口类型:", self.window_type_combo)
        
        window_group.setLayout(window_form)
        filter_layout.addWidget(window_group)
        
        # 3. 自定义滤波器
        custom_group = QGroupBox("自定义滤波器")
        custom_layout = QVBoxLayout()
        
        self.custom_filter_text = QTextEdit()
        self.custom_filter_text.setPlaceholderText("输入自定义滤波器参数（高级用户）")
        self.custom_filter_text.setMaximumHeight(100)
        custom_layout.addWidget(self.custom_filter_text)
        
        custom_group.setLayout(custom_layout)
        filter_layout.addWidget(custom_group)
        
        filter_layout.addStretch()
        tab_widget.addTab(filter_tab, "滤波器设置")
        
        # 2. 说明标签页
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>滤波器说明</h2>
        <h3>1. 无滤波</h3>
        <p>不对数据进行滤波处理，直接使用原始数据进行分析。</p>
        
        <h3>2. 低通滤波</h3>
        <p>去除高频噪声，保留低频成分。适用于去除测量噪声。</p>
        <p><b>参数</b>: 截止频率决定保留的频率上限。</p>
        
        <h3>3. 高通滤波</h3>
        <p>去除低频趋势，保留高频成分。适用于去除基准偏差。</p>
        <p><b>参数</b>: 截止频率决定去除的频率下限。</p>
        
        <h3>4. 带通滤波</h3>
        <p>只保留特定频率范围的成分，适用于提取特定波纹特征。</p>
        <p><b>参数</b>: 低频和高频截止频率决定保留的频率范围。</p>
        
        <h3>5. 窗口函数</h3>
        <ul>
            <li><b>汉宁窗</b>: 平滑过渡，适合大多数情况</li>
            <li><b>汉明窗</b>: 更好的旁瓣抑制</li>
            <li><b>布莱克曼窗</b>: 最佳旁瓣抑制，但主瓣较宽</li>
        </ul>
        
        <h3>推荐设置</h3>
        <p><b>精密齿轮</b>: 带通滤波 [0.1, 5.0] Hz, 4阶, 汉宁窗</p>
        <p><b>普通齿轮</b>: 低通滤波 1.0 Hz, 2阶, 汉宁窗</p>
        """)
        help_layout.addWidget(help_text)
        
        tab_widget.addTab(help_tab, "帮助说明")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)
        layout.addWidget(button_box)
    
    def on_filter_type_changed(self, filter_type):
        """滤波器类型变化时更新UI"""
        # 禁用/启用相关控件
        self.lowpass_spin.setEnabled(filter_type in ["低通滤波", "带通滤波"])
        self.highpass_spin.setEnabled(filter_type in ["高通滤波", "带通滤波"])
        self.bandpass_low_spin.setEnabled(filter_type == "带通滤波")
        self.bandpass_high_spin.setEnabled(filter_type == "带通滤波")
        self.custom_filter_text.setEnabled(filter_type == "自定义")
    
    def restore_defaults(self):
        """恢复默认设置"""
        self.filter_type_combo.setCurrentText("无滤波")
        self.lowpass_spin.setValue(1.0)
        self.highpass_spin.setValue(0.01)
        self.bandpass_low_spin.setValue(0.1)
        self.bandpass_high_spin.setValue(5.0)
        self.filter_order_spin.setValue(4)
        self.window_type_combo.setCurrentText("汉宁窗")
        self.custom_filter_text.clear()
    
    def get_filter_params(self):
        """获取滤波器参数"""
        return {
            'filter_type': self.filter_type_combo.currentText(),
            'lowpass_freq': self.lowpass_spin.value(),
            'highpass_freq': self.highpass_spin.value(),
            'bandpass_low': self.bandpass_low_spin.value(),
            'bandpass_high': self.bandpass_high_spin.value(),
            'filter_order': self.filter_order_spin.value(),
            'window_type': self.window_type_combo.currentText(),
            'custom_filter': self.custom_filter_text.toPlainText()
        }
    
    def load_filter_params(self, params):
        """加载滤波器参数"""
        try:
            self.filter_type_combo.setCurrentText(params.get('filter_type', '无滤波'))
            self.lowpass_spin.setValue(params.get('lowpass_freq', 1.0))
            self.highpass_spin.setValue(params.get('highpass_freq', 0.01))
            self.bandpass_low_spin.setValue(params.get('bandpass_low', 0.1))
            self.bandpass_high_spin.setValue(params.get('bandpass_high', 5.0))
            self.filter_order_spin.setValue(params.get('filter_order', 4))
            self.window_type_combo.setCurrentText(params.get('window_type', '汉宁窗'))
            self.custom_filter_text.setPlainText(params.get('custom_filter', ''))
        except Exception as e:
            logger.error(f"加载滤波参数失败: {e}")

