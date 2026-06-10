"""
新闻模型
"""
from datetime import datetime
from main import db


class News(db.Model):
    """新闻/公告模型"""
    __tablename__ = 'news'

    id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    news_type = db.Column(db.String(50), default='rental')  # 'rental', 'maintenance', 'announcement'
    cover_image = db.Column(db.String(255), nullable=True)
    content_images = db.Column(db.JSON, nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<News {self.title}>'
