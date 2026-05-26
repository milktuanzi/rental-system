"""
认证视图 - 登录、注册、登出
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from main import db
from main.models.user import User
from main.forms.auth import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('common.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('账号已禁用', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_has_allowed_host_and_scheme(next_page):
            next_page = url_for('common.index')
        return redirect(next_page)

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('common.index'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone=form.phone.data,
            user_type=form.user_type.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('注册成功！请登录。', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    flash('已成功登出', 'success')
    return redirect(url_for('common.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """用户信息更改"""
    from main.forms.auth import ProfileForm, ChangePasswordForm
    
    # 获取当前用户信息
    user = User.query.get_or_404(current_user.id)
    
    # 创建表单，传入原始值用于验证
    profile_form = ProfileForm(
        original_username=user.username,
        original_email=user.email,
        original_phone=user.phone or ''
    )
    password_form = ChangePasswordForm(user=user)
    
    if request.method == 'GET':
        # 初始化表单数据
        profile_form.username.data = user.username
        profile_form.email.data = user.email
        profile_form.phone.data = user.phone or ''
        profile_form.bio.data = user.bio or ''
    
    return render_template('auth/profile.html', profile_form=profile_form, password_form=password_form, user=user)


@auth_bp.route('/api/profile/update', methods=['POST'])
@login_required
def api_update_profile():
    """异步更新用户信息API"""
    from main.forms.auth import ProfileForm
    
    try:
        user = User.query.get_or_404(current_user.id)
        
        # 创建表单，传入原始值用于验证
        form = ProfileForm(
            original_username=user.username,
            original_email=user.email,
            original_phone=user.phone or '',
            data=request.form
        )
        
        if form.validate():
            # 更新用户信息
            user.username = form.username.data
            user.email = form.email.data
            user.phone = form.phone.data or None
            user.bio = form.bio.data or None
            
            db.session.commit()
            
            print(f"[LOG] 用户 {user.id} ({user.username}) 更新个人信息成功")
            return {'success': True, 'message': '用户信息更新成功！'}
        else:
            # 返回表单验证错误
            errors = {field: ', '.join(messages) for field, messages in form.errors.items()}
            return {'success': False, 'message': '表单验证失败', 'errors': errors}, 400
            
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] 用户 {current_user.id} 更新个人信息失败: {str(e)}")
        return {'success': False, 'message': '用户信息更新失败，请重试'}, 500


@auth_bp.route('/api/profile/change-password', methods=['POST'])
@login_required
def api_change_password():
    """异步修改密码API"""
    from main.forms.auth import ChangePasswordForm
    from datetime import datetime
    
    try:
        user = User.query.get_or_404(current_user.id)
        
        # 记录当前密码哈希（用于错误时回滚）
        original_password_hash = user.password_hash
        original_updated_at = user.updated_at
        
        # 创建表单
        form = ChangePasswordForm(user=user, data=request.form)
        
        if form.validate():
            # 验证通过，开始密码更新
            print(f"[LOG] 用户 {user.id} ({user.username}) 开始密码修改流程")
            
            # 执行密码更新（使用set_password进行安全加密）
            user.set_password(form.new_password.data)
            
            # 提交数据库事务
            db.session.commit()
            
            print(f"[LOG] 用户 {user.id} ({user.username}) 密码修改成功")
            print(f"[LOG] 新密码哈希: {user.password_hash[:50]}...")
            
            # 返回成功响应
            return {
                'success': True, 
                'message': '密码修改成功！请使用新密码重新登录',
                'autoLogout': True
            }
        else:
            # 表单验证失败
            errors = {field: ', '.join(messages) for field, messages in form.errors.items()}
            print(f"[DEBUG] 密码修改表单验证失败: {errors}")
            return {'success': False, 'message': '表单验证失败', 'errors': errors}, 400
            
    except Exception as e:
        # 发生异常，回滚事务
        db.session.rollback()
        print(f"[ERROR] 用户 {current_user.id} 密码修改失败: {str(e)}")
        import traceback
        print(f"[ERROR] 异常详情: {traceback.format_exc()}")
        return {'success': False, 'message': '密码修改失败，请稍后重试。如果问题持续存在，请联系管理员。'}, 500


def url_has_allowed_host_and_scheme(url, allowed_hosts=None):
    """验证重定向URL是否安全"""
    if allowed_hosts is None:
        allowed_hosts = ['localhost', '127.0.0.1']
    return url.startswith('/') or url.startswith('http')

