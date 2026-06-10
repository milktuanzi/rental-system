"""
管理员视图 - 用户、房源、预约、合同、维修、投诉、公告、账单与系统报表
"""
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response, jsonify
from flask_login import login_required, current_user

from main import db
from main.models.appointment import Appointment
from main.models.complaint import Complaint
from main.models.lease import Lease
from main.models.message import Message
from main.models.news import News
from main.models.payment import Payment
from main.models.property import Property
from main.models.repair import Repair
from main.models.user import User
from main.forms.message import MessageForm, NewsForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


USER_TYPES = {'tenant', 'landlord', 'admin'}
PROPERTY_STATUSES = {'available', 'rented', 'maintenance'}
APPOINTMENT_STATUSES = {'pending', 'confirmed', 'cancelled', 'completed'}
LEASE_STATUSES = {'pending', 'active', 'completed', 'terminated'}
COMPLAINT_STATUSES = {'pending', 'under_review', 'resolved', 'rejected'}
REPAIR_STATUSES = {'pending', 'in_progress', 'completed', 'rejected'}
PAYMENT_STATUSES = {'pending', 'submitted', 'completed', 'overdue'}


def admin_required(f):
    """管理员权限检查装饰器"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('需要管理员权限', 'danger')
            return redirect(url_for('common.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """管理员仪表板"""
    stats = {
        'total_users': User.query.count(),
        'total_landlords': User.query.filter_by(user_type='landlord').count(),
        'total_tenants': User.query.filter_by(user_type='tenant').count(),
        'total_admins': User.query.filter_by(user_type='admin').count(),
        'total_properties': Property.query.count(),
        'available_properties': Property.query.filter_by(status='available').count(),
        'active_leases': Lease.query.filter_by(status='active').count(),
        'pending_leases': Lease.query.filter_by(status='pending').count(),
        'pending_appointments': Appointment.query.filter_by(status='pending').count(),
        'pending_repairs': Repair.query.filter_by(status='pending').count(),
        'pending_complaints': Complaint.query.filter_by(status='pending').count(),
        'pending_payments': Payment.query.filter_by(status='pending').count(),
        'published_news': News.query.filter_by(is_published=True).count(),
    }
    recent_users = User.query.order_by(User.created_at.desc()).limit(6).all()
    recent_properties = Property.query.order_by(Property.created_at.desc()).limit(6).all()
    recent_tasks = {
        'appointments': Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all(),
        'repairs': Repair.query.order_by(Repair.created_at.desc()).limit(5).all(),
        'complaints': Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all(),
    }
    return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users, recent_properties=recent_properties, recent_tasks=recent_tasks)


@admin_bp.route('/messages')
@admin_required
def messages():
    """兼容旧消息列表入口，进入管理员会话中心。"""
    return redirect(url_for('admin.conversation_home'))


@admin_bp.route('/conversation/')
@admin_required
def conversation_home():
    """管理员会话中心：未选中联系人时只展示会话列表。"""
    return render_template(
        'admin/conversation.html',
        form=MessageForm(),
        other_user=None,
        conversations=_build_conversations(current_user.id),
        messages=[]
    )


@admin_bp.route('/conversation/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def conversation(user_id):
    """管理员与房东/租客的对话。"""
    other_user = User.query.get_or_404(user_id)

    if not (other_user.is_landlord() or other_user.is_tenant()):
        flash('只能与房东或租客进行对话', 'danger')
        return redirect(url_for('admin.conversation_home'))

    form = MessageForm()
    if form.validate_on_submit():
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
        return redirect(url_for('admin.conversation', user_id=other_user.id))

    conversation_messages = _conversation_query(current_user.id, other_user.id).all()
    unread_messages = [
        message for message in conversation_messages
        if message.receiver_id == current_user.id and not message.is_read
    ]
    for message in unread_messages:
        message.is_read = True
    if unread_messages:
        db.session.commit()

    return render_template(
        'admin/conversation.html',
        form=form,
        other_user=other_user,
        conversations=_build_conversations(current_user.id),
        messages=_serialize_messages(conversation_messages)
    )


@admin_bp.route('/conversation/<int:user_id>/messages')
@admin_required
def conversation_messages(user_id):
    """获取管理员与房东/租客的最新对话消息。"""
    other_user = User.query.get_or_404(user_id)

    if not (other_user.is_landlord() or other_user.is_tenant()):
        return jsonify({'success': False, 'error': '只能与房东或租客进行对话'}), 403

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


@admin_bp.route('/users')
@admin_required
def users():
    """用户管理"""
    page = request.args.get('page', 1, type=int)
    user_type = request.args.get('type', '')
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', '')

    query = User.query
    if user_type in USER_TYPES:
        query = query.filter_by(user_type=user_type)
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'disabled':
        query = query.filter_by(is_active=False)
    if keyword:
        query = query.filter(db.or_(User.username.ilike(f'%{keyword}%'), User.email.ilike(f'%{keyword}%'), User.phone.ilike(f'%{keyword}%')))

    users_page = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/users.html', users=users_page, user_type=user_type, keyword=keyword, status=status)


@admin_bp.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """启用/禁用用户"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('无法修改自己的状态', 'warning')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'用户已{"启用" if user.is_active else "禁用"}', 'success')
    return redirect(_redirect_back('admin.users'))


@admin_bp.route('/user/<int:user_id>/verify', methods=['POST'])
@admin_required
def verify_user(user_id):
    """认证/取消认证用户"""
    user = User.query.get_or_404(user_id)
    user.is_verified = not user.is_verified
    db.session.commit()
    flash(f'用户已{"认证" if user.is_verified else "取消认证"}', 'success')
    return redirect(_redirect_back('admin.users'))


@admin_bp.route('/user/<int:user_id>/type', methods=['POST'])
@admin_required
def update_user_type(user_id):
    """修改用户角色"""
    user = User.query.get_or_404(user_id)
    new_type = request.form.get('user_type')
    if user.id == current_user.id:
        flash('无法修改自己的角色', 'warning')
        return redirect(url_for('admin.users'))
    if new_type not in USER_TYPES:
        flash('用户角色无效', 'danger')
        return redirect(url_for('admin.users'))
    user.user_type = new_type
    db.session.commit()
    flash('用户角色已更新', 'success')
    return redirect(_redirect_back('admin.users'))


@admin_bp.route('/properties')
@admin_required
def properties():
    """房源管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    keyword = request.args.get('keyword', '').strip()

    query = Property.query
    if status in PROPERTY_STATUSES:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(db.or_(
            Property.title.ilike(f'%{keyword}%'),
            Property.address.ilike(f'%{keyword}%'),
            Property.province.ilike(f'%{keyword}%'),
            Property.city.ilike(f'%{keyword}%'),
            Property.district.ilike(f'%{keyword}%')
        ))

    properties_page = query.order_by(Property.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/properties.html', properties=properties_page, status=status, keyword=keyword)


@admin_bp.route('/property/<int:property_id>/status', methods=['POST'])
@admin_required
def update_property_status(property_id):
    """更新房源状态"""
    property_obj = Property.query.get_or_404(property_id)
    status = request.form.get('status')
    if status not in PROPERTY_STATUSES:
        flash('房源状态无效', 'danger')
        return redirect(url_for('admin.properties'))
    property_obj.status = status
    db.session.commit()
    flash('房源状态已更新', 'success')
    return redirect(_redirect_back('admin.properties'))


@admin_bp.route('/property/<int:property_id>/delete', methods=['POST'])
@admin_required
def delete_property(property_id):
    """删除房源"""
    property_obj = Property.query.get_or_404(property_id)
    db.session.delete(property_obj)
    db.session.commit()
    flash('房源已删除', 'success')
    return redirect(url_for('admin.properties'))


@admin_bp.route('/appointments')
@admin_required
def appointments():
    """预约管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = Appointment.query
    if status in APPOINTMENT_STATUSES:
        query = query.filter_by(status=status)
    appointments_page = query.order_by(Appointment.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/appointments.html', appointments=appointments_page, status=status)


@admin_bp.route('/appointment/<int:appointment_id>/status', methods=['POST'])
@admin_required
def update_appointment_status(appointment_id):
    """更新预约状态"""
    appointment = Appointment.query.get_or_404(appointment_id)
    status = request.form.get('status')
    if status not in APPOINTMENT_STATUSES:
        flash('预约状态无效', 'danger')
        return redirect(url_for('admin.appointments'))
    appointment.status = status
    appointment.updated_at = datetime.utcnow()
    _notify(appointment.tenant_id, f'管理员已将您对“{appointment.property.title}”的预约状态更新为：{_appointment_status_label(status)}。')
    _notify(appointment.landlord_id, f'管理员已将房源“{appointment.property.title}”的预约状态更新为：{_appointment_status_label(status)}。')
    db.session.commit()
    flash('预约状态已更新', 'success')
    return redirect(_redirect_back('admin.appointments'))


@admin_bp.route('/leases')
@admin_required
def leases():
    """合同管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = Lease.query
    if status in LEASE_STATUSES:
        query = query.filter_by(status=status)
    leases_page = query.order_by(Lease.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/leases.html', leases=leases_page, status=status)


@admin_bp.route('/lease/<int:lease_id>/status', methods=['POST'])
@admin_required
def update_lease_status(lease_id):
    """更新合同状态"""
    lease = Lease.query.get_or_404(lease_id)
    status = request.form.get('status')
    if status not in LEASE_STATUSES:
        flash('合同状态无效', 'danger')
        return redirect(url_for('admin.leases'))
    lease.status = status
    if status == 'active' and not lease.is_signed:
        lease.is_signed = True
        lease.sign_date = datetime.utcnow()
    if status in {'active', 'completed'}:
        lease.property.status = 'rented'
    elif status == 'terminated':
        lease.property.status = 'available'
    _notify(lease.tenant_id, f'管理员已将房源“{lease.property.title}”的合同状态更新为：{_lease_status_label(status)}。')
    _notify(lease.property.landlord_id, f'管理员已将房源“{lease.property.title}”的合同状态更新为：{_lease_status_label(status)}。')
    db.session.commit()
    flash('合同状态已更新', 'success')
    return redirect(_redirect_back('admin.leases'))


@admin_bp.route('/complaints')
@admin_required
def complaints():
    """投诉管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = Complaint.query
    if status in COMPLAINT_STATUSES:
        query = query.filter_by(status=status)
    complaints_page = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/complaints.html', complaints=complaints_page, status=status)


@admin_bp.route('/complaint/<int:complaint_id>/handle', methods=['POST'])
@admin_required
def handle_complaint(complaint_id):
    """处理投诉"""
    complaint = Complaint.query.get_or_404(complaint_id)
    status = request.form.get('status')
    admin_reply = (request.form.get('admin_reply') or '').strip()
    if status not in COMPLAINT_STATUSES:
        flash('投诉状态无效', 'danger')
        return redirect(url_for('admin.complaints'))
    if not admin_reply:
        flash('请输入处理说明', 'warning')
        return redirect(url_for('admin.complaints'))
    complaint.status = status
    complaint.admin_reply = admin_reply
    complaint.updated_at = datetime.utcnow()
    complaint.resolved_at = datetime.utcnow() if status == 'resolved' else None
    _notify(complaint.user_id, f'管理员已处理您的投诉“{complaint.title}”：{_complaint_status_label(status)}。\n处理说明：{admin_reply}')
    if complaint.target_id:
        _notify(complaint.target_id, f'管理员已处理与您相关的投诉“{complaint.title}”：{_complaint_status_label(status)}。')
    db.session.commit()
    flash('投诉已处理', 'success')
    return redirect(_redirect_back('admin.complaints'))


@admin_bp.route('/repairs')
@admin_required
def repairs():
    """维修管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = Repair.query
    if status in REPAIR_STATUSES:
        query = query.filter_by(status=status)
    repairs_page = query.order_by(Repair.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/repairs.html', repairs=repairs_page, status=status)


@admin_bp.route('/repair/<int:repair_id>/handle', methods=['POST'])
@admin_required
def handle_repair(repair_id):
    """处理维修"""
    repair = Repair.query.get_or_404(repair_id)
    status = request.form.get('status')
    reply = (request.form.get('reply') or '').strip()
    if status not in REPAIR_STATUSES:
        flash('维修状态无效', 'danger')
        return redirect(url_for('admin.repairs'))
    if not reply:
        flash('请输入处理说明', 'warning')
        return redirect(url_for('admin.repairs'))
    repair.status = status
    repair.landlord_reply = reply
    repair.updated_at = datetime.utcnow()
    repair.completed_at = datetime.utcnow() if status == 'completed' else None
    _notify(repair.tenant_id, f'管理员已处理您的维修申请“{repair.title}”：{_repair_status_label(status)}。\n处理说明：{reply}')
    _notify(repair.property.landlord_id, f'管理员已处理房源“{repair.property.title}”的维修申请“{repair.title}”：{_repair_status_label(status)}。')
    db.session.commit()
    flash('维修已处理', 'success')
    return redirect(_redirect_back('admin.repairs'))


@admin_bp.route('/news')
@admin_required
def news():
    """公告管理"""
    page = request.args.get('page', 1, type=int)
    published = request.args.get('published', '')
    query = News.query
    if published == '1':
        query = query.filter_by(is_published=True)
    elif published == '0':
        query = query.filter_by(is_published=False)
    news_page = query.order_by(News.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/news.html', news=news_page, published=published)


@admin_bp.route('/news/add', methods=['GET', 'POST'])
@admin_required
def add_news():
    """发布公告"""
    form = NewsForm()
    if form.validate_on_submit():
        news_item = News(
            landlord_id=current_user.id,
            title=form.title.data,
            content=form.content.data,
            news_type=form.news_type.data,
            is_published=True
        )
        db.session.add(news_item)
        db.session.commit()
        flash('公告已发布', 'success')
        return redirect(url_for('admin.news'))
    return render_template('admin/news_form.html', form=form, page_title='发布公告', submit_text='发布')


@admin_bp.route('/news/<int:news_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_news(news_id):
    """编辑公告"""
    news_item = News.query.get_or_404(news_id)
    form = NewsForm(obj=news_item)
    if form.validate_on_submit():
        news_item.title = form.title.data
        news_item.content = form.content.data
        news_item.news_type = form.news_type.data
        news_item.updated_at = datetime.utcnow()
        db.session.commit()
        flash('公告已更新', 'success')
        return redirect(url_for('admin.news'))
    return render_template('admin/news_form.html', form=form, news=news_item, page_title='编辑公告', submit_text='保存')


@admin_bp.route('/news/<int:news_id>/toggle', methods=['POST'])
@admin_required
def toggle_news(news_id):
    """发布/下架公告"""
    news_item = News.query.get_or_404(news_id)
    news_item.is_published = not news_item.is_published
    news_item.updated_at = datetime.utcnow()
    db.session.commit()
    flash('公告状态已更新', 'success')
    return redirect(_redirect_back('admin.news'))


@admin_bp.route('/news/<int:news_id>/delete', methods=['POST'])
@admin_required
def delete_news(news_id):
    """删除公告"""
    news_item = News.query.get_or_404(news_id)
    db.session.delete(news_item)
    db.session.commit()
    flash('公告已删除', 'success')
    return redirect(url_for('admin.news'))


@admin_bp.route('/payments')
@admin_required
def payments():
    """账单管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = Payment.query
    if status in PAYMENT_STATUSES:
        query = query.filter_by(status=status)
    payments_page = query.order_by(Payment.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('admin/payments.html', payments=payments_page, status=status)


@admin_bp.route('/payment/<int:payment_id>/status', methods=['POST'])
@admin_required
def update_payment_status(payment_id):
    """更新账单状态"""
    payment = Payment.query.get_or_404(payment_id)
    status = request.form.get('status')
    if status not in PAYMENT_STATUSES:
        flash('账单状态无效', 'danger')
        return redirect(url_for('admin.payments'))
    payment.status = status
    if status == 'completed':
        now = datetime.utcnow()
        payment.payment_date = payment.payment_date or now
        payment.confirmed_at = now
    elif status in {'pending', 'overdue'}:
        payment.confirmed_at = None
    payment.updated_at = datetime.utcnow()
    _notify(payment.lease.tenant_id, f'管理员已将账单 {payment.payment_period or payment.id} 状态更新为：{_payment_status_label(status)}。')
    _notify(payment.lease.property.landlord_id, f'管理员已将账单 {payment.payment_period or payment.id} 状态更新为：{_payment_status_label(status)}。')
    db.session.commit()
    flash('账单状态已更新', 'success')
    return redirect(_redirect_back('admin.payments'))


@admin_bp.route('/reports/system')
@admin_required
def system_reports():
    """系统报表"""
    today = datetime.utcnow().date()
    last_30_days = today - timedelta(days=30)
    total_rent = db.session.query(db.func.coalesce(db.func.sum(Lease.monthly_rent), 0)).filter(Lease.status == 'active').scalar()
    paid_amount = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).filter(Payment.status == 'completed').scalar()

    stats = {
        'new_users_30days': User.query.filter(User.created_at >= last_30_days).count(),
        'new_properties_30days': Property.query.filter(Property.created_at >= last_30_days).count(),
        'total_rent': total_rent,
        'paid_amount': paid_amount,
        'users': {
            'total': User.query.count(),
            'tenant': User.query.filter_by(user_type='tenant').count(),
            'landlord': User.query.filter_by(user_type='landlord').count(),
            'admin': User.query.filter_by(user_type='admin').count(),
            'disabled': User.query.filter_by(is_active=False).count(),
        },
        'property_stats': _count_by(Property, 'status', PROPERTY_STATUSES),
        'leases': _count_by(Lease, 'status', LEASE_STATUSES),
        'appointments': _count_by(Appointment, 'status', APPOINTMENT_STATUSES),
        'repairs': _count_by(Repair, 'status', REPAIR_STATUSES),
        'complaints': _count_by(Complaint, 'status', COMPLAINT_STATUSES),
        'payments': _count_by(Payment, 'status', PAYMENT_STATUSES),
    }
    return render_template('admin/reports.html', stats=stats)


@admin_bp.route('/reports/export')
@admin_required
def export_reports():
    """导出报表"""
    lines = [
        '系统数据报表',
        f'导出时间: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}',
        '',
        f'总用户数: {User.query.count()}',
        f'房东数: {User.query.filter_by(user_type="landlord").count()}',
        f'租客数: {User.query.filter_by(user_type="tenant").count()}',
        f'总房源数: {Property.query.count()}',
        f'可用房源: {Property.query.filter_by(status="available").count()}',
        f'活跃合同: {Lease.query.filter_by(status="active").count()}',
        f'待处理预约: {Appointment.query.filter_by(status="pending").count()}',
        f'待处理维修: {Repair.query.filter_by(status="pending").count()}',
        f'待处理投诉: {Complaint.query.filter_by(status="pending").count()}',
    ]
    response = make_response('\n'.join(lines))
    response.headers['Content-Disposition'] = 'attachment; filename="system_report.txt"'
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response


def _redirect_back(default_endpoint):
    return request.referrer or url_for(default_endpoint)


def _notify(receiver_id, content):
    if receiver_id and receiver_id != current_user.id:
        db.session.add(Message(sender_id=current_user.id, receiver_id=receiver_id, content=content, message_type='notification'))


def _build_conversations(user_id):
    messages = Message.query.filter(
        db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    ).order_by(Message.created_at.desc()).all()

    conversations = {}
    for message in messages:
        other_user = message.sender if message.sender_id != user_id else message.receiver
        if not (other_user.is_landlord() or other_user.is_tenant()):
            continue
        if other_user.id not in conversations:
            conversations[other_user.id] = {
                'user': other_user,
                'last_message': message,
                'unread_count': 0,
                'url': url_for('admin.conversation', user_id=other_user.id),
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
        return {'action_url': url_for('admin.payments'), 'action_label': '查看账单'}
    if '预约' in content:
        return {'action_url': url_for('admin.appointments'), 'action_label': '查看预约'}
    if '维修' in content:
        return {'action_url': url_for('admin.repairs'), 'action_label': '查看维修'}
    if '投诉' in content:
        return {'action_url': url_for('admin.complaints'), 'action_label': '查看投诉'}
    if '合同' in content or '租赁' in content:
        return {'action_url': url_for('admin.leases'), 'action_label': '查看合同'}
    return {'action_url': None, 'action_label': None}


def _count_by(model, field, values):
    return {value: model.query.filter(getattr(model, field) == value).count() for value in values} | {'total': model.query.count()}


def _appointment_status_label(status):
    return {'pending': '待确认', 'confirmed': '已确认', 'cancelled': '已取消', 'completed': '已完成'}.get(status, status)


def _lease_status_label(status):
    return {'pending': '待签署', 'active': '生效中', 'completed': '已完成', 'terminated': '已终止'}.get(status, status)


def _complaint_status_label(status):
    return {'pending': '待处理', 'under_review': '处理中', 'resolved': '已解决', 'rejected': '已驳回'}.get(status, status)


def _repair_status_label(status):
    return {'pending': '待处理', 'in_progress': '处理中', 'completed': '已完成', 'rejected': '已驳回'}.get(status, status)


def _payment_status_label(status):
    return {'pending': '待支付', 'submitted': '待房东确认', 'completed': '已完成', 'overdue': '已逾期'}.get(status, status)
