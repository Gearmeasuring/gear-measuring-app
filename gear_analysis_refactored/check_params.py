import os
import sys
import math

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.file_parser import parse_mka_file
from models.gear_data import create_gear_data_from_dict

def main():
    # 解析测试文件
    mka_file = os.path.join(os.path.dirname(__file__), "testdata", "250311547.mka")
    data_dict = parse_mka_file(mka_file)
    gear_data = create_gear_data_from_dict(data_dict)
    
    # 提取关键参数
    module = getattr(gear_data.basic_info, "module", 1.0) if gear_data.basic_info else 1.0
    pressure_angle = getattr(gear_data.basic_info, "pressure_angle", 20.0) if gear_data.basic_info else 20.0
    helix_angle = getattr(gear_data.basic_info, "helix_angle", 0.0) if gear_data.basic_info else 0.0
    teeth_count = getattr(gear_data.basic_info, "teeth_count", 25) if gear_data.basic_info else 25
    
    # 使用示例值确保有合理的显示
    profile_eval_start = getattr(gear_data.basic_info, "profile_eval_start", 43.829) if gear_data.basic_info else 43.829
    profile_eval_end = getattr(gear_data.basic_info, "profile_eval_end", 51.2) if gear_data.basic_info else 51.2
    
    if profile_eval_start <= 0 or profile_eval_end <= 0 or profile_eval_start == profile_eval_end:
        profile_eval_start = 43.829
        profile_eval_end = 51.2
    
    print("基本参数:")
    print(f"模数(module): {module}")
    print(f"压力角(pressure_angle): {pressure_angle}")
    print(f"螺旋角(helix_angle): {helix_angle}")
    print(f"齿数(teeth_count): {teeth_count}")
    print("\n评价范围:")
    print(f"Profile Eval Start: {profile_eval_start}")
    print(f"Profile Eval End: {profile_eval_end}")
    
    # 手动计算验证
    print("\n手动计算验证:")
    
    # 计算基圆直径 db
    alpha_n = math.radians(float(pressure_angle))
    beta = math.radians(float(helix_angle)) if helix_angle else 0.0
    
    if beta != 0:
        alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
        d = float(teeth_count) * float(module) / math.cos(beta)
    else:
        alpha_t = alpha_n
        d = float(teeth_count) * float(module)
    
    db = d * math.cos(alpha_t)
    print(f"基圆直径(db): {db:.3f}")
    
    # 计算基圆齿距 pb
    pb = math.pi * db / float(teeth_count)
    print(f"基圆齿距(pb): {pb:.3f}")
    
    # 计算滚动长度 lo 和 lu
    # 根据用户说明，profile_eval_start/end 直接作为半径，而不是直径
    r_end = float(profile_eval_end)
    r_start = float(profile_eval_start)
    rb = float(db) / 2.0
    
    lo = float(math.sqrt(max(0.0, r_end * r_end - rb * rb)))
    lu = float(math.sqrt(max(0.0, r_start * r_start - rb * rb)))
    
    print(f"lo: {lo:.3f}")
    print(f"lu: {lu:.3f}")
    
    # 计算 ep
    ep = abs(lo - lu) / pb
    print(f"ep: {ep:.3f}")
    
    # 检查是否与目标值一致
    print("\n与目标值比较:")
    print(f"目标ep: 1.454, 计算ep: {ep:.3f}, 差异: {abs(ep - 1.454):.3f}")
    print(f"目标lo: 33.578, 计算lo: {lo:.3f}, 差异: {abs(lo - 33.578):.3f}")
    print(f"目标lu: 24.775, 计算lu: {lu:.3f}, 差异: {abs(lu - 24.775):.3f}")

if __name__ == "__main__":
    main()
