"""
表单导入管理
"""
from .auth import LoginForm, RegisterForm, ResetPasswordForm
from .property import PropertyForm, SearchPropertyForm
from .lease import LeaseForm, AppointmentForm
from .message import MessageForm, NewsForm
from .repair import RepairForm, ComplaintForm

__all__ = [
    'LoginForm',
    'RegisterForm',
    'ResetPasswordForm',
    'PropertyForm',
    'SearchPropertyForm',
    'LeaseForm',
    'AppointmentForm',
    'MessageForm',
    'NewsForm',
    'RepairForm',
    'ComplaintForm'
]

