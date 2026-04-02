import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from backend.core.database import SessionLocal
from sqlalchemy import text

# 创建数据库会话
db = SessionLocal()

# 执行DESCRIBE命令查看表结构
result = db.execute(text('DESCRIBE user_archives'))

# 打印表头
print('Field\tType\tNull\tKey\tDefault\tExtra')

# 打印每一行数据
for row in result:
    print('\t'.join(str(col) for col in row))

# 关闭会话
db.close()
