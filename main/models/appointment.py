"""
预约模型
"""
from datetime import datetime
from main import db


class Appointment(db.Model):
    """预约看房模型"""
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    preferred_time = db.Column(db.DateTime, nullable=False, index=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'confirmed', 'cancelled', 'completed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系定义
    property = db.relationship('Property', backref=db.backref('appointments', lazy='dynamic'))
    tenant = db.relationship('User', foreign_keys=[tenant_id], backref=db.backref('tenant_appointments', lazy='dynamic'))
    landlord = db.relationship('User', foreign_keys=[landlord_id], backref=db.backref('landlord_appointments', lazy='dynamic'))

    def is_pending(self):
        """是否待确认"""
        return self.status == 'pending'

    def is_confirmed(self):
        """是否已确认"""
        return self.status == 'confirmed'

    def confirm(self):
        """确认预约"""
        self.status = 'confirmed'
        self.updated_at = datetime.utcnow()

    def cancel(self):
        """取消预约"""
        self.status = 'cancelled'
        self.updated_at = datetime.utcnow()

    def complete(self):
        """完成预约"""
        self.status = 'completed'
        self.updated_at = datetime.utcnow()

    def __repr__(self):
        return f'<Appointment {self.id}>'