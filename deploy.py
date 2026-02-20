"""
自动部署脚本 - 部署到 Streamlit Cloud
"""
import os
import sys
import subprocess
import json

def check_git():
    """检查是否安装了 Git"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git 已安装: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    print("❌ 未找到 Git，请先安装: https://git-scm.com/download/win")
    return False

def check_github_cli():
    """检查是否安装了 GitHub CLI"""
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ GitHub CLI 已安装")
            return True
    except FileNotFoundError:
        pass
    print("⚠️ 未找到 GitHub CLI，将使用 git 命令")
    return False

def init_git_repo():
    """初始化 Git 仓库"""
    if os.path.exists('.git'):
        print("✅ Git 仓库已存在")
        return True
    
    result = subprocess.run(['git', 'init'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Git 仓库初始化成功")
        return True
    else:
        print(f"❌ Git 初始化失败: {result.stderr}")
        return False

def config_git_user():
    """配置 Git 用户信息"""
    # 检查是否已配置
    result = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        print(f"✅ Git 用户名: {result.stdout.strip()}")
    else:
        name = input("请输入你的 GitHub 用户名: ")
        subprocess.run(['git', 'config', 'user.name', name])
    
    result = subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        print(f"✅ Git 邮箱: {result.stdout.strip()}")
    else:
        email = input("请输入你的 GitHub 邮箱: ")
        subprocess.run(['git', 'config', 'user.email', email])

def add_and_commit():
    """添加文件并提交"""
    # 添加所有文件
    subprocess.run(['git', 'add', '.'], capture_output=True)
    
    # 检查是否有更改
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
    if not result.stdout.strip():
        print("✅ 没有需要提交的更改")
        return True
    
    # 提交
    result = subprocess.run(['git', 'commit', '-m', 'Update: 齿轮测量报告系统'], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ 提交成功")
        return True
    else:
        print(f"❌ 提交失败: {result.stderr}")
        return False

def create_github_repo(repo_name, is_private=False):
    """创建 GitHub 仓库"""
    print(f"\n🚀 正在创建 GitHub 仓库: {repo_name}")
    
    # 使用 GitHub CLI
    visibility = "--private" if is_private else "--public"
    result = subprocess.run(
        ['gh', 'repo', 'create', repo_name, visibility, '--source=.', '--push'],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print(f"✅ 仓库创建成功: https://github.com/你的用户名/{repo_name}")
        return True
    else:
        print(f"❌ 仓库创建失败: {result.stderr}")
        return False

def push_to_github(repo_url=None):
    """推送到 GitHub"""
    # 检查是否已有远程仓库
    result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
    
    if 'origin' not in result.stdout:
        if not repo_url:
            repo_url = input("请输入 GitHub 仓库地址 (如: https://github.com/用户名/仓库名.git): ")
        subprocess.run(['git', 'remote', 'add', 'origin', repo_url], capture_output=True)
    
    # 推送到 main 分支
    subprocess.run(['git', 'branch', '-M', 'main'], capture_output=True)
    result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 推送到 GitHub 成功")
        return True
    else:
        print(f"❌ 推送失败: {result.stderr}")
        return False

def deploy_to_streamlit(repo_name):
    """部署到 Streamlit Cloud"""
    print("\n" + "="*50)
    print("🚀 部署到 Streamlit Cloud")
    print("="*50)
    print("\n请按以下步骤操作:\n")
    print("1. 访问 https://streamlit.io/cloud")
    print("2. 点击 'Sign in with GitHub'")
    print("3. 授权访问你的 GitHub 仓库")
    print("4. 点击 'New app'")
    print(f"5. 选择仓库: {repo_name}")
    print("6. 设置主文件路径: web_app/app_professional.py")
    print("7. 点击 'Deploy'")
    print("\n等待几分钟，应用就会部署完成！")
    print("="*50)

def main():
    print("="*50)
    print("🚀 齿轮测量报告系统 - 自动部署脚本")
    print("="*50)
    
    # 检查 Git
    if not check_git():
        return
    
    has_gh_cli = check_github_cli()
    
    # 初始化仓库
    if not init_git_repo():
        return
    
    # 配置用户信息
    config_git_user()
    
    # 提交更改
    if not add_and_commit():
        return
    
    # 创建/推送到 GitHub
    if has_gh_cli:
        repo_name = input("\n请输入仓库名称 (如: gear-measuring-app): ")
        is_private = input("是否创建私有仓库? (y/n): ").lower() == 'y'
        if create_github_repo(repo_name, is_private):
            deploy_to_streamlit(repo_name)
    else:
        print("\n📋 手动推送到 GitHub:")
        print("1. 在 GitHub 上创建新仓库 (不要初始化 README)")
        print("2. 复制仓库地址")
        repo_url = input("3. 输入仓库地址: ")
        if push_to_github(repo_url):
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            deploy_to_streamlit(repo_name)
    
    print("\n✨ 完成！")

if __name__ == "__main__":
    main()
