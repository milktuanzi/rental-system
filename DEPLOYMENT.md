# 项目部署指南

本指南包含将智能房屋租赁系统部署到生产环境的步骤。

## 前置要求

- Python 3.8 或更高版本
- MySQL 5.7 或更高版本
- Nginx 或 Apache (用于反向代理)
- Gunicorn (用于运行Flask应用)

## 生产环境配置

### 1. 环境设置

创建 `.env` 文件在项目根目录：

```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-this
DATABASE_URL=mysql+pymysql://username:password@localhost/rental_system
```

### 2. 数据库配置

编辑 `config.py`：

```python
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
```

### 3. 创建生产数据库

```bash
# 连接到MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE rental_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'rental_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON rental_system.* TO 'rental_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
pip install gunicorn
```

### 5. 初始化数据库

```bash
python
>>> from app import app
>>> from main import db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

## 使用Gunicorn运行

### 1. 创建Gunicorn配置文件

创建 `gunicorn_config.py`：

```python
import os
from datetime import timedelta

# Gunicorn配置
workers = 4  # 工作进程数
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
timeout = 30
keepalive = 2

# 日志
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 绑定
bind = "127.0.0.1:8000"
```

### 2. 启动Gunicorn

```bash
gunicorn -c gunicorn_config.py app:app
```

## Nginx配置

### 1. 创建Nginx配置文件

编辑 `/etc/nginx/sites-available/rental_system`：

```nginx
upstream rental_app {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name your-domain.com;

    # 重定向HTTP到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL证书配置
    ssl_certificate /etc/ssl/certs/your-cert.crt;
    ssl_certificate_key /etc/ssl/private/your-key.key;

    # 安全头部
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;

    client_max_body_size 50M;

    # 代理设置
    location / {
        proxy_pass http://rental_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # 静态文件
    location /static/ {
        alias /path/to/flask-demo/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 上传文件
    location /uploads/ {
        alias /path/to/flask-demo/uploads/;
        expires 7d;
    }
}
```

### 2. 启用站点

```bash
sudo ln -s /etc/nginx/sites-available/rental_system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Systemd服务配置

### 1. 创建服务文件

创建 `/etc/systemd/system/rental_system.service`：

```ini
[Unit]
Description=Rental System Flask Application
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/flask-demo
Environment="PATH=/path/to/flask-demo/venv/bin"
Environment="FLASK_ENV=production"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/path/to/flask-demo/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. 启用服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable rental_system
sudo systemctl start rental_system
sudo systemctl status rental_system
```

## SSL证书配置 (使用Let's Encrypt)

### 1. 安装Certbot

```bash
sudo apt-get install certbot python3-certbot-nginx
```

### 2. 获取证书

```bash
sudo certbot certonly --nginx -d your-domain.com
```

### 3. 更新Nginx配置

证书路径通常为：
- `/etc/letsencrypt/live/your-domain.com/fullchain.pem`
- `/etc/letsencrypt/live/your-domain.com/privkey.pem`

### 4. 自动续期

```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## 监控和日志

### 1. 日志管理

创建日志目录：

```bash
mkdir -p /var/log/rental_system
sudo chown www-data:www-data /var/log/rental_system
```

### 2. 使用Supervisor监控（可选）

创建 `/etc/supervisor/conf.d/rental_system.conf`：

```ini
[program:rental_system]
command=/path/to/flask-demo/venv/bin/gunicorn -c gunicorn_config.py app:app
directory=/path/to/flask-demo
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/rental_system/rental_system.log
environment=PYTHONUNBUFFERED=1,FLASK_ENV=production
```

启动Supervisor：

```bash
sudo systemctl restart supervisor
```

## 性能优化

### 1. 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_property_status ON properties(status);
CREATE INDEX idx_lease_tenant ON leases(tenant_id);
CREATE INDEX idx_property_landlord ON properties(landlord_id);
```

### 2. 缓存配置

在 `config.py` 中添加Redis缓存：

```python
CACHE_TYPE = "redis"
CACHE_REDIS_URL = "redis://localhost:6379/0"
```

### 3. 数据库连接池

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}
```

## 备份和恢复

### 1. 自动数据库备份

创建 `backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/backups/mysql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/rental_system_$TIMESTAMP.sql"

mysqldump -u rental_user -p rental_system > $BACKUP_FILE
gzip $BACKUP_FILE

# 保留最近30天的备份
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

添加到crontab：

```bash
0 2 * * * /path/to/backup.sh
```

### 2. 恢复数据库

```bash
gunzip < backup_file.sql.gz | mysql -u rental_user -p rental_system
```

## 故障排查

### 常见问题

1. **连接拒绝错误**
   - 检查Gunicorn是否运行
   - 验证Nginx代理配置
   - 检查防火墙规则

2. **数据库连接失败**
   - 确认MySQL服务运行
   - 验证数据库用户和密码
   - 检查数据库权限

3. **静态文件404错误**
   - 验证Nginx静态文件路径
   - 检查文件权限
   - 清空浏览器缓存

### 查看日志

```bash
# Nginx日志
tail -f /var/log/nginx/error.log

# 应用日志
journalctl -u rental_system -f

# Gunicorn日志
tail -f /var/log/rental_system/rental_system.log
```

## 定期维护

- 每月检查SSL证书状态
- 定期备份数据库
- 监控服务器磁盘空间
- 更新系统和依赖包
- 检查应用日志中的错误

---

**最后更新**: 2024年12月

