#!/usr/bin/env python
"""
显示旋转角的测量曲线，包括左齿形、右齿形、左齿向、右齿向
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# 添加项目根目录到路径
sys.path.append(os.path.abspath('gear_analysis_refactored'))

# 导入必要的模块
try:
    from reports.klingelnberg_ import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings
    from reports.klingelnberg_ import SpectrumParams
    print("✓ 成功导入KlingelnbergRippleSpectrumReport")
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)

class RotationAngleCurveDisplay:
    """旋转角测量曲线显示类"""
    
    def __init__(self):
        """初始化显示类"""
        self.settings = RippleSpectrumSettings()
        self.report = KlingelnbergRippleSpectrumReport(settings=self.settings)
    
    def generate_mock_data(self, num_teeth=92, points_per_tooth=200):
        """
        生成模拟齿轮数据
        
        Args:
            num_teeth: 齿数
            points_per_tooth: 每齿点数
            
        Returns:
            dict: 包含左齿形、右齿形、左齿向、右齿向数据的字典
        """
        data = {
            'profile_left': {},
            'profile_right': {},
            'helix_left': {},
            'helix_right': {}
        }
        
        for tooth_id in range(num_teeth):
            # 生成齿形数据
            x = np.linspace(0, 1, points_per_tooth)
            # 添加多个频率分量和噪声
            profile_left = 0.5 * np.sin(2 * np.pi * 10 * x) + 0.3 * np.sin(2 * np.pi * 20 * x) + 0.05 * np.random.randn(points_per_tooth)
            profile_right = 0.4 * np.sin(2 * np.pi * 10 * x) + 0.25 * np.sin(2 * np.pi * 20 * x) + 0.05 * np.random.randn(points_per_tooth)
            
            # 生成齿向数据
            helix_left = 0.3 * np.sin(2 * np.pi * 5 * x) + 0.15 * np.sin(2 * np.pi * 15 * x) + 0.03 * np.random.randn(points_per_tooth)
            helix_right = 0.25 * np.sin(2 * np.pi * 5 * x) + 0.12 * np.sin(2 * np.pi * 15 * x) + 0.03 * np.random.randn(points_per_tooth)
            
            # 添加齿距偏差
            pitch_dev = 0.02 * np.sin(2 * np.pi * tooth_id / num_teeth)
            profile_left += pitch_dev
            profile_right += pitch_dev
            helix_left += pitch_dev
            helix_right += pitch_dev
            
            data['profile_left'][tooth_id] = profile_left
            data['profile_right'][tooth_id] = profile_right
            data['helix_left'][tooth_id] = helix_left
            data['helix_right'][tooth_id] = helix_right
        
        return data
    
    def create_rotation_angle_curves(self, data_dict, teeth_count=92):
        """
        创建旋转角测量曲线
        
        Args:
            data_dict: 包含齿轮数据的字典
            teeth_count: 齿数
            
        Returns:
            dict: 包含旋转角曲线的字典
        """
        curves = {}
        
        for data_type in ['profile', 'helix']:
            for side in ['left', 'right']:
                key = f'{data_type}_{side}'
                if key in data_dict:
                    tooth_data = data_dict[key]
                    all_tooth_data = []
                    
                    # 收集所有齿的数据
                    for tooth_id, values in tooth_data.items():
                        if values is not None and len(values) > 0:
                            all_tooth_data.append(values)
                    
                    if all_tooth_data:
                        # 生成旋转角度坐标
                        total_angle = 2 * np.pi
                        angle_per_tooth = total_angle / teeth_count
                        
                        # 计算全局旋转角度
                        n_points = min(len(data) for data in all_tooth_data)
                        global_angles = []
                        global_data = []
                        
                        for tooth_idx, tooth_vals in enumerate(all_tooth_data):
                            # 取前n_points个点
                            tooth_vals = tooth_vals[:n_points]
                            # 计算当前齿的旋转角度范围
                            start_angle = tooth_idx * angle_per_tooth
                            end_angle = (tooth_idx + 1) * angle_per_tooth
                            # 生成当前齿的旋转角度
                            tooth_angles = np.linspace(start_angle, end_angle, n_points)
                            # 添加到全局数据
                            global_angles.extend(tooth_angles)
                            global_data.extend(tooth_vals)
                        
                        # 归一化旋转角度到0-2π
                        global_angles = np.array(global_angles) % (2 * np.pi)
                        global_data = np.array(global_data)
                        
                        # 按旋转角度排序
                        sorted_indices = np.argsort(global_angles)
                        global_angles_sorted = global_angles[sorted_indices]
                        global_data_sorted = global_data[sorted_indices]
                        
                        curves[key] = {
                            'angles': global_angles_sorted,
                            'data': global_data_sorted
                        }
        
        return curves
    
    def display_curves(self, curves):
        """
        显示旋转角测量曲线
        
        Args:
            curves: 包含旋转角曲线的字典
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # 左齿形曲线
        if 'profile_left' in curves:
            ax1.plot(curves['profile_left']['angles'], curves['profile_left']['data'], 'b-', linewidth=1.5)
            ax1.set_title('Left Profile Rotation Angle Curve')
            ax1.set_xlabel('Rotation Angle (radians)')
            ax1.set_ylabel('Deviation (μm)')
            ax1.grid(True)
        
        # 右齿形曲线
        if 'profile_right' in curves:
            ax2.plot(curves['profile_right']['angles'], curves['profile_right']['data'], 'r-', linewidth=1.5)
            ax2.set_title('Right Profile Rotation Angle Curve')
            ax2.set_xlabel('Rotation Angle (radians)')
            ax2.set_ylabel('Deviation (μm)')
            ax2.grid(True)
        
        # 左齿向曲线
        if 'helix_left' in curves:
            ax3.plot(curves['helix_left']['angles'], curves['helix_left']['data'], 'g-', linewidth=1.5)
            ax3.set_title('Left Helix Rotation Angle Curve')
            ax3.set_xlabel('Rotation Angle (radians)')
            ax3.set_ylabel('Deviation (μm)')
            ax3.grid(True)
        
        # 右齿向曲线
        if 'helix_right' in curves:
            ax4.plot(curves['helix_right']['angles'], curves['helix_right']['data'], 'y-', linewidth=1.5)
            ax4.set_title('Right Helix Rotation Angle Curve')
            ax4.set_xlabel('Rotation Angle (radians)')
            ax4.set_ylabel('Deviation (μm)')
            ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig('rotation_angle_curves.png')
        print("旋转角测量曲线已保存到 rotation_angle_curves.png")
        
        # 显示曲线
        try:
            plt.show()
        except Exception as e:
            print(f"显示曲线失败: {e}")
    
    def run(self):
        """运行显示流程"""
        print("=== 生成旋转角测量曲线 ===")
        
        # 生成模拟数据
        print("生成模拟齿轮数据...")
        mock_data = self.generate_mock_data()
        
        # 创建旋转角曲线
        print("创建旋转角测量曲线...")
        curves = self.create_rotation_angle_curves(mock_data)
        
        # 显示曲线
        print("显示旋转角测量曲线...")
        self.display_curves(curves)
        
        print("=== 旋转角测量曲线生成完成 ===")

if __name__ == "__main__":
    display = RotationAngleCurveDisplay()
    display.run()
