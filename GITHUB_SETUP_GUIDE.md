# GitHub 仓库设置指南

## 准备工作

### 1. 安装 Git
下载地址: https://git-scm.com/download/win

安装时选择默认选项即可。

### 2. 配置 Git 用户信息
打开命令提示符或 PowerShell，运行：
```bash
git config --global user.name "你的GitHub用户名"
git config --global user.email "你的GitHub邮箱"
```

## 创建 GitHub 仓库

### 步骤 1: 在 GitHub 上创建仓库
1. 访问 https://github.com
2. 登录你的账号
3. 点击右上角的 "+" → "New repository"
4. 填写仓库名称，例如: `gear-measuring-app`
5. **重要**: 不要勾选 "Initialize this repository with a README"
6. 点击 "Create repository"

### 步骤 2: 本地初始化并推送
在项目文件夹中打开命令提示符，运行以下命令：

```bash
# 进入项目目录
cd "e:\python\gear measuring software - 20251217\gear measuring software - 20251217backup"

# 初始化 Git 仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: 齿轮测量报告系统"

# 关联远程仓库（替换为你的用户名和仓库名）
git remote add origin https://github.com/你的用户名/gear-measuring-app.git

# 推送代码
git branch -M main
git push -u origin main
```

## 部署到 Streamlit Cloud

### 步骤 1: 访问 Streamlit Cloud
1. 访问 https://streamlit.io/cloud
2. 点击 "Sign in with GitHub"
3. 授权访问你的 GitHub 仓库

### 步骤 2: 部署应用
1. 点击 "New app"
2. 选择你的仓库 `gear-measuring-app`
3. 设置主文件路径: `web_app/app_professional.py`
4. 点击 "Deploy"

等待几分钟，应用就会部署完成，你会得到一个类似 `https://your-app-name.streamlit.app` 的网址。

## 项目文件结构

```
gear-measuring-app/
├── README.md              # 项目说明
├── requirements.txt       # Python依赖
├── .gitignore            # Git忽略文件
├── web_app/              # Web应用目录
│   ├── app_professional.py    # 主程序
│   └── requirements.txt       # Web应用依赖
├── gear_analysis_refactored/  # 分析模块
│   ├── models/           # 数据模型
│   ├── analysis/         # 分析算法
│   ├── reports/          # 报告生成
│   ├── utils/            # 工具函数
│   └── ui/               # UI组件
└── ripple_waviness_analyzer.py  # 波纹度分析器
```

## 注意事项

1. **大文件**: 如果 MKA 文件很大，不要上传到 GitHub
2. **敏感信息**: 确保代码中没有包含密码、API密钥等敏感信息
3. **依赖版本**: requirements.txt 中指定了最低版本，部署时会自动安装

## 更新代码

修改代码后，推送更新：

```bash
git add .
git commit -m "更新说明"
git push origin main
```

Streamlit Cloud 会自动重新部署。

## 故障排除

### 问题: 推送被拒绝
解决: 先拉取最新代码
```bash
git pull origin main
git push origin main
```

### 问题: 依赖安装失败
解决: 检查 requirements.txt 中的包名是否正确

### 问题: 应用启动失败
解决: 查看 Streamlit Cloud 的日志，检查错误信息
