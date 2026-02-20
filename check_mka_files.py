import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'gear_analysis_refactored'))

print("=== 检查MKA文件读取 ===")
print(f"当前工作目录: {os.getcwd()}")

from utils.gear_overlap_calculator import GearOverlapCalculator

# 创建计算器实例
calculator = GearOverlapCalculator()

# 检查文件1
print("\n=== 检查文件: 263751-018-WAV.mka ===")
mka_file1 = "263751-018-WAV.mka"
print(f"文件存在: {os.path.exists(mka_file1)}")
print(f"文件路径: {os.path.abspath(mka_file1)}")

if os.path.exists(mka_file1):
    try:
        data = calculator.read_from_mka_file(mka_file1)
        print("成功读取文件")
        print(f"齿轮参数: {data['gear_data']}")
        print(f"齿形数据: {data['profile_data'].keys() if data['profile_data'] else 'None'}")
        print(f"齿向数据: {data['flank_data'].keys() if data['flank_data'] else 'None'}")
    except Exception as e:
        print(f"读取失败: {e}")
        import traceback
        traceback.print_exc()

# 检查文件2
print("\n=== 检查文件: 004-xiaoxiao1.mka ===")
mka_file2 = "004-xiaoxiao1.mka"
print(f"文件存在: {os.path.exists(mka_file2)}")
print(f"文件路径: {os.path.abspath(mka_file2)}")

if os.path.exists(mka_file2):
    try:
        data = calculator.read_from_mka_file(mka_file2)
        print("成功读取文件")
        print(f"齿轮参数: {data['gear_data']}")
        print(f"齿形数据: {data['profile_data'].keys() if data['profile_data'] else 'None'}")
        print(f"齿向数据: {data['flank_data'].keys() if data['flank_data'] else 'None'}")
    except Exception as e:
        print(f"读取失败: {e}")
        import traceback
        traceback.print_exc()
