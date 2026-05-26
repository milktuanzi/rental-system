"""
消息/留言模型
"""
from datetime import datetime
from main import db


class Message(db.Model):
    """消息/留言模型"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='message')  # 'message', 'inquiry'
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def mark_as_read(self):
        """标记为已读"""
        self.is_read = True

    def __repr__(self):
        return f'<Message {self.id}>'

