"""
UI对话框模块
包含各种对话框类
"""
import math
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QGroupBox, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QLabel, QGridLayout, QDialogButtonBox,
    QMessageBox, QSpinBox, QCheckBox, QHBoxLayout, QStackedWidget, QWidget,
    QDoubleSpinBox, QScrollArea
)
from PyQt5.QtGui import QDoubleValidator
from gear_analysis_refactored.config.logging_config import logger
from gear_analysis_refactored.config.settings import ToleranceConfig


class ToleranceCalculatorDialog(QDialog):
    """ISO1328 公差计算器对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ISO1328 公差计算器")
        self.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 输入参数组
        input_group = QGroupBox("齿轮参数")
        form_layout = QFormLayout()
        input_group.setLayout(form_layout)

        # 精度等级
        self.grade_combo = QComboBox()
        self.grade_combo.addItems([str(g) for g in ToleranceConfig.ACCURACY_GRADES])
        form_layout.addRow("精度等级:", self.grade_combo)

        # 模数
        self.module_edit = QLineEdit()
        self.module_edit.setValidator(
            QDoubleValidator(ToleranceConfig.MODULE_RANGE[0], 
                           ToleranceConfig.MODULE_RANGE[1], 3)
        )
        form_layout.addRow("模数 (mm):", self.module_edit)

        # 齿数
        self.teeth_edit = QLineEdit()
        self.teeth_edit.setValidator(
            QDoubleValidator(ToleranceConfig.TEETH_RANGE[0], 
                           ToleranceConfig.TEETH_RANGE[1], 0)
        )
        form_layout.addRow("齿数:", self.teeth_edit)

        # 齿宽
        self.width_edit = QLineEdit()
        self.width_edit.setValidator(
            QDoubleValidator(ToleranceConfig.WIDTH_RANGE[0], 
                           ToleranceConfig.WIDTH_RANGE[1], 2)
        )
        form_layout.addRow("齿宽 (mm):", self.width_edit)

        # 计算按钮
        calc_btn = QPushButton("计算公差")
        calc_btn.clicked.connect(self.calculate)

        layout.addWidget(input_group)
        layout.addWidget(calc_btn)

        # 结果组
        result_group = QGroupBox("计算结果 (μm)")
        grid_layout = QGridLayout()
        result_group.setLayout(grid_layout)

        # 齿形公差结果
        grid_layout.addWidget(QLabel("齿形公差 (F_alpha):"), 0, 0)
        self.f_alpha_label = QLabel("0.0")
        grid_layout.addWidget(self.f_alpha_label, 0, 1)

        grid_layout.addWidget(QLabel("齿形斜率公差 (fH_alpha):"), 1, 0)
        self.fh_alpha_label = QLabel("0.0")
        grid_layout.addWidget(self.fh_alpha_label, 1, 1)

        grid_layout.addWidget(QLabel("齿形形状公差 (ff_alpha):"), 2, 0)
        self.ff_alpha_label = QLabel("0.0")
        grid_layout.addWidget(self.ff_alpha_label, 2, 1)

        # 齿向公差结果
        grid_layout.addWidget(QLabel("齿向公差 (F_beta):"), 3, 0)
        self.f_beta_label = QLabel("0.0")
        grid_layout.addWidget(self.f_beta_label, 3, 1)

        grid_layout.addWidget(QLabel("齿向斜率公差 (fH_beta):"), 4, 0)
        self.fh_beta_label = QLabel("0.0")
        grid_layout.addWidget(self.fh_beta_label, 4, 1)

        grid_layout.addWidget(QLabel("齿向形状公差 (ff_beta):"), 5, 0)
        self.ff_beta_label = QLabel("0.0")
        grid_layout.addWidget(self.ff_beta_label, 5, 1)

        layout.addWidget(result_group)

        # 按钮框
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def calculate(self):
        """计算公差值"""
        try:
            # 获取输入值 - 添加空值检查
            accuracy_text = self.grade_combo.currentText()
            if not accuracy_text:
                raise ValueError("请选择精度等级")

            accuracy_grade = int(accuracy_text)

            module_text = self.module_edit.text().strip()
            if not module_text:
                raise ValueError("请输入模数")
            module = float(module_text)

            teeth_text = self.teeth_edit.text().strip()
            if not teeth_text:
                raise ValueError("请输入齿数")
            teeth = int(teeth_text)

            width_text = self.width_edit.text().strip()
            if not width_text:
                raise ValueError("请输入齿宽")
            width = float(width_text)

            # 参数验证
            self._validate_parameters(module, teeth, width, accuracy_grade)

            # 计算公差
            results = self._calculate_tolerances(module, teeth, width, accuracy_grade)

            # 更新UI
            self._update_ui(results)

        except Exception as e:
            logger.exception("公差计算发生错误")
            QMessageBox.critical(self, "计算错误", f"参数错误: {str(e)}")

    def _validate_parameters(self, module, teeth, width, accuracy_grade):
        """验证参数范围"""
        if module <= 0:
            raise ValueError("模数必须大于0")
        if teeth <= 0:
            raise ValueError("齿数必须大于0")
        if width <= 0:
            raise ValueError("齿宽必须大于0")
        
        mod_min, mod_max = ToleranceConfig.MODULE_RANGE
        if module < mod_min or module > mod_max:
            raise ValueError(f"模数范围应在{mod_min}-{mod_max}mm之间")
        
        teeth_min, teeth_max = ToleranceConfig.TEETH_RANGE
        if teeth < teeth_min or teeth > teeth_max:
            raise ValueError(f"齿数范围应在{teeth_min}-{teeth_max}之间")
        
        width_min, width_max = ToleranceConfig.WIDTH_RANGE
        if width < width_min or width > width_max:
            raise ValueError(f"齿宽范围应在{width_min}-{width_max}mm之间")
        
        if accuracy_grade not in ToleranceConfig.ACCURACY_GRADES:
            raise ValueError(f"精度等级应在{min(ToleranceConfig.ACCURACY_GRADES)}-{max(ToleranceConfig.ACCURACY_GRADES)}级之间")

    def _calculate_tolerances(self, module, teeth, width, accuracy_grade):
        """计算所有公差值"""
        # 计算分度圆直径
        pitch_diameter = module * teeth

        # 精度等级系数
        k = ToleranceConfig.GRADE_FACTORS.get(accuracy_grade, 1.6)

        # 1. 计算齿形公差 F_alpha
        sqrt_d = max(0, pitch_diameter)
        F_alpha_5 = 0.1 * module + 0.45 * math.sqrt(sqrt_d) + 5
        F_alpha = k * F_alpha_5

        # 2. 计算齿形斜率公差和形状公差
        fH_alpha = F_alpha * ToleranceConfig.PROFILE_SLOPE_RATIO
        ff_alpha = F_alpha * ToleranceConfig.PROFILE_SHAPE_RATIO

        # 3. 计算齿向公差 F_beta
        width = max(width, 1)  # 防止除零
        d_b_ratio = max(0, pitch_diameter / width)
        sqrt_d_b = math.sqrt(d_b_ratio) if d_b_ratio >= 0 else 0
        sqrt_b = math.sqrt(max(0, width))

        F_beta_5 = 0.1 * sqrt_d_b * width + 0.45 * sqrt_b + 5
        F_beta = k * F_beta_5

        # 4. 计算齿向斜率公差和形状公差
        fH_beta = F_beta * ToleranceConfig.FLANK_SLOPE_RATIO
        ff_beta = F_beta * ToleranceConfig.FLANK_SHAPE_RATIO

        return {
            'F_alpha': F_alpha,
            'fH_alpha': fH_alpha,
            'ff_alpha': ff_alpha,
            'F_beta': F_beta,
            'fH_beta': fH_beta,
            'ff_beta': ff_beta
        }

    def _update_ui(self, results):
        """更新UI显示"""
        self.f_alpha_label.setText(f"{results['F_alpha']:.1f}")
        self.fh_alpha_label.setText(f"{results['fH_alpha']:.1f}")
        self.ff_alpha_label.setText(f"{results['ff_alpha']:.1f}")
        self.f_beta_label.setText(f"{results['F_beta']:.1f}")
        self.fh_beta_label.setText(f"{results['fH_beta']:.1f}")
        self.ff_beta_label.setText(f"{results['ff_beta']:.1f}")


class RippleAnalysisDialog(QDialog):
    """Ripple波纹度分析参数对话框 - 从原程序迁移"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("波纹度分析参数设置")
        self.setGeometry(300, 300, 500, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setup_ui(layout)
    
    def setup_ui(self, layout):
        """设置UI"""
        # 截止波长
        cutoff_group = QGroupBox("截止波长设置 (λc)")
        cutoff_layout = QFormLayout()
        
        self.cutoff_wavelength = QLineEdit("0.8")
        self.cutoff_wavelength.setValidator(QDoubleValidator(0.1, 10.0, 2))
        cutoff_layout.addRow("截止波长 λc (mm):", self.cutoff_wavelength)
        
        cutoff_note = QLabel("说明：截止波长用于分离波纹度和粗糙度。\n• 0.8mm：标准设置\n• 2.5mm：ISO1328标准\n• 自定义：根据需求调整")
        cutoff_note.setStyleSheet("color: #666; font-size: 10px;")
        cutoff_note.setWordWrap(True)
        cutoff_layout.addRow("", cutoff_note)
        
        cutoff_group.setLayout(cutoff_layout)
        layout.addWidget(cutoff_group)
        
        # 滤波器设置
        filter_group = QGroupBox("滤波器设置")
        filter_layout = QFormLayout()
        
        self.highpass_cutoff = QLineEdit("0.01")
        self.highpass_cutoff.setValidator(QDoubleValidator(0.001, 2.0, 3))
        filter_layout.addRow("高通截止频率(周期/mm):", self.highpass_cutoff)
        
        self.lowpass_cutoff = QLineEdit("1.0")
        self.lowpass_cutoff.setValidator(QDoubleValidator(0.1, 20.0, 2))
        filter_layout.addRow("低通截止频率(周期/mm):", self.lowpass_cutoff)
        
        self.filter_type = QComboBox()
        self.filter_type.addItems(["Butterworth", "Chebyshev", "Elliptic", "Bessel"])
        self.filter_type.setCurrentText("Butterworth")
        filter_layout.addRow("滤波器类型:", self.filter_type)
        
        self.filter_order = QComboBox()
        self.filter_order.addItems(["2", "4", "6", "8", "10"])
        self.filter_order.setCurrentIndex(1)
        filter_layout.addRow("滤波器阶数:", self.filter_order)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 阶次分析
        order_group = QGroupBox("阶次分析")
        order_layout = QFormLayout()
        
        self.order_range = QLineEdit("1,200")
        order_layout.addRow("阶次分析范围:", self.order_range)
        
        self.threshold = QLineEdit("0.5")
        self.threshold.setValidator(QDoubleValidator(0.1, 10.0, 2))
        order_layout.addRow("关键阶次阈值(%):", self.threshold)
        
        self.fundamental_method = QComboBox()
        self.fundamental_method.addItems(["基于齿数", "基于周长", "基于转速", "自动检测"])
        order_layout.addRow("基频计算方法:", self.fundamental_method)
        
        self.harmonic_depth = QSpinBox()
        self.harmonic_depth.setRange(3, 20)
        self.harmonic_depth.setValue(10)
        order_layout.addRow("谐波分析深度:", self.harmonic_depth)
        
        order_group.setLayout(order_layout)
        layout.addWidget(order_group)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout()
        
        self.window_type = QComboBox()
        self.window_type.addItems(["矩形窗", "汉宁窗", "汉明窗", "布莱克曼窗"])
        self.window_type.setCurrentText("汉宁窗")
        advanced_layout.addRow("窗口类型:", self.window_type)
        
        self.overlap_ratio = QLineEdit("50")
        self.overlap_ratio.setValidator(QDoubleValidator(0, 100, 1))
        advanced_layout.addRow("重叠率(%):", self.overlap_ratio)
        
        self.zero_padding = QSpinBox()
        self.zero_padding.setRange(0, 10)
        self.zero_padding.setValue(2)
        advanced_layout.addRow("零填充倍数:", self.zero_padding)
        
        self.enable_diagnosis = QCheckBox("启用详细诊断")
        self.enable_diagnosis.setChecked(True)
        advanced_layout.addRow("", self.enable_diagnosis)
        
        self.diagnosis_depth = QComboBox()
        self.diagnosis_depth.addItems(["基本", "详细", "完整"])
        self.diagnosis_depth.setCurrentText("详细")
        advanced_layout.addRow("诊断深度:", self.diagnosis_depth)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_settings(self):
        """获取设置"""
        try:
            cutoff = float(self.cutoff_wavelength.text())
            min_order, max_order = map(int, self.order_range.text().split(','))
            
            return {
                'cutoff_wavelength': cutoff,
                'highpass_cutoff': float(self.highpass_cutoff.text()),
                'lowpass_cutoff': float(self.lowpass_cutoff.text()),
                'filter_type': self.filter_type.currentText(),
                'filter_order': int(self.filter_order.currentText()),
                'min_order': min_order,
                'max_order': max_order,
                'threshold': float(self.threshold.text()) / 100,
                'fundamental_method': self.fundamental_method.currentText(),
                'harmonic_depth': self.harmonic_depth.value(),
                'window_type': self.window_type.currentText(),
                'overlap_ratio': float(self.overlap_ratio.text()),
                'zero_padding': self.zero_padding.value(),
                'enable_diagnosis': self.enable_diagnosis.isChecked(),
                'diagnosis_depth': self.diagnosis_depth.currentText()
            }
        except ValueError as e:
            QMessageBox.warning(self, "参数错误", f"参数格式错误: {str(e)}")
            return None


class AnalysisSettingsDialog(QDialog):
    """分析参数设置对话框 - 从原程序迁移"""
    def __init__(self, current_settings=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分析参数与公差设置")
        self.setGeometry(300, 300, 600, 500)
        self.settings = current_settings if current_settings else self.get_default_settings()
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 评价范围设置
        eval_range_group = QGroupBox("评价范围设置 (0.0表示使用MKA文件默认值)")
        eval_range_layout = QFormLayout(eval_range_group)
        
        self.profile_start_edit = QLineEdit(str(self.settings['profile_range'][0]))
        self.profile_end_edit = QLineEdit(str(self.settings['profile_range'][1]))
        eval_range_layout.addRow("齿形起评点 (d1, mm):", self.profile_start_edit)
        eval_range_layout.addRow("齿形终评点 (d2, mm):", self.profile_end_edit)
        
        self.lead_start_edit = QLineEdit(str(self.settings['lead_range'][0]))
        self.lead_end_edit = QLineEdit(str(self.settings['lead_range'][1]))
        eval_range_layout.addRow("齿向起评点 (b1, mm):", self.lead_start_edit)
        eval_range_layout.addRow("齿向终评点 (b2, mm):", self.lead_end_edit)
        
        layout.addWidget(eval_range_group)
        
        # 公差设置
        tolerance_group = QGroupBox("公差设置")
        tolerance_layout = QVBoxLayout(tolerance_group)
        
        self.tolerance_mode_combo = QComboBox()
        self.tolerance_mode_combo.addItems(["使用MKA文件默认值", "ISO 1328 标准公差", "自定义自由公差"])
        self.tolerance_mode_combo.currentTextChanged.connect(self.on_tolerance_mode_changed)
        tolerance_layout.addWidget(self.tolerance_mode_combo)
        
        self.tolerance_stack = QStackedWidget()
        tolerance_layout.addWidget(self.tolerance_stack)
        
        # Stack 0: MKA默认
        mka_widget = QLabel("将使用MKA文件中定义的或根据文件参数自动计算的公差值。")
        self.tolerance_stack.addWidget(mka_widget)
        
        # Stack 1: ISO标准
        iso_widget = QWidget()
        iso_layout = QFormLayout(iso_widget)
        self.iso_grade_combo = QComboBox()
        self.iso_grade_combo.addItems([str(i) for i in range(4, 13)])
        self.iso_grade_combo.setCurrentText(str(self.settings['iso_grade']))
        iso_layout.addRow("精度等级 (ISO 1328):", self.iso_grade_combo)
        self.tolerance_stack.addWidget(iso_widget)
        
        # Stack 2: 自定义
        custom_widget = QWidget()
        custom_layout = QFormLayout(custom_widget)
        
        self.custom_f_alpha = QLineEdit(str(self.settings['custom_tolerances']['F_alpha']))
        custom_layout.addRow("齿形公差 F_alpha (μm):", self.custom_f_alpha)
        
        self.custom_f_beta = QLineEdit(str(self.settings['custom_tolerances']['F_beta']))
        custom_layout.addRow("齿向公差 F_beta (μm):", self.custom_f_beta)
        
        self.tolerance_stack.addWidget(custom_widget)
        layout.addWidget(tolerance_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_tolerance_mode_changed(self, text):
        """公差模式变化"""
        idx = self.tolerance_mode_combo.currentIndex()
        self.tolerance_stack.setCurrentIndex(idx)
    
    def get_default_settings(self):
        """获取默认设置"""
        return {
            'profile_range': (0.0, 0.0),
            'lead_range': (0.0, 0.0),
            'tolerance_mode': 'mka',
            'iso_grade': 6,
            'custom_tolerances': {'F_alpha': 15.0, 'F_beta': 20.0}
        }
    
    def get_settings(self):
        """获取设置"""
        try:
            mode_map = ['mka', 'iso', 'custom']
            mode = mode_map[self.tolerance_mode_combo.currentIndex()]
            
            return {
                'profile_range': (
                    float(self.profile_start_edit.text()),
                    float(self.profile_end_edit.text())
                ),
                'lead_range': (
                    float(self.lead_start_edit.text()),
                    float(self.lead_end_edit.text())
                ),
                'tolerance_mode': mode,
                'iso_grade': int(self.iso_grade_combo.currentText()),
                'custom_tolerances': {
                    'F_alpha': float(self.custom_f_alpha.text()),
                    'F_beta': float(self.custom_f_beta.text())
                }
            }
        except Exception as e:
            logger.error(f"获取设置失败: {e}")
            return None


class QualityGradeDialog(QDialog):
    """精度等级设置对话框"""
    def __init__(self, current_grade=6, parent=None):
        super().__init__(parent)
        self.setWindowTitle("精度等级设置")
        self.setGeometry(300, 300, 400, 350)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 精度等级选择
        grade_group = QGroupBox("选择精度等级")
        grade_layout = QVBoxLayout()
        grade_group.setLayout(grade_layout)
        
        self.grade_combo = QComboBox()
        self.grade_combo.addItems(["3", "4", "5", "6", "7", "8", "9", "10", "11", "12"])
        self.grade_combo.setCurrentText(str(current_grade))
        self.grade_combo.currentTextChanged.connect(self.on_grade_changed)
        grade_layout.addWidget(self.grade_combo)
        
        # 精度等级说明
        self.grade_description = QLabel()
        self.grade_description.setWordWrap(True)
        self.grade_description.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        grade_layout.addWidget(self.grade_description)
        
        layout.addWidget(grade_group)
        
        # 公差系数设置
        tolerance_group = QGroupBox("公差系数设置")
        tolerance_layout = QFormLayout()
        tolerance_group.setLayout(tolerance_layout)
        
        self.f_alpha_factor = QDoubleSpinBox()
        self.f_alpha_factor.setRange(0.1, 2.0)
        self.f_alpha_factor.setValue(1.0)
        self.f_alpha_factor.setSingleStep(0.1)
        tolerance_layout.addRow("齿形公差系数:", self.f_alpha_factor)
        
        self.f_beta_factor = QDoubleSpinBox()
        self.f_beta_factor.setRange(0.1, 2.0)
        self.f_beta_factor.setValue(1.0)
        self.f_beta_factor.setSingleStep(0.1)
        tolerance_layout.addRow("齿向公差系数:", self.f_beta_factor)
        
        self.fp_factor = QDoubleSpinBox()
        self.fp_factor.setRange(0.1, 2.0)
        self.fp_factor.setValue(1.0)
        self.fp_factor.setSingleStep(0.1)
        tolerance_layout.addRow("周节公差系数:", self.fp_factor)
        
        layout.addWidget(tolerance_group)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 初始化说明
        self.on_grade_changed(str(current_grade))
    
    def on_grade_changed(self, grade_text):
        """精度等级变化时更新说明"""
        grade = int(grade_text)
        if grade <= 4:
            description = "超高精度等级，适用于精密仪器、航空航天等高要求场合"
        elif grade <= 6:
            description = "高精度等级，适用于汽车变速箱、工业减速器等重要传动"
        elif grade <= 8:
            description = "标准精度等级，适用于一般工业传动、通用机械等"
        else:
            description = "普通精度等级，适用于低要求场合、非关键传动"
        
        self.grade_description.setText(f"精度等级 {grade} 级: {description}")
    
    def get_grade(self):
        """获取用户选择的精度等级"""
        return int(self.grade_combo.currentText())
    
    def get_factors(self):
        """获取公差系数"""
        return {
            'f_alpha_factor': self.f_alpha_factor.value(),
            'f_beta_factor': self.f_beta_factor.value(),
            'fp_factor': self.fp_factor.value()
        }


class ProcessingStepsDialog(QDialog):
    """处理步骤详情对话框"""
    def __init__(self, processing_steps, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据处理步骤详情")
        self.setGeometry(100, 100, 800, 600)
        self.processing_steps = processing_steps
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 添加每个步骤的详情
        for i, (step_name, step_data) in enumerate(processing_steps.items()):
            step_frame = self.create_step_frame(step_name, step_data, i)
            scroll_layout.addWidget(step_frame)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def create_step_frame(self, step_name, step_data, index):
        """创建步骤框架"""
        frame = QGroupBox(f"步骤 {index + 1}: {step_name}")
        layout = QVBoxLayout()
        
        # 步骤描述
        if 'description' in step_data:
            desc_label = QLabel(step_data['description'])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #333; font-size: 12px;")
            layout.addWidget(desc_label)
        
        # 参数信息
        if 'parameters' in step_data and step_data['parameters']:
            param_group = QGroupBox("参数设置")
            param_layout = QFormLayout()
            
            for param_name, param_value in step_data['parameters'].items():
                param_layout.addRow(f"{param_name}:", QLabel(str(param_value)))
            
            param_group.setLayout(param_layout)
            layout.addWidget(param_group)
        
        # 处理结果
        if 'results' in step_data and step_data['results']:
            result_group = QGroupBox("处理结果")
            result_layout = QFormLayout()
            
            for result_name, result_value in step_data['results'].items():
                result_layout.addRow(f"{result_name}:", QLabel(str(result_value)))
            
            result_group.setLayout(result_layout)
            layout.addWidget(result_group)
        
        # 状态信息
        if 'status' in step_data:
            status_label = QLabel(f"状态: {step_data['status']}")
            status_label.setStyleSheet("color: #008000; font-weight: bold;")
            layout.addWidget(status_label)
        
        frame.setLayout(layout)
        return frame

