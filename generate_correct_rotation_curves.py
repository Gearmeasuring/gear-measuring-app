#!/usr/bin/env python
"""
生成正确的旋转角测量曲线，展示不同频率分量的波纹
参考图2的格式，生成不连续的波纹曲线
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

class CorrectRotationCurveGenerator:
    """正确的旋转角测量曲线生成器"""
    
    def __init__(self):
        """初始化生成器"""
        pass
    
    def generate_ripple_data(self, num_teeth=33, points_per_tooth=100):
        """
        生成包含不同频率分量的波纹数据
        参考图2的格式，包含偏心、机床振动、噪声等分量
        
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
        
        # 生成全局旋转角度（0到2π）
        total_angle = 2 * np.pi
        global_angles = np.linspace(0, total_angle, num_teeth * points_per_tooth)
        
        # 生成不同频率分量
        # A1: 偏心 (低频)
        eccentric = 1.0 * np.sin(1 * global_angles)
        # A2: 机床振动或方坯振动 (中频)
        machine_vibration = 0.3 * np.sin(4 * global_angles) + 0.2 * np.sin(8 * global_angles)
        # A3: 机床噪声 (高频)
        noise = 0.1 * np.random.randn(len(global_angles))
        
        # 生成齿形和齿向数据
        # 左齿形
        profile_left = eccentric + machine_vibration + noise
        # 右齿形
        profile_right = eccentric + 0.9 * machine_vibration + noise
        # 左齿向
        helix_left = 0.8 * eccentric + 0.7 * machine_vibration + 0.08 * noise
        # 右齿向
        helix_right = 0.7 * eccentric + 0.6 * machine_vibration + 0.08 * noise
        
        # 添加齿距偏差
        for i in range(len(global_angles)):
            tooth_id = i // points_per_tooth
            pitch_dev = 0.05 * np.sin(2 * np.pi * tooth_id / num_teeth)
            profile_left[i] += pitch_dev
            profile_right[i] += pitch_dev
            helix_left[i] += pitch_dev
            helix_right[i] += pitch_dev
        
        # 按齿组织数据
        for tooth_id in range(num_teeth):
            start_idx = tooth_id * points_per_tooth
            end_idx = (tooth_id + 1) * points_per_tooth
            
            tooth_angles = global_angles[start_idx:end_idx]
            
            data['profile_left'][tooth_id] = {
                'angles': tooth_angles,
                'values': profile_left[start_idx:end_idx],
                'eccentric': eccentric[start_idx:end_idx],
                'machine_vibration': machine_vibration[start_idx:end_idx],
                'noise': noise[start_idx:end_idx]
            }
            
            data['profile_right'][tooth_id] = {
                'angles': tooth_angles,
                'values': profile_right[start_idx:end_idx],
                'eccentric': eccentric[start_idx:end_idx],
                'machine_vibration': 0.9 * machine_vibration[start_idx:end_idx],
                'noise': noise[start_idx:end_idx]
            }
            
            data['helix_left'][tooth_id] = {
                'angles': tooth_angles,
                'values': helix_left[start_idx:end_idx],
                'eccentric': 0.8 * eccentric[start_idx:end_idx],
                'machine_vibration': 0.7 * machine_vibration[start_idx:end_idx],
                'noise': 0.08 * noise[start_idx:end_idx]
            }
            
            data['helix_right'][tooth_id] = {
                'angles': tooth_angles,
                'values': helix_right[start_idx:end_idx],
                'eccentric': 0.7 * eccentric[start_idx:end_idx],
                'machine_vibration': 0.6 * machine_vibration[start_idx:end_idx],
                'noise': 0.08 * noise[start_idx:end_idx]
            }
        
        return data
    
    def create_rotation_curves(self, data):
        """
        创建旋转角测量曲线
        
        Args:
            data: 包含波纹数据的字典
            
        Returns:
            dict: 包含旋转角曲线的字典
        """
        curves = {}
        
        for key in data:
            all_angles = []
            all_values = []
            all_eccentric = []
            all_machine_vibration = []
            all_noise = []
            
            for tooth_id, tooth_data in sorted(data[key].items()):
                all_angles.extend(tooth_data['angles'])
                all_values.extend(tooth_data['values'])
                all_eccentric.extend(tooth_data['eccentric'])
                all_machine_vibration.extend(tooth_data['machine_vibration'])
                all_noise.extend(tooth_data['noise'])
            
            curves[key] = {
                'angles': np.array(all_angles),
                'values': np.array(all_values),
                'eccentric': np.array(all_eccentric),
                'machine_vibration': np.array(all_machine_vibration),
                'noise': np.array(all_noise)
            }
        
        return curves
    
    def display_correct_curves(self, curves):
        """
        显示正确的旋转角测量曲线，参考图2的格式
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # 左齿形曲线
        if 'profile_left' in curves:
            self._plot_ripple_curve(ax1, curves['profile_left'], 'Left Profile', 'blue')
        
        # 右齿形曲线
        if 'profile_right' in curves:
            self._plot_ripple_curve(ax2, curves['profile_right'], 'Right Profile', 'red')
        
        # 左齿向曲线
        if 'helix_left' in curves:
            self._plot_ripple_curve(ax3, curves['helix_left'], 'Left Helix', 'green')
        
        # 右齿向曲线
        if 'helix_right' in curves:
            self._plot_ripple_curve(ax4, curves['helix_right'], 'Right Helix', 'yellow')
        
        plt.tight_layout()
        plt.savefig('correct_rotation_curves.png')
        print("正确的旋转角测量曲线已保存到 correct_rotation_curves.png")
        
        # 显示曲线
        try:
            plt.show()
        except Exception as e:
            print(f"显示曲线失败: {e}")
    
    def _plot_ripple_curve(self, ax, curve_data, title, color):
        """
        绘制单个波纹曲线，参考图2的格式
        """
        angles = curve_data['angles']
        values = curve_data['values']
        eccentric = curve_data['eccentric']
        machine_vibration = curve_data['machine_vibration']
        noise = curve_data['noise']
        
        # 绘制总波纹曲线
        ax.plot(angles, values, color=color, linewidth=1.5, label='Total Ripple')
        
        # 绘制不同频率分量
        ax.plot(angles, eccentric, 'b--', linewidth=1.0, label='A1: Eccentric')
        ax.plot(angles, machine_vibration, 'g--', linewidth=1.0, label='A2: Machine Vibration')
        ax.plot(angles, noise, 'r--', linewidth=1.0, label='A3: Noise')
        
        # 设置标题和标签
        ax.set_title(f'{title} Ripple above Rotation Angle')
        ax.set_xlabel('Rotation Angle (radians)')
        ax.set_ylabel('Deviation (μm)')
        ax.grid(True)
        ax.legend()
        
        # 添加频率标注，类似于图2
        ax.text(0.05, 0.95, 'z=33', transform=ax.transAxes, fontsize=10, fontweight='bold')
        ax.text(0.05, 0.90, 'A1: Eccentric', transform=ax.transAxes, fontsize=8, color='blue')
        ax.text(0.05, 0.85, 'A2: Machine Vibration', transform=ax.transAxes, fontsize=8, color='green')
        ax.text(0.05, 0.80, 'A3: Noise', transform=ax.transAxes, fontsize=8, color='red')
    
    def run(self):
        """运行生成流程"""
        print("=== 生成正确的旋转角测量曲线 ===")
        
        # 生成波纹数据
        print("生成包含不同频率分量的波纹数据...")
        data = self.generate_ripple_data()
        
        # 创建旋转角曲线
        print("创建旋转角测量曲线...")
        curves = self.create_rotation_curves(data)
        
        # 显示曲线
        print("显示正确的旋转角测量曲线...")
        self.display_correct_curves(curves)
        
        print("=== 正确的旋转角测量曲线生成完成 ===")

if __name__ == "__main__":
    generator = CorrectRotationCurveGenerator()
    generator.run()
