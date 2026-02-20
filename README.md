# 齿轮波纹度分析 Web 应用

基于 Streamlit 构建的齿轮波纹度分析 Web 应用程序。

## 功能特点

- 📁 支持上传 Klingelnberg MKA 格式文件
- 📊 自动提取齿轮参数（齿数、模数、压力角等）
- 🔍 支持左/右齿形和左/右齿向分析
- 📈 频谱分析和曲线可视化
- 📋 高阶波纹度评价（W值、RMS）

## 快速开始

### 方法一：使用启动脚本（推荐）

1. 双击运行 `run.bat`
2. 等待依赖安装完成
3. 浏览器自动打开 http://localhost:8501

### 方法二：手动启动

```bash
# 进入项目目录
cd web_app

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

## 使用说明

1. **上传文件**：在左侧上传 `.mka` 格式的齿轮测量数据文件
2. **选择分析类型**：勾选需要分析的齿形/齿向方向
3. **查看结果**：
   - 齿轮参数显示
   - 高阶波纹度统计（W值、RMS）
   - 频谱分量表格
   - 合并曲线图

## 技术参数

- **预处理**：去除鼓形（二次多项式）+ 斜率（线性）
- **频谱方法**：迭代最小二乘分解
- **评价标准**：Klingelnberg P 系列标准
- **高阶定义**：阶次 ≥ 齿数 ZE

## 文件结构

```
web_app/
├── app.py              # 主应用文件
├── requirements.txt    # Python 依赖
├── run.bat            # Windows 启动脚本
└── README.md          # 说明文档
```

## 依赖要求

- Python 3.8+
- Streamlit 1.28+
- NumPy 1.24+
- Matplotlib 3.7+

## 浏览器支持

- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

## 注意事项

1. 首次启动需要安装依赖，可能需要几分钟
2. 确保 `ripple_waviness_analyzer.py` 在父目录中
3. 上传的文件大小建议不超过 10MB
