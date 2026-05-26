"""
用户模型
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from main import db, login_manager


class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    user_type = db.Column(db.String(20), nullable=False, default='tenant')  # 'landlord', 'tenant', 'admin'
    avatar = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    properties = db.relationship('Property', backref='landlord', lazy='dynamic', foreign_keys='Property.landlord_id')
    leases_as_tenant = db.relationship('Lease', backref='tenant', lazy='dynamic', foreign_keys='Lease.tenant_id')
    messages_sent = db.relationship('Message', backref='sender', lazy='dynamic', foreign_keys='Message.sender_id')
    messages_received = db.relationship('Message', backref='receiver', lazy='dynamic', foreign_keys='Message.receiver_id')
    news = db.relationship('News', backref='author', lazy='dynamic')
    repairs = db.relationship('Repair', backref='tenant_obj', lazy='dynamic')
    complaints = db.relationship('Complaint', backref='complainer', lazy='dynamic', foreign_keys='Complaint.user_id')

    def set_password(self, password):
        """设置密码（加密）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def is_landlord(self):
        """是否为房东"""
        return self.user_type == 'landlord'

    def is_tenant(self):
        """是否为租客"""
        return self.user_type == 'tenant'

    def is_admin(self):
        """是否为管理员"""
        return self.user_type == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """用户加载器"""
    return User.query.get(int(user_id))

