"""
投诉模型
"""
from datetime import datetime
from main import db


class Complaint(db.Model):
    """投诉模型"""
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    target_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 被投诉人ID
    property_id = db.Column(db.Integer, nullable=True, index=True)  # 关联房源ID
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    complaint_type = db.Column(db.String(50))  # 'property', 'service', 'behavior'
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'under_review', 'resolved', 'rejected'
    admin_reply = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def is_resolved(self):
        """是否已解决"""
        return self.status == 'resolved'

    def __repr__(self):
        return f'<Complaint {self.id}>'

