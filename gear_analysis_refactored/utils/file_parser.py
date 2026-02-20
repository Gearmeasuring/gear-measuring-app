"""
MKA文件解析器模块
负责读取和解析MKA格式的齿轮测量数据文件
"""
import re
import os
import logging
from typing import Dict, List, Tuple, Optional, Any

# 配置日志
logger = logging.getLogger('MKAFileParser')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# 模拟 FileConfig 类
class FileConfig:
    DEFAULT_ENCODING = 'utf-8'
    BACKUP_ENCODING = 'gbk'
    
    @staticmethod
    def get_mka_file_patterns():
        return ['.mka']


class MKAFileParser:
    """
    MKA文件解析器
    用于解析齿轮测量数据文件
    """
    
    def __init__(self):
        self.file_path = ""
        self.content = ""
        self.encoding = FileConfig.DEFAULT_ENCODING
        
    def read_file(self, file_path: str) -> str:
        """
        读取MKA文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容
            
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取失败
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        self.file_path = file_path
        
        # 尝试不同的编码
        encodings = [FileConfig.DEFAULT_ENCODING, FileConfig.BACKUP_ENCODING, 'gbk', 'utf-8']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
                if content:
                    self.content = content
                    self.encoding = encoding
                    logger.info(f"成功读取文件 {os.path.basename(file_path)}，编码: {encoding}")
                    return content
            except Exception as e:
                logger.warning(f"使用 {encoding} 编码读取失败: {e}")
                continue
                
        raise IOError(f"无法读取文件: {file_path}")
    
    def extract_gear_basic_data(self, content: str) -> Dict[str, Any]:
        """
        提取齿轮基本数据
        
        Args:
            content: 文件内容
            
        Returns:
            Dict: 齿轮基本数据
        """
        gear_data = {}
        lines = content.split('\n')
        
        # 定义提取模式
        patterns = [
            # 基本信息
            ('program', r'^\s*1\s*:.*?Zahnrad[^:]*:\s*(.+?)(?:\s*\([^)]*\))?$', 'str', 1),
            ('date', r'^\s*2\s*:Datum[^:]*:\s*(.+)', 'str', 1),
            ('start_time', r'^\s*3\s*:Zeit[^:]*:\s*([\d:]+)\s*/\s*([\d:]*)', 'str', 1),
            ('end_time', r'^\s*3\s*:Zeit[^:]*:\s*[\d:]+\s*/\s*([\d:]+)', 'str', 1),
            ('operator', r'^\s*4\s*:Operator[^:]*:\s*(.+)', 'str', 1),
            ('location', r'^\s*5\s*:Location of check[^:]*:\s*(.+)', 'str', 1),
            ('drawing_no', r'^\s*6\s*:Drawing No[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'^\s*7\s*:Order No[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'^\s*7\s*:.*?Order[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'^\s*7\s*:.*?Serial[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'^\s*7\s*:.*?Serien[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'^\s*\d+\s*:.*?Order[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'^\s*\d+\s*:.*?Serial[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'^\s*\d+\s*:.*?Serien[^:]*:\s*(.+)', 'str', 1),
            # 尝试更宽松的匹配模式
            ('order_no', r'Order\s*No[^:]*:\s*(.+)', 'str', 1),
            ('order_no', r'Serial[^:]*:\s*(.+)', 'str', 1),
            ('type', r'^\s*8\s*:Type[^:]*:\s*(.+)', 'str', 1),
            ('customer', r'^\s*9\s*:Custom/Mach[^:]*:\s*(.+)', 'str', 1),
            ('condition', r'^\s*10\s*:Condition[^:]*:\s*(.+)', 'str', 1),
            
            # 齿轮参数 - 添加多种匹配模式
            ('module', r'^\s*21\s*:.*?Normalmodul[^:]*:\s*([\d.]+)', 'float', 1),
            ('module', r'^\s*21\s*:.*?:\s*([\d.]+)', 'float', 1),  # 备用模式
            ('teeth', r'^\s*22\s*:.*?Zähnezahl[^:]*:\s*(\d+)', 'int', 1),
            ('teeth', r'^\s*22\s*:.*?Z.*?hnezahl[^:]*:\s*(\d+)', 'int', 1),  # 处理编码问题
            ('teeth', r'^\s*22\s*:.*?:\s*(\d+)', 'int', 1),  # 简化模式
            ('helix_angle', r'^\s*23\s*:.*?Schrägungswinkel[^:]*:\s*(-?[\d.]+)', 'float', 1),
            ('helix_angle', r'^\s*23\s*:.*?:\s*(-?[\d.]+)', 'float', 1),  # 备用
            ('pressure_angle', r'^\s*24\s*:.*?Eingriffswinkel[^:]*:\s*([\d.]+)', 'float', 1),
            ('pressure_angle', r'^\s*24\s*:.*?:\s*([\d.]+)', 'float', 1),  # 备用
            ('modification_coeff', r'^\s*25\s*:.*?Profilverschiebungsfaktor[^:]*:\s*([\d.-]+)', 'float', 1),
            ('width', r'^\s*26\s*:.*?Zahnbreite[^:]*:\s*([\d.]+)', 'float', 1),
            ('width', r'^\s*26\s*:.*?:\s*([\d.]+)', 'float', 1),  # 备用
            ('tip_diameter', r'^\s*27\s*:.*?Kopfkreisdurchmesser[^:]*:\s*([\d.]+)', 'float', 1),
            ('root_diameter', r'^\s*272\s*:.*?Fußkreisdurchmesser[^:]*:\s*([\d.]+)', 'float', 1),
            ('root_diameter', r'^\s*272\s*:.*?Fu.*?kreisdurchmesser[^:]*:\s*([\d.]+)', 'float', 1),  # 处理编码
            ('accuracy_grade', r'^\s*1016\s*:.*?:\s*(\d+)', 'int', 1),
            
            # English Patterns & Missing Fields
            ('teeth', r'^\s*22\s*:.*?No\. of teeth[^:]*:\s*(\d+)', 'int', 1),
            ('order_no', r'^\s*7\s*:.*?Order No[^:]*:\s*(.+)', 'str', 1),
            ('condition', r'^\s*10\s*:.*?Condition[^:]*:\s*(.+)', 'str', 1),
            ('location', r'^\s*5\s*:.*?Location[^:]*:\s*(.+)', 'str', 1),
            ('ball_diameter', r'^\s*102\s*:.*?Kugeltaster[^:]*:\s*([\d.]+)', 'float', 1),
            ('ball_diameter', r'^\s*102\s*:.*?Stylus[^:]*:\s*([\d.]+)', 'float', 1),
            ('ball_diameter', r'^\s*102\s*:.*?:\s*([\d.]+)', 'float', 1),
            ('ball_diameter', r'^\s*102\s*:.*?:\s*([\d.]+)', 'float', 1),
            
            # 评价范围 - 改进正则表达式，支持多种格式
            # 格式1: 42 : d1 [mm]..: 47.500
            # 格式2: 42 : d1 [mm]: 47.500
            # 格式3: 42 : d1: 47.500
            # 使用更宽松的模式提取评价范围，不依赖特定行号
            ('profile_eval_start', r'^\s*\d+\s*:.*?d1\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('profile_eval_start', r'^.*?d1\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('profile_eval_end', r'^\s*\d+\s*:.*?d2\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('profile_eval_end', r'^.*?d2\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('helix_eval_start', r'^\s*\d+\s*:.*?b1\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('helix_eval_start', r'^.*?b1\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('helix_eval_end', r'^\s*\d+\s*:.*?b2\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('helix_eval_end', r'^.*?b2\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),

            # 测量范围（起测/终测点）- 使用更宽松的模式，不依赖特定行号
            # Profile: da/de, Helix: ba/be
            ('profile_meas_start', r'^\s*\d+\s*:.*?da\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('profile_meas_start', r'^.*?da\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('profile_meas_end', r'^\s*\d+\s*:.*?de\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('profile_meas_end', r'^.*?de\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('helix_meas_start', r'^\s*\d+\s*:.*?ba\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('helix_meas_start', r'^.*?ba\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('helix_meas_end', r'^\s*\d+\s*:.*?be\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            ('helix_meas_end', r'^.*?be\s*\[?mm\]?\.*:?\s*([-\d.]+)', 'float', 1),
            
            # MDK (Diam. Zweikugelmaß) - 两球测量直径
            # 格式: MDK:47.347 : 0 : .046
            ('mdk_value', r'^\s*111\s*:.*?MDK:([\d.]+)', 'float', 1),
            ('mdk_tolerance', r'^\s*111\s*:.*?MDK:[\d.]+\s*:\s*[\d.]+\s*:\s*([\d.]+)', 'float', 1),
            
            # Winkelabw值（角度偏差值）
            ('winkelabw_profile', r'^\s*\d+\s*:.*?Winkelabw.*?Profil.*?:\s*([-\d.]+)', 'float', 1),
            ('winkelabw_lead', r'^\s*\d+\s*:.*?Winkelabw.*?Flanke.*?:\s*([-\d.]+)', 'float', 1),
            ('winkelabw_profile', r'^.*?Winkelabw.*?Profil.*?:\s*([-\d.]+)', 'float', 1),
            ('winkelabw_lead', r'^.*?Winkelabw.*?Flanke.*?:\s*([-\d.]+)', 'float', 1),
        ]
        
        # 提取数据 - 避免重复覆盖
        for line in lines:
            for key, pattern, data_type, index in patterns:
                # 如果已经提取到该字段，跳过（使用'key in gear_data'检查，允许0.0值）
                if key in gear_data:
                    continue
                    
                match = re.search(pattern, line)
                if match:
                    try:
                        value = match.group(index).strip()
                        if value:
                            if data_type == 'int':
                                gear_data[key] = int(float(value))
                            elif data_type == 'float':
                                gear_data[key] = float(value)
                            else:
                                gear_data[key] = value
                            # 添加调试日志 - 记录评价范围信息
                            if key in ['profile_eval_start', 'profile_eval_end', 'helix_eval_start', 'helix_eval_end',
                                      'profile_meas_start', 'profile_meas_end', 'helix_meas_start', 'helix_meas_end']:
                                logger.info(f"提取评价范围 {key}: {gear_data[key]}")
                            elif key in ['mdk_value', 'mdk_tolerance']:
                                logger.info(f"提取{key}: {gear_data[key]}")
                    except (ValueError, IndexError) as e:
                        logger.debug(f"解析 {key} 失败: {e}")

        # 解析波纹度滤波参数（保存于MKA）
        try:
            filter_match = re.search(r'Filtercharakteristik\s*:.*?FKCHA:\s*([0-9A-F]+)', content, re.IGNORECASE)
            if filter_match:
                fkcha_hex = filter_match.group(1)
                gear_data['ripple_filter_char_raw'] = fkcha_hex
                try:
                    raw_bytes = bytes.fromhex(fkcha_hex)
                    ascii_hint = ''.join(chr(c) if 32 <= c < 127 else ' ' for c in raw_bytes)
                    gear_data['ripple_filter_char_ascii'] = ascii_hint
                    m_ratio = re.search(r'S=(\d{3,9})', ascii_hint)
                    if m_ratio:
                        ratio_val = float(m_ratio.group(1))
                        # 若值过大，尝试缩放（经验：部分版本将数值放大1000倍）
                        if ratio_val > 20000:
                            ratio_val = ratio_val / 1000.0
                        if 1000 <= ratio_val <= 20000:
                            gear_data['ripple_filter_ratio'] = ratio_val
                except Exception:
                    pass
        except Exception:
            pass
        
        # 记录提取到的评价范围信息
        eval_info = {
            'da': gear_data.get('profile_meas_start', 0.0),
            'd1': gear_data.get('profile_eval_start', 0.0),
            'd2': gear_data.get('profile_eval_end', 0.0),
            'de': gear_data.get('profile_meas_end', 0.0),
            'ba': gear_data.get('helix_meas_start', 0.0),
            'b1': gear_data.get('helix_eval_start', 0.0),
            'b2': gear_data.get('helix_eval_end', 0.0),
            'be': gear_data.get('helix_meas_end', 0.0),
        }
        logger.info(f"提取到的评价范围信息: Profile(da={eval_info['da']}, d1={eval_info['d1']}, d2={eval_info['d2']}, de={eval_info['de']}), "
                   f"Helix(ba={eval_info['ba']}, b1={eval_info['b1']}, b2={eval_info['b2']}, be={eval_info['be']})")
                        
        logger.info(f"提取到 {len(gear_data)} 个齿轮基本参数")
        return gear_data
    
    def extract_measurement_data(self, content: str, data_type: str, 
                                 expected_points: int = 915) -> Dict[str, Dict[int, List[float]]]:
        """
        提取测量数据（齿形或齿向）- 改进版，参照原程序逻辑
        
        Args:
            content: 文件内容
            data_type: 数据类型 ('Flankenlinie' 为齿向, 'Profil' 为齿形)
            expected_points: 期望的数据点数
            
        Returns:
            Dict: {'left': {tooth_num: [data]}, 'right': {tooth_num: [data]}}
        """
        measurement_data = {'left': {}, 'right': {}}
        
        # 根据数据类型确定匹配模式和点数
        if data_type == "Flankenlinie":
            pattern_char = r'd'  # 齿向数据匹配 d=
            expected_points = 915  # 齿向数据有915个点
        elif data_type == "Profil":
            pattern_char = r'z'  # 齿形数据匹配 z=
            expected_points = 480  # 齿形数据有480个点
        elif data_type == "Evolventform":
            pattern_char = r'z'  # 齿形数据匹配 z=
            expected_points = 915  # 某些格式有915个点
        elif data_type == "Profile":
            pattern_char = r'z'  # 齿形数据匹配 z=
            expected_points = 480  # 齿形数据有480个点
        else:
            logger.warning(f"未知的数据类型: {data_type}")
            return measurement_data
        
        # 查找数据块的起始位置
        start_patterns = [
            data_type + ": ",
            data_type + ":",
            "TOPOGRAFIE:.*?" + data_type + ":"
        ]
        
        start_index = -1
        for pattern in start_patterns:
            if pattern.endswith("?"):
                # 使用正则搜索
                match = re.search(pattern, content)
                if match:
                    start_index = match.start()
                    break
            else:
                # 简单字符串查找
                start_index = content.find(pattern)
                if start_index != -1:
                    break
        
        if start_index == -1:
            logger.warning(f"未找到{data_type}数据块")
            return measurement_data
        
        # 提取数据块内容
        data_block = content[start_index:]
        
        # 兼容不同格式的正则表达式
        tooth_patterns = [
            # 格式1: Flankenlinie: Zahn-Nr.: 1 rechts / 915 Werte / d= 47.82
            re.compile(rf'Zahn-Nr\.:\s*(\d+)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/?\s*{pattern_char}=\s*([-\d.]+)', re.IGNORECASE),
            # 格式2: Zahn-Nr.: 17 links / 480 Werte d= 104.661
            re.compile(rf'Zahn-Nr\.:\s*(\d+)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*{pattern_char}=\s*([-\d.]+)', re.IGNORECASE),
            # 格式3: Zahn-Nr.: 1 rechts
            re.compile(rf'Zahn-Nr\.:\s*(\d+)\s*(links|rechts)', re.IGNORECASE),
        ]
        
        # 查找所有齿号行
        tooth_matches = []
        actual_points = expected_points
        
        for pattern in tooth_patterns:
            tooth_matches = list(pattern.finditer(data_block))
            if tooth_matches:
                # 如果是完整格式，获取实际点数
                if len(tooth_matches[0].groups()) >= 3:
                    try:
                        reported_points = int(tooth_matches[0].group(3))
                        actual_points = min(reported_points, expected_points)
                        logger.info(f"{data_type}: 报告点数{reported_points}，实际使用{actual_points}点")
                    except (ValueError, IndexError):
                        actual_points = expected_points
                break
        
        if not tooth_matches:
            logger.warning(f"在{data_type}数据块中未找到任何齿数据")
            return measurement_data
        
        # 处理所有匹配的齿
        for i, match in enumerate(tooth_matches):
            tooth_id = int(match.group(1))
            flank = match.group(2).lower()
            start_pos = match.end()
            
            # 确定下一个齿的起始位置
            end_pos = tooth_matches[i + 1].start() if i + 1 < len(tooth_matches) else len(data_block)
            
            # 提取数据点部分
            data_section = data_block[start_pos:end_pos]
            
            # 提取数值 - 使用统一的提取方法
            values = self._extract_numerical_values_unified(data_section, actual_points)
            
            # 存储数据
            if flank == 'links':
                measurement_data['left'][tooth_id] = values
            else:
                measurement_data['right'][tooth_id] = values
        
        logger.info(f"提取{data_type}数据: 左侧{len(measurement_data['left'])}齿, 右侧{len(measurement_data['right'])}齿")
        return measurement_data
    
    def _extract_numerical_values_unified(self, data_section: str, 
                                         expected_points: int) -> List[float]:
        """
        统一的数值提取方法 - 支持915个和480个数据点
        参照原程序逻辑
        
        Args:
            data_section: 数据段内容
            expected_points: 期望的数据点数
            
        Returns:
            List[float]: 数据点列表
        """
        values = []
        
        # 使用更精确的数字提取模式
        number_pattern = re.compile(r'[-+]?\d*\.?\d+')
        numbers = number_pattern.findall(data_section)
        
        # 转换为浮点数
        for num in numbers:
            try:
                # 处理前导点的情况（如 .5 或 -.5）
                if num.startswith('.'):
                    num = '0' + num
                elif num.startswith('-.'):
                    num = num.replace('-.', '-0.')
                    
                values.append(float(num))
            except ValueError:
                continue
            
            # 如果已经收集到足够的点，停止提取
            if len(values) >= expected_points:
                values = values[:expected_points]
                break
        
        # 确保有足够的点
        if len(values) < expected_points:
            # 用0填充不足的点
            logger.warning(f"数据点不足: {len(values)} < {expected_points}，用0填充")
            values.extend([0.0] * (expected_points - len(values)))
        elif len(values) > expected_points:
            values = values[:expected_points]
            logger.info(f"数据点过多: {len(values)} > {expected_points}，截取前{expected_points}个点")
        
        # 异常值处理：检测并替换不合理的大数值
        if len(values) > 0:
            import numpy as np
            
            # 计算中位数（对异常值不敏感）
            median_val = np.median(values)
            
            # 计算中位数绝对偏差 (MAD)
            mad = np.median([abs(x - median_val) for x in values])
            
            # 定义异常值阈值（通常为3-5个MAD）
            threshold = 5.0 * mad if mad > 0 else 1.0
            
            # 统计异常值数量
            outlier_count = 0
            
            # 替换异常值为中位数
            for i in range(len(values)):
                if abs(values[i] - median_val) > threshold:
                    values[i] = median_val
                    outlier_count += 1
            
            if outlier_count > 0:
                logger.info(f"检测并替换了 {outlier_count} 个异常值，使用中位数: {median_val:.3f}")
        
        return values
    
    def extract_pitch_data(self, content: str) -> Dict[str, Dict[int, Dict[str, float]]]:
        """
        提取周节数据
        
        Args:
            content: 文件内容
            
        Returns:
            Dict: {'left': {tooth_num: {'fp': val, 'Fp': val, 'Fr': val}}, 'right': {...}}
        """
        pitch_data = {'left': {}, 'right': {}}
        
        # 查找周节数据段
        left_pattern = r'linke Zahnflanke\s*\n\s*Zahn-Nr\.\s+fp\s+Fp\s+Fr\s*\n((?:\s*\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s*\n?)+)'
        right_pattern = r'rechte Zahnflanke\s*\n\s*Zahn-Nr\.\s+fp\s+Fp\s+Fr\s*\n((?:\s*\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s*\n?)+)'
        
        # 提取左侧数据
        left_match = re.search(left_pattern, content, re.IGNORECASE)
        if left_match:
            pitch_data['left'] = self._parse_pitch_data_block(left_match.group(1))
            
        # 提取右侧数据
        right_match = re.search(right_pattern, content, re.IGNORECASE)
        if right_match:
            pitch_data['right'] = self._parse_pitch_data_block(right_match.group(1))
            
        logger.info(f"提取周节数据: 左侧{len(pitch_data['left'])}齿, 右侧{len(pitch_data['right'])}齿")
        return pitch_data
    
    def _parse_pitch_data_block(self, data_text: str) -> Dict[int, Dict[str, float]]:
        """
        解析周节数据块
        
        Args:
            data_text: 数据文本
            
        Returns:
            Dict: {tooth_num: {'fp': val, 'Fp': val, 'Fr': val}}
        """
        result = {}
        lines = data_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and re.match(r'^\d+', line):
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        tooth_num = int(parts[0])
                        fp = float(parts[1])
                        Fp = float(parts[2])
                        Fr = float(parts[3])
                        
                        result[tooth_num] = {
                            'fp': fp,
                            'Fp': Fp,
                            'Fr': Fr
                        }
                    except (ValueError, IndexError) as e:
                        logger.warning(f"解析周节数据行失败: {line}, {e}")
                        
        return result
    
    def extract_topography_data(self, content: str) -> Dict:
        """
        提取3D形貌数据
        同时解析Profil（z值，齿面高度）和Flankenlinie（d值，齿面直径）数据
        支持两种格式：
        1. TOPOGRAFIE: Zahn-Nr.: 26 /Profil:1 rechts / 480 Werte  / z= 3.5
        2. Profil:  Zahn-Nr.: 1a rechts / 480 Werte  / z= 2.1
        
        Args:
            content: 文件内容
            
        Returns:
            Dict: {tooth_num: {side: {'profiles': {profile_idx: {'z': z_val, 'values': [values]}}, 
                                      'flank_lines': {flank_idx: {'d': d_val, 'values': [values]}}}}}
        """
        topography_data = {}
        
        # 格式1: 带 TOPOGRAFIE 前缀
        # TOPOGRAFIE: Zahn-Nr.: 26 /Profil:1 rechts / 480 Werte  / z= 3.5
        pattern_profil1 = re.compile(r'TOPOGRAFIE:\s*Zahn-Nr\.:\s*(\d+)\s*/Profil:(\d+)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/?\s*z=\s*([-\d.]+)', re.IGNORECASE)
        pattern_flank1 = re.compile(r'TOPOGRAFIE:\s*Zahn-Nr\.:\s*(\d+)\s*/Flankenlinie:(\d+)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/?\s*d=\s*([-\d.]+)', re.IGNORECASE)
        
        # 格式2: 不带 TOPOGRAFIE 前缀
        # Profil:  Zahn-Nr.: 1a rechts / 480 Werte  / z= 2.1
        # Flankenlinie:  Zahn-Nr.: 1a rechts / 480 Werte  / d= 174.822
        pattern_profil2 = re.compile(r'Profil:\s*Zahn-Nr\.:\s*(\d+[a-z]?)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/\s*z=\s*([-\d.]+)', re.IGNORECASE)
        pattern_flank2 = re.compile(r'Flankenlinie:\s*Zahn-Nr\.:\s*(\d+[a-z]?)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/\s*d=\s*([-\d.]+)', re.IGNORECASE)
        
        # 收集所有匹配
        all_matches = []
        for match in pattern_profil1.finditer(content):
            all_matches.append(('profil', 1, match))
        for match in pattern_profil2.finditer(content):
            all_matches.append(('profil', 2, match))
        for match in pattern_flank1.finditer(content):
            all_matches.append(('flank', 1, match))
        for match in pattern_flank2.finditer(content):
            all_matches.append(('flank', 2, match))
        
        # 按位置排序（索引2才是 match 对象）
        all_matches.sort(key=lambda x: x[2].start())
        
        if not all_matches:
            logger.info("未找到形貌数据(TOPOGRAFIE/Profil/Flankenlinie)")
            return topography_data
            
        profil_count = sum(1 for x in all_matches if x[0] == 'profil')
        flank_count = sum(1 for x in all_matches if x[0] == 'flank')
        logger.info(f"找到 {profil_count} 个Profil数据块, {flank_count} 个Flankenlinie数据块")
        
        for i, (data_type, format_type, match) in enumerate(all_matches):
            try:
                if format_type == 1:
                    # 格式1: TOPOGRAFIE: Zahn-Nr.: 26 /Profil:1 rechts / 480 Werte  / z= 3.5
                    tooth_num_str = match.group(1)
                    idx = int(match.group(2))
                    side_str = match.group(3).lower()
                    expected_points = int(match.group(4))
                    if data_type == 'profil':
                        z_val = float(match.group(5))
                    else:
                        d_val = float(match.group(5))
                else:
                    # 格式2: Profil:  Zahn-Nr.: 1a rechts / 480 Werte  / z= 2.1
                    tooth_num_str = match.group(1)
                    side_str = match.group(2).lower()
                    expected_points = int(match.group(3))
                    if data_type == 'profil':
                        z_val = float(match.group(4))
                        # 根据字母后缀确定索引：a=1(底部), b=2(中间), c=3(顶部)
                        if 'a' in tooth_num_str.lower():
                            idx = 1
                        elif 'b' in tooth_num_str.lower():
                            idx = 2
                        elif 'c' in tooth_num_str.lower():
                            idx = 3
                        else:
                            idx = 2  # 默认中间位置
                    else:
                        d_val = float(match.group(4))
                        # 根据字母后缀确定索引
                        if 'a' in tooth_num_str.lower():
                            idx = 1
                        elif 'b' in tooth_num_str.lower():
                            idx = 2
                        elif 'c' in tooth_num_str.lower():
                            idx = 3
                        else:
                            idx = 2
                
                # 提取齿号（去除字母后缀）
                tooth_num_match = re.match(r'(\d+)', tooth_num_str)
                if tooth_num_match:
                    tooth_num = int(tooth_num_match.group(1))
                else:
                    tooth_num = 1
                
                side = 'left' if side_str == 'links' else 'right'
                
                # 确定数据范围
                start_pos = match.end()
                end_pos = all_matches[i+1][2].start() if i + 1 < len(all_matches) else len(content)
                
                data_section = content[start_pos:end_pos]
                
                # 提取数值
                values = self._extract_numerical_values_unified(data_section, expected_points)
                
                # 存储数据
                if tooth_num not in topography_data:
                    topography_data[tooth_num] = {
                        'left': {'profiles': {}, 'flank_lines': {}},
                        'right': {'profiles': {}, 'flank_lines': {}}
                    }
                
                if data_type == 'profil':
                    topography_data[tooth_num][side]['profiles'][idx] = {
                        'z': z_val,
                        'values': values
                    }
                else:  # flank
                    topography_data[tooth_num][side]['flank_lines'][idx] = {
                        'd': d_val,
                        'values': values
                    }
                
            except Exception as e:
                logger.warning(f"解析形貌数据块失败: {e}")
                continue
                
        # 调试输出：显示首个齿的数据结构
        if topography_data:
            first_tooth = sorted(topography_data.keys())[0]
            td = topography_data[first_tooth]
            def _count(side_key: str, key: str) -> int:
                return len(td.get(side_key, {}).get(key, {})) if isinstance(td.get(side_key), dict) else 0
            logger.info(
                f"Topography首齿 {first_tooth}: "
                f"left profiles={_count('left','profiles')}, left flank_lines={_count('left','flank_lines')}, "
                f"right profiles={_count('right','profiles')}, right flank_lines={_count('right','flank_lines')}"
            )
        else:
            logger.info("Topography数据提取结果为空")

        return topography_data


class MKADataValidator:
    """MKA数据验证器"""
    
    @staticmethod
    def validate_gear_data(gear_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证齿轮基本数据
        
        Args:
            gear_data: 齿轮数据
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误消息列表)
        """
        errors = []
        
        # 检查必需字段
        required_fields = ['module', 'teeth']
        for field in required_fields:
            if field not in gear_data or gear_data[field] is None:
                errors.append(f"缺少必需字段: {field}")
                
        # 检查数值范围
        if 'module' in gear_data:
            if gear_data['module'] <= 0 or gear_data['module'] > 100:
                errors.append(f"模数值异常: {gear_data['module']}")
                
        if 'teeth' in gear_data:
            if gear_data['teeth'] < 5 or gear_data['teeth'] > 1000:
                errors.append(f"齿数值异常: {gear_data['teeth']}")
                
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_measurement_data(data: Dict[str, Dict], 
                                  min_teeth: int = 1) -> Tuple[bool, List[str]]:
        """
        验证测量数据
        
        Args:
            data: 测量数据
            min_teeth: 最少齿数
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误消息列表)
        """
        errors = []
        
        if not data or (not data.get('left') and not data.get('right')):
            errors.append("测量数据为空")
            return False, errors
            
        for side in ['left', 'right']:
            if side in data and len(data[side]) < min_teeth:
                errors.append(f"{side}侧数据不足 ({len(data[side])} < {min_teeth})")
                
        return len(errors) == 0, errors


# 便捷函数
def parse_mka_file(file_path: str) -> Dict[str, Any]:
    """
    解析MKA文件的便捷函数
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict: 包含所有解析数据的字典
    """
    parser = MKAFileParser()
    
    try:
        # 读取文件
        content = parser.read_file(file_path)
        
        # 提取齿轮基本数据
        gear_data = parser.extract_gear_basic_data(content)
        
        # 提取测量数据 - 尝试多种关键字
        # 齿形数据：可能是 Profil, Evolventform, Profile 等
        profile_data = parser.extract_measurement_data(content, 'Profil', 480)
        if not profile_data['left'] and not profile_data['right']:
            profile_data = parser.extract_measurement_data(content, 'Evolventform', 915)
        if not profile_data['left'] and not profile_data['right']:
            profile_data = parser.extract_measurement_data(content, 'Profile', 480)
        
        # 齿向数据：通常是 Flankenlinie
        flank_data = parser.extract_measurement_data(content, 'Flankenlinie', 915)
        
        # 周节数据
        pitch_data = parser.extract_pitch_data(content)
        
        # 形貌数据
        topography_data = parser.extract_topography_data(content)
        
        # 验证数据 - 修复teeth字段缺失问题
        if 'teeth' not in gear_data or gear_data['teeth'] == 0:
            # 尝试从周节数据推断齿数
            if pitch_data['left']:
                gear_data['teeth'] = max(pitch_data['left'].keys())
                logger.info(f"从周节数据推断齿数: {gear_data['teeth']}")
            elif pitch_data['right']:
                gear_data['teeth'] = max(pitch_data['right'].keys())
                logger.info(f"从周节数据推断齿数: {gear_data['teeth']}")
        
        # 验证数据
        validator = MKADataValidator()
        valid, errors = validator.validate_gear_data(gear_data)
        if not valid:
            logger.warning(f"齿轮数据验证失败: {errors}")
        
        # 调试：打印MDK数据
        if 'mdk_value' in gear_data or 'mdk_tolerance' in gear_data:
            logger.info(f"MDK数据提取结果: mdk_value={gear_data.get('mdk_value', 'N/A')}, mdk_tolerance={gear_data.get('mdk_tolerance', 'N/A')}")
            
        return {
            'gear_data': gear_data,
            'profile_data': profile_data,
            'flank_data': flank_data,
            'pitch_data': pitch_data,
            'topography_data': topography_data,
            'file_path': file_path
        }
        
    except Exception as e:
        logger.exception(f"解析MKA文件失败: {file_path}")
        raise

