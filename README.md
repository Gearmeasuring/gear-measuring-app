# 齿轮测量报告系统

基于 Python + Streamlit 的齿轮测量数据分析和报告生成系统。

## 功能特点

- 📄 **专业报告**: 生成 PDF 报告（包含齿形/齿向/周节分析）
- 📊 **周节详细报表**: 周节偏差 fp/Fp/Fr 分析和详细数据表
- 📈 **单齿分析**: 单个齿的齿形/齿向偏差曲线
- 📉 **合并曲线**: 0-360°合并曲线和高阶重构
- 📊 **频谱分析**: 各阶次振幅和相位分析

## 技术栈

- Python 3.11+
- Streamlit
- NumPy
- Matplotlib
- SciPy

## 安装

```bash
# 克隆仓库
git clone https://github.com/你的用户名/gear-measuring-app.git
cd gear-measuring-app

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 运行

```bash
# 运行 Web 应用
streamlit run web_app/app_professional.py
```

## 部署到 Streamlit Cloud

1. Fork 本仓库到你的 GitHub 账号
2. 访问 [streamlit.io/cloud](https://streamlit.io/cloud)
3. 用 GitHub 账号登录
4. 点击 "New app"
5. 选择你的仓库，设置主文件路径为 `web_app/app_professional.py`
6. 点击 "Deploy"

## 使用说明

1. 上传 MKA 格式的齿轮测量数据文件
2. 选择需要的功能页面
3. 查看分析结果或下载 PDF 报告

## 许可证

MIT License
