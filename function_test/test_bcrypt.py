import bcrypt

# 测试bcrypt密码验证
def test_bcrypt():
    # 用户pym的密码哈希
    hashed_password = "$2b$12$EI9Oumm8P4dThrpjC773GeO1uv8JeVwj0u6yWu2dA1Jx/hN68Lo1."
    
    # 测试不同的密码
    test_passwords = ["123456", "password", "Pym123456", "admin123"]
    
    for password in test_passwords:
        result = bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
        print(f"Password '{password}': {result}")

if __name__ == "__main__":
    test_bcrypt()
