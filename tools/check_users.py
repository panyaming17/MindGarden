from backend.core.database import SessionLocal, UserDB

db = SessionLocal()
try:
    users = db.query(UserDB).all()
    print('Number of users:', len(users))
    for user in users:
        print('User ID:', user.id, 'Username:', user.username)
finally:
    db.close()
