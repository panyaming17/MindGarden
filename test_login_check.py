from backend.core.database import UserDB, SessionLocal

db = SessionLocal()
try:
    # 检查pym用户
    user = db.query(UserDB).filter(UserDB.username == 'pym').first()
    if user:
        print(f'User: {user.username}')
        print(f'is_active: {user.is_active}')
        print(f'Type: {type(user.is_active)}')
        print(f'not is_active: {not user.is_active}')
        print(f'bool(not user.is_active): {bool(not user.is_active)}')
        
        # 模拟登录检查
        if not user.is_active:
            print('用户账号已被禁用')
        else:
            print('用户账号正常')
    else:
        print('User not found')
finally:
    db.close()
