"""
通用视图 - 首页、房源搜索、房源详情
"""
import json
import os

from flask import Blueprint, render_template, request, jsonify, url_for
from main import db
from main.models.property import Property
from main.models.user import User
from main.models.news import News
from main.forms.property import SearchPropertyForm

common_bp = Blueprint('common', __name__)


@common_bp.route('/')
def index():
    """首页"""
    base_query = Property.query.filter_by(status='available')

    latest_properties = base_query.order_by(Property.created_at.desc()).limit(8).all()
    budget_properties = base_query.order_by(Property.price.asc()).limit(8).all()
    premium_properties = base_query.order_by(Property.price.desc()).limit(8).all()
    mike_properties = base_query.join(User, Property.landlord_id == User.id).filter(
        User.username == 'Mike'
    ).order_by(Property.created_at.desc()).limit(8).all()

    # 热门区域统计
    popular_districts = db.session.query(
        Property.province,
        Property.city,
        Property.district,
        db.func.count(Property.id).label('count')
    ).filter_by(status='available').group_by(
        Property.province, Property.city, Property.district
    ).order_by(db.func.count(Property.id).desc()).limit(8).all()

    featured_sections = [
        {
            'title': '最新发布',
            'subtitle': '刚刚上架的可租房源',
            'properties': latest_properties,
            'url': url_for('common.search', sort_by='newest')
        },
        {
            'title': '低价探索',
            'subtitle': '预算友好的测试房源',
            'properties': budget_properties,
            'url': url_for('common.search', sort_by='price_low')
        },
        {
            'title': '品质整租',
            'subtitle': '价格更高、配置更完整的选择',
            'properties': premium_properties,
            'url': url_for('common.search', sort_by='price_high')
        },
        {
            'title': 'Mike 的中国房源',
            'subtitle': '测试阶段用于覆盖不同城市和价位',
            'properties': mike_properties,
            'url': url_for('common.search')
        },
    ]

    return render_template(
        'index.html',
        featured_sections=featured_sections,
        popular_districts=popular_districts
    )


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
                Property.address.ilike(f'%{keyword}%'),
                Property.province.ilike(f'%{keyword}%'),
                Property.city.ilike(f'%{keyword}%'),
                Property.district.ilike(f'%{keyword}%')
            )
        )

    # 省-市-区县搜索
    province = request.args.get('province', '')
    if province:
        query = query.filter_by(province=province)

    city = request.args.get('city', '')
    if city:
        query = query.filter_by(city=city)

    district = request.args.get('district', '')
    if district:
        query = query.filter_by(district=district)

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
    else:
        sort_by = 'newest'
        query = query.order_by(Property.created_at.desc())

    page = request.args.get('page', 1, type=int)
    properties = query.paginate(page=page, per_page=12)

    return render_template(
        'search.html',
        properties=properties,
        form=form,
        sort_by=sort_by,
        province=province,
        city=city,
        district=district
    )


@common_bp.route('/property/<int:property_id>')
def property_detail(property_id):
    """房源详情页面"""
    property_obj = Property.query.get_or_404(property_id)
    landlord = User.query.get(property_obj.landlord_id)

    # 获取同区域的其他房源
    related_properties = Property.query.filter(
        Property.id != property_id,
        Property.province == property_obj.province,
        Property.city == property_obj.city,
        Property.district == property_obj.district,
        Property.status == 'available'
    ).limit(4).all()

    return render_template(
        'property_detail.html',
        property=property_obj,
        landlord=landlord,
        related_properties=related_properties
    )


@common_bp.route('/news')
def news():
    """用户查看新闻/公告列表。"""
    page = request.args.get('page', 1, type=int)
    news_type = request.args.get('news_type', '')
    query = News.query.filter_by(is_published=True)
    if news_type in {'rental', 'maintenance', 'announcement'}:
        query = query.filter_by(news_type=news_type)
    else:
        news_type = ''
    news_page = query.order_by(News.created_at.desc()).paginate(page=page, per_page=12)
    return render_template('news.html', news=news_page, news_type=news_type, news_type_labels=_news_type_labels())


@common_bp.route('/news/<int:news_id>')
def news_detail(news_id):
    """用户查看新闻/公告详情。"""
    news_item = News.query.filter_by(id=news_id, is_published=True).first_or_404()
    return render_template('news_detail.html', news=news_item, news_type_labels=_news_type_labels())


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


@common_bp.route('/api/locations')
def get_locations():
    """获取中国大陆省、市、区县。"""
    province = request.args.get('province', '')
    city = request.args.get('city', '')
    locations = _load_mainland_locations()

    if not province:
        return jsonify({'provinces': [item['name'] for item in locations]})

    if province and not city:
        province_item = _find_location_item(locations, province)
        return jsonify({'cities': [item['name'] for item in province_item.get('cities', [])] if province_item else []})

    province_item = _find_location_item(locations, province)
    city_item = _find_location_item(province_item.get('cities', []) if province_item else [], city)
    return jsonify({'districts': [item['name'] for item in city_item.get('districts', [])] if city_item else []})


def _load_mainland_locations():
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'static',
        'data',
        'china_mainland_locations.json'
    )
    with open(data_path, 'r', encoding='utf-8') as data_file:
        return json.load(data_file)


def _find_location_item(items, name):
    return next((item for item in items if item.get('name') == name), None)


def _news_type_labels():
    return {
        'rental': '租赁',
        'maintenance': '维修',
        'announcement': '公告',
    }


@common_bp.route('/about')
def about():
    """关于页面"""
    return render_template('about.html')


@common_bp.route('/contact')
def contact():
    """联系我们页面"""
    return render_template('contact.html')
