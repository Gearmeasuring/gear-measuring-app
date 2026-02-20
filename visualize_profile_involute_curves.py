"""
可视化展示齿形数据按渐开线极角合并后的曲线
展示左齿形、右齿形、合并后的0-360度曲线

算法说明:
1. 测量点是沿着渐开线分布的
2. 根据渐开线理论计算每个点的极角: θ = inv(α) = tan(α) - α
3. 找出起评点(d1)，算出起始极角
4. 以此类推，把每一个测量点的极角都算出来，直到终评点(d2)极角
5. 齿1=0°，齿2=节距角，齿3=2*节距角
6. 最终角度 = 齿序号*节距角 + 测量点极角（相对于起评点）
7. y轴为测量值，组成0到360度的一周曲线
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def calculate_involute_polar_angle(radius: float, base_radius: float) -> float:
    """计算渐开线上某点的极角（渐开线函数）
    
    渐开线极角公式: θ = inv(α) = tan(α) - α
    其中 α 为该点的压力角，由 cos(α) = rb/r 求得
    
    Args:
        radius: 当前点的半径 (mm)
        base_radius: 基圆半径 (mm)
    
    Returns:
        极角（弧度），从基圆开始计算
    """
    if radius <= base_radius or base_radius <= 0:
        return 0.0
    
    cos_alpha = base_radius / radius
    cos_alpha = np.clip(cos_alpha, -1.0, 1.0)
    
    alpha = np.arccos(cos_alpha)
    inv_alpha = np.tan(alpha) - alpha
    
    return inv_alpha


def calculate_involute_polar_angle_array(radii: np.ndarray, base_radius: float) -> np.ndarray:
    """计算渐开线上多个点的极角数组"""
    radii = np.array(radii, dtype=float)
    polar_angles = np.zeros_like(radii)
    
    valid_mask = radii > base_radius
    if base_radius > 0:
        cos_alpha = np.zeros_like(radii)
        cos_alpha[valid_mask] = base_radius / radii[valid_mask]
        cos_alpha = np.clip(cos_alpha, -1.0, 1.0)
        
        alpha = np.zeros_like(radii)
        alpha[valid_mask] = np.arccos(cos_alpha[valid_mask])
        
        polar_angles[valid_mask] = np.tan(alpha[valid_mask]) - alpha[valid_mask]
    
    return polar_angles


def remove_slope_and_crowning(data: np.ndarray, x: np.ndarray = None) -> tuple:
    """去除斜率偏差和鼓形
    
    分两步处理：
    1. 先用二元二次多项式（抛物线）去除鼓形
    2. 再用一元一次多项式（线性）去除斜率偏差
    
    Args:
        data: 测量数据数组
        x: x坐标数组，如果为None则使用索引
    
    Returns:
        tuple: (去除斜率和鼓形后的数据, (鼓形系数, 斜率系数))
    """
    if len(data) < 3:
        return data, (None, None)
    
    data = np.array(data, dtype=float)
    n = len(data)
    
    if x is None:
        x = np.arange(n, dtype=float)
    else:
        x = np.array(x, dtype=float)
    
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    crowning_coeffs = np.polyfit(x_norm, data, 2)
    crowning_curve = np.polyval(crowning_coeffs, x_norm)
    data_after_crowning = data - crowning_curve
    
    slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
    slope_curve = np.polyval(slope_coeffs, x_norm)
    corrected_data = data_after_crowning - slope_curve
    
    return corrected_data, (crowning_coeffs, slope_coeffs)


def remove_crowning_only(data: np.ndarray, x: np.ndarray = None) -> tuple:
    """仅去除鼓形（二元二次多项式）
    
    Args:
        data: 测量数据数组
        x: x坐标数组，如果为None则使用索引
    
    Returns:
        tuple: (去除鼓形后的数据, 鼓形系数)
    """
    if len(data) < 3:
        return data, None
    
    data = np.array(data, dtype=float)
    n = len(data)
    
    if x is None:
        x = np.arange(n, dtype=float)
    else:
        x = np.array(x, dtype=float)
    
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    crowning_coeffs = np.polyfit(x_norm, data, 2)
    crowning_curve = np.polyval(crowning_coeffs, x_norm)
    corrected_data = data - crowning_curve
    
    return corrected_data, crowning_coeffs


def remove_slope_only(data: np.ndarray, x: np.ndarray = None) -> tuple:
    """仅去除斜率偏差（一元一次多项式）
    
    Args:
        data: 测量数据数组
        x: x坐标数组，如果为None则使用索引
    
    Returns:
        tuple: (去除斜率后的数据, 斜率系数)
    """
    if len(data) < 2:
        return data, None
    
    data = np.array(data, dtype=float)
    n = len(data)
    
    if x is None:
        x = np.arange(n, dtype=float)
    else:
        x = np.array(x, dtype=float)
    
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    slope_coeffs = np.polyfit(x_norm, data, 1)
    slope_curve = np.polyval(slope_coeffs, x_norm)
    corrected_data = data - slope_curve
    
    return corrected_data, slope_coeffs


def fit_sine_wave_least_squares(angles: np.ndarray, values: np.ndarray, order: int) -> dict:
    """使用最小二乘法拟合指定阶次的正弦波
    
    拟合模型: y = A * sin(order * θ + φ) = A*sin(φ)*cos(order*θ) + A*cos(φ)*sin(order*θ)
    
    Args:
        angles: 角度数组（弧度）
        values: 测量值数组
        order: 阶次（正弦波的周期数）
    
    Returns:
        dict: {
            'amplitude': 振幅,
            'phase': 相位（弧度）,
            'fitted': 拟合值数组,
            'residual': 残差数组,
            'coefficients': (a, b) 系数
        }
    """
    angles = np.array(angles, dtype=float)
    values = np.array(values, dtype=float)
    
    cos_term = np.cos(order * angles)
    sin_term = np.sin(order * angles)
    
    A = np.column_stack([cos_term, sin_term])
    
    coeffs, residuals, rank, s = np.linalg.lstsq(A, values, rcond=None)
    
    a, b = coeffs[0], coeffs[1]
    
    amplitude = np.sqrt(a**2 + b**2)
    phase = np.arctan2(a, b)
    
    fitted = a * cos_term + b * sin_term
    residual = values - fitted
    
    return {
        'amplitude': amplitude,
        'phase': phase,
        'fitted': fitted,
        'residual': residual,
        'coefficients': (a, b)
    }


def find_max_amplitude_order(angles: np.ndarray, values: np.ndarray, 
                              max_order: int = 50, min_order: int = 1) -> dict:
    """寻找振幅最大的阶次
    
    Args:
        angles: 角度数组（弧度）
        values: 测量值数组
        max_order: 最大搜索阶次
        min_order: 最小搜索阶次
    
    Returns:
        dict: {
            'order': 最大振幅对应的阶次,
            'amplitude': 最大振幅,
            'fit_result': 拟合结果
        }
    """
    best_order = min_order
    best_amplitude = 0
    best_result = None
    
    for order in range(min_order, max_order + 1):
        result = fit_sine_wave_least_squares(angles, values, order)
        if result['amplitude'] > best_amplitude:
            best_amplitude = result['amplitude']
            best_order = order
            best_result = result
    
    return {
        'order': best_order,
        'amplitude': best_amplitude,
        'fit_result': best_result
    }


def iterative_sine_decomposition(angles: np.ndarray, values: np.ndarray, 
                                  num_components: int = 10, max_order: int = 50) -> dict:
    """迭代正弦波分解算法
    
    通过最小二乘法分解阶次最大的正弦波，从原始信号中移除已提取的最大阶次正弦波，
    对剩余信号重复上述过程，直到提取出第十个较大的阶次。
    
    Args:
        angles: 角度数组（弧度），范围0-2π
        values: 测量值数组
        num_components: 要提取的分量数量（默认10）
        max_order: 最大搜索阶次
    
    Returns:
        dict: {
            'orders': 提取的阶次列表,
            'amplitudes': 对应的振幅列表,
            'phases': 对应的相位列表,
            'components': 各分量拟合值列表,
            'residual': 最终残差,
            'original': 原始信号,
            'reconstructed': 重构信号
        }
    """
    angles = np.array(angles, dtype=float)
    residual = np.array(values, dtype=float)
    
    orders = []
    amplitudes = []
    phases = []
    components = []
    extracted_orders = set()
    
    for i in range(num_components):
        result = find_max_amplitude_order(angles, residual, max_order, min_order=1)
        
        order = result['order']
        while order in extracted_orders and order < max_order:
            order += 1
        if order > max_order:
            break
        
        extracted_orders.add(order)
        
        fit_result = fit_sine_wave_least_squares(angles, residual, order)
        
        orders.append(order)
        amplitudes.append(fit_result['amplitude'])
        phases.append(fit_result['phase'])
        components.append(fit_result['fitted'])
        
        residual = fit_result['residual']
    
    reconstructed = np.zeros_like(values)
    for comp in components:
        reconstructed += comp
    
    return {
        'orders': np.array(orders),
        'amplitudes': np.array(amplitudes),
        'phases': np.array(phases),
        'components': components,
        'residual': residual,
        'original': np.array(values),
        'reconstructed': reconstructed
    }


def analyze_spectrum_with_iterative_decomposition(angles_deg: np.ndarray, values: np.ndarray,
                                                    num_components: int = 10, 
                                                    max_order: int = 50) -> dict:
    """使用迭代分解法分析频谱
    
    Args:
        angles_deg: 角度数组（度），范围0-360
        values: 测量值数组
        num_components: 要提取的分量数量
        max_order: 最大搜索阶次
    
    Returns:
        dict: 分解结果和频谱信息
    """
    angles_rad = np.radians(angles_deg)
    
    result = iterative_sine_decomposition(angles_rad, values, num_components, max_order)
    
    return result


def calculate_high_order_undulation(spectrum_result: dict, ze: int) -> dict:
    """计算高阶波纹度（波数≥ZE的分量）
    
    高阶波纹度评价方式：筛选出波数≥ZE的所有分量，计算其合成振幅
    
    Args:
        spectrum_result: 迭代分解结果
        ze: 高阶起始波数（High Order Start）
    
    Returns:
        dict: {
            'high_order_indices': 高阶分量索引列表,
            'high_order_waves': 高阶波数列表,
            'high_order_amplitudes': 高阶振幅列表,
            'high_order_phases': 高阶相位列表,
            'total_high_order_amplitude': 高阶总振幅,
            'high_order_rms': 高阶RMS值,
            'high_order_reconstructed': 高阶重构信号
        }
    """
    orders = spectrum_result['orders']
    amplitudes = spectrum_result['amplitudes']
    phases = spectrum_result['phases']
    components = spectrum_result['components']
    
    high_order_mask = orders >= ze
    
    high_order_indices = np.where(high_order_mask)[0]
    high_order_waves = orders[high_order_mask]
    high_order_amplitudes = amplitudes[high_order_mask]
    high_order_phases = phases[high_order_mask]
    
    high_order_reconstructed = np.zeros_like(spectrum_result['original'])
    for idx in high_order_indices:
        if idx < len(components):
            high_order_reconstructed += components[idx]
    
    total_amplitude = np.sum(high_order_amplitudes)
    
    rms = np.sqrt(np.mean(high_order_reconstructed ** 2))
    
    return {
        'high_order_indices': high_order_indices,
        'high_order_waves': high_order_waves,
        'high_order_amplitudes': high_order_amplitudes,
        'high_order_phases': high_order_phases,
        'total_high_order_amplitude': total_amplitude,
        'high_order_rms': rms,
        'high_order_reconstructed': high_order_reconstructed,
        'ze': ze
    }


def remove_slope_and_crowning_from_profile(
    profile_data: dict, 
    side: str = 'left'
) -> dict:
    """对齿形数据去除斜率偏差和鼓形
    
    对每个齿的数据单独进行处理
    
    Args:
        profile_data: 齿形数据 {'left': {...}, 'right': {...}}
        side: 齿面 ('left' 或 'right')
    
    Returns:
        dict: 处理后的数据，包含原始数据和处理后的数据
    """
    if side not in profile_data:
        return {'corrected_data': {}, 'coefficients': {}}
    
    side_data = profile_data[side]
    corrected_data = {}
    coefficients_dict = {}
    
    for tooth_id, values in side_data.items():
        if values and len(values) > 0:
            corrected_values, coeffs = remove_slope_and_crowning(np.array(values))
            corrected_data[tooth_id] = corrected_values
            coefficients_dict[tooth_id] = coeffs
    
    return {
        'corrected_data': corrected_data,
        'coefficients': coefficients_dict
    }


def calculate_full_rotation_curve_from_profile(
    profile_data: dict,
    teeth_count: int,
    module: float,
    pressure_angle: float,
    eval_start_diameter: float = None,
    eval_end_diameter: float = None,
    meas_start_diameter: float = None,
    meas_end_diameter: float = None,
    side: str = 'left',
    base_diameter: float = None,
    use_eval_range_only: bool = True
) -> dict:
    """从齿形数据计算完整旋转角度曲线
    
    算法:
    1. 计算基圆半径: rb = m * z * cos(α) / 2
    2. 计算起评点(d1)和终评点(d2)对应的渐开线极角
    3. 每个测量点的极角在起评点和终评点极角之间分布
    4. 最终角度计算:
       - 右齿形: 齿序号*节距角 + 测量点极角（从齿顶开始排列）
       - 左齿形: 齿序号*节距角 - 测量点极角（从齿顶开始排列）
    5. 组成0-360度的完整曲线
    
    Args:
        use_eval_range_only: 是否只使用评价范围内的数据点
        meas_start_diameter: 测量起始点直径
        meas_end_diameter: 测量终止点直径
        side: 齿面 ('left' 或 'right')
    """
    if side not in profile_data:
        return {'angles': np.array([]), 'values': np.array([]),
                'tooth_indices': np.array([]), 'point_indices': np.array([])}
    
    side_data = profile_data[side]
    if not side_data:
        return {'angles': np.array([]), 'values': np.array([]),
                'tooth_indices': np.array([]), 'point_indices': np.array([])}
    
    pitch_radius = module * teeth_count / 2.0
    if base_diameter and base_diameter > 0:
        base_radius = base_diameter / 2.0
    else:
        base_radius = pitch_radius * np.cos(np.radians(pressure_angle))
    
    pitch_angle_deg = 360.0 / teeth_count
    
    all_angles = []
    all_values = []
    all_tooth_indices = []
    all_point_indices = []
    
    sorted_teeth = sorted(side_data.keys())
    
    first_tooth_values = side_data[sorted_teeth[0]]
    num_points = len(first_tooth_values)
    
    if meas_start_diameter and meas_start_diameter > 0 and meas_end_diameter and meas_end_diameter > 0:
        meas_start_radius = meas_start_diameter / 2.0
        meas_end_radius = meas_end_diameter / 2.0
        meas_start_polar = calculate_involute_polar_angle(meas_start_radius, base_radius)
        meas_end_polar = calculate_involute_polar_angle(meas_end_radius, base_radius)
    else:
        meas_start_radius = base_radius * 1.05
        meas_end_radius = pitch_radius * 1.15
        meas_start_polar = calculate_involute_polar_angle(meas_start_radius, base_radius)
        meas_end_polar = calculate_involute_polar_angle(meas_end_radius, base_radius)
    
    if eval_start_diameter and eval_start_diameter > 0 and eval_end_diameter and eval_end_diameter > 0:
        eval_start_radius = eval_start_diameter / 2.0
        eval_end_radius = eval_end_diameter / 2.0
        eval_start_polar = calculate_involute_polar_angle(eval_start_radius, base_radius)
        eval_end_polar = calculate_involute_polar_angle(eval_end_radius, base_radius)
    else:
        eval_start_polar = meas_start_polar
        eval_end_polar = meas_end_polar
    
    start_polar_angle = eval_start_polar
    end_polar_angle = eval_end_polar
    
    point_polar_angles = np.linspace(meas_start_polar, meas_end_polar, num_points)
    
    if use_eval_range_only:
        eval_start_idx = np.argmin(np.abs(point_polar_angles - eval_start_polar))
        eval_end_idx = np.argmin(np.abs(point_polar_angles - eval_end_polar)) + 1
        
        if eval_start_idx >= eval_end_idx:
            eval_start_idx = 0
            eval_end_idx = num_points
    else:
        eval_start_idx = 0
        eval_end_idx = num_points
    
    point_polar_angles_deg = np.degrees(point_polar_angles - start_polar_angle)
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or (hasattr(tooth_values, '__len__') and len(tooth_values) == 0):
            continue
        
        tooth_values = np.array(tooth_values)
        actual_points = len(tooth_values)
        
        if use_eval_range_only:
            current_eval_start = int(eval_start_idx * actual_points / num_points)
            current_eval_end = int(eval_end_idx * actual_points / num_points)
            
            tooth_values = tooth_values[current_eval_start:current_eval_end]
            actual_points = len(tooth_values)
            
            current_polar_angles = np.linspace(meas_start_polar, meas_end_polar, len(side_data[tooth_id]))
            current_polar_angles = current_polar_angles[current_eval_start:current_eval_end]
            current_polar_angles_deg = np.degrees(current_polar_angles - start_polar_angle)
        else:
            current_polar_angles = np.linspace(meas_start_polar, meas_end_polar, actual_points)
            current_polar_angles_deg = np.degrees(current_polar_angles - start_polar_angle)
        
        tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
        if tooth_index < 0:
            tooth_index = 0
        if tooth_index >= teeth_count:
            tooth_index = teeth_count - 1
        
        tooth_base_angle = tooth_index * pitch_angle_deg
        
        if side == 'left':
            final_angles = tooth_base_angle - current_polar_angles_deg
        else:
            final_angles = tooth_base_angle + current_polar_angles_deg
        
        all_angles.extend(final_angles.tolist())
        all_values.extend(tooth_values.tolist())
        all_tooth_indices.extend([tooth_id] * actual_points)
        all_point_indices.extend(list(range(actual_points)))
    
    if not all_angles:
        return {'angles': np.array([]), 'values': np.array([]),
                'tooth_indices': np.array([]), 'point_indices': np.array([])}
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    all_tooth_indices = np.array(all_tooth_indices)
    all_point_indices = np.array(all_point_indices)
    
    all_angles = all_angles % 360.0
    all_angles[all_angles < 0] += 360.0
    
    sort_indices = np.argsort(all_angles)
    all_angles = all_angles[sort_indices]
    all_values = all_values[sort_indices]
    all_tooth_indices = all_tooth_indices[sort_indices]
    all_point_indices = all_point_indices[sort_indices]
    
    return {
        'angles': all_angles,
        'values': all_values,
        'tooth_indices': all_tooth_indices,
        'point_indices': all_point_indices,
        'start_polar_angle_deg': np.degrees(start_polar_angle),
        'end_polar_angle_deg': np.degrees(end_polar_angle),
        'polar_angle_range_deg': np.degrees(end_polar_angle - start_polar_angle)
    }


def main():
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    
    print(f"读取MKA文件: {mka_file}")
    
    from gear_analysis_refactored.utils.file_parser import MKAFileParser
    
    parser = MKAFileParser()
    content = parser.read_file(mka_file)
    gear_data = parser.extract_gear_basic_data(content)
    
    if gear_data is None:
        print("解析MKA文件失败")
        return
    
    module = gear_data.get('module', 0)
    teeth_count = gear_data.get('teeth', 0)
    pressure_angle = gear_data.get('pressure_angle', 20)
    base_diameter = gear_data.get('base_diameter', 0)
    
    eval_start_diameter = gear_data.get('profile_eval_start', 0)
    eval_end_diameter = gear_data.get('profile_eval_end', 0)
    meas_start_diameter = gear_data.get('profile_meas_start', 0)
    meas_end_diameter = gear_data.get('profile_meas_end', 0)
    
    profile_data = parser.extract_measurement_data(content, 'Profil')
    
    measurement_data = type('MeasurementData', (), {
        'basic_info': type('BasicInfo', (), {
            'module': module,
            'teeth': teeth_count,
            'pressure_angle': pressure_angle,
            'base_diameter': base_diameter
        })(),
        'profile_data': profile_data
    })()
    
    basic_info = measurement_data.basic_info
    module = basic_info.module
    teeth_count = basic_info.teeth
    pressure_angle = basic_info.pressure_angle
    base_diameter = getattr(basic_info, 'base_diameter', 0)
    
    print(f"\n齿轮参数:")
    print(f"  模数: {module} mm")
    print(f"  齿数: {teeth_count}")
    print(f"  压力角: {pressure_angle}°")
    print(f"  基圆直径: {base_diameter} mm")
    
    pitch_radius = module * teeth_count / 2.0
    if base_diameter > 0:
        base_radius = base_diameter / 2.0
    else:
        base_radius = pitch_radius * np.cos(np.radians(pressure_angle))
    pitch_angle_deg = 360.0 / teeth_count
    
    print(f"  分度圆半径: {pitch_radius:.3f} mm")
    print(f"  基圆半径: {base_radius:.3f} mm")
    print(f"  节距角: {pitch_angle_deg:.2f}°")
    
    print(f"\n测量范围:")
    print(f"  测量起始点(da): {meas_start_diameter} mm")
    print(f"  测量终止点(de): {meas_end_diameter} mm")
    print(f"\n评价范围:")
    print(f"  起评点直径(d1): {eval_start_diameter} mm")
    print(f"  终评点直径(d2): {eval_end_diameter} mm")
    
    if eval_start_diameter > 0 and eval_end_diameter > 0:
        start_polar = calculate_involute_polar_angle(eval_start_diameter/2, base_radius)
        end_polar = calculate_involute_polar_angle(eval_end_diameter/2, base_radius)
        print(f"  起评点极角: {np.degrees(start_polar):.4f}°")
        print(f"  终评点极角: {np.degrees(end_polar):.4f}°")
        print(f"  极角范围: {np.degrees(end_polar - start_polar):.4f}°")
    
    profile_data = measurement_data.profile_data
    
    print(f"\n齿形数据:")
    print(f"  左齿面齿数: {len(profile_data.get('left', {}))}")
    print(f"  右齿面齿数: {len(profile_data.get('right', {}))}")
    
    if len(profile_data.get('left', {})) > 0:
        first_tooth = list(profile_data['left'].keys())[0]
        print(f"  每齿测量点数: {len(profile_data['left'][first_tooth])}")
    
    print(f"\n步骤1: 提取评价范围内数据...")
    
    def extract_eval_range_data(profile_data, eval_start_diameter, eval_end_diameter, 
                                 meas_start_diameter, meas_end_diameter, base_radius, num_points):
        """提取评价范围内的数据"""
        result = {'left': {}, 'right': {}}
        
        if meas_start_diameter > 0 and meas_end_diameter > 0:
            meas_start_polar = calculate_involute_polar_angle(meas_start_diameter / 2.0, base_radius)
            meas_end_polar = calculate_involute_polar_angle(meas_end_diameter / 2.0, base_radius)
        else:
            return profile_data
        
        if eval_start_diameter > 0 and eval_end_diameter > 0:
            eval_start_polar = calculate_involute_polar_angle(eval_start_diameter / 2.0, base_radius)
            eval_end_polar = calculate_involute_polar_angle(eval_end_diameter / 2.0, base_radius)
        else:
            return profile_data
        
        point_polar_angles = np.linspace(meas_start_polar, meas_end_polar, num_points)
        eval_start_idx = np.argmin(np.abs(point_polar_angles - eval_start_polar))
        eval_end_idx = np.argmin(np.abs(point_polar_angles - eval_end_polar)) + 1
        
        if eval_start_idx >= eval_end_idx:
            eval_start_idx = 0
            eval_end_idx = num_points
        
        for side in ['left', 'right']:
            if side not in profile_data:
                continue
            for tooth_id, values in profile_data[side].items():
                if values and len(values) > 0:
                    actual_points = len(values)
                    current_eval_start = int(eval_start_idx * actual_points / num_points)
                    current_eval_end = int(eval_end_idx * actual_points / num_points)
                    result[side][tooth_id] = values[current_eval_start:current_eval_end]
        
        return result
    
    if len(profile_data.get('left', {})) > 0:
        first_tooth = list(profile_data['left'].keys())[0]
        num_points = len(profile_data['left'][first_tooth])
        
        eval_range_data = extract_eval_range_data(
            profile_data, eval_start_diameter, eval_end_diameter,
            meas_start_diameter, meas_end_diameter, base_radius, num_points
        )
        
        if len(eval_range_data.get('left', {})) > 0:
            first_tooth_eval = list(eval_range_data['left'].keys())[0]
            print(f"  评价范围内每齿点数: {len(eval_range_data['left'][first_tooth_eval])}")
    
    print(f"\n步骤2: 去除斜率偏差和鼓形...")
    print(f"  方法: 先去除鼓形(二元二次多项式)，再去除斜率偏差(一元一次多项式)")
    
    left_corrected = remove_slope_and_crowning_from_profile(eval_range_data, 'left')
    right_corrected = remove_slope_and_crowning_from_profile(eval_range_data, 'right')
    
    corrected_profile_data = {
        'left': left_corrected['corrected_data'],
        'right': right_corrected['corrected_data']
    }
    
    print(f"  左齿面已处理 {len(left_corrected['corrected_data'])} 个齿")
    print(f"  右齿面已处理 {len(right_corrected['corrected_data'])} 个齿")
    
    print(f"\n步骤3: 计算渐开线极角并合并曲线...")
    
    left_curve = calculate_full_rotation_curve_from_profile(
        corrected_profile_data, teeth_count, module, pressure_angle,
        eval_start_diameter=eval_start_diameter,
        eval_end_diameter=eval_end_diameter,
        meas_start_diameter=meas_start_diameter,
        meas_end_diameter=meas_end_diameter,
        side='left', base_diameter=base_diameter,
        use_eval_range_only=False
    )
    
    right_curve = calculate_full_rotation_curve_from_profile(
        corrected_profile_data, teeth_count, module, pressure_angle,
        eval_start_diameter=eval_start_diameter,
        eval_end_diameter=eval_end_diameter,
        meas_start_diameter=meas_start_diameter,
        meas_end_diameter=meas_end_diameter,
        side='right', base_diameter=base_diameter,
        use_eval_range_only=False
    )
    
    print(f"\n计算结果:")
    print(f"  左齿形数据点数: {len(left_curve['angles'])}")
    print(f"  右齿形数据点数: {len(right_curve['angles'])}")
    
    print(f"\n步骤4: 迭代正弦波分解（最小二乘法）...")
    print(f"  提取前10个较大阶次分量")
    
    if len(left_curve['angles']) > 0:
        unique_angles, unique_indices = np.unique(np.round(left_curve['angles'], 3), return_index=True)
        unique_values = left_curve['values'][unique_indices]
        
        max_order = 5 * teeth_count
        num_interp_points = max(360, 2 * max_order + 10)
        interp_angles = np.linspace(0, 360, num_interp_points)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        left_spectrum = analyze_spectrum_with_iterative_decomposition(
            interp_angles, interp_values, num_components=10, max_order=max_order
        )
        
        print(f"\n  左齿形频谱分析结果:")
        print(f"  {'每转波数':>8} {'振幅(μm)':>12} {'相位(°)':>10}")
        print(f"  {'-'*32}")
        for i, (order, amp, phase) in enumerate(zip(left_spectrum['orders'], 
                                                      left_spectrum['amplitudes'],
                                                      left_spectrum['phases'])):
            print(f"  {order:>8} {amp:>12.4f} {np.degrees(phase):>10.2f}")
    
    if len(right_curve['angles']) > 0:
        unique_angles_r, unique_indices_r = np.unique(np.round(right_curve['angles'], 3), return_index=True)
        unique_values_r = right_curve['values'][unique_indices_r]
        
        max_order_r = 5 * teeth_count
        num_interp_points_r = max(360, 2 * max_order_r + 10)
        interp_angles_r = np.linspace(0, 360, num_interp_points_r)
        interp_values_r = np.interp(interp_angles_r, unique_angles_r, unique_values_r, period=360)
        
        right_spectrum = analyze_spectrum_with_iterative_decomposition(
            interp_angles_r, interp_values_r, num_components=10, max_order=max_order_r
        )
        
        print(f"\n  右齿形频谱分析结果:")
        print(f"  {'每转波数':>8} {'振幅(μm)':>12} {'相位(°)':>10}")
        print(f"  {'-'*32}")
        for i, (order, amp, phase) in enumerate(zip(right_spectrum['orders'], 
                                                      right_spectrum['amplitudes'],
                                                      right_spectrum['phases'])):
            print(f"  {order:>8} {amp:>12.4f} {np.degrees(phase):>10.2f}")
    
    print(f"\n步骤5: 高阶波纹度评价（波数≥ZE）...")
    ze = teeth_count
    print(f"  ZE = {ze} (总齿数，高阶起始波数)")
    
    if len(left_curve['angles']) > 0 and 'left_spectrum' in dir():
        left_high_order = calculate_high_order_undulation(left_spectrum, ze)
        
        print(f"\n  左齿形高阶波纹度评价结果:")
        print(f"  高阶波数(≥{ze}): {list(left_high_order['high_order_waves'])}")
        print(f"  高阶振幅: {[f'{a:.4f}' for a in left_high_order['high_order_amplitudes']]}")
        print(f"  高阶总振幅: {left_high_order['total_high_order_amplitude']:.4f} μm")
        print(f"  高阶RMS值: {left_high_order['high_order_rms']:.4f} μm")
    
    if len(right_curve['angles']) > 0 and 'right_spectrum' in dir():
        right_high_order = calculate_high_order_undulation(right_spectrum, ze)
        
        print(f"\n  右齿形高阶波纹度评价结果:")
        print(f"  高阶波数(≥{ze}): {list(right_high_order['high_order_waves'])}")
        print(f"  高阶振幅: {[f'{a:.4f}' for a in right_high_order['high_order_amplitudes']]}")
        print(f"  高阶总振幅: {right_high_order['total_high_order_amplitude']:.4f} μm")
        print(f"  高阶RMS值: {right_high_order['high_order_rms']:.4f} μm")
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    fig.suptitle(f'Profile Involute Polar Curve (z={teeth_count}, m={module})\n(Slope & Crowning Removed)', fontsize=14, fontweight='bold')
    
    ax1 = axes[0]
    if len(left_curve['angles']) > 0:
        ax1.scatter(left_curve['angles'], left_curve['values'], c=left_curve['tooth_indices'], 
                   cmap='tab20', s=3, alpha=0.7)
        ax1.set_title(f'Left Profile (Corrected) - {len(left_curve["angles"])} points')
        ax1.set_xlabel('Rotation Angle (deg)')
        ax1.set_ylabel('Deviation (um)')
        ax1.set_xlim(0, 360)
        ax1.grid(True, alpha=0.3)
        ax1.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='0 deg')
        for i in range(1, min(teeth_count, 20)):
            ax1.axvline(x=i * pitch_angle_deg, color='gray', linestyle=':', alpha=0.3)
        cbar = plt.colorbar(ax1.collections[0], ax=ax1, label='Tooth No.')
    else:
        ax1.text(0.5, 0.5, 'No left profile data', ha='center', va='center', transform=ax1.transAxes)
    
    ax2 = axes[1]
    if len(right_curve['angles']) > 0:
        ax2.scatter(right_curve['angles'], right_curve['values'], c=right_curve['tooth_indices'], 
                   cmap='tab20', s=3, alpha=0.7)
        ax2.set_title(f'Right Profile (Corrected) - {len(right_curve["angles"])} points')
        ax2.set_xlabel('Rotation Angle (deg)')
        ax2.set_ylabel('Deviation (um)')
        ax2.set_xlim(0, 360)
        ax2.grid(True, alpha=0.3)
        ax2.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='0 deg')
        for i in range(1, min(teeth_count, 20)):
            ax2.axvline(x=i * pitch_angle_deg, color='gray', linestyle=':', alpha=0.3)
        cbar = plt.colorbar(ax2.collections[0], ax=ax2, label='Tooth No.')
    else:
        ax2.text(0.5, 0.5, 'No right profile data', ha='center', va='center', transform=ax2.transAxes)
    
    ax3 = axes[2]
    if len(left_curve['angles']) > 0 and len(right_curve['angles']) > 0:
        ax3.scatter(left_curve['angles'], left_curve['values'], c='blue', s=2, alpha=0.5, label='Left Profile')
        ax3.scatter(right_curve['angles'], right_curve['values'], c='red', s=2, alpha=0.5, label='Right Profile')
        ax3.set_title(f'Combined Curve (Corrected) - Left(blue) + Right(red)')
        ax3.set_xlabel('Rotation Angle (deg)')
        ax3.set_ylabel('Deviation (um)')
        ax3.set_xlim(0, 360)
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc='upper right')
        for i in range(1, min(teeth_count, 20)):
            ax3.axvline(x=i * pitch_angle_deg, color='gray', linestyle=':', alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'No combined data', ha='center', va='center', transform=ax3.transAxes)
    
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5))
    fig2.suptitle(f'Zoomed View: Tooth 1-3 Combined Curve', fontsize=14, fontweight='bold')
    
    angle_end = 3 * pitch_angle_deg + 2
    
    ax_zoom1 = axes2[0]
    if len(left_curve['angles']) > 0:
        mask = (left_curve['angles'] >= 0) & (left_curve['angles'] <= angle_end)
        zoom_angles = left_curve['angles'][mask]
        zoom_values = left_curve['values'][mask]
        zoom_teeth = left_curve['tooth_indices'][mask]
        
        if len(zoom_angles) > 0:
            ax_zoom1.scatter(zoom_angles, zoom_values, c=zoom_teeth, cmap='tab10', s=15, alpha=0.8)
            ax_zoom1.set_title(f'Left Profile (Tooth 1-3)\n{len(zoom_angles)} points')
            ax_zoom1.set_xlabel('Rotation Angle (deg)')
            ax_zoom1.set_ylabel('Deviation (um)')
            ax_zoom1.set_xlim(0, angle_end)
            ax_zoom1.grid(True, alpha=0.3)
            ax_zoom1.axvline(x=0, color='green', linestyle='--', alpha=0.7, label='Tooth 1 start')
            ax_zoom1.axvline(x=pitch_angle_deg, color='blue', linestyle='--', alpha=0.7, label='Tooth 2 start')
            ax_zoom1.axvline(x=2*pitch_angle_deg, color='red', linestyle='--', alpha=0.7, label='Tooth 3 start')
            ax_zoom1.legend(loc='upper right', fontsize=8)
        else:
            ax_zoom1.text(0.5, 0.5, 'No data in range', ha='center', va='center', transform=ax_zoom1.transAxes)
    else:
        ax_zoom1.text(0.5, 0.5, 'No left profile data', ha='center', va='center', transform=ax_zoom1.transAxes)
    
    ax_zoom2 = axes2[1]
    if len(right_curve['angles']) > 0:
        mask = (right_curve['angles'] >= 0) & (right_curve['angles'] <= angle_end)
        zoom_angles = right_curve['angles'][mask]
        zoom_values = right_curve['values'][mask]
        zoom_teeth = right_curve['tooth_indices'][mask]
        
        if len(zoom_angles) > 0:
            ax_zoom2.scatter(zoom_angles, zoom_values, c=zoom_teeth, cmap='tab10', s=15, alpha=0.8)
            ax_zoom2.set_title(f'Right Profile (Tooth 1-3)\n{len(zoom_angles)} points')
            ax_zoom2.set_xlabel('Rotation Angle (deg)')
            ax_zoom2.set_ylabel('Deviation (um)')
            ax_zoom2.set_xlim(0, angle_end)
            ax_zoom2.grid(True, alpha=0.3)
            ax_zoom2.axvline(x=0, color='green', linestyle='--', alpha=0.7, label='Tooth 1 start')
            ax_zoom2.axvline(x=pitch_angle_deg, color='blue', linestyle='--', alpha=0.7, label='Tooth 2 start')
            ax_zoom2.axvline(x=2*pitch_angle_deg, color='red', linestyle='--', alpha=0.7, label='Tooth 3 start')
            ax_zoom2.legend(loc='upper right', fontsize=8)
        else:
            ax_zoom2.text(0.5, 0.5, 'No data in range', ha='center', va='center', transform=ax_zoom2.transAxes)
    else:
        ax_zoom2.text(0.5, 0.5, 'No right profile data', ha='center', va='center', transform=ax_zoom2.transAxes)
    
    plt.tight_layout()
    
    output_file2 = os.path.join(current_dir, 'profile_involute_polar_curves_zoomed.png')
    plt.savefig(output_file2, dpi=150, bbox_inches='tight')
    print(f"Zoomed chart saved: {output_file2}")
    
    output_file = os.path.join(current_dir, 'profile_involute_polar_curves.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nChart saved: {output_file}")
    
    if len(left_curve['angles']) > 0 and 'left_spectrum' in dir():
        fig3, axes3 = plt.subplots(2, 2, figsize=(14, 10))
        fig3.suptitle(f'Spectrum Analysis - Iterative Sine Decomposition (Least Squares)\nz={teeth_count}, m={module}, ZE={ze}', fontsize=14, fontweight='bold')
        
        ax_spectrum = axes3[0, 0]
        orders = left_spectrum['orders']
        amplitudes = left_spectrum['amplitudes']
        
        bar_colors = []
        for o in orders:
            if o >= ze:
                bar_colors.append('red')
            else:
                bar_colors.append('steelblue')
        
        bars = ax_spectrum.bar(range(len(orders)), amplitudes, color=bar_colors, alpha=0.8)
        ax_spectrum.set_xlabel('Component Index')
        ax_spectrum.set_ylabel('Amplitude (um)')
        ax_spectrum.set_title(f'Left Profile - Top 10 Waves per Revolution\n(Red: High Order ≥{ze})')
        ax_spectrum.set_xticks(range(len(orders)))
        ax_spectrum.set_xticklabels([f'{o}' for o in orders])
        ax_spectrum.grid(True, alpha=0.3, axis='y')
        ax_spectrum.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        for i, (bar, amp) in enumerate(zip(bars, amplitudes)):
            ax_spectrum.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                           f'{amp:.3f}', ha='center', va='bottom', fontsize=7)
        
        ax_signal = axes3[0, 1]
        ax_signal.plot(interp_angles, interp_values, 'b-', alpha=0.5, label='Original', linewidth=1)
        ax_signal.plot(interp_angles, left_spectrum['reconstructed'], 'r-', alpha=0.8, label='Reconstructed (All 10)', linewidth=1.5)
        if 'left_high_order' in dir():
            ax_signal.plot(interp_angles, left_high_order['high_order_reconstructed'], 'g-', alpha=0.8, 
                          label=f'High Order (≥{ze})', linewidth=1.5)
        ax_signal.set_xlabel('Rotation Angle (deg)')
        ax_signal.set_ylabel('Deviation (um)')
        ax_signal.set_title('Left Profile - Original vs Reconstructed')
        ax_signal.set_xlim(0, 360)
        ax_signal.grid(True, alpha=0.3)
        ax_signal.legend(loc='upper right', fontsize=8)
        
        ax_residual = axes3[1, 0]
        ax_residual.plot(interp_angles, left_spectrum['residual'], 'g-', alpha=0.7, linewidth=1)
        ax_residual.set_xlabel('Rotation Angle (deg)')
        ax_residual.set_ylabel('Residual (um)')
        ax_residual.set_title('Left Profile - Residual after 10 Components')
        ax_residual.set_xlim(0, 360)
        ax_residual.grid(True, alpha=0.3)
        ax_residual.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        ax_components = axes3[1, 1]
        if 'left_high_order' in dir() and len(left_high_order['high_order_indices']) > 0:
            for idx in left_high_order['high_order_indices']:
                if idx < len(left_spectrum['components']):
                    order = left_spectrum['orders'][idx]
                    comp = left_spectrum['components'][idx]
                    ax_components.plot(interp_angles, comp, label=f'{order} waves/rev', alpha=0.7, linewidth=1)
            ax_components.set_title(f'Left Profile - High Order Components (≥{ze})')
        else:
            for i, (order, comp) in enumerate(zip(orders[:5], left_spectrum['components'][:5])):
                ax_components.plot(interp_angles, comp, label=f'{order} waves/rev', alpha=0.7, linewidth=1)
            ax_components.set_title('Left Profile - Top 5 Sine Components')
        ax_components.set_xlabel('Rotation Angle (deg)')
        ax_components.set_ylabel('Component Value (um)')
        ax_components.set_xlim(0, 360)
        ax_components.grid(True, alpha=0.3)
        ax_components.legend(loc='upper right', fontsize=8)
        
        plt.tight_layout()
        
        output_file3 = os.path.join(current_dir, 'profile_spectrum_analysis.png')
        plt.savefig(output_file3, dpi=150, bbox_inches='tight')
        print(f"Spectrum chart saved: {output_file3}")
    
    plt.show()


if __name__ == '__main__':
    main()
