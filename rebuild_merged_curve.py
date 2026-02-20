"""
根据标准公式重新构建合并曲线

问题：当前合并曲线存在间隙，各齿之间没有正确重叠

标准公式（来自Klingelnberg论文）：
φ = -ξ - Δφ + τ

对于齿形（渐开线）：
- Δφ = 0
- ξ = inv(α) = tan(α) - α （渐开线极角）
- τ = 齿序号 × 360° / 齿数 （节距角）
- 左齿面: φ = τ - ξ
- 右齿面: φ = τ + ξ

对于齿向（螺旋线）：
- ξ = 0
- Δφ = 2 × Δz × tan(β₀) / D₀ （轴向旋转角）
- τ = 齿序号 × 360° / 齿数
- 左齿面: φ = τ - Δφ
- 右齿面: φ = τ + Δφ

关键：所有齿的数据应该连续拼接，形成完整的0-360°曲线，没有间隙！
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


class CorrectedRippleAnalyzer:
    """修正后的波纹度分析器"""
    
    def __init__(self, teeth_count, module, pressure_angle=20.0, 
                 helix_angle=0.0, base_diameter=0.0):
        self.teeth_count = teeth_count
        self.module = module
        self.pressure_angle = pressure_angle
        self.helix_angle = helix_angle
        
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
        print(f"  螺旋角 β₀ = {helix_angle}°")
        print(f"  节圆直径 D₀ = {self.pitch_diameter:.3f} mm")
        print(f"  基圆直径 db = {self.base_diameter:.3f} mm")
        print(f"  节距角 τ = {self.pitch_angle:.4f}°")
    
    def remove_slope_and_crowning(self, data):
        """去除斜率和鼓形"""
        if len(data) < 3:
            return data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n, dtype=float)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        # 去除鼓形
        crowning_coeffs = np.polyfit(x_norm, data, 2)
        crowning_curve = np.polyval(crowning_coeffs, x_norm)
        data_after_crowning = data - crowning_curve
        
        # 去除斜率
        slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
        slope_curve = np.polyval(slope_coeffs, x_norm)
        corrected_data = data_after_crowning - slope_curve
        
        return corrected_data
    
    def calculate_involute_angle(self, radius):
        """计算渐开线极角 inv(α) = tan(α) - α"""
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def build_corrected_merged_curve(self, data_dict, data_type, side,
                                      eval_start, eval_end, 
                                      meas_start, meas_end):
        """
        构建修正后的合并曲线
        
        关键：所有齿的数据应该连续拼接，形成完整的0-360°曲线！
        """
        if side not in data_dict or not data_dict[side]:
            return None, None
        
        side_data = data_dict[side]
        sorted_teeth = sorted(side_data.keys())
        
        print(f"\n构建{side}齿面{data_type}合并曲线...")
        print(f"  齿数: {len(sorted_teeth)}")
        
        all_angles = []
        all_values = []
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            # 数据预处理
            actual_points = len(tooth_values)
            
            # 计算评价范围索引
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
            
            # 去除鼓形和斜率
            corrected_values = self.remove_slope_and_crowning(eval_values)
            
            # 计算齿序号和节距角 τ
            tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
            tau = tooth_index * self.pitch_angle
            
            if data_type == 'profile':
                # 齿形：计算渐开线极角 ξ
                if eval_start > 0 and eval_end > 0:
                    radii = np.linspace(eval_start/2, eval_end/2, eval_points)
                else:
                    radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, eval_points)
                
                # 计算渐开线极角 ξ (度)
                xi_angles = np.array([math.degrees(self.calculate_involute_angle(r)) for r in radii])
                
                # 角度合成: φ = τ ± ξ
                if side == 'left':
                    angles = tau - xi_angles
                else:
                    angles = tau + xi_angles
                
            else:  # helix
                # 齿向：计算轴向旋转角 Δφ
                if abs(self.helix_angle) > 0.01 and self.pitch_diameter > 0:
                    # 生成轴向位置数组
                    axial_positions = np.linspace(eval_start, eval_end, eval_points)
                    # 计算相对于中心的轴向距离
                    eval_center = (eval_start + eval_end) / 2.0
                    delta_z = axial_positions - eval_center
                    
                    # 计算轴向旋转角 Δφ (度)
                    tan_beta0 = math.tan(math.radians(self.helix_angle))
                    delta_phi = np.degrees(2 * delta_z * tan_beta0 / self.pitch_diameter)
                else:
                    delta_phi = np.linspace(0, 1, eval_points)
                
                # 角度合成: φ = τ ± Δφ
                if side == 'left':
                    angles = tau - delta_phi
                else:
                    angles = tau + delta_phi
            
            all_angles.extend(angles.tolist())
            all_values.extend(corrected_values.tolist())
        
        if not all_angles:
            return None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        # 归一化到 0-360° 范围
        all_angles = all_angles % 360.0
        
        # 按角度排序
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        print(f"  总数据点数: {len(all_angles)}")
        print(f"  角度范围: [{all_angles.min():.2f}°, {all_angles.max():.2f}°]")
        print(f"  角度跨度: {all_angles.max() - all_angles.min():.2f}°")
        
        return all_angles, all_values
    
    def visualize_merged_curve(self, angles, values, title, output_file):
        """可视化合并曲线"""
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        fig.suptitle(f'{title}\nCorrected Merged Curve (No Gaps)', 
                    fontsize=14, fontweight='bold')
        
        # 图1: 完整合并曲线
        ax1 = axes[0]
        ax1.plot(angles, values, 'b-', linewidth=0.5, alpha=0.7)
        ax1.set_xlabel('Rotation Angle φ (deg)', fontsize=11)
        ax1.set_ylabel('Deviation (μm)', fontsize=11)
        ax1.set_title(f'Complete Curve ({len(angles)} points, 0-360°)', 
                     fontsize=12, fontweight='bold')
        ax1.set_xlim(0, 360)
        ax1.grid(True, alpha=0.3)
        
        # 添加节距角标记线
        for i in range(self.teeth_count + 1):
            tau = i * self.pitch_angle
            if tau <= 360:
                ax1.axvline(x=tau, color='r', linestyle='--', alpha=0.2, linewidth=0.5)
        
        # 图2: 角度分布直方图（检查是否有间隙）
        ax2 = axes[1]
        ax2.hist(angles, bins=360, alpha=0.7, color='steelblue', edgecolor='black', linewidth=0.1)
        ax2.set_xlabel('Rotation Angle φ (deg)', fontsize=11)
        ax2.set_ylabel('Data Point Count', fontsize=11)
        ax2.set_title('Angle Distribution (Should be continuous, no gaps)', 
                     fontsize=12, fontweight='bold')
        ax2.set_xlim(0, 360)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 添加节距角标记
        for i in range(self.teeth_count + 1):
            tau = i * self.pitch_angle
            if tau <= 360:
                ax2.axvline(x=tau, color='r', linestyle='--', alpha=0.3, linewidth=0.8)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved: {output_file}")
        plt.close()


def main():
    # 读取MKA文件
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print("="*70)
    print("重新构建合并曲线（修正间隙问题）")
    print("="*70)
    print(f"文件: {mka_file}")
    print()
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    # 提取齿轮参数
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    # 创建分析器
    analyzer = CorrectedRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    # 获取评价范围
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    helix_meas_start = gear_data.get('helix_meas_start', 0)
    helix_meas_end = gear_data.get('helix_meas_end', 0)
    
    # 构建并可视化合并曲线
    
    # 左齿形
    if profile_data.get('left'):
        print("\n" + "="*70)
        angles, values = analyzer.build_corrected_merged_curve(
            profile_data, 'profile', 'left',
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end
        )
        if angles is not None:
            analyzer.visualize_merged_curve(
                angles, values, 
                'Left Profile (Involute)',
                os.path.join(current_dir, 'corrected_merged_left_profile.png')
            )
    
    # 右齿形
    if profile_data.get('right'):
        print("\n" + "="*70)
        angles, values = analyzer.build_corrected_merged_curve(
            profile_data, 'profile', 'right',
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end
        )
        if angles is not None:
            analyzer.visualize_merged_curve(
                angles, values,
                'Right Profile (Involute)',
                os.path.join(current_dir, 'corrected_merged_right_profile.png')
            )
    
    # 左齿向
    if flank_data.get('left'):
        print("\n" + "="*70)
        angles, values = analyzer.build_corrected_merged_curve(
            flank_data, 'helix', 'left',
            helix_eval_start, helix_eval_end,
            helix_meas_start, helix_meas_end
        )
        if angles is not None:
            analyzer.visualize_merged_curve(
                angles, values,
                'Left Helix (Spiral)',
                os.path.join(current_dir, 'corrected_merged_left_helix.png')
            )
    
    # 右齿向
    if flank_data.get('right'):
        print("\n" + "="*70)
        angles, values = analyzer.build_corrected_merged_curve(
            flank_data, 'helix', 'right',
            helix_eval_start, helix_eval_end,
            helix_meas_start, helix_meas_end
        )
        if angles is not None:
            analyzer.visualize_merged_curve(
                angles, values,
                'Right Helix (Spiral)',
                os.path.join(current_dir, 'corrected_merged_right_helix.png')
            )
    
    print("\n" + "="*70)
    print("完成！")
    print("="*70)
    print("\n生成的文件:")
    print("  corrected_merged_left_profile.png")
    print("  corrected_merged_right_profile.png")
    print("  corrected_merged_left_helix.png")
    print("  corrected_merged_right_helix.png")
    print("\n检查角度分布直方图，应该显示连续分布，没有间隙！")


if __name__ == '__main__':
    main()
