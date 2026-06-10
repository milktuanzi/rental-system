"""
房东视图 - 房源管理、订单管理、消息管理、报表
"""
import os
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from main import db
from main.models.user import User
from main.models.property import Property
from main.models.lease import Lease
from main.models.message import Message
from main.models.news import News
from main.models.repair import Repair
from main.models.complaint import Complaint
from main.models.appointment import Appointment
from main.models.payment import Payment
from main.forms.property import PropertyForm
from main.forms.lease import LeaseForm, PaymentForm
from main.forms.message import MessageForm, NewsForm

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


def get_news_upload_folder():
    """获取新闻图片上传目录。"""
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'news')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder


def save_news_image(file):
    """保存新闻图片并返回可访问路径。"""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError('仅支持 png、jpg、jpeg、gif、webp 图片格式')

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit('.', 1)[1].lower()
    filename = f"news_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(get_news_upload_folder(), filename)
    file.save(filepath)
    return f"/static/uploads/news/{filename}"


def save_news_images(files, limit=9):
    """批量保存新闻内容图，最多保留 limit 张。"""
    image_urls = []
    for file in files:
        if not file or not file.filename:
            continue
        if len(image_urls) >= limit:
            break
        image_urls.append(save_news_image(file))
    return image_urls


def get_payment_upload_folder():
    """获取账单图片上传目录。"""
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'payments')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder


def save_payment_image(file, prefix='payment'):
    """保存账单相关图片并返回可访问路径。"""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError('仅支持 png、jpg、jpeg、gif、webp 图片格式')

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit('.', 1)[1].lower()
    filename = f"{prefix}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(get_payment_upload_folder(), filename)
    file.save(filepath)
    return f"/static/uploads/payments/{filename}"


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
                province=form.province.data,
                city=form.city.data,
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
        property_obj.province = form.province.data
        property_obj.city = form.city.data
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
        form.province.data = property_obj.province
        form.city.data = property_obj.city
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


@landlord_bp.route('/lease/<int:lease_id>')
@landlord_required
def lease_detail(lease_id):
    """房东查看租赁合同详情"""
    lease = Lease.query.get_or_404(lease_id)

    if lease.property.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.leases'))

    payments = Payment.query.filter_by(lease_id=lease.id).order_by(Payment.created_at.desc()).all()
    return render_template('landlord/lease_detail.html', lease=lease, payments=payments)


@landlord_bp.route('/payments')
@landlord_required
def payments():
    """房东账单列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = Payment.query.join(Lease).join(Property).filter(Property.landlord_id == current_user.id)
    if status in {'pending', 'submitted', 'completed', 'overdue'}:
        query = query.filter(Payment.status == status)
    payments_page = query.order_by(Payment.created_at.desc()).paginate(page=page, per_page=12)
    return render_template('landlord/payments.html', payments=payments_page, status=status)


@landlord_bp.route('/lease/<int:lease_id>/payment/create', methods=['GET', 'POST'])
@landlord_required
def create_payment(lease_id):
    """根据合同发起账单"""
    lease = Lease.query.get_or_404(lease_id)
    if lease.property.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.leases'))
    if lease.status not in {'active', 'pending'}:
        flash('当前合同状态不可发起账单', 'warning')
        return redirect(url_for('landlord.lease_detail', lease_id=lease.id))

    form = PaymentForm()
    if request.method == 'GET':
        form.amount.data = lease.monthly_rent
        form.payment_period.data = datetime.utcnow().strftime('%Y-%m')
        form.due_date.data = datetime.utcnow().date() + timedelta(days=7)

    if form.validate_on_submit():
        try:
            qr_code = save_payment_image(request.files.get('landlord_qr_code'), 'landlord_qr')
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template('landlord/payment_form.html', form=form, lease=lease)

        if not qr_code:
            flash('请上传收款码图片', 'warning')
            return render_template('landlord/payment_form.html', form=form, lease=lease)

        payment = Payment(
            lease_id=lease.id,
            amount=form.amount.data,
            payment_period=form.payment_period.data,
            due_date=datetime.combine(form.due_date.data, datetime.max.time()),
            landlord_qr_code=qr_code,
            remark=form.remark.data,
            status='pending'
        )
        db.session.add(payment)
        db.session.add(Message(
            sender_id=current_user.id,
            receiver_id=lease.tenant_id,
            content=f"房东已发起账单：{payment.payment_period}，金额 ¥{payment.amount:.2f}。请进入账单页面查看收款码并支付。",
            message_type='notification'
        ))
        db.session.commit()
        flash('账单已发起', 'success')
        return redirect(url_for('landlord.payments'))

    return render_template('landlord/payment_form.html', form=form, lease=lease)


@landlord_bp.route('/payment/<int:payment_id>/confirm', methods=['POST'])
@landlord_required
def confirm_payment(payment_id):
    """房东确认收到租客付款"""
    payment = Payment.query.get_or_404(payment_id)
    if payment.lease.property.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.payments'))
    if payment.status != 'submitted':
        flash('只能确认租客已提交支付的账单', 'warning')
        return redirect(url_for('landlord.payments'))

    payment.status = 'completed'
    payment.confirmed_at = datetime.utcnow()
    payment.updated_at = datetime.utcnow()
    db.session.add(Message(
        sender_id=current_user.id,
        receiver_id=payment.lease.tenant_id,
        content=f"房东已确认收到您账单 {payment.payment_period or payment.id} 的付款，账单已完成。",
        message_type='notification'
    ))
    db.session.commit()
    flash('已确认收款，账单完成', 'success')
    return redirect(url_for('landlord.payments'))


@landlord_bp.route('/appointment/<int:appointment_id>/lease/create', methods=['GET', 'POST'])
@landlord_required
def create_lease_from_appointment(appointment_id):
    """基于已确认预约发起租赁合同"""
    appointment = Appointment.query.get_or_404(appointment_id)

    if appointment.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.appointments'))

    if appointment.status != 'confirmed':
        flash('只能对已确认的预约发起合同', 'warning')
        return redirect(url_for('landlord.appointments'))

    existing_lease = Lease.query.filter(
        Lease.property_id == appointment.property_id,
        Lease.status.in_(['pending', 'active'])
    ).first()
    if existing_lease:
        flash('该房源已有待签署或生效合同', 'info')
        return redirect(url_for('landlord.lease_detail', lease_id=existing_lease.id))

    if appointment.property.status != 'available':
        flash('该房源当前不可发起新合同', 'warning')
        return redirect(url_for('landlord.appointments'))

    form = LeaseForm()
    if request.method == 'GET':
        form.monthly_rent.data = appointment.property.price
        form.deposit_amount.data = appointment.property.deposit
        form.start_date.data = datetime.utcnow().date()
        form.lease_duration.data = 12
        form.contract_content.data = _default_contract_content(appointment, 12)

    if form.validate_on_submit():
        start_date = datetime.combine(form.start_date.data, datetime.min.time())
        end_date = start_date + timedelta(days=form.lease_duration.data * 30)
        lease = Lease(
            property_id=appointment.property_id,
            tenant_id=appointment.tenant_id,
            start_date=start_date,
            end_date=end_date,
            contract_content=form.contract_content.data,
            monthly_rent=form.monthly_rent.data,
            deposit_amount=form.deposit_amount.data,
            status='pending',
            is_signed=False
        )
        db.session.add(lease)
        db.session.flush()

        message = Message(
            sender_id=current_user.id,
            receiver_id=appointment.tenant_id,
            content=f"房东已为房源“{appointment.property.title}”发起租赁合同，请进入“我的租赁”查看并签署。",
            message_type='notification'
        )
        db.session.add(message)
        db.session.commit()

        flash('合同已发起，等待租客签署', 'success')
        return redirect(url_for('landlord.lease_detail', lease_id=lease.id))

    return render_template(
        'landlord/create_lease.html',
        form=form,
        appointment=appointment
    )


@landlord_bp.route('/repairs')
@landlord_required
def repairs():
    """维修申请列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    allowed_statuses = {'pending', 'in_progress', 'completed', 'rejected'}
    if status and status not in allowed_statuses:
        status = ''

    query = Repair.query.join(Property).filter(
        Property.landlord_id == current_user.id
    )

    if status:
        query = query.filter(Repair.status == status)

    repairs = query.order_by(Repair.created_at.desc()).paginate(page=page, per_page=10)

    repair_stats = {
        'pending': Repair.query.join(Property).filter(
            Property.landlord_id == current_user.id,
            Repair.status == 'pending'
        ).count(),
        'in_progress': Repair.query.join(Property).filter(
            Property.landlord_id == current_user.id,
            Repair.status == 'in_progress'
        ).count(),
        'completed': Repair.query.join(Property).filter(
            Property.landlord_id == current_user.id,
            Repair.status == 'completed'
        ).count(),
        'rejected': Repair.query.join(Property).filter(
            Property.landlord_id == current_user.id,
            Repair.status == 'rejected'
        ).count(),
    }

    return render_template(
        'landlord/repairs.html',
        repairs=repairs,
        status=status,
        repair_stats=repair_stats
    )


@landlord_bp.route('/repair/<int:repair_id>/reply', methods=['POST'])
@landlord_required
def reply_repair(repair_id):
    """回复维修申请"""
    repair = Repair.query.get_or_404(repair_id)

    if repair.property.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.repairs'))

    reply = (request.form.get('reply') or '').strip()
    status = request.form.get('status')
    allowed_statuses = {'pending', 'in_progress', 'completed', 'rejected'}

    if status not in allowed_statuses:
        flash('维修状态无效', 'danger')
        return redirect(url_for('landlord.repairs'))

    if not reply:
        flash('请输入处理说明', 'warning')
        return redirect(url_for('landlord.repairs'))

    repair.landlord_reply = reply
    repair.status = status

    if status == 'completed' and repair.completed_at is None:
        repair.completed_at = datetime.utcnow()
    elif status != 'completed':
        repair.completed_at = None

    message = Message(
        sender_id=current_user.id,
        receiver_id=repair.tenant_id,
        content=f"您的维修申请“{repair.title}”已更新为：{_repair_status_label(status)}。\n处理说明：{reply}",
        message_type='notification'
    )
    db.session.add(message)

    db.session.commit()
    flash('已回复维修申请', 'success')
    return redirect(url_for('landlord.repairs', status=request.args.get('status', '')))


@landlord_bp.route('/complaints')
@landlord_required
def complaints():
    """接收并处理租客投诉"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    allowed_statuses = {'pending', 'under_review', 'resolved', 'rejected'}
    if status and status not in allowed_statuses:
        status = ''

    query = Complaint.query.filter(Complaint.target_id == current_user.id)
    if status:
        query = query.filter(Complaint.status == status)

    complaints = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=10)

    complaint_stats = {
        'pending': Complaint.query.filter_by(target_id=current_user.id, status='pending').count(),
        'under_review': Complaint.query.filter_by(target_id=current_user.id, status='under_review').count(),
        'resolved': Complaint.query.filter_by(target_id=current_user.id, status='resolved').count(),
        'rejected': Complaint.query.filter_by(target_id=current_user.id, status='rejected').count(),
    }

    return render_template(
        'landlord/complaints.html',
        complaints=complaints,
        status=status,
        complaint_stats=complaint_stats
    )


@landlord_bp.route('/complaint/<int:complaint_id>/handle', methods=['POST'])
@landlord_required
def handle_complaint(complaint_id):
    """处理租客投诉"""
    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.target_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.complaints'))

    status = request.form.get('status')
    reply = (request.form.get('reply') or '').strip()
    allowed_statuses = {'pending', 'under_review', 'resolved', 'rejected'}

    if status not in allowed_statuses:
        flash('投诉状态无效', 'danger')
        return redirect(url_for('landlord.complaints'))

    if not reply:
        flash('请输入处理说明', 'warning')
        return redirect(url_for('landlord.complaints', status=request.args.get('status', '')))

    complaint.status = status
    complaint.admin_reply = reply
    if status == 'resolved':
        complaint.resolved_at = datetime.utcnow()
    elif status != 'resolved':
        complaint.resolved_at = None

    db.session.add(Message(
        sender_id=current_user.id,
        receiver_id=complaint.user_id,
        content=f"您的投诉“{complaint.title}”已更新为：{_complaint_status_label(status)}。\n处理说明：{reply}",
        message_type='notification'
    ))
    db.session.commit()

    flash('投诉已处理', 'success')
    return redirect(url_for('landlord.complaints', status=request.args.get('status', '')))


@landlord_bp.route('/messages')
@landlord_required
def messages():
    """兼容旧消息列表入口，进入会话中心。"""
    return redirect(url_for('landlord.conversation_home'))


@landlord_bp.route('/conversation/')
@landlord_required
def conversation_home():
    """房东会话中心：未选中联系人时只展示会话列表。"""
    return render_template(
        'landlord/conversation.html',
        form=MessageForm(),
        other_user=None,
        conversations=_build_conversations(current_user.id),
        messages=[]
    )


@landlord_bp.route('/message/<int:message_id>')
@landlord_required
def message_detail(message_id):
    """兼容旧消息详情链接，跳转到对应会话"""
    message = Message.query.get_or_404(message_id)
    
    if message.receiver_id != current_user.id and message.sender_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.conversation_home'))
    
    other_user_id = message.sender_id if message.sender_id != current_user.id else message.receiver_id
    return redirect(url_for('landlord.conversation', user_id=other_user_id))


@landlord_bp.route('/conversation/<int:user_id>', methods=['GET', 'POST'])
@landlord_required
def conversation(user_id):
    """房东与租客/管理员的对话"""
    other_user = User.query.get_or_404(user_id)

    if not (other_user.is_tenant() or other_user.is_admin()):
        flash('只能与租客或管理员进行对话', 'danger')
        return redirect(url_for('landlord.conversation_home'))

    form = MessageForm()
    if form.validate_on_submit() and not other_user.is_admin():
        message = Message(
            sender_id=current_user.id,
            receiver_id=other_user.id,
            content=form.content.data,
            message_type='message'
        )
        db.session.add(message)
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'messages': _conversation_payload(current_user.id, other_user.id)})
        return redirect(url_for('landlord.conversation', user_id=other_user.id))

    if form.validate_on_submit() and other_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': '系统通知无需回复'}), 400
        flash('系统通知无需回复', 'info')
        return redirect(url_for('landlord.conversation', user_id=other_user.id))

    conversation_messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.receiver_id == other_user.id),
            db.and_(Message.sender_id == other_user.id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()

    unread_messages = [
        message for message in conversation_messages
        if message.receiver_id == current_user.id and not message.is_read
    ]
    for message in unread_messages:
        message.is_read = True
    if unread_messages:
        db.session.commit()

    return render_template(
        'landlord/conversation.html',
        form=form,
        other_user=other_user,
        conversations=_build_conversations(current_user.id),
        messages=_serialize_messages(conversation_messages)
    )


@landlord_bp.route('/conversation/<int:user_id>/messages')
@landlord_required
def conversation_messages(user_id):
    """获取房东与租客/管理员的最新对话消息。"""
    other_user = User.query.get_or_404(user_id)

    if not (other_user.is_tenant() or other_user.is_admin()):
        return jsonify({'success': False, 'error': '只能与租客或管理员进行对话'}), 403

    messages = _conversation_query(current_user.id, other_user.id).all()
    unread_messages = [
        message for message in messages
        if message.receiver_id == current_user.id and not message.is_read
    ]
    for message in unread_messages:
        message.is_read = True
    if unread_messages:
        db.session.commit()

    return jsonify({'success': True, 'messages': _serialize_messages(messages)})


@landlord_bp.route('/news')
@landlord_required
def news():
    """新闻列表"""
    page = request.args.get('page', 1, type=int)
    news_type = request.args.get('news_type', '')
    if news_type and news_type not in _news_type_labels():
        news_type = ''
    query = News.query.filter_by(landlord_id=current_user.id)

    if news_type:
        query = query.filter(News.news_type == news_type)

    news = query.order_by(
        News.created_at.desc()
    ).paginate(page=page, per_page=10)

    return render_template(
        'landlord/news.html',
        news=news,
        news_type=news_type,
        news_type_labels=_news_type_labels()
    )


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
        try:
            cover_image = save_news_image(request.files.get('cover_image'))
            content_images = save_news_images(request.files.getlist('content_images'))
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template('landlord/add_news.html', form=form, page_title='发布公告', submit_text='发布')

        news = News(
            title=form.title.data,
            content=form.content.data,
            news_type=form.news_type.data,
            landlord_id=current_user.id,
            cover_image=cover_image,
            content_images=content_images
        )
        db.session.add(news)
        db.session.commit()

        flash('新闻发布成功！', 'success')
        return redirect(url_for('landlord.news'))

    return render_template('landlord/add_news.html', form=form, page_title='发布公告', submit_text='发布')


@landlord_bp.route('/news/<int:news_id>/edit', methods=['GET', 'POST'])
@landlord_required
def edit_news(news_id):
    """编辑新闻/公告"""
    news = News.query.get_or_404(news_id)

    if news.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.news'))

    form = NewsForm(obj=news)
    if form.validate_on_submit():
        try:
            cover_image = save_news_image(request.files.get('cover_image'))
            new_content_images = save_news_images(request.files.getlist('content_images'))
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template(
                'landlord/add_news.html',
                form=form,
                page_title='编辑公告',
                submit_text='保存修改',
                news=news
            )

        news.title = form.title.data
        news.content = form.content.data
        news.news_type = form.news_type.data
        if cover_image:
            news.cover_image = cover_image
        if new_content_images:
            existing_images = news.content_images or []
            news.content_images = existing_images + new_content_images
        news.updated_at = datetime.utcnow()
        db.session.commit()

        flash('公告更新成功！', 'success')
        return redirect(url_for('landlord.news'))

    return render_template(
        'landlord/add_news.html',
        form=form,
        page_title='编辑公告',
        submit_text='保存修改',
        news=news
    )


@landlord_bp.route('/news/<int:news_id>/delete', methods=['POST'])
@landlord_required
def delete_news(news_id):
    """删除新闻/公告"""
    news = News.query.get_or_404(news_id)

    if news.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.news'))

    db.session.delete(news)
    db.session.commit()

    flash('公告已删除', 'success')
    return redirect(url_for('landlord.news'))


@landlord_bp.route('/news/<int:news_id>/toggle', methods=['POST'])
@landlord_required
def toggle_news(news_id):
    """发布/下架新闻公告"""
    news = News.query.get_or_404(news_id)

    if news.landlord_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('landlord.news'))

    news.is_published = not news.is_published
    news.updated_at = datetime.utcnow()
    db.session.commit()

    flash('公告状态已更新', 'success')
    return redirect(url_for('landlord.news'))


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
    maintenance_properties = Property.query.filter_by(
        landlord_id=current_user.id, status='maintenance'
    ).count()

    occupancy_rate = (rented_properties / total_properties * 100) if total_properties > 0 else 0

    # 获取租赁统计
    active_leases = Lease.query.join(Property).filter(
        Property.landlord_id == current_user.id,
        Lease.status == 'active'
    ).all()

    total_income = sum(lease.monthly_rent for lease in active_leases)

    lease_ids = [lease.id for lease in active_leases]
    paid_income = 0
    pending_payments = 0
    overdue_payments = 0
    if lease_ids:
        paid_income = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).filter(
            Payment.lease_id.in_(lease_ids),
            Payment.status == 'completed'
        ).scalar() or 0
        pending_payments = Payment.query.filter(
            Payment.lease_id.in_(lease_ids),
            Payment.status == 'pending'
        ).count()
        overdue_payments = Payment.query.filter(
            Payment.lease_id.in_(lease_ids),
            db.or_(
                Payment.status == 'overdue',
                db.and_(Payment.status == 'pending', Payment.due_date < datetime.utcnow())
            )
        ).count()

    repair_stats = {
        'pending': Repair.query.join(Property).filter(
            Property.landlord_id == current_user.id,
            Repair.status == 'pending'
        ).count(),
        'in_progress': Repair.query.join(Property).filter(
            Property.landlord_id == current_user.id,
            Repair.status == 'in_progress'
        ).count(),
        'completed': Repair.query.join(Property).filter(
            Property.landlord_id == current_user.id,
            Repair.status == 'completed'
        ).count(),
        'rejected': Repair.query.join(Property).filter(
            Property.landlord_id == current_user.id,
            Repair.status == 'rejected'
        ).count(),
    }

    return render_template(
        'landlord/reports.html',
        total_properties=total_properties,
        available_properties=available_properties,
        rented_properties=rented_properties,
        maintenance_properties=maintenance_properties,
        occupancy_rate=occupancy_rate,
        active_leases=active_leases,
        total_income=total_income,
        paid_income=paid_income,
        pending_payments=pending_payments,
        overdue_payments=overdue_payments,
        repair_stats=repair_stats
    )


def _news_type_labels():
    return {
        'rental': '租赁相关',
        'maintenance': '维修相关',
        'announcement': '公告',
    }


def _repair_status_label(status):
    return {
        'pending': '待处理',
        'in_progress': '处理中',
        'completed': '已完成',
        'rejected': '已拒绝',
    }.get(status, status)


def _complaint_status_label(status):
    return {
        'pending': '待处理',
        'under_review': '处理中',
        'resolved': '已解决',
        'rejected': '已驳回',
    }.get(status, status)


def _default_contract_content(appointment, duration_months):
    property_obj = appointment.property
    tenant = appointment.tenant
    landlord = appointment.landlord
    return (
        f"甲方（出租方）：{landlord.username}\n"
        f"乙方（承租方）：{tenant.username}\n\n"
        f"一、租赁房源：{property_obj.title}，地址：{property_obj.address}。\n"
        f"二、租赁期限：{duration_months}个月，具体起止日期以本合同填写日期为准。\n"
        f"三、租金与押金：月租金为人民币{property_obj.price}元，押金为人民币{property_obj.deposit}元。\n"
        "四、乙方应按约定用途使用房屋，并按时支付租金及相关费用。\n"
        "五、甲方应保证房屋基本居住条件，并按约定协助处理维修事项。\n"
        "六、双方确认线上签署后，本合同进入生效流程；乙方签署完成后合同正式生效。\n"
        "七、未尽事宜由双方协商解决。"
    )


def _build_conversations(user_id):
    messages = Message.query.filter(
        db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    ).order_by(Message.created_at.desc()).all()

    conversations = {}
    for message in messages:
        other_user = message.sender if message.sender_id != user_id else message.receiver
        if not (other_user.is_tenant() or other_user.is_admin()):
            continue
        if other_user.id not in conversations:
            conversation_url = url_for('landlord.conversation', user_id=other_user.id)
            conversations[other_user.id] = {
                'user': other_user,
                'last_message': message,
                'unread_count': 0,
                'url': conversation_url,
            }
        if message.receiver_id == user_id and not message.is_read:
            conversations[other_user.id]['unread_count'] += 1

    return list(conversations.values())


def _conversation_query(user_id, other_user_id):
    return Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == user_id, Message.receiver_id == other_user_id),
            db.and_(Message.sender_id == other_user_id, Message.receiver_id == user_id)
        )
    ).order_by(Message.created_at.asc())


def _conversation_payload(user_id, other_user_id):
    return _serialize_messages(_conversation_query(user_id, other_user_id).all())


def _serialize_messages(messages):
    return [
        {
            'id': message.id,
            'sender_id': message.sender_id,
            'sender_name': message.sender.username,
            'content': message.content,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_mine': message.sender_id == current_user.id,
            **_message_action(message),
        }
        for message in messages
    ]


def _message_action(message):
    content = message.content or ''
    if '账单' in content or '支付' in content or '付款' in content:
        return {'action_url': url_for('landlord.payments'), 'action_label': '处理账单'}
    if '预约' in content:
        return {'action_url': url_for('landlord.appointments'), 'action_label': '处理预约'}
    if '维修' in content:
        return {'action_url': url_for('landlord.repairs'), 'action_label': '处理维修'}
    if '投诉' in content:
        return {'action_url': url_for('landlord.complaints'), 'action_label': '处理投诉'}
    if '合同' in content or '租赁' in content:
        return {'action_url': url_for('landlord.leases'), 'action_label': '查看合同'}
    return {'action_url': None, 'action_label': None}
