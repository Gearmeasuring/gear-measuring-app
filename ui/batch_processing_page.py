import os
import sys
import logging
import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, 
    QTreeWidget, QTreeWidgetItem, QLabel, QProgressBar, QMessageBox,
    QSplitter, QGroupBox, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QFileInfo
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineCore import QWebEngineSettings

# 批量处理专用的数据处理器类，避免创建完整UI
class BatchGearDataProcessor:
    """批量处理专用的齿轮数据处理器，提供PDF生成所需的核心功能"""
    
    def __init__(self):
        # 核心数据属性
        self.gear_data = None
        self.flank_data = {}
        self.profile_data = {}
        self.pitch_data = {'left': {}, 'right': {}}
        self.topography_data = {}
        self.current_file = ""
        self.deviation_results = None
        self._closing = False
        
    def load_mka_file(self, file_path):
        """加载并解析MKA文件"""
        try:
            self.current_file = file_path
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:  # 大于50MB
                logger.error("文件过大，无法处理")
                return False
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # 检查内容长度
            if len(content) > 100 * 1024 * 1024:  # 大于100MB
                logger.error("文件内容过大")
                return False
            
            # 解析数据
            self.gear_data = self.extract_gear_basic_data(content)
            self.flank_data = self.extract_measurement_data(content, "Flankenlinie")
            self.profile_data = self.extract_measurement_data(content, "Profil")
            self.pitch_data = self.extract_pitch_data(content)
            
            # 处理测量齿数
            self._process_measured_teeth()
            
            # 推断齿数（如果未直接提取到）
            self._infer_teeth()
            
            return True
        except Exception as e:
            logger.error(f"加载MKA文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_gear_basic_data(self, content):
        """从MKA文件内容中提取齿轮基本数据"""
        import re
        import math
        
        gear_data = {}
        lines = content.split('\n')

        patterns = [
            # 基本信息（文本字段）
            ('program', r'^\s*1\s*:Protokolldaten.*?Zahnrad.*?\((.+?)\)', 'str', 1),
            ('date', r'^\s*2\s*:Datum[^:]*:\s*(.+)', 'str', 1),
            ('start_time', r'^\s*3\s*:Zeit[^:]*:\s*([\d:]+)\s*/\s*([\d:]*)', 'str', 1),
            ('end_time', r'^\s*3\s*:Zeit[^:]*:\s*[\d:]+\s*/\s*([\d:]+)', 'str', 1),
            ('operator', r'^\s*4\s*:Operator[^:]*:\s*(.+)', 'str', 1),
            ('drawing_no', r'^\s*6\s*:Drawing No[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'^\s*7\s*:Order No[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'^\s*7\s*:.*?Serial.*?:\s*(.+)', 'str', 1),
            ('type', r'^\s*8\s*:Type[^:]*:\s*(.+)', 'str', 1),
            ('accuracy_grade', r'^\s*1016\s*:.*?:\s*(\d+)', 'int', 1),  # 添加精度等级

            # 齿轮参数 - 单值
            ('module', r'^\s*21\s*:.*?Normalmodul[^:]*:\s*([\d.]+)', 'float', 1),
            ('module', r'^\s*21\s*:.*?:\s*([\d.]+)', 'float', 1),  # 备用模式
            ('teeth', r'^\s*22\s*:.*?Zähnezahl[^:]*:\s*(-?\d+)', 'int', 1),
            ('teeth', r'^\s*22\s*:.*?Z.*?hnezahl[^:]*:\s*(-?\d+)', 'int', 1),  # 处理编码问题
            ('teeth', r'^\s*22\s*:.*?No\. of teeth[^:]*:\s*(-?\d+)', 'int', 1),  # 英文版
            ('teeth', r'^\s*22\s*:.*?Number of teeth[^:]*:\s*(-?\d+)', 'int', 1),  # 英文版
            ('helix_angle', r'^\s*23\s*:.*?Schrägungswinkel[^:]*:\s*(-?[\d.]+)', 'float', 1),
            ('pressure_angle', r'^\s*24\s*:.*?Eingriffswinkel[^:]*:\s*([\d.]+)', 'float', 1),
            ('modification_coeff', r'^\s*25\s*:.*?Profilverschiebungsfaktor[^:]*:\s*([\d.-]+)', 'float', 1),
            ('width', r'^\s*26\s*:.*?Zahnbreite[^:]*:\s*([\d.]+)', 'float', 1),
            ('face_width', r'^\s*26\s*:.*?Zahnbreite[^:]*:\s*([\d.]+)', 'float', 1),  # 别名
            ('tip_diameter', r'^\s*27\s*:.*?Kopfkreisdurchmesser[^:]*:\s*([\d.]+)', 'float', 1),
            ('diameter', r'^\s*27\s*:.*?Kopfkreisdurchmesser[^:]*:\s*([\d.]+)', 'float', 1),  # 别名
            ('measured_teeth', r'^\s*281\s*:.*?(?:Messzähnezahl|Messlückenz\.|Messzzwnezahl)[^=]*[=:][^:]*:\s*(-?\d+)', 'int', 1),
        ]

        for line in lines:
            for key, pattern, data_type, index in patterns:
                # 如果已经提取到该字段且值有效，跳过后续模式
                if key in gear_data:
                    if isinstance(gear_data[key], (int, float)) and gear_data[key] != 0:
                        continue
                    elif isinstance(gear_data[key], str) and gear_data[key]:
                        continue
                
                match = re.search(pattern, line)
                if match:
                    try:
                        if data_type == 'str':
                            value = match.group(index).strip()
                            if value:
                                gear_data[key] = value
                        else:
                            value = match.group(index).strip()
                            if value:
                                if data_type == 'int':
                                    val = int(value)
                                    # 对于齿数，如果值为负数或0，尝试绝对值
                                    if key == 'teeth' and val <= 0:
                                        if val < 0:
                                            val = abs(val)
                                        else:
                                            continue  # 跳过0值
                                    gear_data[key] = val
                                else:
                                    gear_data[key] = float(value)
                            else:
                                gear_data[key] = 0.0 if data_type == 'float' else 0
                    except (ValueError, IndexError) as e:
                        logger.warning(f"解析错误 '{key}' - {line.strip()} - {str(e)}")
                    break

        # 设置默认值
        if 'teeth' not in gear_data or gear_data['teeth'] <= 0:
            gear_data['teeth'] = 0
        if 'module' not in gear_data:
            gear_data['module'] = 0.0
        if 'pressure_angle' not in gear_data:
            gear_data['pressure_angle'] = 20.0
        if 'width' not in gear_data:
            gear_data['width'] = 0.0
        if 'face_width' not in gear_data:
            gear_data['face_width'] = gear_data['width']
        if 'tip_diameter' not in gear_data:
            gear_data['tip_diameter'] = 0.0
        if 'diameter' not in gear_data:
            gear_data['diameter'] = gear_data['tip_diameter']
        if 'helix_angle' not in gear_data:
            gear_data['helix_angle'] = 0.0
        
        return gear_data
    
    def extract_measurement_data(self, content, data_type):
        """提取测量数据（齿形或齿向）"""
        import re
        
        data = {'left': {}, 'right': {}}
        
        # 简单实现，创建基本结构
        # 实际项目中可能需要更复杂的解析逻辑
        
        # 尝试从内容中提取齿号
        teeth_pattern = r'\s*Teeth\s*:\s*(\d+)'
        matches = re.findall(teeth_pattern, content)
        
        if matches:
            for tooth_str in set(matches):
                try:
                    tooth = int(tooth_str)
                    data['left'][tooth] = {'data': []}
                    data['right'][tooth] = {'data': []}
                except:
                    continue
        
        return data
    
    def extract_pitch_data(self, content):
        """提取周节数据"""
        import re
        
        pitch_data = {'left': {}, 'right': {}}
        
        # 简单实现，尝试提取周节数据
        pitch_pattern = r'\s*Teeth\s*:\s*(\d+).*?Pitch\s*:\s*([\d.-]+)'
        matches = re.findall(pitch_pattern, content)
        
        if matches:
            for tooth_str, pitch_str in matches:
                try:
                    tooth = int(tooth_str)
                    pitch = float(pitch_str)
                    pitch_data['left'][tooth] = {'pitch': pitch}
                    pitch_data['right'][tooth] = {'pitch': pitch}
                except:
                    continue
        
        return pitch_data
    
    def _process_measured_teeth(self):
        """处理测量齿数"""
        measured_teeth_set = set()
        
        # 从齿形数据统计
        if self.profile_data and isinstance(self.profile_data, dict):
            for side in ['left', 'right']:
                side_data = self.profile_data.get(side, {})
                if side_data and isinstance(side_data, dict):
                    measured_teeth_set.update(side_data.keys())
        
        # 从齿向数据统计
        if self.flank_data and isinstance(self.flank_data, dict):
            for side in ['left', 'right']:
                side_data = self.flank_data.get(side, {})
                if side_data and isinstance(side_data, dict):
                    measured_teeth_set.update(side_data.keys())
        
        measured_teeth_count = len(measured_teeth_set) if measured_teeth_set else 0
        
        if measured_teeth_count > 0:
            self.gear_data['measured_teeth'] = measured_teeth_count
            logger.info(f"从测量数据统计测量齿数: {measured_teeth_count}")
    
    def _infer_teeth(self):
        """推断齿数（如果未直接提取到）"""
        if self.gear_data.get('teeth', 0) <= 0:
            inferred_teeth = 0
            
            # 从周节数据推断
            if self.pitch_data:
                for side in ['left', 'right']:
                    side_data = self.pitch_data.get(side, {})
                    if side_data and isinstance(side_data, dict) and side_data:
                        max_tooth = max(side_data.keys())
                        inferred_teeth = max(inferred_teeth, max_tooth)
            
            # 从齿形数据推断
            if inferred_teeth <= 0 and self.profile_data and isinstance(self.profile_data, dict):
                for side in ['left', 'right']:
                    side_data = self.profile_data.get(side, {})
                    if side_data and isinstance(side_data, dict):
                        inferred_teeth = max(inferred_teeth, len(side_data))
            
            # 从齿向数据推断
            if inferred_teeth <= 0 and self.flank_data and isinstance(self.flank_data, dict):
                for side in ['left', 'right']:
                    side_data = self.flank_data.get(side, {})
                    if side_data and isinstance(side_data, dict):
                        inferred_teeth = max(inferred_teeth, len(side_data))
            
            if inferred_teeth > 0:
                self.gear_data['teeth'] = inferred_teeth
                logger.info(f"从测量数据推断齿数: {inferred_teeth}")
    
    def analyze_deviation(self):
        """分析偏差"""
        # 创建默认的偏差分析结果
        self.deviation_results = self.create_default_deviation_results()
    
    def create_default_deviation_results(self):
        """创建默认偏差分析结果"""
        return {
            'profile': {'left': {}, 'right': {}},
            'flank': {'left': {}, 'right': {}},
            'pitch': {'left': {}, 'right': {}}
        }
    
    def generate_klingelnberg_pdf_report(self, auto_generate=False):
        """生成克林贝格标准PDF报告"""
        try:
            logger.info(f"开始生成PDF，当前文件: {self.current_file}")
            
            if not self.current_file:
                logger.error("没有当前文件")
                return False
            
            # 验证必要的数据
            if not hasattr(self, 'deviation_results') or not self.deviation_results:
                self.analyze_deviation()
            
            # 生成PDF文件名
            default_name = os.path.splitext(os.path.basename(self.current_file))[0] + ".pdf"
            
            # 自动生成模式，将PDF保存在与MKA文件同一目录
            output_path = os.path.join(os.path.dirname(self.current_file), default_name)
            logger.info(f"PDF保存路径: {output_path}")
            
            # 导入PDF生成相关模块
            from 齿轮波纹度软件2_修改版_simplified import KlingelnbergSinglePageReport, SimpleNamespace
            
            # 适配数据结构
            try:
                # 1. Basic Info
                basic_info = SimpleNamespace(
                    program=self.gear_data.get('图号', 'N/A'),
                    drawing_number=self.gear_data.get('图号', 'N/A'),
                    drawing_no=self.gear_data.get('图号', 'N/A'),
                    module=float(self.gear_data.get('模数', 0)),
                    teeth=int(self.gear_data.get('齿数', 0)),
                    teeth_count=int(self.gear_data.get('齿数', 0)),
                    pressure_angle=float(self.gear_data.get('压力角', 20.0)),
                    gear_number=self.gear_data.get('工件号', 'N/A'),
                    order_no=self.gear_data.get('工件号', 'N/A'),
                    serial=self.gear_data.get('序号', 'N/A'),
                    accuracy_grade=str(self.gear_data.get('accuracy_grade', '6')),
                    operator=self.gear_data.get('操作员', 'N/A'),
                    helix_angle=float(self.gear_data.get('螺旋角', 0)),
                    base_helix_angle=float(self.gear_data.get('基圆螺旋角', 0)),
                    width=float(self.gear_data.get('齿宽', 0)),
                    face_width=float(self.gear_data.get('齿宽', 0)),
                    date=self.gear_data.get('日期', ''),
                    measurement_date=self.gear_data.get('日期', ''),
                    tip_diameter=float(self.gear_data.get('齿顶圆直径', 0)),
                    diameter=float(self.gear_data.get('齿顶圆直径', 0)),
                    # 设置默认的标记位置
                    profile_markers_left=None,
                    profile_markers_right=None,
                    lead_markers_left=None,
                    lead_markers_right=None
                )

                # 2. Profile Data
                profile_data = SimpleNamespace(
                    left=self.profile_data.get('left', {}),
                    right=self.profile_data.get('right', {})
                )

                # 3. Flank Data
                flank_data = SimpleNamespace(
                    left=self.flank_data.get('left', {}),
                    right=self.flank_data.get('right', {})
                )

                # 4. Measurement Data Container
                pitch_data_obj = SimpleNamespace(
                    left=self.pitch_data.get('left', {}),
                    right=self.pitch_data.get('right', {})
                )

                measurement_data = SimpleNamespace(
                    basic_info=basic_info,
                    profile_data=profile_data,
                    flank_data=flank_data,
                    pitch_data=pitch_data_obj
                )
            except (ValueError, TypeError) as e:
                logger.error(f"数据结构适配错误: {str(e)}")
                return False
            
            # 配置公差参数
            if 'tolerance_settings' not in self.deviation_results:
                # 设置默认公差
                quality_grade = 6
                
                # Profile tolerance lookup table
                profile_tolerance_table = {
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
                
                # Lead tolerance lookup table
                lead_tolerance_table = {
                    1: (2.5, 2.0, 3.0),
                    2: (3.5, 5.0, 6.0),
                    3: (4.5, 7.0, 8.0),
                    4: (6.0, 8.0, 10.0),
                    5: (8.0, 9.0, 12.0),
                    6: (11.0, 12.0, 16.0),
                    7: (16.0, 16.0, 22.0),
                    8: (22.0, 25.0, 32.0),
                    9: (32.0, 40.0, 50.0),
                    10: (50.0, 63.0, 80.0),
                    11: (80.0, 100.0, 125.0),
                    12: (125.0, 160.0, 200.0)
                }
                
                # Get tolerances for the quality grade
                fHa, ffa, Fa = profile_tolerance_table.get(quality_grade, profile_tolerance_table[6])
                fHb, ffb, Fb = lead_tolerance_table.get(quality_grade, lead_tolerance_table[6])
                
                # Create tolerance settings structure
                self.deviation_results['tolerance_settings'] = {
                    'profile': {
                        'fHa': {
                            'left': {'upp': fHa, 'low': -fHa, 'qual': quality_grade},
                            'right': {'upp': fHa, 'low': -fHa, 'qual': quality_grade}
                        },
                        'ffa': {
                            'left': {'upp': ffa, 'qual': quality_grade},
                            'right': {'upp': ffa, 'qual': quality_grade}
                        },
                        'Fa': {
                            'left': {'upp': Fa, 'qual': quality_grade},
                            'right': {'upp': Fa, 'qual': quality_grade}
                        }
                    },
                    'lead': {
                        'fHb': {
                            'left': {'upp': fHb, 'low': -fHb, 'qual': quality_grade},
                            'right': {'upp': fHb, 'low': -fHb, 'qual': quality_grade}
                        },
                        'ffb': {
                            'left': {'upp': ffb, 'qual': quality_grade},
                            'right': {'upp': ffb, 'qual': quality_grade}
                        },
                        'Fb': {
                            'left': {'upp': Fb, 'qual': quality_grade},
                            'right': {'upp': Fb, 'qual': quality_grade}
                        }
                    }
                }
            
            # 生成PDF
            try:
                logger.info("创建报告生成器...")
                report_generator = KlingelnbergSinglePageReport()
                
                logger.info("调用报告生成方法...")
                success = report_generator.generate_report(
                    measurement_data,
                    self.deviation_results,
                    output_path
                )
                
                if success:
                    logger.info(f"PDF生成成功: {output_path}")
                    return True
                else:
                    logger.error(f"PDF生成失败: {output_path}")
                    return False
            except Exception as e:
                logger.error(f"报告生成器出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
        except Exception as e:
            logger.error(f"生成PDF时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

# 添加根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logger = logging.getLogger(__name__)

# 批量处理工作线程
class BatchProcessingThread(QThread):
    """批量处理MKA文件生成PDF的工作线程"""
    progress_updated = pyqtSignal(int, str)  # 进度更新信号
    processing_complete = pyqtSignal(list)  # 处理完成信号
    error_occurred = pyqtSignal(str)  # 错误发生信号

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.mka_files = []
        self.generated_pdfs = []
        self.is_running = True

    def run(self):
        try:
            # 查找所有MKA文件
            self.mka_files = [f for f in os.listdir(self.folder_path) 
                           if f.lower().endswith('.mka')]
            
            if not self.mka_files:
                self.error_occurred.emit("未找到任何MKA文件")
                return
            
            total_files = len(self.mka_files)
            
            # 导入所需的类
            from PyQt5.QtWidgets import QApplication
            
            # 确保有QApplication实例
            if not QApplication.instance():
                app = QApplication([])
            
            # 使用简化的BatchGearDataProcessor进行批量处理
            viewer = BatchGearDataProcessor()
            
            for index, mka_file in enumerate(self.mka_files):
                if not self.is_running:
                    break
                
                file_path = os.path.join(self.folder_path, mka_file)
                
                # 更新进度
                progress = int((index + 1) / total_files * 100)
                self.progress_updated.emit(progress, f"正在处理: {mka_file}")
                
                try:
                    # 直接使用BatchGearDataProcessor加载文件
                    self.progress_updated.emit(progress, f"正在加载: {mka_file}")
                    
                    # 加载MKA文件
                    if viewer.load_mka_file(file_path):
                        # 分析偏差
                        self.progress_updated.emit(progress, f"正在分析: {mka_file}")
                        viewer.analyze_deviation()
                        
                        # 生成PDF
                        self.progress_updated.emit(progress, f"正在生成PDF: {mka_file}")
                        success = viewer.generate_klingelnberg_pdf_report(auto_generate=True)
                        
                        if success:
                            # 检查生成的PDF文件
                            pdf_name = f"{os.path.splitext(mka_file)[0]}.pdf"
                            pdf_path = os.path.join(self.folder_path, pdf_name)
                            
                            if os.path.exists(pdf_path):
                                self.generated_pdfs.append((mka_file, pdf_path))
                                logger.info(f"成功生成PDF: {pdf_path}")
                            else:
                                logger.warning(f"PDF生成失败: {pdf_name}")
                        else:
                            logger.warning(f"PDF生成失败: {mka_file}")
                        
                except Exception as e:
                    logger.error(f"处理文件 {mka_file} 时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        except Exception as e:
            logger.error(f"批量处理线程出错: {str(e)}")
            self.error_occurred.emit(f"批量处理出错: {str(e)}")
        finally:
            self.processing_complete.emit(self.generated_pdfs)

    def stop(self):
        """停止处理"""
        self.is_running = False

class BatchProcessingPage(QWidget):
    """批量处理页面"""
    
    # 添加信号用于通知主窗口更新树形菜单
    processing_complete = pyqtSignal(list)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.pdf_files = []  # 存储生成的PDF文件列表
        self.init_ui()
        
        # 连接信号到主窗口的更新方法
        self.processing_complete.connect(self.main_window.update_batch_tree_items)
    
    def init_ui(self):
        """初始化UI界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        
        # 创建控制面板
        control_group = QGroupBox("控制面板")
        control_layout = QHBoxLayout()
        
        # 选择文件夹按钮
        self.select_folder_btn = QPushButton("选择文件夹")
        self.select_folder_btn.clicked.connect(self.select_folder)
        control_layout.addWidget(self.select_folder_btn)
        
        # 开始处理按钮
        self.start_process_btn = QPushButton("开始批量处理")
        self.start_process_btn.clicked.connect(self.start_processing)
        self.start_process_btn.setEnabled(False)  # 初始禁用
        control_layout.addWidget(self.start_process_btn)
        
        # 停止处理按钮
        self.stop_process_btn = QPushButton("停止处理")
        self.stop_process_btn.clicked.connect(self.stop_processing)
        self.stop_process_btn.setEnabled(False)  # 初始禁用
        control_layout.addWidget(self.stop_process_btn)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # 创建进度显示
        self.progress_layout = QHBoxLayout()
        self.progress_label = QLabel("等待处理...")
        self.progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(self.progress_layout)
        
        # 创建分隔器，用于左侧树形菜单和右侧PDF预览
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建PDF列表树形菜单
        self.pdf_tree = QTreeWidget()
        self.pdf_tree.setHeaderLabel("生成的PDF文件列表")
        self.pdf_tree.itemDoubleClicked.connect(self.on_pdf_item_double_clicked)
        splitter.addWidget(self.pdf_tree)
        
        # 创建PDF预览组件
        self.pdf_preview = QWebEngineView()
        self.setup_pdf_viewer()
        splitter.addWidget(self.pdf_preview)
        
        # 设置分隔器比例
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
        
        # 初始化工作线程
        self.worker_thread = None
        
    def setup_pdf_viewer(self):
        """设置PDF预览组件"""
        # 启用PDF查看支持
        settings = self.pdf_preview.settings()
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.PdfViewerEnabled, True)
        
        # 设置空白页面
        self.pdf_preview.setHtml('<html><body style="background-color: #f0f0f0; display: flex; justify-content: center; align-items: center;"><h2>选择并双击PDF文件进行预览</h2></body></html>')
    
    def select_folder(self):
        """选择目标文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择MKA文件文件夹", "", 
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder_path:
            self.selected_folder = folder_path
            self.select_folder_btn.setText(f"文件夹: {os.path.basename(folder_path)}")
            self.start_process_btn.setEnabled(True)
            logger.info(f"选择了文件夹: {folder_path}")
    
    def start_processing(self):
        """开始批量处理"""
        if not hasattr(self, 'selected_folder'):
            QMessageBox.warning(self, "警告", "请先选择文件夹")
            return
        
        # 清空之前的结果
        self.pdf_tree.clear()
        self.pdf_files.clear()
        
        # 禁用控制按钮
        self.select_folder_btn.setEnabled(False)
        self.start_process_btn.setEnabled(False)
        self.stop_process_btn.setEnabled(True)
        
        # 初始化进度
        self.progress_label.setText("正在准备处理...")
        self.progress_bar.setValue(0)
        
        # 创建并启动工作线程
        self.worker_thread = BatchProcessingThread(self.selected_folder)
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.processing_complete.connect(self.on_processing_complete)
        self.worker_thread.error_occurred.connect(self.show_error)
        self.worker_thread.start()
    
    def stop_processing(self):
        """停止批量处理"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()
            
            self.progress_label.setText("处理已停止")
            self.enable_controls()
    
    def update_progress(self, progress, status):
        """更新处理进度"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(status)
    
    def on_processing_complete(self, generated_pdfs):
        """处理完成"""
        self.progress_label.setText(f"处理完成，成功生成 {len(generated_pdfs)} 个PDF文件")
        
        # 更新PDF列表
        self.pdf_files = generated_pdfs
        self.populate_pdf_tree()
        
        # 发送信号通知主窗口更新树形菜单
        self.processing_complete.emit(generated_pdfs)
        
        # 启用控制按钮
        self.enable_controls()
    
    def show_error(self, error_msg):
        """显示错误信息"""
        QMessageBox.critical(self, "错误", error_msg)
        self.progress_label.setText("处理出错")
        self.enable_controls()
    
    def enable_controls(self):
        """启用控制按钮"""
        self.select_folder_btn.setEnabled(True)
        self.start_process_btn.setEnabled(True)
        self.stop_process_btn.setEnabled(False)
    
    def populate_pdf_tree(self):
        """填充PDF文件树形菜单"""
        for mka_file, pdf_path in self.pdf_files:
            item = QTreeWidgetItem(self.pdf_tree)
            item.setText(0, mka_file)
            # 存储PDF路径
            item.setData(0, Qt.UserRole, pdf_path)
        
        # 展开所有项目
        self.pdf_tree.expandAll()
    
    def on_pdf_item_double_clicked(self, item, column):
        """双击PDF项目时打开预览"""
        pdf_path = item.data(0, Qt.UserRole)
        
        if pdf_path and os.path.exists(pdf_path):
            try:
                # 使用QWebEngineView加载PDF，需要使用file://协议
                from PyQt5.QtCore import QUrl
                file_url = QUrl.fromLocalFile(pdf_path)
                self.pdf_preview.load(file_url)
                logger.info(f"在批量处理页面中加载PDF: {pdf_path}")
            except Exception as e:
                logger.error(f"加载PDF时出错: {str(e)}")
                QMessageBox.warning(self, "警告", f"加载PDF失败: {str(e)}")
        else:
            QMessageBox.warning(self, "警告", "PDF文件不存在或路径无效")
