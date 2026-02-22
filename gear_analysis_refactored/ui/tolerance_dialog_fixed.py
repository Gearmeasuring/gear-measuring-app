import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
                             QStackedWidget, QWidget, QLabel, QLineEdit, QPushButton, 
                             QCheckBox, QGroupBox, QGridLayout, QComboBox, QScrollArea,
                             QFrame, QSpinBox, QMessageBox, QHeaderView, QToolButton)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon, QPixmap

class ToleranceSettingsDialog(QDialog):
    tolerances_updated = pyqtSignal(dict)
    
    def __init__(self, gear_data=None, parent=None):
        super().__init__(parent)
        self.gear_data = gear_data or {}
        self.current_page_id = None  # Track current page ID
        self.quality_spins = {}  # Dictionary to store quality spin boxes for each page
        self.setWindowTitle("Tolerance Settings")
        self.setFixedSize(1000, 700)
        self.init_ui()
        self.load_initial_data()
    
    def init_ui(self):
        # Create main layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
    def populate_tree(self):
        # Tree population code...
        pass
    
    def on_tree_item_clicked(self, item, column):
        page_id = item.data(0, Qt.UserRole)
        if page_id is None:
            return
        
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
    
    # Example page creation method (partial)
    def create_din3962_profile_page(self):
        page = QWidget()
        # ... existing page creation code ...
        
        # Header: Quality Level
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Quality levels Q ="))
        
        # Create quality spin box
        quality_spin = QSpinBox()
        quality_spin.setRange(1, 12)
        quality_spin.setValue(5)
        quality_spin.setFixedWidth(50)
        header_layout.addWidget(quality_spin)
        
        # Store the spin box in the dictionary
        self.quality_spins["DIN 3962_Profile"] = quality_spin
        
        set_btn = QPushButton("Set")
        set_btn.clicked.connect(lambda: self.calculate_tolerances("profile"))
        header_layout.addWidget(set_btn)
        
        # ... rest of the page creation code ...
        return page
    
    # Other page creation methods would be modified similarly
    
    def calculate_tolerances(self, type_):
        """Set tolerance values based on quality level using predefined lookup tables"""
        try:
            if type_ == "profile":
                # Get the correct quality spin box based on current page
                if self.current_page_id and self.current_page_id in self.quality_spins:
                    quality_spin = self.quality_spins[self.current_page_id]
                    Q = quality_spin.value()
                else:
                    # Fallback if no current page info
                    Q = 5
                
                # Fixed tolerance values for each quality level (from reference images)
                # Quality level: (fHa, ffa, Fa)
                tolerance_table = {
                    1: (3.0, 4.0, 5.0),
                    2: (4.0, 6.0, 7.0),
                    3: (5.5, 8.0, 10.0),
                    4: (8.0, 12.0, 14.0),
                    5: (11.0, 16.0, 20.0),
                    6: (16.0, 22.0, 28.0),
                    7: (22.0, 32.0, 40.0),
                    8: (28.0, 45.0, 56.0),
                    9: (40.0, 63.0, 80.0),
                    10: (71.0, 110.0, 125.0),
                    11: (110.0, 160.0, 200.0),
                    12: (180.0, 250.0, 320.0)
                }
                
                # Get tolerance values for the selected quality level
                if Q in tolerance_table:
                    fHa, ffa, Fa = tolerance_table[Q]
                else:
                    # Default to quality level 5 if out of range
                    fHa, ffa, Fa = tolerance_table[5]
                
                # Update UI - set all quality fields to the selected quality level
                for side in ['left', 'right']:
                    # Update all quality fields to show the selected quality level
                    for code in self.profile_inputs:
                        if "_check" not in code and side in self.profile_inputs[code]:
                            if 'qual' in self.profile_inputs[code][side]:
                                qual_field = self.profile_inputs[code][side]['qual']
                                if isinstance(qual_field, QLineEdit):
                                    qual_field.setText(str(Q))
                    
                    # Update tolerance values with fixed values from lookup table
                    self.profile_inputs['fHa'][side]['upp'].setText(f"{fHa:.1f}")
                    self.profile_inputs['fHa'][side]['low'].setText(f"{-fHa:.1f}")
                    
                    self.profile_inputs['ffa'][side]['upp'].setText(f"{ffa:.1f}")
                    
                    self.profile_inputs['Fa'][side]['upp'].setText(f"{Fa:.1f}")
                    
                    # Var doesn't have quality field in the visible columns, set to 0.0
                    if 'Var' in self.profile_inputs:
                        self.profile_inputs['Var'][side]['upp'].setText("0.0")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to calculate tolerances: {str(e)}")
    
    # Other methods would be included here
