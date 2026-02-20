"""
生成四组曲线(左/右Profile, 左/右Helix)在360°圆周上的排列可视化
展示ep和el参数如何影响曲线排列
"""
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 齿轮参数
teeth_count = 87
module = 1.859
pressure_angle = 18.6
helix_angle = 25.3

# 评价范围
d1, d2 = 174.822, 180.603
b1, b2 = 2.1, 39.9

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

# 计算每齿角度跨度
angle_per_tooth = 360.0 / teeth_count
profile_span = ep * angle_per_tooth
helix_span = el * angle_per_tooth

print("="*70)
print("四组曲线在360°圆周上的排列可视化")
print("="*70)
print(f"\n基本参数:")
print(f"  齿数 ZE = {teeth_count}")
print(f"  每齿角度 = {angle_per_tooth:.4f}°")
print(f"\nProfile参数:")
print(f"  ep = {ep:.4f}")
print(f"  每齿Profile跨度 = {profile_span:.2f}°")
print(f"\nHelix参数:")
print(f"  el = {el:.4f}")
print(f"  每齿Helix跨度 = {helix_span:.2f}°")

# 创建图形
fig = plt.figure(figsize=(16, 12))

# ========== 1. 极坐标展示四组曲线的圆周排列 ==========
ax1 = fig.add_subplot(2, 2, 1, projection='polar')

# 绘制所有齿的位置
tooth_angles_rad = np.linspace(0, 2*np.pi, teeth_count, endpoint=False)
ax1.scatter(tooth_angles_rad, [1]*teeth_count, c='lightgray', s=10, alpha=0.5, label='齿位置')

# 绘制前5个齿的四组曲线范围
colors = {'left_profile': 'blue', 'right_profile': 'cyan', 
          'left_helix': 'red', 'right_helix': 'orange'}
labels = {'left_profile': 'Left Profile', 'right_profile': 'Right Profile',
          'left_helix': 'Left Helix', 'right_helix': 'Right Helix'}

for i in range(5):
    tooth_angle = tooth_angles_rad[i]
    
    # Left Profile (ep)
    lp_start = tooth_angle - math.radians(profile_span/2)
    lp_end = tooth_angle + math.radians(profile_span/2)
    ax1.barh(0.7, lp_end - lp_start, left=lp_start, height=0.1, 
             color=colors['left_profile'], alpha=0.7, 
             label=labels['left_profile'] if i == 0 else '')
    
    # Right Profile (ep)
    rp_start = tooth_angle - math.radians(profile_span/2)
    rp_end = tooth_angle + math.radians(profile_span/2)
    ax1.barh(0.55, rp_end - rp_start, left=rp_start, height=0.1, 
             color=colors['right_profile'], alpha=0.7,
             label=labels['right_profile'] if i == 0 else '')
    
    # Left Helix (el)
    lh_start = tooth_angle - math.radians(helix_span/2)
    lh_end = tooth_angle + math.radians(helix_span/2)
    ax1.barh(0.4, lh_end - lh_start, left=lh_start, height=0.1, 
             color=colors['left_helix'], alpha=0.7,
             label=labels['left_helix'] if i == 0 else '')
    
    # Right Helix (el)
    rh_start = tooth_angle - math.radians(helix_span/2)
    rh_end = tooth_angle + math.radians(helix_span/2)
    ax1.barh(0.25, rh_end - rh_start, left=rh_start, height=0.1, 
             color=colors['right_helix'], alpha=0.7,
             label=labels['right_helix'] if i == 0 else '')

ax1.set_ylim(0, 1)
ax1.set_title('Four Curves Arrangement on 360° Circle\n(First 5 Teeth)', fontsize=11, pad=20)
ax1.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

# ========== 2. 线性展示四组曲线排列 ==========
ax2 = fig.add_subplot(2, 2, 2)

# 展示前10个齿的角度范围
tooth_angles_deg = np.linspace(0, 360, teeth_count, endpoint=False)
num_display_teeth = 10

for i in range(num_display_teeth):
    tooth_angle = tooth_angles_deg[i]
    y_pos = i * 0.8
    
    # Left Profile
    lp_start = tooth_angle - profile_span/2
    lp_end = tooth_angle + profile_span/2
    ax2.barh(y_pos + 0.6, profile_span, left=lp_start, height=0.15, 
             color='blue', alpha=0.7)
    
    # Right Profile
    ax2.barh(y_pos + 0.4, profile_span, left=lp_start, height=0.15, 
             color='cyan', alpha=0.7)
    
    # Left Helix
    lh_start = tooth_angle - helix_span/2
    ax2.barh(y_pos + 0.2, helix_span, left=lh_start, height=0.15, 
             color='red', alpha=0.7)
    
    # Right Helix
    ax2.barh(y_pos, helix_span, left=lh_start, height=0.15, 
             color='orange', alpha=0.7)
    
    # 标记齿位置
    ax2.axvline(x=tooth_angle, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
    ax2.text(tooth_angle, y_pos + 0.8, f'{i+1}', ha='center', fontsize=7)

# 添加图例
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='blue', alpha=0.7, label='Left Profile'),
    Patch(facecolor='cyan', alpha=0.7, label='Right Profile'),
    Patch(facecolor='red', alpha=0.7, label='Left Helix'),
    Patch(facecolor='orange', alpha=0.7, label='Right Helix')
]
ax2.legend(handles=legend_elements, loc='upper right')

ax2.set_xlim(0, 60)  # 只显示前60度
ax2.set_ylim(-0.2, num_display_teeth * 0.8 + 0.5)
ax2.set_xlabel('Rotation Angle (°)', fontsize=10)
ax2.set_ylabel('Tooth Index', fontsize=10)
ax2.set_title('Four Curves Linear Arrangement\n(First 10 Teeth)', fontsize=11)
ax2.grid(True, alpha=0.3, axis='x')

# ========== 3. 单齿数据映射示意 ==========
ax3 = fig.add_subplot(2, 2, 3)

# 模拟单齿的Profile数据映射
n_points = 100
diameter_range = np.linspace(d1, d2, n_points)
roll_range = np.array([roll_s(d, db) for d in diameter_range])
base_circumference = math.pi * db
profile_angles = (roll_range / base_circumference) * 360.0

# 模拟偏差数据
profile_dev = 5 * np.sin(np.linspace(0, 4*np.pi, n_points)) + np.random.normal(0, 0.5, n_points)

ax3.plot(profile_angles, profile_dev, 'b-', linewidth=1.5, label='Left Profile')
ax3.fill_between(profile_angles, profile_dev, alpha=0.3)
ax3.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='Tooth Center')
ax3.set_xlabel('Rotation Angle (°)', fontsize=10)
ax3.set_ylabel('Deviation (μm)', fontsize=10)
ax3.set_title(f'Profile Data Mapping\n(ep={ep:.3f}, Span={profile_angles[-1]-profile_angles[0]:.2f}°)', fontsize=11)
ax3.grid(True, alpha=0.3)
ax3.legend()

# ========== 4. 单齿Helix数据映射 ==========
ax4 = fig.add_subplot(2, 2, 4)

# 模拟单齿的Helix数据映射
axial_range = np.linspace(b1, b2, n_points)
z0 = (b1 + b2) / 2
tan_beta0 = math.tan(beta)
helix_angles = np.degrees((2.0 * (axial_range - z0) * tan_beta0) / d)

# 模拟偏差数据
helix_dev = 3 * np.cos(np.linspace(0, 3*np.pi, n_points)) + np.random.normal(0, 0.3, n_points)

ax4.plot(helix_angles, helix_dev, 'r-', linewidth=1.5, label='Left Helix')
ax4.fill_between(helix_angles, helix_dev, alpha=0.3, color='red')
ax4.axvline(x=0, color='blue', linestyle='--', alpha=0.5, label='Tooth Center')
ax4.set_xlabel('Rotation Angle (°)', fontsize=10)
ax4.set_ylabel('Deviation (μm)', fontsize=10)
ax4.set_title(f'Helix Data Mapping\n(el={el:.3f}, Span={helix_angles[-1]-helix_angles[0]:.2f}°)', fontsize=11)
ax4.grid(True, alpha=0.3)
ax4.legend()

plt.tight_layout()
plt.savefig('four_curves_arrangement.png', dpi=150, bbox_inches='tight')
print(f"\n可视化图表已保存: four_curves_arrangement.png")
plt.show()

# ========== 打印详细说明 ==========
print(f"\n" + "="*70)
print("四组曲线排列详细说明")
print("="*70)

print(f"\n1. Profile (齿形) 曲线排列:")
print(f"   - 左齿形 (Left Profile): ep = {ep:.4f}")
print(f"     每齿角度跨度 = {profile_span:.2f}°")
print(f"   - 右齿形 (Right Profile): ep = {ep:.4f}")
print(f"     每齿角度跨度 = {profile_span:.2f}°")
print(f"\n   映射公式:")
print(f"     展长: s(d) = sqrt((d/2)^2 - (db/2)^2)")
print(f"     旋转角: ξ = (s / (π×db)) × 360°")
print(f"     范围: {profile_angles[0]:.2f}° ~ {profile_angles[-1]:.2f}°")

print(f"\n2. Helix (齿向) 曲线排列:")
print(f"   - 左齿向 (Left Helix): el = {el:.4f}")
print(f"     每齿角度跨度 = {helix_span:.2f}°")
print(f"   - 右齿向 (Right Helix): el = {el:.4f}")
print(f"     每齿角度跨度 = {helix_span:.2f}°")
print(f"\n   映射公式:")
print(f"     轴向角度差: Δφ = 2×Δz×tan(βb)/d")
print(f"     旋转角: α = Δφ")
print(f"     范围: {helix_angles[0]:.2f}° ~ {helix_angles[-1]:.2f}°")

print(f"\n3. 闭合曲线构建:")
print(f"   - 将{teeth_count}个齿的数据按上述角度映射到360°圆周")
print(f"   - 对重叠区域进行加权平均")
print(f"   - 形成四组独立的闭合曲线")
print(f"   - 对每组曲线进行FFT频谱分析")

print(f"\n4. 频谱分析:")
print(f"   - 分析阶次范围: 1 ~ 5×ZE = {5*teeth_count}")
print(f"   - 提取高阶成分 (阶次 ≥ ZE = {teeth_count})")
print(f"   - 计算W值 (高阶总振幅) 和 RMS值")
