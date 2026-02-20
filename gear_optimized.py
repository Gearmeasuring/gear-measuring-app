import sys
import re
import os
import logging
import numpy as np
import math
import datetime
import subprocess
import pandas as pd
from collections import defaultdict
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QStackedWidget, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QMessageBox, QLabel, QHeaderView, QAbstractItemView, QStatusBar, QAction, QTreeWidget, QTreeWidgetItem, QTextEdit, QProgressBar, QDialog, QGroupBox, QFormLayout, QScrollArea, QFrame, QGridLayout, QSizePolicy, QComboBox, QLineEdit, QDialogButtonBox, QSpinBox, QCheckBox, QSplitter, QMenu)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QEvent, QSettings
from PyQt5.QtGui import QFont, QIcon, QColor, QPainter, QDoubleValidator
import matplotlib as mpl
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, butter, filtfilt
from scipy.ndimage import gaussian_filter1d
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
from scipy.signal import stft
from typing import Dict, List, Optional
from types import SimpleNamespace

# 核心数据结构和常量
global_settings = {
    'theme': 'light',
    'font_size': 10,
    'decimal_places': 4,
    'auto_save': True,
    'save_path': os.path.expanduser('~')
}

class ToleranceCalculatorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("公差计算器")
        self.setModal(True)
        self.resize(400, 300)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建输入组
        input_group = QGroupBox("齿轮参数")
        input_layout = QFormLayout()
        
        # 添加参数输入框
        self.m_module_edit = QLineEdit()
        self.z_teeth_edit = QLineEdit()
        self.b_width_edit = QLineEdit()
        self.grade_edit = QComboBox()
        self.grade_edit.addItems(["3", "4", "5", "6", "7", "8", "9"])
        
        input_layout.addRow("模数 m:", self.m_module_edit)
        input_layout.addRow("齿数 z:", self.z_teeth_edit)
        input_layout.addRow("齿宽 b:", self.b_width_edit)
        input_layout.addRow("精度等级:", self.grade_edit)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 创建结果显示组
        result_group = QGroupBox("计算结果")
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # 创建按钮组
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.calculate)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def calculate(self):
        # 简单的公差计算逻辑
        try:
            m = float(self.m_module_edit.text())
            z = int(self.z_teeth_edit.text())
            b = float(self.b_width_edit.text())
            grade = int(self.grade_edit.currentText())
            
            # 根据ISO 1328-1计算基本公差
            if grade < 3 or grade > 9:
                QMessageBox.warning(self, "警告", "精度等级必须在3-9之间")
                return
            
            # 齿距累积公差计算
            fpk = 2.0 * (grade / 3.0) * math.sqrt(m * z)
            
            # 齿廓总公差计算
            fha = 1.6 * (grade / 3.0) * math.sqrt(m)
            
            # 螺旋线总公差计算
            fhb = 1.1 * (grade / 3.0) * math.sqrt(m * (b / 100.0))
            
            # 显示结果
            result = f"齿轮公差计算结果\n\n"
            result += f"模数 m: {m} mm\n"
            result += f"齿数 z: {z}\n"
            result += f"齿宽 b: {b} mm\n"
            result += f"精度等级: ISO {grade}\n\n"
            result += f"齿距累积公差 fpk: {fpk:.3f} μm\n"
            result += f"齿廓总公差 fha: {fha:.3f} μm\n"
            result += f"螺旋线总公差 fhb: {fhb:.3f} μm\n"
            
            self.result_text.setPlainText(result)
            
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的数值")

class FileProcessingThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.stop_flag = False
    
    def run(self):
        try:
            self.progress.emit(10)
            
            if not os.path.exists(self.file_path):
                self.error.emit(f"文件不存在: {self.file_path}")
                return
            
            # 检查文件扩展名
            _, ext = os.path.splitext(self.file_path)
            if ext.lower() != '.mka':
                self.error.emit("仅支持MKA格式文件")
                return
            
            self.progress.emit(30)
            
            # 读取文件内容
            with open(self.file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            
            self.progress.emit(50)
            
            # 解析基本信息
            gear_info = {
                'filename': os.path.basename(self.file_path),
                'path': self.file_path,
                'module': 0.0,
                'teeth': 0,
                'pressure_angle': 20.0,
                'helix_angle': 0.0,
                'measurement_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 提取齿轮参数
            module_match = re.search(r'Modul\s*=\s*([\d.,]+)', content)
            if module_match:
                gear_info['module'] = float(module_match.group(1).replace(',', '.'))
            
            teeth_match = re.search(r'Zaehne\s*=\s*(\d+)', content)
            if teeth_match:
                gear_info['teeth'] = int(teeth_match.group(1))
            
            self.progress.emit(70)
            
            # 提取测量数据
            data_pattern = r'\[Messdaten\](.*?)\[Ende Messdaten\]'
            data_match = re.search(data_pattern, content, re.DOTALL)
            
            if data_match:
                data_content = data_match.group(1)
                lines = data_content.strip().split('\n')
                
                # 解析数据列
                gear_info['raw_data'] = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            parts = list(map(float, line.replace(',', '.').split()))
                            if len(parts) >= 4:  # 角度, X, Y, Z
                                gear_info['raw_data'].append(parts)
                        except ValueError:
                            continue
            
            self.progress.emit(90)
            
            if not gear_info['raw_data']:
                self.error.emit("文件中未找到有效测量数据")
                return
            
            # 转换为numpy数组
            gear_info['data_array'] = np.array(gear_info['raw_data'])
            
            self.progress.emit(100)
            self.finished.emit(gear_info)
            
        except Exception as e:
            self.error.emit(f"文件处理错误: {str(e)}")
    
    def stop(self):
        self.stop_flag = True

class RippleAnalysisThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, gear_data):
        super().__init__()
        self.gear_data = gear_data
        self.settings = {
            'cutoff_frequency': 5.0,
            'window_size': 5,
            'peak_threshold': 0.1
        }
    
    def run(self):
        try:
            self.progress.emit(10)
            
            if not hasattr(self.gear_data, 'data_array') or self.gear_data.data_array.size == 0:
                self.error.emit("没有可用的测量数据")
                return
            
            self.progress.emit(30)
            
            # 提取Z轴数据（波纹数据）
            z_data = self.gear_data.data_array[:, 3]
            
            # 数据预处理
            z_data = z_data - np.mean(z_data)  # 去均值
            
            self.progress.emit(50)
            
            # 低通滤波
            cutoff = self.settings['cutoff_frequency']
            fs = 100.0  # 假设采样频率
            nyq = 0.5 * fs
            normal_cutoff = cutoff / nyq
            b, a = butter(4, normal_cutoff, btype='low', analog=False)
            filtered_data = filtfilt(b, a, z_data)
            
            self.progress.emit(70)
            
            # 检测峰值
            peaks, _ = find_peaks(np.abs(filtered_data), height=self.settings['peak_threshold'])
            
            # 计算波纹参数
            amplitude = np.max(np.abs(filtered_data))
            mean = np.mean(filtered_data)
            rms = np.sqrt(np.mean(filtered_data**2))
            std_dev = np.std(filtered_data)
            
            self.progress.emit(90)
            
            # 准备结果
            results = {
                'amplitude': amplitude,
                'mean': mean,
                'rms': rms,
                'std_dev': std_dev,
                'peak_count': len(peaks),
                'filtered_data': filtered_data,
                'original_data': z_data
            }
            
            self.progress.emit(100)
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"波纹分析错误: {str(e)}")

class RippleAnalysisDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("波纹分析")
        self.setModal(True)
        self.resize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建设置区域
        settings_group = QGroupBox("分析设置")
        settings_layout = QGridLayout()
        
        # 添加设置控件
        settings_layout.addWidget(QLabel("截止频率:"), 0, 0)
        self.cutoff_spin = QDoubleSpinBox()
        self.cutoff_spin.setRange(0.1, 20.0)
        self.cutoff_spin.setValue(5.0)
        settings_layout.addWidget(self.cutoff_spin, 0, 1)
        
        settings_layout.addWidget(QLabel("滤波窗口:"), 0, 2)
        self.window_spin = QSpinBox()
        self.window_spin.setRange(3, 21)
        self.window_spin.setValue(5)
        settings_layout.addWidget(self.window_spin, 0, 3)
        
        settings_layout.addWidget(QLabel("峰值阈值:"), 1, 0)
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.01, 1.0)
        self.threshold_spin.setValue(0.1)
        settings_layout.addWidget(self.threshold_spin, 1, 1)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 创建图表区域
        self.figure = Figure(figsize=(8, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 创建结果区域
        result_group = QGroupBox("分析结果")
        result_layout = QFormLayout()
        
        self.amplitude_label = QLabel("0.0")
        self.rms_label = QLabel("0.0")
        self.peak_count_label = QLabel("0")
        
        result_layout.addRow("最大振幅:", self.amplitude_label)
        result_layout.addRow("RMS值:", self.rms_label)
        result_layout.addRow("峰值数量:", self.peak_count_label)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # 创建按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def plot_data(self, original_data, filtered_data):
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        x = np.arange(len(original_data))
        
        ax.plot(x, original_data, 'b-', alpha=0.5, label='原始数据')
        ax.plot(x, filtered_data, 'r-', label='滤波后数据')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_title('齿轮波纹分析')
        ax.set_xlabel('测量点')
        ax.set_ylabel('Z轴偏差 (μm)')
        
        self.canvas.draw()

class AnalysisSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分析参数设置")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建分析类型选择
        type_group = QGroupBox("分析类型")
        type_layout = QVBoxLayout()
        
        self.ripple_checkbox = QCheckBox("波纹分析")
        self.deviation_checkbox = QCheckBox("偏差分析")
        self.pitch_checkbox = QCheckBox("周节分析")
        
        type_layout.addWidget(self.ripple_checkbox)
        type_layout.addWidget(self.deviation_checkbox)
        type_layout.addWidget(self.pitch_checkbox)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # 创建波纹分析设置
        ripple_group = QGroupBox("波纹分析设置")
        ripple_layout = QFormLayout()
        
        self.ripple_cutoff_edit = QDoubleSpinBox()
        self.ripple_cutoff_edit.setRange(0.1, 20.0)
        self.ripple_cutoff_edit.setValue(5.0)
        
        self.ripple_window_edit = QSpinBox()
        self.ripple_window_edit.setRange(3, 21)
        self.ripple_window_edit.setValue(5)
        
        ripple_layout.addRow("截止频率:", self.ripple_cutoff_edit)
        ripple_layout.addRow("滤波窗口:", self.ripple_window_edit)
        
        ripple_group.setLayout(ripple_layout)
        layout.addWidget(ripple_group)
        
        # 创建按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)

class Gear3DViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D齿轮视图")
        self.resize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建3D图表
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 创建工具栏
        toolbar_layout = QHBoxLayout()
        
        self.rotate_button = QPushButton("旋转视图")
        self.reset_button = QPushButton("重置视图")
        
        toolbar_layout.addWidget(self.rotate_button)
        toolbar_layout.addWidget(self.reset_button)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 连接信号
        self.rotate_button.clicked.connect(self.rotate_view)
        self.reset_button.clicked.connect(self.reset_view)
        
        # 初始化3D图
        self.init_3d_plot()
    
    def init_3d_plot(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.ax.set_title("齿轮3D视图")
        self.ax.set_xlabel("X轴")
        self.ax.set_ylabel("Y轴")
        self.ax.set_zlabel("Z轴")
        self.canvas.draw()
    
    def update_gear_data(self, gear_data):
        if not hasattr(gear_data, 'data_array') or gear_data.data_array.size == 0:
            return
        
        # 提取数据
        x_data = gear_data.data_array[:, 1]
        y_data = gear_data.data_array[:, 2]
        z_data = gear_data.data_array[:, 3]
        
        # 更新3D图表
        self.ax.clear()
        self.ax.scatter(x_data, y_data, z_data, c='b', marker='o', s=1)
        self.ax.set_title(f"齿轮: {gear_data.filename}")
        self.ax.set_xlabel("X轴")
        self.ax.set_ylabel("Y轴")
        self.ax.set_zlabel("Z轴")
        self.canvas.draw()
    
    def rotate_view(self):
        self.ax.view_init(elev=30, azim=45)
        self.canvas.draw()
    
    def reset_view(self):
        self.ax.view_init(elev=0, azim=0)
        self.canvas.draw()

class GearDataViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("齿轮波纹度测量软件")
        self.resize(1200, 800)
        self.setCentralWidget(QWidget())
        
        # 初始化数据
        self.gear_data = None
        self.analysis_results = {}
        self.current_tab = 0
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 初始化UI
        self.init_ui()
        self.create_actions_toolbars_and_menus()
        
        # 自动加载上次文件
        self.auto_load_last_file()
    
    def init_ui(self):
        # 创建主布局
        main_layout = QHBoxLayout(self.centralWidget())
        
        # 创建左侧导航树
        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderLabel("数据导航")
        self.nav_tree.setMaximumWidth(300)
        main_layout.addWidget(self.nav_tree)
        
        # 创建右侧选项卡
        self.tab_widget = QTabWidget()
        
        # 创建各个选项卡
        self.raw_data_tab = QWidget()
        self.analysis_tab = QWidget()
        self.report_tab = QWidget()
        
        self.tab_widget.addTab(self.raw_data_tab, "原始数据")
        self.tab_widget.addTab(self.analysis_tab, "分析结果")
        self.tab_widget.addTab(self.report_tab, "报告")
        
        main_layout.addWidget(self.tab_widget)
        
        # 初始化原始数据选项卡
        self.init_raw_data_tab()
    
    def init_raw_data_tab(self):
        layout = QVBoxLayout(self.raw_data_tab)
        
        # 创建表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["角度", "X轴", "Y轴", "Z轴"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.data_table)
    
    def create_actions_toolbars_and_menus(self):
        # 创建动作
        self.open_action = QAction("打开MKA文件", self)
        self.open_action.triggered.connect(self.open_mka_file)
        
        self.view_3d_action = QAction("3D齿轮视图", self)
        self.view_3d_action.triggered.connect(self.show_3d_view)
        
        self.klingelnberg_report_action = QAction("生成克林贝格报告", self)
        self.klingelnberg_report_action.triggered.connect(self.generate_klingelnberg_report)
        
        # 创建工具栏
        main_toolbar = self.addToolBar("主工具栏")
        main_toolbar.addAction(self.open_action)
        main_toolbar.addSeparator()
        main_toolbar.addAction(self.view_3d_action)
        main_toolbar.addSeparator()
        main_toolbar.addAction(self.klingelnberg_report_action)
        
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        file_menu.addAction(self.open_action)
        
        # 查看菜单
        view_menu = menubar.addMenu("查看")
        view_menu.addAction(self.view_3d_action)
        
        # 报告菜单
        report_menu = menubar.addMenu("报告")
        report_menu.addAction(self.klingelnberg_report_action)
    
    def open_mka_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开MKA文件", "", "MKA文件 (*.mka);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        # 显示进度对话框
        progress_dialog = QProgressDialog("正在加载文件...", "取消", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.show()
        
        # 处理文件
        self.status_bar.showMessage(f"正在加载文件: {os.path.basename(file_path)}")
        
        # 模拟加载进度
        for i in range(101):
            progress_dialog.setValue(i)
            QApplication.processEvents()
            
            if progress_dialog.wasCanceled():
                break
            
            # 实际加载文件（简化版）
            if i == 50:
                # 创建齿轮数据对象
                self.gear_data = SimpleNamespace()
                self.gear_data.filename = os.path.basename(file_path)
                self.gear_data.path = file_path
                self.gear_data.data_array = np.random.rand(1000, 4) * 100  # 模拟数据
                
                # 更新表格
                self.update_data_table()
                
                # 更新导航树
                self.update_navigation_tree()
        
        progress_dialog.close()
        self.status_bar.showMessage(f"文件加载完成: {self.gear_data.filename}")
    
    def update_data_table(self):
        if not self.gear_data or not hasattr(self.gear_data, 'data_array'):
            return
        
        data = self.gear_data.data_array
        self.data_table.setRowCount(data.shape[0])
        
        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                item = QTableWidgetItem(f"{data[row, col]:.3f}")
                item.setTextAlignment(Qt.AlignRight)
                self.data_table.setItem(row, col, item)
    
    def update_navigation_tree(self):
        self.nav_tree.clear()
        
        if not self.gear_data:
            return
        
        # 创建根节点
        root = QTreeWidgetItem(self.nav_tree)
        root.setText(0, self.gear_data.filename)
        
        # 添加子节点
        data_node = QTreeWidgetItem(root)
        data_node.setText(0, "测量数据")
        
        analysis_node = QTreeWidgetItem(root)
        analysis_node.setText(0, "分析结果")
        
        root.setExpanded(True)
    
    def show_3d_view(self):
        if not hasattr(self, 'gear_3d_viewer'):
            self.gear_3d_viewer = Gear3DViewer(self)
        
        if self.gear_data:
            self.gear_3d_viewer.update_gear_data(self.gear_data)
        
        self.gear_3d_viewer.show()
    
    def generate_klingelnberg_report(self):
        if not self.gear_data:
            QMessageBox.warning(self, "警告", "请先加载齿轮数据文件")
            return
        
        # 生成简单的报告
        report_content = f"克林贝格格式报告\n"\
                         f"==================\n\n"\
                         f"文件名称: {self.gear_data.filename}\n"\
                         f"测量时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"\
                         f"数据点数: {self.gear_data.data_array.shape[0] if hasattr(self.gear_data, 'data_array') else 0}\n\n"\
                         f"报告生成完成！\n"
        
        # 保存报告
        save_path, _ = QFileDialog.getSaveFileName(
            self, "保存报告", "klingelnberg_report.txt", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            QMessageBox.information(self, "成功", f"报告已保存至: {save_path}")
    
    def auto_load_last_file(self):
        # 简单实现，实际应用中可以使用QSettings保存上次打开的文件
        pass

class CustomFigureCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.figure.add_subplot(111)
        
        super().__init__(self.figure)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()
    
    def plot_data(self, x_data, y_data, title="", xlabel="", ylabel=""):
        self.axes.clear()
        self.axes.plot(x_data, y_data)
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.axes.grid(True, alpha=0.3)
        self.draw()

# 主程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = GearDataViewer()
    main_window.show()
    sys.exit(app.exec_())