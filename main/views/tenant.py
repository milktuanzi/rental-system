"""
租客视图 - 房源搜索、租赁管理、维修投诉、消息
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from main import db
from main.models.property import Property
from main.models.lease import Lease
from main.models.message import Message
from main.models.repair import Repair
from main.models.complaint import Complaint
from main.models.payment import Payment
from main.models.appointment import Appointment
from main.forms.lease import AppointmentForm
from main.forms.message import MessageForm
from main.forms.repair import RepairForm, ComplaintForm

tenant_bp = Blueprint('tenant', __name__, url_prefix='/tenant')


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

    lease.is_signed = True
    lease.sign_date = datetime.utcnow()
    lease.status = 'active'

    # 更新房源状态为已租赁
    lease.property.status = 'rented'

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
    form = ComplaintForm()
    if form.validate_on_submit():
        complaint = Complaint(
            user_id=current_user.id,
            title=form.title.data,
            content=form.content.data,
            complaint_type=form.complaint_type.data
        )
        db.session.add(complaint)
        db.session.commit()

        flash('投诉已提交，管理员将在24小时内处理', 'success')
        return redirect(url_for('tenant.complaints'))

    return render_template('tenant/add_complaint.html', form=form)


@tenant_bp.route('/messages')
@tenant_required
def messages():
    """我的消息"""
    page = request.args.get('page', 1, type=int)
    messages = Message.query.filter_by(receiver_id=current_user.id).order_by(
        Message.created_at.desc()
    ).paginate(page=page, per_page=15)

    return render_template('tenant/messages.html', messages=messages)


@tenant_bp.route('/message/<int:message_id>')
@tenant_required
def message_detail(message_id):
    """消息详情"""
    message = Message.query.get_or_404(message_id)

    if message.receiver_id != current_user.id:
        flash('权限不足', 'danger')
        return redirect(url_for('tenant.messages'))

    message.mark_as_read()
    db.session.commit()

    return render_template('tenant/message_detail.html', message=message)


@tenant_bp.route('/message/<int:receiver_id>/send', methods=['GET', 'POST'])
@tenant_required
def send_message(receiver_id):
    """发送消息"""
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=form.content.data,
            message_type='message'
        )
        db.session.add(message)
        db.session.commit()

        flash('消息已发送', 'success')
        return redirect(url_for('tenant.messages'))

    return render_template('tenant/send_message.html', form=form, receiver_id=receiver_id)

