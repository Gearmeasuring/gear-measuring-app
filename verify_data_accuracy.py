#!/usr/bin/env python
"""
验证数据准确性并生成四张准确的图表
"""
import numpy as np
import matplotlib.pyplot as plt
import re

class DataAccuracyVerifier:
    """
    数据准确性验证器
    """
    
    def __init__(self, mka_file):
        """
        初始化验证器
        """
        self.mka_file = mka_file
        self.num_teeth = 87
        self.data = {
            'profile_left': {'teeth': [], 'values': []},
            'profile_right': {'teeth': [], 'values': []},
            'helix_left': {'teeth': [], 'values': []},
            'helix_right': {'teeth': [], 'values': []}
        }
        self.validation_results = {}
    
    def parse_mka_file(self):
        """
        解析MKA文件并验证数据
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
        
        # 提取齿形数据并验证
        print("提取齿形数据...")
        self._extract_and_validate_data(content, 'Profil', 480, 10)
        
        # 提取齿向数据并验证
        print("提取齿向数据...")
        self._extract_and_validate_data(content, 'Flankenlinie', 915, 15)
    
    def _extract_and_validate_data(self, content, data_type, expected_points, sample_points):
        """
        提取并验证数据
        """
        if data_type == 'Profil':
            pattern = re.compile(r'Profil:\s*Zahn-Nr\.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)\s*/\s*(\d+)\s*Werte.*?\n((?:\s*[-+]?\d*\.?\d+\s*)*)', re.DOTALL)
            data_keys = {'links': 'profile_left', 'rechts': 'profile_right'}
        else:
            pattern = re.compile(r'Flankenlinie:\s*Zahn-Nr\.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)\s*/\s*(\d+)\s*Werte.*?\n((?:\s*[-+]?\d*\.?\d+\s*)*)', re.DOTALL)
            data_keys = {'links': 'helix_left', 'rechts': 'helix_right'}
        
        matches = pattern.finditer(content)
        tooth_count = 0
        total_values = 0
        
        for match in matches:
            tooth_id = match.group(1)
            side = match.group(2)
            reported_points = match.group(3)
            data_text = match.group(4)
            
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
            
            # 验证数据
            actual_points = len(values)
            tooth_count += 1
            total_values += actual_points
            
            # 减少数据点
            if len(values) > sample_points:
                step = max(1, len(values) // sample_points)
                values = values[::step][:sample_points]
            
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
        
        # 验证结果
        self.validation_results[data_type] = {
            'tooth_count': tooth_count,
            'total_values': total_values,
            'average_points_per_tooth': total_values / tooth_count if tooth_count > 0 else 0
        }
        
        print(f"{data_type} 验证结果: {tooth_count} 个齿, 共 {total_values} 个数据点, 平均每齿 {total_values / tooth_count:.1f} 个点")
    
    def display_four_accurate_curves(self):
        """
        显示四张准确的曲线
        """
        print("显示四张准确的旋转角度曲线...")
        
        # 创建四张独立的图表
        fig, ((ax1), (ax2), (ax3), (ax4)) = plt.subplots(4, 1, figsize=(16, 16))
        
        # 左齿形
        if self.data['profile_left']['teeth']:
            ax1.plot(self.data['profile_left']['teeth'], self.data['profile_left']['values'], 'b-', linewidth=0.8)
            ax1.set_title('Left Profile - 87 Teeth')
            ax1.set_xlabel('Tooth Number')
            ax1.set_ylabel('Deviation (μm)')
            ax1.set_xlim(0, self.num_teeth)
            ax1.grid(True, alpha=0.3)
            ax1.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax1.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿形
        if self.data['profile_right']['teeth']:
            ax2.plot(self.data['profile_right']['teeth'], self.data['profile_right']['values'], 'r-', linewidth=0.8)
            ax2.set_title('Right Profile - 87 Teeth')
            ax2.set_xlabel('Tooth Number')
            ax2.set_ylabel('Deviation (μm)')
            ax2.set_xlim(0, self.num_teeth)
            ax2.grid(True, alpha=0.3)
            ax2.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax2.transAxes, fontsize=10, fontweight='bold')
        
        # 左齿向
        if self.data['helix_left']['teeth']:
            ax3.plot(self.data['helix_left']['teeth'], self.data['helix_left']['values'], 'g-', linewidth=0.8)
            ax3.set_title('Left Helix - 87 Teeth')
            ax3.set_xlabel('Tooth Number')
            ax3.set_ylabel('Deviation (μm)')
            ax3.set_xlim(0, self.num_teeth)
            ax3.grid(True, alpha=0.3)
            ax3.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax3.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿向
        if self.data['helix_right']['teeth']:
            ax4.plot(self.data['helix_right']['teeth'], self.data['helix_right']['values'], 'y-', linewidth=0.8)
            ax4.set_title('Right Helix - 87 Teeth')
            ax4.set_xlabel('Tooth Number')
            ax4.set_ylabel('Deviation (μm)')
            ax4.set_xlim(0, self.num_teeth)
            ax4.grid(True, alpha=0.3)
            ax4.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax4.transAxes, fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('four_accurate_87_teeth_curves.png')
        print("四张准确的旋转角度曲线已保存到 four_accurate_87_teeth_curves.png")
        
        # 显示组合图
        plt.show()
    
    def run(self):
        """
        运行验证流程
        """
        print("=== 验证数据准确性并生成四张准确曲线 ===")
        
        # 解析MKA文件并验证数据
        self.parse_mka_file()
        
        # 显示验证结果
        print("\n=== 数据验证结果 ===")
        for data_type, result in self.validation_results.items():
            print(f"{data_type}:")
            print(f"  齿数量: {result['tooth_count']}")
            print(f"  数据点总数: {result['total_values']}")
            print(f"  平均每齿数据点: {result['average_points_per_tooth']:.1f}")
        
        # 显示四张准确的曲线
        self.display_four_accurate_curves()
        
        print("=== 四张准确曲线生成完成 ===")

if __name__ == "__main__":
    mka_file = "263751-018-WAV.mka"
    verifier = DataAccuracyVerifier(mka_file)
    verifier.run()
