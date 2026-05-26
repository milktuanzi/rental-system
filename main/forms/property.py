"""
房源管理表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SelectField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class PropertyForm(FlaskForm):
    """房源发布/编辑表单"""
    title = StringField('房源标题', validators=[DataRequired(), Length(min=5, max=255)])
    description = TextAreaField('房源描述', validators=[Length(max=1000)])
    address = StringField('房源地址', validators=[DataRequired(), Length(max=255)])
    district = StringField('所属区域', validators=[Length(max=100)])
    area = FloatField('建筑面积(m²)', validators=[DataRequired(), NumberRange(min=1)])
    rooms = IntegerField('房间数', validators=[DataRequired(), NumberRange(min=1)])
    halls = IntegerField('厅数', validators=[DataRequired(), NumberRange(min=1)])
    bathrooms = IntegerField('卫生间数', validators=[DataRequired(), NumberRange(min=1)])
    floor = IntegerField('楼层', validators=[Optional(), NumberRange(min=1)])
    total_floors = IntegerField('总楼层', validators=[Optional(), NumberRange(min=1)])
    price = FloatField('月租金(元)', validators=[DataRequired(), NumberRange(min=0)])
    deposit = FloatField('押金(元)', validators=[DataRequired(), NumberRange(min=0)])
    decoration = SelectField('装修情况', choices=[
        ('', '请选择'),
        ('毛坯', '毛坯'),
        ('简装', '简装'),
        ('精装', '精装')
    ])
    property_type = SelectField('房源类型', choices=[
        ('', '请选择'),
        ('公寓', '公寓'),
        ('独栋', '独栋'),
        ('复式', '复式'),
        ('别墅', '别墅')
    ])
    status = SelectField('房源状态', choices=[
        ('available', '空置'),
        ('rented', '出租中'),
        ('maintenance', '维修中')
    ], validators=[DataRequired()])
    facilities = SelectMultipleField('设施设备', choices=[
        ('空调', '空调'),
        ('洗机', '洗衣机'),
        ('冰箱', '冰箱'),
        ('燃气灶', '燃气灶'),
        ('热水器', '热水器'),
        ('电视', '电视'),
        ('网络', '网络'),
        ('停车位', '停车位'),
        ('电梯', '电梯')
    ])
    submit = SubmitField('发布房源')


class SearchPropertyForm(FlaskForm):
    """房源搜索表单"""
    keyword = StringField('搜索关键词')
    district = StringField('区域')
    min_price = FloatField('最低租金')
    max_price = FloatField('最高租金')
    rooms = SelectField('户型', choices=[
        ('', '不限'),
        ('1', '1室'),
        ('2', '2室'),
        ('3', '3室'),
        ('4', '4+室')
    ], coerce=str)
    decoration = SelectField('装修', choices=[
        ('', '不限'),
        ('毛坯', '毛坯'),
        ('简装', '简装'),
        ('精装', '精装')
    ])
    sort_by = SelectField('排序', choices=[
        ('newest', '最新'),
        ('price_low', '价格低→高'),
        ('price_high', '价格高→低'),
        ('area_large', '面积大→小')
    ])
    submit = SubmitField('搜索')

