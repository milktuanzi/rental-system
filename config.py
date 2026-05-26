import os
from datetime import timedelta

# 应用配置
class Config:
    """基础配置"""
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_ENV = 'development'

    # SQLAlchemy配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Session配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # 上传文件配置
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'properties')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB最大文件大小
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_IMAGE_COUNT = 3
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    # 使用 SQLite 避免 MySQL 数据库不存在的问题
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'rental_system.db')
    
    # 禁用缓存以确保开发期间修改能立即生效
    SEND_FILE_MAX_AGE_DEFAULT = 0  # 静态文件不缓存
    TEMPLATES_AUTO_RELOAD = True  # 模板自动重载


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

