"""
数据模型导入管理
"""
from .user import User
from .property import Property
from .lease import Lease
from .message import Message
from .news import News
from .repair import Repair
from .complaint import Complaint
from .payment import Payment
from .appointment import Appointment

__all__ = [
    'User',
    'Property',
    'Lease',
    'Message',
    'News',
    'Repair',
    'Complaint',
    'Payment',
    'Appointment'
]

