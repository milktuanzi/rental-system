"""
租客视图 - 房源搜索、租赁管理、维修投诉、消息
"""
import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from main import db
from main.models.user import User
from main.models.property import Property
from main.models.lease import Lease
from main.models.message import Message
from main.models.repair import Repair
from main.models.complaint import Complaint
from main.models.payment import Payment
from main.models.appointment import Appointment
from main.forms.lease import AppointmentForm, PaymentSubmitForm
from main.forms.message import MessageForm
from main.forms.repair import RepairForm, ComplaintForm

tenant_bp = Blueprint('tenant', __name__, url_prefix='/tenant')


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def get_payment_upload_folder():
    """获取账单图片上传目录。"""
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'payments')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder


def save_payment_image(file, prefix='tenant_proof'):
    """保存租客支付凭证并返回可访问路径。"""
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


def tenant_required(f):
    """租客权限检查装饰器"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_tenant():
            flash('需要租客权限', 'danger')
            return redirect(url_for('common.index'))
        return f(*args, **kwargs)
    return decorated_function


@tenant_bp.route('/dashboard')
@tenant_required
def dashboard():
    """租客仪表板"""
    # 统计数据
    active_leases = Lease.query.filter_by(
        tenant_id=current_user.id,
        status='active'
    ).count()
    pending_repairs = Repair.query.filter_by(
        tenant_id=current_user.id,
        status='pending'
    ).count()
    unread_messages = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()

    # 获取最近的租赁
    recent_leases = Lease.query.filter_by(
        tenant_id=current_user.id
    ).order_by(Lease.created_at.desc()).limit(3).all()

    # 获取预约统计和最近预约
    pending_appointments = Appointment.query.filter_by(
        tenant_id=current_user.id,
        status='pending'
    ).count()
    recent_appointments = Appointment.query.filter_by(
        tenant_id=current_user.id
    ).order_by(Appointment.created_at.desc()).limit(5).all()

    return render_template(
        'tenant/dashboard.html',
        active_leases=active_leases,
        pending_repairs=pending_repairs,
        unread_messages=unread_messages,
        recent_leases=recent_leases,
        pending_appointments=pending_appointments,
        recent_appointments=recent_appointments
    )


@tenant_bp.route('/my-leases')
@tenant_required
def my_leases():
    """我的租赁列表"""
    page = request.args.get('page', 1, type=int)
    leases = Lease.query.filter_by(tenant_id=current_user.id).order_by(
        Lease.created_at.desc()
    ).paginate(page=page, per_page=10)

    return render_template('tenant/my_leases.html', leases=leases)


@tenant_bp.route('/appointments')
@tenant_required
def my_appointments():
    """我的预约列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Appointment.query.filter_by(tenant_id=current_user.id)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    appointments = query.order_by(Appointment.created_at.desc()).paginate(page=page, per_page=10)

    return render_template('tenant/appointments.html', appointments=appointments, status=status)


@tenant_bp.route('/lease/<int:lease_id>/detail')
@tenant_required
def lease_detail(lease_id):
    """租赁详情"""
    lease = Lease.query.get_or_404(lease_id)

    if lease.tenant_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('tenant.my_leases'))

    # 获取该租赁的支付记录
    payments = Payment.query.filter_by(lease_id=lease.id).order_by(
        Payment.created_at.desc()
    ).all()

    return render_template('tenant/lease_detail.html', lease=lease, payments=payments)


@tenant_bp.route('/payments')
@tenant_required
def payments():
    """租客账单列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    query = Payment.query.join(Lease).filter(Lease.tenant_id == current_user.id)
    if status in {'pending', 'submitted', 'completed', 'overdue'}:
        query = query.filter(Payment.status == status)
    payments_page = query.order_by(Payment.created_at.desc()).paginate(page=page, per_page=12)
    return render_template('tenant/payments.html', payments=payments_page, status=status)


@tenant_bp.route('/payment/<int:payment_id>/pay', methods=['GET', 'POST'])
@tenant_required
def pay_payment(payment_id):
    """租客提交账单支付凭证"""
    payment = Payment.query.get_or_404(payment_id)
    if payment.lease.tenant_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('tenant.payments'))
    if payment.status not in {'pending', 'overdue'}:
        flash('当前账单不可重复支付', 'warning')
        return redirect(url_for('tenant.payments'))

    form = PaymentSubmitForm()
    if form.validate_on_submit():
        try:
            proof = save_payment_image(request.files.get('tenant_payment_proof'), 'tenant_proof')
        except ValueError as exc:
            flash(str(exc), 'danger')
            return render_template('tenant/pay_payment.html', payment=payment, form=form)

        if not proof:
            flash('请上传支付凭证图片', 'warning')
            return render_template('tenant/pay_payment.html', payment=payment, form=form)

        payment.status = 'submitted'
        payment.payment_method = form.payment_method.data or '扫码支付'
        payment.transaction_id = form.transaction_id.data or None
        payment.tenant_payment_proof = proof
        payment.payment_date = datetime.utcnow()
        payment.updated_at = datetime.utcnow()
        db.session.add(Message(
            sender_id=current_user.id,
            receiver_id=payment.lease.property.landlord_id,
            content=f"租客已提交账单 {payment.payment_period or payment.id} 的支付凭证，金额 ¥{payment.amount:.2f}，请确认收款。",
            message_type='notification'
        ))
        db.session.commit()
        flash('支付凭证已提交，等待房东确认', 'success')
        return redirect(url_for('tenant.payments'))

    return render_template('tenant/pay_payment.html', payment=payment, form=form)


@tenant_bp.route('/lease/<int:lease_id>/sign', methods=['POST'])
@tenant_required
def sign_lease(lease_id):
    """签署租赁合同"""
    lease = Lease.query.get_or_404(lease_id)

    if lease.tenant_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('tenant.my_leases'))

    if lease.is_signed:
        flash('合同已签署', 'info')
        return redirect(url_for('tenant.lease_detail', lease_id=lease_id))

    if lease.status != 'pending':
        flash('当前合同状态不可签署', 'warning')
        return redirect(url_for('tenant.lease_detail', lease_id=lease_id))

    lease.is_signed = True
    lease.sign_date = datetime.utcnow()
    lease.status = 'active'

    # 更新房源状态为已租赁
    lease.property.status = 'rented'

    message = Message(
        sender_id=current_user.id,
        receiver_id=lease.property.landlord_id,
        content=f"租客 {current_user.username} 已签署房源“{lease.property.title}”的租赁合同，合同已生效。",
        message_type='notification'
    )
    db.session.add(message)

    db.session.commit()
    flash('合同签署成功！', 'success')
    return redirect(url_for('tenant.lease_detail', lease_id=lease_id))


@tenant_bp.route('/property/<int:property_id>/appointment', methods=['GET', 'POST'])
@tenant_required
def appointment(property_id):
    """预约看房"""
    property_obj = Property.query.get_or_404(property_id)

    if not property_obj.is_available():
        flash('该房源暂不可预约', 'warning')
        return redirect(url_for('common.property_detail', property_id=property_id))

    form = AppointmentForm()
    
    # 调试日志
    if request.method == 'POST':
        print(f"[DEBUG] 收到预约请求，method: {request.method}")
        print(f"[DEBUG] form data: {request.form}")
        print(f"[DEBUG] preferred_time field value: {request.form.get('preferred_time', 'NOT FOUND')}")
        print(f"[DEBUG] form.validate_on_submit(): {form.validate_on_submit()}")
        if form.errors:
            print(f"[DEBUG] 表单验证错误: {form.errors}")
    
    if form.validate_on_submit():
        try:
            print(f"[DEBUG] 开始创建预约记录...")
            # 创建预约记录
            appointment = Appointment(
                property_id=property_id,
                tenant_id=current_user.id,
                landlord_id=property_obj.landlord_id,
                preferred_time=form.preferred_time.data,
                message=form.message.data,
                status='pending'
            )
            db.session.add(appointment)
            print(f"[DEBUG] 预约记录已添加到session")

            # 创建消息通知房东
            message = Message(
                sender_id=current_user.id,
                receiver_id=property_obj.landlord_id,
                content=f"预约看房时间: {form.preferred_time.data.strftime('%Y-%m-%d %H:%M')}\n备注: {form.message.data}",
                message_type='inquiry'
            )
            db.session.add(message)
            print(f"[DEBUG] 消息记录已添加到session")
            
            # 提交事务
            db.session.commit()
            print(f"[DEBUG] 数据库事务提交成功")
            
            # 验证数据是否正确写入
            check_appointment = Appointment.query.filter_by(id=appointment.id).first()
            if check_appointment:
                print(f"[DEBUG] 验证成功: 预约记录已保存到数据库，ID={check_appointment.id}, status={check_appointment.status}")
            else:
                print(f"[DEBUG] 验证失败: 预约记录未保存到数据库")

            flash('预约成功！房东将尽快与您联系。', 'success')
            return redirect(url_for('tenant.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] 预约创建失败: {str(e)}")
            flash('预约失败，请重试', 'danger')
            return redirect(url_for('tenant.appointment', property_id=property_id))

    return render_template('tenant/appointment.html', property=property_obj, form=form)


@tenant_bp.route('/repairs')
@tenant_required
def repairs():
    """我的维修申请"""
    page = request.args.get('page', 1, type=int)
    repairs = Repair.query.filter_by(tenant_id=current_user.id).order_by(
        Repair.created_at.desc()
    ).paginate(page=page, per_page=10)

    return render_template('tenant/repairs.html', repairs=repairs)


@tenant_bp.route('/repair/add', methods=['GET', 'POST'])
@tenant_required
def add_repair():
    """提交维修申请"""
    # 获取租客当前的活跃租赁
    active_leases = Lease.query.filter_by(
        tenant_id=current_user.id,
        status='active'
    ).all()

    if not active_leases:
        flash('您没有活跃的租赁合同', 'warning')
        return redirect(url_for('tenant.repairs'))

    form = RepairForm()
    if form.validate_on_submit():
        property_id = request.form.get('property_id', type=int)

        # 验证租客是否在该房源有活跃租赁
        lease = Lease.query.filter_by(
            property_id=property_id,
            tenant_id=current_user.id,
            status='active'
        ).first()

        if not lease:
            flash('权限不足', 'danger')
            return redirect(url_for('tenant.repairs'))

        repair = Repair(
            property_id=property_id,
            tenant_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data
        )
        db.session.add(repair)
        db.session.add(Message(
            sender_id=current_user.id,
            receiver_id=lease.property.landlord_id,
            content=f"租客 {current_user.username} 提交了维修申请“{form.title.data}”，请在维修管理中处理。",
            message_type='notification'
        ))
        db.session.commit()

        flash('维修申请已提交', 'success')
        return redirect(url_for('tenant.repairs'))

    return render_template('tenant/add_repair.html', form=form, active_leases=active_leases)


@tenant_bp.route('/complaints')
@tenant_required
def complaints():
    """我的投诉"""
    page = request.args.get('page', 1, type=int)
    complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(
        Complaint.created_at.desc()
    ).paginate(page=page, per_page=10)

    return render_template('tenant/complaints.html', complaints=complaints)


@tenant_bp.route('/complaint/add', methods=['GET', 'POST'])
@tenant_required
def add_complaint():
    """提交投诉"""
    active_leases = Lease.query.filter_by(
        tenant_id=current_user.id,
        status='active'
    ).all()

    form = ComplaintForm()
    if form.validate_on_submit():
        property_id = request.form.get('property_id', type=int)
        lease = Lease.query.filter_by(
            property_id=property_id,
            tenant_id=current_user.id,
            status='active'
        ).first()

        if not lease:
            flash('请选择您当前租赁中的房源', 'warning')
            return redirect(url_for('tenant.add_complaint'))

        complaint = Complaint(
            user_id=current_user.id,
            target_id=lease.property.landlord_id,
            property_id=lease.property_id,
            title=form.title.data,
            content=form.content.data,
            complaint_type=form.complaint_type.data
        )
        db.session.add(complaint)
        db.session.add(Message(
            sender_id=current_user.id,
            receiver_id=lease.property.landlord_id,
            content=f"租客 {current_user.username} 提交了投诉“{form.title.data}”，请在投诉管理中处理。",
            message_type='notification'
        ))
        db.session.commit()

        flash('投诉已提交，房东将尽快处理', 'success')
        return redirect(url_for('tenant.complaints'))

    return render_template('tenant/add_complaint.html', form=form, active_leases=active_leases)


@tenant_bp.route('/messages')
@tenant_required
def messages():
    """兼容旧消息列表入口，进入会话中心。"""
    return redirect(url_for('tenant.conversation_home'))


@tenant_bp.route('/conversation/')
@tenant_required
def conversation_home():
    """租客会话中心：未选中联系人时只展示会话列表。"""
    return render_template(
        'tenant/conversation.html',
        form=MessageForm(),
        other_user=None,
        conversations=_build_conversations(current_user.id),
        messages=[]
    )


@tenant_bp.route('/message/<int:message_id>')
@tenant_required
def message_detail(message_id):
    """兼容旧消息详情链接，跳转到对应会话"""
    message = Message.query.get_or_404(message_id)

    if message.receiver_id != current_user.id and message.sender_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('tenant.conversation_home'))

    other_user_id = message.sender_id if message.sender_id != current_user.id else message.receiver_id
    return redirect(url_for('tenant.conversation', user_id=other_user_id))


@tenant_bp.route('/conversation/<int:user_id>', methods=['GET', 'POST'])
@tenant_required
def conversation(user_id):
    """租客与房东/管理员的对话"""
    other_user = User.query.get_or_404(user_id)

    if not (other_user.is_landlord() or other_user.is_admin()):
        flash('只能与房东或管理员进行对话', 'danger')
        return redirect(url_for('tenant.conversation_home'))

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
        return redirect(url_for('tenant.conversation', user_id=other_user.id))

    if form.validate_on_submit() and other_user.is_admin():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': '系统通知无需回复'}), 400
        flash('系统通知无需回复', 'info')
        return redirect(url_for('tenant.conversation', user_id=other_user.id))

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
        message.mark_as_read()
    if unread_messages:
        db.session.commit()

    return render_template(
        'tenant/conversation.html',
        form=form,
        other_user=other_user,
        conversations=_build_conversations(current_user.id),
        messages=_serialize_messages(conversation_messages)
    )


@tenant_bp.route('/conversation/<int:user_id>/messages')
@tenant_required
def conversation_messages(user_id):
    """获取租客与房东/管理员的最新对话消息。"""
    other_user = User.query.get_or_404(user_id)

    if not (other_user.is_landlord() or other_user.is_admin()):
        return jsonify({'success': False, 'error': '只能与房东或管理员进行对话'}), 403

    messages = _conversation_query(current_user.id, other_user.id).all()
    unread_messages = [
        message for message in messages
        if message.receiver_id == current_user.id and not message.is_read
    ]
    for message in unread_messages:
        message.mark_as_read()
    if unread_messages:
        db.session.commit()

    return jsonify({'success': True, 'messages': _serialize_messages(messages)})


@tenant_bp.route('/message/<int:message_id>/read')
@tenant_required
def mark_message_read(message_id):
    """标记消息为已读"""
    message = Message.query.get_or_404(message_id)

    if message.receiver_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('tenant.conversation_home'))

    if not message.is_read:
        message.mark_as_read()
        db.session.commit()

    flash('消息已标记为已读', 'success')
    return redirect(url_for('tenant.conversation_home'))


@tenant_bp.route('/message/<int:receiver_id>/send', methods=['GET', 'POST'])
@tenant_required
def send_message(receiver_id):
    """发送消息"""
    receiver = User.query.get_or_404(receiver_id)

    if receiver.id == current_user.id:
        flash('不能给自己发送消息', 'warning')
        return redirect(url_for('tenant.conversation_home'))

    if not receiver.is_landlord():
        flash('只能联系房东用户', 'danger')
        return redirect(url_for('tenant.conversation_home'))

    form = MessageForm()
    if request.method == 'GET':
        return redirect(url_for('tenant.conversation', user_id=receiver.id))

    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver.id,
            content=form.content.data,
            message_type='message'
        )
        db.session.add(message)
        db.session.commit()

        flash('消息已发送', 'success')
        return redirect(url_for('tenant.conversation', user_id=receiver.id))

    return render_template('tenant/send_message.html', form=form, receiver=receiver)


def _build_conversations(user_id):
    messages = Message.query.filter(
        db.or_(Message.sender_id == user_id, Message.receiver_id == user_id)
    ).order_by(Message.created_at.desc()).all()

    conversations = {}
    for message in messages:
        other_user = message.sender if message.sender_id != user_id else message.receiver
        if not (other_user.is_landlord() or other_user.is_admin()):
            continue
        if other_user.id not in conversations:
            conversation_url = url_for('tenant.conversation', user_id=other_user.id)
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
        return {'action_url': url_for('tenant.payments'), 'action_label': '查看账单'}
    if '合同' in content or '租赁' in content:
        return {'action_url': url_for('tenant.my_leases'), 'action_label': '查看合同'}
    if '预约' in content:
        return {'action_url': url_for('tenant.my_appointments'), 'action_label': '查看预约'}
    if '维修' in content:
        return {'action_url': url_for('tenant.repairs'), 'action_label': '查看维修'}
    if '投诉' in content:
        return {'action_url': url_for('tenant.complaints'), 'action_label': '查看投诉'}
    return {'action_url': None, 'action_label': None}
