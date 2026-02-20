import fitz
import csv
import re
import os

def extract_pdf_data(pdf_path):
    """从PDF文件中提取数据并整理成表格"""
    print(f"开始处理PDF文件: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    print(f"PDF文件页数: {doc.page_count}")
    
    # 提取所有文本
    all_text = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text("text")
        all_text.append(text)
        print(f"第{page_num + 1}页提取完成")
    
    doc.close()
    
    # 合并所有文本
    full_text = "\n".join(all_text)
    print(f"总文本长度: {len(full_text)} 字符")
    
    # 分析文本内容
    print("\n文本内容预览:")
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
            parts = re.split(r'\s+', first_data_line)
            print(f"\n第一行数据分割结果: {parts}")
            
            # 生成表头
            headers = [f"列{i+1}" for i in range(len(parts))]
            table_data.append(headers)
            
            # 解析数据行
            for line in data_lines:
                parts = re.split(r'\s+', line)
                # 确保数据长度与表头一致
                if len(parts) == len(headers):
                    table_data.append(parts)
                else:
                    # 处理长度不一致的情况
                    table_data.append(parts + [''] * (len(headers) - len(parts)))
    
    # 5. 保存为CSV文件
    output_csv = os.path.splitext(pdf_path)[0] + "_extracted.csv"
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(table_data)
    
    print(f"\n数据已保存到: {output_csv}")
    print(f"表格行数: {len(table_data)}")
    
    # 6. 生成HTML表格
    output_html = os.path.splitext(pdf_path)[0] + "_table.html"
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF数据表格</title>
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
            background-color: #4CAF50;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>PDF数据提取表格</h1>
        <div class="info">
            <p><strong>源文件:</strong> ''' + os.path.basename(pdf_path) + '''</p>
            <p><strong>提取时间:</strong> ''' + __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
            <p><strong>数据行数:</strong> ''' + str(len(table_data) - 1) + '''</p>
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
    
    return output_csv, output_html

if __name__ == "__main__":
    pdf_file = "==3015608970000AF0000000000-251126083.pdf"
    extract_pdf_data(pdf_file)
