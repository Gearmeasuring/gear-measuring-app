"""
根据Klingelnberg论文重构齿形旋转角度合并算法

论文核心思想：
1. 将偏差曲线连接起来，模拟齿轮啮合滚动过程
2. 对于特定旋转角度，齿轮与作用平面相交
3. 由于重叠，每个旋转角度可以分配2个齿形测量点和2个齿向测量点

关键理解：
- 齿形测量只覆盖渐开线的一段（评价范围）
- 但通过角度合成，多个齿的数据会在旋转角度上重叠
- 这种重叠是正常的，因为齿轮啮合时相邻齿会同时参与接触

角度合成公式：
φ = -ξ - Δφ + τ

对于齿形（渐开线）：
- Δφ = 0（无轴向旋转）
- ξ = inv(α) = tan(α) - α（渐开线极角）
- τ = 齿序号 × 360° / 齿数（节距角）

因此：φ = -ξ + τ

对于左齿面：φ = τ - ξ
对于右齿面：φ = τ + ξ
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


class ProfileRippleAnalyzer:
    """齿形波纹度分析器 - 根据Klingelnberg论文重构"""
    
    def __init__(self, teeth_count, module, pressure_angle=20.0, base_diameter=0.0):
        self.teeth_count = teeth_count
        self.module = module
        self.pressure_angle = pressure_angle
        
        self.pitch_diameter = module * teeth_count
        self.pitch_radius = self.pitch_diameter / 2.0
        self.pitch_angle = 360.0 / teeth_count
        
        if base_diameter > 0:
            self.base_diameter = base_diameter
        else:
            self.base_diameter = self.pitch_diameter * math.cos(math.radians(pressure_angle))
        
        self.base_radius = self.base_diameter / 2.0
        
        print(f"齿轮参数:")
        print(f"  齿数 ZE = {teeth_count}")
        print(f"  模数 m = {module} mm")
        print(f"  压力角 α = {pressure_angle}°")
        print(f"  节圆直径 D₀ = {self.pitch_diameter:.3f} mm")
        print(f"  基圆直径 db = {self.base_diameter:.3f} mm")
        print(f"  节距角 τ = {self.pitch_angle:.4f}°")
    
    def remove_slope_and_crowning(self, data):
        """去除斜率和鼓形偏差"""
        if len(data) < 3:
            return data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n, dtype=float)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        # 去除鼓形（二次多项式）
        crowning_coeffs = np.polyfit(x_norm, data, 2)
        crowning_curve = np.polyval(crowning_coeffs, x_norm)
        data_after_crowning = data - crowning_curve
        
        # 去除斜率（一次多项式）
        slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
        slope_curve = np.polyval(slope_coeffs, x_norm)
        corrected_data = data_after_crowning - slope_curve
        
        return corrected_data
    
    def calculate_involute_angle(self, radius):
        """
        计算渐开线极角（滚动角）
        
        公式: inv(α) = tan(α) - α
        其中: α = arccos(rb/r)
        """
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def calculate_rotation_angle(self, radius, tooth_index, side='left'):
        """
        计算旋转角度
        
        根据论文公式: φ = -ξ + τ
        
        对于左齿面: φ = τ - ξ
        对于右齿面: φ = τ + ξ
        
        Args:
            radius: 测量点半径
            tooth_index: 齿序号（从0开始）
            side: 'left' 或 'right'
        
        Returns:
            旋转角度（度）
        """
        # 计算渐开线极角 ξ（弧度转度）
        xi_rad = self.calculate_involute_angle(radius)
        xi_deg = math.degrees(xi_rad)
        
        # 计算节距角 τ
        tau = tooth_index * self.pitch_angle
        
        # 角度合成
        if side == 'left':
            phi = tau - xi_deg
        else:
            phi = tau + xi_deg
        
        return phi
    
    def build_merged_curve(self, profile_data, side, eval_start, eval_end, 
                           meas_start, meas_end):
        """
        构建齿形合并曲线
        
        根据论文：将偏差曲线连接起来，模拟齿轮啮合滚动过程
        
        关键点：
        1. 每个齿的测量数据映射到旋转角度
        2. 多个齿的数据会在旋转角度上有重叠
        3. 这种重叠是正常的，模拟了齿轮啮合时相邻齿同时接触的情况
        """
        if side not in profile_data or not profile_data[side]:
            return None, None
        
        side_data = profile_data[side]
        sorted_teeth = sorted(side_data.keys())
        
        print(f"\n构建{side}齿面齿形合并曲线...")
        print(f"  齿数: {len(sorted_teeth)}")
        
        all_angles = []
        all_values = []
        all_tooth_ids = []
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            # 计算评价范围索引
            actual_points = len(tooth_values)
            
            if meas_end > meas_start and eval_end > eval_start:
                eval_start_ratio = (eval_start - meas_start) / (meas_end - meas_start)
                eval_end_ratio = (eval_end - meas_start) / (meas_end - meas_start)
                start_idx = int(actual_points * max(0.0, min(1.0, eval_start_ratio)))
                end_idx = int(actual_points * max(0.0, min(1.0, eval_end_ratio)))
            else:
                start_idx = 0
                end_idx = actual_points
            
            # 提取评价范围内数据
            eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
            eval_points = len(eval_values)
            
            if eval_points < 3:
                continue
            
            # 数据预处理：去除鼓形和斜率
            corrected_values = self.remove_slope_and_crowning(eval_values)
            
            # 计算齿序号
            tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
            
            # 计算每个测量点的旋转角度
            # 测量点对应的半径范围
            if eval_start > 0 and eval_end > 0:
                radii = np.linspace(eval_start/2, eval_end/2, eval_points)
            else:
                radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, eval_points)
            
            # 计算旋转角度
            angles = np.array([self.calculate_rotation_angle(r, tooth_index, side) for r in radii])
            
            all_angles.extend(angles.tolist())
            all_values.extend(corrected_values.tolist())
            all_tooth_ids.extend([tooth_id] * eval_points)
        
        if not all_angles:
            return None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        all_tooth_ids = np.array(all_tooth_ids)
        
        # 归一化到 0-360° 范围
        all_angles = all_angles % 360.0
        
        # 按角度排序
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        all_tooth_ids = all_tooth_ids[sort_idx]
        
        print(f"  总数据点数: {len(all_angles)}")
        print(f"  角度范围: [{all_angles.min():.2f}°, {all_angles.max():.2f}°]")
        print(f"  角度跨度: {all_angles.max() - all_angles.min():.2f}°")
        
        return all_angles, all_values, all_tooth_ids
    
    def visualize_merged_curve(self, angles, values, tooth_ids, title, output_file):
        """
        可视化合并曲线
        
        展示：
        1. 完整的合并曲线（模拟齿轮啮合滚动）
        2. 各齿数据的重叠情况
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'{title}\nMerged Profile Curve (Simulating Gear Mesh Rolling)', 
                    fontsize=14, fontweight='bold')
        
        # 图1: 完整合并曲线
        ax1 = axes[0, 0]
        ax1.plot(angles, values, 'b-', linewidth=0.5, alpha=0.7)
        ax1.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
        ax1.set_ylabel('Profile Deviation (μm)', fontsize=10)
        ax1.set_title(f'Complete Merged Curve ({len(angles)} points)', fontsize=11, fontweight='bold')
        ax1.set_xlim(0, 360)
        ax1.grid(True, alpha=0.3)
        
        # 添加节距角标记
        for i in range(self.teeth_count + 1):
            tau = i * self.pitch_angle
            if tau <= 360:
                ax1.axvline(x=tau, color='r', linestyle='--', alpha=0.2, linewidth=0.5)
        
        # 图2: 各齿数据分布（用颜色区分）
        ax2 = axes[0, 1]
        unique_teeth = np.unique(tooth_ids)
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_teeth)))
        
        for idx, tooth_id in enumerate(unique_teeth[:20]):  # 只显示前20个齿
            mask = tooth_ids == tooth_id
            ax2.scatter(angles[mask], values[mask], c=[colors[idx]], s=1, alpha=0.5, label=f'Tooth {tooth_id}')
        
        ax2.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
        ax2.set_ylabel('Profile Deviation (μm)', fontsize=10)
        ax2.set_title('Individual Tooth Data Distribution', fontsize=11, fontweight='bold')
        ax2.set_xlim(0, 360)
        ax2.legend(loc='upper right', fontsize=6, ncol=2)
        ax2.grid(True, alpha=0.3)
        
        # 图3: 角度分布直方图
        ax3 = axes[1, 0]
        ax3.hist(angles, bins=360, alpha=0.7, color='steelblue', edgecolor='black', linewidth=0.1)
        ax3.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
        ax3.set_ylabel('Data Point Count', fontsize=10)
        ax3.set_title('Angle Distribution (Gaps are Normal for Profile)', fontsize=11, fontweight='bold')
        ax3.set_xlim(0, 360)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 图4: 每个角度的数据点数量（检查重叠）
        ax4 = axes[1, 1]
        
        # 计算每个角度区间的数据点数量
        angle_bins = np.linspace(0, 360, 361)
        hist, _ = np.histogram(angles, bins=angle_bins)
        
        ax4.bar(angle_bins[:-1], hist, width=1, alpha=0.7, color='steelblue', edgecolor='black', linewidth=0.1)
        ax4.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
        ax4.set_ylabel('Data Points per Degree', fontsize=10)
        ax4.set_title('Data Density per Degree (Overlapping = Multiple Teeth)', fontsize=11, fontweight='bold')
        ax4.set_xlim(0, 360)
        ax4.grid(True, alpha=0.3, axis='y')
        
        # 添加说明
        explanation = f"""
Algorithm Based on Klingelnberg Paper:

1. Link deviation curves to simulate gear mesh rolling
2. For each rotation angle, multiple teeth may contribute data
3. Formula: φ = τ ± ξ
   - τ = tooth_index × 360°/ZE (pitch angle)
   - ξ = inv(α) = tan(α) - α (involute angle)

Key Points:
- Gaps between teeth are NORMAL (profile measures only a segment)
- Overlapping data indicates multiple teeth contributing at same angle
- This simulates the actual gear mesh behavior

Parameters:
- ZE = {self.teeth_count}
- τ = {self.pitch_angle:.4f}°
- db = {self.base_diameter:.3f} mm
        """
        
        fig.text(0.02, 0.02, explanation, fontsize=8, verticalalignment='bottom',
                fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"保存: {output_file}")
        plt.close()


def main():
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print("="*70)
    print("根据Klingelnberg论文重构齿形旋转角度合并算法")
    print("="*70)
    print(f"文件: {mka_file}")
    print()
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    analyzer = ProfileRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        base_diameter=base_diameter
    )
    
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    # 分析左齿形
    if profile_data.get('left'):
        print("\n" + "="*70)
        result = analyzer.build_merged_curve(
            profile_data, 'left',
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end
        )
        if result[0] is not None:
            angles, values, tooth_ids = result
            analyzer.visualize_merged_curve(
                angles, values, tooth_ids,
                'Left Profile (Involute)',
                os.path.join(current_dir, 'refactored_profile_left.png')
            )
    
    # 分析右齿形
    if profile_data.get('right'):
        print("\n" + "="*70)
        result = analyzer.build_merged_curve(
            profile_data, 'right',
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end
        )
        if result[0] is not None:
            angles, values, tooth_ids = result
            analyzer.visualize_merged_curve(
                angles, values, tooth_ids,
                'Right Profile (Involute)',
                os.path.join(current_dir, 'refactored_profile_right.png')
            )
    
    print("\n" + "="*70)
    print("重构完成！")
    print("="*70)
    print("\n生成的文件:")
    print("  refactored_profile_left.png")
    print("  refactored_profile_right.png")
    print("\n关键理解:")
    print("  1. 齿形测量只覆盖渐开线的一段，所以各齿之间有间隙是正常的")
    print("  2. 角度合成公式 φ = τ ± ξ 将各齿数据映射到旋转角度")
    print("  3. 合并曲线模拟了齿轮啮合滚动过程")


if __name__ == '__main__':
    main()
