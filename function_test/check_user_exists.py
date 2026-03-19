from backend.core.database import UserDB, SessionLocal

db = SessionLocal()
try:
    # 检查pym用户
    user = db.query(UserDB).filter(UserDB.username == 'pym').first()
    if user:
        print(f'User found: {user.username}')
        print(f'is_active: {user.is_active}')
        print(f'ID: {user.id}')
        print(f'Email: {user.email}')
        print(f'Role: {user.role}')
        print(f'Password hash: {user.password_hash}')
    else:
        print('User pym not found!')
    
    # 检查所有用户
    print('\nAll users:')
    users = db.query(UserDB).all()
    for u in users:
        print(f'Username: {u.username}, is_active: {u.is_active}')
finally:
    db.close()
