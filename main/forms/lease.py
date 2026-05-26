"""
租赁管理表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Length


class AppointmentForm(FlaskForm):
    """预约看房表单"""
    preferred_time = DateTimeField('预约时间', validators=[DataRequired()], format='%Y-%m-%d %H:%M:%S')
    message = TextAreaField('留言', validators=[Length(max=500)])
    submit = SubmitField('预约看房')


class LeaseForm(FlaskForm):
    """租赁合同表单"""
    contract_content = TextAreaField('合同内容', validators=[DataRequired(), Length(min=20)])
    monthly_rent = StringField('月租金', validators=[DataRequired()])
    deposit_amount = StringField('押金金额', validators=[DataRequired()])
    lease_duration = StringField('租赁期限(月)', validators=[DataRequired()])
    submit = SubmitField('生成合同')

