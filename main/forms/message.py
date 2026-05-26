"""
消息和新闻表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length


class MessageForm(FlaskForm):
    """留言表单"""
    content = TextAreaField('留言内容', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('发送')


class NewsForm(FlaskForm):
    """新闻发布表单"""
    title = StringField('新闻标题', validators=[DataRequired(), Length(min=5, max=255)])
    content = TextAreaField('新闻内容', validators=[DataRequired(), Length(min=20, max=5000)])
    news_type = SelectField('新闻类型', choices=[
        ('rental', '租赁相关'),
        ('maintenance', '维修相关'),
        ('announcement', '公告')
    ])
    submit = SubmitField('发布')

