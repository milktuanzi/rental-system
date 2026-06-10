"""
维修和投诉表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError


class ChineseSelectField(SelectField):
    """将下拉框无效选项提示改为中文。"""
    def pre_validate(self, form):
        try:
            super().pre_validate(form)
        except ValidationError as exc:
            raise ValidationError('请选择有效选项') from exc


class RepairForm(FlaskForm):
    """维修申请表单"""
    title = StringField('维修标题', validators=[
        DataRequired(message='请输入维修标题'),
        Length(min=3, max=255, message='维修标题必须在3到255个字符之间')
    ])
    description = TextAreaField('维修描述', validators=[
        DataRequired(message='请输入维修描述'),
        Length(min=10, max=1000, message='维修描述必须在10到1000个字符之间')
    ])
    priority = ChineseSelectField('优先级', choices=[
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急')
    ])
    submit = SubmitField('提交维修申请')


class ComplaintForm(FlaskForm):
    """投诉表单"""
    title = StringField('投诉标题', validators=[
        DataRequired(message='请输入投诉标题'),
        Length(min=3, max=255, message='投诉标题必须在3到255个字符之间')
    ])
    content = TextAreaField('投诉内容', validators=[
        DataRequired(message='请输入投诉内容'),
        Length(min=10, max=2000, message='投诉内容必须在10到2000个字符之间')
    ])
    complaint_type = ChineseSelectField('投诉类型', choices=[
        ('property', '房源问题'),
        ('service', '服务问题'),
        ('behavior', '行为不当')
    ])
    submit = SubmitField('提交投诉')
