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

    # 1. 自动从本地 git 配置中解析默认 remote url
    default_url = "https://github.com/zhangruinepster/bravio-erp.git"
    try:
        config = repo.get_config()
        if (b"remote", b"origin") in config.sections():
            origin_url = config.get((b"remote", b"origin"), b"url")
            if origin_url:
                default_url = origin_url.decode("utf-8")
    except Exception:
        pass

    # 获取目标 URL
    repo_url = args.repo_url or default_url
    print("=" * 60)
    print("   Bravio ERP - 一键同步至 GitHub (支持标签与版本)")
    print("=" * 60)
    print(f"目标仓库: {repo_url}")
    print(f"目标分支: {args.branch}")

    # 获取本地标签
    tags = list(repo.refs.as_dict(b"refs/tags").keys())
    tag_names = [t.decode("utf-8") for t in tags]
    print(f"检测到本地版本标签: {tag_names or '无'}")

    # 2. 获取 Token (若为 HTTPS 且未嵌入 Token)
    token = args.token
    if not token and repo_url.startswith("https://") and "@" not in repo_url:
        print("\n提示：如果系统已通过 Git Credential Manager 授权，可直接回车跳过 Token 输入；")
        print("     或者输入您的 GitHub Personal Access Token (PAT) 进行直接推送。")
        token = input("请输入 GitHub PAT (可选，留空则尝试原生 Git 认证): ").strip()

    # 3. 如果未提供 Token，优先尝试调用系统原生 git 命令推送到远端 (自带 Credential Manager)
    if not token:
        import subprocess
        git_cmd = "git"
        # 尝试检测 Git 绝对路径
        if os.path.exists(r"C:\Program Files\Git\cmd\git.exe"):
            git_cmd = r"C:\Program Files\Git\cmd\git.exe"

        print(f"\n正在尝试使用原生 Git ({git_cmd}) 推送代码与标签...")
        try:
            push_res = subprocess.run([git_cmd, "push", "-u", "origin", args.branch], check=False)
            if push_res.returncode == 0:
                print("\n[OK] 分支推送成功，正在推送版本标签...")
                tag_res = subprocess.run([git_cmd, "push", "origin", "--tags"], check=False)
                if tag_res.returncode == 0:
                    print("=" * 60)
                    print(f"✅ 成功将分支 '{args.branch}' 及版本标签 ({', '.join(tag_names)}) 推送到 GitHub！")
                    print("=" * 60)
                    return 0
        except Exception as e:
            print(f"原生 Git 推送未完成或需要 Token: {e}")

    # 4. 如果原生 Git 未完成或提供了 Token，使用 dulwich 库直接推送
    target_url = repo_url
    if token and repo_url.startswith("https://") and "@" not in repo_url:
        clean_url = repo_url.replace("https://", "")
        target_url = f"https://{token}@{clean_url}"

    print(f"\n正在使用 Python Dulwich 引擎推送分支 '{args.branch}' 及标签至远程仓库...")

    try:
        try:
            repo.refs[f"refs/heads/{args.branch}".encode("utf-8")] = repo.head()
        except Exception:
            pass

        refspecs = [f"refs/heads/{args.branch}:refs/heads/{args.branch}".encode("utf-8")]
        for tag in tags:
            tag_name = tag.decode("utf-8")
            refspecs.append(f"refs/tags/{tag_name}:refs/tags/{tag_name}".encode("utf-8"))

        porcelain.push(repo_path, target_url, refspecs=refspecs)
        print("=" * 60)
        print(f"✅ 成功备份并推送到 GitHub 仓库: {repo_url}")
        print(f"   分支: {args.branch}")
        print(f"   版本标签: {', '.join(tag_names)}")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"[错误] 推送到 GitHub 失败: {e}")
        print("\n排查建议：")
        print("1. 远程仓库已在 GitHub 上创建；")
        print("2. 提供的 Personal Access Token 具有 'repo' (读取和写入) 权限；")
        print("3. 网络能够正常访问 github.com。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
