"""
支付/账单模型
"""
from datetime import datetime
from main import db


class Payment(db.Model):
    """租金支付模型"""
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    payment_period = db.Column(db.String(20), nullable=True)  # 例如: '2024-01', '2024-02'
    status = db.Column(db.String(20), default='pending', index=True)  # 'pending', 'completed', 'overdue'
    payment_method = db.Column(db.String(50), nullable=True)  # 'online', 'transfer', 'cash'
    transaction_id = db.Column(db.String(255), unique=True, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True, index=True)
    payment_date = db.Column(db.DateTime, nullable=True)
    remark = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_paid(self):
        """是否已支付"""
        return self.status == 'completed'

    def is_overdue(self):
        """是否逾期"""
        if self.status == 'pending' and self.due_date:
            return datetime.utcnow() > self.due_date
        return False

    def __repr__(self):
        return f'<Payment {self.id}>'

