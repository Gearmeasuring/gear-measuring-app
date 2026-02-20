import math

# 目标值
target_ep = 1.454
target_lo = 33.578
target_lu = 24.775
target_el = 2.766
target_zo = 18.900
target_zu = -18.900

# 计算需要的 pb 值（使 ep 正确）
delta_lo_lu = abs(target_lo - target_lu)
required_pb = delta_lo_lu / target_ep
print(f"需要的基圆齿距(pb): {required_pb:.3f}")

# 计算需要的 db 值（基于目标 ep）
teeth_count = 25
required_db = (required_pb * teeth_count) / math.pi
print(f"需要的基圆直径(db): {required_db:.3f}")

# 计算基圆半径 rb
required_rb = required_db / 2.0
print(f"需要的基圆半径(rb): {required_rb:.3f}")

# 反推需要的 r_end 和 r_start（直径）
required_r_end = math.sqrt(target_lo**2 + required_rb**2)
required_r_start = math.sqrt(target_lu**2 + required_rb**2)

required_profile_eval_end = 2 * required_r_end
required_profile_eval_start = 2 * required_r_start

print(f"\n需要的评价范围（直径）:")
print(f"profile_eval_end: {required_profile_eval_end:.3f}")
print(f"profile_eval_start: {required_profile_eval_start:.3f}")

# 验证计算
lo = math.sqrt(required_r_end**2 - required_rb**2)
lu = math.sqrt(required_r_start**2 - required_rb**2)
ep = abs(lo - lu) / required_pb

print(f"\n验证计算:")
print(f"lo: {lo:.3f}")
print(f"lu: {lu:.3f}")
print(f"ep: {ep:.3f}")

# 检查是否与目标值一致
print(f"\n与目标值比较:")
print(f"lo匹配: {abs(lo - target_lo) < 0.001}")
print(f"lu匹配: {abs(lu - target_lu) < 0.001}")
print(f"ep匹配: {abs(ep - target_ep) < 0.001}")

# 计算需要的压力角（基于已知的 module 和 required_db）
module = 1.745
beta = 0.0  # 假设螺旋角为0进行简化计算

# 计算分度圆直径 d
d = teeth_count * module / math.cos(math.radians(beta)) if beta else teeth_count * module

# 计算压力角 alpha_t
try:
    cos_alpha_t = required_db / d
    if cos_alpha_t > 1.0 or cos_alpha_t < -1.0:
        print("\n警告: 计算出的cos(alpha_t)超出范围")
        alpha_t_deg = 17.0  # 使用默认值
    else:
        alpha_t = math.acos(cos_alpha_t)
        alpha_t_deg = math.degrees(alpha_t)
        print(f"\n需要的压力角(alpha_t): {alpha_t_deg:.3f}度")
except Exception as e:
    print(f"\n计算压力角时出错: {e}")
    alpha_t_deg = 17.0

# Helix参数计算
helix_eval_start = target_zo
helix_eval_end = target_zo + target_el
print(f"\nHelix参数:")
print(f"需要的helix_eval_start: {helix_eval_start}")
print(f"需要的helix_eval_end: {helix_eval_end}")

print("\n总结需要的参数设置:")
print(f"1. profile_eval_end: {required_profile_eval_end:.3f}")
print(f"2. profile_eval_start: {required_profile_eval_start:.3f}")
print(f"3. 基圆齿距(pb)需要调整为: {required_pb:.3f}")
print(f"4. 基圆直径(db)需要调整为: {required_db:.3f}")

