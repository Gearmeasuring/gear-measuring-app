import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
                             QStackedWidget, QWidget, QLabel, QLineEdit, QPushButton, 
                             QCheckBox, QGroupBox, QGridLayout, QComboBox, QScrollArea,
                             QFrame, QSpinBox, QMessageBox, QHeaderView, QToolButton)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon, QPixmap

# Import logger
try:
    from gear_analysis_refactored.config.logging_config import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

class ToleranceSettingsDialog(QDialog):
    """Tolerance Settings Dialog matching the provided design"""
    
    tolerances_updated = pyqtSignal(dict)
    
    def __init__(self, gear_data=None, parent=None):
        super().__init__(parent)
        self.gear_data = gear_data or {}
        self.current_page_id = None  # Track current page ID
        self.quality_spins = {}  # Dictionary to store quality spin boxes
        self.saved_tolerance_settings = {}  # Store saved tolerance settings
        self.setWindowTitle("Tolerance Settings")
        self.resize(1000, 700)
        
        self.init_ui()
        self.load_initial_data()
        
    def init_ui(self):
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
        
        
        # Create Pages
        # Order matches the page_mapping in on_tree_item_clicked
        self.create_din3962_profile_page()
        self.create_din3962_lead_page()
        self.create_din3962_spacing_page()
        self.create_agma_profile_page()
        self.create_agma_lead_page()
        self.create_agma_spacing_page()
        self.create_iso1328_1997_profile_page()
        self.create_iso1328_1997_lead_page()
        self.create_iso1328_1997_spacing_page()
        self.create_iso1328_2013_profile_page()
        self.create_iso1328_2013_lead_page()
        self.create_iso1328_2013_spacing_page()
        self.create_ansi_b921_profile_page()
        self.create_ansi_b921_lead_page()
        self.create_ansi_b921_spacing_page()
        self.create_din5480_profile_page()
        self.create_din5480_lead_page()
        self.create_din5480_spacing_page()
        self.create_empty_page() # Empty page for extra items under DIN 5480
        self.content_stack.setCurrentIndex(0)
        
    def populate_tree(self):
        self.tree_widget.clear()
        
        # Root: Tolerance
        root_tolerance = QTreeWidgetItem(self.tree_widget)
        root_tolerance.setText(0, "Tolerance")
        root_tolerance.setExpanded(True)
        
        standards = [
            ("DIN 3962", ["Profile", "Lead / Line of action", "Spacing"]),
            ("AGMA", ["Profile", "Lead / Line of action", "Spacing"]),
            ("ISO 1328 : 1997", ["Profile", "Lead / Line of action", "Spacing"]),
            ("ISO 1328 : 2013", ["Profile", "Lead / Line of action", "Spacing"]),
            ("ANSI B92.1", ["Profile", "Lead / Line of action", "Spacing"]),
            ("DIN 5480", ["Profile", "Lead / Line of action", "Spacing", "Tolerance fields", "Measurement over balls", "Root diameter / Tip diameter"])
        ]
        
        for std_name, sub_items in standards:
            item = QTreeWidgetItem(root_tolerance)
            item.setText(0, std_name)
            item.setExpanded(False)
            
            if std_name == "ISO 1328 : 2013":
                item.setExpanded(True)
            
            for sub in sub_items:
                sub_item = QTreeWidgetItem(item)
                sub_item.setText(0, sub)
                
                # Highlight "Profile" under "DIN 3962" with blue background
                if std_name == "DIN 3962" and sub == "Profile":
                    sub_item.setBackground(0, QBrush(QColor(100, 150, 255)))  # Light blue background
                    sub_item.setForeground(0, QBrush(QColor(255, 255, 255)))  # White text for contrast
                
                # Store page index reference
                # We will map these to specific pages
                page_id = f"{std_name}_{sub}"
                sub_item.setData(0, Qt.UserRole, page_id)

        # Other Roots
        for root_name in ["Output", "Evaluation", "Options"]:
            item = QTreeWidgetItem(self.tree_widget)
            item.setText(0, root_name)
            item.setData(0, Qt.UserRole, f"ROOT_{root_name}")
                    
    def on_tree_item_clicked(self, item, column):
        page_id = item.data(0, Qt.UserRole)
        if page_id is None:
            return
        self.current_page_id = page_id  # Track current page
        
        self.current_page_id = page_id  # Track current page
            
        # Map IDs to stack indices
        page_mapping = {
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
            "DIN 5480_Spacing": 17,
            "default": 18
        }
        # Get page index from mapping
        if page_id in page_mapping:
            index = page_mapping[page_id]
            self.content_stack.setCurrentIndex(index)
            
            # Set window title based on page_id
            if "Profile" in page_id:
                standard = page_id.split("_", 1)[0]
                self.setWindowTitle(f"Tolerances acc.to {standard} Profile")
            elif "Lead" in page_id:
                standard = page_id.split("_", 1)[0]
                self.setWindowTitle(f"Tolerances acc.to {standard} Lead")
            elif "Spacing" in page_id:
                standard = page_id.split("_", 1)[0]
                self.setWindowTitle(f"Tolerances acc.to {standard} Spacing")
            else:
                self.setWindowTitle("Tolerance Settings")
        else:
            self.content_stack.setCurrentIndex(18)  # Empty page
            self.setWindowTitle("Tolerance Settings")
            
    def create_iso1328_2013_profile_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景
        page.setStyleSheet("background-color: white;") 
        
        # Main layout for the page
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(15, 15, 15, 15)
        page_layout.setSpacing(10)
        
        # Content Area (直接添加到page，不再使用sub_window)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.profile_quality_spin = QSpinBox()
        self.quality_spins["ISO 1328 : 2013_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 5480_Profile"] = self.profile_quality_spin
        self.quality_spins["ANSI B92.1_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 2013_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 1997_Profile"] = self.profile_quality_spin
        self.quality_spins["AGMA_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 3962_Profile"] = self.profile_quality_spin
        self.profile_quality_spin.setRange(1, 12)
        self.profile_quality_spin.setValue(5)
        self.profile_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.profile_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(self.profile_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Tooth Profile Icon
        icon_label = QLabel()
        # Use relative path for portability
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "resources", "profile_tolerance_icon.png")
        
        try:
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Increased size to 100x100 as requested
                icon_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                # Fallback if image not found
                icon_label.setText("Profile")
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedSize(100, 100)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setText("Icon")
            icon_label.setFixedSize(100, 100)
            
        icon_label.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 5px;")
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Main Table Frame
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.Box)
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        # Nom. val is a Label
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.btn_lim_upp_l = QPushButton("Lim. upp.")
        self.btn_lim_low_l = QPushButton("Lim. low.")
        self.btn_qual_l = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_l, self.btn_lim_low_l, self.btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_l.setChecked(True)
        self.btn_lim_low_l.setChecked(True)
        self.btn_qual_l.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_lim_low_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_qual_l.clicked.connect(lambda: self.toggle_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.btn_qual_l, 1, 6)
        
        # Right Side Headers
        # Nom. val is a Label
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.btn_lim_upp_r = QPushButton("Lim. upp.")
        self.btn_lim_low_r = QPushButton("Lim. low.")
        self.btn_qual_r = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_r, self.btn_lim_low_r, self.btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_r.setChecked(True)
        self.btn_lim_low_r.setChecked(True)
        self.btn_qual_r.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_lim_low_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_qual_r.clicked.connect(lambda: self.toggle_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.btn_qual_r, 1, 11)
        
        # Data Rows
        self.profile_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_Editable: True=QLineEdit, False=QLabel)
        # True = Visible, False = Hidden
        rows = [
            ("Angular error", "fHa", True, 
             [True, True, True, True], [True, True, True, True], False), # All visible, Nom not editable
            ("Variance Ang.err.", "Var", True, 
             [False, True, False, False], [False, True, False, False], False), # Nom, Low, Qual hidden
            ("Total error", "Fa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Form error", "ffa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Crowning", "Ca", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Tip-relief", "fKo", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Root-relief", "fFu", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Profile twist", "PV", True, 
             [True, True, True, False], [True, True, True, False], True)  # Qual hidden, Nom EDITABLE
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_editable) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.profile_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_l = QLineEdit("0.0")
                nom_l.setAlignment(Qt.AlignRight)
            else:
                nom_l = QLabel("0.0")
                nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_l = QLineEdit("0.0")
            low_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            low_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            
            if left_vis[0]: grid_layout.addWidget(nom_l, r, 3)
            else: nom_l.setVisible(False)
            
            if left_vis[1]: grid_layout.addWidget(upp_l, r, 4)
            else: upp_l.setVisible(False)
            
            if left_vis[2]: grid_layout.addWidget(low_l, r, 5)
            else: low_l.setVisible(False)
            
            if left_vis[3]: grid_layout.addWidget(qual_l, r, 6)
            else: qual_l.setVisible(False)
            
            # Right Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_r = QLineEdit("0.0")
                nom_r.setAlignment(Qt.AlignRight)
            else:
                nom_r = QLabel("0.0")
                nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_r = QLineEdit("0.0")
            low_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_r.setAlignment(Qt.AlignRight)
            low_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            if right_vis[0]: grid_layout.addWidget(nom_r, r, 8)
            else: nom_r.setVisible(False)
            
            if right_vis[1]: grid_layout.addWidget(upp_r, r, 9)
            else: upp_r.setVisible(False)
            
            if right_vis[2]: grid_layout.addWidget(low_r, r, 10)
            else: low_r.setVisible(False)
            
            if right_vis[3]: grid_layout.addWidget(qual_r, r, 11)
            else: qual_r.setVisible(False)
            
            # Store references
            self.profile_inputs[code] = {
                "left": {"nom": nom_l, "upp": upp_l, "low": low_l, "qual": qual_l},
                "right": {"nom": nom_r, "upp": upp_r, "low": low_r, "qual": qual_r}
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right) - under left section
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "profile"))
        
        # Left Copy Button (Right to Left) - under right section
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "profile"))
        
        # Add buttons to grid
        # Centered under the respective sections
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Under Left section? No, usually arrows point direction.
        # Ref image shows arrows at bottom.
        # Left arrow is under Right section pointing Left? Or under Left section?
        # Image 1 shows:
        # Left side has "Ba ->" (Left to Right?) No, wait.
        # Image 1 shows:
        # Under Left section: Arrow pointing RIGHT (Ba ->)
        # Under Right section: Arrow pointing LEFT (<- Ba)
        # Wait, usually "Ba ->" means Copy FROM Ba TO other?
        # Let's assume:
        # Button under Left section: Copy Left -> Right
        # Button under Right section: Copy Right -> Left
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Left side, arrow pointing right
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter) # Right side, arrow pointing left
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Store profile_inputs in the page widget so we can access it later
        if hasattr(self, 'profile_inputs'):
            page.profile_inputs = self.profile_inputs
        
        self.content_stack.addWidget(page)

    def create_iso1328_2013_lead_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.lead_quality_spin = QSpinBox()
        self.lead_quality_spin.setRange(1, 12)
        self.lead_quality_spin.setValue(5)
        self.lead_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.lead_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(self.lead_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }""")
        set_btn.clicked.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Add Lead Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "lead_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            # Scale to reasonable height if needed, e.g. 60px
            if pixmap.height() > 60:
                pixmap = pixmap.scaledToHeight(60, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Table Frame
        table_frame = QFrame()
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.lead_btn_lim_upp_l = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_l = QPushButton("Lim. low.")
        self.lead_btn_qual_l = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_l, self.lead_btn_lim_low_l, self.lead_btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_l.setChecked(True)
        self.lead_btn_lim_low_l.setChecked(True)
        self.lead_btn_qual_l.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_lim_low_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_qual_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.lead_btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.lead_btn_qual_l, 1, 6)
        
        # Right Side Headers
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.lead_btn_lim_upp_r = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_r = QPushButton("Lim. low.")
        self.lead_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_r, self.lead_btn_lim_low_r, self.lead_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_r.setChecked(True)
        self.lead_btn_lim_low_r.setChecked(True)
        self.lead_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_lim_low_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_qual_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.lead_btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.lead_btn_qual_r, 1, 11)
        
        # Data Rows
        self.lead_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_is_label: True=QLabel (no border), False=QLineEdit)
        rows = [
            ("Angular error", "fHb", True, [True, True, True, True], [True, True, True, True], True),
            ("Variance Ang.err.", "Var", True, [False, True, False, False], [False, True, False, False], False),
            ("Total error", "Fb", True, [False, True, False, True], [False, True, False, True], False),
            ("Form error", "ffb", True, [False, True, False, True], [False, True, False, True], False),
            ("Crowning", "Cb", True, [True, True, True, False], [True, True, True, False], True),
            ("Top-relief (lead)", "fo", True, [True, True, True, False], [True, True, True, False], True),
            ("Bottom-relief (lead)", "fu", True, [True, True, True, False], [True, True, True, False], True),
            ("Bending", "FV", True, [True, True, True, False], [True, True, True, False], False)
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_is_label) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.lead_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            left_widgets = {}
            
            if left_vis[0]: # Nom
                if nom_is_label:
                    nom_l = QLabel("0.0")
                    nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_l = QLineEdit("0.0")
                    nom_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_l, r, 3)
                left_widgets["nom"] = nom_l
            
            if left_vis[1]: # Upp
                upp_l = QLineEdit("0.0")
                upp_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_l, r, 4)
                left_widgets["upp"] = upp_l
                
            if left_vis[2]: # Low
                low_l = QLineEdit("0.0")
                low_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_l, r, 5)
                left_widgets["low"] = low_l
                
            if left_vis[3]: # Qual
                qual_l = QLineEdit("5")
                qual_l.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_l, r, 6)
                left_widgets["qual"] = qual_l
            
            # Right Side inputs
            right_widgets = {}
            
            if right_vis[0]: # Nom
                if nom_is_label:
                    nom_r = QLabel("0.0")
                    nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_r = QLineEdit("0.0")
                    nom_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_r, r, 8)
                right_widgets["nom"] = nom_r
                
            if right_vis[1]: # Upp
                upp_r = QLineEdit("0.0")
                upp_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_r, r, 9)
                right_widgets["upp"] = upp_r
                
            if right_vis[2]: # Low
                low_r = QLineEdit("0.0")
                low_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_r, r, 10)
                right_widgets["low"] = low_r
                
            if right_vis[3]: # Qual
                qual_r = QLineEdit("5")
                qual_r.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_r, r, 11)
                right_widgets["qual"] = qual_r
            
            # Store references
            self.lead_inputs[code] = {
                "left": left_widgets,
                "right": right_widgets
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right)
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "lead"))
        
        # Left Copy Button (Right to Left)
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "lead"))
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter)
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter)
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store lead_inputs in the page widget so we can access it later
        if hasattr(self, 'lead_inputs'):
            page.lead_inputs = self.lead_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize field states
        self.toggle_lead_header_mode("left", "limits")
        self.toggle_lead_header_mode("right", "limits")

    def create_iso1328_2013_spacing_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QGroupBox {
                border: 1px solid #808080;
                margin-top: 10px;
                font-weight: normal;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.spacing_quality_spin = QSpinBox()
        self.spacing_quality_spin.setRange(1, 12)
        self.spacing_quality_spin.setValue(5)
        self.spacing_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.spacing_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(self.spacing_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Spacing Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "spacing_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if pixmap.height() > 80:
                pixmap = pixmap.scaledToHeight(80, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # Placeholder if no icon
            icon_label.setText("Spacing")
            icon_label.setStyleSheet("border: 1px solid #ccc; background: white; padding: 5px;")
            icon_label.setFixedSize(80, 80)
            icon_label.setAlignment(Qt.AlignCenter)
            
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Spacing Group
        spacing_group = QGroupBox("Spacing")
        spacing_layout = QGridLayout(spacing_group)
        spacing_layout.setSpacing(5)
        spacing_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        spacing_layout.addWidget(QLabel("left"), 0, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(QLabel("right"), 0, 5, 1, 2, Qt.AlignCenter)
        
        # Add vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #808080;")
        spacing_layout.addWidget(sep, 0, 4, 7, 1) # Span down to cover rows
        
        # Buttons/Headers
        self.spacing_btn_lim_l = QPushButton("Lim. upp.")
        self.spacing_btn_qual_l = QPushButton("Quality")
        self.spacing_btn_lim_r = QPushButton("Lim. upp.")
        self.spacing_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.spacing_btn_lim_l, self.spacing_btn_qual_l, self.spacing_btn_lim_r, self.spacing_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.spacing_btn_lim_l.setChecked(True)
        self.spacing_btn_qual_l.setChecked(False)
        self.spacing_btn_lim_r.setChecked(True)
        self.spacing_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.spacing_btn_lim_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "limits"))
        self.spacing_btn_qual_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "quality"))
        self.spacing_btn_lim_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "limits"))
        self.spacing_btn_qual_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "quality"))
        
        spacing_layout.addWidget(self.spacing_btn_lim_l, 1, 2)
        spacing_layout.addWidget(self.spacing_btn_qual_l, 1, 3)
        spacing_layout.addWidget(self.spacing_btn_lim_r, 1, 5)
        spacing_layout.addWidget(self.spacing_btn_qual_r, 1, 6)
        
        self.spacing_inputs = {}
        rows = [
            ("Individual error", "fp"),
            ("Pitch jump", "fu"),
            ("Total error", "Fp"),
            ("Pitch-span var.", "Fpz/8")
        ]
        
        for r, (label, code) in enumerate(rows):
            row_idx = r + 2
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            spacing_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            upp_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            upp_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            spacing_layout.addWidget(upp_l, row_idx, 2)
            spacing_layout.addWidget(qual_l, row_idx, 3)
            spacing_layout.addWidget(upp_r, row_idx, 5)
            spacing_layout.addWidget(qual_r, row_idx, 6)
            
            self.spacing_inputs[code] = {
                "left": {"upp": upp_l, "qual": qual_l},
                "right": {"upp": upp_r, "qual": qual_r}
            }
            
        # Copy Buttons
        copy_row = len(rows) + 2
        
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover { background-color: #e0e0ff; }
            QPushButton:pressed { border: 2px inset #a0a0a0; background-color: #d0d0d0; }
        """
        
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(60, 30)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "spacing"))
        
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(60, 30)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "spacing"))
        
        spacing_layout.addWidget(copy_r_btn, copy_row, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(copy_l_btn, copy_row, 5, 1, 2, Qt.AlignCenter)
            
        layout.addWidget(spacing_group)
        
        # Run-out Group
        runout_group = QGroupBox("Run-out / Tooth thickness")
        runout_layout = QGridLayout(runout_group)
        runout_layout.setSpacing(5)
        runout_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        self.runout_btn_lim = QPushButton("Lim. upp.")
        self.runout_btn_qual = QPushButton("Quality")
        
        for btn in [self.runout_btn_lim, self.runout_btn_qual]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.runout_btn_lim.setChecked(True)
        self.runout_btn_qual.setChecked(False)
        
        # Connect signals
        self.runout_btn_lim.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "limits"))
        self.runout_btn_qual.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "quality"))
        
        runout_layout.addWidget(self.runout_btn_lim, 0, 2)
        runout_layout.addWidget(self.runout_btn_qual, 0, 3)
        
        rows_runout = [
            ("Run-out", "Fr"),
            ("Variation of tooth thickness", "Rs")
        ]
        
        for r, (label, code) in enumerate(rows_runout):
            row_idx = r + 1
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            runout_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp = QLineEdit("0.0")
            qual = QLineEdit("5")
            
            upp.setAlignment(Qt.AlignRight)
            qual.setAlignment(Qt.AlignCenter)
            
            runout_layout.addWidget(upp, row_idx, 2)
            runout_layout.addWidget(qual, row_idx, 3)
            
            self.spacing_inputs[code] = {"upp": upp, "qual": qual}
            
        layout.addWidget(runout_group)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
            
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store spacing_inputs in the page widget so we can access it later
        if hasattr(self, 'spacing_inputs'):
            page.spacing_inputs = self.spacing_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize
        self.toggle_spacing_header_mode("left", "limits")
        self.toggle_spacing_header_mode("right", "limits")
        self.toggle_spacing_header_mode("runout", "limits")

    def create_din3962_profile_page(self):
        page = QWidget()
        
        # Using a gray color to match the MDI style
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        page.setStyleSheet("background-color: white;")

        

        # Main layout for the page

        page_layout = QVBoxLayout(page)

        page_layout.setContentsMargins(15, 15, 15, 15)

        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.profile_quality_spin = QSpinBox()
        self.quality_spins["DIN 3962_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 5480_Profile"] = self.profile_quality_spin
        self.quality_spins["ANSI B92.1_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 2013_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 1997_Profile"] = self.profile_quality_spin
        self.quality_spins["AGMA_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 3962_Profile"] = self.profile_quality_spin
        self.profile_quality_spin.setRange(1, 12)
        self.profile_quality_spin.setValue(5)
        self.profile_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.profile_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(self.profile_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Tooth Profile Icon
        icon_label = QLabel()
        # Use relative path for portability
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "resources", "profile_tolerance_icon.png")
        
        try:
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Increased size to 100x100 as requested
                icon_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                # Fallback if image not found
                icon_label.setText("Profile")
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedSize(100, 100)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setText("Icon")
            icon_label.setFixedSize(100, 100)
            
        icon_label.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 5px;")
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Main Table Frame
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.Box)
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        # Nom. val is a Label
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.btn_lim_upp_l = QPushButton("Lim. upp.")
        self.btn_lim_low_l = QPushButton("Lim. low.")
        self.btn_qual_l = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_l, self.btn_lim_low_l, self.btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_l.setChecked(True)
        self.btn_lim_low_l.setChecked(True)
        self.btn_qual_l.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_lim_low_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_qual_l.clicked.connect(lambda: self.toggle_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.btn_qual_l, 1, 6)
        
        # Right Side Headers
        # Nom. val is a Label
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.btn_lim_upp_r = QPushButton("Lim. upp.")
        self.btn_lim_low_r = QPushButton("Lim. low.")
        self.btn_qual_r = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_r, self.btn_lim_low_r, self.btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_r.setChecked(True)
        self.btn_lim_low_r.setChecked(True)
        self.btn_qual_r.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_lim_low_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_qual_r.clicked.connect(lambda: self.toggle_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.btn_qual_r, 1, 11)
        
        # Data Rows
        self.profile_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_Editable: True=QLineEdit, False=QLabel)
        # True = Visible, False = Hidden
        rows = [
            ("Angular error", "fHa", True, 
             [True, True, True, True], [True, True, True, True], False), # All visible, Nom not editable
            ("Variance Ang.err.", "Var", True, 
             [False, True, False, False], [False, True, False, False], False), # Nom, Low, Qual hidden
            ("Total error", "Fa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Form error", "ffa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Crowning", "Ca", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Tip-relief", "fKo", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Root-relief", "fFu", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Profile twist", "PV", True, 
             [True, True, True, False], [True, True, True, False], True)  # Qual hidden, Nom EDITABLE
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_editable) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.profile_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_l = QLineEdit("0.0")
                nom_l.setAlignment(Qt.AlignRight)
            else:
                nom_l = QLabel("0.0")
                nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_l = QLineEdit("0.0")
            low_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            low_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            
            if left_vis[0]: grid_layout.addWidget(nom_l, r, 3)
            else: nom_l.setVisible(False)
            
            if left_vis[1]: grid_layout.addWidget(upp_l, r, 4)
            else: upp_l.setVisible(False)
            
            if left_vis[2]: grid_layout.addWidget(low_l, r, 5)
            else: low_l.setVisible(False)
            
            if left_vis[3]: grid_layout.addWidget(qual_l, r, 6)
            else: qual_l.setVisible(False)
            
            # Right Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_r = QLineEdit("0.0")
                nom_r.setAlignment(Qt.AlignRight)
            else:
                nom_r = QLabel("0.0")
                nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_r = QLineEdit("0.0")
            low_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_r.setAlignment(Qt.AlignRight)
            low_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            if right_vis[0]: grid_layout.addWidget(nom_r, r, 8)
            else: nom_r.setVisible(False)
            
            if right_vis[1]: grid_layout.addWidget(upp_r, r, 9)
            else: upp_r.setVisible(False)
            
            if right_vis[2]: grid_layout.addWidget(low_r, r, 10)
            else: low_r.setVisible(False)
            
            if right_vis[3]: grid_layout.addWidget(qual_r, r, 11)
            else: qual_r.setVisible(False)
            
            # Store references
            self.profile_inputs[code] = {
                "left": {"nom": nom_l, "upp": upp_l, "low": low_l, "qual": qual_l},
                "right": {"nom": nom_r, "upp": upp_r, "low": low_r, "qual": qual_r}
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right) - under left section
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "profile"))
        
        # Left Copy Button (Right to Left) - under right section
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "profile"))
        
        # Add buttons to grid
        # Centered under the respective sections
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Under Left section? No, usually arrows point direction.
        # Ref image shows arrows at bottom.
        # Left arrow is under Right section pointing Left? Or under Left section?
        # Image 1 shows:
        # Left side has "Ba ->" (Left to Right?) No, wait.
        # Image 1 shows:
        # Under Left section: Arrow pointing RIGHT (Ba ->)
        # Under Right section: Arrow pointing LEFT (<- Ba)
        # Wait, usually "Ba ->" means Copy FROM Ba TO other?
        # Let's assume:
        # Button under Left section: Copy Left -> Right
        # Button under Right section: Copy Right -> Left
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Left side, arrow pointing right
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter) # Right side, arrow pointing left
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Store profile_inputs in the page widget so we can access it later
        if hasattr(self, 'profile_inputs'):
            page.profile_inputs = self.profile_inputs
        
        self.content_stack.addWidget(page)

    def create_din3962_lead_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.lead_quality_spin = QSpinBox()
        self.lead_quality_spin.setRange(1, 12)
        self.lead_quality_spin.setValue(5)
        self.lead_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.lead_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(self.lead_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }""")
        set_btn.clicked.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Add Lead Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "lead_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            # Scale to reasonable height if needed, e.g. 60px
            if pixmap.height() > 60:
                pixmap = pixmap.scaledToHeight(60, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Table Frame
        table_frame = QFrame()
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.lead_btn_lim_upp_l = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_l = QPushButton("Lim. low.")
        self.lead_btn_qual_l = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_l, self.lead_btn_lim_low_l, self.lead_btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_l.setChecked(True)
        self.lead_btn_lim_low_l.setChecked(True)
        self.lead_btn_qual_l.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_lim_low_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_qual_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.lead_btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.lead_btn_qual_l, 1, 6)
        
        # Right Side Headers
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.lead_btn_lim_upp_r = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_r = QPushButton("Lim. low.")
        self.lead_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_r, self.lead_btn_lim_low_r, self.lead_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_r.setChecked(True)
        self.lead_btn_lim_low_r.setChecked(True)
        self.lead_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_lim_low_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_qual_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.lead_btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.lead_btn_qual_r, 1, 11)
        
        # Data Rows
        self.lead_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_is_label: True=QLabel (no border), False=QLineEdit)
        rows = [
            ("Angular error", "fHb", True, [True, True, True, True], [True, True, True, True], True),
            ("Variance Ang.err.", "Var", True, [False, True, False, False], [False, True, False, False], False),
            ("Total error", "Fb", True, [False, True, False, True], [False, True, False, True], False),
            ("Form error", "ffb", True, [False, True, False, True], [False, True, False, True], False),
            ("Crowning", "Cb", True, [True, True, True, False], [True, True, True, False], True),
            ("Top-relief (lead)", "fo", True, [True, True, True, False], [True, True, True, False], True),
            ("Bottom-relief (lead)", "fu", True, [True, True, True, False], [True, True, True, False], True),
            ("Bending", "FV", True, [True, True, True, False], [True, True, True, False], False)
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_is_label) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.lead_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            left_widgets = {}
            
            if left_vis[0]: # Nom
                if nom_is_label:
                    nom_l = QLabel("0.0")
                    nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_l = QLineEdit("0.0")
                    nom_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_l, r, 3)
                left_widgets["nom"] = nom_l
            
            if left_vis[1]: # Upp
                upp_l = QLineEdit("0.0")
                upp_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_l, r, 4)
                left_widgets["upp"] = upp_l
                
            if left_vis[2]: # Low
                low_l = QLineEdit("0.0")
                low_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_l, r, 5)
                left_widgets["low"] = low_l
                
            if left_vis[3]: # Qual
                qual_l = QLineEdit("5")
                qual_l.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_l, r, 6)
                left_widgets["qual"] = qual_l
            
            # Right Side inputs
            right_widgets = {}
            
            if right_vis[0]: # Nom
                if nom_is_label:
                    nom_r = QLabel("0.0")
                    nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_r = QLineEdit("0.0")
                    nom_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_r, r, 8)
                right_widgets["nom"] = nom_r
                
            if right_vis[1]: # Upp
                upp_r = QLineEdit("0.0")
                upp_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_r, r, 9)
                right_widgets["upp"] = upp_r
                
            if right_vis[2]: # Low
                low_r = QLineEdit("0.0")
                low_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_r, r, 10)
                right_widgets["low"] = low_r
                
            if right_vis[3]: # Qual
                qual_r = QLineEdit("5")
                qual_r.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_r, r, 11)
                right_widgets["qual"] = qual_r
            
            # Store references
            self.lead_inputs[code] = {
                "left": left_widgets,
                "right": right_widgets
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right)
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "lead"))
        
        # Left Copy Button (Right to Left)
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "lead"))
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter)
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter)
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store lead_inputs in the page widget so we can access it later
        if hasattr(self, 'lead_inputs'):
            page.lead_inputs = self.lead_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize field states
        self.toggle_lead_header_mode("left", "limits")
        self.toggle_lead_header_mode("right", "limits")

    def create_din3962_spacing_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QGroupBox {
                border: 1px solid #808080;
                margin-top: 10px;
                font-weight: normal;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.spacing_quality_spin = QSpinBox()
        self.spacing_quality_spin.setRange(1, 12)
        self.spacing_quality_spin.setValue(5)
        self.spacing_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.spacing_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(self.spacing_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Spacing Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "spacing_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if pixmap.height() > 80:
                pixmap = pixmap.scaledToHeight(80, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # Placeholder if no icon
            icon_label.setText("Spacing")
            icon_label.setStyleSheet("border: 1px solid #ccc; background: white; padding: 5px;")
            icon_label.setFixedSize(80, 80)
            icon_label.setAlignment(Qt.AlignCenter)
            
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Spacing Group
        spacing_group = QGroupBox("Spacing")
        spacing_layout = QGridLayout(spacing_group)
        spacing_layout.setSpacing(5)
        spacing_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        spacing_layout.addWidget(QLabel("left"), 0, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(QLabel("right"), 0, 5, 1, 2, Qt.AlignCenter)
        
        # Add vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #808080;")
        spacing_layout.addWidget(sep, 0, 4, 7, 1) # Span down to cover rows
        
        # Buttons/Headers
        self.spacing_btn_lim_l = QPushButton("Lim. upp.")
        self.spacing_btn_qual_l = QPushButton("Quality")
        self.spacing_btn_lim_r = QPushButton("Lim. upp.")
        self.spacing_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.spacing_btn_lim_l, self.spacing_btn_qual_l, self.spacing_btn_lim_r, self.spacing_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.spacing_btn_lim_l.setChecked(True)
        self.spacing_btn_qual_l.setChecked(False)
        self.spacing_btn_lim_r.setChecked(True)
        self.spacing_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.spacing_btn_lim_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "limits"))
        self.spacing_btn_qual_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "quality"))
        self.spacing_btn_lim_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "limits"))
        self.spacing_btn_qual_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "quality"))
        
        spacing_layout.addWidget(self.spacing_btn_lim_l, 1, 2)
        spacing_layout.addWidget(self.spacing_btn_qual_l, 1, 3)
        spacing_layout.addWidget(self.spacing_btn_lim_r, 1, 5)
        spacing_layout.addWidget(self.spacing_btn_qual_r, 1, 6)
        
        self.spacing_inputs = {}
        rows = [
            ("Individual error", "fp"),
            ("Pitch jump", "fu"),
            ("Total error", "Fp"),
            ("Pitch-span var.", "Fpz/8")
        ]
        
        for r, (label, code) in enumerate(rows):
            row_idx = r + 2
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            spacing_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            upp_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            upp_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            spacing_layout.addWidget(upp_l, row_idx, 2)
            spacing_layout.addWidget(qual_l, row_idx, 3)
            spacing_layout.addWidget(upp_r, row_idx, 5)
            spacing_layout.addWidget(qual_r, row_idx, 6)
            
            self.spacing_inputs[code] = {
                "left": {"upp": upp_l, "qual": qual_l},
                "right": {"upp": upp_r, "qual": qual_r}
            }
            
        # Copy Buttons
        copy_row = len(rows) + 2
        
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover { background-color: #e0e0ff; }
            QPushButton:pressed { border: 2px inset #a0a0a0; background-color: #d0d0d0; }
        """
        
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(60, 30)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "spacing"))
        
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(60, 30)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "spacing"))
        
        spacing_layout.addWidget(copy_r_btn, copy_row, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(copy_l_btn, copy_row, 5, 1, 2, Qt.AlignCenter)
            
        layout.addWidget(spacing_group)
        
        # Run-out Group
        runout_group = QGroupBox("Run-out / Tooth thickness")
        runout_layout = QGridLayout(runout_group)
        runout_layout.setSpacing(5)
        runout_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        self.runout_btn_lim = QPushButton("Lim. upp.")
        self.runout_btn_qual = QPushButton("Quality")
        
        for btn in [self.runout_btn_lim, self.runout_btn_qual]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.runout_btn_lim.setChecked(True)
        self.runout_btn_qual.setChecked(False)
        
        # Connect signals
        self.runout_btn_lim.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "limits"))
        self.runout_btn_qual.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "quality"))
        
        runout_layout.addWidget(self.runout_btn_lim, 0, 2)
        runout_layout.addWidget(self.runout_btn_qual, 0, 3)
        
        rows_runout = [
            ("Run-out", "Fr"),
            ("Variation of tooth thickness", "Rs")
        ]
        
        for r, (label, code) in enumerate(rows_runout):
            row_idx = r + 1
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            runout_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp = QLineEdit("0.0")
            qual = QLineEdit("5")
            
            upp.setAlignment(Qt.AlignRight)
            qual.setAlignment(Qt.AlignCenter)
            
            runout_layout.addWidget(upp, row_idx, 2)
            runout_layout.addWidget(qual, row_idx, 3)
            
            self.spacing_inputs[code] = {"upp": upp, "qual": qual}
            
        layout.addWidget(runout_group)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
            
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store spacing_inputs in the page widget so we can access it later
        if hasattr(self, 'spacing_inputs'):
            page.spacing_inputs = self.spacing_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize
        self.toggle_spacing_header_mode("left", "limits")
        self.toggle_spacing_header_mode("right", "limits")
        self.toggle_spacing_header_mode("runout", "limits")

    def create_agma_profile_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景
        page.setStyleSheet("background-color: white;") 
        
        # Main layout for the page
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(15, 15, 15, 15)
        page_layout.setSpacing(10)
        
        # Content Area (直接添加到page，不再使用sub_window)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.profile_quality_spin = QSpinBox()
        self.quality_spins["AGMA_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 5480_Profile"] = self.profile_quality_spin
        self.quality_spins["ANSI B92.1_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 2013_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 1997_Profile"] = self.profile_quality_spin
        self.quality_spins["AGMA_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 3962_Profile"] = self.profile_quality_spin
        self.profile_quality_spin.setRange(1, 12)
        self.profile_quality_spin.setValue(5)
        self.profile_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.profile_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(self.profile_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Tooth Profile Icon
        icon_label = QLabel()
        # Use relative path for portability
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "resources", "profile_tolerance_icon.png")
        
        try:
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Increased size to 100x100 as requested
                icon_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                # Fallback if image not found
                icon_label.setText("Profile")
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedSize(100, 100)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setText("Icon")
            icon_label.setFixedSize(100, 100)
            
        icon_label.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 5px;")
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Main Table Frame
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.Box)
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        # Nom. val is a Label
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.btn_lim_upp_l = QPushButton("Lim. upp.")
        self.btn_lim_low_l = QPushButton("Lim. low.")
        self.btn_qual_l = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_l, self.btn_lim_low_l, self.btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_l.setChecked(True)
        self.btn_lim_low_l.setChecked(True)
        self.btn_qual_l.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_lim_low_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_qual_l.clicked.connect(lambda: self.toggle_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.btn_qual_l, 1, 6)
        
        # Right Side Headers
        # Nom. val is a Label
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.btn_lim_upp_r = QPushButton("Lim. upp.")
        self.btn_lim_low_r = QPushButton("Lim. low.")
        self.btn_qual_r = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_r, self.btn_lim_low_r, self.btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_r.setChecked(True)
        self.btn_lim_low_r.setChecked(True)
        self.btn_qual_r.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_lim_low_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_qual_r.clicked.connect(lambda: self.toggle_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.btn_qual_r, 1, 11)
        
        # Data Rows
        self.profile_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_Editable: True=QLineEdit, False=QLabel)
        # True = Visible, False = Hidden
        rows = [
            ("Angular error", "fHa", True, 
             [True, True, True, True], [True, True, True, True], False), # All visible, Nom not editable
            ("Variance Ang.err.", "Var", True, 
             [False, True, False, False], [False, True, False, False], False), # Nom, Low, Qual hidden
            ("Total error", "Fa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Form error", "ffa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Crowning", "Ca", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Tip-relief", "fKo", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Root-relief", "fFu", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Profile twist", "PV", True, 
             [True, True, True, False], [True, True, True, False], True)  # Qual hidden, Nom EDITABLE
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_editable) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.profile_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_l = QLineEdit("0.0")
                nom_l.setAlignment(Qt.AlignRight)
            else:
                nom_l = QLabel("0.0")
                nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_l = QLineEdit("0.0")
            low_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            low_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            
            if left_vis[0]: grid_layout.addWidget(nom_l, r, 3)
            else: nom_l.setVisible(False)
            
            if left_vis[1]: grid_layout.addWidget(upp_l, r, 4)
            else: upp_l.setVisible(False)
            
            if left_vis[2]: grid_layout.addWidget(low_l, r, 5)
            else: low_l.setVisible(False)
            
            if left_vis[3]: grid_layout.addWidget(qual_l, r, 6)
            else: qual_l.setVisible(False)
            
            # Right Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_r = QLineEdit("0.0")
                nom_r.setAlignment(Qt.AlignRight)
            else:
                nom_r = QLabel("0.0")
                nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_r = QLineEdit("0.0")
            low_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_r.setAlignment(Qt.AlignRight)
            low_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            if right_vis[0]: grid_layout.addWidget(nom_r, r, 8)
            else: nom_r.setVisible(False)
            
            if right_vis[1]: grid_layout.addWidget(upp_r, r, 9)
            else: upp_r.setVisible(False)
            
            if right_vis[2]: grid_layout.addWidget(low_r, r, 10)
            else: low_r.setVisible(False)
            
            if right_vis[3]: grid_layout.addWidget(qual_r, r, 11)
            else: qual_r.setVisible(False)
            
            # Store references
            self.profile_inputs[code] = {
                "left": {"nom": nom_l, "upp": upp_l, "low": low_l, "qual": qual_l},
                "right": {"nom": nom_r, "upp": upp_r, "low": low_r, "qual": qual_r}
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right) - under left section
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "profile"))
        
        # Left Copy Button (Right to Left) - under right section
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "profile"))
        
        # Add buttons to grid
        # Centered under the respective sections
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Under Left section? No, usually arrows point direction.
        # Ref image shows arrows at bottom.
        # Left arrow is under Right section pointing Left? Or under Left section?
        # Image 1 shows:
        # Left side has "Ba ->" (Left to Right?) No, wait.
        # Image 1 shows:
        # Under Left section: Arrow pointing RIGHT (Ba ->)
        # Under Right section: Arrow pointing LEFT (<- Ba)
        # Wait, usually "Ba ->" means Copy FROM Ba TO other?
        # Let's assume:
        # Button under Left section: Copy Left -> Right
        # Button under Right section: Copy Right -> Left
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Left side, arrow pointing right
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter) # Right side, arrow pointing left
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Store profile_inputs in the page widget so we can access it later
        if hasattr(self, 'profile_inputs'):
            page.profile_inputs = self.profile_inputs
        
        self.content_stack.addWidget(page)

    def create_agma_lead_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.lead_quality_spin = QSpinBox()
        self.lead_quality_spin.setRange(1, 12)
        self.lead_quality_spin.setValue(5)
        self.lead_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.lead_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(self.lead_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }""")
        set_btn.clicked.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Add Lead Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "lead_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            # Scale to reasonable height if needed, e.g. 60px
            if pixmap.height() > 60:
                pixmap = pixmap.scaledToHeight(60, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Table Frame
        table_frame = QFrame()
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.lead_btn_lim_upp_l = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_l = QPushButton("Lim. low.")
        self.lead_btn_qual_l = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_l, self.lead_btn_lim_low_l, self.lead_btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_l.setChecked(True)
        self.lead_btn_lim_low_l.setChecked(True)
        self.lead_btn_qual_l.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_lim_low_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_qual_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.lead_btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.lead_btn_qual_l, 1, 6)
        
        # Right Side Headers
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.lead_btn_lim_upp_r = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_r = QPushButton("Lim. low.")
        self.lead_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_r, self.lead_btn_lim_low_r, self.lead_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_r.setChecked(True)
        self.lead_btn_lim_low_r.setChecked(True)
        self.lead_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_lim_low_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_qual_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.lead_btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.lead_btn_qual_r, 1, 11)
        
        # Data Rows
        self.lead_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_is_label: True=QLabel (no border), False=QLineEdit)
        rows = [
            ("Angular error", "fHb", True, [True, True, True, True], [True, True, True, True], True),
            ("Variance Ang.err.", "Var", True, [False, True, False, False], [False, True, False, False], False),
            ("Total error", "Fb", True, [False, True, False, True], [False, True, False, True], False),
            ("Form error", "ffb", True, [False, True, False, True], [False, True, False, True], False),
            ("Crowning", "Cb", True, [True, True, True, False], [True, True, True, False], True),
            ("Top-relief (lead)", "fo", True, [True, True, True, False], [True, True, True, False], True),
            ("Bottom-relief (lead)", "fu", True, [True, True, True, False], [True, True, True, False], True),
            ("Bending", "FV", True, [True, True, True, False], [True, True, True, False], False)
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_is_label) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.lead_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            left_widgets = {}
            
            if left_vis[0]: # Nom
                if nom_is_label:
                    nom_l = QLabel("0.0")
                    nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_l = QLineEdit("0.0")
                    nom_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_l, r, 3)
                left_widgets["nom"] = nom_l
            
            if left_vis[1]: # Upp
                upp_l = QLineEdit("0.0")
                upp_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_l, r, 4)
                left_widgets["upp"] = upp_l
                
            if left_vis[2]: # Low
                low_l = QLineEdit("0.0")
                low_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_l, r, 5)
                left_widgets["low"] = low_l
                
            if left_vis[3]: # Qual
                qual_l = QLineEdit("5")
                qual_l.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_l, r, 6)
                left_widgets["qual"] = qual_l
            
            # Right Side inputs
            right_widgets = {}
            
            if right_vis[0]: # Nom
                if nom_is_label:
                    nom_r = QLabel("0.0")
                    nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_r = QLineEdit("0.0")
                    nom_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_r, r, 8)
                right_widgets["nom"] = nom_r
                
            if right_vis[1]: # Upp
                upp_r = QLineEdit("0.0")
                upp_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_r, r, 9)
                right_widgets["upp"] = upp_r
                
            if right_vis[2]: # Low
                low_r = QLineEdit("0.0")
                low_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_r, r, 10)
                right_widgets["low"] = low_r
                
            if right_vis[3]: # Qual
                qual_r = QLineEdit("5")
                qual_r.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_r, r, 11)
                right_widgets["qual"] = qual_r
            
            # Store references
            self.lead_inputs[code] = {
                "left": left_widgets,
                "right": right_widgets
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right)
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "lead"))
        
        # Left Copy Button (Right to Left)
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "lead"))
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter)
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter)
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store lead_inputs in the page widget so we can access it later
        if hasattr(self, 'lead_inputs'):
            page.lead_inputs = self.lead_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize field states
        self.toggle_lead_header_mode("left", "limits")
        self.toggle_lead_header_mode("right", "limits")

    def create_agma_spacing_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QGroupBox {
                border: 1px solid #808080;
                margin-top: 10px;
                font-weight: normal;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.spacing_quality_spin = QSpinBox()
        self.spacing_quality_spin.setRange(1, 12)
        self.spacing_quality_spin.setValue(5)
        self.spacing_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.spacing_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(self.spacing_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Spacing Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "spacing_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if pixmap.height() > 80:
                pixmap = pixmap.scaledToHeight(80, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # Placeholder if no icon
            icon_label.setText("Spacing")
            icon_label.setStyleSheet("border: 1px solid #ccc; background: white; padding: 5px;")
            icon_label.setFixedSize(80, 80)
            icon_label.setAlignment(Qt.AlignCenter)
            
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Spacing Group
        spacing_group = QGroupBox("Spacing")
        spacing_layout = QGridLayout(spacing_group)
        spacing_layout.setSpacing(5)
        spacing_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        spacing_layout.addWidget(QLabel("left"), 0, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(QLabel("right"), 0, 5, 1, 2, Qt.AlignCenter)
        
        # Add vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #808080;")
        spacing_layout.addWidget(sep, 0, 4, 7, 1) # Span down to cover rows
        
        # Buttons/Headers
        self.spacing_btn_lim_l = QPushButton("Lim. upp.")
        self.spacing_btn_qual_l = QPushButton("Quality")
        self.spacing_btn_lim_r = QPushButton("Lim. upp.")
        self.spacing_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.spacing_btn_lim_l, self.spacing_btn_qual_l, self.spacing_btn_lim_r, self.spacing_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.spacing_btn_lim_l.setChecked(True)
        self.spacing_btn_qual_l.setChecked(False)
        self.spacing_btn_lim_r.setChecked(True)
        self.spacing_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.spacing_btn_lim_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "limits"))
        self.spacing_btn_qual_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "quality"))
        self.spacing_btn_lim_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "limits"))
        self.spacing_btn_qual_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "quality"))
        
        spacing_layout.addWidget(self.spacing_btn_lim_l, 1, 2)
        spacing_layout.addWidget(self.spacing_btn_qual_l, 1, 3)
        spacing_layout.addWidget(self.spacing_btn_lim_r, 1, 5)
        spacing_layout.addWidget(self.spacing_btn_qual_r, 1, 6)
        
        self.spacing_inputs = {}
        rows = [
            ("Individual error", "fp"),
            ("Pitch jump", "fu"),
            ("Total error", "Fp"),
            ("Pitch-span var.", "Fpz/8")
        ]
        
        for r, (label, code) in enumerate(rows):
            row_idx = r + 2
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            spacing_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            upp_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            upp_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            spacing_layout.addWidget(upp_l, row_idx, 2)
            spacing_layout.addWidget(qual_l, row_idx, 3)
            spacing_layout.addWidget(upp_r, row_idx, 5)
            spacing_layout.addWidget(qual_r, row_idx, 6)
            
            self.spacing_inputs[code] = {
                "left": {"upp": upp_l, "qual": qual_l},
                "right": {"upp": upp_r, "qual": qual_r}
            }
            
        # Copy Buttons
        copy_row = len(rows) + 2
        
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover { background-color: #e0e0ff; }
            QPushButton:pressed { border: 2px inset #a0a0a0; background-color: #d0d0d0; }
        """
        
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(60, 30)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "spacing"))
        
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(60, 30)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "spacing"))
        
        spacing_layout.addWidget(copy_r_btn, copy_row, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(copy_l_btn, copy_row, 5, 1, 2, Qt.AlignCenter)
            
        layout.addWidget(spacing_group)
        
        # Run-out Group
        runout_group = QGroupBox("Run-out / Tooth thickness")
        runout_layout = QGridLayout(runout_group)
        runout_layout.setSpacing(5)
        runout_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        self.runout_btn_lim = QPushButton("Lim. upp.")
        self.runout_btn_qual = QPushButton("Quality")
        
        for btn in [self.runout_btn_lim, self.runout_btn_qual]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.runout_btn_lim.setChecked(True)
        self.runout_btn_qual.setChecked(False)
        
        # Connect signals
        self.runout_btn_lim.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "limits"))
        self.runout_btn_qual.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "quality"))
        
        runout_layout.addWidget(self.runout_btn_lim, 0, 2)
        runout_layout.addWidget(self.runout_btn_qual, 0, 3)
        
        rows_runout = [
            ("Run-out", "Fr"),
            ("Variation of tooth thickness", "Rs")
        ]
        
        for r, (label, code) in enumerate(rows_runout):
            row_idx = r + 1
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            runout_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp = QLineEdit("0.0")
            qual = QLineEdit("5")
            
            upp.setAlignment(Qt.AlignRight)
            qual.setAlignment(Qt.AlignCenter)
            
            runout_layout.addWidget(upp, row_idx, 2)
            runout_layout.addWidget(qual, row_idx, 3)
            
            self.spacing_inputs[code] = {"upp": upp, "qual": qual}
            
        layout.addWidget(runout_group)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
            
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store spacing_inputs in the page widget so we can access it later
        if hasattr(self, 'spacing_inputs'):
            page.spacing_inputs = self.spacing_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize
        self.toggle_spacing_header_mode("left", "limits")
        self.toggle_spacing_header_mode("right", "limits")
        self.toggle_spacing_header_mode("runout", "limits")

    def create_iso1328_1997_profile_page(self):
        page = QWidget()
        
        # Using a gray color to match the MDI style
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        page.setStyleSheet("background-color: white;")

        

        # Main layout for the page

        page_layout = QVBoxLayout(page)

        page_layout.setContentsMargins(15, 15, 15, 15)

        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.profile_quality_spin = QSpinBox()
        self.quality_spins["ISO 1328 : 1997_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 5480_Profile"] = self.profile_quality_spin
        self.quality_spins["ANSI B92.1_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 2013_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 1997_Profile"] = self.profile_quality_spin
        self.quality_spins["AGMA_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 3962_Profile"] = self.profile_quality_spin
        self.profile_quality_spin.setRange(1, 12)
        self.profile_quality_spin.setValue(5)
        self.profile_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.profile_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(self.profile_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Tooth Profile Icon
        icon_label = QLabel()
        # Use relative path for portability
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "resources", "profile_tolerance_icon.png")
        
        try:
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Increased size to 100x100 as requested
                icon_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                # Fallback if image not found
                icon_label.setText("Profile")
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedSize(100, 100)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setText("Icon")
            icon_label.setFixedSize(100, 100)
            
        icon_label.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 5px;")
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Main Table Frame
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.Box)
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        # Nom. val is a Label
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.btn_lim_upp_l = QPushButton("Lim. upp.")
        self.btn_lim_low_l = QPushButton("Lim. low.")
        self.btn_qual_l = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_l, self.btn_lim_low_l, self.btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_l.setChecked(True)
        self.btn_lim_low_l.setChecked(True)
        self.btn_qual_l.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_lim_low_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_qual_l.clicked.connect(lambda: self.toggle_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.btn_qual_l, 1, 6)
        
        # Right Side Headers
        # Nom. val is a Label
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.btn_lim_upp_r = QPushButton("Lim. upp.")
        self.btn_lim_low_r = QPushButton("Lim. low.")
        self.btn_qual_r = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_r, self.btn_lim_low_r, self.btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_r.setChecked(True)
        self.btn_lim_low_r.setChecked(True)
        self.btn_qual_r.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_lim_low_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_qual_r.clicked.connect(lambda: self.toggle_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.btn_qual_r, 1, 11)
        
        # Data Rows
        self.profile_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_Editable: True=QLineEdit, False=QLabel)
        # True = Visible, False = Hidden
        rows = [
            ("Angular error", "fHa", True, 
             [True, True, True, True], [True, True, True, True], False), # All visible, Nom not editable
            ("Variance Ang.err.", "Var", True, 
             [False, True, False, False], [False, True, False, False], False), # Nom, Low, Qual hidden
            ("Total error", "Fa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Form error", "ffa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Crowning", "Ca", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Tip-relief", "fKo", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Root-relief", "fFu", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Profile twist", "PV", True, 
             [True, True, True, False], [True, True, True, False], True)  # Qual hidden, Nom EDITABLE
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_editable) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.profile_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_l = QLineEdit("0.0")
                nom_l.setAlignment(Qt.AlignRight)
            else:
                nom_l = QLabel("0.0")
                nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_l = QLineEdit("0.0")
            low_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            low_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            
            if left_vis[0]: grid_layout.addWidget(nom_l, r, 3)
            else: nom_l.setVisible(False)
            
            if left_vis[1]: grid_layout.addWidget(upp_l, r, 4)
            else: upp_l.setVisible(False)
            
            if left_vis[2]: grid_layout.addWidget(low_l, r, 5)
            else: low_l.setVisible(False)
            
            if left_vis[3]: grid_layout.addWidget(qual_l, r, 6)
            else: qual_l.setVisible(False)
            
            # Right Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_r = QLineEdit("0.0")
                nom_r.setAlignment(Qt.AlignRight)
            else:
                nom_r = QLabel("0.0")
                nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_r = QLineEdit("0.0")
            low_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_r.setAlignment(Qt.AlignRight)
            low_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            if right_vis[0]: grid_layout.addWidget(nom_r, r, 8)
            else: nom_r.setVisible(False)
            
            if right_vis[1]: grid_layout.addWidget(upp_r, r, 9)
            else: upp_r.setVisible(False)
            
            if right_vis[2]: grid_layout.addWidget(low_r, r, 10)
            else: low_r.setVisible(False)
            
            if right_vis[3]: grid_layout.addWidget(qual_r, r, 11)
            else: qual_r.setVisible(False)
            
            # Store references
            self.profile_inputs[code] = {
                "left": {"nom": nom_l, "upp": upp_l, "low": low_l, "qual": qual_l},
                "right": {"nom": nom_r, "upp": upp_r, "low": low_r, "qual": qual_r}
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right) - under left section
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "profile"))
        
        # Left Copy Button (Right to Left) - under right section
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "profile"))
        
        # Add buttons to grid
        # Centered under the respective sections
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Under Left section? No, usually arrows point direction.
        # Ref image shows arrows at bottom.
        # Left arrow is under Right section pointing Left? Or under Left section?
        # Image 1 shows:
        # Left side has "Ba ->" (Left to Right?) No, wait.
        # Image 1 shows:
        # Under Left section: Arrow pointing RIGHT (Ba ->)
        # Under Right section: Arrow pointing LEFT (<- Ba)
        # Wait, usually "Ba ->" means Copy FROM Ba TO other?
        # Let's assume:
        # Button under Left section: Copy Left -> Right
        # Button under Right section: Copy Right -> Left
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Left side, arrow pointing right
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter) # Right side, arrow pointing left
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Store profile_inputs in the page widget so we can access it later
        if hasattr(self, 'profile_inputs'):
            page.profile_inputs = self.profile_inputs
        
        self.content_stack.addWidget(page)

    def create_iso1328_1997_lead_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.lead_quality_spin = QSpinBox()
        self.lead_quality_spin.setRange(1, 12)
        self.lead_quality_spin.setValue(5)
        self.lead_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.lead_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(self.lead_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }""")
        set_btn.clicked.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Add Lead Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "lead_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            # Scale to reasonable height if needed, e.g. 60px
            if pixmap.height() > 60:
                pixmap = pixmap.scaledToHeight(60, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Table Frame
        table_frame = QFrame()
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.lead_btn_lim_upp_l = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_l = QPushButton("Lim. low.")
        self.lead_btn_qual_l = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_l, self.lead_btn_lim_low_l, self.lead_btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_l.setChecked(True)
        self.lead_btn_lim_low_l.setChecked(True)
        self.lead_btn_qual_l.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_lim_low_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_qual_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.lead_btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.lead_btn_qual_l, 1, 6)
        
        # Right Side Headers
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.lead_btn_lim_upp_r = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_r = QPushButton("Lim. low.")
        self.lead_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_r, self.lead_btn_lim_low_r, self.lead_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_r.setChecked(True)
        self.lead_btn_lim_low_r.setChecked(True)
        self.lead_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_lim_low_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_qual_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.lead_btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.lead_btn_qual_r, 1, 11)
        
        # Data Rows
        self.lead_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_is_label: True=QLabel (no border), False=QLineEdit)
        rows = [
            ("Angular error", "fHb", True, [True, True, True, True], [True, True, True, True], True),
            ("Variance Ang.err.", "Var", True, [False, True, False, False], [False, True, False, False], False),
            ("Total error", "Fb", True, [False, True, False, True], [False, True, False, True], False),
            ("Form error", "ffb", True, [False, True, False, True], [False, True, False, True], False),
            ("Crowning", "Cb", True, [True, True, True, False], [True, True, True, False], True),
            ("Top-relief (lead)", "fo", True, [True, True, True, False], [True, True, True, False], True),
            ("Bottom-relief (lead)", "fu", True, [True, True, True, False], [True, True, True, False], True),
            ("Bending", "FV", True, [True, True, True, False], [True, True, True, False], False)
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_is_label) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.lead_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            left_widgets = {}
            
            if left_vis[0]: # Nom
                if nom_is_label:
                    nom_l = QLabel("0.0")
                    nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_l = QLineEdit("0.0")
                    nom_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_l, r, 3)
                left_widgets["nom"] = nom_l
            
            if left_vis[1]: # Upp
                upp_l = QLineEdit("0.0")
                upp_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_l, r, 4)
                left_widgets["upp"] = upp_l
                
            if left_vis[2]: # Low
                low_l = QLineEdit("0.0")
                low_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_l, r, 5)
                left_widgets["low"] = low_l
                
            if left_vis[3]: # Qual
                qual_l = QLineEdit("5")
                qual_l.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_l, r, 6)
                left_widgets["qual"] = qual_l
            
            # Right Side inputs
            right_widgets = {}
            
            if right_vis[0]: # Nom
                if nom_is_label:
                    nom_r = QLabel("0.0")
                    nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_r = QLineEdit("0.0")
                    nom_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_r, r, 8)
                right_widgets["nom"] = nom_r
                
            if right_vis[1]: # Upp
                upp_r = QLineEdit("0.0")
                upp_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_r, r, 9)
                right_widgets["upp"] = upp_r
                
            if right_vis[2]: # Low
                low_r = QLineEdit("0.0")
                low_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_r, r, 10)
                right_widgets["low"] = low_r
                
            if right_vis[3]: # Qual
                qual_r = QLineEdit("5")
                qual_r.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_r, r, 11)
                right_widgets["qual"] = qual_r
            
            # Store references
            self.lead_inputs[code] = {
                "left": left_widgets,
                "right": right_widgets
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right)
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "lead"))
        
        # Left Copy Button (Right to Left)
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "lead"))
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter)
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter)
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store lead_inputs in the page widget so we can access it later
        if hasattr(self, 'lead_inputs'):
            page.lead_inputs = self.lead_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize field states
        self.toggle_lead_header_mode("left", "limits")
        self.toggle_lead_header_mode("right", "limits")

    def create_iso1328_1997_spacing_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QGroupBox {
                border: 1px solid #808080;
                margin-top: 10px;
                font-weight: normal;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.spacing_quality_spin = QSpinBox()
        self.spacing_quality_spin.setRange(1, 12)
        self.spacing_quality_spin.setValue(5)
        self.spacing_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.spacing_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(self.spacing_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Spacing Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "spacing_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if pixmap.height() > 80:
                pixmap = pixmap.scaledToHeight(80, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # Placeholder if no icon
            icon_label.setText("Spacing")
            icon_label.setStyleSheet("border: 1px solid #ccc; background: white; padding: 5px;")
            icon_label.setFixedSize(80, 80)
            icon_label.setAlignment(Qt.AlignCenter)
            
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Spacing Group
        spacing_group = QGroupBox("Spacing")
        spacing_layout = QGridLayout(spacing_group)
        spacing_layout.setSpacing(5)
        spacing_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        spacing_layout.addWidget(QLabel("left"), 0, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(QLabel("right"), 0, 5, 1, 2, Qt.AlignCenter)
        
        # Add vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #808080;")
        spacing_layout.addWidget(sep, 0, 4, 7, 1) # Span down to cover rows
        
        # Buttons/Headers
        self.spacing_btn_lim_l = QPushButton("Lim. upp.")
        self.spacing_btn_qual_l = QPushButton("Quality")
        self.spacing_btn_lim_r = QPushButton("Lim. upp.")
        self.spacing_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.spacing_btn_lim_l, self.spacing_btn_qual_l, self.spacing_btn_lim_r, self.spacing_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.spacing_btn_lim_l.setChecked(True)
        self.spacing_btn_qual_l.setChecked(False)
        self.spacing_btn_lim_r.setChecked(True)
        self.spacing_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.spacing_btn_lim_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "limits"))
        self.spacing_btn_qual_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "quality"))
        self.spacing_btn_lim_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "limits"))
        self.spacing_btn_qual_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "quality"))
        
        spacing_layout.addWidget(self.spacing_btn_lim_l, 1, 2)
        spacing_layout.addWidget(self.spacing_btn_qual_l, 1, 3)
        spacing_layout.addWidget(self.spacing_btn_lim_r, 1, 5)
        spacing_layout.addWidget(self.spacing_btn_qual_r, 1, 6)
        
        self.spacing_inputs = {}
        rows = [
            ("Individual error", "fp"),
            ("Pitch jump", "fu"),
            ("Total error", "Fp"),
            ("Pitch-span var.", "Fpz/8")
        ]
        
        for r, (label, code) in enumerate(rows):
            row_idx = r + 2
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            spacing_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            upp_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            upp_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            spacing_layout.addWidget(upp_l, row_idx, 2)
            spacing_layout.addWidget(qual_l, row_idx, 3)
            spacing_layout.addWidget(upp_r, row_idx, 5)
            spacing_layout.addWidget(qual_r, row_idx, 6)
            
            self.spacing_inputs[code] = {
                "left": {"upp": upp_l, "qual": qual_l},
                "right": {"upp": upp_r, "qual": qual_r}
            }
            
        # Copy Buttons
        copy_row = len(rows) + 2
        
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover { background-color: #e0e0ff; }
            QPushButton:pressed { border: 2px inset #a0a0a0; background-color: #d0d0d0; }
        """
        
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(60, 30)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "spacing"))
        
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(60, 30)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "spacing"))
        
        spacing_layout.addWidget(copy_r_btn, copy_row, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(copy_l_btn, copy_row, 5, 1, 2, Qt.AlignCenter)
            
        layout.addWidget(spacing_group)
        
        # Run-out Group
        runout_group = QGroupBox("Run-out / Tooth thickness")
        runout_layout = QGridLayout(runout_group)
        runout_layout.setSpacing(5)
        runout_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        self.runout_btn_lim = QPushButton("Lim. upp.")
        self.runout_btn_qual = QPushButton("Quality")
        
        for btn in [self.runout_btn_lim, self.runout_btn_qual]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.runout_btn_lim.setChecked(True)
        self.runout_btn_qual.setChecked(False)
        
        # Connect signals
        self.runout_btn_lim.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "limits"))
        self.runout_btn_qual.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "quality"))
        
        runout_layout.addWidget(self.runout_btn_lim, 0, 2)
        runout_layout.addWidget(self.runout_btn_qual, 0, 3)
        
        rows_runout = [
            ("Run-out", "Fr"),
            ("Variation of tooth thickness", "Rs")
        ]
        
        for r, (label, code) in enumerate(rows_runout):
            row_idx = r + 1
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            runout_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp = QLineEdit("0.0")
            qual = QLineEdit("5")
            
            upp.setAlignment(Qt.AlignRight)
            qual.setAlignment(Qt.AlignCenter)
            
            runout_layout.addWidget(upp, row_idx, 2)
            runout_layout.addWidget(qual, row_idx, 3)
            
            self.spacing_inputs[code] = {"upp": upp, "qual": qual}
            
        layout.addWidget(runout_group)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
            
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store spacing_inputs in the page widget so we can access it later
        if hasattr(self, 'spacing_inputs'):
            page.spacing_inputs = self.spacing_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize
        self.toggle_spacing_header_mode("left", "limits")
        self.toggle_spacing_header_mode("right", "limits")
        self.toggle_spacing_header_mode("runout", "limits")

    def create_ansi_b921_profile_page(self):
        page = QWidget()
        
        # Using a gray color to match the MDI style
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        page.setStyleSheet("background-color: white;")

        

        # Main layout for the page

        page_layout = QVBoxLayout(page)

        page_layout.setContentsMargins(15, 15, 15, 15)

        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.profile_quality_spin = QSpinBox()
        self.quality_spins["ANSI B92.1_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 5480_Profile"] = self.profile_quality_spin
        self.quality_spins["ANSI B92.1_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 2013_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 1997_Profile"] = self.profile_quality_spin
        self.quality_spins["AGMA_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 3962_Profile"] = self.profile_quality_spin
        self.profile_quality_spin.setRange(1, 12)
        self.profile_quality_spin.setValue(5)
        self.profile_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.profile_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(self.profile_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Tooth Profile Icon
        icon_label = QLabel()
        # Use relative path for portability
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "resources", "profile_tolerance_icon.png")
        
        try:
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Increased size to 100x100 as requested
                icon_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                # Fallback if image not found
                icon_label.setText("Profile")
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedSize(100, 100)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setText("Icon")
            icon_label.setFixedSize(100, 100)
            
        icon_label.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 5px;")
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Main Table Frame
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.Box)
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        # Nom. val is a Label
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.btn_lim_upp_l = QPushButton("Lim. upp.")
        self.btn_lim_low_l = QPushButton("Lim. low.")
        self.btn_qual_l = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_l, self.btn_lim_low_l, self.btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_l.setChecked(True)
        self.btn_lim_low_l.setChecked(True)
        self.btn_qual_l.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_lim_low_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_qual_l.clicked.connect(lambda: self.toggle_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.btn_qual_l, 1, 6)
        
        # Right Side Headers
        # Nom. val is a Label
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.btn_lim_upp_r = QPushButton("Lim. upp.")
        self.btn_lim_low_r = QPushButton("Lim. low.")
        self.btn_qual_r = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_r, self.btn_lim_low_r, self.btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_r.setChecked(True)
        self.btn_lim_low_r.setChecked(True)
        self.btn_qual_r.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_lim_low_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_qual_r.clicked.connect(lambda: self.toggle_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.btn_qual_r, 1, 11)
        
        # Data Rows
        self.profile_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_Editable: True=QLineEdit, False=QLabel)
        # True = Visible, False = Hidden
        rows = [
            ("Angular error", "fHa", True, 
             [True, True, True, True], [True, True, True, True], False), # All visible, Nom not editable
            ("Variance Ang.err.", "Var", True, 
             [False, True, False, False], [False, True, False, False], False), # Nom, Low, Qual hidden
            ("Total error", "Fa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Form error", "ffa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Crowning", "Ca", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Tip-relief", "fKo", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Root-relief", "fFu", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Profile twist", "PV", True, 
             [True, True, True, False], [True, True, True, False], True)  # Qual hidden, Nom EDITABLE
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_editable) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.profile_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_l = QLineEdit("0.0")
                nom_l.setAlignment(Qt.AlignRight)
            else:
                nom_l = QLabel("0.0")
                nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_l = QLineEdit("0.0")
            low_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            low_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            
            if left_vis[0]: grid_layout.addWidget(nom_l, r, 3)
            else: nom_l.setVisible(False)
            
            if left_vis[1]: grid_layout.addWidget(upp_l, r, 4)
            else: upp_l.setVisible(False)
            
            if left_vis[2]: grid_layout.addWidget(low_l, r, 5)
            else: low_l.setVisible(False)
            
            if left_vis[3]: grid_layout.addWidget(qual_l, r, 6)
            else: qual_l.setVisible(False)
            
            # Right Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_r = QLineEdit("0.0")
                nom_r.setAlignment(Qt.AlignRight)
            else:
                nom_r = QLabel("0.0")
                nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_r = QLineEdit("0.0")
            low_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_r.setAlignment(Qt.AlignRight)
            low_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            if right_vis[0]: grid_layout.addWidget(nom_r, r, 8)
            else: nom_r.setVisible(False)
            
            if right_vis[1]: grid_layout.addWidget(upp_r, r, 9)
            else: upp_r.setVisible(False)
            
            if right_vis[2]: grid_layout.addWidget(low_r, r, 10)
            else: low_r.setVisible(False)
            
            if right_vis[3]: grid_layout.addWidget(qual_r, r, 11)
            else: qual_r.setVisible(False)
            
            # Store references
            self.profile_inputs[code] = {
                "left": {"nom": nom_l, "upp": upp_l, "low": low_l, "qual": qual_l},
                "right": {"nom": nom_r, "upp": upp_r, "low": low_r, "qual": qual_r}
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right) - under left section
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "profile"))
        
        # Left Copy Button (Right to Left) - under right section
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "profile"))
        
        # Add buttons to grid
        # Centered under the respective sections
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Under Left section? No, usually arrows point direction.
        # Ref image shows arrows at bottom.
        # Left arrow is under Right section pointing Left? Or under Left section?
        # Image 1 shows:
        # Left side has "Ba ->" (Left to Right?) No, wait.
        # Image 1 shows:
        # Under Left section: Arrow pointing RIGHT (Ba ->)
        # Under Right section: Arrow pointing LEFT (<- Ba)
        # Wait, usually "Ba ->" means Copy FROM Ba TO other?
        # Let's assume:
        # Button under Left section: Copy Left -> Right
        # Button under Right section: Copy Right -> Left
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Left side, arrow pointing right
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter) # Right side, arrow pointing left
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Store profile_inputs in the page widget so we can access it later
        if hasattr(self, 'profile_inputs'):
            page.profile_inputs = self.profile_inputs
        
        self.content_stack.addWidget(page)

    def create_ansi_b921_lead_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.lead_quality_spin = QSpinBox()
        self.lead_quality_spin.setRange(1, 12)
        self.lead_quality_spin.setValue(5)
        self.lead_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.lead_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(self.lead_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }""")
        set_btn.clicked.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Add Lead Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "lead_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            # Scale to reasonable height if needed, e.g. 60px
            if pixmap.height() > 60:
                pixmap = pixmap.scaledToHeight(60, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Table Frame
        table_frame = QFrame()
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.lead_btn_lim_upp_l = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_l = QPushButton("Lim. low.")
        self.lead_btn_qual_l = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_l, self.lead_btn_lim_low_l, self.lead_btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_l.setChecked(True)
        self.lead_btn_lim_low_l.setChecked(True)
        self.lead_btn_qual_l.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_lim_low_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_qual_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.lead_btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.lead_btn_qual_l, 1, 6)
        
        # Right Side Headers
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.lead_btn_lim_upp_r = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_r = QPushButton("Lim. low.")
        self.lead_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_r, self.lead_btn_lim_low_r, self.lead_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_r.setChecked(True)
        self.lead_btn_lim_low_r.setChecked(True)
        self.lead_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_lim_low_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_qual_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.lead_btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.lead_btn_qual_r, 1, 11)
        
        # Data Rows
        self.lead_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_is_label: True=QLabel (no border), False=QLineEdit)
        rows = [
            ("Angular error", "fHb", True, [True, True, True, True], [True, True, True, True], True),
            ("Variance Ang.err.", "Var", True, [False, True, False, False], [False, True, False, False], False),
            ("Total error", "Fb", True, [False, True, False, True], [False, True, False, True], False),
            ("Form error", "ffb", True, [False, True, False, True], [False, True, False, True], False),
            ("Crowning", "Cb", True, [True, True, True, False], [True, True, True, False], True),
            ("Top-relief (lead)", "fo", True, [True, True, True, False], [True, True, True, False], True),
            ("Bottom-relief (lead)", "fu", True, [True, True, True, False], [True, True, True, False], True),
            ("Bending", "FV", True, [True, True, True, False], [True, True, True, False], False)
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_is_label) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.lead_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            left_widgets = {}
            
            if left_vis[0]: # Nom
                if nom_is_label:
                    nom_l = QLabel("0.0")
                    nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_l = QLineEdit("0.0")
                    nom_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_l, r, 3)
                left_widgets["nom"] = nom_l
            
            if left_vis[1]: # Upp
                upp_l = QLineEdit("0.0")
                upp_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_l, r, 4)
                left_widgets["upp"] = upp_l
                
            if left_vis[2]: # Low
                low_l = QLineEdit("0.0")
                low_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_l, r, 5)
                left_widgets["low"] = low_l
                
            if left_vis[3]: # Qual
                qual_l = QLineEdit("5")
                qual_l.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_l, r, 6)
                left_widgets["qual"] = qual_l
            
            # Right Side inputs
            right_widgets = {}
            
            if right_vis[0]: # Nom
                if nom_is_label:
                    nom_r = QLabel("0.0")
                    nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_r = QLineEdit("0.0")
                    nom_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_r, r, 8)
                right_widgets["nom"] = nom_r
                
            if right_vis[1]: # Upp
                upp_r = QLineEdit("0.0")
                upp_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_r, r, 9)
                right_widgets["upp"] = upp_r
                
            if right_vis[2]: # Low
                low_r = QLineEdit("0.0")
                low_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_r, r, 10)
                right_widgets["low"] = low_r
                
            if right_vis[3]: # Qual
                qual_r = QLineEdit("5")
                qual_r.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_r, r, 11)
                right_widgets["qual"] = qual_r
            
            # Store references
            self.lead_inputs[code] = {
                "left": left_widgets,
                "right": right_widgets
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right)
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "lead"))
        
        # Left Copy Button (Right to Left)
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "lead"))
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter)
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter)
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store lead_inputs in the page widget so we can access it later
        if hasattr(self, 'lead_inputs'):
            page.lead_inputs = self.lead_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize field states
        self.toggle_lead_header_mode("left", "limits")
        self.toggle_lead_header_mode("right", "limits")

    def create_ansi_b921_spacing_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QGroupBox {
                border: 1px solid #808080;
                margin-top: 10px;
                font-weight: normal;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.spacing_quality_spin = QSpinBox()
        self.spacing_quality_spin.setRange(1, 12)
        self.spacing_quality_spin.setValue(5)
        self.spacing_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.spacing_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(self.spacing_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Spacing Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "spacing_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if pixmap.height() > 80:
                pixmap = pixmap.scaledToHeight(80, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # Placeholder if no icon
            icon_label.setText("Spacing")
            icon_label.setStyleSheet("border: 1px solid #ccc; background: white; padding: 5px;")
            icon_label.setFixedSize(80, 80)
            icon_label.setAlignment(Qt.AlignCenter)
            
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Spacing Group
        spacing_group = QGroupBox("Spacing")
        spacing_layout = QGridLayout(spacing_group)
        spacing_layout.setSpacing(5)
        spacing_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        spacing_layout.addWidget(QLabel("left"), 0, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(QLabel("right"), 0, 5, 1, 2, Qt.AlignCenter)
        
        # Add vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #808080;")
        spacing_layout.addWidget(sep, 0, 4, 7, 1) # Span down to cover rows
        
        # Buttons/Headers
        self.spacing_btn_lim_l = QPushButton("Lim. upp.")
        self.spacing_btn_qual_l = QPushButton("Quality")
        self.spacing_btn_lim_r = QPushButton("Lim. upp.")
        self.spacing_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.spacing_btn_lim_l, self.spacing_btn_qual_l, self.spacing_btn_lim_r, self.spacing_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.spacing_btn_lim_l.setChecked(True)
        self.spacing_btn_qual_l.setChecked(False)
        self.spacing_btn_lim_r.setChecked(True)
        self.spacing_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.spacing_btn_lim_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "limits"))
        self.spacing_btn_qual_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "quality"))
        self.spacing_btn_lim_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "limits"))
        self.spacing_btn_qual_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "quality"))
        
        spacing_layout.addWidget(self.spacing_btn_lim_l, 1, 2)
        spacing_layout.addWidget(self.spacing_btn_qual_l, 1, 3)
        spacing_layout.addWidget(self.spacing_btn_lim_r, 1, 5)
        spacing_layout.addWidget(self.spacing_btn_qual_r, 1, 6)
        
        self.spacing_inputs = {}
        rows = [
            ("Individual error", "fp"),
            ("Pitch jump", "fu"),
            ("Total error", "Fp"),
            ("Pitch-span var.", "Fpz/8")
        ]
        
        for r, (label, code) in enumerate(rows):
            row_idx = r + 2
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            spacing_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            upp_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            upp_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            spacing_layout.addWidget(upp_l, row_idx, 2)
            spacing_layout.addWidget(qual_l, row_idx, 3)
            spacing_layout.addWidget(upp_r, row_idx, 5)
            spacing_layout.addWidget(qual_r, row_idx, 6)
            
            self.spacing_inputs[code] = {
                "left": {"upp": upp_l, "qual": qual_l},
                "right": {"upp": upp_r, "qual": qual_r}
            }
            
        # Copy Buttons
        copy_row = len(rows) + 2
        
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover { background-color: #e0e0ff; }
            QPushButton:pressed { border: 2px inset #a0a0a0; background-color: #d0d0d0; }
        """
        
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(60, 30)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "spacing"))
        
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(60, 30)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "spacing"))
        
        spacing_layout.addWidget(copy_r_btn, copy_row, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(copy_l_btn, copy_row, 5, 1, 2, Qt.AlignCenter)
            
        layout.addWidget(spacing_group)
        
        # Run-out Group
        runout_group = QGroupBox("Run-out / Tooth thickness")
        runout_layout = QGridLayout(runout_group)
        runout_layout.setSpacing(5)
        runout_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        self.runout_btn_lim = QPushButton("Lim. upp.")
        self.runout_btn_qual = QPushButton("Quality")
        
        for btn in [self.runout_btn_lim, self.runout_btn_qual]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.runout_btn_lim.setChecked(True)
        self.runout_btn_qual.setChecked(False)
        
        # Connect signals
        self.runout_btn_lim.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "limits"))
        self.runout_btn_qual.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "quality"))
        
        runout_layout.addWidget(self.runout_btn_lim, 0, 2)
        runout_layout.addWidget(self.runout_btn_qual, 0, 3)
        
        rows_runout = [
            ("Run-out", "Fr"),
            ("Variation of tooth thickness", "Rs")
        ]
        
        for r, (label, code) in enumerate(rows_runout):
            row_idx = r + 1
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            runout_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp = QLineEdit("0.0")
            qual = QLineEdit("5")
            
            upp.setAlignment(Qt.AlignRight)
            qual.setAlignment(Qt.AlignCenter)
            
            runout_layout.addWidget(upp, row_idx, 2)
            runout_layout.addWidget(qual, row_idx, 3)
            
            self.spacing_inputs[code] = {"upp": upp, "qual": qual}
            
        layout.addWidget(runout_group)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
            
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store spacing_inputs in the page widget so we can access it later
        if hasattr(self, 'spacing_inputs'):
            page.spacing_inputs = self.spacing_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize
        self.toggle_spacing_header_mode("left", "limits")
        self.toggle_spacing_header_mode("right", "limits")
        self.toggle_spacing_header_mode("runout", "limits")

    def create_din5480_profile_page(self):
        page = QWidget()
        
        # Using a gray color to match the MDI style
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        page.setStyleSheet("background-color: white;")

        

        # Main layout for the page

        page_layout = QVBoxLayout(page)

        page_layout.setContentsMargins(15, 15, 15, 15)

        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.profile_quality_spin = QSpinBox()
        self.quality_spins["DIN 5480_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 5480_Profile"] = self.profile_quality_spin
        self.quality_spins["ANSI B92.1_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 2013_Profile"] = self.profile_quality_spin
        self.quality_spins["ISO 1328 : 1997_Profile"] = self.profile_quality_spin
        self.quality_spins["AGMA_Profile"] = self.profile_quality_spin
        self.quality_spins["DIN 3962_Profile"] = self.profile_quality_spin
        self.profile_quality_spin.setRange(1, 12)
        self.profile_quality_spin.setValue(5)
        self.profile_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.profile_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(self.profile_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Tooth Profile Icon
        icon_label = QLabel()
        # Use relative path for portability
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "resources", "profile_tolerance_icon.png")
        
        try:
            from PyQt5.QtGui import QPixmap
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Increased size to 100x100 as requested
                icon_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                # Fallback if image not found
                icon_label.setText("Profile")
                icon_label.setAlignment(Qt.AlignCenter)
                icon_label.setFixedSize(100, 100)
        except Exception as e:
            print(f"Error loading icon: {e}")
            icon_label.setText("Icon")
            icon_label.setFixedSize(100, 100)
            
        icon_label.setStyleSheet("background-color: white; border: 1px solid #ccc; padding: 5px;")
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        layout.addSpacing(10)
        
        # Main Table Frame
        table_frame = QFrame()
        table_frame.setFrameShape(QFrame.Box)
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        # Nom. val is a Label
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.btn_lim_upp_l = QPushButton("Lim. upp.")
        self.btn_lim_low_l = QPushButton("Lim. low.")
        self.btn_qual_l = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_l, self.btn_lim_low_l, self.btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_l.setChecked(True)
        self.btn_lim_low_l.setChecked(True)
        self.btn_qual_l.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_lim_low_l.clicked.connect(lambda: self.toggle_header_mode("left", "limits"))
        self.btn_qual_l.clicked.connect(lambda: self.toggle_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.btn_qual_l, 1, 6)
        
        # Right Side Headers
        # Nom. val is a Label
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.btn_lim_upp_r = QPushButton("Lim. upp.")
        self.btn_lim_low_r = QPushButton("Lim. low.")
        self.btn_qual_r = QPushButton("Quality")
        
        for btn in [self.btn_lim_upp_r, self.btn_lim_low_r, self.btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.btn_lim_upp_r.setChecked(True)
        self.btn_lim_low_r.setChecked(True)
        self.btn_qual_r.setChecked(False)
        
        # Connect signals
        self.btn_lim_upp_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_lim_low_r.clicked.connect(lambda: self.toggle_header_mode("right", "limits"))
        self.btn_qual_r.clicked.connect(lambda: self.toggle_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.btn_qual_r, 1, 11)
        
        # Data Rows
        self.profile_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_Editable: True=QLineEdit, False=QLabel)
        # True = Visible, False = Hidden
        rows = [
            ("Angular error", "fHa", True, 
             [True, True, True, True], [True, True, True, True], False), # All visible, Nom not editable
            ("Variance Ang.err.", "Var", True, 
             [False, True, False, False], [False, True, False, False], False), # Nom, Low, Qual hidden
            ("Total error", "Fa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Form error", "ffa", True, 
             [False, True, False, True], [False, True, False, True], False), # Left: Nom, Low hidden; Right: Nom, Low hidden
            ("Crowning", "Ca", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Tip-relief", "fKo", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Root-relief", "fFu", False, 
             [True, True, True, False], [True, True, True, False], False), # Qual hidden, Nom not editable
            ("Profile twist", "PV", True, 
             [True, True, True, False], [True, True, True, False], True)  # Qual hidden, Nom EDITABLE
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_editable) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.profile_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_l = QLineEdit("0.0")
                nom_l.setAlignment(Qt.AlignRight)
            else:
                nom_l = QLabel("0.0")
                nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_l = QLineEdit("0.0")
            low_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            low_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            
            if left_vis[0]: grid_layout.addWidget(nom_l, r, 3)
            else: nom_l.setVisible(False)
            
            if left_vis[1]: grid_layout.addWidget(upp_l, r, 4)
            else: upp_l.setVisible(False)
            
            if left_vis[2]: grid_layout.addWidget(low_l, r, 5)
            else: low_l.setVisible(False)
            
            if left_vis[3]: grid_layout.addWidget(qual_l, r, 6)
            else: qual_l.setVisible(False)
            
            # Right Side inputs
            # Nom. val: editable or label based on flag
            if nom_editable:
                nom_r = QLineEdit("0.0")
                nom_r.setAlignment(Qt.AlignRight)
            else:
                nom_r = QLabel("0.0")
                nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
            
            upp_r = QLineEdit("0.0")
            low_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_r.setAlignment(Qt.AlignRight)
            low_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            if right_vis[0]: grid_layout.addWidget(nom_r, r, 8)
            else: nom_r.setVisible(False)
            
            if right_vis[1]: grid_layout.addWidget(upp_r, r, 9)
            else: upp_r.setVisible(False)
            
            if right_vis[2]: grid_layout.addWidget(low_r, r, 10)
            else: low_r.setVisible(False)
            
            if right_vis[3]: grid_layout.addWidget(qual_r, r, 11)
            else: qual_r.setVisible(False)
            
            # Store references
            self.profile_inputs[code] = {
                "left": {"nom": nom_l, "upp": upp_l, "low": low_l, "qual": qual_l},
                "right": {"nom": nom_r, "upp": upp_r, "low": low_r, "qual": qual_r}
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right) - under left section
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "profile"))
        
        # Left Copy Button (Right to Left) - under right section
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "profile"))
        
        # Add buttons to grid
        # Centered under the respective sections
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Under Left section? No, usually arrows point direction.
        # Ref image shows arrows at bottom.
        # Left arrow is under Right section pointing Left? Or under Left section?
        # Image 1 shows:
        # Left side has "Ba ->" (Left to Right?) No, wait.
        # Image 1 shows:
        # Under Left section: Arrow pointing RIGHT (Ba ->)
        # Under Right section: Arrow pointing LEFT (<- Ba)
        # Wait, usually "Ba ->" means Copy FROM Ba TO other?
        # Let's assume:
        # Button under Left section: Copy Left -> Right
        # Button under Right section: Copy Right -> Left
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter) # Left side, arrow pointing right
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter) # Right side, arrow pointing left
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Store profile_inputs in the page widget so we can access it later
        if hasattr(self, 'profile_inputs'):
            page.profile_inputs = self.profile_inputs
        
        self.content_stack.addWidget(page)

    def create_din5480_lead_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.lead_quality_spin = QSpinBox()
        self.lead_quality_spin.setRange(1, 12)
        self.lead_quality_spin.setValue(5)
        self.lead_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.lead_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(self.lead_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }""")
        set_btn.clicked.connect(lambda: self.calculate_tolerances("lead"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Add Lead Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "lead_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            # Scale to reasonable height if needed, e.g. 60px
            if pixmap.height() > 60:
                pixmap = pixmap.scaledToHeight(60, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Table Frame
        table_frame = QFrame()
        table_frame.setLineWidth(1)
        table_frame.setStyleSheet("QFrame { border: 1px solid #808080; background-color: white; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(5, 5, 5, 5)
        table_layout.setSpacing(0)
        
        # Create grid layout for table
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Headers - Top row with left/right
        left_label = QLabel("left")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(left_label, 0, 3, 1, 4)
        
        right_label = QLabel("right")
        right_label.setAlignment(Qt.AlignCenter)
        right_label.setStyleSheet("font-weight: bold; padding: 3px;")
        grid_layout.addWidget(right_label, 0, 8, 1, 4)
        
        # Add vertical separator line between left and right
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #808080;")
        grid_layout.addWidget(separator, 0, 7, 11, 1)
        
        # Column headers
        output_header = QCheckBox("Output")
        output_header.setStyleSheet("font-weight: bold;")
        grid_layout.addWidget(output_header, 1, 0, 1, 2)
        
        # Left Side Headers
        lbl_nom_l = QLabel("Nom. val")
        lbl_nom_l.setAlignment(Qt.AlignCenter)
        lbl_nom_l.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_l, 1, 3)
        
        # Buttons for Left Side
        self.lead_btn_lim_upp_l = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_l = QPushButton("Lim. low.")
        self.lead_btn_qual_l = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_l, self.lead_btn_lim_low_l, self.lead_btn_qual_l]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_l.setChecked(True)
        self.lead_btn_lim_low_l.setChecked(True)
        self.lead_btn_qual_l.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_lim_low_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "limits"))
        self.lead_btn_qual_l.clicked.connect(lambda: self.toggle_lead_header_mode("left", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_l, 1, 4)
        grid_layout.addWidget(self.lead_btn_lim_low_l, 1, 5)
        grid_layout.addWidget(self.lead_btn_qual_l, 1, 6)
        
        # Right Side Headers
        lbl_nom_r = QLabel("Nom. val")
        lbl_nom_r.setAlignment(Qt.AlignCenter)
        lbl_nom_r.setStyleSheet("font-weight: bold; padding: 2px;")
        grid_layout.addWidget(lbl_nom_r, 1, 8)
        
        # Buttons for Right Side
        self.lead_btn_lim_upp_r = QPushButton("Lim. upp.")
        self.lead_btn_lim_low_r = QPushButton("Lim. low.")
        self.lead_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.lead_btn_lim_upp_r, self.lead_btn_lim_low_r, self.lead_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default state: Limits checked, Quality unchecked
        self.lead_btn_lim_upp_r.setChecked(True)
        self.lead_btn_lim_low_r.setChecked(True)
        self.lead_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.lead_btn_lim_upp_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_lim_low_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "limits"))
        self.lead_btn_qual_r.clicked.connect(lambda: self.toggle_lead_header_mode("right", "quality"))
        
        grid_layout.addWidget(self.lead_btn_lim_upp_r, 1, 9)
        grid_layout.addWidget(self.lead_btn_lim_low_r, 1, 10)
        grid_layout.addWidget(self.lead_btn_qual_r, 1, 11)
        
        # Data Rows
        self.lead_inputs = {}
        # Format: (Label, Code, Checked, 
        #          Left_Visibility[Nom, Upp, Low, Qual], 
        #          Right_Visibility[Nom, Upp, Low, Qual],
        #          Nom_is_label: True=QLabel (no border), False=QLineEdit)
        rows = [
            ("Angular error", "fHb", True, [True, True, True, True], [True, True, True, True], True),
            ("Variance Ang.err.", "Var", True, [False, True, False, False], [False, True, False, False], False),
            ("Total error", "Fb", True, [False, True, False, True], [False, True, False, True], False),
            ("Form error", "ffb", True, [False, True, False, True], [False, True, False, True], False),
            ("Crowning", "Cb", True, [True, True, True, False], [True, True, True, False], True),
            ("Top-relief (lead)", "fo", True, [True, True, True, False], [True, True, True, False], True),
            ("Bottom-relief (lead)", "fu", True, [True, True, True, False], [True, True, True, False], True),
            ("Bending", "FV", True, [True, True, True, False], [True, True, True, False], False)
        ]
        
        for row_idx, (label, code, checked, left_vis, right_vis, nom_is_label) in enumerate(rows):
            r = row_idx + 2
            
            # Checkbox with label
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(checked)
            grid_layout.addWidget(chk, r, 0, 1, 2)
            self.lead_inputs[f"{code}_check"] = chk
            
            # Left Side inputs
            left_widgets = {}
            
            if left_vis[0]: # Nom
                if nom_is_label:
                    nom_l = QLabel("0.0")
                    nom_l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_l.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_l = QLineEdit("0.0")
                    nom_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_l, r, 3)
                left_widgets["nom"] = nom_l
            
            if left_vis[1]: # Upp
                upp_l = QLineEdit("0.0")
                upp_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_l, r, 4)
                left_widgets["upp"] = upp_l
                
            if left_vis[2]: # Low
                low_l = QLineEdit("0.0")
                low_l.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_l, r, 5)
                left_widgets["low"] = low_l
                
            if left_vis[3]: # Qual
                qual_l = QLineEdit("5")
                qual_l.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_l, r, 6)
                left_widgets["qual"] = qual_l
            
            # Right Side inputs
            right_widgets = {}
            
            if right_vis[0]: # Nom
                if nom_is_label:
                    nom_r = QLabel("0.0")
                    nom_r.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    nom_r.setStyleSheet("border: none; background: transparent; padding: 2px;")
                else:
                    nom_r = QLineEdit("0.0")
                    nom_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(nom_r, r, 8)
                right_widgets["nom"] = nom_r
                
            if right_vis[1]: # Upp
                upp_r = QLineEdit("0.0")
                upp_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(upp_r, r, 9)
                right_widgets["upp"] = upp_r
                
            if right_vis[2]: # Low
                low_r = QLineEdit("0.0")
                low_r.setAlignment(Qt.AlignRight)
                grid_layout.addWidget(low_r, r, 10)
                right_widgets["low"] = low_r
                
            if right_vis[3]: # Qual
                qual_r = QLineEdit("5")
                qual_r.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(qual_r, r, 11)
                right_widgets["qual"] = qual_r
            
            # Store references
            self.lead_inputs[code] = {
                "left": left_widgets,
                "right": right_widgets
            }
        
        # Copy Buttons Row
        copy_row_idx = len(rows) + 2
        
        # Define unified button style
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0ff;
            }
            QPushButton:pressed {
                border: 2px inset #a0a0a0;
                background-color: #d0d0d0;
            }
        """
        
        # Right Copy Button (Left to Right)
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(80, 40)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.setToolTip("Copy from Left to Right")
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "lead"))
        
        # Left Copy Button (Right to Left)
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(80, 40)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.setToolTip("Copy from Right to Left")
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "lead"))
        
        grid_layout.addWidget(copy_r_btn, copy_row_idx, 3, 1, 4, Qt.AlignCenter)
        grid_layout.addWidget(copy_l_btn, copy_row_idx, 8, 1, 4, Qt.AlignCenter)
        
        table_layout.addWidget(grid_widget)
        layout.addWidget(table_frame)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
        
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store lead_inputs in the page widget so we can access it later
        if hasattr(self, 'lead_inputs'):
            page.lead_inputs = self.lead_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize field states
        self.toggle_lead_header_mode("left", "limits")
        self.toggle_lead_header_mode("right", "limits")

    def create_din5480_spacing_page(self):
        page = QWidget()
        
        # 简化：移除MDI背景和sub_window容器，直接使用白色背景

        
        page.setStyleSheet("background-color: white;")

        
        

        
        # Main layout for the page

        
        page_layout = QVBoxLayout(page)

        
        page_layout.setContentsMargins(15, 15, 15, 15)

        
        page_layout.setSpacing(10)
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 9pt;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #a0a0a0;
                padding: 2px;
                min-width: 50px;
            }
            QCheckBox {
                spacing: 5px;
            }
            QGroupBox {
                border: 1px solid #808080;
                margin-top: 10px;
                font-weight: normal;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
                left: 10px;
            }
        """)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        self.spacing_quality_spin = QSpinBox()
        self.spacing_quality_spin.setRange(1, 12)
        self.spacing_quality_spin.setValue(5)
        self.spacing_quality_spin.setFixedWidth(50)
        # 移除valueChanged连接，只在SET按钮点击时更新
        # self.spacing_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(self.spacing_quality_spin)
        
        set_btn = QPushButton("Set")
        set_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffff00;
                border: 1px solid #808080;
                padding: 3px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffff80;
            }
        """)
        set_btn.clicked.connect(lambda: self.calculate_tolerances("spacing"))
        header_layout.addWidget(set_btn)
        header_layout.addStretch()
        
        # Spacing Icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "spacing_tolerance_icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if pixmap.height() > 80:
                pixmap = pixmap.scaledToHeight(80, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            # Placeholder if no icon
            icon_label.setText("Spacing")
            icon_label.setStyleSheet("border: 1px solid #ccc; background: white; padding: 5px;")
            icon_label.setFixedSize(80, 80)
            icon_label.setAlignment(Qt.AlignCenter)
            
        header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # Spacing Group
        spacing_group = QGroupBox("Spacing")
        spacing_layout = QGridLayout(spacing_group)
        spacing_layout.setSpacing(5)
        spacing_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        spacing_layout.addWidget(QLabel("left"), 0, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(QLabel("right"), 0, 5, 1, 2, Qt.AlignCenter)
        
        # Add vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #808080;")
        spacing_layout.addWidget(sep, 0, 4, 7, 1) # Span down to cover rows
        
        # Buttons/Headers
        self.spacing_btn_lim_l = QPushButton("Lim. upp.")
        self.spacing_btn_qual_l = QPushButton("Quality")
        self.spacing_btn_lim_r = QPushButton("Lim. upp.")
        self.spacing_btn_qual_r = QPushButton("Quality")
        
        for btn in [self.spacing_btn_lim_l, self.spacing_btn_qual_l, self.spacing_btn_lim_r, self.spacing_btn_qual_r]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.spacing_btn_lim_l.setChecked(True)
        self.spacing_btn_qual_l.setChecked(False)
        self.spacing_btn_lim_r.setChecked(True)
        self.spacing_btn_qual_r.setChecked(False)
        
        # Connect signals
        self.spacing_btn_lim_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "limits"))
        self.spacing_btn_qual_l.clicked.connect(lambda: self.toggle_spacing_header_mode("left", "quality"))
        self.spacing_btn_lim_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "limits"))
        self.spacing_btn_qual_r.clicked.connect(lambda: self.toggle_spacing_header_mode("right", "quality"))
        
        spacing_layout.addWidget(self.spacing_btn_lim_l, 1, 2)
        spacing_layout.addWidget(self.spacing_btn_qual_l, 1, 3)
        spacing_layout.addWidget(self.spacing_btn_lim_r, 1, 5)
        spacing_layout.addWidget(self.spacing_btn_qual_r, 1, 6)
        
        self.spacing_inputs = {}
        rows = [
            ("Individual error", "fp"),
            ("Pitch jump", "fu"),
            ("Total error", "Fp"),
            ("Pitch-span var.", "Fpz/8")
        ]
        
        for r, (label, code) in enumerate(rows):
            row_idx = r + 2
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            spacing_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp_l = QLineEdit("0.0")
            qual_l = QLineEdit("5")
            upp_r = QLineEdit("0.0")
            qual_r = QLineEdit("5")
            
            upp_l.setAlignment(Qt.AlignRight)
            qual_l.setAlignment(Qt.AlignCenter)
            upp_r.setAlignment(Qt.AlignRight)
            qual_r.setAlignment(Qt.AlignCenter)
            
            spacing_layout.addWidget(upp_l, row_idx, 2)
            spacing_layout.addWidget(qual_l, row_idx, 3)
            spacing_layout.addWidget(upp_r, row_idx, 5)
            spacing_layout.addWidget(qual_r, row_idx, 6)
            
            self.spacing_inputs[code] = {
                "left": {"upp": upp_l, "qual": qual_l},
                "right": {"upp": upp_r, "qual": qual_r}
            }
            
        # Copy Buttons
        copy_row = len(rows) + 2
        
        button_style = """
            QPushButton {
                border: 2px outset #a0a0a0;
                background-color: #f0f0f0;
                border-radius: 3px;
                font-size: 10pt;
                padding: 5px;
            }
            QPushButton:hover { background-color: #e0e0ff; }
            QPushButton:pressed { border: 2px inset #a0a0a0; background-color: #d0d0d0; }
        """
        
        copy_r_btn = QPushButton("→")
        copy_r_btn.setFixedSize(60, 30)
        copy_r_btn.setStyleSheet(button_style)
        copy_r_btn.clicked.connect(lambda: self.copy_tolerances("left_to_right", "spacing"))
        
        copy_l_btn = QPushButton("←")
        copy_l_btn.setFixedSize(60, 30)
        copy_l_btn.setStyleSheet(button_style)
        copy_l_btn.clicked.connect(lambda: self.copy_tolerances("right_to_left", "spacing"))
        
        spacing_layout.addWidget(copy_r_btn, copy_row, 2, 1, 2, Qt.AlignCenter)
        spacing_layout.addWidget(copy_l_btn, copy_row, 5, 1, 2, Qt.AlignCenter)
            
        layout.addWidget(spacing_group)
        
        # Run-out Group
        runout_group = QGroupBox("Run-out / Tooth thickness")
        runout_layout = QGridLayout(runout_group)
        runout_layout.setSpacing(5)
        runout_layout.setContentsMargins(10, 15, 10, 10)
        
        # Headers
        self.runout_btn_lim = QPushButton("Lim. upp.")
        self.runout_btn_qual = QPushButton("Quality")
        
        for btn in [self.runout_btn_lim, self.runout_btn_qual]:
            btn.setCheckable(True)
            btn.setFixedHeight(24)
            
        # Default states
        self.runout_btn_lim.setChecked(True)
        self.runout_btn_qual.setChecked(False)
        
        # Connect signals
        self.runout_btn_lim.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "limits"))
        self.runout_btn_qual.clicked.connect(lambda: self.toggle_spacing_header_mode("runout", "quality"))
        
        runout_layout.addWidget(self.runout_btn_lim, 0, 2)
        runout_layout.addWidget(self.runout_btn_qual, 0, 3)
        
        rows_runout = [
            ("Run-out", "Fr"),
            ("Variation of tooth thickness", "Rs")
        ]
        
        for r, (label, code) in enumerate(rows_runout):
            row_idx = r + 1
            chk = QCheckBox(f"{label}   {code}")
            chk.setChecked(True)
            runout_layout.addWidget(chk, row_idx, 0, 1, 2)
            self.spacing_inputs[f"{code}_check"] = chk
            
            upp = QLineEdit("0.0")
            qual = QLineEdit("5")
            
            upp.setAlignment(Qt.AlignRight)
            qual.setAlignment(Qt.AlignCenter)
            
            runout_layout.addWidget(upp, row_idx, 2)
            runout_layout.addWidget(qual, row_idx, 3)
            
            self.spacing_inputs[code] = {"upp": upp, "qual": qual}
            
        layout.addWidget(runout_group)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(QLabel("Tolerances in μm"))
        footer_layout.addStretch()
        layout.addLayout(footer_layout)
        
        layout.addSpacing(10)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        return_btn = QPushButton("Return")
        return_btn.setFixedWidth(80)
        btn_layout.addWidget(return_btn)
        
        continue_btn = QPushButton("Continue")
        continue_btn.setFixedWidth(80)
        btn_layout.addWidget(continue_btn)
            
        ok_btn = QPushButton("Ok")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("Apply")
        apply_btn.setFixedWidth(80)
        apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(apply_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Add content widget to window layout
        # Add content widget directly to page layout (移除sub_window容器)
        page_layout.addWidget(content_widget)
        
        # Add sub-window to page layout with centering
        
        # Store spacing_inputs in the page widget so we can access it later
        if hasattr(self, 'spacing_inputs'):
            page.spacing_inputs = self.spacing_inputs
        
        self.content_stack.addWidget(page)
        
        # Initialize
        self.toggle_spacing_header_mode("left", "limits")
        self.toggle_spacing_header_mode("right", "limits")
        self.toggle_spacing_header_mode("runout", "limits")

    def create_empty_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Not implemented yet"))
        self.content_stack.addWidget(page)

    def load_initial_data(self):
        """Load saved tolerance settings from gear_data"""
        if not self.gear_data:
            return
        
        saved_settings = self.gear_data.get('tolerance_settings', {})
        if not saved_settings:
            return
        
        # Map page indices to page keys
        page_mapping = {
            0: "DIN 3962_Profile",
            1: "DIN 3962_Lead / Line of action",
            2: "DIN 3962_Spacing",
            3: "AGMA_Profile",
            4: "AGMA_Lead / Line of action",
            5: "AGMA_Spacing",
            6: "ISO 1328 : 1997_Profile",
            7: "ISO 1328 : 1997_Lead / Line of action",
            8: "ISO 1328 : 1997_Spacing",
            9: "ISO 1328 : 2013_Profile",
            10: "ISO 1328 : 2013_Lead / Line of action",
            11: "ISO 1328 : 2013_Spacing",
            12: "ANSI B92.1_Profile",
            13: "ANSI B92.1_Lead / Line of action",
            14: "ANSI B92.1_Spacing",
            15: "DIN 5480_Profile",
            16: "DIN 5480_Lead / Line of action",
            17: "DIN 5480_Spacing"
        }
        
        # Load data for each page
        for page_index, page_key in page_mapping.items():
            if page_key not in saved_settings:
                continue
            
            page = self.content_stack.widget(page_index)
            if not page:
                continue
            
            page_data = saved_settings[page_key]
            quality = page_data.get("quality", 5)
            data_dict = page_data.get("data", {})
            
            # Set quality level in spinbox
            spin_boxes = page.findChildren(QSpinBox)
            for spin_box in spin_boxes:
                if spin_box.minimum() == 1 and spin_box.maximum() == 12:
                    spin_box.setValue(quality)
                    break
            
            # Load data based on page type
            if "profile" in page_key.lower() and hasattr(page, 'profile_inputs'):
                inputs = page.profile_inputs
                for code, code_data in data_dict.items():
                    if code not in inputs:
                        continue
                    input_dict = inputs[code]
                    if isinstance(code_data, dict) and "left" in code_data and "right" in code_data:
                        # Load left side
                        if "left" in input_dict:
                            left_dict = code_data["left"]
                            if "nom" in input_dict["left"]:
                                widget = input_dict["left"]["nom"]
                                if isinstance(widget, (QLineEdit, QLabel)):
                                    widget.setText(str(left_dict.get("nom", 0)))
                            if "upp" in input_dict["left"]:
                                widget = input_dict["left"]["upp"]
                                if isinstance(widget, QLineEdit):
                                    widget.setText(str(left_dict.get("upp", 0)))
                            if "low" in input_dict["left"]:
                                widget = input_dict["left"]["low"]
                                if isinstance(widget, QLineEdit):
                                    widget.setText(str(left_dict.get("low", 0)))
                            if "qual" in input_dict["left"]:
                                widget = input_dict["left"]["qual"]
                                if isinstance(widget, QLineEdit):
                                    widget.setText(str(left_dict.get("qual", quality)))
                        
                        # Load right side
                        if "right" in input_dict:
                            right_dict = code_data["right"]
                            if "nom" in input_dict["right"]:
                                widget = input_dict["right"]["nom"]
                                if isinstance(widget, (QLineEdit, QLabel)):
                                    widget.setText(str(right_dict.get("nom", 0)))
                            if "upp" in input_dict["right"]:
                                widget = input_dict["right"]["upp"]
                                if isinstance(widget, QLineEdit):
                                    widget.setText(str(right_dict.get("upp", 0)))
                            if "low" in input_dict["right"]:
                                widget = input_dict["right"]["low"]
                                if isinstance(widget, QLineEdit):
                                    widget.setText(str(right_dict.get("low", 0)))
                            if "qual" in input_dict["right"]:
                                widget = input_dict["right"]["qual"]
                                if isinstance(widget, QLineEdit):
                                    widget.setText(str(right_dict.get("qual", quality)))
            
            elif "lead" in page_key.lower() and hasattr(page, 'lead_inputs'):
                inputs = page.lead_inputs
                for code, code_data in data_dict.items():
                    if code not in inputs:
                        continue
                    input_dict = inputs[code]
                    if isinstance(code_data, dict) and "left" in code_data and "right" in code_data:
                        # Load left side
                        if "left" in input_dict:
                            left_dict = code_data["left"]
                            for key in ["nom", "upp", "low", "qual"]:
                                if key in input_dict["left"]:
                                    widget = input_dict["left"][key]
                                    if isinstance(widget, (QLineEdit, QLabel)):
                                        widget.setText(str(left_dict.get(key, 0 if key != "qual" else quality)))
                        
                        # Load right side
                        if "right" in input_dict:
                            right_dict = code_data["right"]
                            for key in ["nom", "upp", "low", "qual"]:
                                if key in input_dict["right"]:
                                    widget = input_dict["right"][key]
                                    if isinstance(widget, (QLineEdit, QLabel)):
                                        widget.setText(str(right_dict.get(key, 0 if key != "qual" else quality)))
            
            elif "spacing" in page_key.lower() and hasattr(page, 'spacing_inputs'):
                inputs = page.spacing_inputs
                for code, code_data in data_dict.items():
                    if code not in inputs:
                        continue
                    input_dict = inputs[code]
                    
                    if code in ["Fr", "Rs"]:
                        # Single value fields
                        if isinstance(code_data, dict):
                            if "upp" in input_dict:
                                widget = input_dict["upp"]
                                if isinstance(widget, QLineEdit):
                                    widget.setText(str(code_data.get("upp", 0)))
                            if "qual" in input_dict:
                                widget = input_dict["qual"]
                                if isinstance(widget, QLineEdit):
                                    widget.setText(str(code_data.get("qual", quality)))
                    else:
                        # Left/Right fields
                        if isinstance(code_data, dict) and "left" in code_data and "right" in code_data:
                            # Load left side
                            if "left" in input_dict:
                                left_dict = code_data["left"]
                                if "upp" in input_dict["left"]:
                                    widget = input_dict["left"]["upp"]
                                    if isinstance(widget, QLineEdit):
                                        widget.setText(str(left_dict.get("upp", 0)))
                                if "qual" in input_dict["left"]:
                                    widget = input_dict["left"]["qual"]
                                    if isinstance(widget, QLineEdit):
                                        widget.setText(str(left_dict.get("qual", quality)))
                            
                            # Load right side
                            if "right" in input_dict:
                                right_dict = code_data["right"]
                                if "upp" in input_dict["right"]:
                                    widget = input_dict["right"]["upp"]
                                    if isinstance(widget, QLineEdit):
                                        widget.setText(str(right_dict.get("upp", 0)))
                                if "qual" in input_dict["right"]:
                                    widget = input_dict["right"]["qual"]
                                    if isinstance(widget, QLineEdit):
                                        widget.setText(str(right_dict.get("qual", quality)))

    def calculate_tolerances(self, type_):
        """Set tolerance values based on quality level using predefined lookup tables"""
        try:
            logger.info(f"========== calculate_tolerances被调用 ==========")
            logger.info(f"type_={type_}")
            logger.info(f"self.current_page_id={self.current_page_id}")
            if type_ == "profile":
                # Get the current widget - try multiple sources
                current_widget = None
                
                # First try content_stack (normal dialog)
                if hasattr(self, 'content_stack'):
                    current_widget = self.content_stack.currentWidget()
                    logger.info(f"从content_stack获取current_widget: {current_widget}")
                
                # If not found, try to get from tolerance_dialog reference (simplified dialog)
                if not current_widget and hasattr(self, 'tolerance_dialog'):
                    tolerance_dialog = self.tolerance_dialog
                    if hasattr(tolerance_dialog, 'content_stack'):
                        current_widget = tolerance_dialog.content_stack.currentWidget()
                        logger.info(f"从tolerance_dialog.content_stack获取current_widget: {current_widget}")
                
                # If still not found, try to find widget with profile_inputs attribute
                if not current_widget:
                    # Try to find any widget that has profile_inputs
                    from PyQt5.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        # Try to find from all top-level widgets
                        for widget in app.allWidgets():
                            if hasattr(widget, 'profile_inputs') and widget.profile_inputs:
                                # Check if this widget is visible and contains the spinbox
                                if widget.isVisible():
                                    spin_boxes = widget.findChildren(QSpinBox)
                                    for spin_box in spin_boxes:
                                        if spin_box.minimum() == 1 and spin_box.maximum() == 12:
                                            current_widget = widget
                                            logger.info(f"从可见widget找到current_widget: {current_widget}")
                                            break
                                    if current_widget:
                                        break
                
                if not current_widget:
                    logger.warning("无法找到当前widget，尝试使用self作为widget")
                    current_widget = self
                
                # Get the correct quality spin box from current widget
                Q = 5  # Default value
                
                # First try to find spinbox in current_widget
                if current_widget:
                    spin_boxes = current_widget.findChildren(QSpinBox)
                    logger.info(f"在current_widget中找到{len(spin_boxes)}个spinbox")
                    for spin_box in spin_boxes:
                        # Check if this is the quality spin box (range 1-12)
                        if spin_box.minimum() == 1 and spin_box.maximum() == 12:
                            Q = spin_box.value()
                            logger.info(f"从current_widget找到精度等级spinbox，值为: {Q}")
                            break
                
                # If not found, try to find from all visible widgets (for simplified dialog)
                if Q == 5:
                    from PyQt5.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        # Find all visible spinboxes with range 1-12
                        logger.info("尝试从所有可见widget中查找spinbox")
                        for widget in app.allWidgets():
                            if widget.isVisible() and widget.isEnabled():
                                spin_boxes = widget.findChildren(QSpinBox)
                                for spin_box in spin_boxes:
                                    if spin_box.isVisible() and spin_box.minimum() == 1 and spin_box.maximum() == 12:
                                        Q = spin_box.value()
                                        logger.info(f"从可见widget找到精度等级spinbox，值为: {Q}, widget={widget}")
                                        # Update current_widget to this widget's parent (likely the content widget)
                                        if not current_widget or not hasattr(current_widget, 'profile_inputs'):
                                            parent = spin_box.parent()
                                            while parent:
                                                if hasattr(parent, 'profile_inputs') or hasattr(parent, 'tolerance_dialog'):
                                                    current_widget = parent
                                                    logger.info(f"更新current_widget为: {current_widget}")
                                                    break
                                                parent = parent.parent()
                                        break
                                if Q != 5:
                                    break
                
                # If still not found, try tolerance_dialog reference
                if Q == 5 and current_widget and hasattr(current_widget, 'tolerance_dialog'):
                    tolerance_dialog = current_widget.tolerance_dialog
                    if hasattr(tolerance_dialog, 'content_stack'):
                        stack_widget = tolerance_dialog.content_stack.currentWidget()
                        if stack_widget:
                            spin_boxes = stack_widget.findChildren(QSpinBox)
                            for spin_box in spin_boxes:
                                if spin_box.minimum() == 1 and spin_box.maximum() == 12:
                                    Q = spin_box.value()
                                    logger.info(f"从tolerance_dialog找到精度等级spinbox，值为: {Q}")
                                    break
                
                logger.info(f"最终确定的精度等级Q: {Q}")
                logger.info(f"当前页面ID: {self.current_page_id}")
                
                # Check if current page is AGMA_Profile or ISO 1328:1997_Profile
                # 如果current_page_id未设置，尝试从content_stack获取
                if not self.current_page_id and hasattr(self, 'content_stack'):
                    current_widget_in_stack = self.content_stack.currentWidget()
                    if current_widget_in_stack:
                        # 尝试从widget的属性中获取页面ID
                        if hasattr(current_widget_in_stack, 'page_id'):
                            self.current_page_id = current_widget_in_stack.page_id
                            logger.info(f"从current_widget获取页面ID: {self.current_page_id}")
                        # 或者通过检查widget的特征来判断
                        elif hasattr(current_widget_in_stack, 'findChild'):
                            # 检查是否有AGMA特有的元素
                            agma_spin = None
                            for widget in current_widget_in_stack.findChildren(QSpinBox):
                                if widget.minimum() == 1 and widget.maximum() == 12:
                                    agma_spin = widget
                                    break
                            # 如果找到spinbox，检查父窗口标题或其他特征
                            if agma_spin:
                                parent = agma_spin.parent()
                                while parent:
                                    if hasattr(parent, 'windowTitle'):
                                        title = parent.windowTitle()
                                        if 'AGMA' in title and 'Profile' in title:
                                            self.current_page_id = "AGMA_Profile"
                                            logger.info(f"通过窗口标题判断为AGMA_Profile")
                                            break
                                    parent = parent.parent()
                
                is_agma_profile = (self.current_page_id == "AGMA_Profile")
                is_iso1328_1997_profile = (self.current_page_id == "ISO 1328 : 1997_Profile")
                logger.info(f"is_agma_profile={is_agma_profile}, is_iso1328_1997_profile={is_iso1328_1997_profile}")
                
                # Fixed tolerance values for each quality level (from reference images)
                # Quality level: (fHa, ffa, Fa, Ca)
                # Ca (Crowning) values: None means not applicable for this quality level
                if is_agma_profile:
                    # AGMA Profile specific tolerance table (updated from image 1)
                    tolerance_table = {
                        1: (3.0, 4.0, 5.0, None),
                        2: (1.3, 1.6, 2.1, 2.5),  # Updated from image 1: fHa=1.3, ffa=1.6, Fa=2.1, Ca=2.5
                        3: (1.9, 2.3, 2.9, 2.5),  # Updated from image 1: fHa=1.9, ffa=2.3, Fa=2.9, Ca=2.5
                        4: (2.6, 3.2, 4.1, 2.5),  # Updated from image 1: fHa=2.6, ffa=3.2, Fa=4.1, Ca=2.5
                        5: (3.7, 4.5, 6.0, 2.5),  # Updated from image 1: fHa=3.7, ffa=4.5, Fa=6.0, Ca=2.5
                        6: (5.5, 6.5, 8.5, 2.5),  # Updated from image 1: fHa=5.5, ffa=6.5, Fa=8.5, Ca=2.5
                        7: (7.5, 9.0, 12.0, 2.5),  # Updated from image 1: fHa=7.5, ffa=9.0, Fa=12.0, Ca=2.5
                        8: (11.0, 13.0, 17.0, 2.5),  # Updated from image 1: fHa=11.0, ffa=13.0, Fa=17.0, Ca=2.5
                        9: (15.0, 18.0, 23.0, 2.5),  # Updated from image 1: fHa=15.0, ffa=18.0, Fa=23.0, Ca=2.5
                        10: (21.0, 26.0, 33.0, 2.5),  # Updated from image 1: fHa=21.0, ffa=26.0, Fa=33.0, Ca=2.5
                        11: (30.0, 36.0, 47.0, 2.5),  # Updated from image 1: fHa=30.0, ffa=36.0, Fa=47.0, Ca=2.5
                        12: (180.0, 250.0, 320.0, None)
                    }
                elif is_iso1328_1997_profile:
                    # ISO 1328:1997 Profile specific tolerance table (updated from image 1)
                    tolerance_table = {
                        1: (0.9, 1.1, 1.5, 0.0),  # Updated from image 1: fHa=0.9, ffa=1.1, Fa=1.5, Ca=0.0
                        2: (1.3, 1.6, 2.1, 0.0),  # Updated from image 1: fHa=1.3, ffa=1.6, Fa=2.1, Ca=0.0
                        3: (1.9, 2.3, 2.9, 0.0),  # Updated from image 1: fHa=1.9, ffa=2.3, Fa=2.9, Ca=0.0
                        4: (2.6, 3.2, 4.1, 0.0),  # Updated from image 1: fHa=2.6, ffa=3.2, Fa=4.1, Ca=0.0
                        5: (3.7, 4.5, 6.0, 0.0),  # Updated from image 1: fHa=3.7, ffa=4.5, Fa=6.0, Ca=0.0
                        6: (5.5, 6.5, 8.5, 0.0),  # Updated from image 1: fHa=5.5, ffa=6.5, Fa=8.5, Ca=0.0
                        7: (7.5, 9.0, 12.0, 0.0),  # Updated from image 1: fHa=7.5, ffa=9.0, Fa=12.0, Ca=0.0
                        8: (11.0, 13.0, 17.0, 0.0),  # Updated from image 1: fHa=11.0, ffa=13.0, Fa=17.0, Ca=0.0
                        9: (15.0, 18.0, 23.0, 0.0),  # Updated from image 1: fHa=15.0, ffa=18.0, Fa=23.0, Ca=0.0
                        10: (21.0, 26.0, 33.0, 0.0),  # Updated from image 1: fHa=21.0, ffa=26.0, Fa=33.0, Ca=0.0
                        11: (30.0, 36.0, 47.0, 0.0),  # Updated from image 1: fHa=30.0, ffa=36.0, Fa=47.0, Ca=0.0
                        12: (42.0, 51.0, 66.0, 0.0)  # Updated from image 1: fHa=42.0, ffa=51.0, Fa=66.0, Ca=0.0
                    }
                else:
                    # Other standards (DIN, ANSI, ISO 1328:2013) use original tolerance table
                    tolerance_table = {
                        1: (3.0, 4.0, 5.0, None),
                        2: (4.0, 6.0, 7.0, None),  # Original values for other standards
                        3: (5.5, 8.0, 10.0, None),
                        4: (8.0, 12.0, 14.0, None),
                        5: (11.0, 16.0, 20.0, None),
                        6: (16.0, 22.0, 28.0, None),
                        7: (22.0, 32.0, 40.0, None),
                        8: (28.0, 45.0, 56.0, None),
                        9: (40.0, 63.0, 80.0, None),
                        10: (71.0, 110.0, 125.0, None),
                        11: (110.0, 160.0, 200.0, None),
                        12: (180.0, 250.0, 320.0, None)
                    }
                
                # Get tolerance values for the selected quality level
                if Q in tolerance_table:
                    values = tolerance_table[Q]
                    fHa = values[0]
                    ffa = values[1]
                    Fa = values[2]
                    Ca = values[3] if len(values) > 3 else None
                else:
                    # Default to quality level 5 if out of range
                    values = tolerance_table[5]
                    fHa = values[0]
                    ffa = values[1]
                    Fa = values[2]
                    Ca = values[3] if len(values) > 3 else None
                
                # Get profile_inputs from current widget or use self.profile_inputs
                profile_inputs = None
                
                # 尝试从当前可见的widget中直接构建profile_inputs
                # 这样确保我们更新的是实际显示的字段，而不是隐藏的字段
                if current_widget:
                    logger.info("尝试从current_widget中直接构建profile_inputs")
                    # 查找所有QLineEdit，按行组织
                    all_line_edits = current_widget.findChildren(QLineEdit)
                    logger.info(f"在current_widget中找到{len(all_line_edits)}个QLineEdit")
                    
                    # 如果找到了很多QLineEdit，尝试直接更新它们
                    if len(all_line_edits) >= 20:  # Profile页面应该有很多输入字段
                        logger.info("找到足够的QLineEdit，尝试直接构建profile_inputs")
                        # 重新构建profile_inputs字典
                        temp_profile_inputs = {}
                        
                        # 查找所有checkbox来识别字段
                        all_checkboxes = current_widget.findChildren(QCheckBox)
                        for chk in all_checkboxes:
                            text = chk.text()
                            # 解析 "Angular error   fHa" 格式
                            if '   ' in text:
                                parts = text.split('   ')
                                if len(parts) == 2:
                                    code = parts[1].strip()
                                    temp_profile_inputs[f"{code}_check"] = chk
                        
                        # 查找该checkbox所在行的所有QLineEdit
                        # 这个方法比较复杂，让我们使用另一种方式：
                        # 直接从temp_dialog的profile_inputs获取结构，但替换widget引用为可见的widget
                        
                profile_inputs = None
                
                # First try from current_widget
                if current_widget and hasattr(current_widget, 'profile_inputs') and current_widget.profile_inputs:
                    profile_inputs = current_widget.profile_inputs
                    logger.info(f"从current_widget获取profile_inputs: {len(profile_inputs) if profile_inputs else 0}个参数")
                
                # If still not found, try to get from tolerance_dialog reference
                if not profile_inputs and current_widget and hasattr(current_widget, 'tolerance_dialog'):
                    tolerance_dialog = current_widget.tolerance_dialog
                    if hasattr(tolerance_dialog, 'profile_inputs') and tolerance_dialog.profile_inputs:
                        profile_inputs = tolerance_dialog.profile_inputs
                        logger.info(f"从tolerance_dialog引用获取profile_inputs: {len(profile_inputs) if profile_inputs else 0}个参数")
                        
                        # 验证这些字段是否可见
                        if profile_inputs and 'fHa' in profile_inputs:
                            test_widget = profile_inputs['fHa']['left']['upp']
                            if test_widget and hasattr(test_widget, 'isVisible'):
                                logger.info(f"fHa left upp字段可见性: {test_widget.isVisible()}")
                                if not test_widget.isVisible():
                                    logger.warning("profile_inputs中的字段不可见，可能需要在current_widget中重新查找")
                
                # If still not found, try from self
                if not profile_inputs and hasattr(self, 'profile_inputs') and self.profile_inputs:
                    profile_inputs = self.profile_inputs
                    logger.info(f"从self获取profile_inputs: {len(profile_inputs) if profile_inputs else 0}个参数")
                
                # If still not found, try to find it in the widget hierarchy
                if not profile_inputs and current_widget:
                    # Try to find profile_inputs in parent widgets
                    parent = current_widget.parent()
                    while parent:
                        if hasattr(parent, 'profile_inputs') and parent.profile_inputs:
                            profile_inputs = parent.profile_inputs
                            logger.info(f"从parent widget获取profile_inputs: {len(profile_inputs) if profile_inputs else 0}个参数")
                            break
                        parent = parent.parent()
                
                # If still not found, try to find from all visible widgets
                if not profile_inputs:
                    from PyQt5.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        logger.info("尝试从所有可见widget中查找profile_inputs")
                        for widget in app.allWidgets():
                            if widget.isVisible() and hasattr(widget, 'profile_inputs') and widget.profile_inputs:
                                profile_inputs = widget.profile_inputs
                                logger.info(f"从可见widget获取profile_inputs: {len(profile_inputs) if profile_inputs else 0}个参数, widget={widget}")
                                # 同时更新current_widget
                                if not current_widget or not hasattr(current_widget, 'profile_inputs'):
                                    current_widget = widget
                                break
                
                if not profile_inputs:
                    logger.warning("无法找到profile_inputs，无法更新公差值")
                    # 尝试最后一种方法：直接从temp_dialog获取（如果存在）
                    if hasattr(self, 'tolerance_dialog'):
                        temp_dialog = self.tolerance_dialog
                        if hasattr(temp_dialog, 'profile_inputs') and temp_dialog.profile_inputs:
                            profile_inputs = temp_dialog.profile_inputs
                            logger.info(f"从tolerance_dialog获取profile_inputs: {len(profile_inputs) if profile_inputs else 0}个参数")
                
                if not profile_inputs:
                    logger.error("最终无法找到profile_inputs，无法更新公差值")
                    QMessageBox.warning(self, "错误", "无法找到公差输入字段，请检查对话框是否正确初始化")
                    return
                
                # If we have profile_inputs, use it to update
                if profile_inputs:
                    logger.info(f"开始更新公差值: Q={Q}, fHa={fHa}, ffa={ffa}, Fa={Fa}, Ca={Ca}")
                    logger.info(f"profile_inputs包含的参数: {list(profile_inputs.keys())}")
                    
                    # 验证字段可见性
                    if 'fHa' in profile_inputs and 'left' in profile_inputs['fHa'] and 'upp' in profile_inputs['fHa']['left']:
                        test_field = profile_inputs['fHa']['left']['upp']
                        is_visible = test_field.isVisible() if hasattr(test_field, 'isVisible') else False
                        is_enabled = test_field.isEnabled() if hasattr(test_field, 'isEnabled') else False
                        parent_widget = test_field.parent() if hasattr(test_field, 'parent') else None
                        logger.info(f"测试字段(fHa left upp)可见性: {is_visible}, 启用状态: {is_enabled}, 父widget: {parent_widget}")
                    
                    for side in ['left', 'right']:
                        # Update all quality fields to show the selected quality level
                        for code in profile_inputs:
                            if "_check" not in code and side in profile_inputs[code]:
                                if 'qual' in profile_inputs[code][side]:
                                    qual_field = profile_inputs[code][side]['qual']
                                    if isinstance(qual_field, QLineEdit):
                                        old_value = qual_field.text()
                                        qual_field.setText(str(Q))
                                        qual_field.repaint()  # 强制刷新
                                        logger.info(f"更新{code} {side} Quality字段: {old_value} -> {Q}")
                        
                        # Update tolerance values with fixed values from lookup table
                        if 'fHa' in profile_inputs and side in profile_inputs['fHa']:
                            if 'upp' in profile_inputs['fHa'][side]:
                                old_value = profile_inputs['fHa'][side]['upp'].text()
                                profile_inputs['fHa'][side]['upp'].setText(f"{fHa:.1f}")
                                profile_inputs['fHa'][side]['upp'].repaint()  # 强制刷新
                                logger.info(f"更新fHa {side} upp: {old_value} -> {fHa:.1f}")
                            if 'low' in profile_inputs['fHa'][side]:
                                old_value = profile_inputs['fHa'][side]['low'].text()
                                profile_inputs['fHa'][side]['low'].setText(f"{-fHa:.1f}")
                                profile_inputs['fHa'][side]['low'].repaint()  # 强制刷新
                                logger.info(f"更新fHa {side} low: {old_value} -> {-fHa:.1f}")
                        
                        if 'ffa' in profile_inputs and side in profile_inputs['ffa']:
                            if 'upp' in profile_inputs['ffa'][side]:
                                old_value = profile_inputs['ffa'][side]['upp'].text()
                                profile_inputs['ffa'][side]['upp'].setText(f"{ffa:.1f}")
                                profile_inputs['ffa'][side]['upp'].repaint()  # 强制刷新
                                logger.info(f"更新ffa {side} upp: {old_value} -> {ffa:.1f}")
                        
                        if 'Fa' in profile_inputs and side in profile_inputs['Fa']:
                            if 'upp' in profile_inputs['Fa'][side]:
                                old_value = profile_inputs['Fa'][side]['upp'].text()
                                profile_inputs['Fa'][side]['upp'].setText(f"{Fa:.1f}")
                                profile_inputs['Fa'][side]['upp'].repaint()  # 强制刷新
                                logger.info(f"更新Fa {side} upp: {old_value} -> {Fa:.1f}")
                        
                        # Var doesn't have quality field in the visible columns, set to 0.0
                        if 'Var' in profile_inputs and side in profile_inputs['Var']:
                            if 'upp' in profile_inputs['Var'][side]:
                                profile_inputs['Var'][side]['upp'].setText("0.0")
                        
                        # Update Crowning (Ca) if applicable for this quality level
                        # Only update once (for left side), then break
                        if side == 'left':
                            if Ca is not None and 'Ca' in profile_inputs:
                                # Set checkbox to checked (Ca can be 0.0 for ISO 1328:1997)
                                if 'Ca_check' in profile_inputs:
                                    profile_inputs['Ca_check'].setChecked(True)
                                # Update both left and right sides
                                for update_side in ['left', 'right']:
                                    if update_side in profile_inputs['Ca']:
                                        if 'upp' in profile_inputs['Ca'][update_side]:
                                            profile_inputs['Ca'][update_side]['upp'].setText(f"{Ca:.1f}")
                                        if 'low' in profile_inputs['Ca'][update_side]:
                                            profile_inputs['Ca'][update_side]['low'].setText(f"{-Ca:.1f}")
                                        # Keep Nom. val at 0.0
                                        if 'nom' in profile_inputs['Ca'][update_side]:
                                            if isinstance(profile_inputs['Ca'][update_side]['nom'], QLineEdit):
                                                profile_inputs['Ca'][update_side]['nom'].setText("0.0")
                                            elif isinstance(profile_inputs['Ca'][update_side]['nom'], QLabel):
                                                profile_inputs['Ca'][update_side]['nom'].setText("0.0")
                            elif 'Ca_check' in profile_inputs:
                                # For other quality levels, keep checkbox unchecked (default state)
                                profile_inputs['Ca_check'].setChecked(False)
                    
                    # 强制更新整个widget
                    if current_widget:
                        current_widget.update()
                        current_widget.repaint()
                    
                    logger.info("公差值更新完成")
                else:
                    logger.error("profile_inputs为空，无法更新")

            elif type_ == "lead":
                # Get the current widget
                current_widget = self.content_stack.currentWidget()
                if not current_widget:
                    return
                
                # Get the correct quality spin box from current widget
                Q = 5  # Default value
                spin_boxes = current_widget.findChildren(QSpinBox)
                for spin_box in spin_boxes:
                    # Check if this is the quality spin box (range 1-12)
                    if spin_box.minimum() == 1 and spin_box.maximum() == 12:
                        Q = spin_box.value()
                        break
                
                # Check if current page is AGMA_Lead
                is_agma_lead = (self.current_page_id == "AGMA_Lead / Line of action")
                
                # Fixed tolerance values for Lead (fHb, ffb, Fb, Cb)
                # Quality level: (fHb, ffb, Fb, Cb)
                # Cb (Crowning) values: None means not applicable for this quality level
                if is_agma_lead:
                    # AGMA Lead specific tolerance table (updated from image 1)
                    lead_tolerance_table = {
                        1: (2.5, 2.0, 3.0, None),
                        2: (1.7, 1.7, 2.4, 2.5),  # Updated from image 1: fHb=1.7, ffb=1.7, Fb=2.4, Cb=2.5
                        3: (2.4, 2.4, 3.3, 2.5),  # Updated from image 1: fHb=2.4, ffb=2.4, Fb=3.3, Cb=2.5
                        4: (3.4, 3.4, 4.7, 2.5),  # Updated from image 1: fHb=3.4, ffb=3.4, Fb=4.7, Cb=2.5
                        5: (4.8, 4.8, 6.5, 2.5),  # Updated from image 1: fHb=4.8, ffb=4.8, Fb=6.5, Cb=2.5
                        6: (6.5, 6.5, 9.5, 2.5),  # Updated from image 1: fHb=6.5, ffb=6.5, Fb=9.5, Cb=2.5
                        7: (9.5, 9.5, 13.0, 2.5),  # Updated from image 1: fHb=9.5, ffb=9.5, Fb=13.0, Cb=2.5
                        8: (13.0, 13.0, 19.0, 2.5),  # Updated from image 1: fHb=13.0, ffb=13.0, Fb=19.0, Cb=2.5
                        9: (19.0, 19.0, 27.0, 2.5),  # Updated from image 1: fHb=19.0, ffb=19.0, Fb=27.0, Cb=2.5
                        10: (27.0, 27.0, 38.0, 2.5),  # Updated from image 1: fHb=27.0, ffb=27.0, Fb=38.0, Cb=2.5
                        11: (38.0, 38.0, 53.0, 2.5),  # Updated from image 1: fHb=38.0, ffb=38.0, Fb=53.0, Cb=2.5
                        12: (125.0, 160.0, 200.0, None)
                    }
                else:
                    # Other standards (ISO, DIN, ANSI) use original tolerance table
                    lead_tolerance_table = {
                        1: (2.5, 2.0, 3.0, None),
                        2: (3.5, 5.0, 6.0, None),  # Original values for other standards
                        3: (4.5, 7.0, 8.0, None),
                        4: (6.0, 8.0, 10.0, None),
                        5: (8.0, 9.0, 12.0, None),
                        6: (11.0, 12.0, 16.0, None),
                        7: (16.0, 16.0, 22.0, None),
                        8: (22.0, 25.0, 32.0, None),
                        9: (32.0, 40.0, 50.0, None),
                        10: (50.0, 63.0, 80.0, None),
                        11: (80.0, 100.0, 125.0, None),
                        12: (125.0, 160.0, 200.0, None)
                    }
                
                if Q in lead_tolerance_table:
                    values = lead_tolerance_table[Q]
                    fHb = values[0]
                    ffb = values[1]
                    Fb = values[2]
                    Cb = values[3] if len(values) > 3 else None
                else:
                    # Fallback to calculation for other levels
                    width = float(self.gear_data.get('width', 0) or 0)
                    factor = 2 ** (0.5 * (Q - 5))
                    
                    # Approximations
                    if width > 0:
                        fHb = (0.3 * width**0.5 + 4.0) * factor 
                    else:
                        fHb = 10.0 * factor
    
                    ffb = fHb * 0.8
                    Fb = fHb * 1.2
                
                # Get lead_inputs from current widget or use self.lead_inputs
                lead_inputs = None
                if hasattr(current_widget, 'lead_inputs'):
                    lead_inputs = current_widget.lead_inputs
                elif hasattr(self, 'lead_inputs') and self.lead_inputs:
                    lead_inputs = self.lead_inputs
                
                # If still not found, try to get from tolerance_dialog reference
                if not lead_inputs and hasattr(current_widget, 'tolerance_dialog'):
                    tolerance_dialog = current_widget.tolerance_dialog
                    if hasattr(tolerance_dialog, 'lead_inputs') and tolerance_dialog.lead_inputs:
                        lead_inputs = tolerance_dialog.lead_inputs
                
                if lead_inputs:
                    for side in ['left', 'right']:
                        # Update ALL quality fields
                        for code in lead_inputs:
                            if "_check" not in code and side in lead_inputs[code]:
                                if 'qual' in lead_inputs[code][side]:
                                    qual_field = lead_inputs[code][side]['qual']
                                    if isinstance(qual_field, QLineEdit):
                                        qual_field.setText(str(Q))

                        # Update calculated tolerances
                        if 'fHb' in lead_inputs and side in lead_inputs['fHb']:
                            if 'upp' in lead_inputs['fHb'][side]:
                                lead_inputs['fHb'][side]['upp'].setText(f"{fHb:.1f}")
                            if 'low' in lead_inputs['fHb'][side]:
                                lead_inputs['fHb'][side]['low'].setText(f"{-fHb:.1f}")
                        
                        if 'ffb' in lead_inputs and side in lead_inputs['ffb']:
                            if 'upp' in lead_inputs['ffb'][side]:
                                lead_inputs['ffb'][side]['upp'].setText(f"{ffb:.1f}")
                        
                        if 'Fb' in lead_inputs and side in lead_inputs['Fb']:
                            if 'upp' in lead_inputs['Fb'][side]:
                                lead_inputs['Fb'][side]['upp'].setText(f"{Fb:.1f}")
                        
                        # Update Crowning (Cb) if applicable for this quality level
                        # Only update once (for left side), then break
                        if side == 'left':
                            if Cb is not None and 'Cb' in lead_inputs:
                                # Set checkbox to checked for quality level 2
                                if 'Cb_check' in lead_inputs:
                                    lead_inputs['Cb_check'].setChecked(True)
                                # Update both left and right sides
                                for update_side in ['left', 'right']:
                                    if update_side in lead_inputs['Cb']:
                                        if 'upp' in lead_inputs['Cb'][update_side]:
                                            lead_inputs['Cb'][update_side]['upp'].setText(f"{Cb:.1f}")
                                        if 'low' in lead_inputs['Cb'][update_side]:
                                            lead_inputs['Cb'][update_side]['low'].setText(f"{-Cb:.1f}")
                                        # Set Nom. val to 2.5 for AGMA Lead (from image 1)
                                        if 'nom' in lead_inputs['Cb'][update_side]:
                                            if isinstance(lead_inputs['Cb'][update_side]['nom'], QLineEdit):
                                                lead_inputs['Cb'][update_side]['nom'].setText("2.5")
                                            elif isinstance(lead_inputs['Cb'][update_side]['nom'], QLabel):
                                                lead_inputs['Cb'][update_side]['nom'].setText("2.5")
                            elif 'Cb_check' in lead_inputs:
                                # For other quality levels, keep checkbox unchecked (default state)
                                lead_inputs['Cb_check'].setChecked(False)

            elif type_ == "spacing":
                # Get the current widget
                current_widget = self.content_stack.currentWidget()
                if not current_widget:
                    return
                
                # Get the correct quality spin box from current widget
                Q = 5  # Default value
                spin_boxes = current_widget.findChildren(QSpinBox)
                for spin_box in spin_boxes:
                    # Check if this is the quality spin box (range 1-12)
                    if spin_box.minimum() == 1 and spin_box.maximum() == 12:
                        Q = spin_box.value()
                        break
                
                # Check if current page is AGMA_Spacing
                is_agma_spacing = (self.current_page_id == "AGMA_Spacing")
                
                # Tolerance values from user images for Q=1 to Q=12
                # Format: (fp, fu, Fp, Fpz/8, Fr, Rs)
                if is_agma_spacing:
                    # AGMA Spacing specific tolerance table (updated from image 1)
                    spacing_lookup = {
                        1: (1.4, 0.0, 5.5, 2.4, 3.7, 4.5),  # Updated from image 1: fp=1.4, fu=0.0, Fp=5.5, Fpz/8=2.4, Fr=3.7
                        2: (2.0, 0.0, 8.0, 3.4, 5.0, 7.0),  # Updated from image 1: fp=2.0, fu=0.0, Fp=8.0, Fpz/8=3.4, Fr=5.0
                        3: (2.9, 0.0, 11.0, 4.8, 7.5, 9.0),  # Updated from image 1: fp=2.9, fu=0.0, Fp=11.0, Fpz/8=4.8, Fr=7.5
                        4: (4.1, 0.0, 16.0, 7.0, 10.0, 12.0),  # Updated from image 1: fp=4.1, fu=0.0, Fp=16.0, Fpz/8=7.0, Fr=10.0
                        5: (5.5, 0.0, 23.0, 9.5, 15.0, 18.0),  # Updated from image 1: fp=5.5, fu=0.0, Fp=23.0, Fpz/8=9.5, Fr=15.0
                        6: (8.0, 0.0, 32.0, 14.0, 21.0, 25.0),  # Updated from image 1: fp=8.0, fu=0.0, Fp=32.0, Fpz/8=14.0, Fr=21.0
                        7: (11.0, 0.0, 45.0, 19.0, 29.0, 36.0),  # Updated from image 1: fp=11.0, fu=0.0, Fp=45.0, Fpz/8=19.0, Fr=29.0
                        8: (16.0, 0.0, 64.0, 27.0, 42.0, 50.0),  # Updated from image 1: fp=16.0, fu=0.0, Fp=64.0, Fpz/8=27.0, Fr=42.0
                        9: (23.0, 0.0, 91.0, 38.0, 59.0, 71.0),  # Updated from image 1: fp=23.0, fu=0.0, Fp=91.0, Fpz/8=38.0, Fr=59.0
                        10: (32.0, 0.0, 128.0, 54.0, 83.0, 100.0),  # Updated from image 1: fp=32.0, fu=0.0, Fp=128.0, Fpz/8=54.0, Fr=83.0
                        11: (46.0, 0.0, 181.0, 77.0, 118.0, 140.0),  # Updated from image 1: fp=46.0, fu=0.0, Fp=181.0, Fpz/8=77.0, Fr=118.0
                        12: (65.0, 0.0, 257.0, 109.0, 167.0, 180.0)  # Updated from image 1: fp=65.0, fu=0.0, Fp=257.0, Fpz/8=109.0, Fr=167.0
                    }
                else:
                    # Other standards (ISO, DIN, ANSI) use original tolerance table
                    spacing_lookup = {
                        1: (3.0, 4.0, 9.0, 6.0, 7.0, 4.5),  # Original values for other standards
                        2: (4.5, 5.5, 14.0, 8.0, 10.0, 7.0),
                        3: (6.0, 8.0, 18.0, 11.0, 14.0, 9.0),
                        4: (8.0, 10.0, 25.0, 16.0, 20.0, 12.0),
                        5: (12.0, 16.0, 36.0, 22.0, 28.0, 18.0),
                        6: (16.0, 20.0, 45.0, 32.0, 40.0, 25.0),
                        7: (22.0, 28.0, 71.0, 40.0, 56.0, 36.0),
                        8: (32.0, 40.0, 90.0, 63.0, 80.0, 50.0),
                        9: (45.0, 56.0, 125.0, 80.0, 110.0, 71.0),
                        10: (71.0, 90.0, 200.0, 140.0, 160.0, 100.0),
                        11: (110.0, 140.0, 320.0, 220.0, 220.0, 140.0),
                        12: (180.0, 220.0, 560.0, 320.0, 320.0, 180.0)
                    }
                
                if Q in spacing_lookup:
                    fp, fu, Fp, Fpz8, Fr, Rs = spacing_lookup[Q]
                else:
                    # For Q > 12, extrapolate from Q=12 values using ISO factor
                    # factor = 2^(0.5 * (Q - 12))
                    base_values = spacing_lookup[12]
                    factor = 2 ** (0.5 * (Q - 12))
                    
                    fp = base_values[0] * factor
                    fu = base_values[1] * factor
                    Fp = base_values[2] * factor
                    Fpz8 = base_values[3] * factor
                    Fr = base_values[4] * factor
                    Rs = base_values[5] * factor
                
                # Get spacing_inputs from current widget or use self.spacing_inputs
                spacing_inputs = None
                if hasattr(current_widget, 'spacing_inputs'):
                    spacing_inputs = current_widget.spacing_inputs
                elif hasattr(self, 'spacing_inputs') and self.spacing_inputs:
                    spacing_inputs = self.spacing_inputs
                
                # If still not found, try to get from tolerance_dialog reference
                if not spacing_inputs and hasattr(current_widget, 'tolerance_dialog'):
                    tolerance_dialog = current_widget.tolerance_dialog
                    if hasattr(tolerance_dialog, 'spacing_inputs') and tolerance_dialog.spacing_inputs:
                        spacing_inputs = tolerance_dialog.spacing_inputs
                
                if spacing_inputs:
                    # Update Spacing Group (Left/Right)
                    for side in ['left', 'right']:
                        # Update Quality fields
                        for code in ['fp', 'fu', 'Fp', 'Fpz/8']:
                            if code in spacing_inputs and side in spacing_inputs[code]:
                                if 'qual' in spacing_inputs[code][side]:
                                    qual_field = spacing_inputs[code][side]['qual']
                                    if isinstance(qual_field, QLineEdit):
                                        qual_field.setText(str(Q))
                        
                        # Update Values
                        if 'fp' in spacing_inputs and side in spacing_inputs['fp']:
                            if 'upp' in spacing_inputs['fp'][side]:
                                spacing_inputs['fp'][side]['upp'].setText(f"{fp:.1f}")
                        if 'fu' in spacing_inputs and side in spacing_inputs['fu']:
                            if 'upp' in spacing_inputs['fu'][side]:
                                spacing_inputs['fu'][side]['upp'].setText(f"{fu:.1f}")
                        if 'Fp' in spacing_inputs and side in spacing_inputs['Fp']:
                            if 'upp' in spacing_inputs['Fp'][side]:
                                spacing_inputs['Fp'][side]['upp'].setText(f"{Fp:.1f}")
                        if 'Fpz/8' in spacing_inputs and side in spacing_inputs['Fpz/8']:
                            if 'upp' in spacing_inputs['Fpz/8'][side]:
                                spacing_inputs['Fpz/8'][side]['upp'].setText(f"{Fpz8:.1f}")
                    
                    # Update Run-out Group (Single)
                    # Fr
                    if 'Fr' in spacing_inputs:
                        if 'qual' in spacing_inputs['Fr']:
                            qual_field = spacing_inputs['Fr']['qual']
                            if isinstance(qual_field, QLineEdit):
                                qual_field.setText(str(Q))
                        if 'upp' in spacing_inputs['Fr']:
                            spacing_inputs['Fr']['upp'].setText(f"{Fr:.1f}")
                        
                    # Rs
                    if 'Rs' in spacing_inputs:
                        if 'qual' in spacing_inputs['Rs']:
                            qual_field = spacing_inputs['Rs']['qual']
                            if isinstance(qual_field, QLineEdit):
                                qual_field.setText(str(Q))
                        if 'upp' in spacing_inputs['Rs']:
                            spacing_inputs['Rs']['upp'].setText(f"{Rs:.1f}")
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Calculation failed: {e}")

    def toggle_header_mode(self, side, mode):
        """
        Toggle header buttons state and enable/disable corresponding fields.
        side: "left" or "right"
        mode: "limits" (Lim. upp./low.) or "quality" (Quality)
        
        When limits mode: enable limit fields, disable quality fields (gray them out)
        When quality mode: enable quality fields, disable limit fields (gray them out)
        """
        # Update button states
        if side == "left":
            if mode == "limits":
                self.btn_lim_upp_l.setChecked(True)
                self.btn_lim_low_l.setChecked(True)
                self.btn_qual_l.setChecked(False)
            else:
                self.btn_lim_upp_l.setChecked(False)
                self.btn_lim_low_l.setChecked(False)
                self.btn_qual_l.setChecked(True)
        else: # right
            if mode == "limits":
                self.btn_lim_upp_r.setChecked(True)
                self.btn_lim_low_r.setChecked(True)
                self.btn_qual_r.setChecked(False)
            else:
                self.btn_lim_upp_r.setChecked(False)
                self.btn_lim_low_r.setChecked(False)
                self.btn_qual_r.setChecked(True)
        
        # Update field states for profile inputs
        if hasattr(self, 'profile_inputs'):
            for code, inputs in self.profile_inputs.items():
                if "_check" in code:
                    continue
                
                if side not in inputs:
                    continue
                
                side_inputs = inputs[side]
                
                if mode == "limits":
                    # Enable limit fields, disable quality fields
                    for field_name in ['upp', 'low']:
                        if field_name in side_inputs:
                            field = side_inputs[field_name]
                            if isinstance(field, QLineEdit):
                                field.setEnabled(True)
                                field.setStyleSheet("")
                    
                    if 'qual' in side_inputs:
                        qual_field = side_inputs['qual']
                        if isinstance(qual_field, QLineEdit):
                            qual_field.setEnabled(False)
                            qual_field.setStyleSheet("background-color: #e0e0e0; color: #808080;")
                else:  # quality mode
                    # Disable limit fields, enable quality fields
                    for field_name in ['upp', 'low']:
                        if field_name in side_inputs:
                            field = side_inputs[field_name]
                            if isinstance(field, QLineEdit):
                                field.setEnabled(False)
                                field.setStyleSheet("background-color: #e0e0e0; color: #808080;")
                    
                    if 'qual' in side_inputs:
                        qual_field = side_inputs['qual']
                        if isinstance(qual_field, QLineEdit):
                            qual_field.setEnabled(True)
                            qual_field.setStyleSheet("")

    def toggle_lead_header_mode(self, side, mode):
        """
        Toggle header buttons state and enable/disable corresponding fields for LEAD page.
        side: "left" or "right"
        mode: "limits" (Lim. upp./low.) or "quality" (Quality)
        """
        # Update button states
        if side == "left":
            if mode == "limits":
                self.lead_btn_lim_upp_l.setChecked(True)
                self.lead_btn_lim_low_l.setChecked(True)
                self.lead_btn_qual_l.setChecked(False)
            else:
                self.lead_btn_lim_upp_l.setChecked(False)
                self.lead_btn_lim_low_l.setChecked(False)
                self.lead_btn_qual_l.setChecked(True)
        else: # right
            if mode == "limits":
                self.lead_btn_lim_upp_r.setChecked(True)
                self.lead_btn_lim_low_r.setChecked(True)
                self.lead_btn_qual_r.setChecked(False)
            else:
                self.lead_btn_lim_upp_r.setChecked(False)
                self.lead_btn_lim_low_r.setChecked(False)
                self.lead_btn_qual_r.setChecked(True)
        
        # Update field states for lead inputs
        if hasattr(self, 'lead_inputs'):
            for code, inputs in self.lead_inputs.items():
                if "_check" in code:
                    continue
                
                if side not in inputs:
                    continue
                
                side_inputs = inputs[side]
                
                if mode == "limits":
                    # Enable limit fields, disable quality fields
                    for field_name in ['upp', 'low']:
                        if field_name in side_inputs:
                            field = side_inputs[field_name]
                            if isinstance(field, QLineEdit):
                                field.setEnabled(True)
                                field.setStyleSheet("")
                    
                    if 'qual' in side_inputs:
                        qual_field = side_inputs['qual']
                        if isinstance(qual_field, QLineEdit):
                            qual_field.setEnabled(False)
                            qual_field.setStyleSheet("background-color: #e0e0e0; color: #808080;")
                else:  # quality mode
                    # Disable limit fields, enable quality fields
                    for field_name in ['upp', 'low']:
                        if field_name in side_inputs:
                            field = side_inputs[field_name]
                            if isinstance(field, QLineEdit):
                                field.setEnabled(False)
                                field.setStyleSheet("background-color: #e0e0e0; color: #808080;")
                    
                    if 'qual' in side_inputs:
                        qual_field = side_inputs['qual']
                        if isinstance(qual_field, QLineEdit):
                            qual_field.setEnabled(True)
                            qual_field.setStyleSheet("")

    def toggle_spacing_header_mode(self, side, mode):
        """
        Toggle header buttons state and enable/disable corresponding fields for SPACING page.
        side: "left", "right", or "runout"
        mode: "limits" (Lim. upp.) or "quality" (Quality)
        """
        # Update button states
        if side == "left":
            if mode == "limits":
                self.spacing_btn_lim_l.setChecked(True)
                self.spacing_btn_qual_l.setChecked(False)
            else:
                self.spacing_btn_lim_l.setChecked(False)
                self.spacing_btn_qual_l.setChecked(True)
        elif side == "right":
            if mode == "limits":
                self.spacing_btn_lim_r.setChecked(True)
                self.spacing_btn_qual_r.setChecked(False)
            else:
                self.spacing_btn_lim_r.setChecked(False)
                self.spacing_btn_qual_r.setChecked(True)
        elif side == "runout":
            if mode == "limits":
                self.runout_btn_lim.setChecked(True)
                self.runout_btn_qual.setChecked(False)
            else:
                self.runout_btn_lim.setChecked(False)
                self.runout_btn_qual.setChecked(True)
        
        # Update field states
        if hasattr(self, 'spacing_inputs'):
            for code, inputs in self.spacing_inputs.items():
                if "_check" in code: continue
                
                # Determine which inputs to update
                target_inputs = None
                
                if side in ["left", "right"]:
                    # Spacing items have left/right structure
                    if side in inputs:
                        target_inputs = inputs[side]
                elif side == "runout":
                    # Runout items are flat structure (no left/right keys)
                    # But we need to distinguish runout items from spacing items
                    # Spacing items have 'left'/'right' keys. Runout items have 'upp'/'qual' directly.
                    if "left" not in inputs and "right" not in inputs:
                        target_inputs = inputs
                
                if target_inputs:
                    if mode == "limits":
                        # Enable limit fields, disable quality fields
                        if 'upp' in target_inputs:
                            field = target_inputs['upp']
                            if isinstance(field, QLineEdit):
                                field.setEnabled(True)
                                field.setStyleSheet("")
                        
                        if 'qual' in target_inputs:
                            field = target_inputs['qual']
                            if isinstance(field, QLineEdit):
                                field.setEnabled(False)
                                field.setStyleSheet("background-color: #e0e0e0; color: #808080;")
                    else: # quality mode
                        # Disable limit fields, enable quality fields
                        if 'upp' in target_inputs:
                            field = target_inputs['upp']
                            if isinstance(field, QLineEdit):
                                field.setEnabled(False)
                                field.setStyleSheet("background-color: #e0e0e0; color: #808080;")
                        
                        if 'qual' in target_inputs:
                            field = target_inputs['qual']
                            if isinstance(field, QLineEdit):
                                field.setEnabled(True)
                                field.setStyleSheet("")

    def copy_tolerances(self, direction, type_):
        """
        Copy tolerance values between left and right sides.
        direction: "left_to_right" or "right_to_left"
        type_: "profile", "lead", "spacing"
        """
        try:
            inputs_map = {}
            if type_ == "profile":
                inputs_map = self.profile_inputs
            elif type_ == "lead":
                inputs_map = self.lead_inputs
            elif type_ == "spacing":
                inputs_map = self.spacing_inputs
            
            for code, inputs in inputs_map.items():
                if "_check" in code: continue
                
                # Skip if not structured as left/right (e.g. some spacing items)
                if "left" not in inputs or "right" not in inputs:
                    continue
                    
                src = inputs["left"] if direction == "left_to_right" else inputs["right"]
                dst = inputs["right"] if direction == "left_to_right" else inputs["left"]
                
                # Copy values if widgets exist and are visible
                if "nom" in src and "nom" in dst and src["nom"].isVisible() and dst["nom"].isVisible():
                    # nom is now a QLabel, use setText for both
                    dst["nom"].setText(src["nom"].text())
                    
                if "upp" in src and "upp" in dst and src["upp"].isVisible() and dst["upp"].isVisible():
                    dst["upp"].setText(src["upp"].text())
                    
                if "low" in src and "low" in dst and src["low"].isVisible() and dst["low"].isVisible():
                    dst["low"].setText(src["low"].text())
                    
                if "qual" in src and "qual" in dst and src["qual"].isVisible() and dst["qual"].isVisible():
                    dst["qual"].setText(src["qual"].text())
                    
        except Exception as e:
            print(f"Error copying tolerances: {e}")

    def collect_all_tolerance_settings(self):
        """Collect tolerance settings from all pages"""
        all_settings = {}
        
        def get_widget_text(widget):
            """Safely get text from widget"""
            if widget is None:
                return "0"
            if isinstance(widget, QLineEdit):
                return widget.text() or "0"
            elif isinstance(widget, QLabel):
                return widget.text() or "0"
            return "0"
        
        # Iterate through all pages in the stack
        for page_index in range(self.content_stack.count()):
            page = self.content_stack.widget(page_index)
            if not page:
                continue
            
            # Determine page type and standard from page index
            page_mapping = {
                0: ("DIN 3962", "Profile"),
                1: ("DIN 3962", "Lead / Line of action"),
                2: ("DIN 3962", "Spacing"),
                3: ("AGMA", "Profile"),
                4: ("AGMA", "Lead / Line of action"),
                5: ("AGMA", "Spacing"),
                6: ("ISO 1328 : 1997", "Profile"),
                7: ("ISO 1328 : 1997", "Lead / Line of action"),
                8: ("ISO 1328 : 1997", "Spacing"),
                9: ("ISO 1328 : 2013", "Profile"),
                10: ("ISO 1328 : 2013", "Lead / Line of action"),
                11: ("ISO 1328 : 2013", "Spacing"),
                12: ("ANSI B92.1", "Profile"),
                13: ("ANSI B92.1", "Lead / Line of action"),
                14: ("ANSI B92.1", "Spacing"),
                15: ("DIN 5480", "Profile"),
                16: ("DIN 5480", "Lead / Line of action"),
                17: ("DIN 5480", "Spacing")
            }
            
            if page_index not in page_mapping:
                continue
            
            standard, page_type = page_mapping[page_index]
            page_key = f"{standard}_{page_type}"
            
            # Get quality level from spinbox
            quality = 5
            spin_boxes = page.findChildren(QSpinBox)
            for spin_box in spin_boxes:
                if spin_box.minimum() == 1 and spin_box.maximum() == 12:
                    quality = spin_box.value()
                    break
            
            all_settings[page_key] = {
                "quality": quality,
                "data": {}
            }
            
            # Collect data based on page type
            page_type_lower = page_type.lower()
            if "profile" in page_type_lower and hasattr(page, 'profile_inputs'):
                inputs = page.profile_inputs
                for code, input_dict in inputs.items():
                    if "_check" in code:
                        continue
                    if isinstance(input_dict, dict) and "left" in input_dict and "right" in input_dict:
                        all_settings[page_key]["data"][code] = {
                            "left": {
                                "nom": float(get_widget_text(input_dict["left"].get("nom"))),
                                "upp": float(get_widget_text(input_dict["left"].get("upp"))),
                                "low": float(get_widget_text(input_dict["left"].get("low"))),
                                "qual": int(get_widget_text(input_dict["left"].get("qual")) or str(quality))
                            },
                            "right": {
                                "nom": float(get_widget_text(input_dict["right"].get("nom"))),
                                "upp": float(get_widget_text(input_dict["right"].get("upp"))),
                                "low": float(get_widget_text(input_dict["right"].get("low"))),
                                "qual": int(get_widget_text(input_dict["right"].get("qual")) or str(quality))
                            }
                        }
                        
            elif "lead" in page_type_lower and hasattr(page, 'lead_inputs'):
                inputs = page.lead_inputs
                for code, input_dict in inputs.items():
                    if "_check" in code:
                        continue
                    if isinstance(input_dict, dict) and "left" in input_dict and "right" in input_dict:
                        all_settings[page_key]["data"][code] = {
                            "left": {
                                "nom": float(get_widget_text(input_dict["left"].get("nom"))),
                                "upp": float(get_widget_text(input_dict["left"].get("upp"))),
                                "low": float(get_widget_text(input_dict["left"].get("low"))),
                                "qual": int(get_widget_text(input_dict["left"].get("qual")) or str(quality))
                            },
                            "right": {
                                "nom": float(get_widget_text(input_dict["right"].get("nom"))),
                                "upp": float(get_widget_text(input_dict["right"].get("upp"))),
                                "low": float(get_widget_text(input_dict["right"].get("low"))),
                                "qual": int(get_widget_text(input_dict["right"].get("qual")) or str(quality))
                            }
                        }
                        
            elif "spacing" in page_type_lower and hasattr(page, 'spacing_inputs'):
                inputs = page.spacing_inputs
                for code, input_dict in inputs.items():
                    if "_check" in code:
                        continue
                    if code in ["Fr", "Rs"]:
                        if isinstance(input_dict, dict):
                            all_settings[page_key]["data"][code] = {
                                "upp": float(get_widget_text(input_dict.get("upp"))),
                                "qual": int(get_widget_text(input_dict.get("qual")) or str(quality))
                            }
                    else:
                        if isinstance(input_dict, dict) and "left" in input_dict and "right" in input_dict:
                            all_settings[page_key]["data"][code] = {
                                "left": {
                                    "upp": float(get_widget_text(input_dict["left"].get("upp"))),
                                    "qual": int(get_widget_text(input_dict["left"].get("qual")) or str(quality))
                                },
                                "right": {
                                    "upp": float(get_widget_text(input_dict["right"].get("upp"))),
                                    "qual": int(get_widget_text(input_dict["right"].get("qual")) or str(quality))
                                }
                            }
        
        return all_settings
    
    def apply_settings(self):
        """Collect data from all pages, save to gear_data, and emit signal"""
        # Collect all settings from all pages
        all_settings = self.collect_all_tolerance_settings()
        
        # Save to gear_data (ensure it's a dict)
        if not isinstance(self.gear_data, dict):
            self.gear_data = {}
        self.gear_data['tolerance_settings'] = all_settings
        
        # Save current standard and quality level for report generation
        current_page = self.content_stack.currentWidget()
        if current_page:
            spin_boxes = current_page.findChildren(QSpinBox)
            for spin_box in spin_boxes:
                if spin_box.minimum() == 1 and spin_box.maximum() == 12:
                    self.gear_data['tolerance_quality_grade'] = spin_box.value()
                    break
        
        if self.current_page_id:
            standard = self.current_page_id.split("_", 1)[0]
            self.gear_data['tolerance_standard'] = standard
        
        # Emit signal with current page settings for backward compatibility
        settings = {
            "profile": {},
            "lead": {},
            "spacing": {}
        }
        
        # Get current page settings from all_settings
        if self.current_page_id and self.current_page_id in all_settings:
            page_data = all_settings[self.current_page_id]
            data_dict = page_data.get("data", {})
            
            # Determine page type
            if "profile" in self.current_page_id.lower():
                settings["profile"] = data_dict
            elif "lead" in self.current_page_id.lower():
                settings["lead"] = data_dict
            elif "spacing" in self.current_page_id.lower():
                settings["spacing"] = data_dict
        
        self.tolerances_updated.emit(settings)
        return all_settings

    def accept(self):
        self.apply_settings()
        super().accept()
