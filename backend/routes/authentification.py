# routers/authentication.py

# ... (імпорти та router = APIRouter(...) як раніше) ...
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated # Для Python 3.9+
import database, schemas, models, hashing, auth_token as token_utils, oauth2
from sqlalchemy.orm import joinedload # Для завантаження ролі

router = APIRouter(
    tags=['Authentication']
)

@router.post('/api/v1/login/token', response_model=schemas.Token)
async def login(
    request: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(database.get_db)
):
    user = db.query(models.Employee)\
             .options(joinedload(models.Employee.role))\
             .filter(models.Employee.email == request.username)\
             .first()

    print(f"Login attempt for: {request.username}")

    if not user:
        print("User not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Invalid Credentials")

    print(f"User found: {user.email}. Verifying password...")

    # Пряме порівняння пароля
    if request.password != user.password_hash:
        print("Password verification failed.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Invalid Credentials")

    role_name = user.role.role_name if user.role else "Unknown"
    print(f"Password verified. Generating token for role: {role_name}")

    access_token = token_utils.create_access_token(
        data={"sub": user.email, "role": role_name}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/api/v1/users/me", response_model=schemas.User) # Використовуємо схему User без пароля
async def read_users_me(
    current_user: Annotated[models.Employee, Depends(oauth2.get_current_user_from_token)] # Використовуємо залежність для отримання поточного користувача
):
    # FastAPI автоматично викличе get_current_user_from_token,
    # який перевірить токен і поверне об'єкт моделі Employee

    # Якщо токен невалідний або користувач не знайдений, залежність Depends(oauth2.get_current_user_from_token)
    # автоматично викине помилку 401 Unauthorized

    # Створюємо Pydantic схему з моделі SQLAlchemy для відповіді
    # Переконуємось, що роль завантажена (має бути через joinedload в get_current_user_from_token)
    role_name = current_user.role.role_name if current_user.role else "Unknown"

    user_data = schemas.User(
        employee_id=current_user.employee_id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role_name=role_name
    )
    return user_data