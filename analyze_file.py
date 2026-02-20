import os
import csv
import struct
import binascii

# 分析文件
def analyze_file(file_path):
    print(f"Analyzing file: {file_path}")
    print(f"File size: {os.path.getsize(file_path)} bytes")
    
    # 读取文件头
    with open(file_path, 'rb') as f:
        header = f.read(100)
    
    print("\nFile header (hex):")
    print(binascii.hexlify(header[:50]).decode('utf-8'))
    
    print("\nFile header (raw):")
    print(repr(header[:50]))
    
    # 检查是否有CSV特征
    print("\nChecking for CSV patterns...")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i < 5:
                    print(f"Line {i+1}: {repr(line[:100])}")
                if i >= 10:
                    break
    except Exception as e:
        print(f"Error reading as text: {e}")
    
    # 尝试检测文件类型
    print("\nDetecting file type...")
    magic_numbers = {
        b'PK': 'ZIP file',
        b'%PDF': 'PDF file',
        b'GIF8': 'GIF image',
        b'\xff\xd8': 'JPEG image',
        b'RIFF': 'RIFF container (WAV, AVI)',
        b'BM': 'BMP image',
        b'\x89PNG': 'PNG image',
        b'#!': 'Script file',
        b'{': 'JSON file',
        b'<?xml': 'XML file'
    }
    
    for magic, desc in magic_numbers.items():
        if header.startswith(magic):
            print(f"Detected: {desc}")
            break
    else:
        print("Unknown file type")

if __name__ == "__main__":
    file_path = "340446-z19--cp.csv"
    analyze_file(file_path)