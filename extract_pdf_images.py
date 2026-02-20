import fitz
import os
import cv2
import numpy as np
from PIL import Image

def extract_pdf_images(pdf_path):
    """从PDF文件中提取图像"""
    print(f"开始从PDF中提取图像: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    print(f"PDF文件页数: {doc.page_count}")
    
    # 创建输出目录
    output_dir = os.path.splitext(pdf_path)[0] + "_images"
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}")
    
    # 提取每一页的图像
    for page_num in range(doc.page_count):
        print(f"处理第{page_num + 1}页...")
        page = doc[page_num]
        
        # 将页面转换为图像
        zoom = 3.0  # 高分辨率以提高OCR精度
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # 保存为PNG图像
        image_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        pix.save(image_path)
        print(f"已保存图像: {image_path}")
        
        # 检查图像质量
        img = Image.open(image_path)
        width, height = img.size
        print(f"图像大小: {width} x {height}")
        
        # 显示图像信息
        print(f"图像格式: {img.format}")
        print(f"图像模式: {img.mode}")
    
    doc.close()
    
    print(f"\n图像提取完成!")
    print(f"共提取 {doc.page_count} 张图像")
    print(f"图像保存位置: {output_dir}")
    
    # 生成使用说明
    create_usage_instructions(output_dir)
    
    return output_dir

def create_usage_instructions(output_dir):
    """创建使用说明文件"""
    instructions = f"""# PDF图像提取说明

## 提取结果
- 已从PDF文件中提取 {len(os.listdir(output_dir))} 张图像
- 图像保存位置: {output_dir}

## 如何使用这些图像

### 方法1: 使用在线OCR工具
1. 访问以下在线OCR工具之一:
   - ABBYY FineReader Online: https://online.abbyy.com/zh-cn/ocr/
   - Online OCR: https://www.onlineocr.net/
   - Google Drive: 上传图像后使用"打开方式→Google文档"
   - Microsoft OneDrive: 上传图像后使用"打开方式→Word"

2. 上传提取的图像文件
3. 选择语言为"中文"
4. 选择输出格式为"Excel"或"Word"
5. 开始OCR识别
6. 下载识别结果

### 方法2: 使用手机OCR应用
1. 将图像传输到手机
2. 使用以下应用:
   - 微软Office Lens (免费)
   - CamScanner
   - Adobe Scan
3. 扫描图像并导出为Excel或CSV

### 方法3: 使用其他OCR软件
1. Adobe Acrobat Pro: 内置OCR功能
2. ABBYY FineReader: 专业OCR软件
3. Readiris: 另一个优秀的OCR工具

## 注意事项
- 提取的图像分辨率较高，有利于OCR识别
- 表格数据应该能够被大多数OCR工具正确识别
- 建议使用支持表格识别的OCR工具以获得最佳效果
"""
    
    instructions_path = os.path.join(output_dir, "使用说明.txt")
    with open(instructions_path, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"\n已生成使用说明: {instructions_path}")

if __name__ == "__main__":
    pdf_file = "==3015608970000AF0000000000-251126083.pdf"
    extract_pdf_images(pdf_file)
