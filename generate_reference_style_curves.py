#!/usr/bin/env python
"""
生成类似参考图像的连续曲线
显示左右齿面的对比，类似用户提供的参考图
"""
import numpy as np
import matplotlib.pyplot as plt
import re

class ReferenceStyleCurveGenerator:
    """
    参考样式曲线生成器
    """
    
    def __init__(self, mka_file):
        """
        初始化生成器
        """
        self.mka_file = mka_file
        self.num_teeth = 87
        self.data = {
            'profile_left': {'teeth': [], 'values': []},
            'profile_right': {'teeth': [], 'values': []},
            'helix_left': {'teeth': [], 'values': []},
            'helix_right': {'teeth': [], 'values': []}
        }
    
    def parse_mka_file(self):
        """
        解析MKA文件
        """
        print(f"解析MKA文件: {self.mka_file}")
        
        # 读取文件内容
        with open(self.mka_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 提取齿数
        teeth_match = re.search(r'Z\u00e4hnezahl z.*?:\s*(\d+)', content)
        if teeth_match:
            self.num_teeth = int(teeth_match.group(1))
            print(f"提取到齿数: {self.num_teeth}")
        
        # 提取齿形数据
        print("提取齿形数据...")
        self._extract_data(content, 'Profil', 10)  # 每齿取10个点，生成更连续的曲线
        
        # 提取齿向数据
        print("提取齿向数据...")
        self._extract_data(content, 'Flankenlinie', 15)  # 每齿取15个点
    
    def _extract_data(self, content, data_type, points_per_tooth):
        """
        提取数据
        """
        if data_type == 'Profil':
            pattern = re.compile(r'Profil:\s*Zahn-Nr\.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)\s*/\s*\d+\s*Werte.*?\n((?:\s*[-+]?\d*\.?\d+\s*)*)', re.DOTALL)
            data_keys = {'links': 'profile_left', 'rechts': 'profile_right'}
        else:
            pattern = re.compile(r'Flankenlinie:\s*Zahn-Nr\.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)\s*/\s*\d+\s*Werte.*?\n((?:\s*[-+]?\d*\.?\d+\s*)*)', re.DOTALL)
            data_keys = {'links': 'helix_left', 'rechts': 'helix_right'}
        
        matches = pattern.finditer(content)
        
        for match in matches:
            tooth_id = match.group(1)
            side = match.group(2)
            data_text = match.group(3)
            
            # 提取数值
            numbers = re.findall(r'[-+]?\d*\.?\d+', data_text)
            values = []
            for num in numbers:
                try:
                    if num.startswith('.'):
                        num = '0' + num
                    elif num.startswith('-.'):
                        num = '-0' + num[1:]
                    values.append(float(num))
                except ValueError:
                    continue
            
            # 减少数据点，使曲线更连续
            if len(values) > points_per_tooth:
                step = max(1, len(values) // points_per_tooth)
                values = values[::step][:points_per_tooth]
            
            # 转换齿号
            tooth_num = re.search(r'(\d+)', tooth_id)
            if tooth_num:
                tooth_idx = int(tooth_num.group(1)) - 1
                
                # 生成齿位置数据
                num_points = len(values)
                if num_points > 0:
                    tooth_positions = np.linspace(tooth_idx, tooth_idx + 1, num_points)
                    
                    # 保存数据
                    if side in data_keys:
                        key = data_keys[side]
                        self.data[key]['teeth'].extend(tooth_positions.tolist())
                        self.data[key]['values'].extend(values)
    
    def display_reference_style_curves(self):
        """
        显示类似参考图像的曲线
        """
        print("显示参考样式的旋转角度曲线...")
        
        # 创建一行两列的布局，显示左右齿面的对比
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 10))
        
        # 齿形对比
        if self.data['profile_left']['teeth'] and self.data['profile_right']['teeth']:
            # 左齿形（蓝色）
            ax1.plot(self.data['profile_left']['teeth'], self.data['profile_left']['values'], 'b-', linewidth=1.0, label='Left Profile')
            # 右齿形（红色）
            ax1.plot(self.data['profile_right']['teeth'], self.data['profile_right']['values'], 'r-', linewidth=1.0, label='Right Profile')
            ax1.set_title('Profile Comparison - 87 Teeth')
            ax1.set_xlabel('Tooth Number')
            ax1.set_ylabel('Deviation (μm)')
            ax1.set_xlim(0, self.num_teeth)
            ax1.grid(True, alpha=0.2)
            ax1.legend()
            ax1.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax1.transAxes, fontsize=10, fontweight='bold')
        
        # 齿向对比
        if self.data['helix_left']['teeth'] and self.data['helix_right']['teeth']:
            # 左齿向（绿色）
            ax2.plot(self.data['helix_left']['teeth'], self.data['helix_left']['values'], 'g-', linewidth=1.0, label='Left Helix')
            # 右齿向（黄色）
            ax2.plot(self.data['helix_right']['teeth'], self.data['helix_right']['values'], 'y-', linewidth=1.0, label='Right Helix')
            ax2.set_title('Helix Comparison - 87 Teeth')
            ax2.set_xlabel('Tooth Number')
            ax2.set_ylabel('Deviation (μm)')
            ax2.set_xlim(0, self.num_teeth)
            ax2.grid(True, alpha=0.2)
            ax2.legend()
            ax2.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax2.transAxes, fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('reference_style_87_teeth_curves.png')
        print("参考样式的旋转角度曲线已保存到 reference_style_87_teeth_curves.png")
        
        # 显示组合图
        plt.show()
    
    def run(self):
        """
        运行生成流程
        """
        print("=== 生成参考样式的87个齿旋转角度曲线 ===")
        
        # 解析MKA文件
        self.parse_mka_file()
        
        # 显示曲线
        self.display_reference_style_curves()
        
        print("=== 参考样式曲线生成完成 ===")

if __name__ == "__main__":
    mka_file = "263751-018-WAV.mka"
    generator = ReferenceStyleCurveGenerator(mka_file)
    generator.run()
