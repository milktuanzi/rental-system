"""
应用工厂模式 - 初始化Flask应用和相关扩展
"""
import os
from flask import Flask, url_for
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

    @app.context_processor
    def inject_message_counts():
        """向所有模板注入全局导航和新闻栏数据。"""
        from flask_login import current_user
        from main.models.message import Message
        from main.models.news import News

        if current_user.is_authenticated:
            if current_user.is_admin():
                recent_messages = Message.query.filter(
                    (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
                ).order_by(Message.created_at.desc()).all()
            else:
                recent_messages = Message.query.filter(
                    (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
                ).order_by(Message.created_at.desc()).all()

            conversations = {}
            for message in recent_messages:
                other_user = message.sender if message.sender_id != current_user.id else message.receiver
                if current_user.is_landlord() and not (other_user.is_tenant() or other_user.is_admin()):
                    continue
                if current_user.is_tenant() and not (other_user.is_landlord() or other_user.is_admin()):
                    continue
                if current_user.is_admin() and not (other_user.is_landlord() or other_user.is_tenant()):
                    continue
                if other_user.id not in conversations:
                    if current_user.is_landlord():
                        conversation_url = url_for('landlord.conversation', user_id=other_user.id)
                    elif current_user.is_tenant():
                        conversation_url = url_for('tenant.conversation', user_id=other_user.id)
                    elif current_user.is_admin():
                        conversation_url = url_for('admin.conversation', user_id=other_user.id)
                    else:
                        conversation_url = None

                    conversations[other_user.id] = {
                        'user': other_user,
                        'last_message': message,
                        'unread_count': 0,
                        'url': conversation_url
                    }
                if message.receiver_id == current_user.id and not message.is_read:
                    conversations[other_user.id]['unread_count'] += 1

            message_conversations = list(conversations.values())
            unread_messages_count = sum(item['unread_count'] for item in message_conversations)
            if current_user.is_landlord():
                message_center_url = url_for('landlord.conversation_home')
            elif current_user.is_tenant():
                message_center_url = url_for('tenant.conversation_home')
            elif current_user.is_admin():
                message_center_url = url_for('admin.conversation_home')
            else:
                message_center_url = None
        else:
            unread_messages_count = 0
            message_conversations = []
            message_center_url = None

        latest_news = News.query.filter_by(is_published=True).order_by(
            News.created_at.desc()
        ).all()

        return {
            'unread_messages_count': unread_messages_count,
            'latest_news': latest_news,
            'message_conversations': message_conversations,
            'message_center_url': message_center_url
        }

    return app
