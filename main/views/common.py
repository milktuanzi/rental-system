"""
通用视图 - 首页、房源搜索、房源详情
"""
from flask import Blueprint, render_template, request, jsonify
from main import db
from main.models.property import Property
from main.models.user import User
from main.forms.property import SearchPropertyForm

common_bp = Blueprint('common', __name__)


@common_bp.route('/')
def index():
    """首页"""
    # 获取最新房源
    page = request.args.get('page', 1, type=int)
    properties = Property.query.filter_by(status='available').order_by(
        Property.created_at.desc()
    ).paginate(page=page, per_page=12)

    # 热门区域统计
    popular_districts = db.session.query(
        Property.district,
        db.func.count(Property.id).label('count')
    ).filter_by(status='available').group_by(Property.district).limit(8).all()

    return render_template('index.html', properties=properties, popular_districts=popular_districts)


@common_bp.route('/search')
def search():
    """房源搜索"""
    form = SearchPropertyForm()
    query = Property.query.filter_by(status='available')

    # 关键词搜索
    keyword = request.args.get('keyword', '')
    if keyword:
        query = query.filter(
            db.or_(
                Property.title.ilike(f'%{keyword}%'),
                Property.address.ilike(f'%{keyword}%')
            )
        )

    # 区域搜索
    district = request.args.get('district', '')
    if district:
        query = query.filter_by(district=district)

    # 价格范围
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price:
        query = query.filter(Property.price >= min_price)
    if max_price:
        query = query.filter(Property.price <= max_price)

    # 户型筛选
    rooms = request.args.get('rooms', '')
    if rooms:
        if rooms == '4':
            query = query.filter(Property.rooms >= 4)
        else:
            query = query.filter(Property.rooms == int(rooms))

    # 装修筛选
    decoration = request.args.get('decoration', '')
    if decoration:
        query = query.filter_by(decoration=decoration)

    # 排序
    sort_by = request.args.get('sort_by', 'newest')
    if sort_by == 'price_low':
        query = query.order_by(Property.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Property.price.desc())
    elif sort_by == 'area_large':
        query = query.order_by(Property.area.desc())
    else:
        query = query.order_by(Property.created_at.desc())

    page = request.args.get('page', 1, type=int)
    properties = query.paginate(page=page, per_page=12)

    return render_template('search.html', properties=properties, form=form)


@common_bp.route('/property/<int:property_id>')
def property_detail(property_id):
    """房源详情页面"""
    property_obj = Property.query.get_or_404(property_id)
    landlord = User.query.get(property_obj.landlord_id)

    # 获取同区域的其他房源
    related_properties = Property.query.filter(
        Property.id != property_id,
        Property.district == property_obj.district,
        Property.status == 'available'
    ).limit(4).all()

    return render_template(
        'property_detail.html',
        property=property_obj,
        landlord=landlord,
        related_properties=related_properties
    )


@common_bp.route('/api/districts')
def get_districts():
    """获取所有热门区域 API"""
    districts = db.session.query(Property.district).filter(
        Property.district.isnot(None),
        Property.status == 'available'
    ).distinct().all()

    return jsonify({
        'districts': [d[0] for d in districts if d[0]]
    })


@common_bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')


@common_bp.route('/contact')
def contact():
    """联系我们页面"""
    return render_template('contact.html')

