"""
消息和新闻表单
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import MultipleFileField, StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError


class ChineseSelectField(SelectField):
    """将下拉框无效选项提示改为中文。"""
    def pre_validate(self, form):
        try:
            super().pre_validate(form)
        except ValidationError as exc:
            raise ValidationError('请选择有效选项') from exc


class MessageForm(FlaskForm):
    """留言表单"""
    content = TextAreaField('留言内容', validators=[
        DataRequired(message='请输入消息内容'),
        Length(min=1, max=1000, message='消息内容必须在1到1000个字符之间')
    ])
    submit = SubmitField('发送')


class NewsForm(FlaskForm):
    """新闻发布表单"""
    title = StringField('新闻标题', validators=[
        DataRequired(message='请输入新闻标题'),
        Length(min=5, max=255, message='新闻标题必须在5到255个字符之间')
    ])
    content = TextAreaField('新闻内容', validators=[
        DataRequired(message='请输入新闻内容'),
        Length(min=20, max=5000, message='新闻内容必须在20到5000个字符之间')
    ])
    news_type = ChineseSelectField('新闻类型', choices=[
        ('rental', '租赁相关'),
        ('maintenance', '维修相关'),
        ('announcement', '公告')
    ])
    cover_image = FileField('封面图', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], '仅支持图片文件')
    ])
    content_images = MultipleFileField('内容图')
    submit = SubmitField('发布')
