"""
Batch Processing Page
Allows users to select a folder, process all MKA files, and view generated reports.
"""
import os
import glob
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFileDialog, QProgressBar, QListWidget, QListWidgetItem, 
    QSplitter, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QAxContainer import QAxWidget

from gear_analysis_refactored.config.logging_config import logger
try:
    from ..utils import parse_mka_file
    from ..models import create_gear_data_from_dict
    from ..reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
except ImportError:
    from gear_analysis_refactored.utils import parse_mka_file
    from gear_analysis_refactored.models import create_gear_data_from_dict
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
from matplotlib.backends.backend_pdf import PdfPages

class BatchWorker(QThread):
    """Worker thread for batch processing"""
    progress_updated = pyqtSignal(int, int)  # current, total
    file_processed = pyqtSignal(str, str, bool, str)  # filename, full_path, success, message
    finished = pyqtSignal()
    
    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.is_running = True
        
    def run(self):
        mka_files = glob.glob(os.path.join(self.folder_path, "*.mka"))
        total_files = len(mka_files)
        
        for i, file_path in enumerate(mka_files):
            if not self.is_running:
                break
                
            filename = os.path.basename(file_path)
            try:
                # 1. Parse MKA
                data_dict = parse_mka_file(file_path)
                measurement_data = create_gear_data_from_dict(data_dict)
                
                # 2. Generate PDF Report
                # Output filename: [original_name]_Ripple.pdf
                output_filename = os.path.splitext(filename)[0] + "_Ripple.pdf"
                output_path = os.path.join(self.folder_path, output_filename)
                
                report = KlingelnbergRippleSpectrumReport()
                with PdfPages(output_path) as pdf:
                    report.create_page(pdf, measurement_data)
                
                self.file_processed.emit(filename, output_path, True, "Success")
                
            except Exception as e:
                logger.error(f"Failed to process {filename}: {e}")
                self.file_processed.emit(filename, "", False, str(e))
            
            self.progress_updated.emit(i + 1, total_files)
            
        self.finished.emit()
        
    def stop(self):
        self.is_running = False

class BatchProcessingPage(QWidget):
    """Batch Processing UI"""
    
    # 添加信号用于通知主窗口更新树形菜单
    processing_complete = pyqtSignal(list)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.processed_files = {} # filename -> pdf_path
        self.init_ui()
        
        # 连接信号到主窗口的更新方法（如果存在）
        if hasattr(main_window, 'update_batch_tree_items'):
            self.processing_complete.connect(self.main_window.update_batch_tree_items)
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Top Control Panel
        control_panel = QFrame()
        control_panel.setFrameShape(QFrame.StyledPanel)
        control_layout = QHBoxLayout(control_panel)
        
        self.folder_label = QLabel("No folder selected")
        self.select_btn = QPushButton("📂 Select Folder")
        self.select_btn.clicked.connect(self.select_folder)
        
        self.start_btn = QPushButton("▶ Start Processing")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_processing)
        
        control_layout.addWidget(self.select_btn)
        control_layout.addWidget(self.folder_label)
        control_layout.addStretch()
        control_layout.addWidget(self.start_btn)
        
        layout.addWidget(control_panel)
        
        # 2. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 3. Main Content (Splitter)
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: File List
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addWidget(QLabel("Processed Files:"))
        
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.on_file_clicked)
        list_layout.addWidget(self.file_list)
        
        splitter.addWidget(list_container)
        
        # Right: PDF Viewer
        viewer_container = QWidget()
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.addWidget(QLabel("Report Preview:"))
        
        try:
            self.pdf_viewer = QAxWidget()
            self.pdf_viewer.setControl("AcroPDF.PDF") # Try Adobe Reader
        except Exception as e:
            logger.warning(f"Failed to init ActiveX PDF Viewer: {e}")
            self.pdf_viewer = QLabel("PDF Viewer not available (ActiveX error)")
            self.pdf_viewer.setAlignment(Qt.AlignCenter)
            
        viewer_layout.addWidget(self.pdf_viewer)
        
        splitter.addWidget(viewer_container)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder containing MKA files")
        if folder:
            self.folder_path = folder
            self.folder_label.setText(folder)
            self.start_btn.setEnabled(True)
            self.file_list.clear()
            self.processed_files.clear()
            
    def start_processing(self):
        if not hasattr(self, 'folder_path'):
            return
            
        self.start_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.file_list.clear()
        self.processed_files.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = BatchWorker(self.folder_path)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.file_processed.connect(self.on_file_processed)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.start()
        
    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"Processing... {current}/{total}")
        
    def on_file_processed(self, filename, pdf_path, success, message):
        item = QListWidgetItem()
        if success:
            item.setText(f"✅ {filename}")
            item.setData(Qt.UserRole, pdf_path)
            self.processed_files[filename] = pdf_path
        else:
            item.setText(f"❌ {filename} ({message})")
            item.setForeground(QColor("red"))
            
        self.file_list.addItem(item)
        
    def on_processing_finished(self):
        self.start_btn.setEnabled(True)
        self.select_btn.setEnabled(True)
        self.progress_bar.setFormat("Done!")
        QMessageBox.information(self, "Batch Processing", "Processing completed!")
        
        # 发送信号通知主窗口更新树形菜单
        processed_files_list = list(self.processed_files.items())
        self.processing_complete.emit(processed_files_list)
        
    def on_file_clicked(self, item):
        pdf_path = item.data(Qt.UserRole)
        if pdf_path and os.path.exists(pdf_path):
            try:
                # Load file into ActiveX control
                self.pdf_viewer.dynamicCall("LoadFile(const QString&)", pdf_path)
            except Exception as e:
                logger.error(f"Failed to load PDF: {e}")
                # Fallback: Open externally
                os.startfile(pdf_path)
