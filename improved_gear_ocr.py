import fitz
import os
import cv2
import numpy as np
import pytesseract
import csv
import json
import datetime
from PIL import Image

# 设置Tesseract OCR路径
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ImprovedGearOCRAnalyzer:
    """改进的齿轮测量数据OCR分析器"""
    
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.output_dir = os.path.splitext(pdf_path)[0] + "_improved_analysis"
        os.makedirs(self.output_dir, exist_ok=True)
        self.results = {
            'metadata': {},
            'pages': [],
            'tables': {},
            'summary': {}
        }
    
    def analyze(self):
        """分析PDF文件"""
        print(f"开始改进的OCR分析: {self.pdf_path}")
        
        # 提取PDF信息
        self.extract_metadata()
        
        # 处理每一页
        doc = fitz.open(self.pdf_path)
        for page_num in range(doc.page_count):
            print(f"\n处理第{page_num + 1}页...")
            page = doc[page_num]
            page_results = self.process_page(page, page_num + 1)
            self.results['pages'].append(page_results)
        doc.close()
        
        # 生成报告
        self.generate_report()
        
        print("\n改进的分析完成!")
        return self.results
    
    def extract_metadata(self):
        """提取PDF元数据"""
        doc = fitz.open(self.pdf_path)
        metadata = doc.metadata
        self.results['metadata'] = {
            'filename': os.path.basename(self.pdf_path),
            'pages': doc.page_count,
            'size': os.path.getsize(self.pdf_path),
            'format': metadata.get('format', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', '')
        }
        doc.close()
        
    def process_page(self, page, page_num):
        """处理单个页面"""
        # 提取页面为超高分辨率图像
        zoom = 6.0  # 提高缩放比例
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        
        # 保存原始图像
        raw_image_path = os.path.join(self.output_dir, f"page_{page_num}_raw.png")
        pix.save(raw_image_path)
        
        # 预处理图像
        img = Image.open(raw_image_path)
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # 增强图像（改进版）
        enhanced_img = self.enhance_image(img_cv)
        
        # 保存增强后的图像
        enhanced_image_path = os.path.join(self.output_dir, f"page_{page_num}_enhanced.png")
        cv2.imwrite(enhanced_image_path, enhanced_img)
        
        # 使用优化的OCR识别文本
        ocr_results = self.perform_ocr(enhanced_img, page_num)
        
        # 分析识别结果
        analysis = self.analyze_ocr_results(ocr_results, page_num)
        
        return {
            'page_num': page_num,
            'raw_image': raw_image_path,
            'enhanced_image': enhanced_image_path,
            'ocr_results': ocr_results,
            'analysis': analysis
        }
    
    def enhance_image(self, img):
        """增强图像质量（改进版）"""
        # 转换为灰度
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 应用高斯模糊降噪
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 应用自适应阈值（改进参数）
        adaptive = cv2.adaptiveThreshold(
            blurred, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV,  # 使用反二值化
            21,  # 更大的块大小
            3    # 更小的常数
        )
        
        # 形态学操作 - 膨胀
        kernel = np.ones((2, 2), np.uint8)
        dilated = cv2.dilate(adaptive, kernel, iterations=1)
        
        # 形态学操作 - 腐蚀
        eroded = cv2.erode(dilated, kernel, iterations=1)
        
        # 边缘增强
        edges = cv2.Canny(eroded, 50, 150)
        edges_enhanced = cv2.addWeighted(eroded, 0.8, edges, 0.2, 0)
        
        return edges_enhanced
    
    def perform_ocr(self, img, page_num):
        """执行OCR识别（优化版）"""
        # 使用优化的OCR配置
        custom_config = r'--oem 3 --psm 6 -l eng+chi_sim'
        
        # 识别整个页面
        full_text = pytesseract.image_to_string(img, config=custom_config)
        
        # 保存OCR结果
        ocr_text_path = os.path.join(self.output_dir, f"page_{page_num}_ocr.txt")
        with open(ocr_text_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        # 识别表格数据（按区域）
        boxes = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
        
        # 尝试使用表格识别模式
        try:
            table_config = r'--oem 3 --psm 4 -l eng+chi_sim'
            table_text = pytesseract.image_to_string(img, config=table_config)
            table_text_path = os.path.join(self.output_dir, f"page_{page_num}_table_ocr.txt")
            with open(table_text_path, 'w', encoding='utf-8') as f:
                f.write(table_text)
        except Exception as e:
            table_text = ""
            table_text_path = ""
        
        return {
            'full_text': full_text,
            'table_text': table_text,
            'text_path': ocr_text_path,
            'table_text_path': table_text_path,
            'boxes': boxes
        }
    
    def analyze_ocr_results(self, ocr_results, page_num):
        """分析OCR结果"""
        # 合并两种识别结果
        text = ocr_results['full_text'] + "\n" + ocr_results['table_text']
        lines = text.split('\n')
        
        # 识别数据类型
        data_types = []
        if 'Gear Profile' in text or 'PROFILE' in text or '齿形' in text:
            data_types.append('profile')
        if 'Gear Lead' in text or 'LEAD' in text or '齿向' in text:
            data_types.append('lead')
        if 'Gear Spacing' in text or 'SPACING' in text or '周节' in text:
            data_types.append('spacing')
        if 'Tooth' in text or '齿' in text:
            data_types.append('tooth_data')
        
        # 提取齿轮参数
        gear_params = self.extract_gear_params(text)
        
        # 提取表格数据（改进版）
        tables = self.extract_tables(lines, data_types)
        
        return {
            'data_types': data_types,
            'gear_params': gear_params,
            'tables': tables
        }
    
    def extract_gear_params(self, text):
        """提取齿轮参数"""
        params = {}
        
        # 尝试识别常见参数
        patterns = {
            'module': r'module|模数|Module',
            'teeth': r'teeth|齿数|Zähnezahl',
            'helix_angle': r'helix|螺旋角|Schrägung',
            'pressure_angle': r'pressure|压力角|Druckwinkel',
            'width': r'width|齿宽|Breite'
        }
        
        for param, pattern in patterns.items():
            if pattern.lower() in text.lower():
                params[param] = 'detected'
        
        return params
    
    def extract_tables(self, lines, data_types):
        """提取表格数据（改进版）"""
        tables = {}
        
        # 过滤空行和噪音行
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if line and len(line) > 3:
                filtered_lines.append(line)
        
        # 处理齿形数据
        if 'profile' in data_types:
            tables['profile'] = self.extract_profile_data(filtered_lines)
        
        # 处理齿向数据
        if 'lead' in data_types:
            tables['lead'] = self.extract_lead_data(filtered_lines)
        
        # 处理周节数据
        if 'spacing' in data_types:
            tables['spacing'] = self.extract_spacing_data(filtered_lines)
        
        return tables
    
    def extract_profile_data(self, lines):
        """提取齿形数据"""
        profile_data = []
        
        # 寻找包含齿形数据的行
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['PROFILE', 'profile', '齿形']):
                # 收集后续的表格行
                for j in range(i + 1, min(i + 30, len(lines))):
                    data_line = lines[j]
                    if data_line and any(char.isdigit() for char in data_line):
                        profile_data.append(data_line)
        
        return profile_data
    
    def extract_lead_data(self, lines):
        """提取齿向数据"""
        lead_data = []
        
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['LEAD', 'lead', '齿向']):
                for j in range(i + 1, min(i + 30, len(lines))):
                    data_line = lines[j]
                    if data_line and any(char.isdigit() for char in data_line):
                        lead_data.append(data_line)
        
        return lead_data
    
    def extract_spacing_data(self, lines):
        """提取周节数据"""
        spacing_data = []
        
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['SPACING', 'spacing', '周节']):
                for j in range(i + 1, min(i + 30, len(lines))):
                    data_line = lines[j]
                    if data_line and any(char.isdigit() for char in data_line):
                        spacing_data.append(data_line)
        
        return spacing_data
    
    def generate_report(self):
        """生成分析报告"""
        # 保存分析结果
        analysis_path = os.path.join(self.output_dir, "analysis_results.json")
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        # 生成HTML报告
        self.generate_html_report()
        
        # 生成CSV数据文件
        self.generate_csv_reports()
        
    def generate_html_report(self):
        """生成HTML报告"""
        report_path = os.path.join(self.output_dir, "gear_analysis_report.html")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # 写入HTML头部
            f.write('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>齿轮测量数据OCR分析报告（改进版）</title>
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
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            border-bottom: 3px solid #2196F3;
            padding-bottom: 15px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
            border-left: 4px solid #2196F3;
            padding-left: 15px;
        }
        h3 {
            color: #666;
            margin-top: 20px;
        }
        .info-box {
            background-color: #e3f2fd;
            border: 1px solid #bbdefb;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }
        .data-box {
            background-color: #f3e5f5;
            border: 1px solid #e1bee7;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }
        .image-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .image-item {
            text-align: center;
        }
        .image-item img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        th {
            background-color: #2196F3;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }
        pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>齿轮测量数据OCR分析报告（改进版）</h1>
        
        <div class="info-box">
            <h2>基本信息</h2>
            <p><strong>文件名:</strong> ''' + self.results['metadata'].get('filename', '') + '''</p>
            <p><strong>页数:</strong> ''' + str(self.results['metadata'].get('pages', 0)) + '''</p>
            <p><strong>文件大小:</strong> ''' + str(self.results['metadata'].get('size', 0)) + ''' 字节</p>
            <p><strong>创建日期:</strong> ''' + self.results['metadata'].get('creation_date', '') + '''</p>
            <p><strong>分析时间:</strong> ''' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
        </div>
''')
            
            # 每页分析结果
            for i, page_result in enumerate(self.results['pages']):
                page_num = page_result['page_num']
                analysis = page_result['analysis']
                
                f.write(f'''
        <h2>第{page_num}页分析结果</h2>
        
        <h3>识别的数据类型</h3>
        <div class="info-box">
            <ul>
''')
                
                for data_type in analysis['data_types']:
                    f.write(f'                <li>{data_type}</li>\n')
                
                f.write('''
            </ul>
        </div>
        
        <h3>齿轮参数</h3>
        <div class="info-box">
''')
                
                if analysis['gear_params']:
                    for param, value in analysis['gear_params'].items():
                        f.write(f'            <p><strong>{param}:</strong> {value}</p>\n')
                else:
                    f.write('            <p>未识别到齿轮参数</p>\n')
                
                f.write('''
        </div>
        
        <h3>图像预览</h3>
        <div class="image-grid">
            <div class="image-item">
                <p>原始图像</p>
                <img src="''' + os.path.basename(page_result['raw_image']) + '''" alt="原始图像">
            </div>
            <div class="image-item">
                <p>增强图像</p>
                <img src="''' + os.path.basename(page_result['enhanced_image']) + '''" alt="增强图像">
            </div>
        </div>
''')
                
                # 表格数据
                if analysis['tables']:
                    f.write('''
        <h3>表格数据</h3>
''')
                    for table_name, table_data in analysis['tables'].items():
                        f.write(f'''
        <div class="data-box">
            <h4>{table_name} 数据</h4>
''')
                        if table_data:
                            f.write('            <pre>')
                            for line in table_data[:30]:  # 显示更多行
                                f.write(line + '\n')
                            f.write('            </pre>')
                        else:
                            f.write('            <p>未识别到表格数据</p>')
                        f.write('        </div>\n')
            
            # 写入HTML尾部
            f.write('''
        <div class="footer">
            <p>报告生成时间: ''' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
            <p>使用改进的Tesseract OCR引擎分析</p>
        </div>
    </div>
</body>
</html>
''')
        
    def generate_csv_reports(self):
        """生成CSV报告"""
        # 为每种数据类型生成CSV文件
        data_types = ['profile', 'lead', 'spacing']
        
        for data_type in data_types:
            csv_path = os.path.join(self.output_dir, f"{data_type}_data.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Page', 'Line', 'Data'])
                
                for page_result in self.results['pages']:
                    page_num = page_result['page_num']
                    analysis = page_result['analysis']
                    tables = analysis.get('tables', {})
                    
                    if data_type in tables:
                        for i, line in enumerate(tables[data_type]):
                            writer.writerow([page_num, i + 1, line])

# 主函数
def main():
    """主函数"""
    pdf_file = "==3015608970000AF0000000000-251126083.pdf"
    
    analyzer = ImprovedGearOCRAnalyzer(pdf_file)
    results = analyzer.analyze()
    
    print(f"\n改进的分析报告已生成:")
    print(f"输出目录: {analyzer.output_dir}")
    print(f"HTML报告: {os.path.join(analyzer.output_dir, 'gear_analysis_report.html')}")

if __name__ == "__main__":
    main()
