"""
预约功能数据库更新逻辑测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from main import create_app, db
from main.models.user import User
from main.models.property import Property
from main.models.appointment import Appointment
from main.models.message import Message

# 创建测试应用
app = create_app('testing')
app.app_context().push()

# 创建测试数据
def setup_test_data():
    print("[TEST] 设置测试数据...")
    
    # 创建测试房东
    landlord = User(
        username='test_landlord',
        email='landlord@test.com',
        user_type='landlord',
        phone='13800138001'
    )
    landlord.set_password('password123')
    db.session.add(landlord)
    
    # 创建测试租客
    tenant = User(
        username='test_tenant',
        email='tenant@test.com',
        user_type='tenant',
        phone='13800138002'
    )
    tenant.set_password('password123')
    db.session.add(tenant)
    
    # 创建测试房源
    property_obj = Property(
        title='测试房源',
        address='测试地址',
        price=2000,
        deposit=4000,
        area=80,
        rooms=2,
        halls=1,
        bathrooms=1,
        landlord_id=1,
        status='available',
        description='测试房源描述'
    )
    db.session.add(property_obj)
    
    db.session.commit()
    print("[TEST] 测试数据创建完成")
    return landlord, tenant, property_obj

# 测试预约创建流程
def test_appointment_creation():
    print("\n[TEST] 开始测试预约创建流程...")
    
    try:
        # 获取测试数据
        tenant = User.query.filter_by(username='test_tenant').first()
        property_obj = Property.query.filter_by(title='测试房源').first()
        
        if not tenant or not property_obj:
            print("[ERROR] 测试数据不存在，请先运行setup_test_data")
            return False
        
        print(f"[TEST] 租客信息: ID={tenant.id}, username={tenant.username}")
        print(f"[TEST] 房源信息: ID={property_obj.id}, title={property_obj.title}, landlord_id={property_obj.landlord_id}")
        
        # 创建预约记录
        print("[TEST] 创建预约记录...")
        appointment_time = datetime.now() + timedelta(days=1)
        
        appointment = Appointment(
            property_id=property_obj.id,
            tenant_id=tenant.id,
            landlord_id=property_obj.landlord_id,
            preferred_time=appointment_time,
            message='测试预约留言',
            status='pending'
        )
        db.session.add(appointment)
        print("[TEST] 预约记录已添加到session")
        
        # 创建消息通知
        print("[TEST] 创建消息通知...")
        message = Message(
            sender_id=tenant.id,
            receiver_id=property_obj.landlord_id,
            content=f"预约看房时间: {appointment_time.strftime('%Y-%m-%d %H:%M')}\n备注: 测试预约留言",
            message_type='inquiry'
        )
        db.session.add(message)
        print("[TEST] 消息记录已添加到session")
        
        # 提交事务
        print("[TEST] 提交数据库事务...")
        db.session.commit()
        print("[TEST] 数据库事务提交成功")
        
        # 验证数据是否正确写入
        print("[TEST] 验证数据库写入...")
        check_appointment = Appointment.query.filter_by(id=appointment.id).first()
        
        if check_appointment:
            print(f"[SUCCESS] 预约记录验证成功:")
            print(f"  - ID: {check_appointment.id}")
            print(f"  - property_id: {check_appointment.property_id}")
            print(f"  - tenant_id: {check_appointment.tenant_id}")
            print(f"  - landlord_id: {check_appointment.landlord_id}")
            print(f"  - preferred_time: {check_appointment.preferred_time}")
            print(f"  - status: {check_appointment.status}")
            print(f"  - created_at: {check_appointment.created_at}")
        else:
            print("[ERROR] 预约记录未保存到数据库")
            return False
        
        # 验证消息记录
        check_message = Message.query.filter_by(sender_id=tenant.id).first()
        if check_message:
            print(f"[SUCCESS] 消息记录验证成功:")
            print(f"  - ID: {check_message.id}")
            print(f"  - sender_id: {check_message.sender_id}")
            print(f"  - receiver_id: {check_message.receiver_id}")
            print(f"  - content: {check_message.content}")
        else:
            print("[ERROR] 消息记录未保存到数据库")
            return False
        
        # 验证关联关系
        print("[TEST] 验证关联关系...")
        if check_appointment.property:
            print(f"[SUCCESS] 预约与房源关联正常: {check_appointment.property.title}")
        else:
            print("[ERROR] 预约与房源关联失败")
            return False
        
        if check_appointment.tenant:
            print(f"[SUCCESS] 预约与租客关联正常: {check_appointment.tenant.username}")
        else:
            print("[ERROR] 预约与租客关联失败")
            return False
        
        print("\n[TEST] 所有测试通过！")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# 测试预约状态更新
def test_appointment_status_update():
    print("\n[TEST] 开始测试预约状态更新...")
    
    try:
        # 获取预约记录
        appointment = Appointment.query.filter_by(status='pending').first()
        
        if not appointment:
            print("[ERROR] 未找到待确认的预约记录")
            return False
        
        print(f"[TEST] 当前预约状态: {appointment.status}")
        
        # 更新状态
        appointment.confirm()
        db.session.commit()
        print(f"[TEST] 状态更新后: {appointment.status}")
        
        # 验证更新
        check_appointment = Appointment.query.filter_by(id=appointment.id).first()
        if check_appointment.status == 'confirmed':
            print("[SUCCESS] 预约状态更新成功")
            return True
        else:
            print(f"[ERROR] 预约状态更新失败，期望'confirmed'，实际'{check_appointment.status}'")
            return False
            
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] 测试失败: {str(e)}")
        return False

if __name__ == '__main__':
    # 初始化数据库
    db.create_all()
    
    # 清理旧数据
    print("[TEST] 清理旧测试数据...")
    Appointment.query.delete()
    Message.query.delete()
    Property.query.delete()
    User.query.delete()
    db.session.commit()
    
    # 运行测试
    setup_test_data()
    test_appointment_creation()
    test_appointment_status_update()
    
    print("\n[TEST] 测试完成")