import PyPDF2
import sys

# 读取PDF文件
try:
    pdf_file = open("e:\python\gear measuring software - 20251217\Wave_Produ.pdf", "rb")
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    # 获取PDF文件的页数
    num_pages = len(pdf_reader.pages)
    print(f"PDF文件页数: {num_pages}")
    
    # 读取每一页的内容
    for page_num in range(num_pages):
        print(f"\n--- 第{page_num + 1}页内容 ---")
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        print(text[:500] + "..." if len(text) > 500 else text)  # 只显示前500个字符
        
    pdf_file.close()
    
except Exception as e:
    print(f"读取PDF文件失败: {e}")
    sys.exit(1)