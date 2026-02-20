import os
import struct
import binascii
import numpy as np

def analyze_binary_file(file_path):
    """分析二进制文件结构"""
    print(f"分析文件: {file_path}")
    print(f"文件大小: {os.path.getsize(file_path)} 字节")
    
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # 分析文件头
    header = content[:100]
    print("\n文件头 (十六进制):")
    print(binascii.hexlify(header).decode('utf-8'))
    
    print("\n文件头 (原始):")
    print(repr(header))
    
    # 尝试识别文件格式
    print("\n尝试识别文件格式:")
    
    # 检查常见的文件头
    magic_numbers = {
        b'PK': 'ZIP file',
        b'%PDF': 'PDF file',
        b'GIF8': 'GIF image',
        b'\xff\xd8': 'JPEG image',
        b'RIFF': 'RIFF container',
        b'BM': 'BMP image',
        b'\x89PNG': 'PNG image',
        b'#!': 'Script file',
        b'{': 'JSON file',
        b'<?xml': 'XML file',
        b'\x00\x00\x00\x00': '可能是某种二进制数据格式'
    }
    
    for magic, desc in magic_numbers.items():
        if header.startswith(magic):
            print(f"检测到: {desc}")
            break
    else:
        print("未知文件类型")
    
    # 分析数据结构
    print("\n分析数据结构:")
    
    # 检查是否有明显的数据块
    chunk_markers = []
    for i in range(len(content)):
        # 寻找可能的数据块标记
        if content[i:i+4] == b'\x00\x00\x00\x00':
            chunk_markers.append(i)
    
    if chunk_markers:
        print(f"找到 {len(chunk_markers)} 个可能的数据块标记")
        for i, pos in enumerate(chunk_markers[:10]):
            print(f"  标记 {i+1}: 位置 {pos}")
    
    # 尝试解析数值数据
    print("\n尝试解析数值数据:")
    
    # 检查是否有浮点数据
    try:
        # 尝试读取不同大小的浮点数
        for offset in range(100, min(1000, len(content)), 4):
            if offset + 4 <= len(content):
                try:
                    value = struct.unpack('<f', content[offset:offset+4])[0]
                    if abs(value) < 10000:  # 合理范围内的数值
                        print(f"偏移 {offset}: {value}")
                except:
                    pass
    except Exception as e:
        print(f"解析浮点数错误: {e}")
    
    # 检查是否有整数数据
    try:
        for offset in range(100, min(1000, len(content)), 2):
            if offset + 2 <= len(content):
                try:
                    value = struct.unpack('<H', content[offset:offset+2])[0]
                    if value < 10000:  # 合理范围内的数值
                        print(f"偏移 {offset} (uint16): {value}")
                except:
                    pass
    except Exception as e:
        print(f"解析整数错误: {e}")
    
    # 检查文件的整体结构
    print("\n文件整体结构分析:")
    
    # 计算非零字节的比例
    non_zero_bytes = sum(1 for b in content if b != 0)
    zero_bytes = len(content) - non_zero_bytes
    print(f"非零字节: {non_zero_bytes} ({non_zero_bytes/len(content)*100:.2f}%)")
    print(f"零字节: {zero_bytes} ({zero_bytes/len(content)*100:.2f}%)")
    
    # 分析字节分布
    byte_counts = [0] * 256
    for b in content:
        byte_counts[b] += 1
    
    print("\n字节分布统计 (前20个):")
    sorted_bytes = sorted(range(256), key=lambda x: byte_counts[x], reverse=True)[:20]
    for b in sorted_bytes:
        print(f"0x{b:02x} ({chr(b) if 32 <= b <= 126 else ' '}): {byte_counts[b]} 次")

if __name__ == "__main__":
    file_path = "340446-z19--cp.csv"
    analyze_binary_file(file_path)