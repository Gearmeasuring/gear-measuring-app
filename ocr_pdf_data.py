import fitz
import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
import csv

# 设置Tesseract OCR路径
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def ocr_pdf_data(pdf_path):
    """使用OCR从PDF文件中提取数据"""
    print(f"开始使用OCR处理PDF文件: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    print(f"PDF文件页数: {doc.page_count}")
    
    # 提取所有页面为图像并进行OCR
    all_text = []
    
    for page_num in range(doc.page_count):
        print(f"处理第{page_num + 1}页...")
        page = doc[page_num]
        
        # 将页面转换为图像
        zoom = 2.0  # 放大倍数以提高OCR精度
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # 转换为PIL图像
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 转换为OpenCV格式
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # 预处理图像以提高OCR精度
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # 应用阈值处理
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 降噪
        denoised = cv2.medianBlur(binary, 3)
        
        # 使用Tesseract进行OCR
        try:
            text = pytesseract.image_to_string(denoised, lang='chi_sim+eng', config='--psm 6')
            all_text.append(text)
            print(f"第{page_num + 1}页OCR完成")
            
            # 保存预处理后的图像用于调试
            debug_img_path = f"page_{page_num + 1}_processed.png"
            cv2.imwrite(debug_img_path, denoised)
            print(f"预处理图像已保存到: {debug_img_path}")
            
        except Exception as e:
            print(f"OCR错误: {e}")
            all_text.append("")
    
    doc.close()
    
    # 合并所有OCR结果
    full_text = "\n".join(all_text)
    print(f"OCR总文本长度: {len(full_text)} 字符")
    
    # 分析OCR结果
    print("\nOCR结果预览:")
    print(full_text[:1000] + "..." if len(full_text) > 1000 else full_text)
    
    # 尝试识别表格数据
    print("\n尝试识别表格数据...")
    
    # 1. 查找可能的数据行
    lines = full_text.split('\n')
    data_lines = []
    
    # 2. 尝试识别数据行（包含数字的行）
    for line in lines:
        line = line.strip()
        if line:
            # 检查是否包含数字
            if any(char.isdigit() for char in line):
                # 进一步检查是否包含小数点或其他数据特征
                if any(char in '.+-' for char in line):
                    data_lines.append(line)
    
    print(f"找到 {len(data_lines)} 行可能的数据")
    
    # 3. 打印数据行预览
    print("\n数据行预览:")
    for i, line in enumerate(data_lines[:10]):
        print(f"{i+1}: {line}")
    
    # 4. 尝试解析数据
    table_data = []
    headers = []
    
    # 尝试识别表头
    if data_lines:
        # 假设第一行是表头
        if len(data_lines) > 1:
            # 分析数据格式
            first_data_line = data_lines[0]
            
            # 尝试按空格或制表符分割
            parts = first_data_line.split()
            print(f"\n第一行数据分割结果: {parts}")
            
            # 生成表头
            headers = [f"列{i+1}" for i in range(len(parts))]
            table_data.append(headers)
            
            # 解析数据行
            for line in data_lines:
                parts = line.split()
                # 确保数据长度与表头一致
                if len(parts) == len(headers):
                    table_data.append(parts)
                else:
                    # 处理长度不一致的情况
                    table_data.append(parts + [''] * (len(headers) - len(parts)))
    
    # 5. 保存为CSV文件
    output_csv = os.path.splitext(pdf_path)[0] + "_ocr_extracted.csv"
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(table_data)
    
    print(f"\nOCR数据已保存到: {output_csv}")
    print(f"表格行数: {len(table_data)}")
    
    # 6. 生成HTML表格
    output_html = os.path.splitext(pdf_path)[0] + "_ocr_table.html"
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF OCR数据表格</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #2196F3;
            color: white;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #e8f4f8;
        }
        .info {
            margin-top: 20px;
            padding: 15px;
            background-color: #e3f2fd;
            border-left: 4px solid #2196F3;
        }
        .ocr-note {
            margin-top: 20px;
            padding: 15px;
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>PDF OCR数据提取表格</h1>
        <div class="info">
            <p><strong>源文件:</strong> ''' + os.path.basename(pdf_path) + '''</p>
            <p><strong>提取时间:</strong> ''' + __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
            <p><strong>数据行数:</strong> ''' + str(len(table_data) - 1) + '''</p>
        </div>
        <div class="ocr-note">
            <p><strong>OCR提取说明:</strong></p>
            <p>• 本表格数据通过光学字符识别(OCR)技术从PDF图像中提取</p>
            <p>• 由于OCR技术限制，可能存在识别误差</p>
            <p>• 建议对提取的数据进行人工核对</p>
        </div>
        <table>
''')
        
        # 写入表头
        f.write('            <tr>')
        for header in headers:
            f.write(f'<th>{header}</th>')
        f.write('</tr>\n')
        
        # 写入数据行
        for row in table_data[1:]:
            f.write('            <tr>')
            for cell in row:
                f.write(f'<td>{cell}</td>')
            f.write('</tr>\n')
        
        f.write('''
        </table>
    </div>
</body>
</html>
''')
    
    print(f"HTML表格已保存到: {output_html}")
    
    # 保存原始OCR文本
    output_txt = os.path.splitext(pdf_path)[0] + "_ocr_raw.txt"
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    print(f"原始OCR文本已保存到: {output_txt}")
    
    return output_csv, output_html, output_txt

if __name__ == "__main__":
    # 设置Tesseract路径（如果系统环境变量中没有）
    # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    pdf_file = "==3015608970000AF0000000000-251126083.pdf"
    ocr_pdf_data(pdf_file)
