"""
周节分析页面模块
完整的周节分析MDI子窗体实现
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QMdiArea, QMdiSubWindow, QTableWidget, QHeaderView, QAbstractItemView,
    QScrollArea, QTableWidgetItem
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from ui.custom_canvas import CustomFigureCanvas
from gear_analysis_refactored.config.logging_config import logger


class PitchAnalysisPage(QWidget):
    """周节分析完整页面 - MDI子窗体版本"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 说明标签
        info_label = QLabel("周节偏差分析 (fp, Fp, Fr)")
        info_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 5px;")
        layout.addWidget(info_label)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        
        self.analyze_pitch_btn = QPushButton("分析周节偏差")
        self.analyze_pitch_btn.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #2980b9; }"
            "QPushButton:disabled { background-color: #95a5a6; }"
        )
        self.analyze_pitch_btn.setEnabled(False)
        
        btn_layout.addWidget(self.analyze_pitch_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 创建MDI区域
        self.pitch_mdi_area = QMdiArea()
        self.pitch_mdi_area.setViewMode(QMdiArea.SubWindowView)
        self.pitch_mdi_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.pitch_mdi_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.pitch_mdi_area.setMinimumHeight(600)
        layout.addWidget(self.pitch_mdi_area)
        
        # 状态标签
        self.pitch_stats_label = QLabel("分析状态: 未分析")
        layout.addWidget(self.pitch_stats_label)
        
        # 创建子窗体
        self.create_pitch_subwindows()
    
    def create_pitch_subwindows(self):
        """创建周节分析的MDI子窗体"""
        # 创建单个整合的子窗体
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 1. 左面齿面fp图表
        left_fp_label = QLabel("左面齿面 - fp (单齿周节偏差)")
        left_fp_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px; font-size: 14px;")
        content_layout.addWidget(left_fp_label)
        
        self.pitch_figure_left_fp = Figure(figsize=(12, 4), dpi=100)
        self.pitch_canvas_left_fp = CustomFigureCanvas(self.pitch_figure_left_fp)
        self.pitch_canvas_left_fp.setFixedHeight(300)
        content_layout.addWidget(self.pitch_canvas_left_fp)
        
        # 2. 左面齿面Fp图表
        left_Fp_label = QLabel("左面齿面 - Fp (累积周节偏差)")
        left_Fp_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px; font-size: 14px;")
        content_layout.addWidget(left_Fp_label)
        
        self.pitch_figure_left_Fp = Figure(figsize=(12, 4), dpi=100)
        self.pitch_canvas_left_Fp = CustomFigureCanvas(self.pitch_figure_left_Fp)
        self.pitch_canvas_left_Fp.setFixedHeight(300)
        content_layout.addWidget(self.pitch_canvas_left_Fp)
        
        # 3. 右面齿面fp图表
        right_fp_label = QLabel("右面齿面 - fp (单齿周节偏差)")
        right_fp_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px; font-size: 14px;")
        content_layout.addWidget(right_fp_label)
        
        self.pitch_figure_right_fp = Figure(figsize=(12, 4), dpi=100)
        self.pitch_canvas_right_fp = CustomFigureCanvas(self.pitch_figure_right_fp)
        self.pitch_canvas_right_fp.setFixedHeight(300)
        content_layout.addWidget(self.pitch_canvas_right_fp)
        
        # 4. 右面齿面Fp图表
        right_Fp_label = QLabel("右面齿面 - Fp (累积周节偏差)")
        right_Fp_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px; font-size: 14px;")
        content_layout.addWidget(right_Fp_label)
        
        self.pitch_figure_right_Fp = Figure(figsize=(12, 4), dpi=100)
        self.pitch_canvas_right_Fp = CustomFigureCanvas(self.pitch_figure_right_Fp)
        self.pitch_canvas_right_Fp.setFixedHeight(300)
        content_layout.addWidget(self.pitch_canvas_right_Fp)
        
        # 5. 左面齿面表格
        left_table_label = QLabel("左面齿面数据表格")
        left_table_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px; font-size: 14px;")
        content_layout.addWidget(left_table_label)
        
        self.pitch_table_left = QTableWidget()
        self.pitch_table_left.setRowCount(3)  # 3行：fp, Fp, Fr
        self.pitch_table_left.setVerticalHeaderLabels(["fp (μm)", "Fp (μm)", "Fr (μm)"])
        self.pitch_table_left.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.pitch_table_left.setMinimumHeight(150)
        self.pitch_table_left.setAlternatingRowColors(True)
        self.pitch_table_left.setEditTriggers(QAbstractItemView.NoEditTriggers)
        content_layout.addWidget(self.pitch_table_left)
        
        # 6. 右面齿面表格
        right_table_label = QLabel("右面齿面数据表格")
        right_table_label.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px; font-size: 14px;")
        content_layout.addWidget(right_table_label)
        
        self.pitch_table_right = QTableWidget()
        self.pitch_table_right.setRowCount(3)  # 3行：fp, Fp, Fr
        self.pitch_table_right.setVerticalHeaderLabels(["fp (μm)", "Fp (μm)", "Fr (μm)"])
        self.pitch_table_right.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.pitch_table_right.setMinimumHeight(150)
        self.pitch_table_right.setAlternatingRowColors(True)
        self.pitch_table_right.setEditTriggers(QAbstractItemView.NoEditTriggers)
        content_layout.addWidget(self.pitch_table_right)
        
        # 设置滚动区域
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # 添加到MDI
        subwindow = QMdiSubWindow()
        subwindow.setWindowTitle("周节分析图表")
        subwindow.setWidget(main_widget)
        self.pitch_mdi_area.addSubWindow(subwindow)
        subwindow.showMaximized()
    
    def update_pitch_results(self, results):
        """更新周节分析结果"""
        if not results:
            return
        
        # 更新左侧数据
        left_data = results.get('left', {})
        if left_data:
            self._update_pitch_chart(self.pitch_figure_left_fp, left_data, 'fp', '左面齿面 - fp')
            self._update_pitch_chart(self.pitch_figure_left_Fp, left_data, 'Fp', '左面齿面 - Fp')
            self._update_pitch_table(self.pitch_table_left, left_data)
        
        # 更新右侧数据
        right_data = results.get('right', {})
        if right_data:
            self._update_pitch_chart(self.pitch_figure_right_fp, right_data, 'fp', '右面齿面 - fp')
            self._update_pitch_chart(self.pitch_figure_right_Fp, right_data, 'Fp', '右面齿面 - Fp')
            self._update_pitch_table(self.pitch_table_right, right_data)
        
        # 更新状态
        self.pitch_stats_label.setText(
            f"分析完成 - 左侧: {len(left_data.get('teeth', []))}齿, "
            f"右侧: {len(right_data.get('teeth', []))}齿"
        )
    
    def _update_pitch_chart(self, figure, data, value_type, title):
        """更新周节图表"""
        teeth = data.get('teeth', [])
        values = data.get(value_type, [])
        
        if not teeth or not values:
            return
        
        figure.clear()
        ax = figure.add_subplot(111)
        
        import numpy as np
        x = np.arange(len(teeth))
        bars = ax.bar(x, values, color='skyblue', alpha=0.8, width=0.8)
        
        ax.set_xticks(x)
        ax.set_xticklabels(teeth)
        ax.set_xlabel("齿号")
        ax.set_ylabel(f"{value_type} (μm)")
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        
        # 添加数值标签
        for i, (tooth, value) in enumerate(zip(teeth, values)):
            ax.text(i, value + (max(values) - min(values)) * 0.01, 
                   f'{value:.1f}', ha='center', va='bottom', fontsize=8)
        
        figure.canvas.draw()
    
    def _update_pitch_table(self, table, data):
        """更新周节表格"""
        teeth = data.get('teeth', [])
        fp_values = data.get('fp', [])
        Fp_values = data.get('Fp', [])
        
        if not teeth:
            return
        
        table.setColumnCount(len(teeth))
        table.setHorizontalHeaderLabels([str(t) for t in teeth])
        
        # 填充数据
        for col, (fp, Fp) in enumerate(zip(fp_values, Fp_values)):
            table.setItem(0, col, QTableWidgetItem(f"{fp:.2f}"))
            table.setItem(1, col, QTableWidgetItem(f"{Fp:.2f}"))
        
        # Fr值
        Fr = data.get('Fr', 0)
        table.setItem(2, 0, QTableWidgetItem(f"{Fr:.2f}"))
        
        # 合并Fr行的其他列
        for col in range(1, len(teeth)):
            table.setItem(2, col, QTableWidgetItem(""))


