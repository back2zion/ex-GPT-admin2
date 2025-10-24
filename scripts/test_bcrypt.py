"""
bcrypt 비밀번호 검증 테스트
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DB에서 가져온 해시
hashed = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyVbsj0fNz7i"

# 테스트할 비밀번호들
test_passwords = ["admin123", "password", "admin", "test"]

for password in test_passwords:
    result = pwd_context.verify(password, hashed)
    print(f"비밀번호 '{password}': {result}")

# 새로운 해시 생성
new_hash = pwd_context.hash("admin123")
print(f"\n새로운 'admin123' 해시: {new_hash}")
print(f"새 해시 검증: {pwd_context.verify('admin123', new_hash)}")
