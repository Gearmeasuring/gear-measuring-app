"""
可视化87个齿的曲线如何合并成360°闭合曲线
展示Profile和Helix数据的合并过程
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
el = (lb * math.tan(beta_b)) / pb

# 计算每齿角度跨度
angle_per_tooth = 360.0 / teeth_count
profile_span = ep * angle_per_tooth
helix_span = el * angle_per_tooth

print("="*70)
print("87个齿曲线合并为360°闭合曲线可视化")
print("="*70)
print(f"\n基本参数:")
print(f"  齿数 ZE = {teeth_count}")
print(f"  每齿角度 = {angle_per_tooth:.4f}°")
print(f"  Profile跨度 = {profile_span:.2f}° (ep={ep:.3f})")
print(f"  Helix跨度 = {helix_span:.2f}° (el={el:.3f})")

# 创建图形
fig = plt.figure(figsize=(16, 12))

# ========== 1. Profile曲线合并过程 ==========
ax1 = fig.add_subplot(2, 2, 1)

# 模拟87个齿的Profile数据合并
n_points_per_tooth = 50
base_circumference = math.pi * db

# 生成完整的360度数据
full_angles = []
full_values = []

for tooth_idx in range(teeth_count):
    # 每个齿的中心角度
    tooth_center = tooth_idx * angle_per_tooth
    
    # 生成该齿的Profile数据点
    roll_range = np.linspace(lu, lo, n_points_per_tooth)
    local_angles = (roll_range / base_circumference) * 360.0
    
    # 映射到全局角度 (以齿中心为基准)
    global_angles = tooth_center + local_angles - (local_angles[-1] - local_angles[0]) / 2
    
    # 模拟偏差数据 (添加一些周期性波动)
    t = np.linspace(0, 1, n_points_per_tooth)
    deviation = 3 * np.sin(2 * np.pi * 5 * t) + 2 * np.sin(2 * np.pi * 12 * t)
    deviation += 0.5 * np.random.normal(0, 1, n_points_per_tooth)
    
    full_angles.extend(global_angles)
    full_values.extend(deviation)
    
    # 只绘制前10个齿的示意
    if tooth_idx < 10:
        color = plt.cm.viridis(tooth_idx / 10)
        ax1.plot(global_angles, deviation, '-', color=color, alpha=0.7, linewidth=1)
        ax1.axvline(x=tooth_center, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)

ax1.set_xlim(0, 60)
ax1.set_xlabel('Rotation Angle (°)', fontsize=10)
ax1.set_ylabel('Deviation (μm)', fontsize=10)
ax1.set_title(f'Profile: First 10 Teeth (Each spans {profile_span:.1f}°)', fontsize=11)
ax1.grid(True, alpha=0.3)

# ========== 2. Helix曲线合并过程 ==========
ax2 = fig.add_subplot(2, 2, 2)

# 模拟87个齿的Helix数据合并
full_angles_h = []
full_values_h = []

for tooth_idx in range(teeth_count):
    # 每个齿的中心角度
    tooth_center = tooth_idx * angle_per_tooth
    
    # 生成该齿的Helix数据点
    axial_range = np.linspace(b1, b2, n_points_per_tooth)
    z0 = (b1 + b2) / 2
    tan_beta0 = math.tan(beta)
    local_angles = np.degrees((2.0 * (axial_range - z0) * tan_beta0) / d)
    
    # 映射到全局角度
    global_angles = tooth_center + local_angles
    
    # 模拟偏差数据
    t = np.linspace(0, 1, n_points_per_tooth)
    deviation = 4 * np.cos(2 * np.pi * 3 * t) + 1.5 * np.sin(2 * np.pi * 8 * t)
    deviation += 0.3 * np.random.normal(0, 1, n_points_per_tooth)
    
    full_angles_h.extend(global_angles)
    full_values_h.extend(deviation)
    
    # 只绘制前10个齿的示意
    if tooth_idx < 10:
        color = plt.cm.plasma(tooth_idx / 10)
        ax2.plot(global_angles, deviation, '-', color=color, alpha=0.7, linewidth=1)
        ax2.axvline(x=tooth_center, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)

ax2.set_xlim(0, 60)
ax2.set_xlabel('Rotation Angle (°)', fontsize=10)
ax2.set_ylabel('Deviation (μm)', fontsize=10)
ax2.set_title(f'Helix: First 10 Teeth (Each spans {helix_span:.1f}°)', fontsize=11)
ax2.grid(True, alpha=0.3)

# ========== 3. 完整的360° Profile闭合曲线 ==========
ax3 = fig.add_subplot(2, 2, 3)

# 将数据排序并处理重叠
full_angles = np.array(full_angles)
full_values = np.array(full_values)
sort_idx = np.argsort(full_angles)
full_angles = full_angles[sort_idx]
full_values = full_values[sort_idx]

# 对重叠角度进行平均
unique_angles = np.unique(full_angles)
avg_values = []
for angle in unique_angles:
    mask = np.abs(full_angles - angle) < 0.01
    avg_values.append(np.mean(full_values[mask]))

# 绘制完整的360度曲线
ax3.plot(unique_angles, avg_values, 'b-', linewidth=0.8, alpha=0.8)
ax3.fill_between(unique_angles, avg_values, alpha=0.2)

# 标记每齿位置
for i in range(teeth_count):
    tooth_angle = i * angle_per_tooth
    ax3.axvline(x=tooth_angle, color='red', linestyle='--', alpha=0.2, linewidth=0.3)

ax3.set_xlim(0, 360)
ax3.set_xlabel('Rotation Angle (°)', fontsize=10)
ax3.set_ylabel('Deviation (μm)', fontsize=10)
ax3.set_title(f'Profile: Full 360° Closed Curve (87 teeth merged)', fontsize=11)
ax3.grid(True, alpha=0.3)

# 添加统计信息
ax3.text(0.02, 0.98, f'Mean: {np.mean(avg_values):.2f} μm\nStd: {np.std(avg_values):.2f} μm\nMax: {np.max(avg_values):.2f} μm\nMin: {np.min(avg_values):.2f} μm',
         transform=ax3.transAxes, fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# ========== 4. 完整的360° Helix闭合曲线 ==========
ax4 = fig.add_subplot(2, 2, 4)

# 将数据排序并处理重叠
full_angles_h = np.array(full_angles_h)
full_values_h = np.array(full_values_h)
sort_idx_h = np.argsort(full_angles_h)
full_angles_h = full_angles_h[sort_idx_h]
full_values_h = full_values_h[sort_idx_h]

# 对重叠角度进行平均
unique_angles_h = np.unique(full_angles_h)
avg_values_h = []
for angle in unique_angles_h:
    mask = np.abs(full_angles_h - angle) < 0.01
    avg_values_h.append(np.mean(full_values_h[mask]))

# 绘制完整的360度曲线
ax4.plot(unique_angles_h, avg_values_h, 'r-', linewidth=0.8, alpha=0.8)
ax4.fill_between(unique_angles_h, avg_values_h, alpha=0.2, color='red')

# 标记每齿位置
for i in range(teeth_count):
    tooth_angle = i * angle_per_tooth
    ax4.axvline(x=tooth_angle, color='blue', linestyle='--', alpha=0.2, linewidth=0.3)

ax4.set_xlim(0, 360)
ax4.set_xlabel('Rotation Angle (°)', fontsize=10)
ax4.set_ylabel('Deviation (μm)', fontsize=10)
ax4.set_title(f'Helix: Full 360° Closed Curve (87 teeth merged)', fontsize=11)
ax4.grid(True, alpha=0.3)

# 添加统计信息
ax4.text(0.02, 0.98, f'Mean: {np.mean(avg_values_h):.2f} μm\nStd: {np.std(avg_values_h):.2f} μm\nMax: {np.max(avg_values_h):.2f} μm\nMin: {np.min(avg_values_h):.2f} μm',
         transform=ax4.transAxes, fontsize=9, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('87_teeth_merged_curves.png', dpi=150, bbox_inches='tight')
print(f"\n可视化图表已保存: 87_teeth_merged_curves.png")
plt.show()

# ========== 打印合并统计信息 ==========
print(f"\n" + "="*70)
print("87个齿曲线合并统计")
print("="*70)

print(f"\n【Profile曲线合并】")
print(f"  原始数据点数: {len(full_angles)}")
print(f"  合并后唯一角度数: {len(unique_angles)}")
print(f"  平均每角度数据点数: {len(full_angles)/len(unique_angles):.1f}")
print(f"  角度覆盖范围: {np.min(unique_angles):.2f}° ~ {np.max(unique_angles):.2f}°")
print(f"  数据范围: {np.min(avg_values):.2f} ~ {np.max(avg_values):.2f} μm")
print(f"  标准差: {np.std(avg_values):.2f} μm")

print(f"\n【Helix曲线合并】")
print(f"  原始数据点数: {len(full_angles_h)}")
print(f"  合并后唯一角度数: {len(unique_angles_h)}")
print(f"  平均每角度数据点数: {len(full_angles_h)/len(unique_angles_h):.1f}")
print(f"  角度覆盖范围: {np.min(unique_angles_h):.2f}° ~ {np.max(unique_angles_h):.2f}°")
print(f"  数据范围: {np.min(avg_values_h):.2f} ~ {np.max(avg_values_h):.2f} μm")
print(f"  标准差: {np.std(avg_values_h):.2f} μm")

print(f"\n【合并原理】")
print(f"  1. 每个齿的Profile数据占据 {profile_span:.2f}°")
print(f"     87个齿 × {profile_span:.2f}° = {87*profile_span:.1f}° 覆盖360°圆周")
print(f"\n  2. 每个齿的Helix数据占据 {helix_span:.2f}°")
print(f"     87个齿 × {helix_span:.2f}° = {87*helix_span:.1f}° 覆盖360°圆周")
print(f"\n  3. 重叠区域处理:")
print(f"     - 将相同角度的数据点进行平均")
print(f"     - 形成平滑的360°闭合曲线")
print(f"     - 用于后续的FFT频谱分析")
