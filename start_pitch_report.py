"""
齿轮周节详细报表 Web 应用启动脚本
"""
import subprocess
import sys
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 切换到工作目录
os.chdir(parent_dir)

# 设置环境变量跳过Streamlit的email提示
env = os.environ.copy()
env['STREAMLIT_SERVER_HEADLESS'] = 'true'

# 启动 Streamlit 应用
cmd = [
    sys.executable, "-m", "streamlit", "run",
    os.path.join(current_dir, "app_pitch_report.py"),
    "--server.port", "8510",
    "--server.address", "localhost",
    "--server.headless", "true"
]

print("正在启动齿轮周节详细报表系统...")
print(f"访问地址: http://localhost:8510")
print("-" * 50)

subprocess.run(cmd, env=env)
