"""
租赁管理表单
"""
from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateField, DateTimeField, FloatField, IntegerField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class ChineseDateField(DateField):
    """将日期格式错误提示改为中文。"""
    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist)
            try:
                self.data = datetime.strptime(date_str, self.format).date()
            except ValueError as exc:
                self.data = None
                raise ValueError('请输入有效的日期，格式为YYYY-MM-DD') from exc


class ChineseDateTimeField(DateTimeField):
    """将日期时间格式错误提示改为中文。"""
    def process_formdata(self, valuelist):
        if valuelist:
            datetime_str = ' '.join(valuelist)
            try:
                self.data = datetime.strptime(datetime_str, self.format)
            except ValueError as exc:
                self.data = None
                raise ValueError('请输入有效的日期时间') from exc


class ChineseFloatField(FloatField):
    """将小数格式错误提示改为中文。"""
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = float(valuelist[0])
            except ValueError as exc:
                self.data = None
                raise ValueError('请输入有效的数字') from exc


class ChineseIntegerField(IntegerField):
    """将整数格式错误提示改为中文。"""
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = int(valuelist[0])
            except ValueError as exc:
                self.data = None
                raise ValueError('请输入有效的整数') from exc


class AppointmentForm(FlaskForm):
    """预约看房表单"""
    preferred_time = ChineseDateTimeField('预约时间', validators=[DataRequired(message='请选择预约时间')], format='%Y-%m-%d %H:%M:%S')
    message = TextAreaField('留言', validators=[Length(max=500, message='留言最多500个字符')])
    submit = SubmitField('预约看房')


class LeaseForm(FlaskForm):
    """租赁合同表单"""
    contract_content = TextAreaField('合同内容', validators=[
        DataRequired(message='请输入合同内容'),
        Length(min=20, message='合同内容至少20个字符')
    ])
    monthly_rent = ChineseFloatField('月租金', validators=[
        DataRequired(message='请输入月租金'),
        NumberRange(min=0, message='月租金不能小于0')
    ])
    deposit_amount = ChineseFloatField('押金金额', validators=[
        DataRequired(message='请输入押金金额'),
        NumberRange(min=0, message='押金金额不能小于0')
    ])
    start_date = ChineseDateField('租赁开始日期', validators=[DataRequired(message='请选择租赁开始日期')], format='%Y-%m-%d')
    lease_duration = ChineseIntegerField('租赁期限(月)', validators=[
        DataRequired(message='请输入租赁期限'),
        NumberRange(min=1, max=120, message='租赁期限必须在1到120个月之间')
    ])
    submit = SubmitField('生成合同')


class PaymentForm(FlaskForm):
    """房东发起账单表单"""
    amount = ChineseFloatField('账单金额', validators=[
        DataRequired(message='请输入账单金额'),
        NumberRange(min=0.01, message='账单金额必须大于0')
    ])
    payment_period = StringField('账单周期', validators=[
        DataRequired(message='请输入账单周期'),
        Length(max=20, message='账单周期最多20个字符')
    ])
    due_date = ChineseDateField('支付截止日期', validators=[DataRequired(message='请选择支付截止日期')], format='%Y-%m-%d')
    remark = TextAreaField('账单说明', validators=[Length(max=500, message='账单说明最多500个字符')])
    landlord_qr_code = FileField('收款码图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], '仅支持图片文件')
    ])
    submit = SubmitField('发起账单')


class PaymentSubmitForm(FlaskForm):
    """租客支付账单表单"""
    payment_method = StringField('支付方式', validators=[Length(max=50, message='支付方式最多50个字符')])
    transaction_id = StringField('交易单号', validators=[Length(max=255, message='交易单号最多255个字符')])
    tenant_payment_proof = FileField('支付凭证图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], '仅支持图片文件')
    ])
    submit = SubmitField('提交支付')
