"""
房源模型
"""
from datetime import datetime
from main import db


class Property(db.Model):
    """房源模型"""
    __tablename__ = 'properties'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=False, index=True)
    district = db.Column(db.String(100), nullable=True, index=True)
    area = db.Column(db.Float, nullable=False)  # 面积（平方米）
    rooms = db.Column(db.Integer, nullable=False)  # 房间数
    halls = db.Column(db.Integer, nullable=False, default=1)  # 厅数
    bathrooms = db.Column(db.Integer, nullable=False, default=1)  # 卫生间数
    floor = db.Column(db.Integer, nullable=True)  # 楼层
    total_floors = db.Column(db.Integer, nullable=True)  # 总楼层
    price = db.Column(db.Float, nullable=False, index=True)  # 月租金
    deposit = db.Column(db.Float, nullable=False)  # 押金
    decoration = db.Column(db.String(50), nullable=True)  # 装修情况: '毛坯', '简装', '精装'
    property_type = db.Column(db.String(50), nullable=True)  # 房源类型: '公寓', '独栋', '复式'等
    status = db.Column(db.String(20), default='available', index=True)  # 状态: 'available', 'rented', 'maintenance'
    landlord_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    images = db.Column(db.JSON, nullable=True)  # 房源图片URL列表
    videos = db.Column(db.JSON, nullable=True)  # 房源视频URL列表
    facilities = db.Column(db.JSON, nullable=True)  # 设施设备: ['空调', '洗机', '冰箱']等
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    leases = db.relationship('Lease', backref='property', lazy='dynamic', cascade='all, delete-orphan')
    repairs = db.relationship('Repair', backref='property', lazy='dynamic', cascade='all, delete-orphan')

    def get_room_format(self):
        """获取户型格式字符串"""
        return f'{self.rooms}室{self.halls}厅{self.bathrooms}卫'

    def is_available(self):
        """是否可租"""
        return self.status == 'available'

    def __repr__(self):
        return f'<Property {self.title}>'

