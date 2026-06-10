"""
认证表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from main.models.user import User


class ChineseSelectField(SelectField):
    """将下拉框无效选项提示改为中文。"""
    def pre_validate(self, form):
        try:
            super().pre_validate(form)
        except ValidationError as exc:
            raise ValidationError('请选择有效选项') from exc


class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField('用户名', validators=[DataRequired(message='请输入用户名')])
    password = PasswordField('密码', validators=[DataRequired(message='请输入密码')])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegisterForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=80, message='用户名长度必须在3到80个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='请输入密码'),
        Length(min=6, message='密码长度至少为6位')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(message='请再次输入密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    phone = StringField('手机号', validators=[
        DataRequired(message='请输入手机号'),
        Length(min=11, max=11, message='手机号必须为11位')
    ])
    user_type = ChineseSelectField('用户类型', choices=[('tenant', '租客'), ('landlord', '房东')])
    submit = SubmitField('注册')

    def validate_username(self, field):
        """验证用户名是否已存在"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在')

    def validate_email(self, field):
        """验证邮箱是否已存在"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已注册')

    def validate_phone(self, field):
        """验证手机号是否已存在"""
        if User.query.filter_by(phone=field.data).first():
            raise ValidationError('手机号已注册')


class ResetPasswordForm(FlaskForm):
    """重置密码表单"""
    password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        Length(min=6, message='密码长度至少为6位')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(message='请再次输入密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('重置密码')


class ProfileForm(FlaskForm):
    """用户信息更改表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='请输入用户名'),
        Length(min=3, max=80, message='用户名长度必须在3到80个字符之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='请输入邮箱'),
        Email(message='请输入有效的邮箱地址')
    ])
    phone = StringField('手机号', validators=[Length(min=11, max=11, message='手机号必须为11位')])
    bio = StringField('个人简介')
    submit = SubmitField('确认更改')

    def __init__(self, original_username, original_email, original_phone, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        self.original_phone = original_phone

    def validate_username(self, field):
        """验证用户名是否已被其他用户使用"""
        if field.data != self.original_username and User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被使用')

    def validate_email(self, field):
        """验证邮箱是否已被其他用户使用"""
        if field.data != self.original_email and User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')

    def validate_phone(self, field):
        """验证手机号是否已被其他用户使用"""
        if field.data and field.data != self.original_phone and User.query.filter_by(phone=field.data).first():
            raise ValidationError('手机号已被使用')


class ChangePasswordForm(FlaskForm):
    """密码修改表单"""
    current_password = PasswordField('当前密码', validators=[DataRequired(message='请输入当前密码')])
    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        Length(min=8, message='密码长度至少为8位')
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请再次输入新密码'),
        EqualTo('new_password', message='两次输入的密码不一致')
    ])
    submit = SubmitField('确认修改')

    def __init__(self, user, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_current_password(self, field):
        """验证当前密码是否正确"""
        if not self.user.check_password(field.data):
            raise ValidationError('当前密码不正确')

    def validate_new_password(self, field):
        """验证新密码强度"""
        password = field.data
        
        # 检查长度
        if len(password) < 8:
            raise ValidationError('密码长度至少为8位')
        
        # 检查是否包含数字
        if not any(char.isdigit() for char in password):
            raise ValidationError('密码必须包含至少一个数字')
        
        # 检查是否包含字母
        if not any(char.isalpha() for char in password):
            raise ValidationError('密码必须包含至少一个字母')
