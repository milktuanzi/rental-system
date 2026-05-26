"""
租赁模型
"""
from datetime import datetime
from main import db


class Lease(db.Model):
    """租赁合同模型"""
    __tablename__ = 'leases'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    start_date = db.Column(db.DateTime, nullable=False, index=True)
    end_date = db.Column(db.DateTime, nullable=False)
    contract_content = db.Column(db.Text, nullable=True)
    monthly_rent = db.Column(db.Float, nullable=False)
    deposit_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'active', 'completed', 'terminated'
    is_signed = db.Column(db.Boolean, default=False)
    sign_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    payments = db.relationship('Payment', backref='lease', lazy='dynamic', cascade='all, delete-orphan')

    def is_active(self):
        """租赁是否有效"""
        return self.status == 'active'

    def is_pending(self):
        """租赁是否待签署"""
        return self.status == 'pending'

    def __repr__(self):
        return f'<Lease {self.id}>'

