from backend.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('DROP TABLE IF EXISTS messages'))
    conn.execute(text('DROP TABLE IF EXISTS conversations'))
    conn.commit()
    print('Tables dropped successfully')
