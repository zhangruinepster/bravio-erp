"""
Bravio ERP - Git Backup & GitHub Push Tool
用于在无外部命令行 git 依赖的情况下，使用内置 dulwich 将本地代码库推送到远程 GitHub 仓库。

使用方法:
  python git_push.py --repo-url https://github.com/<your-username>/bravio-erp.git --token <your-github-token>
或者：
  python git_push.py
  (交互式输入远程仓库 URL 与 Token/密码)
"""

import os
import sys
import argparse
from dulwich import porcelain
from dulwich.repo import Repo

def main():
    parser = argparse.ArgumentParser(description="Backup Bravio ERP to GitHub")
    parser.add_argument("--repo-url", help="GitHub repository URL (e.g., https://github.com/username/bravio-erp.git)")
    parser.add_argument("--token", help="GitHub Personal Access Token (PAT)")
    parser.add_argument("--branch", default="main", help="Target branch name (default: main)")
    args = parser.parse_args()

    repo_path = os.path.abspath(os.path.dirname(__file__))
    repo = Repo(repo_path)

    # 1. 获取目标 URL
    repo_url = args.repo_url
    if not repo_url:
        print("=" * 60)
        print("   Bravio ERP - 一键备份同步至 GitHub")
        print("=" * 60)
        repo_url = input("请输入您的 GitHub 仓库 URL (例如 https://github.com/your-name/bravio-erp.git): ").strip()
        if not repo_url:
            print("[错误] 未提供仓库地址，退出。")
            return 1

    # 2. 获取 Token (若为 HTTPS 且未嵌入 Token)
    token = args.token
    if not token and repo_url.startswith("https://") and "@" not in repo_url:
        token = input("请输入 GitHub Personal Access Token (PAT, 密码方式已弃用): ").strip()

    target_url = repo_url
    if token and repo_url.startswith("https://") and "@" not in repo_url:
        # 将 Token 嵌入 HTTPS 认证 URL
        clean_url = repo_url.replace("https://", "")
        target_url = f"https://{token}@{clean_url}"

    print(f"正在准备推送分支 '{args.branch}' 至远程仓库...")

    try:
        # 设置默认分支引用
        try:
            repo.refs[f"refs/heads/{args.branch}".encode("utf-8")] = repo.head()
        except Exception:
            pass

        refspec = f"refs/heads/{args.branch}:refs/heads/{args.branch}".encode("utf-8")
        porcelain.push(repo_path, target_url, refspecs=[refspec])
        print("=" * 60)
        print(f"✅ 成功备份并推送到 GitHub 仓库: {repo_url} (分支: {args.branch})")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"[错误] 推送到 GitHub 失败: {e}")
        print("\n提示：请确认：")
        print("1. 远程仓库已在 GitHub 上创建；")
        print("2. 提供的 Personal Access Token 具有 'repo' (读取和写入) 权限；")
        print("3. 网络能够正常访问 github.com。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
