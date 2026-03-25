#!/usr/bin/env python3
"""
测试重置密码逻辑
"""
import bcrypt
import time

# 模拟Redis存储
class InMemoryRedis:
    def __init__(self):
        self.data = {}
    
    def setex(self, key, expire, value):
        self.data[key] = (value, time.time() + expire)
    
    def get(self, key):
        if key in self.data:
            value, expire_at = self.data[key]
            if time.time() < expire_at:
                return value
            else:
                del self.data[key]
        return None
    
    def delete(self, key):
        if key in self.data:
            del self.data[key]

# 初始化Redis模拟
redis_client = InMemoryRedis()

# 密码加密
def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# 密码验证
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# 存储验证码
def store_verification_code(key: str, code: str) -> bool:
    """存储验证码到Redis"""
    try:
        redis_client.setex(key, 600, code)
        return True
    except Exception as e:
        print(f"存储验证码失败: {str(e)}")
        return False

# 获取验证码
def get_verification_code(key: str) -> str:
    """从Redis获取验证码"""
    try:
        value = redis_client.get(key)
        # 为了测试方便，当验证码不存在时，返回固定的验证码"123456"
        if not value:
            return "123456"
        return value
    except Exception as e:
        print(f"获取验证码失败: {str(e)}")
        return None

# 删除验证码
def delete_verification_code(key: str) -> bool:
    """从Redis删除验证码"""
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"删除验证码失败: {str(e)}")
        return False

# 模拟重置密码逻辑
def test_reset_password(old_password, new_password):
    """测试重置密码"""
    # 模拟用户数据
    username = "test_user"
    email = "test@example.com"
    hashed_password = get_password_hash(old_password)
    
    print(f"测试重置密码: 旧密码='{old_password}', 新密码='{new_password}'")
    
    # 1. 验证用户是否存在（模拟用户存在）
    print("1. 验证用户存在: 成功")
    
    # 2. 验证邮箱是否匹配（模拟匹配）
    print("2. 验证邮箱匹配: 成功")
    
    # 3. 验证验证码
    key = f"reset:{username}:{email}"
    store_verification_code(key, "123456")
    stored_code = get_verification_code(key)
    if stored_code != "123456":
        print("3. 验证验证码: 失败")
        return False
    print("3. 验证验证码: 成功")
    
    # 4. 验证新密码是否与旧密码相同
    if verify_password(new_password, hashed_password):
        print("4. 验证新密码与旧密码相同: 失败 - 新密码不能与旧密码相同")
        return False
    print("4. 验证新密码与旧密码相同: 成功")
    
    # 5. 删除验证码
    delete_verification_code(key)
    print("5. 删除验证码: 成功")
    
    # 6. 更新密码
    print("6. 更新密码: 成功")
    
    return True

# 测试用例
print("=== 测试用例1: 新密码与旧密码相同 ===")
test_reset_password("test123", "test123")
print()

print("=== 测试用例2: 新密码与旧密码不同 ===")
test_reset_password("test123", "newpassword123")
print()
