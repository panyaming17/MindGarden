from backend.core.database import UserDB, SessionLocal
import bcrypt

db = SessionLocal()
try:
    # 获取用户pym
    user = db.query(UserDB).filter(UserDB.username == 'pym').first()
    if user:
        # 设置新密码为"Pym123456"
        password = "Pym123456"
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user.password_hash = hashed_password.decode("utf-8")
        # 确保用户被软删除
        user.is_active = False
        db.commit()
        print(f"User pym's password has been set to: {password}")
        print(f"User pym's is_active status: {user.is_active}")
    else:
        print("User not found")
finally:
    db.close()
