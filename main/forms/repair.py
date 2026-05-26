"""
维修和投诉表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class RepairForm(FlaskForm):
    """维修申请表单"""
    title = StringField('维修标题', validators=[DataRequired(), Length(min=3, max=255)])
    description = TextAreaField('维修描述', validators=[DataRequired(), Length(min=10, max=1000)])
    priority = SelectField('优先级', choices=[
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急')
    ])
    submit = SubmitField('提交维修申请')


class ComplaintForm(FlaskForm):
    """投诉表单"""
    title = StringField('投诉标题', validators=[DataRequired(), Length(min=3, max=255)])
    content = TextAreaField('投诉内容', validators=[DataRequired(), Length(min=10, max=2000)])
    complaint_type = SelectField('投诉类型', choices=[
        ('property', '房源问题'),
        ('service', '服务问题'),
        ('behavior', '行为不当')
    ])
    submit = SubmitField('提交投诉')

