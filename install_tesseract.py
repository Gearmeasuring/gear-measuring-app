import os
import requests
import zipfile
import subprocess
import ctypes
import sys

def is_admin():
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def download_file(url, filename):
    """下载文件"""
    print(f"开始下载: {url}")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0
    
    with open(filename, 'wb') as f:
        for data in response.iter_content(chunk_size=8192):
            size = f.write(data)
            downloaded_size += size
            if total_size > 0:
                progress = (downloaded_size / total_size) * 100
                print(f"下载进度: {progress:.1f}%", end='\r')
    
    print(f"\n下载完成: {filename}")
    return filename

def install_tesseract():
    """安装Tesseract OCR"""
    print("开始安装Tesseract OCR引擎...")
    
    # 检查是否以管理员权限运行
    if not is_admin():
        print("错误: 需要以管理员权限运行此脚本")
        print("请右键点击脚本并选择'以管理员身份运行'")
        return False
    
    # Tesseract OCR下载链接（最新版本）
    # 注意：这里使用的是UB Mannheim的预编译版本
    tesseract_url = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.3.3.20231005/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
    installer_path = "tesseract-installer.exe"
    
    try:
        # 下载安装程序
        download_file(tesseract_url, installer_path)
        
        # 运行安装程序
        print("正在运行Tesseract OCR安装程序...")
        print("请按照安装向导的提示完成安装")
        print("注意：请确保选择'Add to PATH'选项")
        
        # 运行安装程序
        subprocess.run([installer_path], check=True)
        
        # 验证安装
        print("验证Tesseract OCR安装...")
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Tesseract OCR安装成功!")
            print(f"版本信息: {result.stdout}")
            
            # 检查中文语言包
            check_language_pack()
            
            return True
        else:
            print("Tesseract OCR安装失败")
            print(f"错误信息: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"安装过程中出现错误: {e}")
        return False
    finally:
        # 清理安装程序
        if os.path.exists(installer_path):
            os.remove(installer_path)
            print(f"已删除安装程序: {installer_path}")

def check_language_pack():
    """检查并安装中文语言包"""
    print("\n检查中文语言包...")
    
    # 检查Tesseract数据目录
    try:
        # 获取Tesseract数据目录
        result = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True)
        if result.returncode == 0:
            print("已安装的语言包:")
            print(result.stdout)
            
            # 检查是否有中文语言包
            if 'chi_sim' in result.stdout or 'chi_tra' in result.stdout:
                print("中文语言包已安装")
            else:
                print("中文语言包未安装，建议下载安装")
                print("请从以下链接下载中文语言包:")
                print("https://github.com/tesseract-ocr/tessdata/blob/main/chi_sim.traineddata")
                print("https://github.com/tesseract-ocr/tessdata/blob/main/chi_tra.traineddata")
                print("并将文件复制到Tesseract的数据目录中")
        else:
            print("无法列出语言包")
    except Exception as e:
        print(f"检查语言包时出错: {e}")

def main():
    """主函数"""
    print("Tesseract OCR安装向导")
    print("=" * 50)
    print("此脚本将帮助您安装Tesseract OCR引擎")
    print("Tesseract OCR是一个开源的光学字符识别引擎")
    print("用于从图像中提取文本，支持多种语言")
    print("=" * 50)
    
    # 检查是否已经安装
    try:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Tesseract OCR已经安装!")
            print(f"版本: {result.stdout}")
            check_language_pack()
            return
    except:
        pass
    
    # 开始安装
    print("\n开始安装Tesseract OCR...")
    success = install_tesseract()
    
    if success:
        print("\n安装完成！")
        print("现在您可以使用OCR功能从PDF中提取表格数据了")
        print("请重新运行 ocr_pdf_data.py 脚本")
    else:
        print("\n安装失败，请手动安装Tesseract OCR")
        print("下载地址: https://github.com/UB-Mannheim/tesseract/releases")

if __name__ == "__main__":
    main()
