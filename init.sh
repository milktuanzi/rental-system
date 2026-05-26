#!/bin/bash

# 智能房屋租赁系统 - 快速启动脚本

set -e

echo "================================"
echo "智能房屋租赁系统 - 初始化脚本"
echo "================================"
echo ""

# 检查Python版本
echo "✓ 检查Python版本..."
python3 --version

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "✓ 创建虚拟环境..."
    python3 -m venv venv
else
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "✓ 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "✓ 升级pip..."
pip install --upgrade pip -q

# 安装依赖
echo "✓ 安装依赖包..."
pip install -r requirements.txt -q

# 初始化数据库
echo "✓ 初始化数据库..."
python3 << END
from app import app
from main import db

with app.app_context():
    db.create_all()
    print("  ✓ 数据库表创建成功")
END

echo ""
echo "================================"
echo "初始化完成！"
echo "================================"
echo ""
echo "现在可以运行应用：python app.py"
echo ""
echo "应用将在 http://localhost:5000 运行"
echo ""
echo "提示："
echo "  - 访问首页: http://localhost:5000"
echo "  - 登录/注册: http://localhost:5000/auth/login"
echo "  - 搜索房源: http://localhost:5000/search"
echo ""

