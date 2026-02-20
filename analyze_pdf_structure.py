import fitz
import os
import json

def analyze_pdf_structure(pdf_path):
    """分析PDF文件结构并尝试提取数据"""
    print(f"开始分析PDF文件结构: {pdf_path}")
    
    # 打开PDF文件
    doc = fitz.open(pdf_path)
    print(f"PDF文件页数: {doc.page_count}")
    print(f"PDF文件大小: {os.path.getsize(pdf_path)} 字节")
    
    # 提取PDF元数据
    metadata = doc.metadata
    print("\nPDF元数据:")
    for key, value in metadata.items():
        if value:
            print(f"{key}: {value}")
    
    # 分析每个页面
    page_analyses = []
    
    for page_num in range(doc.page_count):
        print(f"\n分析第{page_num + 1}页...")
        page = doc[page_num]
        
        # 获取页面大小
        page_rect = page.rect
        print(f"页面大小: {page_rect.width:.2f} x {page_rect.height:.2f}")
        
        # 尝试不同的文本提取方法
        print("\n尝试提取文本 (text模式):")
        text = page.get_text("text")
        print(f"提取的文本长度: {len(text)} 字符")
        if text.strip():
            print(f"文本预览: {text[:200]}..." if len(text) > 200 else text)
        
        print("\n尝试提取文本 (blocks模式):")
        blocks = page.get_text("blocks")
        print(f"找到 {len(blocks)} 个文本块")
        
        # 分析文本块
        block_text = []
        for i, block in enumerate(blocks):
            if block[4].strip():
                block_text.append(block[4].strip())
                if i < 3:  # 只显示前3个文本块
                    print(f"  文本块 {i+1}: {block[4].strip()[:100]}..." if len(block[4]) > 100 else block[4].strip())
        
        # 尝试提取文本 (words模式)
        print("\n尝试提取文本 (words模式):")
        words = page.get_text("words")
        print(f"找到 {len(words)} 个单词")
        if words:
            word_text = " ".join([w[4] for w in words if w[4].strip()])
            print(f"单词预览: {word_text[:200]}..." if len(word_text) > 200 else word_text)
        
        # 检查是否有图像
        images = page.get_images(full=True)
        print(f"\n找到 {len(images)} 个图像")
        
        # 检查是否有表格
        print("\n检查表格结构...")
        # 尝试检测表格（基于文本块的排列）
        if blocks:
            # 按垂直位置排序文本块
            blocks.sort(key=lambda b: b[1])
            # 分析文本块的水平对齐
            x_positions = []
            for block in blocks:
                if block[4].strip():
                    x_positions.append(block[0])
            
            if x_positions:
                # 计算唯一的x位置（考虑小误差）
                unique_x = []
                x_positions.sort()
                for x in x_positions:
                    if not unique_x or x - unique_x[-1] > 5:
                        unique_x.append(x)
                print(f"检测到 {len(unique_x)} 个可能的列位置")
        
        # 保存页面分析结果
        page_analyses.append({
            'page_num': page_num + 1,
            'width': page_rect.width,
            'height': page_rect.height,
            'text_length': len(text),
            'block_count': len(blocks),
            'word_count': len(words),
            'image_count': len(images),
            'text_preview': text[:500] if text else "",
            'block_text': block_text[:5]  # 只保存前5个文本块
        })
    
    doc.close()
    
    # 保存分析结果
    analysis_output = os.path.splitext(pdf_path)[0] + "_analysis.json"
    with open(analysis_output, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': metadata,
            'page_count': len(page_analyses),
            'pages': page_analyses
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n分析结果已保存到: {analysis_output}")
    
    # 尝试生成简单的表格
    print("\n尝试生成表格...")
    
    # 收集所有文本数据
    all_text_data = []
    for page_info in page_analyses:
        if page_info['block_text']:
            all_text_data.extend(page_info['block_text'])
    
    # 尝试识别表格数据
    table_data = []
    headers = []
    
    if all_text_data:
        # 假设第一行是表头
        first_line = all_text_data[0]
        parts = first_line.split()
        if parts:
            headers = [f"列{i+1}" for i in range(len(parts))]
            table_data.append(headers)
            
            # 解析数据行
            for line in all_text_data:
                parts = line.split()
                if parts and len(parts) == len(headers):
                    table_data.append(parts)
    
    # 保存表格数据
    if table_data:
        csv_output = os.path.splitext(pdf_path)[0] + "_simple_table.csv"
        with open(csv_output, 'w', newline='', encoding='utf-8') as f:
            import csv
            writer = csv.writer(f)
            writer.writerows(table_data)
        print(f"表格已保存到: {csv_output}")
        print(f"表格行数: {len(table_data)}")
    else:
        print("未找到足够的数据生成表格")
    
    return analysis_output

if __name__ == "__main__":
    pdf_file = "==3015608970000AF0000000000-251126083.pdf"
    analyze_pdf_structure(pdf_file)
