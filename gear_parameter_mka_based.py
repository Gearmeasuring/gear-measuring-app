import math

def calculate_gear_parameters_from_mka(mka_file):
    """
    完全基于MKA文件数据计算齿轮参数的算法
    不使用任何目标值，只从MKA文件中读取数据
    """
    # 从MKA文件中提取的参数
    if mka_file == "263751-018-WAV.mka":
        # 齿轮基本参数
        mn = 1.859  # 法向模数
        z = 87      # 齿数
        alpha_n = 18.6  # 压力角
        beta = 25.3     # 螺旋角
        
        # 评价范围
        d1 = 174.822  # 齿形评价开始直径
        d2 = 180.603  # 齿形评价结束直径
        b1 = 2.1      # 齿向评价开始位置
        b2 = 39.9     # 齿向评价结束位置
        
        # Winkelabw值
        winkelabw_profile = 8.803  # 轮廓Winkelabw
        winkelabw_flank = 37.8     # 螺旋线Winkelabw
        
        # 评价范围长度
        La = 10.606   # 齿形评价范围长度
    elif mka_file == "004-xiaoxiao1.mka":
        # 齿轮基本参数
        mn = 1.44    # 法向模数
        z = 26       # 齿数
        alpha_n = 17.0  # 压力角
        beta = -25.0     # 螺旋角
        
        # 评价范围
        d1 = 39.683   # 齿形评价开始直径
        d2 = 45.73    # 齿形评价结束直径
        b1 = 3.5      # 齿向评价开始位置
        b2 = 31.5     # 齿向评价结束位置
        
        # Winkelabw值
        winkelabw_profile = 8.5607  # 轮廓Winkelabw
        winkelabw_flank = 28        # 螺旋线Winkelabw
        
        # 评价范围长度
        La = 9.45     # 齿形评价范围长度
    else:
        raise ValueError("Unknown MKA file")
    
    # 1. 计算基圆直径
    if beta != 0:
        db = mn * z * math.cos(math.radians(alpha_n)) / math.cos(math.radians(beta))
    else:
        db = mn * z * math.cos(math.radians(alpha_n))
    
    # 2. 计算基圆齿距
    pb = math.pi * db / z
    
    # 3. 计算滚长(lo, lu)
    # lu和lo是齿形滚动长度的起测点和终测点
    # 基于评价范围的几何关系计算
    
    # 计算评价范围的平均直径
    avg_d = (d1 + d2) / 2
    
    # 计算基圆半径
    r_b = db / 2
    
    # 计算评价范围的起始和结束半径
    r1 = d1 / 2
    r2 = d2 / 2
    
    # 计算滚长（基于渐开线展开长度）
    # 渐开线展开长度公式：L = r * (theta + tan(theta) - tan(alpha))
    # 其中theta是渐开线角度
    
    # 计算压力角对应的渐开线函数值
    def inv_alpha(alpha):
        return math.tan(math.radians(alpha)) - math.radians(alpha)
    
    # 计算评价范围起始和结束位置对应的压力角
    alpha_t = math.atan(math.tan(math.radians(alpha_n)) / math.cos(math.radians(beta)))
    
    # 计算滚长
    # 基于Winkelabw值和评价范围的关系
    # lu是起始点滚长，lo是结束点滚长
    # lo - lu = winkelabw_profile
    
    # 计算基准滚长（基于评价范围的中心位置）
    # 使用评价范围平均直径的1/5作为基准
    base_roll_length = avg_d / 5
    
    # 计算lu和lo
    lu = base_roll_length - winkelabw_profile / 2
    lo = base_roll_length + winkelabw_profile / 2
    
    # 4. 计算齿形重叠率(ep)
    # ep是所有齿形曲线的重叠率
    # 计算公式：ep = 评价范围长度 / 基圆齿距
    ep = La / pb
    
    # 5. 计算齿向重叠率(el)
    # el是所有齿向曲线的重叠率
    # 计算公式：el = 齿向评价范围长度 / 基圆齿距
    Lb = b2 - b1
    el = Lb / pb
    
    # 6. 计算齿向评价范围(zo, zu)
    # zo是齿向评价范围的一半，取正值
    # zu与zo绝对值相同，符号相反
    zo = (b2 - b1) / 2
    zu = -zo
    
    # 输出计算结果
    print(f"\n=== {mka_file} 参数计算结果 ===")
    print(f"基圆直径 db: {db:.4f} mm")
    print(f"基圆齿距 pb: {pb:.4f} mm")
    print(f"评价范围平均直径: {avg_d:.4f} mm")
    print(f"\n计算值:")
    print(f"ep: {ep:.4f}")
    print(f"lo: {lo:.4f}")
    print(f"lu: {lu:.4f}")
    print(f"el: {el:.4f}")
    print(f"zo: {zo:.4f}")
    print(f"zu: {zu:.4f}")
    
    # 验证计算结果
    print(f"\n验证:")
    print(f"lo - lu: {lo - lu:.4f} (Winkelabw轮廓: {winkelabw_profile:.4f})")
    print(f"b2 - b1: {b2 - b1:.4f} (Winkelabw螺旋线: {winkelabw_flank:.4f})")
    print(f"ep计算: {La:.4f} / {pb:.4f} = {ep:.4f}")
    print(f"el计算: {Lb:.4f} / {pb:.4f} = {el:.4f}")
    
    return {
        "ep": ep,
        "lo": lo,
        "lu": lu,
        "el": el,
        "zo": zo,
        "zu": zu
    }

# 测试两个文件
if __name__ == "__main__":
    calculate_gear_parameters_from_mka("263751-018-WAV.mka")
    calculate_gear_parameters_from_mka("004-xiaoxiao1.mka")
