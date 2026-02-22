# 齿轮测量报告 Web 应用

## 部署到 Streamlit Cloud

### 步骤 1: 创建 GitHub 仓库

1. 登录 [GitHub](https://github.com)
2. 创建新仓库，例如 `gear-measurement-app`
3. 上传以下文件：
   - `app_professional_cloud.py` (完整版应用 - **推荐**)
   - `streamlit_app.py` (简化版)
   - `ripple_waviness_analyzer.py` (分析模块)
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `packages.txt`
   - `.gitignore`

### 步骤 2: 部署到 Streamlit Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 选择仓库和分支
5. **设置主文件路径**：
   - 完整版：`app_professional_cloud.py`
   - 简化版：`streamlit_app.py`
6. 点击 "Deploy"

### 文件结构

```
gear-measuring-app/
├── app_professional_cloud.py  # 完整专业版 (推荐)
├── streamlit_app.py           # 简化版
├── ripple_waviness_analyzer.py  # 分析模块
├── requirements.txt           # Python 依赖
├── packages.txt               # 系统包 (中文字体)
├── .streamlit/
│   └── config.toml           # Streamlit 配置
├── .gitignore                # Git 忽略文件
├── Dockerfile                # Docker 部署文件
└── README.md                 # 说明文档
```

### 两个版本的区别

| 功能 | app_professional_cloud.py | streamlit_app.py |
|------|---------------------------|------------------|
| 专业报告 | ✅ 完整 Klingenberg 格式 | ✅ 简化版 |
| 周节报表 | ✅ 完整 | ✅ 简化 |
| 单齿分析 | ✅ 完整 | ✅ 简化 |
| 合并曲线 | ✅ 完整 + 前5齿放大 | ✅ 完整 |
| 频谱分析 | ✅ 完整 | ✅ 完整 |

**推荐使用 `app_professional_cloud.py`**，功能更完整。

### 注意事项

1. **中文字体**: `packages.txt` 包含 `fonts-noto-cjk` 用于显示中文
2. **文件大小限制**: Streamlit Cloud 免费版有 1GB 存储限制
3. **隐私**: 不要上传敏感的 MKA 数据文件到公开仓库

### 本地运行

完整版：
```bash
cd web_app/gear-measuring-app
pip install -r requirements.txt
streamlit run app_professional_cloud.py
```

简化版：
```bash
cd web_app/gear-measuring-app
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 其他部署选项

### Docker 部署

```bash
docker build -t gear-app .
docker run -p 8501:8501 gear-app
```

### 云服务器部署

```bash
nohup streamlit run app_professional_cloud.py --server.port 8501 --server.address 0.0.0.0 &
```
