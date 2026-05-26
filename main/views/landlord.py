"""
房东视图 - 房源管理、订单管理、消息管理、报表
"""
import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from main import db
from main.models.property import Property
from main.models.lease import Lease
from main.models.message import Message
from main.models.news import News
from main.models.repair import Repair
from main.models.appointment import Appointment
from main.forms.property import PropertyForm
from main.forms.message import NewsForm

landlord_bp = Blueprint('landlord', __name__, url_prefix='/landlord')


def landlord_required(f):
    """房东权限检查装饰器"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_landlord():
            flash('需要房东权限', 'danger')
            return redirect(url_for('common.index'))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def get_upload_folder():
    """获取上传文件夹路径，不存在则创建"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder


@landlord_bp.route('/api/property/<int:property_id>/upload-image', methods=['POST'])
@landlord_required
def upload_property_image(property_id):
    """上传房源图片"""
    property_obj = Property.query.get_or_404(property_id)
    
    # 验证权限
    if property_obj.landlord_id != current_user.id:
        return jsonify({'success': False, 'error': '没有权限'}), 403
    
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': '不支持的文件格式，请上传 JPG、PNG、GIF 或 WEBP 格式'}), 400
    
    # 检查文件大小
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    if file_size > current_app.config['MAX_IMAGE_SIZE']:
        return jsonify({'success': False, 'error': '文件大小超过5MB限制'}), 400
    
    # 检查现有图片数量
    current_images = property_obj.images or []
    if len(current_images) >= current_app.config['MAX_IMAGE_COUNT']:
        return jsonify({'success': False, 'error': '最多只能上传3张图片'}), 400
    
    # 生成唯一文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    # 保存文件
    upload_folder = get_upload_folder()
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # 生成URL路径
    image_url = f"/static/uploads/properties/{filename}"
    
    # 更新房源图片列表
    current_images.append(image_url)
    property_obj.images = current_images
    db.session.commit()
    
    return jsonify({
        'success': True,
        'url': image_url,
        'filename': filename
    })


@landlord_bp.route('/api/property/<int:property_id>/delete-image', methods=['POST'])
@landlord_required
def delete_property_image(property_id):
    """删除房源图片"""
    property_obj = Property.query.get_or_404(property_id)
    
    # 验证权限
    if property_obj.landlord_id != current_user.id:
        return jsonify({'success': False, 'error': '没有权限'}), 403
    
    data = request.get_json()
    image_url = data.get('url')
    
    if not image_url:
        return jsonify({'success': False, 'error': '没有指定图片'}), 400
    
    current_images = property_obj.images or []
    
    if image_url in current_images:
        # 删除物理文件
        filepath = os.path.join(current_app.root_path, image_url.lstrip('/'))
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # 更新数据库
        current_images.remove(image_url)
        property_obj.images = current_images
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': '图片不存在'}), 400


@landlord_bp.route('/api/property/<int:property_id>/images', methods=['GET'])
@landlord_required
def get_property_images(property_id):
    """获取房源图片列表"""
    property_obj = Property.query.get_or_404(property_id)
    
    # 验证权限
    if property_obj.landlord_id != current_user.id:
        return jsonify({'success': False, 'error': '没有权限'}), 403
    
    return jsonify({
        'success': True,
        'images': property_obj.images or []
    })


@landlord_bp.route('/dashboard')
@landlord_required
def dashboard():
    """房东仪表板"""
    from datetime import datetime, timedelta
    
    # 统计数据
    total_properties = Property.query.filter_by(landlord_id=current_user.id).count()
    active_leases = Lease.query.join(Property).filter(
        Property.landlord_id == current_user.id,
        Lease.status == 'active'
    ).count()
    pending_repairs = Repair.query.join(Property).filter(
        Property.landlord_id == current_user.id,
        Repair.status == 'pending'
    ).count()
    unread_messages = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()
    pending_appointments = Appointment.query.join(Property).filter(
        Property.landlord_id == current_user.id,
        Appointment.status == 'pending'
    ).count()

    # 最近预约记录（按创建时间降序，取最近5条）
    recent_appointments = Appointment.query.join(Property).filter(
        Property.landlord_id == current_user.id
    ).order_by(Appointment.created_at.desc()).limit(5).all()

    return render_template(
        'landlord/dashboard.html',
        total_properties=total_properties,
        active_leases=active_leases,
        pending_repairs=pending_repairs,
        unread_messages=unread_messages,
        pending_appointments=pending_appointments,
        recent_appointments=recent_appointments,
        datetime=datetime,
        timedelta=timedelta
    )


@landlord_bp.route('/properties')
@landlord_required
def properties():
    """房源列表"""
    page = request.args.get('page', 1, type=int)
    properties = Property.query.filter_by(landlord_id=current_user.id).order_by(
        Property.created_at.desc()
    ).paginate(page=page, per_page=10)

    return render_template('landlord/properties.html', properties=properties)


@landlord_bp.route('/property/add', methods=['GET', 'POST'])
@landlord_required
def add_property():
    """添加房源"""
    form = PropertyForm()
    
    if request.method == 'POST':
        # 打印调试信息
        print(f"[DEBUG] Form submitted: {request.form}")
        print(f"[DEBUG] Form validators: {form.validate()}")
        print(f"[DEBUG] Form errors: {form.errors}")
    
    if form.validate_on_submit():
        try:
            property_obj = Property(
                title=form.title.data,
                description=form.description.data,
                address=form.address.data,
                district=form.district.data,
                area=form.area.data,
                rooms=form.rooms.data,
                halls=form.halls.data,
                bathrooms=form.bathrooms.data,
                floor=form.floor.data,
                total_floors=form.total_floors.data,
                price=form.price.data,
                deposit=form.deposit.data,
                decoration=form.decoration.data,
                property_type=form.property_type.data,
                status=form.status.data,
                facilities=form.facilities.data if form.facilities.data else [],
                landlord_id=current_user.id,
                images=[]  # 初始化空图片列表
            )
            db.session.add(property_obj)
            db.session.commit()
            
            print(f"[DEBUG] Property added successfully: {property_obj.id}")
            flash('房源发布成功！请继续添加图片', 'success')
            # 重定向到编辑页面以便上传图片
            return redirect(url_for('landlord.edit_property', property_id=property_obj.id))
        
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Failed to add property: {str(e)}")
            flash(f'房源发布失败：{str(e)}', 'danger')

    return render_template('landlord/add_property.html', form=form)


@landlord_bp.route('/property/<int:property_id>/edit', methods=['GET', 'POST'])
@landlord_required
def edit_property(property_id):
    """编辑房源"""
    property_obj = Property.query.get_or_404(property_id)

    if property_obj.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('common.index'))

    form = PropertyForm()
    if form.validate_on_submit():
        property_obj.title = form.title.data
        property_obj.description = form.description.data
        property_obj.address = form.address.data
        property_obj.district = form.district.data
        property_obj.area = form.area.data
        property_obj.rooms = form.rooms.data
        property_obj.halls = form.halls.data
        property_obj.bathrooms = form.bathrooms.data
        property_obj.floor = form.floor.data
        property_obj.total_floors = form.total_floors.data
        property_obj.price = form.price.data
        property_obj.deposit = form.deposit.data
        property_obj.decoration = form.decoration.data
        property_obj.property_type = form.property_type.data
        property_obj.status = form.status.data
        property_obj.facilities = form.facilities.data if form.facilities.data else []

        db.session.commit()
        flash('房源更新成功！', 'success')
        return redirect(url_for('landlord.properties'))
    elif request.method == 'GET':
        form.title.data = property_obj.title
        form.description.data = property_obj.description
        form.address.data = property_obj.address
        form.district.data = property_obj.district
        form.area.data = property_obj.area
        form.rooms.data = property_obj.rooms
        form.halls.data = property_obj.halls
        form.bathrooms.data = property_obj.bathrooms
        form.floor.data = property_obj.floor
        form.total_floors.data = property_obj.total_floors
        form.price.data = property_obj.price
        form.deposit.data = property_obj.deposit
        form.decoration.data = property_obj.decoration
        form.property_type.data = property_obj.property_type
        form.status.data = property_obj.status
        form.facilities.data = property_obj.facilities or []

    return render_template('landlord/edit_property.html', form=form, property=property_obj)


@landlord_bp.route('/property/<int:property_id>/delete', methods=['POST'])
@landlord_required
def delete_property(property_id):
    """删除房源"""
    property_obj = Property.query.get_or_404(property_id)

    if property_obj.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('common.index'))

    db.session.delete(property_obj)
    db.session.commit()
    flash('房源已删除', 'success')
    return redirect(url_for('landlord.properties'))


@landlord_bp.route('/leases')
@landlord_required
def leases():
    """租赁合同列表"""
    page = request.args.get('page', 1, type=int)
    leases = Lease.query.join(Property).filter(
        Property.landlord_id == current_user.id
    ).order_by(Lease.created_at.desc()).paginate(page=page, per_page=10)

    return render_template('landlord/leases.html', leases=leases)


@landlord_bp.route('/repairs')
@landlord_required
def repairs():
    """维修申请列表"""
    page = request.args.get('page', 1, type=int)
    repairs = Repair.query.join(Property).filter(
        Property.landlord_id == current_user.id
    ).order_by(Repair.created_at.desc()).paginate(page=page, per_page=10)

    return render_template('landlord/repairs.html', repairs=repairs)


@landlord_bp.route('/repair/<int:repair_id>/reply', methods=['POST'])
@landlord_required
def reply_repair(repair_id):
    """回复维修申请"""
    repair = Repair.query.get_or_404(repair_id)

    if repair.property.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.repairs'))

    reply = request.form.get('reply')
    status = request.form.get('status')

    repair.landlord_reply = reply
    if status:
        repair.status = status

    db.session.commit()
    flash('已回复维修申请', 'success')
    return redirect(url_for('landlord.repairs'))


@landlord_bp.route('/messages')
@landlord_required
def messages():
    """消息列表"""
    page = request.args.get('page', 1, type=int)
    messages = Message.query.filter_by(receiver_id=current_user.id).order_by(
        Message.created_at.desc()
    ).paginate(page=page, per_page=15)

    return render_template('landlord/messages.html', messages=messages)


@landlord_bp.route('/message/<int:message_id>')
@landlord_required
def message_detail(message_id):
    """消息详情"""
    message = Message.query.get_or_404(message_id)
    
    # 验证权限：确保消息是发给当前用户的
    if message.receiver_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.messages'))
    
    # 标记消息为已读
    if not message.is_read:
        message.is_read = True
        db.session.commit()
    
    return render_template('landlord/message_detail.html', message=message)


@landlord_bp.route('/news')
@landlord_required
def news():
    """新闻列表"""
    page = request.args.get('page', 1, type=int)
    news = News.query.filter_by(landlord_id=current_user.id).order_by(
        News.created_at.desc()
    ).paginate(page=page, per_page=10)

    return render_template('landlord/news.html', news=news)


@landlord_bp.route('/appointments')
@landlord_required
def appointments():
    """预约列表"""
    from datetime import datetime, timedelta
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Appointment.query.join(Property).filter(Property.landlord_id == current_user.id)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    appointments = query.order_by(
        Appointment.created_at.desc()
    ).paginate(page=page, per_page=10)

    return render_template('landlord/appointments.html', appointments=appointments, status=status, datetime=datetime, timedelta=timedelta)


@landlord_bp.route('/appointment/<int:appointment_id>/confirm', methods=['POST'])
@landlord_required
def confirm_appointment(appointment_id):
    """确认预约"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.appointments'))
    
    appointment.confirm()
    db.session.commit()
    
    # 创建确认消息通知租客
    message = Message(
        sender_id=current_user.id,
        receiver_id=appointment.tenant_id,
        content=f"您的预约已确认！预约时间: {appointment.preferred_time.strftime('%Y-%m-%d %H:%M')}",
        message_type='notification'
    )
    db.session.add(message)
    db.session.commit()
    
    flash('预约已确认', 'success')
    return redirect(url_for('landlord.appointments'))


@landlord_bp.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@landlord_required
def cancel_appointment(appointment_id):
    """取消预约"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.appointments'))
    
    appointment.cancel()
    db.session.commit()
    
    # 创建取消消息通知租客
    message = Message(
        sender_id=current_user.id,
        receiver_id=appointment.tenant_id,
        content=f"您的预约已取消。预约时间: {appointment.preferred_time.strftime('%Y-%m-%d %H:%M')}",
        message_type='notification'
    )
    db.session.add(message)
    db.session.commit()
    
    flash('预约已取消', 'success')
    return redirect(url_for('landlord.appointments'))


@landlord_bp.route('/news/add', methods=['GET', 'POST'])
@landlord_required
def add_news():
    """发布新闻"""
    form = NewsForm()
    if form.validate_on_submit():
        news = News(
            title=form.title.data,
            content=form.content.data,
            news_type=form.news_type.data,
            landlord_id=current_user.id
        )
        db.session.add(news)
        db.session.commit()

        flash('新闻发布成功！', 'success')
        return redirect(url_for('landlord.news'))

    return render_template('landlord/add_news.html', form=form)


@landlord_bp.route('/reports')
@landlord_required
def reports():
    """报表统计"""
    # 获取房东的统计数据
    total_properties = Property.query.filter_by(landlord_id=current_user.id).count()
    available_properties = Property.query.filter_by(
        landlord_id=current_user.id, status='available'
    ).count()
    rented_properties = Property.query.filter_by(
        landlord_id=current_user.id, status='rented'
    ).count()

    occupancy_rate = (rented_properties / total_properties * 100) if total_properties > 0 else 0

    # 获取租赁统计
    active_leases = Lease.query.join(Property).filter(
        Property.landlord_id == current_user.id,
        Lease.status == 'active'
    ).all()

    total_income = sum(lease.monthly_rent for lease in active_leases)

    return render_template(
        'landlord/reports.html',
        total_properties=total_properties,
        available_properties=available_properties,
        rented_properties=rented_properties,
        occupancy_rate=occupancy_rate,
        active_leases=active_leases,
        total_income=total_income
    )

