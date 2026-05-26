"""
维修申请模型
"""
from datetime import datetime
from main import db


class Repair(db.Model):
    """维修申请模型"""
    __tablename__ = 'repairs'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'in_progress', 'completed', 'rejected'
    landlord_reply = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def is_pending(self):
        """是否待处理"""
        return self.status == 'pending'

    def is_completed(self):
        """是否已完成"""
        return self.status == 'completed'

    def __repr__(self):
        return f'<Repair {self.id}>'

