from backend.core.database import UserDB, SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

db = SessionLocal()
try:
    # 检查pym用户
    user = db.query(UserDB).filter(UserDB.username == 'pym').first()
    if user:
        print(f'User: {user.username}')
        print(f'is_active: {user.is_active}')
        print(f'Password hash: {user.password_hash}')
        print(f'Password "123456" is correct: {verify_password("123456", user.password_hash)}')
        print(f'Password "password" is correct: {verify_password("password", user.password_hash)}')
    else:
        print('User not found')
finally:
    db.close()
