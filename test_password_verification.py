#!/usr/bin/env python3
"""
测试密码验证逻辑
"""
import bcrypt

def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# 测试用例
password = "test123"
hashed = get_password_hash(password)

print(f"原始密码: {password}")
print(f"哈希密码: {hashed}")
print(f"验证相同密码: {verify_password(password, hashed)}")
print(f"验证不同密码: {verify_password('different', hashed)}")
