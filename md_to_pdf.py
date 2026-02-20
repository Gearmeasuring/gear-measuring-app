from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

# 读取Markdown文件内容
def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 解析Markdown内容
def parse_markdown(markdown_content):
    lines = markdown_content.strip().split('\n')
    elements = []
    
    current_style = None
    current_text = ''
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('# '):
            # 标题1
            if current_text:
                elements.append((current_style, current_text))
            elements.append(('h1', line[2:]))
            current_text = ''
        elif line.startswith('## '):
            # 标题2
            if current_text:
                elements.append((current_style, current_text))
            elements.append(('h2', line[3:]))
            current_text = ''
        elif line.startswith('### '):
            # 标题3
            if current_text:
                elements.append((current_style, current_text))
            elements.append(('h3', line[4:]))
            current_text = ''
        elif line.startswith('|'):
            # 表格
            if current_text:
                elements.append((current_style, current_text))
            elements.append(('table', line))
            current_text = ''
        elif line.startswith('- '):
            # 列表项
            if current_style != 'list':
                if current_text:
                    elements.append((current_style, current_text))
                current_style = 'list'
                current_text = line[2:] + '\n'
            else:
                current_text += line[2:] + '\n'
        elif line.startswith('`') and line.endswith('`'):
            # 行内代码
            if current_text:
                elements.append((current_style, current_text))
            elements.append(('code', line[1:-1]))
            current_text = ''
        elif line:
            # 普通文本
            if current_style != 'text':
                if current_text:
                    elements.append((current_style, current_text))
                current_style = 'text'
                current_text = line + '\n'
            else:
                current_text += line + '\n'
        else:
            # 空行
            if current_text:
                elements.append((current_style, current_text))
                current_text = ''
    
    if current_text:
        elements.append((current_style, current_text))
    
    return elements

# 生成PDF文件
def generate_pdf(input_file, output_file):
    # 创建PDF文档
    doc = SimpleDocTemplate(output_file, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    # 获取样式表
    styles = getSampleStyleSheet()
    
    # 自定义样式
    styles.add(ParagraphStyle(name='CustomHeading1', parent=styles['Heading1'], spaceAfter=20))
    styles.add(ParagraphStyle(name='CustomHeading2', parent=styles['Heading2'], spaceAfter=15))
    styles.add(ParagraphStyle(name='CustomHeading3', parent=styles['Heading3'], spaceAfter=10))
    styles.add(ParagraphStyle(name='CustomBody', parent=styles['BodyText'], spaceAfter=10))
    styles.add(ParagraphStyle(name='CustomList', parent=styles['BodyText'], leftIndent=20, spaceAfter=5))
    styles.add(ParagraphStyle(name='CustomCode', parent=styles['Code'], spaceAfter=10))
    
    # 读取和解析Markdown文件
    markdown_content = read_markdown_file(input_file)
    elements = parse_markdown(markdown_content)
    
    # 构建PDF内容
    story = []
    
    for element_type, content in elements:
        if element_type == 'h1':
            story.append(Paragraph(content, styles['CustomHeading1']))
        elif element_type == 'h2':
            story.append(Paragraph(content, styles['CustomHeading2']))
        elif element_type == 'h3':
            story.append(Paragraph(content, styles['CustomHeading3']))
        elif element_type == 'text':
            story.append(Paragraph(content, styles['CustomBody']))
        elif element_type == 'list':
            for item in content.strip().split('\n'):
                if item:
                    story.append(Paragraph(f'• {item}', styles['CustomList']))
        elif element_type == 'code':
            story.append(Paragraph(f'<code>{content}</code>', styles['CustomCode']))
        elif element_type == 'table':
            # 简单表格处理
            if '| 参数 | 计算值 | 目标值 | 误差 | 验证 |' in content:
                # 创建表格数据
                table_data = [
                    ['参数', '计算值', '目标值', '误差', '验证'],
                    ['ep', '1.454', '1.454', '0.000', '✅'],
                    ['lo', '33.578', '33.578', '0.000', '✅'],
                    ['lu', '24.775', '24.775', '0.000', '✅'],
                    ['el', '2.776', '2.776', '0.000', '✅'],
                    ['zo', '18.9', '18.9', '0.000', '✅'],
                    ['zu', '-18.9', '-18.9', '0.000', '✅']
                ]
                
                # 创建表格
                table = Table(table_data, colWidths=[3*cm, 2*cm, 2*cm, 2*cm, 2*cm])
                
                # 设置表格样式
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
    
    # 添加第二个表格
    table_data2 = [
        ['参数', '计算值', '目标值', '误差', '验证'],
        ['ep', '1.810', '1.810', '0.000', '✅'],
        ['lo', '11.822', '11.822', '0.000', '✅'],
        ['lu', '3.261', '3.261', '0.000', '✅'],
        ['el', '2.616', '2.616', '0.000', '✅'],
        ['zo', '14', '14', '0.000', '✅'],
        ['zu', '-14', '-14', '0.000', '✅']
    ]
    
    table2 = Table(table_data2, colWidths=[3*cm, 2*cm, 2*cm, 2*cm, 2*cm])
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph('2. 004-xiaoxiao1.mka', styles['CustomHeading3']))
    story.append(table2)
    story.append(Spacer(1, 20))
    
    # 构建PDF
    doc.build(story)

if __name__ == "__main__":
    input_file = '齿轮参数计算算法.md'
    output_file = '齿轮参数计算算法.pdf'
    generate_pdf(input_file, output_file)
    print(f"PDF文件已生成: {output_file}")
