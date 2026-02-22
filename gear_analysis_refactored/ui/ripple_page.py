"""
Ripple分析页面模块
完整的Ripple分析MDI子窗体实现
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMdiArea, QMdiSubWindow, QTableWidget, QHeaderView, QAbstractItemView,
    QScrollArea
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from ui.custom_canvas import CustomFigureCanvas
from gear_analysis_refactored.config.logging_config import logger


class RippleAnalysisPage(QWidget):
    """Ripple分析完整页面 - MDI子窗体版本"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 添加说明标签
        info_label = QLabel("Ripple(波纹度)分析 - 识别周期性波纹及其工艺根源")
        info_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 5px;")
        layout.addWidget(info_label)
        
        # 创建参数设置区域
        param_layout = QHBoxLayout()
        
        self.analyze_ripple_btn = QPushButton("Ripple分析")
        self.analyze_ripple_btn.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #2980b9; }"
            "QPushButton:disabled { background-color: #95a5a6; }"
        )
        self.analyze_ripple_btn.setEnabled(False)
        
        self.settings_btn = QPushButton("分析设置")
        self.settings_btn.setStyleSheet(
            "QPushButton { background-color: #9b59b6; color: white; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #8e44ad; }"
        )
        
        self.export_ripple_btn = QPushButton("生成报告")
        self.export_ripple_btn.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #219653; }"
            "QPushButton:disabled { background-color: #95a5a6; }"
        )
        self.export_ripple_btn.setEnabled(False)
        
        self.process_view_btn = QPushButton("查看处理过程")
        self.process_view_btn.setStyleSheet(
            "QPushButton { background-color: #e67e22; color: white; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #d35400; }"
            "QPushButton:disabled { background-color: #95a5a6; }"
        )
        self.process_view_btn.setEnabled(False)
        
        self.order_spectrum_btn = QPushButton("生成阶次谱报告")
        self.order_spectrum_btn.setStyleSheet(
            "QPushButton { background-color: #9b59b6; color: white; font-weight: bold; padding: 8px; }"
            "QPushButton:hover { background-color: #8e44ad; }"
            "QPushButton:disabled { background-color: #95a5a6; }"
        )
        self.order_spectrum_btn.setEnabled(False)
        
        self.order_params_help_btn = QPushButton("阶次谱参数说明")
        self.order_params_help_btn.setStyleSheet(
            "QPushButton { background-color: #f39c12; color: white; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #e67e22; }"
        )
        
        param_layout.addWidget(self.analyze_ripple_btn)
        param_layout.addWidget(self.settings_btn)
        param_layout.addWidget(self.export_ripple_btn)
        param_layout.addWidget(self.order_spectrum_btn)
        param_layout.addWidget(self.process_view_btn)
        param_layout.addWidget(self.order_params_help_btn)
        param_layout.addStretch()
        
        layout.addLayout(param_layout)
        
        # 创建统计信息区域
        self.ripple_stats_label = QLabel("未进行Ripple分析")
        self.ripple_stats_label.setStyleSheet("font-size: 12px; background-color: #f0f0f0; padding: 8px;")
        self.ripple_stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.ripple_stats_label)
        
        # 创建MDI区域
        self.ripple_mdi_area = QMdiArea()
        self.ripple_mdi_area.setViewMode(QMdiArea.TabbedView)
        self.ripple_mdi_area.setTabsClosable(True)
        self.ripple_mdi_area.setTabsMovable(True)
        layout.addWidget(self.ripple_mdi_area)
        
        # 创建Ripple分析子窗体
        self.create_ripple_subwindows()
    
    def create_ripple_subwindows(self):
        """创建Ripple分析MDI子窗体"""
        # 1. 参数说明子窗体
        params_subwindow = QMdiSubWindow()
        params_subwindow.setWindowTitle("参数说明")
        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)
        
        params_title = QLabel("波纹度参数说明")
        params_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; padding: 10px;")
        params_layout.addWidget(params_title)
        
        params_content = QLabel("""
        <h3>参数含义说明：</h3>
        <p><b>Wt (峰谷高度)</b>：波纹度曲线的最大值与最小值之间的差值</p>
        <p><b>Wq (均方根偏差)</b>：波纹度曲线的RMS值</p>
        <p><b>Wa (算术平均偏差)</b>：波纹度曲线偏差平均值的平均绝对值</p>
        
        <h3>质量评价标准：</h3>
        <p><b>优秀</b>：Wt≤10μm, Wq≤3μm, Wa≤2μm</p>
        <p><b>良好</b>：Wt≤20μm, Wq≤6μm, Wa≤4μm</p>
        <p><b>一般</b>：Wt≤30μm, Wq≤9μm, Wa≤6μm</p>
        <p><b>超差</b>：超出上述范围</p>
        """)
        params_content.setStyleSheet("background-color: #f8f9fa; padding: 15px; border-radius: 5px;")
        params_content.setWordWrap(True)
        params_layout.addWidget(params_content)
        
        params_subwindow.setWidget(params_widget)
        self.ripple_mdi_area.addSubWindow(params_subwindow)
        params_subwindow.show()
        
        # 2. 分析结果子窗体
        results_subwindow = QMdiSubWindow()
        results_subwindow.setWindowTitle("分析结果")
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        results_title = QLabel("当前分析结果")
        results_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #27ae60; padding: 10px; background-color: #d5f4e6; border-radius: 5px;")
        results_layout.addWidget(results_title)
        
        self.ripple_results_label = QLabel("未进行Ripple分析")
        self.ripple_results_label.setStyleSheet("background-color: #f0f0f0; padding: 15px; border-radius: 5px;")
        self.ripple_results_label.setAlignment(Qt.AlignCenter)
        results_layout.addWidget(self.ripple_results_label)
        
        results_subwindow.setWidget(results_widget)
        self.ripple_mdi_area.addSubWindow(results_subwindow)
        results_subwindow.show()
        
        # 3. 阶次分析图表子窗体
        chart_subwindow = QMdiSubWindow()
        chart_subwindow.setWindowTitle("阶次分析图表")
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        chart_title = QLabel("阶次分析图表")
        chart_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; padding: 10px;")
        chart_layout.addWidget(chart_title)
        
        # 创建图表
        self.ripple_figure = Figure(figsize=(12, 8), dpi=100)
        self.ripple_canvas = CustomFigureCanvas(self.ripple_figure)
        
        # 创建滚动区域
        chart_scroll_area = QScrollArea()
        chart_scroll_area.setWidget(self.ripple_canvas)
        chart_scroll_area.setWidgetResizable(True)
        chart_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        chart_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 初始化图表
        self.init_ripple_chart()
        
        chart_layout.addWidget(chart_scroll_area)
        
        chart_subwindow.setWidget(chart_widget)
        self.ripple_mdi_area.addSubWindow(chart_subwindow)
        chart_subwindow.show()
        
        # 4. 诊断表格子窗体
        diagnosis_subwindow = QMdiSubWindow()
        diagnosis_subwindow.setWindowTitle("诊断表格")
        diagnosis_widget = QWidget()
        diagnosis_layout = QVBoxLayout(diagnosis_widget)
        
        diagnosis_title = QLabel("阶次诊断表格")
        diagnosis_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50; padding: 10px;")
        diagnosis_layout.addWidget(diagnosis_title)
        
        self.diagnosis_table = QTableWidget()
        self.diagnosis_table.setColumnCount(3)
        self.diagnosis_table.setHorizontalHeaderLabels(["阶次", "幅值", "可能原因"])
        self.diagnosis_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.diagnosis_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.diagnosis_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.diagnosis_table.verticalHeader().setVisible(False)
        self.diagnosis_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 初始化诊断表格
        self.init_diagnosis_table()
        
        diagnosis_layout.addWidget(self.diagnosis_table)
        
        diagnosis_subwindow.setWidget(diagnosis_widget)
        self.ripple_mdi_area.addSubWindow(diagnosis_subwindow)
        diagnosis_subwindow.show()
    
    def init_ripple_chart(self):
        """初始化Ripple图表"""
        self.ripple_figure.clear()
        ax = self.ripple_figure.add_subplot(111)
        ax.text(0.5, 0.5, "等待Ripple分析...\n请点击分析按钮", 
                ha='center', va='center', transform=ax.transAxes,
                fontsize=14, color='gray')
        ax.set_title("Ripple阶次分析图表")
        ax.axis('off')
        self.ripple_canvas.draw()
    
    def init_diagnosis_table(self):
        """初始化诊断表格，显示示例内容"""
        example_data = [
            ("1×转速", "待分析", "不平衡、偏心"),
            ("2×转速", "待分析", "热变形、装配误差"),
            ("齿数×转速", "待分析", "齿轮啮合误差"),
            ("高阶谐波", "待分析", "加工质量问题")
        ]
        
        self.diagnosis_table.setRowCount(len(example_data))
        
        for row, (order, amplitude, diagnosis) in enumerate(example_data):
            self.diagnosis_table.setItem(row, 0, QTableWidgetItem(order))
            self.diagnosis_table.setItem(row, 1, QTableWidgetItem(amplitude))
            self.diagnosis_table.setItem(row, 2, QTableWidgetItem(diagnosis))
    
    def update_ripple_results(self, results):
        """更新Ripple分析结果"""
        if not results:
            return
        
        # 更新统计信息
        stats = results.get('stats', {})
        profile_stats = stats.get('profile', {})
        flank_stats = stats.get('flank', {})
        
        stats_text = f"""
        <h3>Ripple分析完成</h3>
        <p><b>齿形波纹度：</b></p>
        <ul>
            <li>总齿数: {profile_stats.get('total', 0)}</li>
            <li>通过齿数: {profile_stats.get('passed', 0)}</li>
            <li>失败齿数: {profile_stats.get('failed', 0)}</li>
            <li>平均W值: {profile_stats.get('avg_w', 0):.3f} μm</li>
            <li>平均RMS: {profile_stats.get('avg_rms', 0):.3f} μm</li>
        </ul>
        <p><b>齿向波纹度：</b></p>
        <ul>
            <li>总齿数: {flank_stats.get('total', 0)}</li>
            <li>通过齿数: {flank_stats.get('passed', 0)}</li>
            <li>失败齿数: {flank_stats.get('failed', 0)}</li>
            <li>平均W值: {flank_stats.get('avg_w', 0):.3f} μm</li>
            <li>平均RMS: {flank_stats.get('avg_rms', 0):.3f} μm</li>
        </ul>
        """
        
        self.ripple_results_label.setText(stats_text)
        self.ripple_stats_label.setText(f"分析完成 - Profile: {profile_stats.get('total', 0)}齿, Flank: {flank_stats.get('total', 0)}齿")
        
        # 更新图表
        self.update_ripple_chart(results)
        
        # 更新诊断表格
        self.update_diagnosis_table(results)
        
        # 启用按钮
        self.export_ripple_btn.setEnabled(True)
        self.process_view_btn.setEnabled(True)
        self.order_spectrum_btn.setEnabled(True)
    
    def update_ripple_chart(self, results):
        """更新Ripple图表"""
        order_analysis = results.get('order_analysis', {})
        
        if not order_analysis:
            return
        
        self.ripple_figure.clear()
        
        # 创建多个子图
        fig = self.ripple_figure
        
        # Profile阶次谱
        if 'profile' in order_analysis:
            ax1 = fig.add_subplot(221)
            profile_data = order_analysis['profile']
            orders = profile_data.get('orders', [])
            amplitudes = profile_data.get('amplitudes', [])
            
            if orders and amplitudes:
                ax1.bar(orders, amplitudes, width=0.8, color='blue', alpha=0.7)
                ax1.set_title('Profile 阶次谱')
                ax1.set_xlabel('阶次')
                ax1.set_ylabel('幅值')
                ax1.grid(True, alpha=0.3)
        
        # Flank阶次谱
        if 'flank' in order_analysis:
            ax2 = fig.add_subplot(222)
            flank_data = order_analysis['flank']
            orders = flank_data.get('orders', [])
            amplitudes = flank_data.get('amplitudes', [])
            
            if orders and amplitudes:
                ax2.bar(orders, amplitudes, width=0.8, color='green', alpha=0.7)
                ax2.set_title('Flank 阶次谱')
                ax2.set_xlabel('阶次')
                ax2.set_ylabel('幅值')
                ax2.grid(True, alpha=0.3)
        
        fig.tight_layout()
        self.ripple_canvas.draw()
    
    def update_diagnosis_table(self, results):
        """更新诊断表格"""
        # 简化版诊断表格更新
        # 可以根据实际阶次分析结果填充
        pass

