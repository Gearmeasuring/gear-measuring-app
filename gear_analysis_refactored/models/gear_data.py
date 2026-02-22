"""
齿轮数据模型
定义齿轮测量数据的结构
"""
try:
    from dataclasses import dataclass, field
except ImportError:
    # Python 3.6 兼容性
    print("警告: dataclasses不可用，请升级到Python 3.7+或安装: pip install dataclasses")
    # 提供简单的替代实现
    def dataclass(cls):
        return cls
    def field(default_factory=None):
        return default_factory() if default_factory else None

from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class GearBasicInfo:
    """齿轮基本信息"""
    # 测量信息
    program: str = ""
    date: str = ""
    start_time: str = ""
    end_time: str = ""
    operator: str = ""
    location: str = ""
    drawing_no: str = ""
    order_no: str = ""
    type_: str = ""
    customer: str = ""
    condition: str = ""
    
    # 齿轮参数
    module: float = 0.0
    teeth: int = 0
    helix_angle: float = 0.0
    pressure_angle: float = 0.0
    modification_coeff: float = 0.0
    width: float = 0.0
    tip_diameter: float = 0.0
    root_diameter: float = 0.0
    accuracy_grade: int = 5
    ball_diameter: float = 0.0
    
    # MDK (Diam. Zweikugelmaß) - 两球测量直径
    mdk_value: float = 0.0
    mdk_tolerance: float = 0.0

    # 波纹度滤波参数（来自MKA）
    ripple_filter_ratio: float = 0.0
    ripple_filter_char_raw: str = ""
    ripple_filter_char_ascii: str = ""
    
    # 测量范围 (Start, End)
    profile_range_left: tuple = (0.0, 0.0)
    profile_range_right: tuple = (0.0, 0.0)
    lead_range_left: tuple = (0.0, 0.0)
    lead_range_right: tuple = (0.0, 0.0)

    # 测量标记点 (Start, Eval Start, Eval End, End)
    profile_markers_left: tuple = (0.0, 0.0, 0.0, 0.0)
    profile_markers_right: tuple = (0.0, 0.0, 0.0, 0.0)
    lead_markers_left: tuple = (0.0, 0.0, 0.0, 0.0)
    lead_markers_right: tuple = (0.0, 0.0, 0.0, 0.0)
    
    # 评价范围 (Explicit fields for easier access)
    profile_eval_start: float = 0.0
    profile_eval_end: float = 0.0
    helix_eval_start: float = 0.0
    helix_eval_end: float = 0.0
    
    def __str__(self) -> str:
        return f"齿轮[模数:{self.module}, 齿数:{self.teeth}, 精度:{self.accuracy_grade}级]"


@dataclass
class MeasurementData:
    """测量数据"""
    left: Dict[int, List[float]] = field(default_factory=dict)  # 左齿面数据 {齿号: [数据点]}
    right: Dict[int, List[float]] = field(default_factory=dict)  # 右齿面数据
    
    def get_tooth_count(self, side: str = 'both') -> int:
        """获取齿数"""
        if side == 'left':
            return len(self.left)
        elif side == 'right':
            return len(self.right)
        else:
            return max(len(self.left), len(self.right))
    
    def has_data(self) -> bool:
        """是否有数据"""
        return bool(self.left or self.right)


@dataclass
class PitchData:
    """周节数据"""
    left: Dict[int, Dict[str, float]] = field(default_factory=dict)  # {齿号: {'fp': 值, 'Fp': 值, 'Fr': 值}}
    right: Dict[int, Dict[str, float]] = field(default_factory=dict)
    
    def has_data(self) -> bool:
        """是否有数据"""
        return bool(self.left or self.right)


@dataclass
class TopographyData:
    """3D形貌数据"""
    # 新格式: {齿号: {side: {'profiles': {profile_idx: {'z': z_val, 'values': [values]}}, 
    #                        'flank_lines': {flank_idx: {'d': d_val, 'values': [values]}}}}}
    # 旧格式: {齿号: {side: {profile_idx: [values]}}}
    # side: 'left' or 'right'
    data: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    def has_data(self) -> bool:
        """是否有数据"""
        return bool(self.data)
    
    def add_data(self, tooth: int, side: str, profile_idx: int, values: List[float]):
        """添加数据（兼容旧格式）"""
        if tooth not in self.data:
            self.data[tooth] = {'left': {}, 'right': {}}
        
        if side not in self.data[tooth]:
            self.data[tooth][side] = {}
            
        # 检查是否是新格式
        if isinstance(self.data[tooth][side], dict) and ('profiles' in self.data[tooth][side] or 'flank_lines' in self.data[tooth][side]):
            # 新格式，需要转换
            if 'profiles' not in self.data[tooth][side]:
                self.data[tooth][side]['profiles'] = {}
            self.data[tooth][side]['profiles'][profile_idx] = {
                'z': 0.0,  # 默认值
                'values': values
            }
        else:
            # 旧格式，直接存储
            self.data[tooth][side][profile_idx] = values


@dataclass
class ToleranceData:
    """公差数据"""
    # 齿形公差
    F_alpha: float = 0.0
    fH_alpha: float = 0.0
    ff_alpha: float = 0.0
    
    # 齿向公差
    F_beta: float = 0.0
    fH_beta: float = 0.0
    ff_beta: float = 0.0
    
    # 波纹度公差曲线参数
    # R: 允许波深（当 R<0 没有公差曲线）
    # N0: 用于描述公差曲线的常数
    # K: 修正值
    # 公式：公差 = R / (O-1)^N，其中 N = N0 + K / O，O = 阶次
    ripple_tolerance_R: float = 2.0  # 默认值，可根据需要调整
    ripple_tolerance_N0: float = 1.0  # 默认值
    ripple_tolerance_K: float = 0.0   # 默认值
    ripple_tolerance_enabled: bool = True  # 是否启用公差曲线显示
    
    def __str__(self) -> str:
        return f"公差[Fα:{self.F_alpha:.1f}μm, Fβ:{self.F_beta:.1f}μm]"


@dataclass
class DeviationResult:
    """偏差分析结果"""
    # 齿形偏差
    profile_deviation: Dict[str, float] = field(default_factory=dict)
    # 齿向偏差
    flank_deviation: Dict[str, float] = field(default_factory=dict)
    # 评价结果
    grade: int = 5
    is_qualified: bool = True
    
    def get_summary(self) -> str:
        """获取摘要"""
        status = "合格" if self.is_qualified else "不合格"
        return f"精度等级{self.grade}级 - {status}"


@dataclass
class GearMeasurementData:
    """
    完整的齿轮测量数据
    这是主要的数据容器
    """
    # 基本信息
    basic_info: GearBasicInfo = field(default_factory=GearBasicInfo)
    
    # 测量数据
    profile_data: MeasurementData = field(default_factory=MeasurementData)  # 齿形数据
    flank_data: MeasurementData = field(default_factory=MeasurementData)    # 齿向数据
    pitch_data: PitchData = field(default_factory=PitchData)                # 周节数据
    topography_data: 'TopographyData' = field(default_factory=lambda: TopographyData()) # 形貌数据
    
    # 公差和分析结果
    tolerance: ToleranceData = field(default_factory=ToleranceData)
    deviation_result: Optional[DeviationResult] = None
    
    # 元数据
    file_path: str = ""
    load_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.load_time is None:
            self.load_time = datetime.now()
    
    def has_profile_data(self) -> bool:
        """是否有齿形数据"""
        return self.profile_data.has_data()
    
    def has_flank_data(self) -> bool:
        """是否有齿向数据"""
        return self.flank_data.has_data()
    
    def has_pitch_data(self) -> bool:
        """是否有周节数据"""
        return self.pitch_data.has_data()
    
    def get_summary(self) -> str:
        """获取数据摘要"""
        parts = [str(self.basic_info)]
        
        if self.has_profile_data():
            parts.append(f"齿形数据:{self.profile_data.get_tooth_count()}齿")
        
        if self.has_flank_data():
            parts.append(f"齿向数据:{self.flank_data.get_tooth_count()}齿")
        
        if self.has_pitch_data():
            parts.append("周节数据")
        
        return ", ".join(parts)


# 工厂函数
def create_gear_data_from_dict(data_dict: Dict[str, Any]) -> GearMeasurementData:
    """
    从字典创建齿轮测量数据对象
    
    Args:
        data_dict: 包含所有数据的字典
        
    Returns:
        GearMeasurementData: 齿轮测量数据对象
    """
    # 创建基本信息
    gear_data = data_dict.get('gear_data', {})
    # 组装 markers/range（若文件未提供则保留0）
    da = float(gear_data.get('profile_meas_start', 0.0) or 0.0)
    de = float(gear_data.get('profile_meas_end', 0.0) or 0.0)
    d1 = float(gear_data.get('profile_eval_start', 0.0) or 0.0)
    d2 = float(gear_data.get('profile_eval_end', 0.0) or 0.0)
    ba = float(gear_data.get('helix_meas_start', 0.0) or 0.0)
    be = float(gear_data.get('helix_meas_end', 0.0) or 0.0)
    b1 = float(gear_data.get('helix_eval_start', 0.0) or 0.0)
    b2 = float(gear_data.get('helix_eval_end', 0.0) or 0.0)
    
    # 记录构造的markers信息
    from gear_analysis_refactored.config.logging_config import logger
    logger.info(f"构造markers: Profile(da={da}, d1={d1}, d2={d2}, de={de}), Helix(ba={ba}, b1={b1}, b2={b2}, be={be})")

    # 如果 program 为空，使用文件名作为备选
    program = gear_data.get('program', '')
    if not program:
        file_path = data_dict.get('file_path', '')
        if file_path:
            import os
            program = os.path.basename(file_path)
    
    basic_info = GearBasicInfo(
        program=program,
        date=gear_data.get('date', ''),
        start_time=gear_data.get('start_time', ''),
        end_time=gear_data.get('end_time', ''),
        operator=gear_data.get('operator', ''),
        location=gear_data.get('location', ''),
        drawing_no=gear_data.get('drawing_no', ''),
        order_no=gear_data.get('order_no', ''),
        type_=gear_data.get('type', ''),
        customer=gear_data.get('customer', ''),
        condition=gear_data.get('condition', ''),
        module=gear_data.get('module', 0.0),
        teeth=gear_data.get('teeth', 0),
        helix_angle=gear_data.get('helix_angle', 0.0),
        pressure_angle=gear_data.get('pressure_angle', 0.0),
        modification_coeff=gear_data.get('modification_coeff', 0.0),
        width=gear_data.get('width', 0.0),
        tip_diameter=gear_data.get('tip_diameter', 0.0),
        root_diameter=gear_data.get('root_diameter', 0.0),
        accuracy_grade=gear_data.get('accuracy_grade', 5),

        ball_diameter=gear_data.get('ball_diameter', 0.0),
        profile_eval_start=gear_data.get('profile_eval_start', 0.0),
        profile_eval_end=gear_data.get('profile_eval_end', 0.0),
        helix_eval_start=gear_data.get('helix_eval_start', 0.0),
        helix_eval_end=gear_data.get('helix_eval_end', 0.0),
        mdk_value=gear_data.get('mdk_value', 0.0),
        mdk_tolerance=gear_data.get('mdk_tolerance', 0.0),
        ripple_filter_ratio=gear_data.get('ripple_filter_ratio', 0.0),
        ripple_filter_char_raw=gear_data.get('ripple_filter_char_raw', ''),
        ripple_filter_char_ascii=gear_data.get('ripple_filter_char_ascii', ''),

        # ranges
        profile_range_left=(da, de),
        profile_range_right=(da, de),
        lead_range_left=(ba, be),
        lead_range_right=(ba, be),

        # markers (Start, Eval Start, Eval End, End)
        profile_markers_left=(da, d1, d2, de),
        profile_markers_right=(da, d1, d2, de),
        lead_markers_left=(ba, b1, b2, be),
        lead_markers_right=(ba, b1, b2, be),
    )
    
    # 创建测量数据
    profile_dict = data_dict.get('profile_data', {})
    profile_data = MeasurementData(
        left=profile_dict.get('left', {}),
        right=profile_dict.get('right', {})
    )
    
    flank_dict = data_dict.get('flank_data', {})
    flank_data = MeasurementData(
        left=flank_dict.get('left', {}),
        right=flank_dict.get('right', {})
    )
    
    pitch_dict = data_dict.get('pitch_data', {})
    pitch_data = PitchData(
        left=pitch_dict.get('left', {}),
        right=pitch_dict.get('right', {})
    )
    
    # 创建形貌数据
    topography_dict = data_dict.get('topography_data', {})
    topography_data = TopographyData(
        data=topography_dict
    )
    
    # 创建完整对象
    return GearMeasurementData(
        basic_info=basic_info,
        profile_data=profile_data,
        flank_data=flank_data,
        pitch_data=pitch_data,
        topography_data=topography_data,
        file_path=data_dict.get('file_path', '')
    )

