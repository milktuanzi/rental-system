"""
管理员视图 - 用户管理、系统监控、报表统计
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from main import db
from main.models.user import User
from main.models.property import Property
from main.models.lease import Lease
from main.models.complaint import Complaint
from main.models.repair import Repair

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


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
    # 统计数据
    total_users = User.query.count()
    total_landlords = User.query.filter_by(user_type='landlord').count()
    total_tenants = User.query.filter_by(user_type='tenant').count()
    total_properties = Property.query.count()
    active_leases = Lease.query.filter_by(status='active').count()
    pending_complaints = Complaint.query.filter_by(status='pending').count()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_landlords=total_landlords,
        total_tenants=total_tenants,
        total_properties=total_properties,
        active_leases=active_leases,
        pending_complaints=pending_complaints
    )


@admin_bp.route('/users')
@admin_required
def users():
    """用户管理"""
    page = request.args.get('page', 1, type=int)
    user_type = request.args.get('type', '')

    query = User.query
    if user_type:
        query = query.filter_by(user_type=user_type)

    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15)

    return render_template('admin/users.html', users=users, user_type=user_type)


@admin_bp.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """切换用户状态"""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('无法修改自己的状态', 'warning')
        return redirect(url_for('admin.users'))

    user.is_active = not user.is_active
    db.session.commit()

    status = '激活' if user.is_active else '禁用'
    flash(f'用户已{status}', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/properties')
@admin_required
def properties():
    """房源管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Property.query
    if status:
        query = query.filter_by(status=status)

    properties = query.order_by(Property.created_at.desc()).paginate(page=page, per_page=15)

    return render_template('admin/properties.html', properties=properties, status=status)


@admin_bp.route('/property/<int:property_id>/delete', methods=['POST'])
@admin_required
def delete_property(property_id):
    """删除房源"""
    property_obj = Property.query.get_or_404(property_id)

    db.session.delete(property_obj)
    db.session.commit()

    flash('房源已删除', 'success')
    return redirect(url_for('admin.properties'))


@admin_bp.route('/complaints')
@admin_required
def complaints():
    """投诉管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Complaint.query
    if status:
        query = query.filter_by(status=status)

    complaints = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=15)

    return render_template('admin/complaints.html', complaints=complaints, status=status)


@admin_bp.route('/complaint/<int:complaint_id>/handle', methods=['POST'])
@admin_required
def handle_complaint(complaint_id):
    """处理投诉"""
    complaint = Complaint.query.get_or_404(complaint_id)

    status = request.form.get('status')
    admin_reply = request.form.get('admin_reply')

    complaint.status = status
    complaint.admin_reply = admin_reply
    if status == 'resolved':
        from datetime import datetime
        complaint.resolved_at = datetime.utcnow()

    db.session.commit()
    flash('投诉已处理', 'success')
    return redirect(url_for('admin.complaints'))


@admin_bp.route('/repairs')
@admin_required
def repairs():
    """维修管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')

    query = Repair.query
    if status:
        query = query.filter_by(status=status)

    repairs = query.order_by(Repair.created_at.desc()).paginate(page=page, per_page=15)

    return render_template('admin/repairs.html', repairs=repairs, status=status)


@admin_bp.route('/reports/system')
@admin_required
def system_reports():
    """系统报表"""
    # 用户增长统计
    from datetime import datetime, timedelta

    today = datetime.utcnow().date()
    last_30_days = today - timedelta(days=30)

    new_users_30days = User.query.filter(
        User.created_at >= last_30_days
    ).count()

    # 房源统计
    property_stats = {
        'total': Property.query.count(),
        'available': Property.query.filter_by(status='available').count(),
        'rented': Property.query.filter_by(status='rented').count(),
        'maintenance': Property.query.filter_by(status='maintenance').count(),
    }

    # 租赁统计
    lease_stats = {
        'active': Lease.query.filter_by(status='active').count(),
        'pending': Lease.query.filter_by(status='pending').count(),
        'completed': Lease.query.filter_by(status='completed').count(),
    }

    # 投诉统计
    complaint_stats = {
        'pending': Complaint.query.filter_by(status='pending').count(),
        'under_review': Complaint.query.filter_by(status='under_review').count(),
        'resolved': Complaint.query.filter_by(status='resolved').count(),
    }

    return render_template(
        'admin/reports.html',
        new_users_30days=new_users_30days,
        property_stats=property_stats,
        lease_stats=lease_stats,
        complaint_stats=complaint_stats
    )


@admin_bp.route('/reports/export')
@admin_required
def export_reports():
    """导出报表"""
    from flask import make_response
    from datetime import datetime

    # 获取所有数据
    users = User.query.all()
    properties = Property.query.all()
    leases = Lease.query.all()

    # 构建CSV内容
    csv_content = "系统数据报表\n"
    csv_content += f"导出时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    csv_content += "用户统计\n"
    csv_content += f"总用户数: {len(users)}\n"
    csv_content += f"房东数: {sum(1 for u in users if u.is_landlord())}\n"
    csv_content += f"租客数: {sum(1 for u in users if u.is_tenant())}\n\n"

    csv_content += "房源统计\n"
    csv_content += f"总房源数: {len(properties)}\n"
    csv_content += f"可用房源: {sum(1 for p in properties if p.status == 'available')}\n"
    csv_content += f"已出租: {sum(1 for p in properties if p.status == 'rented')}\n\n"

    csv_content += "租赁统计\n"
    csv_content += f"总租赁数: {len(leases)}\n"
    csv_content += f"活跃租赁: {sum(1 for l in leases if l.status == 'active')}\n"

    response = make_response(csv_content)
    response.headers['Content-Disposition'] = 'attachment; filename="system_report.txt"'
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'

    return response

