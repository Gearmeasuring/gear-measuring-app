import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, 
                             QStackedWidget, QWidget, QLabel, QLineEdit, QPushButton, 
                             QCheckBox, QGroupBox, QGridLayout, QComboBox, QScrollArea,
                             QFrame, QSpinBox, QMessageBox, QHeaderView, QToolButton)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QBrush, QIcon, QPixmap

class ToleranceSettingsDialog(QDialog):
    """
    Tolerance Settings Dialog class for gear analysis software.
    This dialog allows users to view and modify tolerance values for different gear parameters.
    """
    
    tolerances_updated = pyqtSignal(dict)
    
    def __init__(self, gear_data=None, parent=None):
        super().__init__(parent)
        self.gear_data = gear_data or {}
        self.setWindowTitle("Tolerance Settings")
        self.resize(1000, 700)
        
        # Add properties to track current page and quality controls
        self.current_page_id = None
        self.profile_quality_spins = {}
        self.lead_quality_spins = {}
        self.spacing_quality_spins = {}
        
        self.init_ui()
        self.load_initial_data()