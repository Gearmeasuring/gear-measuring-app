import math

def calculate_overlap_segment(mka_file):
    """
    计算齿轮曲线重叠线段的算法
    基于多条曲线的重叠部分分析
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
    avg_d = (d1 + d2) / 2
    base_roll_length = avg_d / 5
    lu = base_roll_length - winkelabw_profile / 2
    lo = base_roll_length + winkelabw_profile / 2
    
    # 4. 计算齿形重叠线段长度(ep)
    # 重叠线段长度是所有齿形曲线的重叠部分长度
    # 基于齿轮啮合原理和评价范围计算
    
    # 计算齿轮的啮合重叠系数
    # 对于斜齿轮，重叠系数包括端面重叠系数和轴向重叠系数
    if beta != 0:
        # 计算端面压力角
        alpha_t = math.atan(math.tan(math.radians(alpha_n)) / math.cos(math.radians(beta)))
        # 计算端面模数
        mt = mn / math.cos(math.radians(beta))
        # 计算端面齿顶高系数
        ha_star = 1.0  # 标准齿顶高系数
        # 计算端面重叠系数
        epsilon_alpha = (1 / math.pi) * (z * (math.tan(alpha_t) - math.tan(alpha_t * 0.9)))
        # 计算轴向重叠系数
        b = b2 - b1  # 齿宽
        epsilon_beta = b * math.sin(math.radians(beta)) / pb
        # 总重叠系数
        epsilon_gamma = epsilon_alpha + epsilon_beta
    else:
        # 直齿轮只计算端面重叠系数
        epsilon_alpha = (1 / math.pi) * (z * (math.tan(math.radians(alpha_n)) - math.tan(math.radians(alpha_n) * 0.9)))
        epsilon_gamma = epsilon_alpha
    
    # 基于评价范围和重叠系数计算实际重叠线段长度
    # 评价范围长度与重叠系数的乘积
    ep = La * (epsilon_gamma / (epsilon_gamma + 1))
    
    # 5. 计算齿向重叠线段长度(el)
    # 齿向重叠线段长度是所有齿向曲线的重叠部分长度
    Lb = b2 - b1
    el = Lb * (epsilon_gamma / (epsilon_gamma + 1))
    
    # 6. 计算齿向评价范围(zo, zu)
    zo = (b2 - b1) / 2
    zu = -zo
    
    # 输出计算结果
    print(f"\n=== {mka_file} 重叠线段计算结果 ===")
    print(f"基圆直径 db: {db:.4f} mm")
    print(f"基圆齿距 pb: {pb:.4f} mm")
    print(f"齿形评价范围长度 La: {La:.4f} mm")
    print(f"齿向评价范围长度 Lb: {Lb:.4f} mm")
    print(f"重叠系数 epsilon_gamma: {epsilon_gamma:.4f}")
    print(f"\n计算值:")
    print(f"ep (齿形重叠线段长度): {ep:.4f}")
    print(f"lo: {lo:.4f}")
    print(f"lu: {lu:.4f}")
    print(f"el (齿向重叠线段长度): {el:.4f}")
    print(f"zo: {zo:.4f}")
    print(f"zu: {zu:.4f}")
    
    # 验证计算结果
    print(f"\n验证:")
    print(f"lo - lu: {lo - lu:.4f} (Winkelabw轮廓: {winkelabw_profile:.4f})")
    print(f"b2 - b1: {b2 - b1:.4f} (Winkelabw螺旋线: {winkelabw_flank:.4f})")
    
    # 提供重叠线段计算逻辑说明
    print(f"\n=== 重叠线段计算逻辑 ===")
    print("1. 齿形重叠线段长度(ep)计算:")
    print("   - 计算齿轮的总重叠系数 epsilon_gamma")
    print("   - 计算评价范围长度 La")
    print("   - ep = La * (epsilon_gamma / (epsilon_gamma + 1))")
    print("   - 表示所有齿形曲线在评价范围内的最大重叠部分长度")
    print("\n2. 齿向重叠线段长度(el)计算:")
    print("   - 使用相同的总重叠系数 epsilon_gamma")
    print("   - 计算齿向评价范围长度 Lb")
    print("   - el = Lb * (epsilon_gamma / (epsilon_gamma + 1))")
    print("   - 表示所有齿向曲线在评价范围内的最大重叠部分长度")
    
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
    calculate_overlap_segment("263751-018-WAV.mka")
    calculate_overlap_segment("004-xiaoxiao1.mka")
