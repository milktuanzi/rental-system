"""
应用工厂模式 - 初始化Flask应用和相关扩展
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name='development'):
    """
    应用工厂函数
    Args:
        config_name: 配置环境名称 (development, testing, production)
    """
    # 获取项目根目录（main包的父目录）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static')
    )

    # 加载配置
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'

    # 应用上下文中创建表
    with app.app_context():
        # 导入所有模型（确保 db.create_all() 知道要创建哪些表）
        from main.models import User, Property, Lease, Message, News, Repair, Complaint, Payment, Appointment
        db.create_all()

    # 注册蓝图
    from main.views.auth import auth_bp
    from main.views.common import common_bp
    from main.views.landlord import landlord_bp
    from main.views.tenant import tenant_bp
    from main.views.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(common_bp)
    app.register_blueprint(landlord_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(admin_bp)

    # 注册错误处理器
    from main.errors import register_error_handlers
    register_error_handlers(app)

    return app

