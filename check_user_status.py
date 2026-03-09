from backend.core.database import UserDB, SessionLocal

db = SessionLocal()
try:
    # 检查pym用户
    user = db.query(UserDB).filter(UserDB.username == 'pym').first()
    if user:
        print(f'User: {user.username}')
        print(f'is_active: {user.is_active}')
        print(f'Type of is_active: {type(user.is_active)}')
        print(f'Boolean value: {bool(user.is_active)}')
    else:
        print('User not found')
finally:
    db.close()
