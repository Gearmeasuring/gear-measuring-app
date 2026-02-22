# 齿轮测量报告 Web 应用

## 部署到 Streamlit Cloud

### 步骤 1: 创建 GitHub 仓库

1. 登录 [GitHub](https://github.com)
2. 创建新仓库，例如 `gear-measurement-app`
3. 上传以下文件：
   - `streamlit_app.py` (主应用)
   - `app_professional.py` (完整版应用)
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `packages.txt`
   - `ripple_waviness_analyzer.py` (在上级目录)

### 步骤 2: 部署到 Streamlit Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 选择仓库和分支
5. 设置主文件路径为 `streamlit_app.py`
6. 点击 "Deploy"

### 文件结构

```
gear-measuring-app/
├── streamlit_app.py          # Streamlit Cloud 入口文件
├── app_professional.py        # 完整版应用
├── requirements.txt           # Python 依赖
├── packages.txt               # 系统包 (中文字体)
├── .streamlit/
│   └── config.toml           # Streamlit 配置
├── .gitignore                # Git 忽略文件
└── README.md                 # 说明文档
```

### 注意事项

1. **中文字体**: `packages.txt` 包含 `fonts-noto-cjk` 用于显示中文
2. **文件大小限制**: Streamlit Cloud 免费版有 1GB 存储限制
3. **隐私**: 不要上传敏感的 MKA 数据文件

### 本地运行

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
nohup streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
```
