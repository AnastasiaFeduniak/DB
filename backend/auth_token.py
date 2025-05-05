from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
import schemas # Імпортуємо схеми

# --- Конфігурація (можна винести в окремий файл/змінні середовища) ---
SECRET_KEY = "YOUR_VERY_SECRET_KEY_NEEDS_TO_BE_CHANGED" # Той самий ключ, що і в main.py / database.py
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception) -> schemas.TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role") # Отримуємо роль з токена
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email, role=role) # Створюємо об'єкт TokenData
    except JWTError:
        raise credentials_exception
    return token_data