"""
可视化说明 ep 和 el 如何用于排列齿形和齿向曲线数据

核心概念:
- ep = la / pb = 评价长度与基节的比值
  用于将齿形(profile)数据按展长比例映射到旋转角度
  
- el = (lb × tan(βb)) / pb = 齿向评价参数
  用于将齿向(helix)数据按轴向位置映射到旋转角度
"""
import math
import numpy as np
import matplotlib.pyplot as plt

# 齿轮参数
teeth_count = 87
module = 1.859
pressure_angle = 18.6
helix_angle = 25.3

# 评价范围
d1, d2 = 174.822, 180.603  # Profile评价直径
b1, b2 = 2.1, 39.9          # Helix评价位置

# 计算基础参数
alpha_n = math.radians(pressure_angle)
beta = math.radians(helix_angle)
alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
d = teeth_count * module / math.cos(beta)
db = d * math.cos(alpha_t)
pb = math.pi * db / teeth_count
beta_b = math.asin(math.sin(beta) * math.cos(alpha_n))

# Profile参数
def roll_s(diameter, base_diameter):
    r, rb = diameter/2, base_diameter/2
    return math.sqrt(max(0, r*r - rb*rb))

lu = roll_s(d1, db)
lo = roll_s(d2, db)
la = lo - lu
ep = la / pb

# Helix参数
lb = b2 - b1
zo = lb / 2
zu = -zo
el = (lb * math.tan(beta_b)) / pb

print("="*70)
print("曲线数据排列原理可视化")
print("="*70)

print(f"\n【基础参数】")
print(f"  基圆直径 db = {db:.4f} mm")
print(f"  基节 pb = {pb:.4f} mm")
print(f"  基圆螺旋角 βb = {math.degrees(beta_b):.4f}°")

print(f"\n【Profile (齿形) 数据排列】")
print(f"  ep = {ep:.4f}")
print(f"  lu = {lu:.4f} mm")
print(f"  lo = {lo:.4f} mm")
print(f"  la = {la:.4f} mm")

print(f"\n  齿形数据排列原理:")
print(f"  1. 将直径坐标 d 转换为展长坐标 s(d) = √((d/2)² - (db/2)²)")
print(f"  2. 展长范围: lu={lu:.3f}mm → lo={lo:.3f}mm")
print(f"  3. 评价长度 la = {la:.3f}mm = {ep:.3f} × pb ({pb:.3f}mm)")
print(f"  4. 每个齿的Profile数据占据旋转角: {ep*360/teeth_count:.2f}°")

print(f"\n【Helix (齿向) 数据排列】")
print(f"  el = {el:.4f}")
print(f"  lb = {lb:.4f} mm")
print(f"  zo = {zo:.4f} mm")
print(f"  zu = {zu:.4f} mm")

print(f"\n  齿向数据排列原理:")
print(f"  1. 轴向位置 b 转换为旋转角 Δφ = 2×(b-z0)×tan(βb)/d")
print(f"  2. 轴向范围: b1={b1}mm → b2={b2}mm")
print(f"  3. 评价参数 el = {el:.3f} = (lb×tan(βb))/pb")
print(f"  4. 每个齿的Helix数据占据旋转角: {el*360/teeth_count:.2f}°")

# 创建可视化
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# ========== Profile 数据映射 ==========
ax1 = axes[0, 0]
# 模拟一个齿的Profile数据 (100个点)
n_points = 100
diameter_range = np.linspace(d1, d2, n_points)
roll_range = np.array([roll_s(d, db) for d in diameter_range])
# 模拟偏差数据
profile_deviation = 5 * np.sin(np.linspace(0, 4*np.pi, n_points)) + np.random.normal(0, 0.5, n_points)

# 转换为旋转角 (基于展长/基圆周长)
base_circumference = math.pi * db
angle_range = (roll_range / base_circumference) * 360.0

ax1.plot(angle_range, profile_deviation, 'b-', linewidth=1, label='Profile偏差')
ax1.set_xlabel('旋转角 (度)', fontsize=10)
ax1.set_ylabel('偏差 (μm)', fontsize=10)
ax1.set_title(f'Profile数据映射\n(ep={ep:.3f}, 角度跨度={angle_range[-1]-angle_range[0]:.2f}°)', fontsize=11)
ax1.grid(True, alpha=0.3)
ax1.legend()

# ========== Helix 数据映射 ==========
ax2 = axes[0, 1]
# 模拟一个齿的Helix数据
axial_range = np.linspace(b1, b2, n_points)
z0 = (b1 + b2) / 2
tan_beta0 = math.tan(beta)
# 模拟偏差数据
helix_deviation = 3 * np.cos(np.linspace(0, 3*np.pi, n_points)) + np.random.normal(0, 0.3, n_points)

# 转换为旋转角 (基于轴向位置)
alpha2_range = np.degrees((2.0 * (axial_range - z0) * tan_beta0) / d)

ax2.plot(alpha2_range, helix_deviation, 'r-', linewidth=1, label='Helix偏差')
ax2.set_xlabel('旋转角 (度)', fontsize=10)
ax2.set_ylabel('偏差 (μm)', fontsize=10)
ax2.set_title(f'Helix数据映射\n(el={el:.3f}, 角度跨度={alpha2_range[-1]-alpha2_range[0]:.2f}°)', fontsize=11)
ax2.grid(True, alpha=0.3)
ax2.legend()

# ========== 四组曲线在圆周上的排列 ==========
ax3 = axes[1, 0]

# 模拟4个齿的数据排列在360度圆周上
tooth_angles = np.linspace(0, 360, teeth_count, endpoint=False)

# Profile: 每个齿占据的角度范围
profile_angle_per_tooth = 360.0 / teeth_count
profile_data_span = ep * profile_angle_per_tooth  # 每个齿的Profile数据在圆周上的跨度

# 绘制示意图
for i in range(4):  # 只画4个齿作为示例
    tooth_start = tooth_angles[i]
    # Profile数据范围 (在齿的中心位置)
    profile_center = tooth_start
    profile_start = profile_center - profile_data_span / 2
    profile_end = profile_center + profile_data_span / 2
    
    # 绘制Profile数据块
    ax3.barh(i, profile_end - profile_start, left=profile_start, height=0.3, 
             color='blue', alpha=0.6, label='Profile' if i == 0 else '')
    
    # Helix数据范围
    helix_data_span = el * profile_angle_per_tooth
    helix_center = tooth_start
    helix_start = helix_center - helix_data_span / 2
    helix_end = helix_center + helix_data_span / 2
    
    # 绘制Helix数据块
    ax3.barh(i+0.35, helix_end - helix_start, left=helix_start, height=0.3, 
             color='red', alpha=0.6, label='Helix' if i == 0 else '')
    
    # 标记齿的位置
    ax3.axvline(x=tooth_start, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
    ax3.text(tooth_start, i+0.6, f'齿{i+1}', ha='center', fontsize=8)

ax3.set_xlim(0, 360)
ax3.set_ylim(-0.5, 4.5)
ax3.set_xlabel('旋转角 (度)', fontsize=10)
ax3.set_ylabel('齿序号', fontsize=10)
ax3.set_title('四组曲线在360°圆周上的排列示意\n(左齿形/左齿向)', fontsize=11)
ax3.legend(loc='upper right')
ax3.grid(True, alpha=0.3, axis='x')

# ========== 角度计算说明 ==========
ax4 = axes[1, 1]
ax4.axis('off')

explanation_text = f"""
【曲线数据排列原理】

1. Profile (齿形) 数据排列:
   
   展长公式: s(d) = √((d/2)² - (db/2)²)
   
   旋转角: ξ = (s / (π×db)) × 360°
   
   评价长度: la = lo - lu = {la:.3f}mm
   
   ep = la / pb = {ep:.3f}
   
   每齿角度跨度 = ep × (360°/ZE) = {ep * 360/teeth_count:.2f}°

2. Helix (齿向) 数据排列:
   
   轴向角度差: Δφ = 2×Δz×tan(βb)/d
   
   评价长度: lb = {lb:.3f}mm
   
   el = (lb×tan(βb))/pb = {el:.3f}
   
   每齿角度跨度 = el × (360°/ZE) = {el * 360/teeth_count:.2f}°

3. 四组曲线:
   - 左齿形 (Left Profile): ep = {ep:.3f}
   - 右齿形 (Right Profile): ep = {ep:.3f}
   - 左齿向 (Left Helix): el = {el:.3f}
   - 右齿向 (Right Helix): el = {el:.3f}
   
   每组曲线按各自的ep/el值在360°圆周上排列
"""

ax4.text(0.1, 0.9, explanation_text, transform=ax4.transAxes, fontsize=9,
         verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig('curve_arrangement_visualization.png', dpi=150, bbox_inches='tight')
print(f"\n可视化图表已保存: curve_arrangement_visualization.png")
plt.show()

print(f"\n" + "="*70)
print("关键结论:")
print("="*70)
print(f"1. ep ({ep:.3f}) 决定了每个齿的Profile数据在圆周上占据的角度范围")
print(f"   → 每个齿Profile占据: {ep * 360/teeth_count:.2f}°")
print(f"\n2. el ({el:.3f}) 决定了每个齿的Helix数据在圆周上占据的角度范围")
print(f"   → 每个齿Helix占据: {el * 360/teeth_count:.2f}°")
print(f"\n3. 四组曲线 (左/右 Profile, 左/右 Helix) 分别按各自的ep/el值")
print(f"   在360°圆周范围内排列，形成闭合曲线进行频谱分析")
