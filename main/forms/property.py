"""
房源管理表单
"""
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SelectField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


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


class ChineseSelectField(SelectField):
    """将下拉框无效选项提示改为中文。"""
    def pre_validate(self, form):
        try:
            super().pre_validate(form)
        except ValidationError as exc:
            raise ValidationError('请选择有效选项') from exc


class ChineseSelectMultipleField(SelectMultipleField):
    """将多选框无效选项提示改为中文。"""
    def pre_validate(self, form):
        try:
            super().pre_validate(form)
        except ValidationError as exc:
            raise ValidationError('请选择有效选项') from exc


class PropertyForm(FlaskForm):
    """房源发布/编辑表单"""
    title = StringField('房源标题', validators=[
        DataRequired(message='请输入房源标题'),
        Length(min=5, max=255, message='房源标题必须在5到255个字符之间')
    ])
    description = TextAreaField('房源描述', validators=[Length(max=1000, message='房源描述最多1000个字符')])
    province = StringField('省/自治区/直辖市', validators=[
        DataRequired(message='请选择省份'),
        Length(max=50, message='省份名称最多50个字符')
    ])
    city = StringField('地级市', validators=[
        DataRequired(message='请选择城市'),
        Length(max=50, message='城市名称最多50个字符')
    ])
    district = StringField('区/县/县级市', validators=[
        DataRequired(message='请选择区县'),
        Length(max=100, message='区县名称最多100个字符')
    ])
    address = StringField('详细地址', validators=[
        DataRequired(message='请输入详细地址'),
        Length(max=255, message='详细地址最多255个字符')
    ])
    area = ChineseFloatField('建筑面积(m²)', validators=[
        DataRequired(message='请输入建筑面积'),
        NumberRange(min=1, message='建筑面积必须大于0')
    ])
    rooms = ChineseIntegerField('房间数', validators=[
        DataRequired(message='请输入房间数'),
        NumberRange(min=1, message='房间数必须至少为1')
    ])
    halls = ChineseIntegerField('厅数', validators=[
        DataRequired(message='请输入厅数'),
        NumberRange(min=1, message='厅数必须至少为1')
    ])
    bathrooms = ChineseIntegerField('卫生间数', validators=[
        DataRequired(message='请输入卫生间数'),
        NumberRange(min=1, message='卫生间数必须至少为1')
    ])
    floor = ChineseIntegerField('楼层', validators=[
        Optional(),
        NumberRange(min=1, message='楼层必须至少为1')
    ])
    total_floors = ChineseIntegerField('总楼层', validators=[
        Optional(),
        NumberRange(min=1, message='总楼层必须至少为1')
    ])
    price = ChineseFloatField('月租金(元)', validators=[
        DataRequired(message='请输入月租金'),
        NumberRange(min=0, message='月租金不能小于0')
    ])
    deposit = ChineseFloatField('押金(元)', validators=[
        DataRequired(message='请输入押金'),
        NumberRange(min=0, message='押金不能小于0')
    ])
    decoration = ChineseSelectField('装修情况', choices=[
        ('', '请选择'),
        ('毛坯', '毛坯'),
        ('简装', '简装'),
        ('精装', '精装')
    ])
    property_type = ChineseSelectField('房源类型', choices=[
        ('', '请选择'),
        ('公寓', '公寓'),
        ('独栋', '独栋'),
        ('复式', '复式'),
        ('别墅', '别墅')
    ])
    status = ChineseSelectField('房源状态', choices=[
        ('available', '空置'),
        ('rented', '出租中'),
        ('maintenance', '维修中')
    ], validators=[DataRequired(message='请选择房源状态')])
    facilities = ChineseSelectMultipleField('设施设备', choices=[
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
    province = StringField('省/自治区/直辖市')
    city = StringField('地级市')
    district = StringField('区/县/县级市')
    rooms = ChineseSelectField('户型', choices=[
        ('', '不限'),
        ('1', '1室'),
        ('2', '2室'),
        ('3', '3室'),
        ('4', '4+室')
    ], coerce=str)
    decoration = ChineseSelectField('装修', choices=[
        ('', '不限'),
        ('毛坯', '毛坯'),
        ('简装', '简装'),
        ('精装', '精装')
    ])
    sort_by = ChineseSelectField('排序', choices=[
        ('newest', '最新发布'),
        ('price_low', '价格从低到高'),
        ('price_high', '价格从高到低')
    ])
    submit = SubmitField('搜索')
