"""
使用 klingelnberg_ripple_spectrum.py 中的正确方法计算参数
"""
import math

# 从 MKA 文件读取的基本参数
teeth_count = 87       # 齿数 ZE
module = 1.859         # 法向模数 mn (mm)
pressure_angle = 18.6  # 压力角 α (度)
helix_angle = 25.3     # 螺旋角 β (度)

# 评价范围参数 (从MKA文件)
d1 = 174.822   # Profile评价起始直径 (mm)
d2 = 180.603   # Profile评价结束直径 (mm)
b1 = 2.1       # Helix评价起始位置 (mm)
b2 = 39.9      # Helix评价结束位置 (mm)

print("="*70)
print("齿轮参数计算 (使用Klingelnberg方法)")
print("="*70)

print(f"\n【基本参数】")
print(f"  齿数 ZE = {teeth_count}")
print(f"  法向模数 mn = {module} mm")
print(f"  压力角 α = {pressure_angle}°")
print(f"  螺旋角 β = {helix_angle}°")

# 1. 计算端面压力角
alpha_n = math.radians(pressure_angle)
beta = math.radians(helix_angle)
alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
print(f"\n【端面压力角计算】")
print(f"  αt = atan(tan(αn) / cos(β))")
print(f"     = atan(tan({pressure_angle}°) / cos({helix_angle}°))")
print(f"     = atan({math.tan(alpha_n):.6f} / {math.cos(beta):.6f})")
print(f"     = atan({math.tan(alpha_n) / math.cos(beta):.6f})")
print(f"     = {math.degrees(alpha_t):.4f}°")

# 2. 计算分度圆直径
d = teeth_count * module / math.cos(beta)
print(f"\n【分度圆直径计算】")
print(f"  d = ZE × mn / cos(β)")
print(f"    = {teeth_count} × {module} / cos({helix_angle}°)")
print(f"    = {teeth_count * module:.4f} / {math.cos(beta):.6f}")
print(f"    = {d:.4f} mm")

# 3. 计算基圆直径
db = d * math.cos(alpha_t)
print(f"\n【基圆直径计算】")
print(f"  db = d × cos(αt)")
print(f"     = {d:.4f} × cos({math.degrees(alpha_t):.4f}°)")
print(f"     = {d:.4f} × {math.cos(alpha_t):.6f}")
print(f"     = {db:.4f} mm")

# 4. 计算基节
pb = math.pi * db / teeth_count
print(f"\n【基节计算】")
print(f"  pb = π × db / ZE")
print(f"     = π × {db:.4f} / {teeth_count}")
print(f"     = {pb:.4f} mm")

# 5. 计算基圆螺旋角
beta_b = math.asin(math.sin(beta) * math.cos(alpha_n))
print(f"\n【基圆螺旋角计算】")
print(f"  βb = asin(sin(β) × cos(α))")
print(f"     = asin(sin({helix_angle}°) × cos({pressure_angle}°))")
print(f"     = asin({math.sin(beta):.6f} × {math.cos(alpha_n):.6f})")
print(f"     = asin({math.sin(beta) * math.cos(alpha_n):.6f})")
print(f"     = {math.degrees(beta_b):.4f}°")

# ========== Profile 参数计算 ==========
print(f"\n" + "="*70)
print("【Profile (齿形) 参数计算】")
print("="*70)

# 展长计算公式: s(d) = sqrt((d/2)^2 - (db/2)^2)
def roll_s_from_diameter(diameter_mm, base_diameter_mm):
    """Klingelnberg 报表里的 Profile 坐标 lo/lu"""
    d = float(diameter_mm)
    db = float(base_diameter_mm)
    r = d / 2.0
    rb = db / 2.0
    if d >= db:
        return float(math.sqrt(max(0.0, r * r - rb * rb)))
    else:
        return abs(d - db) / 2.0

print(f"\n  评价起始直径 d1 = {d1} mm")
print(f"  评价结束直径 d2 = {d2} mm")

lu = roll_s_from_diameter(d1, db)
lo = roll_s_from_diameter(d2, db)
la = abs(lo - lu)
ep = la / pb

print(f"\n  展长计算 (s(d) = sqrt((d/2)^2 - (db/2)^2)):")
print(f"  lu = s({d1}) = sqrt(({d1}/2)^2 - ({db:.4f}/2)^2)")
print(f"     = sqrt({d1/2:.4f}^2 - {db/2:.4f}^2)")
print(f"     = sqrt({(d1/2)**2:.4f} - {(db/2)**2:.4f})")
print(f"     = sqrt({max(0, (d1/2)**2 - (db/2)**2):.4f})")
print(f"     = {lu:.4f} mm")

print(f"\n  lo = s({d2}) = sqrt(({d2}/2)^2 - ({db:.4f}/2)^2)")
print(f"     = sqrt({d2/2:.4f}^2 - {db/2:.4f}^2)")
print(f"     = sqrt({(d2/2)**2:.4f} - {(db/2)**2:.4f})")
print(f"     = sqrt({max(0, (d2/2)**2 - (db/2)**2):.4f})")
print(f"     = {lo:.4f} mm")

print(f"\n  la = |lo - lu| = |{lo:.4f} - {lu:.4f}| = {la:.4f} mm")
print(f"\n  ep = la / pb = {la:.4f} / {pb:.4f} = {ep:.4f}")

print(f"\n" + "-"*50)
print("【Profile 计算结果对比】")
print("-"*50)
print(f"  参数    |  计算值   |  PDF值   |  差异")
print(f"  --------|-----------|----------|--------")
print(f"  ep      |  {ep:.3f}   |  1.454   |  {abs(ep - 1.454):.3f}")
print(f"  lo      |  {lo:.3f}  |  33.578  |  {abs(lo - 33.578):.3f}")
print(f"  lu      |  {lu:.3f}  |  24.775  |  {abs(lu - 24.775):.3f}")

# ========== Helix 参数计算 ==========
print(f"\n" + "="*70)
print("【Helix (齿向) 参数计算】")
print("="*70)

print(f"\n  评价起始位置 b1 = {b1} mm")
print(f"  评价结束位置 b2 = {b2} mm")

lb = abs(b2 - b1)
zo = lb / 2.0
zu = -zo
el = (lb * math.tan(beta_b)) / pb

print(f"\n  lb = |b2 - b1| = |{b2} - {b1}| = {lb:.4f} mm")
print(f"\n  zo = lb / 2 = {lb:.4f} / 2 = {zo:.4f} mm")
print(f"  zu = -zo = {zu:.4f} mm")
print(f"\n  el = (lb × tan(βb)) / pb")
print(f"     = ({lb:.4f} × tan({math.degrees(beta_b):.4f}°)) / {pb:.4f}")
print(f"     = ({lb:.4f} × {math.tan(beta_b):.6f}) / {pb:.4f}")
print(f"     = {lb * math.tan(beta_b):.4f} / {pb:.4f}")
print(f"     = {el:.4f}")

print(f"\n" + "-"*50)
print("【Helix 计算结果对比】")
print("-"*50)
print(f"  参数    |  计算值   |  PDF值   |  差异")
print(f"  --------|-----------|----------|--------")
print(f"  el      |  {el:.3f}   |  2.766   |  {abs(el - 2.766):.3f}")
print(f"  zo      |  {zo:.3f}  |  18.900  |  {abs(zo - 18.900):.3f}")
print(f"  zu      |  {zu:.3f}  | -18.900  |  {abs(zu - (-18.900)):.3f}")

print(f"\n" + "="*70)
print("【总结】")
print("="*70)

# 检查差异
ep_diff = abs(ep - 1.454)
lo_diff = abs(lo - 33.578)
lu_diff = abs(lu - 24.775)
el_diff = abs(el - 2.766)
zo_diff = abs(zo - 18.900)

if all(d < 0.1 for d in [ep_diff, lo_diff, lu_diff, el_diff, zo_diff]):
    print("✓ 所有参数计算结果与PDF值基本一致 (差异 < 0.1)")
else:
    print("⚠ 部分参数与PDF值有差异:")
    if ep_diff >= 0.1:
        print(f"  - ep 差异: {ep_diff:.3f}")
    if lo_diff >= 0.1:
        print(f"  - lo 差异: {lo_diff:.3f}")
    if lu_diff >= 0.1:
        print(f"  - lu 差异: {lu_diff:.3f}")
    if el_diff >= 0.1:
        print(f"  - el 差异: {el_diff:.3f}")
    if zo_diff >= 0.1:
        print(f"  - zo 差异: {zo_diff:.3f}")
