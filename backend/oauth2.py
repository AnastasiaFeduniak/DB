from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import auth_token as token_utils # Імпортуємо наш модуль token
import schemas, models # Імпортуємо моделі та схеми
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy.orm import joinedload # Для завантаження ролі

# Шлях до ендпоінта, який генерує токен
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/token")

# Перейменована функція для уникнення конфлікту імен
async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.Employee: # Повертає модель SQLAlchemy
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = token_utils.verify_token(token, credentials_exception)

    # ЗАПИТ ДО РЕАЛЬНОЇ БД для отримання користувача за email з токена
    user = db.query(models.Employee)\
             .options(joinedload(models.Employee.role))\
             .filter(models.Employee.email == token_data.email)\
             .first()

    if user is None:
        raise credentials_exception
    return user

# Функція для отримання поточного АКТИВНОГО користувача (приклад розширення)
# Можна додати перевірку поля is_active, якщо воно є у моделі Employee
# async def get_current_active_user(current_user: models.Employee = Depends(get_current_user_from_token)) -> models.Employee:
#     if not current_user.is_active: # Припускаючи, що є поле is_active
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user