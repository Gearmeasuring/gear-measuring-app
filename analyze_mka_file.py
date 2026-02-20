import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'gear_analysis_refactored'))

from utils.file_parser import MKAFileParser, parse_mka_file
from utils.gear_overlap_calculator import calculate_gear_parameters

# 读取MKA文件
mka_file = '004-xiaoxiao1.mka'
try:
    # 使用便捷函数解析MKA文件
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    print('=== MKA文件分析结果 ===')
    print('\n1. 基本齿轮参数:')
    print(f'   模数: {gear_data.get("module", gear_data.get("normal_module", "N/A"))}')
    print(f'   齿数: {gear_data.get("teeth", "N/A")}')
    print(f'   压力角: {gear_data.get("pressure_angle", "N/A")}')
    print(f'   螺旋角: {gear_data.get("helix_angle", "N/A")}')
    print(f'   齿轮宽度: {gear_data.get("gear_width", "N/A")}')
    
    print('\n2. 评价范围参数:')
    print(f'   左侧齿形评价开始: {gear_data.get("profile_eval_start_left", gear_data.get("profile_eval_start", "N/A"))}')
    print(f'   左侧齿形评价结束: {gear_data.get("profile_eval_end_left", gear_data.get("profile_eval_end", "N/A"))}')
    print(f'   右侧齿形评价开始: {gear_data.get("profile_eval_start_right", gear_data.get("profile_eval_start", "N/A"))}')
    print(f'   右侧齿形评价结束: {gear_data.get("profile_eval_end_right", gear_data.get("profile_eval_end", "N/A"))}')
    print(f'   左侧齿向评价开始: {gear_data.get("lead_eval_start_left", gear_data.get("lead_eval_start", "N/A"))}')
    print(f'   左侧齿向评价结束: {gear_data.get("lead_eval_end_left", gear_data.get("lead_eval_end", "N/A"))}')
    print(f'   右侧齿向评价开始: {gear_data.get("lead_eval_start_right", gear_data.get("lead_eval_start", "N/A"))}')
    print(f'   右侧齿向评价结束: {gear_data.get("lead_eval_end_right", gear_data.get("lead_eval_end", "N/A"))}')
    
    print('\n3. Winkelabw值:')
    print(f'   左侧轮廓Winkelabw: {gear_data.get("profile_angle_dev_left", "N/A")}')
    print(f'   右侧轮廓Winkelabw: {gear_data.get("profile_angle_dev_right", "N/A")}')
    print(f'   左侧齿向Winkelabw: {gear_data.get("lead_angle_dev_left", "N/A")}')
    print(f'   右侧齿向Winkelabw: {gear_data.get("lead_angle_dev_right", "N/A")}')
    
    # 提取测量数据（模拟数据，实际应从文件中读取）
    profile_data = {}
    flank_data = {}
    
    # 计算齿轮参数
    params = calculate_gear_parameters(gear_data, profile_data, flank_data)
    
    print('\n4. 计算的齿轮参数:')
    print(f'   ep (齿形误差): {params.get("ep", "N/A"):.3f}')
    print(f'   lo (滚长上限): {params.get("lo", "N/A"):.3f}')
    print(f'   lu (滚长下限): {params.get("lu", "N/A"):.3f}')
    print(f'   el (齿向误差): {params.get("el", "N/A"):.3f}')
    print(f'   zo (齿向起始): {params.get("zo", "N/A"):.3f}')
    print(f'   zu (齿向结束): {params.get("zu", "N/A"):.3f}')
    
    # 验证计算结果
    if 'ep' in params and 'lo' in params and 'lu' in params:
        print('\n5. 验证结果:')
        lo_lu_diff = params.get('lo', 0) - params.get('lu', 0)
        print(f'   lo - lu = {lo_lu_diff:.3f}')
    
    print('\n=== 分析完成 ===')
    
except Exception as e:
    print(f'分析失败: {e}')
    import traceback
    traceback.print_exc()
