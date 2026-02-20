"""
启动完整报表版 Streamlit Web 应用
"""
import subprocess
import sys
import os

# 设置环境变量跳过 Streamlit 的邮件收集
os.environ['STREAMLIT_TELEMETRY_OPT_OUT'] = 'true'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 添加父目录到路径
sys.path.insert(0, parent_dir)

# 启动 streamlit
cmd = [
    sys.executable, "-m", "streamlit", "run", 
    os.path.join(current_dir, "app_report.py"),
    "--server.port=8504",
    "--server.address=localhost",
    "--browser.gatherUsageStats=false"
]

print("="*60)
print("齿轮测量报告系统 - 完整报表版")
print("="*60)
print(f"请在浏览器中访问: http://localhost:8504")
print("="*60)

subprocess.run(cmd)
