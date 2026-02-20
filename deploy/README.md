# 齿轮波纹度分析 Web 应用

基于 Streamlit 的齿轮波纹度分析 Web 应用程序。

## 🚀 快速部署到 Streamlit Cloud

### 步骤 1: 准备文件

确保以下文件在同一目录：
- `app.py` - 主应用文件
- `requirements.txt` - Python 依赖
- `ripple_waviness_analyzer.py` - 核心算法文件

### 步骤 2: 上传到 GitHub

1. 创建新的 GitHub 仓库
2. 上传上述三个文件
3. 提交更改

### 步骤 3: 部署到 Streamlit Cloud

1. 访问 https://streamlit.io/cloud
2. 用 GitHub 账号登录
3. 点击 "New app"
4. 选择您的 GitHub 仓库
5. 主文件路径填写: `app.py`
6. 点击 "Deploy"

### 步骤 4: 访问应用

部署完成后，您将获得一个公网 URL，例如：
```
https://your-app-name.streamlit.app
```

任何人都可以通过该 URL 访问您的应用！

## 📋 文件说明

| 文件 | 说明 |
|------|------|
| `app.py` | Streamlit Web 应用主文件 |
| `requirements.txt` | Python 依赖包列表 |
| `ripple_waviness_analyzer.py` | 波纹度分析核心算法 |

## 🔧 依赖要求

```
streamlit>=1.28.0
numpy>=1.24.0
matplotlib>=3.7.0
pandas>=2.0.0
```

## 🌐 在线演示

部署后，您的应用将具有以下功能：

- 📁 上传 MKA 格式齿轮测量数据
- 📊 自动提取齿轮参数
- 🔍 左/右齿形和齿向分析
- 📈 频谱分析和可视化
- 📋 高阶波纹度评价

## 📝 使用说明

1. 打开应用 URL
2. 在左侧上传 `.mka` 文件
3. 选择要分析的类型
4. 查看分析结果

## 🔒 隐私说明

- 上传的文件仅用于分析，不会永久存储
- 分析完成后临时文件会自动删除

## 🆘 故障排除

**问题**: 部署后显示 "Module not found"
**解决**: 确保 `requirements.txt` 包含所有依赖

**问题**: 中文显示乱码
**解决**: 这是已知问题，不影响功能

**问题**: 上传大文件失败
**解决**: Streamlit Cloud 有 200MB 文件限制

## 📞 联系方式

如有问题，请通过 GitHub Issues 反馈。
