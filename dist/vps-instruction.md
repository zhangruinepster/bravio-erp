# Bravio ERP (V0.0) 生产环境 VPS 部署完整指南 (VPS Deployment Instructions)

本文档面向系统管理员与 DevOps 运维人员，详细说明如何将 **Bravio ERP V0.0** 部署至主流 Linux VPS 服务器（如 Ubuntu 22.04 / 24.04 LTS、Debian 12、Rocky Linux / AlmaLinux 等）。

---

## 1. 版本概述与交付物说明

### 1.1 系统架构与组件
- **Web & API 核心**：FastAPI (Python 3.12 异步引擎) + 响应式企业工作台 SPA
- **企业数据库**：PostgreSQL 16 (预配 WAL 级别为 replica，支持不可篡改审计)
- **缓存与 Session**：Redis 7 (会话管控、令牌黑名单与频率限制)
- **反代网关**：Nginx (HTTPS 终止、速率限制、静态分发)

### 1.2 发布包清单 (`dist/`)
- `bravio-erp-v0.0.0.tar.gz`：Linux 专用打包文件（包含后端源码、前端门户、Dockerfile、Docker Compose 与文档）
- `bravio-erp-v0.0.0.zip`：通用压缩包
- `vps-instruction.md`：本部署指导手册

### 1.3 默认预设安全凭据（首次部署后建议立即在后台或终端修改）
| 账号类型 | 默认用户名 | 默认登录密码 | 系统角色 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **超级管理员** | `admin` | `admin123` | `admin` (Superuser) | 拥有全系统配置与审计最高权限 |
| **质检操作员** | `operator` | `operator123` | `operator` | 演示车间质检与工单流转角色 |

---

## 2. VPS 服务器基础环境配置

登录您的 VPS（推荐以 root 或具有 `sudo` 权限的运维用户登录）：

```bash
# 1. 更新系统软件包索引
sudo apt-get update && sudo apt-get upgrade -y

# 2. 安装基础运维工具集
sudo apt-get install -y curl wget git unzip tar ufw rsync
```

### 2.1 安全防火墙配置 (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # 允许 SSH (如有自定义端口请修改)
sudo ufw allow 80/tcp    # 允许 HTTP (Nginx Web 网关)
sudo ufw allow 443/tcp   # 允许 HTTPS (SSL 加密)
sudo ufw enable
```
> [!IMPORTANT]
> 绝不要在公网防火墙中开放 `5432` (PostgreSQL) 或 `6379` (Redis) 端口！所有数据存储服务均运行在 Docker 内部隔离网络中。

---

## 3. 部署方案 A：Docker Compose 一键部署（首选推荐方案）

Docker 容器化部署能确保 100% 的环境一致性与隔离性，维护最省心。

### 3.1 安装 Docker Engine 与 Docker Compose 插件
如果 VPS 尚未安装 Docker，可使用官方一键脚本安装：
```bash
# 官方便捷脚本安装 Docker
curl -fsSL https://get.docker.com | sh

# 启动并设置 Docker 开机自启
sudo systemctl enable --now docker

# 验证安装
docker --version
docker compose version
```

### 3.2 解压发布包
创建应用主目录并解压：
```bash
sudo mkdir -p /opt/bravio-erp
sudo chown -R $USER:$USER /opt/bravio-erp
cd /opt/bravio-erp

# 将本地 dist/bravio-erp-v0.0.0.tar.gz 上传到服务器该目录下后执行解压：
tar -zxvf bravio-erp-v0.0.0.tar.gz
```

### 3.3 生产环境环境变量配置
复制并修改生产环境配置文件：
```bash
cp .env.example .env
nano .env
```
请务必修改以下敏感项：
```ini
# 运行环境
ENVIRONMENT=production
DEBUG=False

# 生成一个高强度 64 位以上随机秘钥 (例如使用 openssl rand -hex 32 生成)
SECRET_KEY=replace_this_with_a_super_strong_random_secret_key_in_production

# JWT 令牌过期时间 (单位: 分钟，生产环境建议 480 即 8 小时)
ACCESS_TOKEN_EXPIRE_MINUTES=480

# 生产环境容器数据库连接串 (bravio-db 与 docker-compose.yml 服务名匹配)
DATABASE_URL=postgresql+asyncpg://bravio_admin:bravio_secret_2026@bravio-db:5432/bravio_erp

# 生产环境 Redis 连接串
REDIS_URL=redis://bravio-redis:6379/0

# 开发者与生产日志
LOG_LEVEL=INFO
LOG_DIR=logs
```

### 3.4 一键构建并启动集群
```bash
# 构建镜像并在后台启动所有服务
docker compose up -d --build

# 查看运行状态
docker compose ps
```
若正常运行，您将看到 3 个容器均处于 `Up` / `healthy` 状态：
- `bravio-api` (主业务后端与静态门户，映射宿主机 8000 端口)
- `bravio-db` (PostgreSQL 16 数据库，健康检查通过)
- `bravio-redis` (Redis 7 缓存，健康检查通过)

### 3.5 验证系统健康状态
在 VPS 终端执行：
```bash
curl http://127.0.0.1:8000/api/v1/system/health
```
正常响应示例：
```json
{"status":"operational","version":"1.0.0-dev","environment":"production","database":"connected","uptime_seconds":12.5,"timestamp":"2026-10-17T12:00:00Z"}
```

---

## 4. 部署方案 B：Linux 裸机 / Systemd 服务部署（轻量级替代方案）

如果您的 VPS 内存小于 1GB 或不方便使用 Docker，可直接使用 Python 虚拟环境与 SQLite / 本地 PostgreSQL 运行。

### 4.1 安装 Python 3.12
```bash
# Ubuntu 22.04 / 24.04
sudo apt-get install -y python3 python3-pip python3-venv
```

### 4.2 初始化虚拟环境
```bash
cd /opt/bravio-erp
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4.3 配置 Systemd 守护进程
创建服务单元文件：
```bash
sudo nano /etc/systemd/system/bravio-erp.service
```
写入以下内容：
```ini
[Unit]
Description=Bravio ERP Enterprise Core Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bravio-erp
Environment="PYTHONPATH=/opt/bravio-erp/backend"
ExecStart=/opt/bravio-erp/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

激活并启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bravio-erp
sudo systemctl status bravio-erp
```

---

## 5. Nginx 反向代理网关与 SSL 证书配置

为保障企业级传输安全与外网平稳访问，必须通过 Nginx 作为反代网关并配置 HTTPS 加密。

### 5.1 安装 Nginx
```bash
sudo apt-get install -y nginx
```

### 5.2 配置 Nginx 虚拟主机站点
创建站点配置文件：
```bash
sudo nano /etc/nginx/sites-available/bravio-erp.conf
```
写入配置（将 `erp.yourdomain.com` 替换为您的实际解析域名或公网 IP）：
```nginx
server {
    listen 80;
    server_name erp.yourdomain.com;

    # 客户端请求体大小上限 (支持后续工业图纸、固件上传)
    client_max_body_size 100M;

    # 全局安全响应头
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Frame-Options SAMEORIGIN;

    # 访问与错误日志
    access_log /var/log/nginx/bravio_access.log;
    error_log /var/log/nginx/bravio_error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;

        # WebSocket 支持 (用于后续 Chatter 与实时日志流推送)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 请求上下文穿透
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
```

启用站点配置并重新加载 Nginx：
```bash
sudo ln -sf /etc/nginx/sites-available/bravio-erp.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5.3 配置 Let's Encrypt 免费自动化 SSL 证书
```bash
# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 自动签发并部署 SSL 证书 (根据提示输入邮箱并同意条款)
sudo certbot --nginx -d erp.yourdomain.com

# 验证自动续期任务
sudo certbot renew --dry-run
```

---

## 6. 日常运维、日志与安全备份指令

### 6.1 查看系统日志
- **宿主机日志文件**：
  ```bash
  tail -f /opt/bravio-erp/logs/bravio_dev_*.log
  ```
- **Docker 容器实时日志**：
  ```bash
  docker compose logs -f bravio-api
  docker compose logs -f bravio-db
  ```
- **Web 前端开发者控制台**：
  管理员登录系统首页后，在下方直接查看实时终端流并进行等级过滤与探针触发。

### 6.2 常用服务维护命令
```bash
# 停止所有服务
docker compose stop

# 重启所有服务
docker compose restart

# 平滑更新代码后重启
git pull  # 或解压新版发布包覆盖
docker compose up -d --build

# 进入后端容器 Shell 调试
docker compose exec bravio-api bash

# 进入数据库交互终端
docker compose exec bravio-db psql -U bravio_admin -d bravio_erp
```

### 6.3 数据库日常热备份指令
```bash
# 导出当前数据库全量 SQL 备份并按时间戳归档
docker compose exec -T bravio-db pg_dump -U bravio_admin bravio_erp | gzip > /opt/bravio-erp/backup_$(date +%Y%m%d_%H%M%S).sql.gz

# 恢复备份指令
# gunzip < backup_xxxx.sql.gz | docker compose exec -T bravio-db psql -U bravio_admin -d bravio_erp
```

---

至此，**Bravio ERP V0.0** 已在您的 VPS 上成功运行并对外提供高可靠服务！
如有疑问或需进一步扩展业务模块，请参考工程根目录 `docs/` 架构规范文档。
