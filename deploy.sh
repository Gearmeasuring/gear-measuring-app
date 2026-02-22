#!/bin/bash
# 部署脚本

echo "=== 部署到 GitHub ==="

cd "$(dirname "$0")"

# 添加所有更改
git add .

# 提交
git commit -m "修复语法错误：修复 set_xlabel 字符串未闭合问题"

# 推送到 GitHub
git push origin main

echo "=== 部署完成 ==="
echo "请访问 https://share.streamlit.io 查看部署状态"
