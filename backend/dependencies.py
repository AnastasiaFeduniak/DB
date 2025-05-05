# dependencies.py
from fastapi import Depends, HTTPException, status
import models, oauth2 # Припускаємо, що ці файли існують

# Перевірка Адміністратора (з books.py)
async def get_current_admin_user(current_user: models.Employee = Depends(oauth2.get_current_user_from_token)) -> models.Employee:
    if not current_user.role or current_user.role.role_name != 'Administrator':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires Administrator privileges"
        )
    return current_user

# Перевірка Менеджера (НОВА)
async def get_current_manager_user(current_user: models.Employee = Depends(oauth2.get_current_user_from_token)) -> models.Employee:
    # Дозволяємо також Адміністраторам виконувати дії Менеджерів (опціонально)
    allowed_roles = ['Location Manager', 'Administrator']
    if not current_user.role or current_user.role.role_name not in allowed_roles:
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Operation requires Manager or Administrator privileges"
         )
    return current_user

async def get_current_admin_or_manager_user(
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
) -> models.Employee:
    """
    Перевіряє, чи поточний користувач є Адміністратором або Менеджером Локації.
    """
    allowed_roles = ["Administrator", "Manager"] # Або "Location Manager"
    if not current_user.role or current_user.role.role_name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted for this role"
        )
    return current_user
# Перевірка будь-якого авторизованого користувача (з oauth2.py)
# Це просто Depends(oauth2.get_current_user_from_token)