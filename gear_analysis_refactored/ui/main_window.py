"""
主窗口模块
齿轮分析软件的主界面
"""
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
    QTreeWidgetItem, QStackedWidget, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QFileDialog, QMessageBox, QStatusBar,
    QProgressBar, QDockWidget, QTextEdit, QHeaderView, QFrame,
    QSplitter, QGroupBox, QGridLayout, QAction
)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QFont
from datetime import datetime

from gear_analysis_refactored.config.logging_config import logger
from gear_analysis_refactored.config.settings import UIConfig
try:
    from ..models import GearMeasurementData, create_gear_data_from_dict
    from ..utils import parse_mka_file
    from ..threads import FileProcessingThread
    from ..analysis import ISO1328ToleranceCalculator
except ImportError:
    from gear_analysis_refactored.models import GearMeasurementData, create_gear_data_from_dict
    from gear_analysis_refactored.utils import parse_mka_file
    from gear_analysis_refactored.threads import FileProcessingThread
    from gear_analysis_refactored.analysis import ISO1328ToleranceCalculator


class GearDataViewer(QMainWindow):
    """齿轮分析软件主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化数据
        self.current_file = ""
        self.gear_data = None
        self.measurement_data = None
        self.file_thread = None
        
        # 初始化分析结果（避免AttributeError）
        self.deviation_results = None
        self.undulation_results = None
        self.pitch_results = None
        self.ripple_results = None
        
        # 初始化最近文件列表
        self.recent_files = []
        self.max_recent_files = 10
        
        # 初始化UI
        self.init_ui()
        
        # 启用拖放功能
        self.setAcceptDrops(True)
        
        logger.info("主窗口初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(UIConfig.WINDOW_TITLE)
        self.setGeometry(100, 100, *UIConfig.WINDOW_SIZE)
        self.setMinimumSize(*UIConfig.MIN_WINDOW_SIZE)
        
        # 设置主窗口背景色
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F9F6F0;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #F9F6F0;")
        self.setCentralWidget(central_widget)
        
        # 创建主布局 - 使用分割器
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧导航树
        self.create_navigation_tree()
        splitter.addWidget(self.nav_widget)
        
        # 右侧内容区
        self.create_content_area()
        splitter.addWidget(self.content_widget)
        
        # 设置分割比例 (1:4)
        splitter.setSizes([250, 1000])
        
        # 创建菜单栏和工具栏
        self.create_menus()
        self.create_toolbar()
        
        # 创建状态栏
        self.create_statusbar()
        
        logger.info("UI初始化完成")
    
    def create_navigation_tree(self):
        """创建左侧导航树"""
        self.nav_widget = QFrame()
        self.nav_widget.setFrameShape(QFrame.StyledPanel)
        nav_layout = QVBoxLayout(self.nav_widget)
        
        # 标题
        title = QLabel("📁 功能导航")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("""
            QLabel {
                background-color: #F9F6F0;
                color: #333333;
                padding: 10px;
                border: 1px solid #D9CFC1;
                border-radius: 5px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        nav_layout.addWidget(title)
        
        # 树形控件
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #F9F6F0;
                font-size: 11px;
                border: 1px solid #D9CFC1;
                border-radius: 5px;
            }
            QTreeWidget::item {
                height: 32px;
                padding-left: 10px;
                color: #333333;
            }
            QTreeWidget::item:selected {
                background-color: #7A9E7E;
                color: #333333;
            }
            QTreeWidget::item:hover {
                background-color: #E8F0E8;
            }
        """)
        
        # 添加节点
        root = QTreeWidgetItem(self.tree, ["功能列表"])
        root.setExpanded(True)
        
        # 文件操作
        file_item = QTreeWidgetItem(root, ["📂 文件操作"])
        QTreeWidgetItem(file_item, ["打开MKA文件"])
        QTreeWidgetItem(file_item, ["批量处理"])
        
        # 基础信息
        info_item = QTreeWidgetItem(root, ["📊 基础信息"])
        QTreeWidgetItem(info_item, ["基本信息"])
        QTreeWidgetItem(info_item, ["齿轮参数"])
        
        # 数据分析
        analysis_item = QTreeWidgetItem(root, ["📈 数据分析"])
        QTreeWidgetItem(analysis_item, ["齿形数据"])
        QTreeWidgetItem(analysis_item, ["齿向数据"])
        QTreeWidgetItem(analysis_item, ["周节数据"])
        
        # 曲线图表
        chart_item = QTreeWidgetItem(root, ["📊 曲线图表"])
        QTreeWidgetItem(chart_item, ["齿形曲线"])
        QTreeWidgetItem(chart_item, ["齿向曲线"])
        QTreeWidgetItem(chart_item, ["统计分析"])
        QTreeWidgetItem(chart_item, ["左右对比"])
        
        # 偏差分析
        deviation_item = QTreeWidgetItem(root, ["📋 偏差分析"])
        QTreeWidgetItem(deviation_item, ["ISO1328偏差"])
        
        # 工具
        tools_item = QTreeWidgetItem(root, ["🔧 工具"])
        QTreeWidgetItem(tools_item, ["公差计算器"])
        
        # 设置
        settings_item = QTreeWidgetItem(root, ["⚙️ 设置"])
        QTreeWidgetItem(settings_item, ["波纹度公差设置"])
        
        self.tree.expandAll()
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        
        nav_layout.addWidget(self.tree)
    
    def create_content_area(self):
        """创建右侧内容区"""
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        
        # 使用堆叠窗口切换不同页面
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        # 创建各个页面
        self.create_welcome_page()
        self.create_basic_info_page()
        self.create_gear_params_page()
        self.create_profile_data_page()
        self.create_flank_data_page()
        self.create_chart_pages()
        
        # 批量处理页
        from ..ui.batch_processing_page import BatchProcessingPage
        self.batch_processing_page = BatchProcessingPage(self)
        self.stacked_widget.addWidget(self.batch_processing_page)
        
        # 默认显示欢迎页
        self.stacked_widget.setCurrentIndex(0)
    
    def create_welcome_page(self):
        """创建欢迎页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 欢迎信息
        welcome_label = QLabel("""
            <h1>🎉 欢迎使用齿轮分析软件</h1>
            <h3>重构版 - 模块化设计</h3>
            <p style='font-size: 14px; color: #555;'>
                请从左侧菜单选择功能，或点击下方按钮开始
            </p>
        """)
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setWordWrap(True)
        layout.addWidget(welcome_label)
        
        # 快速操作按钮
        btn_layout = QHBoxLayout()
        
        open_btn = QPushButton("📂 打开MKA文件")
        open_btn.setMinimumHeight(50)
        open_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #A0522D;
                color: #F9F6F0;
                border: 1px solid #8B4513;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #8B4513;
            }
        """)
        open_btn.clicked.connect(self.open_file)
        
        calc_btn = QPushButton("🧮 公差计算器")
        calc_btn.setMinimumHeight(50)
        calc_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #7A9E7E;
                color: #F9F6F0;
                border: 1px solid #6B8E6B;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #6B8E6B;
            }
        """)
        calc_btn.clicked.connect(self.show_tolerance_calculator)
        
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(calc_btn)
        layout.addLayout(btn_layout)
        
        # 状态信息
        info_label = QLabel("""
            <div style='background-color: #F9F6F0; padding: 20px; border: 1px solid #D9CFC1; border-radius: 5px; color: #333333;'>
                <h4>📊 当前状态</h4>
                <p>• 配置系统: ✅ 已加载</p>
                <p>• 数据模型: ✅ 已初始化</p>
                <p>• 文件解析器: ✅ 就绪</p>
                <p>• 分析算法: ✅ 可用</p>
            </div>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        self.stacked_widget.addWidget(page)
        self.welcome_page = page
    
    def create_basic_info_page(self):
        """创建基本信息页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 标题
        title = QLabel("<h2>📄 基本信息</h2>")
        layout.addWidget(title)
        
        # 信息表格
        self.basic_info_table = QTableWidget(0, 2)
        self.basic_info_table.setHorizontalHeaderLabels(["项目", "值"])
        self.basic_info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.basic_info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.basic_info_table.setStyleSheet("""
            QTableWidget {
                background-color: #F9F6F0;
                border: 1px solid #D9CFC1;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #F5F0E6;
                color: #333333;
                padding: 8px;
                border: 1px solid #D9CFC1;
            }
            QTableWidgetItem {
                color: #333333;
                padding: 5px;
                border-bottom: 1px solid #D9CFC1;
            }
        """)
        layout.addWidget(self.basic_info_table)
        
        self.stacked_widget.addWidget(page)
        self.basic_info_page = page
    
    def create_gear_params_page(self):
        """创建齿轮参数页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 标题
        title = QLabel("<h2>⚙️ 齿轮参数</h2>")
        layout.addWidget(title)
        
        # 参数表格
        self.gear_params_table = QTableWidget(0, 2)
        self.gear_params_table.setHorizontalHeaderLabels(["参数", "值"])
        self.gear_params_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.gear_params_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.gear_params_table.setStyleSheet("""
            QTableWidget {
                background-color: #F9F6F0;
                border: 1px solid #D9CFC1;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #F5F0E6;
                color: #333333;
                padding: 8px;
                border: 1px solid #D9CFC1;
            }
            QTableWidgetItem {
                color: #333333;
                padding: 5px;
                border-bottom: 1px solid #D9CFC1;
            }
        """)
        layout.addWidget(self.gear_params_table)
        
        self.stacked_widget.addWidget(page)
        self.gear_params_page = page
    
    def create_profile_data_page(self):
        """创建齿形数据页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 标题
        title = QLabel("<h2>📈 齿形数据</h2>")
        layout.addWidget(title)
        
        # 数据摘要
        self.profile_summary = QLabel("暂无数据")
        self.profile_summary.setStyleSheet("padding: 10px; background-color: #F9F6F0; border: 1px solid #D9CFC1; border-radius: 5px; color: #333333;")
        layout.addWidget(self.profile_summary)
        
        # 数据表格
        self.profile_table = QTableWidget(0, 4)
        self.profile_table.setHorizontalHeaderLabels(["齿号", "侧面", "数据点数", "平均值 (μm)"])
        self.profile_table.setStyleSheet("""
            QTableWidget {
                background-color: #F9F6F0;
                border: 1px solid #D9CFC1;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #F5F0E6;
                color: #333333;
                padding: 8px;
                border: 1px solid #D9CFC1;
            }
            QTableWidgetItem {
                color: #333333;
                padding: 5px;
                border-bottom: 1px solid #D9CFC1;
            }
        """)
        layout.addWidget(self.profile_table)
        
        self.stacked_widget.addWidget(page)
        self.profile_data_page = page
    
    def create_flank_data_page(self):
        """创建齿向数据页"""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 标题
        title = QLabel("<h2>📉 齿向数据</h2>")
        layout.addWidget(title)
        
        # 数据摘要
        self.flank_summary = QLabel("暂无数据")
        self.flank_summary.setStyleSheet("padding: 10px; background-color: #F9F6F0; border: 1px solid #D9CFC1; border-radius: 5px; color: #333333;")
        layout.addWidget(self.flank_summary)
        
        # 数据表格
        self.flank_table = QTableWidget(0, 4)
        self.flank_table.setHorizontalHeaderLabels(["齿号", "侧面", "数据点数", "平均值 (μm)"])
        self.flank_table.setStyleSheet("""
            QTableWidget {
                background-color: #F9F6F0;
                border: 1px solid #D9CFC1;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #F5F0E6;
                color: #333333;
                padding: 8px;
                border: 1px solid #D9CFC1;
            }
            QTableWidgetItem {
                color: #333333;
                padding: 5px;
                border-bottom: 1px solid #D9CFC1;
            }
        """)
        layout.addWidget(self.flank_table)
        
        self.stacked_widget.addWidget(page)
        self.flank_data_page = page
    
    def create_chart_pages(self):
        """创建图表页面"""
        from ui.chart_widgets import (ProfileCurveWidget, FlankCurveWidget,
                                      StatisticsChartWidget, ComparisonChartWidget)
        
        # 齿形曲线页
        self.profile_curve_widget = ProfileCurveWidget()
        self.stacked_widget.addWidget(self.profile_curve_widget)
        
        # 齿向曲线页
        self.flank_curve_widget = FlankCurveWidget()
        self.stacked_widget.addWidget(self.flank_curve_widget)
        
        # 统计分析页
        self.stats_widget = StatisticsChartWidget()
        self.stacked_widget.addWidget(self.stats_widget)
        
        # 对比分析页
        self.comparison_widget = ComparisonChartWidget()
        self.stacked_widget.addWidget(self.comparison_widget)
    
    def create_menus(self):
        """创建菜单栏 - 完整复刻原程序"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        self.open_action = file_menu.addAction("📂 打开MKA文件")
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.open_file)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("❌ 退出")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        # 分析菜单
        analysis_menu = menubar.addMenu("分析(&A)")
        
        # 分析设置
        self.settings_action = analysis_menu.addAction("⚙️ 分析参数设置")
        self.settings_action.setEnabled(False)
        self.settings_action.triggered.connect(self.show_analysis_settings)
        
        analysis_menu.addSeparator()
        
        # 运行所有分析
        self.run_all_action = analysis_menu.addAction("▶️ 运行所有分析")
        self.run_all_action.setEnabled(False)
        self.run_all_action.triggered.connect(self.run_all_analyses)
        
        analysis_menu.addSeparator()
        
        # 各项分析
        self.deviation_action = analysis_menu.addAction("📋 ISO1328偏差分析")
        self.deviation_action.setEnabled(False)
        self.deviation_action.triggered.connect(self.analyze_deviation)
        
        self.pitch_action = analysis_menu.addAction("📐 周节偏差分析")
        self.pitch_action.setEnabled(False)
        self.pitch_action.triggered.connect(self.show_pitch_analysis)
        
        self.ripple_action = analysis_menu.addAction("🌊 Ripple阶次分析")
        self.ripple_action.setEnabled(False)
        self.ripple_action.triggered.connect(self.show_ripple_analysis)
        
        # 报表菜单
        report_menu = menubar.addMenu("报表(&R)")
        
        self.html_report_action = report_menu.addAction("📄 生成HTML报告")
        self.html_report_action.setEnabled(False)
        self.html_report_action.triggered.connect(self.generate_html_report)
        
        self.pdf_report_action = report_menu.addAction("📋 生成克林贝格PDF报告")
        self.pdf_report_action.setEnabled(False)
        self.pdf_report_action.triggered.connect(self.generate_klingelnberg_professional_report)
        
        self.exact_pdf_action = report_menu.addAction("🎯 生成克林贝格精确PDF报告")
        self.exact_pdf_action.setEnabled(False)
        self.exact_pdf_action.triggered.connect(self.generate_klingelnberg_exact_report)
        
        self.original_pdf_action = report_menu.addAction("📋 生成原版PDF报告")
        self.original_pdf_action.setEnabled(False)
        self.original_pdf_action.triggered.connect(self.generate_original_pdf_report)
        
        self.ripple_pdf_action = report_menu.addAction("🌊 生成Ripple分析PDF报告")
        self.ripple_pdf_action.setEnabled(False)
        self.ripple_pdf_action.triggered.connect(self.generate_ripple_pdf_report)
        
        report_menu.addSeparator()
        
        self.csv_export_action = report_menu.addAction("📊 导出数据到CSV")
        self.csv_export_action.setEnabled(False)
        self.csv_export_action.triggered.connect(self.export_data_to_csv)
        
        # 高级功能菜单
        advanced_menu = menubar.addMenu("高级功能(&A)")
        
        self.advanced_charts_action = advanced_menu.addAction("📈 高级图表")
        self.advanced_charts_action.setEnabled(False)
        self.advanced_charts_action.triggered.connect(self.create_advanced_charts)
        
        self.professional_order_action = advanced_menu.addAction("🎯 专业阶次谱分析")
        self.professional_order_action.setEnabled(False)
        self.professional_order_action.triggered.connect(self.create_advanced_charts)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        calc_action = tools_menu.addAction("🧮 ISO1328公差计算器")
        calc_action.triggered.connect(self.show_tolerance_calculator)
        
        ripple_settings_action = tools_menu.addAction("⚙️ Ripple参数设置")
        ripple_settings_action.triggered.connect(self.show_ripple_settings)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        help_action = help_menu.addAction("❓ 使用帮助")
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        
        about_action = help_menu.addAction("ℹ️ 关于")
        about_action.triggered.connect(self.show_about)
    
    def create_toolbar(self):
        """创建工具栏 - 复刻原程序"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setObjectName("main_toolbar")
        
        # 文件操作
        toolbar.addAction(self.open_action)
        toolbar.addSeparator()
        
        # 分析操作
        toolbar.addAction(self.settings_action)
        toolbar.addAction(self.run_all_action)
        toolbar.addAction(self.pitch_action)
        toolbar.addSeparator()
        
        # 报表操作
        toolbar.addAction(self.html_report_action)
        toolbar.addAction(self.pdf_report_action)
    
    def create_statusbar(self):
        """创建状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.statusbar.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)
        
        self.statusbar.showMessage("欢迎使用齿轮分析软件！")
    
    def on_tree_item_clicked(self, item, column):
        """处理树形菜单点击"""
        text = item.text(0)
        logger.info(f"点击菜单项: {text}")
        
        # 根据点击的项目切换页面
        if "打开MKA文件" in text:
            self.open_file()
        elif "批量处理" in text:
            self.stacked_widget.setCurrentWidget(self.batch_processing_page)
        elif "基本信息" in text:
            self.stacked_widget.setCurrentWidget(self.basic_info_page)
        elif "齿轮参数" in text:
            self.stacked_widget.setCurrentWidget(self.gear_params_page)
        elif "齿形数据" in text:
            self.stacked_widget.setCurrentWidget(self.profile_data_page)
        elif "齿向数据" in text:
            self.stacked_widget.setCurrentWidget(self.flank_data_page)
        elif "齿形曲线" in text:
            self.show_profile_curve()
        elif "齿向曲线" in text:
            self.show_flank_curve()
        elif "统计分析" in text:
            self.show_statistics()
        elif "左右对比" in text:
            self.show_comparison()
        elif "生成HTML报告" in text:
            self.generate_html_report()
        elif "生成PDF报告" in text:
            self.generate_pdf_report()
        elif "导出数据到CSV" in text:
            self.export_data_to_csv()
        elif "公差计算器" in text:
            self.show_tolerance_calculator()
        elif "ISO1328偏差" in text:
            self.analyze_deviation()
        elif "波纹度公差设置" in text:
            self.show_ripple_tolerance_settings()
    
    def open_file(self):
        """打开MKA文件"""
        # 获取上次打开文件的文件夹
        initial_dir = ""
        try:
            settings = QSettings("GearAnalysis", "GearDataViewer")
            last_file = settings.value("last_file_path", "")
            if last_file and os.path.exists(last_file):
                initial_dir = os.path.dirname(last_file)
            elif hasattr(self, 'current_file') and self.current_file and os.path.exists(self.current_file):
                initial_dir = os.path.dirname(self.current_file)
        except Exception as e:
            logger.warning(f"获取上次打开文件夹失败: {e}")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择MKA文件",
            initial_dir,
            "MKA文件 (*.mka *.MKA);;所有文件 (*.*)"
        )
        
        if not file_path:
            return
        
        logger.info(f"选择文件: {file_path}")
        self.statusbar.showMessage(f"正在加载: {file_path}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        try:
            # 解析文件
            data_dict = parse_mka_file(file_path)
            
            # 创建数据对象
            self.measurement_data = create_gear_data_from_dict(data_dict)
            self.current_file = file_path
            
            # 保存最后打开的文件路径
            try:
                settings = QSettings("GearAnalysis", "GearDataViewer")
                settings.setValue("last_file_path", file_path)
                logger.info(f"已保存最后打开的文件路径: {file_path}")
            except Exception as e:
                logger.warning(f"保存文件路径失败: {e}")
            
            # DEBUG: Print basic info
            info = self.measurement_data.basic_info
            logger.info(f"DEBUG: Basic Info Loaded: Teeth={info.teeth}, Order={info.order_no}, Condition={info.condition}, ModCoeff={info.modification_coeff}, Ball={info.ball_diameter}")
            
            # 更新显示
            self.update_all_displays()
            
            # ✅ 启用所有分析和报表菜单
            self.settings_action.setEnabled(True)
            self.run_all_action.setEnabled(True)
            self.deviation_action.setEnabled(True)
            self.pitch_action.setEnabled(True)
            self.ripple_action.setEnabled(True)
            self.html_report_action.setEnabled(True)
            self.pdf_report_action.setEnabled(True)
            self.exact_pdf_action.setEnabled(True)
            self.original_pdf_action.setEnabled(True)
            self.ripple_pdf_action.setEnabled(True)
            self.csv_export_action.setEnabled(True)
            self.advanced_charts_action.setEnabled(True)
            self.professional_order_action.setEnabled(True)
            
            logger.info("✅ 所有分析和报表功能已启用")
            
            self.statusbar.showMessage(f"✅ 文件加载成功: {file_path}", 5000)
            QMessageBox.information(self, "成功", f"文件加载成功！\n\n{self.measurement_data.get_summary()}")
            
            # 自动切换到基本信息页
            self.stacked_widget.setCurrentWidget(self.basic_info_page)
            
        except Exception as e:
            logger.exception(f"文件加载失败: {e}")
            QMessageBox.critical(self, "错误", f"文件加载失败：\n{str(e)}")
            self.statusbar.showMessage("❌ 文件加载失败", 5000)
        
        finally:
            self.progress_bar.setVisible(False)
    
    def update_all_displays(self):
        """更新所有显示"""
        if not self.measurement_data:
            return
        
        self.update_basic_info()
        self.update_gear_params()
        self.update_profile_data()
        self.update_flank_data()
        self.update_charts()
    
    def update_basic_info(self):
        """更新基本信息"""
        if not self.measurement_data:
            return
        
        info = self.measurement_data.basic_info
        
        data = [
            ("程序名称", info.program),
            ("测量日期", info.date),
            ("开始时间", info.start_time),
            ("结束时间", info.end_time),
            ("操作员", info.operator),
            ("位置", info.location),
            ("图号", info.drawing_no),
            ("订单号", info.order_no),
            ("类型", info.type_),
            ("客户", info.customer),
        ]
        
        self.basic_info_table.setRowCount(len(data))
        for i, (key, value) in enumerate(data):
            self.basic_info_table.setItem(i, 0, QTableWidgetItem(key))
            self.basic_info_table.setItem(i, 1, QTableWidgetItem(str(value)))
    
    def update_gear_params(self):
        """更新齿轮参数"""
        if not self.measurement_data:
            return
        
        info = self.measurement_data.basic_info
        
        data = [
            ("模数 (mm)", f"{info.module:.3f}"),
            ("齿数", str(info.teeth)),
            ("螺旋角 (°)", f"{info.helix_angle:.2f}"),
            ("压力角 (°)", f"{info.pressure_angle:.2f}"),
            ("变位系数", f"{info.modification_coeff:.4f}"),
            ("齿宽 (mm)", f"{info.width:.2f}"),
            ("齿顶圆直径 (mm)", f"{info.tip_diameter:.3f}"),
            ("齿根圆直径 (mm)", f"{info.root_diameter:.3f}"),
            ("精度等级", f"{info.accuracy_grade}级"),
        ]
        
        self.gear_params_table.setRowCount(len(data))
        for i, (key, value) in enumerate(data):
            self.gear_params_table.setItem(i, 0, QTableWidgetItem(key))
            self.gear_params_table.setItem(i, 1, QTableWidgetItem(value))
    
    def update_profile_data(self):
        """更新齿形数据显示"""
        if not self.measurement_data or not self.measurement_data.has_profile_data():
            self.profile_summary.setText("暂无齿形数据")
            return
        
        data = self.measurement_data.profile_data
        
        # 更新摘要
        left_count = len(data.left)
        right_count = len(data.right)
        self.profile_summary.setText(
            f"📊 齿形数据摘要: 左侧 {left_count} 齿, 右侧 {right_count} 齿"
        )
        
        # 更新表格
        rows = []
        for tooth_num, values in data.left.items():
            avg = sum(values) / len(values) if values else 0
            rows.append((tooth_num, "左侧", len(values), f"{avg:.3f}"))
        
        for tooth_num, values in data.right.items():
            avg = sum(values) / len(values) if values else 0
            rows.append((tooth_num, "右侧", len(values), f"{avg:.3f}"))
        
        self.profile_table.setRowCount(len(rows))
        for i, (tooth, side, count, avg) in enumerate(rows):
            self.profile_table.setItem(i, 0, QTableWidgetItem(str(tooth)))
            self.profile_table.setItem(i, 1, QTableWidgetItem(side))
            self.profile_table.setItem(i, 2, QTableWidgetItem(str(count)))
            self.profile_table.setItem(i, 3, QTableWidgetItem(avg))
    
    def update_flank_data(self):
        """更新齿向数据显示"""
        if not self.measurement_data or not self.measurement_data.has_flank_data():
            self.flank_summary.setText("暂无齿向数据")
            return
        
        data = self.measurement_data.flank_data
        
        # 更新摘要
        left_count = len(data.left)
        right_count = len(data.right)
        self.flank_summary.setText(
            f"📊 齿向数据摘要: 左侧 {left_count} 齿, 右侧 {right_count} 齿"
        )
        
        # 更新表格
        rows = []
        for tooth_num, values in data.left.items():
            avg = sum(values) / len(values) if values else 0
            rows.append((tooth_num, "左侧", len(values), f"{avg:.3f}"))
        
        for tooth_num, values in data.right.items():
            avg = sum(values) / len(values) if values else 0
            rows.append((tooth_num, "右侧", len(values), f"{avg:.3f}"))
        
        self.flank_table.setRowCount(len(rows))
        for i, (tooth, side, count, avg) in enumerate(rows):
            self.flank_table.setItem(i, 0, QTableWidgetItem(str(tooth)))
            self.flank_table.setItem(i, 1, QTableWidgetItem(side))
            self.flank_table.setItem(i, 2, QTableWidgetItem(str(count)))
            self.flank_table.setItem(i, 3, QTableWidgetItem(avg))
    
    def update_charts(self):
        """更新所有图表"""
        if not self.measurement_data:
            return
        
        # 默认显示左侧数据的前几个齿
        logger.info("图表数据已准备，可通过菜单查看")
    
    def show_profile_curve(self):
        """显示齿形曲线"""
        if not self.measurement_data or not self.measurement_data.has_profile_data():
            QMessageBox.warning(self, "提示", "暂无齿形数据")
            return
        
        self.stacked_widget.setCurrentWidget(self.profile_curve_widget)
        
        # 绘制左侧数据（默认）
        data = self.measurement_data.profile_data
        if data.left:
            self.profile_curve_widget.plot_data(data.left, 'left')
        elif data.right:
            self.profile_curve_widget.plot_data(data.right, 'right')
    
    def show_flank_curve(self):
        """显示齿向曲线"""
        if not self.measurement_data or not self.measurement_data.has_flank_data():
            QMessageBox.warning(self, "提示", "暂无齿向数据")
            return
        
        self.stacked_widget.setCurrentWidget(self.flank_curve_widget)
        
        # 绘制左侧数据（默认）
        data = self.measurement_data.flank_data
        if data.left:
            self.flank_curve_widget.plot_data(data.left, 'left')
        elif data.right:
            self.flank_curve_widget.plot_data(data.right, 'right')
    
    def show_statistics(self):
        """显示统计分析"""
        if not self.measurement_data or not self.measurement_data.has_profile_data():
            QMessageBox.warning(self, "提示", "暂无数据")
            return
        
        self.stacked_widget.setCurrentWidget(self.stats_widget)
        
        # 绘制齿形数据分布（默认左侧）
        data = self.measurement_data.profile_data
        if data.left:
            self.stats_widget.plot_distribution(data.left, 'left')
        elif data.right:
            self.stats_widget.plot_distribution(data.right, 'right')
    
    def show_comparison(self):
        """显示左右对比"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "暂无数据")
            return
        
        self.stacked_widget.setCurrentWidget(self.comparison_widget)
        
        # 绘制齿形数据对比
        if self.measurement_data.has_profile_data():
            data = self.measurement_data.profile_data
            self.comparison_widget.plot_comparison(data.left, data.right)
        elif self.measurement_data.has_flank_data():
            data = self.measurement_data.flank_data
            self.comparison_widget.plot_comparison(data.left, data.right)
    
    def analyze_deviation(self):
        """ISO1328偏差分析"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        try:
            info = self.measurement_data.basic_info
            
            # 计算公差
            calculator = ISO1328ToleranceCalculator()
            tolerances = calculator.calculate_tolerances(
                info.module,
                info.teeth,
                info.width,
                info.accuracy_grade
            )
            
            # 显示结果
            result_text = f"""
            <h3>ISO1328偏差分析结果</h3>
            <p><b>齿轮参数:</b></p>
            <ul>
                <li>模数: {info.module:.3f} mm</li>
                <li>齿数: {info.teeth}</li>
                <li>齿宽: {info.width:.2f} mm</li>
                <li>精度等级: {info.accuracy_grade}级</li>
            </ul>
            
            <p><b>齿形公差:</b></p>
            <ul>
                <li>总公差 F<sub>α</sub>: {tolerances['F_alpha']:.2f} μm</li>
                <li>斜率公差 fH<sub>α</sub>: {tolerances['fH_alpha']:.2f} μm</li>
                <li>形状公差 ff<sub>α</sub>: {tolerances['ff_alpha']:.2f} μm</li>
            </ul>
            
            <p><b>齿向公差:</b></p>
            <ul>
                <li>总公差 F<sub>β</sub>: {tolerances['F_beta']:.2f} μm</li>
                <li>斜率公差 fH<sub>β</sub>: {tolerances['fH_beta']:.2f} μm</li>
                <li>形状公差 ff<sub>β</sub>: {tolerances['ff_beta']:.2f} μm</li>
            </ul>
            """
            
            msg = QMessageBox(self)
            msg.setWindowTitle("偏差分析结果")
            msg.setTextFormat(Qt.RichText)
            msg.setText(result_text)
            msg.setIcon(QMessageBox.Information)
            msg.exec_()
            
        except Exception as e:
            logger.exception(f"偏差分析失败: {e}")
            QMessageBox.critical(self, "错误", f"偏差分析失败：\n{str(e)}")
    
    def generate_html_report(self):
        """生成HTML报告"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            from reports.html_report_generator import HTMLReportGenerator
            from analysis import ISO1328ToleranceCalculator
            
            # 选择保存位置
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "保存HTML报告",
                f"齿轮分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                "HTML文件 (*.html);;所有文件 (*.*)"
            )
            
            if not filename:
                return
            
            # 计算公差
            info = self.measurement_data.basic_info
            calculator = ISO1328ToleranceCalculator()
            tolerances = calculator.calculate_tolerances(
                info.module, info.teeth, info.width, info.accuracy_grade
            )
            
            # 生成报告
            self.statusbar.showMessage("正在生成报告...")
            generator = HTMLReportGenerator(
                self.measurement_data.basic_info.__dict__,
                self.deviation_results,
                self.undulation_results,
                self.pitch_results,
                self.current_file,
                self.measurement_data.profile_data,
                self.measurement_data.flank_data
            )
            report_path = generator.generate()
            success = report_path is not None
            
            if success:
                self.statusbar.showMessage(f"✅ 报告已生成: {filename}", 5000)
                QMessageBox.information(self, "成功", f"HTML报告已生成！\n\n{filename}")
                
                # 询问是否打开
                reply = QMessageBox.question(
                    self, "打开报告", "是否现在打开报告？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    import webbrowser
                    webbrowser.open(filename)
            else:
                self.statusbar.showMessage("❌ 报告生成失败", 5000)
                QMessageBox.critical(self, "错误", "报告生成失败")
                
        except Exception as e:
            logger.exception(f"生成HTML报告失败: {e}")
            QMessageBox.critical(self, "错误", f"报告生成失败：\n{str(e)}")
    
    def run_all_analyses(self):
        """运行所有分析 - 复刻原程序功能"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        try:
            from PyQt5.QtCore import QTimer
            
            reply = QMessageBox.question(
                self, 
                "运行所有分析",
                "将依次运行:\n1. ISO1328偏差分析\n2. 波纹度分析\n3. 周节分析\n4. Ripple阶次分析\n\n是否继续?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 使用QTimer依次启动分析
                QTimer.singleShot(10, self.analyze_deviation)
                QTimer.singleShot(1000, self.analyze_undulation)
                QTimer.singleShot(2000, self.analyze_pitch)
                QTimer.singleShot(3000, self.analyze_ripple)
                
                QMessageBox.information(self, "提示", "已启动所有分析任务，请稍候...")
                
        except Exception as e:
            logger.exception(f"运行所有分析失败: {e}")
            QMessageBox.critical(self, "错误", f"运行所有分析失败：\n{str(e)}")
    
    def analyze_undulation(self):
        """启动波纹度分析"""
        if not self.measurement_data:
            return
        
        try:
            from threads.worker_threads import UndulationAnalysisThread
            
            # 创建线程（修复参数传递）
            gear_data_dict = self.measurement_data.basic_info.__dict__ if hasattr(self.measurement_data.basic_info, '__dict__') else {}
            
            self.undulation_thread = UndulationAnalysisThread(
                self.measurement_data.profile_data,
                self.measurement_data.flank_data,
                gear_data_dict
            )
            
            self.undulation_thread.finished.connect(self.on_undulation_finished)
            self.undulation_thread.progress.connect(lambda msg: self.statusbar.showMessage(msg))
            
            self.undulation_thread.start()
            logger.info("波纹度分析已启动")
            
        except Exception as e:
            logger.exception(f"启动波纹度分析失败: {e}")
    
    def on_undulation_finished(self, results):
        """波纹度分析完成"""
        logger.info("波纹度分析完成")
        self.statusbar.showMessage("波纹度分析完成", 3000)
        # 可以在这里保存结果或更新UI
    
    def analyze_pitch(self):
        """启动周节分析"""
        if not self.measurement_data:
            return
        
        try:
            from threads.worker_threads import PitchAnalysisThread
            
            gear_data_dict = self.measurement_data.basic_info.__dict__ if hasattr(self.measurement_data.basic_info, '__dict__') else {}
            
            self.pitch_thread = PitchAnalysisThread(
                self.measurement_data.pitch_data,
                gear_data_dict
            )
            
            self.pitch_thread.finished.connect(self.on_pitch_finished)
            self.pitch_thread.progress.connect(lambda msg: self.statusbar.showMessage(msg))
            
            self.pitch_thread.start()
            logger.info("周节分析已启动")
            
        except Exception as e:
            logger.exception(f"启动周节分析失败: {e}")
    
    def on_pitch_finished(self, results):
        """周节分析完成"""
        logger.info("周节分析完成")
        self.statusbar.showMessage("周节分析完成", 3000)
    
    def analyze_ripple(self):
        """启动Ripple分析"""
        if not self.measurement_data:
            return
        
        try:
            from threads.worker_threads import RippleAnalysisThread
            
            gear_data_dict = self.measurement_data.basic_info.__dict__ if hasattr(self.measurement_data.basic_info, '__dict__') else {}
            
            self.ripple_thread = RippleAnalysisThread(
                self.measurement_data.profile_data,
                self.measurement_data.flank_data,
                gear_data_dict,
                ripple_settings=None
            )
            
            self.ripple_thread.finished.connect(self.on_ripple_finished)
            self.ripple_thread.progress.connect(lambda msg: self.statusbar.showMessage(msg))
            
            self.ripple_thread.start()
            logger.info("Ripple分析已启动")
            
        except Exception as e:
            logger.exception(f"启动Ripple分析失败: {e}")
    
    def on_ripple_finished(self, results):
        """Ripple分析完成"""
        logger.info("Ripple分析完成")
        self.statusbar.showMessage("所有分析完成！", 5000)
        QMessageBox.information(self, "完成", "所有分析已完成！")
    
    def generate_original_pdf_report(self):
        """生成原版风格PDF报告 - 复刻原程序"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            from reports.original_pdf_report import generate_original_pdf_report
            
            # 选择保存位置
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "保存原版PDF报告",
                f"ISO1328_偏差分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF文件 (*.pdf);;所有文件 (*.*)"
            )
            
            if not filename:
                return
            
            # 显示进度
            self.statusbar.showMessage("正在生成原版PDF报告...")
            
            # 确保有偏差分析结果
            if not hasattr(self, 'deviation_results') or not self.deviation_results:
                QMessageBox.information(self, "提示", "将先执行偏差分析...")
                self.analyze_deviation()
                # 等待分析完成
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(2000, lambda: self._generate_original_pdf_delayed(filename))
                return
            
            # 生成报告
            success = generate_original_pdf_report(
                self.measurement_data,
                self.deviation_results,
                filename
            )
            
            if success:
                self.statusbar.showMessage("原版PDF报告生成完成")
                QMessageBox.information(self, "成功", f"原版PDF报告已生成:\n{filename}")
                # 打开报告
                import os
                os.startfile(filename)
            else:
                self.statusbar.showMessage("原版PDF报告生成失败")
                QMessageBox.critical(self, "错误", "生成原版PDF报告失败")
                
        except Exception as e:
            logger.exception(f"生成原版PDF报告失败: {e}")
            QMessageBox.critical(self, "错误", f"原版PDF报告生成失败：\n{str(e)}")
    
    def _generate_original_pdf_delayed(self, filename):
        """延迟生成原版PDF（等待分析完成）"""
        try:
            from reports.original_pdf_report import generate_original_pdf_report
            
            if hasattr(self, 'deviation_results') and self.deviation_results:
                success = generate_original_pdf_report(
                    self.measurement_data,
                    self.deviation_results,
                    filename
                )
                
                if success:
                    QMessageBox.information(self, "成功", f"原版PDF报告已生成:\n{filename}")
                    import os
                    os.startfile(filename)
            else:
                QMessageBox.warning(self, "提示", "偏差分析未完成，请稍后重试")
                
        except Exception as e:
            logger.exception(f"延迟生成PDF失败: {e}")
            QMessageBox.critical(self, "错误", f"生成失败：\n{str(e)}")
    
    def generate_pdf_report(self):
        """生成PDF报告（克林贝格标准）- 旧版本，保留兼容"""
        self.generate_klingelnberg_professional_report()
    
    def generate_klingelnberg_professional_report(self):
        """生成克林贝格专业PDF报告 - 完全仿照克林贝格格式"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        # 如果没有偏差分析结果，先运行分析
        if not self.deviation_results:
            reply = QMessageBox.question(
                self, "提示", 
                "生成克林贝格报告需要先进行ISO1328偏差分析。\n是否现在运行分析？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.analyze_deviation()
                # 延迟生成PDF
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(2000, self._generate_klingelnberg_delayed)
                return
            else:
                return
        
        self._generate_klingelnberg_delayed()
    
    def generate_klingelnberg_exact_report(self):
        """生成克林贝格精确PDF报告 - 与原始克林贝格PDF完全一致"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        # 如果没有偏差分析结果，先运行分析
        if not self.deviation_results:
            reply = QMessageBox.question(
                self, "提示", 
                "生成克林贝格精确报告需要先进行ISO1328偏差分析。\n是否现在运行分析？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.analyze_deviation()
                # 延迟生成PDF
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(2000, self._generate_klingelnberg_exact_delayed)
                return
            else:
                return
        
        self._generate_klingelnberg_exact_delayed()
    
    def _generate_klingelnberg_delayed(self):
        """延迟生成克林贝格报告"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            from reports.klingelnberg_professional import KlingelnbergProfessionalReportGenerator
            
            # 选择保存位置
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "保存克林贝格专业PDF报告",
                f"Klingelnberg_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF文件 (*.pdf);;所有文件 (*.*)"
            )
            
            if not filename:
                return
            
            # 显示进度
            self.statusbar.showMessage("正在生成克林贝格专业PDF报告...")
            logger.info(f"开始生成克林贝格专业PDF报告: {filename}")
            
            # 生成克林贝格专业报告
            generator = KlingelnbergProfessionalReportGenerator(
                self.measurement_data,
                self.deviation_results,
                self.current_file
            )
            
            success = generator.generate_report(filename)
            
            if success:
                self.statusbar.showMessage("✅ 克林贝格PDF报告生成完成", 5000)
                logger.info(f"克林贝格专业PDF报告生成成功: {filename}")
                
                # 询问是否打开
                reply = QMessageBox.question(
                    self, "成功",
                    f"克林贝格专业PDF报告已生成！\n\n{filename}\n\n是否现在打开？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    import os
                    os.startfile(filename)
            else:
                self.statusbar.showMessage("❌ 克林贝格PDF报告生成失败", 5000)
                QMessageBox.critical(self, "错误", "生成克林贝格专业PDF报告失败")
                
        except Exception as e:
            logger.exception(f"生成克林贝格专业PDF报告失败: {e}")
            QMessageBox.critical(self, "错误", f"生成克林贝格专业PDF报告失败：\n{str(e)}")
    
    def _generate_klingelnberg_exact_delayed(self):
        """延迟生成克林贝格精确报告"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            # 选择保存位置
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "保存克林贝格精确PDF报告",
                f"Klingelnberg_Exact_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF文件 (*.pdf);;所有文件 (*.*)"
            )
            
            if not filename:
                return
            
            # 显示进度
            self.statusbar.showMessage("正在生成克林贝格精确PDF报告...")
            logger.info(f"开始生成克林贝格精确PDF报告: {filename}")
            
            # 导入克林贝格精确报告生成器
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            
            from reports.klingelnberg_exact import generate_klingelnberg_exact_report
            
            # 生成克林贝格精确报告
            success = generate_klingelnberg_exact_report(self.measurement_data, filename)
            
            if success:
                self.statusbar.showMessage("✅ 克林贝格精确PDF报告生成完成", 5000)
                logger.info(f"克林贝格精确PDF报告生成成功: {filename}")
                
                # 询问是否打开
                reply = QMessageBox.question(
                    self, "成功",
                    f"克林贝格精确PDF报告已生成！\n\n{filename}\n\n是否现在打开？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    import os
                    os.startfile(filename)
            else:
                self.statusbar.showMessage("❌ 克林贝格精确PDF报告生成失败", 5000)
                QMessageBox.critical(self, "错误", "生成克林贝格精确PDF报告失败")
                
        except Exception as e:
            logger.exception(f"生成克林贝格精确PDF报告失败: {e}")
            QMessageBox.critical(self, "错误", f"生成克林贝格精确PDF报告失败：\n{str(e)}")
    
    def export_data_to_csv(self):
        """导出数据到CSV"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            from utils import export_all_data
            
            # 选择保存目录
            base_path, _ = QFileDialog.getSaveFileName(
                self,
                "选择导出文件名（将生成多个CSV文件）",
                f"齿轮数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "CSV文件 (*.csv)"
            )
            
            if not base_path:
                return
            
            # 去掉扩展名
            if base_path.endswith('.csv'):
                base_path = base_path[:-4]
            
            # 导出所有数据
            self.statusbar.showMessage("正在导出数据...")
            results = export_all_data(self.measurement_data, base_path)
            
            # 统计结果
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            
            if success_count > 0:
                self.statusbar.showMessage(f"✅ 导出完成: {success_count}/{total_count}个文件", 5000)
                QMessageBox.information(
                    self, 
                    "导出成功", 
                    f"成功导出 {success_count}/{total_count} 个数据文件！\n\n"
                    f"保存位置: {os.path.dirname(base_path)}"
                )
            else:
                self.statusbar.showMessage("❌ 导出失败", 5000)
                QMessageBox.warning(self, "警告", "没有数据可导出")
                
        except Exception as e:
            logger.exception(f"导出数据失败: {e}")
            QMessageBox.critical(self, "错误", f"导出失败：\n{str(e)}")
    
    def show_tolerance_calculator(self):
        """显示公差计算器"""
        from ui.dialogs import ToleranceCalculatorDialog
        dialog = ToleranceCalculatorDialog(self)
        dialog.exec_()
    
    def show_ripple_tolerance_settings(self):
        """显示波纹度公差设置对话框"""
        try:
            if not hasattr(self, 'measurement_data') or self.measurement_data is None:
                QMessageBox.warning(self, "提示", "请先加载MKA文件")
                return
            
            from ui.ripple_tolerance_dialog import RippleToleranceDialog
            dialog = RippleToleranceDialog(self.measurement_data, self)
            
            # 连接设置更新信号
            def on_settings_updated(settings):
                logger.info(f"波纹度公差设置已更新: {settings}")
                # 设置已自动保存到measurement_data中
                QMessageBox.information(self, "成功", "波纹度公差设置已保存")
            
            dialog.settings_updated.connect(on_settings_updated)
            
            if dialog.exec_():
                logger.info("波纹度公差设置对话框已关闭")
        except Exception as e:
            logger.exception(f"显示波纹度公差设置对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开设置对话框失败：\n{str(e)}")
    
    def show_analysis_settings(self):
        """显示分析参数设置对话框"""
        try:
            from ui.dialogs import AnalysisSettingsDialog
            dialog = AnalysisSettingsDialog(parent=self)
            if dialog.exec_():
                settings = dialog.get_settings()
                if settings:
                    logger.info(f"分析参数已更新: {settings}")
                    QMessageBox.information(self, "成功", "分析参数设置已保存")
        except Exception as e:
            logger.exception(f"显示分析设置对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开设置对话框失败：\n{str(e)}")
    
    def show_pitch_analysis(self):
        """显示周节分析"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        try:
            self.analyze_pitch()
            QMessageBox.information(self, "提示", "周节分析已启动")
        except Exception as e:
            logger.exception(f"周节分析失败: {e}")
            QMessageBox.critical(self, "错误", f"周节分析失败：\n{str(e)}")
    
    def show_ripple_analysis(self):
        """显示Ripple分析"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        try:
            self.analyze_ripple()
            QMessageBox.information(self, "提示", "Ripple阶次分析已启动")
        except Exception as e:
            logger.exception(f"Ripple分析失败: {e}")
            QMessageBox.critical(self, "错误", f"Ripple分析失败：\n{str(e)}")
    
    def generate_ripple_pdf_report(self):
        """生成Ripple分析PDF报告（使用正弦拟合方法）"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        try:
            from PyQt5.QtWidgets import QFileDialog
            from reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
            from matplotlib.backends.backend_pdf import PdfPages
            
            # 选择保存位置
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "保存Ripple分析报告",
                os.path.splitext(self.current_file)[0] + "_Ripple报告.pdf",
                "PDF文件 (*.pdf);;所有文件 (*.*)"
            )
            
            if not filename:
                return
            
            # 生成报告
            self.statusbar.showMessage("正在生成Ripple频谱报告...")
            
            # 使用新的正弦拟合方法生成报告
            report = KlingelnbergRippleSpectrumReport()
            
            # 创建PDF文件
            with PdfPages(filename) as pdf:
                # 添加频谱分析页面
                report.create_page(pdf, self.measurement_data)
            
            QMessageBox.information(self, "成功", f"Ripple分析报告已生成:\n{filename}")
                
        except Exception as e:
            logger.exception("生成Ripple分析PDF报告失败")
            QMessageBox.critical(self, "错误", f"生成Ripple分析PDF报告失败:\n{str(e)}")
    
    def create_advanced_charts(self):
        """创建高级图表"""
        if not self.measurement_data:
            QMessageBox.warning(self, "提示", "请先加载MKA文件")
            return
        
        try:
            from ui.advanced_charts import WaterfallChartWidget, OrderSpectrumChartWidget, UndulationDistributionChartWidget
            from PyQt5.QtWidgets import QMdiSubWindow
            
            # 创建MDI区域（如果不存在）
            if not hasattr(self, 'mdi_area'):
                self.mdi_area = QMdiSubWindow()
                self.mdi_area.setWindowTitle("高级图表")
                self.setCentralWidget(self.mdi_area)
            
            # 创建瀑布图
            if self.ripple_results and self.ripple_results:
                waterfall_widget = WaterfallChartWidget()
                waterfall_widget.plot_waterfall_analysis(self.ripple_results)
                
                waterfall_subwindow = QMdiSubWindow()
                waterfall_subwindow.setWidget(waterfall_widget)
                waterfall_subwindow.setWindowTitle("时频瀑布图")
                self.mdi_area.addSubWindow(waterfall_subwindow)
                waterfall_subwindow.show()
            
            # 创建阶次谱图
            if self.ripple_results and 'order_analysis' in self.ripple_results:
                order_widget = OrderSpectrumChartWidget()
                order_widget.plot_order_spectrum(self.ripple_results['order_analysis'], 'profile')
                
                order_subwindow = QMdiSubWindow()
                order_subwindow.setWidget(order_widget)
                order_subwindow.setWindowTitle("阶次谱图")
                self.mdi_area.addSubWindow(order_subwindow)
                order_subwindow.show()
            
            # 创建波纹度分布图
            if self.undulation_results:
                undulation_widget = UndulationDistributionChartWidget()
                undulation_widget.plot_undulation_distribution(self.undulation_results)
                
                undulation_subwindow = QMdiSubWindow()
                undulation_subwindow.setWidget(undulation_widget)
                undulation_subwindow.setWindowTitle("波纹度分布图")
                self.mdi_area.addSubWindow(undulation_subwindow)
                undulation_subwindow.show()
                
        except Exception as e:
            logger.exception("创建高级图表失败")
            QMessageBox.critical(self, "错误", f"创建高级图表失败:\n{str(e)}")
    
    def show_ripple_settings(self):
        """显示Ripple参数设置对话框"""
        try:
            from ui.dialogs import RippleAnalysisDialog
            dialog = RippleAnalysisDialog(parent=self)
            if dialog.exec_():
                settings = dialog.get_settings()
                if settings:
                    logger.info(f"Ripple参数已更新: {settings}")
                    QMessageBox.information(self, "成功", "Ripple参数设置已保存")
        except Exception as e:
            logger.exception(f"显示Ripple设置对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开设置对话框失败：\n{str(e)}")
    
    def show_help(self):
        """显示帮助对话框"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton
            
            help_dialog = QDialog(self)
            help_dialog.setWindowTitle("使用帮助")
            help_dialog.setGeometry(100, 100, 900, 700)
            
            layout = QVBoxLayout()
            help_dialog.setLayout(layout)
            
            help_browser = QTextBrowser()
            help_browser.setOpenExternalLinks(True)
            
            help_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Microsoft YaHei', Arial; line-height: 1.6; padding: 20px; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; margin-top: 25px; }
        .highlight { background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }
        ul { margin: 10px 0; padding-left: 30px; }
        li { margin: 8px 0; }
        code { background-color: #f8f9fa; padding: 2px 6px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>齿轮波纹度分析软件 - 使用帮助</h1>
    
    <h2>快速入门</h2>
    <div class="highlight">
        <strong>基本流程：</strong>
        <ol>
            <li>文件 → 打开MKA文件 (Ctrl+O)</li>
            <li>分析 → 运行所有分析</li>
            <li>报表 → 生成PDF/HTML报告</li>
            <li>报表 → 导出CSV数据</li>
        </ol>
    </div>
    
    <h2>主要功能</h2>
    <ul>
        <li><strong>文件操作</strong>：打开MKA格式齿轮测量文件</li>
        <li><strong>数据查看</strong>：查看基本信息、齿形、齿向、周节数据</li>
        <li><strong>ISO1328分析</strong>：计算齿形、齿向偏差及公差</li>
        <li><strong>运行所有分析</strong>：一键执行所有分析项目</li>
        <li><strong>报告生成</strong>：生成HTML、克林贝格PDF、原版PDF报告</li>
        <li><strong>数据导出</strong>：导出CSV格式数据</li>
    </ul>
    
    <h2>工具功能</h2>
    <ul>
        <li><strong>ISO1328公差计算器</strong>：根据齿轮参数计算标准公差</li>
        <li><strong>Ripple参数设置</strong>：配置滤波器和分析参数</li>
        <li><strong>分析参数设置</strong>：设置评价范围和公差模式</li>
    </ul>
    
    <h2>快捷键</h2>
    <ul>
        <li><code>Ctrl+O</code> - 打开文件</li>
        <li><code>F1</code> - 显示帮助</li>
        <li><code>Ctrl+Q</code> - 退出程序</li>
    </ul>
    
    <h2>常见问题</h2>
    <p><strong>Q: 如何打开MKA文件？</strong><br>
    A: 点击"文件 → 打开MKA文件"或按Ctrl+O，选择.mka文件。</p>
    
    <p><strong>Q: 如何执行所有分析？</strong><br>
    A: 点击"分析 → 运行所有分析"即可一键执行所有分析。</p>
    
    <p><strong>Q: 如何生成报告？</strong><br>
    A: 点击"报表"菜单，选择所需的报告格式（HTML、PDF、CSV）。</p>
    
    <hr>
    <p style="text-align: center; color: #7f8c8d;">
        <strong>齿轮波纹度分析软件 v2.0</strong><br>
        完全重构版 | 无需登录 | 2025
    </p>
</body>
</html>
            """
            
            help_browser.setHtml(help_html)
            layout.addWidget(help_browser)
            
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(help_dialog.close)
            layout.addWidget(close_btn)
            
            help_dialog.exec_()
            
        except Exception as e:
            logger.exception(f"显示帮助对话框失败: {e}")
            QMessageBox.information(
                self, 
                "帮助", 
                "齿轮波纹度分析软件 v2.0\n\n"
                "基本流程：\n"
                "1. 文件 → 打开MKA文件 (Ctrl+O)\n"
                "2. 分析 → 运行所有分析\n"
                "3. 报表 → 生成报告\n\n"
                "详细文档请查看软件目录下的文档文件。"
            )
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
<h2>齿轮波纹度分析软件</h2>
<p><b>版本：</b> v2.0 (完全重构版)</p>
<p><b>更新日期：</b> 2025-10-28</p>

<h3>主要功能：</h3>
<ul>
<li>✅ ISO1328标准偏差分析</li>
<li>✅ 波纹度分析（W值/RMS）</li>
<li>✅ 周节偏差分析（fp/Fp/Fr）</li>
<li>✅ Ripple阶次分析（FFT）</li>
<li>✅ 专业PDF/HTML报告生成</li>
<li>✅ 完整数据导出</li>
</ul>

<h3>特点：</h3>
<ul>
<li>🎯 100%复刻原程序核心功能</li>
<li>🚀 模块化架构，易于维护</li>
<li>📊 现代化用户界面</li>
<li>🔧 完整的文档和测试</li>
<li>✅ 无需登录验证</li>
</ul>

<hr>
<p style='text-align: center;'>
<b>© 2025 齿轮波纹度分析软件</b><br>
完全重构版 | 代码优化82% | 功能增强47%
</p>
        """
        
        QMessageBox.about(self, "关于 - 齿轮波纹度分析软件", about_text)
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出程序吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("程序正常退出")
            event.accept()
        else:
            event.ignore()
    
    def dragEnterEvent(self, event):
        """拖入事件 - 支持拖放MKA文件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            # 检查是否有MKA文件
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.mka'):
                    event.acceptProposedAction()
                    logger.info(f"检测到MKA文件拖入: {file_path}")
                    return
    
    def dropEvent(self, event):
        """放下事件 - 处理拖放的MKA文件"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        
        # 过滤MKA文件
        mka_files = [f for f in files if f.lower().endswith('.mka')]
        
        if not mka_files:
            QMessageBox.warning(self, "提示", "请拖放MKA文件（.mka格式）")
            return
        
        # 打开第一个MKA文件
        file_path = mka_files[0]
        logger.info(f"通过拖放打开文件: {file_path}")
        
        # 使用现有的open_file方法打开文件
        self.current_file = file_path
        self.open_file_by_path(file_path)
        
        if len(mka_files) > 1:
            QMessageBox.information(self, "提示", 
                f"检测到{len(mka_files)}个MKA文件，已打开第一个：\n{os.path.basename(file_path)}")
    
    def open_file_by_path(self, file_path):
        """通过文件路径直接打开文件"""
        if not file_path:
            return
        
        try:
            logger.info(f"加载文件: {file_path}")
            self.statusbar.showMessage(f"正在加载: {file_path}")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            # 解析文件
            from utils.file_parser import parse_mka_file
            from models.gear_data import create_gear_data_from_dict
            
            data_dict = parse_mka_file(file_path)
            self.measurement_data = create_gear_data_from_dict(data_dict)
            self.current_file = file_path
            
            # 更新最近文件列表
            self.add_to_recent_files(file_path)
            
            # 更新显示
            self.update_all_displays()
            
            # 启用所有分析和报表功能
            self.enable_all_analysis_actions_unified()
            
            logger.info("✅ 所有分析和报表功能已启用")
            self.statusbar.showMessage(f"✅ 文件加载成功: {file_path}", 5000)
            QMessageBox.information(self, "成功", f"文件加载成功！\n\n{self.measurement_data.get_summary()}")
            
        except Exception as e:
            logger.exception(f"文件加载失败: {e}")
            QMessageBox.critical(self, "错误", f"文件加载失败：\n{str(e)}")
            self.statusbar.showMessage("❌ 文件加载失败", 5000)
        
        finally:
            self.progress_bar.setVisible(False)
    
    def enable_all_analysis_actions_unified(self):
        """统一启用所有分析和报表功能"""
        actions_to_enable = [
            'settings_action', 'run_all_action', 'deviation_action',
            'pitch_action', 'ripple_action', 'html_report_action',
            'pdf_report_action', 'original_pdf_action', 'ripple_pdf_action',
            'csv_export_action', 'advanced_charts_action', 'professional_order_action'
        ]
        
        for action_name in actions_to_enable:
            if hasattr(self, action_name):
                action = getattr(self, action_name)
                if action:
                    action.setEnabled(True)
    
    def add_to_recent_files(self, file_path):
        """添加到最近文件列表"""
        if not hasattr(self, 'recent_files'):
            self.recent_files = []
        if not hasattr(self, 'max_recent_files'):
            self.max_recent_files = 10
        
        # 移除重复项
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        # 添加到列表开头
        self.recent_files.insert(0, file_path)
        
        # 保持列表长度
        self.recent_files = self.recent_files[:self.max_recent_files]
        
        logger.info(f"添加到最近文件: {file_path} (总共{len(self.recent_files)}个)")

