#!/usr/bin/env python
"""
生成87个齿的不连续旋转角度曲线
包含左齿形、右齿形、左齿向、右齿向四个方向
每个测量点的旋转角度由滚动角、轴向位置产生的旋转以及节距角三者之和计算
"""
import numpy as np
import matplotlib.pyplot as plt

class TeethRotationCurveGenerator:
    """87个齿的旋转角度曲线生成器"""
    
    def __init__(self, num_teeth=87):
        """
        初始化生成器
        
        Args:
            num_teeth: 齿数，默认87
        """
        self.num_teeth = num_teeth
        self.points_per_tooth = 50  # 每齿测量点数
        self.total_points = num_teeth * self.points_per_tooth
        
    def calculate_rotation_angle(self, tooth_id, point_id, axial_position=0):
        """
        计算单个点的旋转角度
        
        Args:
            tooth_id: 齿序号
            point_id: 齿上点序号
            axial_position: 轴向位置
            
        Returns:
            float: 旋转角度（弧度）
        """
        # 节距角：每个齿的角度
        pitch_angle = (2 * np.pi) / self.num_teeth
        
        # 滚动角：齿上点的角度
        roll_angle = (point_id / self.points_per_tooth) * pitch_angle
        
        # 轴向位置产生的旋转（假设微小影响）
        axial_rotation = 0.01 * axial_position * (2 * np.pi) / self.num_teeth
        
        # 节距角：当前齿的起始角度
        tooth_angle = tooth_id * pitch_angle
        
        # 总旋转角度
        total_angle = tooth_angle + roll_angle + axial_rotation
        
        return total_angle
    
    def generate_discontinuous_curves(self):
        """
        生成不连续的旋转角度曲线
        
        Returns:
            dict: 包含四个方向曲线数据的字典
        """
        data = {
            'profile_left': {'angles': [], 'values': []},
            'profile_right': {'angles': [], 'values': []},
            'helix_left': {'angles': [], 'values': []},
            'helix_right': {'angles': [], 'values': []}
        }
        
        # 生成每个齿的数据
        for tooth_id in range(self.num_teeth):
            tooth_angles = []
            tooth_profile_left = []
            tooth_profile_right = []
            tooth_helix_left = []
            tooth_helix_right = []
            
            # 生成齿上每个点的数据
            for point_id in range(self.points_per_tooth):
                # 计算旋转角度
                angle = self.calculate_rotation_angle(tooth_id, point_id)
                tooth_angles.append(angle)
                
                # 生成基础波纹
                base_ripple = 1.0 * np.sin(angle) + 0.3 * np.sin(4 * angle) + 0.1 * np.random.randn()
                
                # 左齿形
                profile_left = base_ripple + 0.05 * np.sin(2 * np.pi * tooth_id / self.num_teeth)
                tooth_profile_left.append(profile_left)
                
                # 右齿形
                profile_right = base_ripple * 0.9 + 0.05 * np.sin(2 * np.pi * tooth_id / self.num_teeth)
                tooth_profile_right.append(profile_right)
                
                # 左齿向
                helix_left = base_ripple * 0.8 + 0.03 * np.sin(2 * np.pi * tooth_id / self.num_teeth)
                tooth_helix_left.append(helix_left)
                
                # 右齿向
                helix_right = base_ripple * 0.7 + 0.03 * np.sin(2 * np.pi * tooth_id / self.num_teeth)
                tooth_helix_right.append(helix_right)
            
            # 添加到总数据中（添加间隙）
            data['profile_left']['angles'].extend(tooth_angles)
            data['profile_left']['values'].extend(tooth_profile_left)
            
            data['profile_right']['angles'].extend(tooth_angles)
            data['profile_right']['values'].extend(tooth_profile_right)
            
            data['helix_left']['angles'].extend(tooth_angles)
            data['helix_left']['values'].extend(tooth_helix_left)
            
            data['helix_right']['angles'].extend(tooth_angles)
            data['helix_right']['values'].extend(tooth_helix_right)
        
        return data
    
    def display_curves(self, curves):
        """
        显示四个方向的旋转角度曲线
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 12))
        
        # 左齿形
        ax1.plot(curves['profile_left']['angles'], curves['profile_left']['values'], 'b-', linewidth=1.0)
        ax1.set_title('Left Profile - 87 Teeth')
        ax1.set_xlabel('Rotation Angle (radians)')
        ax1.set_ylabel('Deviation (μm)')
        ax1.grid(True)
        ax1.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax1.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿形
        ax2.plot(curves['profile_right']['angles'], curves['profile_right']['values'], 'r-', linewidth=1.0)
        ax2.set_title('Right Profile - 87 Teeth')
        ax2.set_xlabel('Rotation Angle (radians)')
        ax2.set_ylabel('Deviation (μm)')
        ax2.grid(True)
        ax2.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax2.transAxes, fontsize=10, fontweight='bold')
        
        # 左齿向
        ax3.plot(curves['helix_left']['angles'], curves['helix_left']['values'], 'g-', linewidth=1.0)
        ax3.set_title('Left Helix - 87 Teeth')
        ax3.set_xlabel('Rotation Angle (radians)')
        ax3.set_ylabel('Deviation (μm)')
        ax3.grid(True)
        ax3.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax3.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿向
        ax4.plot(curves['helix_right']['angles'], curves['helix_right']['values'], 'y-', linewidth=1.0)
        ax4.set_title('Right Helix - 87 Teeth')
        ax4.set_xlabel('Rotation Angle (radians)')
        ax4.set_ylabel('Deviation (μm)')
        ax4.grid(True)
        ax4.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax4.transAxes, fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('87_teeth_rotation_curves.png')
        print("87个齿的旋转角度曲线已保存到 87_teeth_rotation_curves.png")
        
        # 显示组合图
        plt.show()
    
    def run(self):
        """
        运行生成流程
        """
        print(f"=== 生成{self.num_teeth}个齿的不连续旋转角度曲线 ===")
        
        # 生成曲线数据
        print("生成不连续的旋转角度曲线数据...")
        curves = self.generate_discontinuous_curves()
        
        # 显示曲线
        print("显示旋转角度曲线...")
        self.display_curves(curves)
        
        print(f"=== {self.num_teeth}个齿的旋转角度曲线生成完成 ===")

if __name__ == "__main__":
    generator = TeethRotationCurveGenerator(num_teeth=87)
    generator.run()
