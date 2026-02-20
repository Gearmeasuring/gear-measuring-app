"""
简单测试齿距数据整合到波纹频谱分析中
"""
import numpy as np
import math

# 模拟 _end_match 函数
def _end_match(y):
    """端点匹配（拼接多齿曲线前消除阶跃）"""
    if y is None:
        return y
    y = np.asarray(y, dtype=float)
    if y.size <= 1:
        return y
    ramp = np.linspace(y[0], y[-1], y.size, dtype=float)
    return y - ramp

# 模拟修改后的 _build_common_closed_curve_angle 函数
def _build_common_closed_curve_angle(all_tooth_data, eval_length, base_diameter, teeth_count, pitch_data=None):
    """按旋转角拼接所有齿并处理重叠/间隙，生成闭合曲线（整数阶次）"""
    if not all_tooth_data:
        return None
    if teeth_count <= 0:
        teeth_count = 1
    min_len = min(len(d) for d in all_tooth_data)
    if min_len < 8:
        min_len = 8
    
    try:
        # 计算每个齿的旋转角范围
        total_angle = 2.0 * math.pi
        angle_per_tooth = total_angle / float(teeth_count)
        
        # 计算全局旋转角点数（确保足够的分辨率）
        n_global = max(200, min_len * teeth_count)
        
        # 初始化全局数据和计数数组
        sum_arr = np.zeros(n_global, dtype=float)
        cnt_arr = np.zeros(n_global, dtype=float)
        
        # 处理齿距数据
        pitch_deviations = None
        if pitch_data:
            try:
                # 检查齿距数据格式
                if isinstance(pitch_data, dict):
                    # 假设格式为 {齿号: 齿距偏差值}
                    pitch_deviations = pitch_data
                    print(f"处理齿距数据: {pitch_deviations}")
                elif isinstance(pitch_data, (list, tuple, np.ndarray)):
                    # 假设格式为 [齿距偏差值1, 齿距偏差值2, ...]
                    pitch_deviations = {i: val for i, val in enumerate(pitch_data)}
                    print(f"处理齿距数据列表: {pitch_deviations}")
            except Exception as e:
                print(f"处理齿距数据失败: {e}")
        
        # 对每个齿的数据进行旋转角映射
        for tooth_idx, segment in enumerate(all_tooth_data):
            seg = np.asarray(segment, dtype=float)
            if len(seg) > min_len:
                seg = seg[:min_len]
            
            # 计算当前齿的旋转角偏移
            tooth_offset = float(tooth_idx) * angle_per_tooth
            
            # 生成当前齿的局部旋转角（0到angle_per_tooth）
            local_angles = np.linspace(0.0, angle_per_tooth, len(seg), dtype=float)
            
            # 计算全局旋转角
            global_angles = (tooth_offset + local_angles) % total_angle
            
            # 映射到全局数组索引
            indices = np.round((global_angles / total_angle) * n_global).astype(int) % n_global
            
            # 整合齿距数据
            if pitch_deviations and tooth_idx in pitch_deviations:
                try:
                    pitch_dev = float(pitch_deviations[tooth_idx])
                    # 将齿距偏差应用到当前齿的数据中
                    seg = seg + pitch_dev
                    print(f"应用齿距偏差到齿{tooth_idx}: {pitch_dev}")
                except Exception as e:
                    print(f"应用齿距偏差失败: {e}")
            
            # 累加数据到全局数组
            np.add.at(sum_arr, indices, seg)
            np.add.at(cnt_arr, indices, 1.0)
        
        # 计算平均值，处理重叠区域
        with np.errstate(divide='ignore', invalid='ignore'):
            common = np.where(cnt_arr > 0, sum_arr / cnt_arr, 0.0)
        
        # 应用端点匹配，确保曲线闭合
        common = _end_match(common)
        
        return common
    except Exception as e:
        print(f"_build_common_closed_curve_angle: 拼接失败 {e}，使用备用方案")
        # 即使失败，也尝试返回第一个齿的数据
        if all_tooth_data:
            try:
                first_tooth = all_tooth_data[0]
                # 对第一个齿的数据也应用端点匹配
                first_tooth = _end_match(first_tooth)
                return first_tooth
            except Exception:
                return None
        return None

def generate_test_data(teeth_count=87, points_per_tooth=100):
    """生成测试数据"""
    # 生成齿廓数据
    profile_right = {}
    
    # 生成齿距数据
    pitch_data = {}
    
    for tooth in range(teeth_count):
        # 生成齿廓测试数据（添加一些随机噪声）
        profile_right[tooth] = np.sin(np.linspace(0, 4 * np.pi, points_per_tooth)) * 0.1 + np.random.normal(0, 0.02, points_per_tooth)
        
        # 生成齿距数据（添加一些随机偏差）
        pitch_data[tooth] = np.random.normal(0, 0.005, 1)[0]
    
    return profile_right, pitch_data

def test_pitch_integration():
    """测试齿距数据整合"""
    print("=== 测试齿距数据整合到波纹频谱分析 ===")
    
    # 生成测试数据
    teeth_count = 87
    points_per_tooth = 100
    
    profile_right, pitch_data = generate_test_data(teeth_count, points_per_tooth)
    
    print(f"生成了 {teeth_count} 个齿的数据，每个齿 {points_per_tooth} 个点")
    print(f"齿距数据示例: {dict(list(pitch_data.items())[:5])}")
    
    # 处理齿数据
    all_tooth_data = []
    for tooth in range(teeth_count):
        values = profile_right[tooth]
        # 处理数据（去均值、端点匹配）
        detrended = values - np.mean(values)
        # 端点匹配
        detrended = _end_match(detrended)
        all_tooth_data.append(detrended)
    
    # 测试1：不使用齿距数据构建闭合曲线
    print("\n=== 测试1：不使用齿距数据构建闭合曲线 ===")
    common_curve_no_pitch = _build_common_closed_curve_angle(
        all_tooth_data,
        eval_length=10.0,
        base_diameter=45.0,
        teeth_count=teeth_count,
        pitch_data=None
    )
    
    print(f"构建的闭合曲线长度: {len(common_curve_no_pitch)}")
    print(f"闭合曲线数据范围: [{np.min(common_curve_no_pitch):.3f}, {np.max(common_curve_no_pitch):.3f}]")
    
    # 测试2：使用齿距数据构建闭合曲线
    print("\n=== 测试2：使用齿距数据构建闭合曲线 ===")
    common_curve_with_pitch = _build_common_closed_curve_angle(
        all_tooth_data,
        eval_length=10.0,
        base_diameter=45.0,
        teeth_count=teeth_count,
        pitch_data=pitch_data
    )
    
    print(f"构建的闭合曲线长度: {len(common_curve_with_pitch)}")
    print(f"闭合曲线数据范围: [{np.min(common_curve_with_pitch):.3f}, {np.max(common_curve_with_pitch):.3f}]")
    
    # 比较两种方法的结果
    print("\n=== 比较结果 ===")
    print(f"不使用齿距数据的均值: {np.mean(common_curve_no_pitch):.6f}")
    print(f"使用齿距数据的均值: {np.mean(common_curve_with_pitch):.6f}")
    print(f"不使用齿距数据的标准差: {np.std(common_curve_no_pitch):.6f}")
    print(f"使用齿距数据的标准差: {np.std(common_curve_with_pitch):.6f}")
    
    # 计算两种方法结果的差异
    difference = np.abs(common_curve_with_pitch - common_curve_no_pitch)
    print(f"\n两种方法结果的平均差异: {np.mean(difference):.6f}")
    print(f"两种方法结果的最大差异: {np.max(difference):.6f}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_pitch_integration()
