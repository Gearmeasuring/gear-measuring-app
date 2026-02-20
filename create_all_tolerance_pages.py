import re
import os

# 读取文件内容
file_path = 'gear_analysis_refactored/ui/tolerance_dialog.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修改init_ui方法，添加所有标准的页面
new_init_ui = '''    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left Side: Tree View
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Tolerance")
        self.tree_widget.setFixedWidth(250)
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)
        main_layout.addWidget(self.tree_widget)
        
        # Populate Tree
        self.populate_tree()
        
        # Right Side: Content Area
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        # Create Pages for all standards
        # DIN 3962
        self.create_din3962_profile_page()
        self.create_din3962_lead_page()
        self.create_din3962_spacing_page()
        
        # AGMA
        self.create_agma_profile_page()
        self.create_agma_lead_page()
        self.create_agma_spacing_page()
        
        # ISO 1328:1997
        self.create_iso1328_1997_profile_page()
        self.create_iso1328_1997_lead_page()
        self.create_iso1328_1997_spacing_page()
        
        # ISO 1328:2013
        self.create_iso1328_2013_profile_page()
        self.create_iso1328_2013_lead_page()
        self.create_iso1328_2013_spacing_page()
        
        # ANSI B92.1
        self.create_ansi_b92_1_profile_page()
        self.create_ansi_b92_1_lead_page()
        self.create_ansi_b92_1_spacing_page()
        
        # DIN 5480
        self.create_din5480_profile_page()
        self.create_din5480_lead_page()
        self.create_din5480_spacing_page()
        
        # Empty placeholder for other pages
        self.create_empty_page()
        
        # Set default page
        self.content_stack.setCurrentIndex(0)  # DIN 3962 Profile''' 

# 替换init_ui方法
content = re.sub(r'def init_ui\(self\):.*?self\.content_stack\.setCurrentIndex\(0\)', new_init_ui, content, flags=re.DOTALL)

# 2. 修改on_tree_item_clicked方法，为每个标准映射到对应的页面
new_on_tree_item_clicked = '''    def on_tree_item_clicked(self, item, column):
        page_id = item.data(0, Qt.UserRole)
        if page_id is None:
            return
            
        # Check if it's a standard page
        if isinstance(page_id, str) and "_" in page_id:
            standard, type_ = page_id.split("_", 1)
            
            # Map to specific stack indices
            page_map = {
                "DIN 3962_Profile": 0,
                "DIN 3962_Lead / Line of action": 1,
                "DIN 3962_Spacing": 2,
                "AGMA_Profile": 3,
                "AGMA_Lead / Line of action": 4,
                "AGMA_Spacing": 5,
                "ISO 1328 : 1997_Profile": 6,
                "ISO 1328 : 1997_Lead / Line of action": 7,
                "ISO 1328 : 1997_Spacing": 8,
                "ISO 1328 : 2013_Profile": 9,
                "ISO 1328 : 2013_Lead / Line of action": 10,
                "ISO 1328 : 2013_Spacing": 11,
                "ANSI B92.1_Profile": 12,
                "ANSI B92.1_Lead / Line of action": 13,
                "ANSI B92.1_Spacing": 14,
                "DIN 5480_Profile": 15,
                "DIN 5480_Lead / Line of action": 16,
                "DIN 5480_Spacing": 17
            }
            
            if page_id in page_map:
                self.content_stack.setCurrentIndex(page_map[page_id])
                self.setWindowTitle(f"Tolerances acc.to {standard} {type_.split('/')[0]}")
            else:
                self.content_stack.setCurrentIndex(18)  # Empty page
                self.setWindowTitle("Tolerance Settings")
        else:
            self.content_stack.setCurrentIndex(18)  # Empty page
            self.setWindowTitle("Tolerance Settings")''' 

# 替换on_tree_item_clicked方法
content = re.sub(r'def on_tree_item_clicked\(self, item, column\):.*?self\.setWindowTitle\("Tolerance Settings"\)', new_on_tree_item_clicked, content, flags=re.DOTALL)

# 3. 创建所有标准的Profile页面方法
profile_pages = '''
    def create_din3962_profile_page(self):
        """Create DIN 3962 Profile page"""
        page = QWidget()
        
        # Background
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sub-window
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        # Icon
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to DIN Profile"))
        title_layout.addStretch()
        
        # Window Controls
        min_btn = QToolButton()
        min_btn.setText("─")
        min_btn.setFixedSize(20, 18)
        min_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                padding-bottom: 5px;
            }
            QToolButton:hover { background-color: #d0d0ff; }
        """)
        
        max_btn = QToolButton()
        max_btn.setText("□")
        max_btn.setFixedSize(20, 18)
        max_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
            }
            QToolButton:hover { background-color: #d0d0ff; }
        """)
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        
        title_layout.addWidget(min_btn)
        title_layout.addWidget(max_btn)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Quality Levels
        quality_group = QHBoxLayout()
        quality_group.addWidget(QLabel("Quality levels Q ="))
        
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setRange(1, 12)
        self.quality_spinbox.setValue(5)
        quality_group.addWidget(self.quality_spinbox)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                border: 1px solid #808080;
                padding: 2px 8px;
                font-size: 8pt;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """)
        quality_group.addWidget(set_btn)
        quality_group.addStretch()
        
        main_layout.addLayout(quality_group)
        
        # Tolerance Table
        table_group = QHBoxLayout()
        
        # Left Table (left side)
        left_table_widget = QWidget()
        left_table_layout = QVBoxLayout(left_table_widget)
        left_table_layout.setSpacing(5)
        
        # Header
        left_header = QHBoxLayout()
        left_header.addWidget(QLabel("left"))
        left_header.addStretch()
        left_table_layout.addLayout(left_header)
        
        # Output options
        output_group = QHBoxLayout()
        output_group.addWidget(QLabel("Output"))
        output_group.addStretch()
        left_table_layout.addLayout(output_group)
        
        # Tolerance items with checkboxes
        tolerance_items = [
            ("Angular error", "IHA"),
            ("Variance Ang.err.", "Var"),
            ("Total error", "Fa"),
            ("Form error", "ffa"),
            ("Crowning", "Ca"),
            ("Tip-relief", "fKo"),
            ("Root-relief", "fRu"),
            ("Profile twist", "PV")
        ]
        
        for label, key in tolerance_items:
            tolerance_layout = QHBoxLayout()
            check_box = QCheckBox()
            if key in ["IHA", "Var", "Fa", "ffa", "PV"]:  # Check some by default
                check_box.setChecked(True)
            tolerance_layout.addWidget(check_box)
            tolerance_layout.addWidget(QLabel(label))
            
            # DIN 3962 specific values
            if key == "IHA":
                tolerance_layout.addWidget(QLabel("0.0"))  # Norm.val
                tolerance_layout.addWidget(QLabel("11.0"))  # Lim.upp
                tolerance_layout.addWidget(QLabel("-11.0"))  # Lim.low
                tolerance_layout.addWidget(QLabel("5"))  # Quality
            elif key == "Var":
                tolerance_layout.addWidget(QLabel("0.0"))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel(""))
            elif key == "Fa":
                tolerance_layout.addWidget(QLabel("20.0"))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel("5"))
            elif key == "ffa":
                tolerance_layout.addWidget(QLabel("16.0"))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel("5"))
            else:
                for _ in range(4):
                    tolerance_layout.addWidget(QLabel("0.0"))
            
            left_table_layout.addLayout(tolerance_layout)
        
        table_group.addWidget(left_table_widget)
        
        # Right Table (right side)
        right_table_widget = QWidget()
        right_table_layout = QVBoxLayout(right_table_widget)
        right_table_layout.setSpacing(5)
        
        # Header
        right_header = QHBoxLayout()
        right_header.addWidget(QLabel("right"))
        right_header.addStretch()
        right_table_layout.addLayout(right_header)
        
        # Tolerance items with same values as left but no checkboxes
        for label, key in tolerance_items:
            tolerance_layout = QHBoxLayout()
            tolerance_layout.addWidget(QLabel(""))  # Empty space for checkbox
            tolerance_layout.addWidget(QLabel(""))  # Empty space for label
            
            # DIN 3962 specific values
            if key == "IHA":
                tolerance_layout.addWidget(QLabel("0.0"))  # Norm.val
                tolerance_layout.addWidget(QLabel("11.0"))  # Lim.upp
                tolerance_layout.addWidget(QLabel("-11.0"))  # Lim.low
                tolerance_layout.addWidget(QLabel("5"))  # Quality
            elif key == "Var":
                tolerance_layout.addWidget(QLabel("0.0"))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel(""))
            elif key == "Fa":
                tolerance_layout.addWidget(QLabel("20.0"))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel("5"))
            elif key == "ffa":
                tolerance_layout.addWidget(QLabel("16.0"))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel(""))
                tolerance_layout.addWidget(QLabel("5"))
            else:
                for _ in range(4):
                    tolerance_layout.addWidget(QLabel("0.0"))
            
            right_table_layout.addLayout(tolerance_layout)
        
        table_group.addWidget(right_table_widget)
        
        main_layout.addLayout(table_group)
        
        # Footer
        footer = QHBoxLayout()
        footer.addWidget(QLabel("Tolerances in um"))
        footer.addStretch()
        main_layout.addLayout(footer)
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)

    def create_agma_profile_page(self):
        """Create AGMA Profile page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to AGMA Profile"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # AGMA specific content
        main_layout.addWidget(QLabel("AGMA Profile Tolerance Settings"))
        main_layout.addWidget(QLabel("AGMA Standard - Gear Quality Levels and Tolerances"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)

    def create_iso1328_1997_profile_page(self):
        """Create ISO 1328:1997 Profile page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to ISO 1328:1997 Profile"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(QLabel("ISO 1328:1997 Profile Tolerance Settings"))
        main_layout.addWidget(QLabel("ISO 1328:1997 Standard - Profile Deviations"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)

    def create_ansi_b92_1_profile_page(self):
        """Create ANSI B92.1 Profile page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to ANSI B92.1 Profile"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(QLabel("ANSI B92.1 Profile Tolerance Settings"))
        main_layout.addWidget(QLabel("ANSI B92.1 Standard - Gear Tooth Profile"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)

    def create_din5480_profile_page(self):
        """Create DIN 5480 Profile page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to DIN 5480 Profile"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(QLabel("DIN 5480 Profile Tolerance Settings"))
        main_layout.addWidget(QLabel("DIN 5480 Standard - Spur and Helical Gears"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)'''

# 添加Profile页面方法
content += profile_pages

# 3. 创建所有标准的Lead页面方法
lead_pages = '''
    def create_din3962_lead_page(self):
        """Create DIN 3962 Lead page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to DIN 3962 Lead"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(QLabel("DIN 3962 Lead Tolerance Settings"))
        main_layout.addWidget(QLabel("Lead / Line of action deviations for DIN 3962"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)

    def create_agma_lead_page(self):
        """Create AGMA Lead page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to AGMA Lead"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(QLabel("AGMA Lead Tolerance Settings"))
        main_layout.addWidget(QLabel("AGMA Standard - Lead Deviations"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)

    def create_iso1328_1997_lead_page(self):
        """Create ISO 1328:1997 Lead page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to ISO 1328:1997 Lead"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(QLabel("ISO 1328:1997 Lead Tolerance Settings"))
        main_layout.addWidget(QLabel("ISO 1328:1997 Standard - Lead Deviations"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)

    def create_ansi_b92_1_lead_page(self):
        """Create ANSI B92.1 Lead page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to ANSI B92.1 Lead"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(QLabel("ANSI B92.1 Lead Tolerance Settings"))
        main_layout.addWidget(QLabel("ANSI B92.1 Standard - Lead Deviations"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)

    def create_din5480_lead_page(self):
        """Create DIN 5480 Lead page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to DIN 5480 Lead"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(QLabel("DIN 5480 Lead Tolerance Settings"))
        main_layout.addWidget(QLabel("DIN 5480 Standard - Lead Deviations"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)'''

# 添加Lead页面方法
content += lead_pages

# 4. 创建所有标准的Spacing页面方法
spacing_pages = '''
    def create_din3962_spacing_page(self):
        """Create DIN 3962 Spacing page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to DIN 3962 Spacing"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1px solid #808080;
                border-radius: 2px;
                font-size: 8pt;
                color: #800000;
            }
            QToolButton:hover { background-color: #ffd0d0; }
        """)
        title_layout.addWidget(close_btn)
        
        window_layout.addWidget(title_bar)
        
        # Main Content Area
        main_content = QWidget()
        main_content.setStyleSheet("background-color: #f0f0f0;")
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        main_layout.addWidget(QLabel("DIN 3962 Spacing Tolerance Settings"))
        main_layout.addWidget(QLabel("DIN 3962 Standard - Spacing Deviations"))
        main_layout.addStretch()
        
        # Navigation buttons
        nav_buttons = QHBoxLayout()
        nav_buttons.addStretch()
        
        nav_btns = ["Return", "Continue", "OK", "Cancel", "Apply"]
        for btn_text in nav_btns:
            btn = QPushButton(btn_text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #E0E0E0;
                    border: 1px solid #808080;
                    padding: 3px 10px;
                    font-size: 8pt;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            nav_buttons.addWidget(btn)
        
        main_layout.addLayout(nav_buttons)
        
        window_layout.addWidget(main_content)
        
        page_layout.addWidget(sub_window, alignment=Qt.AlignCenter)
        
        self.content_stack.addWidget(page)

    def create_agma_spacing_page(self):
        """Create AGMA Spacing page"""
        page = QWidget()
        page.setStyleSheet("background-color: #A0A0A0;")
        
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        
        sub_window = QWidget()
        sub_window.setObjectName("sub_window")
        sub_window.setFixedWidth(800)
        sub_window.setStyleSheet("""
            QWidget#sub_window {
                background-color: #f0f0f0;
                border: 1px solid #404040;
                border-radius: 2px;
            }
        """)
        
        window_layout = QVBoxLayout(sub_window)
        window_layout.setContentsMargins(2, 2, 2, 2)
        window_layout.setSpacing(0)
        
        # Title Bar
        title_bar = QFrame()
        title_bar.setFixedHeight(26)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B9D1EA, stop:1 #87B3E0);
                border-bottom: 1px solid #a0a0a0;
            }
            QLabel {
                color: black;
                font-weight: bold;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 9pt;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 0, 5, 0)
        title_layout.setSpacing(5)
        
        icon_lbl = QLabel("🔹")
        icon_lbl.setStyleSheet("color: #000080; font-size: 10pt;")
        title_layout.addWidget(icon_lbl)
        
        title_layout.addWidget(QLabel("Tolerances acc.to AGMA Spacing"))
        title_layout.addStretch()
        
        close_btn = QToolButton()
        close_btn.setText("×")
        close_btn.setFixedSize(20, 18)
        close_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: 1