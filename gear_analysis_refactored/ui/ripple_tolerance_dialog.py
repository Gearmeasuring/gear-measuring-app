"""
波纹度公差设置对话框
用于设置波纹度频谱图的公差曲线参数
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
                             QStackedWidget, QWidget, QLabel, QLineEdit, QPushButton,
                             QCheckBox, QGroupBox, QGridLayout, QDoubleSpinBox, QMessageBox,
                             QSplitter, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QShowEvent


class RippleToleranceDialog(QDialog):
    """波纹度公差设置对话框"""
    
    settings_updated = pyqtSignal(dict)  # 设置更新信号
    
    def __init__(self, measurement_data=None, parent=None):
        super().__init__(parent)
        self.measurement_data = measurement_data
        self.setWindowTitle("设置 - 波纹度")
        self.resize(900, 800)  # 增加初始高度，确保有足够空间
        self.setMinimumSize(700, 600)  # 设置最小尺寸，确保对话框不会太小
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 使用垂直分割器实现可调整大小的上下分割
        vertical_splitter = QSplitter(Qt.Vertical)
        
        # 上半部分：使用水平分割器实现可调整大小的左右分割
        horizontal_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：树形菜单（包装在滚动区域中）
        tree_scroll = QScrollArea()
        tree_scroll.setWidgetResizable(True)
        tree_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tree_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("设置")
        self.tree_widget.setMinimumWidth(180)
        # 移除最大宽度限制，允许手动调整到50%
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        tree_scroll.setWidget(self.tree_widget)
        horizontal_splitter.addWidget(tree_scroll)
        
        # 填充树形菜单
        self.populate_tree()
        
        # 右侧：内容区域（包装在滚动区域中）
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)  # 保持True，让内容可以适应滚动区域
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content_scroll.setMinimumWidth(300)  # 设置最小宽度，确保内容区域有足够空间
        self.content_stack = QStackedWidget()
        self.content_stack.setMinimumWidth(300)  # 设置内容栈的最小宽度
        # 设置内容栈的大小策略，确保内容可以完整显示
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        content_scroll.setWidget(self.content_stack)
        horizontal_splitter.addWidget(content_scroll)
        
        # 设置水平分割器为可手动调节，初始位置为50%
        # 使用相等的stretch factor，让两侧都可以拉伸
        horizontal_splitter.setStretchFactor(0, 1)  # 左侧可以拉伸
        horizontal_splitter.setStretchFactor(1, 1)  # 右侧可以拉伸
        # 初始大小设置为50%:50%（在showEvent中设置会更准确）
        # 先设置一个临时值，showEvent中会重新设置为50%
        horizontal_splitter.setSizes([400, 400])
        
        # 将水平分割器添加到垂直分割器的上半部分
        vertical_splitter.addWidget(horizontal_splitter)
        
        # 保存水平splitter引用以便后续使用
        self.splitter = horizontal_splitter
        self._splitter_initialized = False  # 标记是否已初始化分割器位置
        
        # 创建页面
        self.create_tolerance_page()
        self.create_pitch_ripple_page()
        self.content_stack.setCurrentIndex(0)
        
        # 下半部分：底部按钮区域
        button_widget = QWidget()
        button_widget.setMinimumHeight(100)  # 设置按钮区域最小高度，确保所有内容完全可见
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(10, 10, 10, 10)
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self.apply_settings)
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept_and_save)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        # 将按钮区域添加到垂直分割器的下半部分
        vertical_splitter.addWidget(button_widget)
        
        # 设置垂直分割器：内容区域可拉伸，按钮区域固定高度
        vertical_splitter.setStretchFactor(0, 1)  # 上半部分（内容）可以拉伸
        vertical_splitter.setStretchFactor(1, 0)  # 下半部分（按钮）不拉伸，保持固定
        # 初始大小：内容区域占大部分，按钮区域有足够空间（确保所有内容完全可见）
        vertical_splitter.setSizes([500, 120])  # 内容500，按钮120
        
        # 将垂直分割器添加到主布局
        main_layout.addWidget(vertical_splitter)
        
        # 保存垂直splitter引用
        self.vertical_splitter = vertical_splitter
        self._vertical_splitter_initialized = False  # 标记是否已初始化垂直分割器位置
        
    def populate_tree(self):
        """填充树形菜单"""
        self.tree_widget.clear()
        
        # 根节点
        root = QTreeWidgetItem(self.tree_widget, ["波纹度设置"])
        root.setExpanded(True)
        
        # 公差节点
        tolerance_item = QTreeWidgetItem(root, ["公差"])
        tolerance_item.setData(0, Qt.UserRole, "tolerance")
        
        # 周节波纹度节点
        pitch_ripple_item = QTreeWidgetItem(root, ["周节波纹度"])
        pitch_ripple_item.setData(0, Qt.UserRole, "pitch_ripple")
        
        self.tree_widget.expandAll()
        
    def on_tree_item_clicked(self, item, column):
        """树形菜单项点击事件"""
        page_id = item.data(0, Qt.UserRole)
        if page_id == "tolerance":
            self.content_stack.setCurrentIndex(0)
        elif page_id == "pitch_ripple":
            self.content_stack.setCurrentIndex(1)
            
    def create_tolerance_page(self):
        """创建公差设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        
        # 公差元素组
        tolerance_elements_group = QGroupBox("公差元素")
        tolerance_elements_layout = QVBoxLayout()
        
        # 应用复选框
        application_layout = QHBoxLayout()
        application_label = QLabel("应用:")
        self.left_checkbox = QCheckBox("左")
        self.right_checkbox = QCheckBox("右")
        self.sector_checkbox = QCheckBox("扇形")
        self.radial_checkbox = QCheckBox("径向")
        self.circumferential_checkbox = QCheckBox("周节")
        
        application_layout.addWidget(application_label)
        application_layout.addWidget(self.left_checkbox)
        application_layout.addWidget(self.right_checkbox)
        application_layout.addWidget(self.sector_checkbox)
        application_layout.addWidget(self.radial_checkbox)
        application_layout.addWidget(self.circumferential_checkbox)
        application_layout.addStretch()
        tolerance_elements_layout.addLayout(application_layout)
        
        # 公差激活复选框
        self.tolerance_activation_checkbox = QCheckBox("公差激活")
        tolerance_elements_layout.addWidget(self.tolerance_activation_checkbox)
        
        # 公差曲线组
        tolerance_curve_group = QGroupBox("公差曲线")
        tolerance_curve_layout = QGridLayout()
        
        # R参数
        r_label = QLabel("R:")
        self.r_spinbox = QDoubleSpinBox()
        self.r_spinbox.setRange(-100.0, 100.0)
        self.r_spinbox.setDecimals(2)
        self.r_spinbox.setSingleStep(0.1)
        self.r_spinbox.setSuffix(" μm")
        tolerance_curve_layout.addWidget(r_label, 0, 0)
        tolerance_curve_layout.addWidget(self.r_spinbox, 0, 1)
        
        # N0参数
        n0_label = QLabel("N0:")
        self.n0_spinbox = QDoubleSpinBox()
        self.n0_spinbox.setRange(-100.0, 100.0)
        self.n0_spinbox.setDecimals(2)
        self.n0_spinbox.setSingleStep(0.1)
        tolerance_curve_layout.addWidget(n0_label, 1, 0)
        tolerance_curve_layout.addWidget(self.n0_spinbox, 1, 1)
        
        # K参数
        k_label = QLabel("K:")
        self.k_spinbox = QDoubleSpinBox()
        self.k_spinbox.setRange(-100.0, 100.0)
        self.k_spinbox.setDecimals(2)
        self.k_spinbox.setSingleStep(0.1)
        tolerance_curve_layout.addWidget(k_label, 2, 0)
        tolerance_curve_layout.addWidget(self.k_spinbox, 2, 1)
        
        # 公差公式按钮
        formula_btn = QPushButton("公差公式")
        formula_btn.clicked.connect(self.show_tolerance_formula)
        tolerance_curve_layout.addWidget(formula_btn, 3, 0, 1, 2)
        
        tolerance_curve_group.setLayout(tolerance_curve_layout)
        tolerance_elements_layout.addWidget(tolerance_curve_group)
        
        tolerance_elements_group.setLayout(tolerance_elements_layout)
        layout.addWidget(tolerance_elements_group)
        
        # 显示组
        display_group = QGroupBox("显示")
        display_layout = QVBoxLayout()
        
        # 绘制公差元素复选框
        self.draw_tolerance_checkbox = QCheckBox("绘制公差元素")
        self.draw_tolerance_checkbox.setChecked(True)  # 默认选中
        display_layout.addWidget(self.draw_tolerance_checkbox)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # 添加说明文本
        info_label = QLabel("说明：公差 = R / (O-1)^N，其中 N = N0 + K / O，O = 阶次")
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        info_label.setWordWrap(True)  # 允许文本换行
        layout.addWidget(info_label)
        
        # 移除addStretch，让内容自然显示，不需要拉伸
        # layout.addStretch()
        self.content_stack.addWidget(page)
        
    def create_pitch_ripple_page(self):
        """创建周节波纹度公差设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        
        # 公差元素组
        tolerance_elements_group = QGroupBox("公差元素")
        tolerance_elements_layout = QVBoxLayout()
        
        # 应用复选框
        application_layout = QHBoxLayout()
        application_label = QLabel("应用:")
        self.pitch_left_checkbox = QCheckBox("左")
        self.pitch_right_checkbox = QCheckBox("右")
        
        application_layout.addWidget(application_label)
        application_layout.addWidget(self.pitch_left_checkbox)
        application_layout.addWidget(self.pitch_right_checkbox)
        application_layout.addStretch()
        tolerance_elements_layout.addLayout(application_layout)
        
        # 公差激活复选框
        self.pitch_tolerance_activation_checkbox = QCheckBox("公差激活")
        tolerance_elements_layout.addWidget(self.pitch_tolerance_activation_checkbox)
        
        # 公差曲线组
        tolerance_curve_group = QGroupBox("公差曲线")
        tolerance_curve_layout = QGridLayout()
        
        # R参数
        r_label = QLabel("R:")
        self.pitch_r_spinbox = QDoubleSpinBox()
        self.pitch_r_spinbox.setRange(-100.0, 100.0)
        self.pitch_r_spinbox.setDecimals(2)
        self.pitch_r_spinbox.setSingleStep(0.1)
        self.pitch_r_spinbox.setSuffix(" μm")
        tolerance_curve_layout.addWidget(r_label, 0, 0)
        tolerance_curve_layout.addWidget(self.pitch_r_spinbox, 0, 1)
        
        # N0参数
        n0_label = QLabel("N0:")
        self.pitch_n0_spinbox = QDoubleSpinBox()
        self.pitch_n0_spinbox.setRange(-100.0, 100.0)
        self.pitch_n0_spinbox.setDecimals(2)
        self.pitch_n0_spinbox.setSingleStep(0.1)
        tolerance_curve_layout.addWidget(n0_label, 1, 0)
        tolerance_curve_layout.addWidget(self.pitch_n0_spinbox, 1, 1)
        
        # K参数
        k_label = QLabel("K:")
        self.pitch_k_spinbox = QDoubleSpinBox()
        self.pitch_k_spinbox.setRange(-100.0, 100.0)
        self.pitch_k_spinbox.setDecimals(2)
        self.pitch_k_spinbox.setSingleStep(0.1)
        tolerance_curve_layout.addWidget(k_label, 2, 0)
        tolerance_curve_layout.addWidget(self.pitch_k_spinbox, 2, 1)
        
        # 公差公式按钮
        formula_btn = QPushButton("公差公式")
        formula_btn.clicked.connect(self.show_tolerance_formula)
        tolerance_curve_layout.addWidget(formula_btn, 3, 0, 1, 2)
        
        tolerance_curve_group.setLayout(tolerance_curve_layout)
        tolerance_elements_layout.addWidget(tolerance_curve_group)
        
        tolerance_elements_group.setLayout(tolerance_elements_layout)
        layout.addWidget(tolerance_elements_group)
        
        # 显示组
        display_group = QGroupBox("显示")
        display_layout = QVBoxLayout()
        
        # 绘制公差元素复选框
        self.pitch_draw_tolerance_checkbox = QCheckBox("绘制公差元素")
        self.pitch_draw_tolerance_checkbox.setChecked(True)  # 默认选中
        display_layout.addWidget(self.pitch_draw_tolerance_checkbox)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # 添加说明文本
        info_label = QLabel("说明：公差 = R / (O-1)^N，其中 N = N0 + K / O，O = 阶次")
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        info_label.setWordWrap(True)  # 允许文本换行
        layout.addWidget(info_label)
        
        # 移除addStretch，让内容自然显示，不需要拉伸
        # layout.addStretch()
        self.content_stack.addWidget(page)
        
    def show_tolerance_formula(self):
        """显示公差公式说明"""
        formula_text = """
公差曲线公式说明：

公差 = R / (O-1)^N

其中：
  N = N0 + K / O
  O = 阶次

参数说明：
  R: 允许波深（当 R < 0 时不显示公差曲线）
  N0: 用于描述公差曲线的常数
  K: 修正值

默认值：
  R = 2.0 μm
  N0 = 1.0
  K = 0.0
        """
        QMessageBox.information(self, "公差公式", formula_text.strip())
        
    def load_settings(self):
        """加载设置"""
        if self.measurement_data and hasattr(self.measurement_data, 'tolerance'):
            tolerance = self.measurement_data.tolerance
            # 波纹度公差设置
            self.r_spinbox.setValue(getattr(tolerance, 'ripple_tolerance_R', 2.0))
            self.n0_spinbox.setValue(getattr(tolerance, 'ripple_tolerance_N0', 1.0))
            self.k_spinbox.setValue(getattr(tolerance, 'ripple_tolerance_K', 0.0))
            self.draw_tolerance_checkbox.setChecked(getattr(tolerance, 'ripple_tolerance_enabled', True))
            
            # 周节波纹度公差设置（使用相同的参数，或可以单独存储）
            self.pitch_r_spinbox.setValue(getattr(tolerance, 'ripple_tolerance_R', 2.0))
            self.pitch_n0_spinbox.setValue(getattr(tolerance, 'ripple_tolerance_N0', 1.0))
            self.pitch_k_spinbox.setValue(getattr(tolerance, 'ripple_tolerance_K', 0.0))
            self.pitch_draw_tolerance_checkbox.setChecked(getattr(tolerance, 'ripple_tolerance_enabled', True))
        else:
            # 使用默认值
            self.r_spinbox.setValue(2.0)
            self.n0_spinbox.setValue(1.0)
            self.k_spinbox.setValue(0.0)
            self.draw_tolerance_checkbox.setChecked(True)
            
            self.pitch_r_spinbox.setValue(2.0)
            self.pitch_n0_spinbox.setValue(1.0)
            self.pitch_k_spinbox.setValue(0.0)
            self.pitch_draw_tolerance_checkbox.setChecked(True)
            
    def get_settings(self):
        """获取当前设置"""
        return {
            'R': self.r_spinbox.value(),
            'N0': self.n0_spinbox.value(),
            'K': self.k_spinbox.value(),
            'enabled': self.draw_tolerance_checkbox.isChecked(),
            'left': self.left_checkbox.isChecked(),
            'right': self.right_checkbox.isChecked(),
            'sector': self.sector_checkbox.isChecked(),
            'radial': self.radial_checkbox.isChecked(),
            'circumferential': self.circumferential_checkbox.isChecked(),
            'tolerance_activation': self.tolerance_activation_checkbox.isChecked()
        }
        
    def apply_settings(self):
        """应用设置到图表（不关闭对话框）"""
        settings = self.get_settings()
        
        # 保存到measurement_data
        if self.measurement_data:
            if not hasattr(self.measurement_data, 'tolerance'):
                from models.gear_data import ToleranceData
                self.measurement_data.tolerance = ToleranceData()
            
            tolerance = self.measurement_data.tolerance
            # 波纹度公差设置（周节波纹度使用相同的参数）
            tolerance.ripple_tolerance_R = settings['R']
            tolerance.ripple_tolerance_N0 = settings['N0']
            tolerance.ripple_tolerance_K = settings['K']
            tolerance.ripple_tolerance_enabled = settings['enabled']
        
        # 发送更新信号，触发图表刷新
        self.settings_updated.emit(settings)
        
        # 显示提示信息
        QMessageBox.information(self, "成功", "公差设置已应用到图表！")
    
    def accept_and_save(self):
        """保存设置并关闭对话框"""
        settings = self.get_settings()
        
        # 保存到measurement_data
        if self.measurement_data:
            if not hasattr(self.measurement_data, 'tolerance'):
                from models.gear_data import ToleranceData
                self.measurement_data.tolerance = ToleranceData()
            
            tolerance = self.measurement_data.tolerance
            # 波纹度公差设置（周节波纹度使用相同的参数）
            tolerance.ripple_tolerance_R = settings['R']
            tolerance.ripple_tolerance_N0 = settings['N0']
            tolerance.ripple_tolerance_K = settings['K']
            tolerance.ripple_tolerance_enabled = settings['enabled']
        
        # 发送更新信号，触发图表刷新
        self.settings_updated.emit(settings)
        
        self.accept()
    
    def showEvent(self, event: QShowEvent):
        """窗口显示时的事件处理"""
        super().showEvent(event)
        # 在窗口显示后设置水平分割器初始位置为50%
        if not self._splitter_initialized and hasattr(self, 'splitter'):
            # 获取splitter的总宽度
            total_width = self.splitter.width()
            if total_width > 0:
                # 设置左右各占50%
                half_width = total_width // 2
                self.splitter.setSizes([half_width, half_width])
                self._splitter_initialized = True
            else:
                # 如果宽度为0，延迟设置（使用定时器）
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: self._init_splitter_position())
        
        # 在窗口显示后设置垂直分割器初始位置，确保按钮区域完全可见
        if not self._vertical_splitter_initialized and hasattr(self, 'vertical_splitter'):
            # 获取splitter的总高度
            total_height = self.vertical_splitter.height()
            if total_height > 0:
                # 设置按钮区域为固定高度（120像素），内容区域占据剩余空间
                # 确保内容区域有足够空间显示所有内容
                button_height = 120
                content_height = total_height - button_height
                if content_height > 400:  # 如果总高度足够，给内容区域更多空间
                    self.vertical_splitter.setSizes([content_height, button_height])
                elif content_height > 0:
                    self.vertical_splitter.setSizes([content_height, button_height])
                else:
                    # 如果总高度太小，至少保证按钮区域可见
                    self.vertical_splitter.setSizes([max(400, total_height - 120), 120])
                self._vertical_splitter_initialized = True
            else:
                # 如果高度为0，延迟设置（使用定时器）
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: self._init_vertical_splitter_position())
    
    def _init_splitter_position(self):
        """初始化水平分割器位置为50%"""
        if hasattr(self, 'splitter') and not self._splitter_initialized:
            total_width = self.splitter.width()
            if total_width > 0:
                half_width = total_width // 2
                self.splitter.setSizes([half_width, half_width])
                self._splitter_initialized = True
    
    def _init_vertical_splitter_position(self):
        """初始化垂直分割器位置，确保按钮区域完全可见"""
        if hasattr(self, 'vertical_splitter') and not self._vertical_splitter_initialized:
            total_height = self.vertical_splitter.height()
            if total_height > 0:
                # 设置按钮区域为固定高度（120像素），内容区域占据剩余空间
                # 确保内容区域有足够空间显示所有内容
                button_height = 120
                content_height = total_height - button_height
                if content_height > 400:  # 如果总高度足够，给内容区域更多空间
                    self.vertical_splitter.setSizes([content_height, button_height])
                elif content_height > 0:
                    self.vertical_splitter.setSizes([content_height, button_height])
                else:
                    # 如果总高度太小，至少保证按钮区域可见
                    self.vertical_splitter.setSizes([max(400, total_height - 120), 120])
                self._vertical_splitter_initialized = True



