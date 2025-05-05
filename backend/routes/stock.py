# routes/stock.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import database, models, schemas, oauth2
# Припустимо, у вас є файл dependencies.py з цією функцією
from dependencies import get_current_manager_user

stock_router = APIRouter(
    prefix="/api/v1/stock",
    tags=['Stock Management'] # Тег для документації Swagger
)

# --- Ендпоінт для отримання залишків ---
@stock_router.get("/", response_model=List[schemas.BookAmountLocationRead])
async def get_stock_levels(
    location_id: Optional[int] = Query(None, description="Filter by specific location ID (optional)"),
    book_title: Optional[str] = Query(None, description="Filter by book title (case-insensitive search)"),
    db: Session = Depends(database.get_db),
    # Доступно всім автентифікованим користувачам
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    query = db.query(models.BookAmountLocation).options(
        # Завантажуємо пов'язані дані ефективно
        joinedload(models.BookAmountLocation.book),
        joinedload(models.BookAmountLocation.location)
    )

    # --- Фільтрація ---
    # Менеджер бачить ТІЛЬКИ свою локацію
    if current_user.role.role_name in ['Location Manager', 'Cashier']:
        if not current_user.location_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manager's location is not set")
        query = query.filter(models.BookAmountLocation.location_id == current_user.location_id)
    # Якщо запит прийшов з параметром location_id (наприклад, для Адміна чи Касира)
    elif location_id:
        query = query.filter(models.BookAmountLocation.location_id == location_id)
    # Інакше (Адмін без фільтра) - показуємо все

    # Фільтр за назвою книги
    if book_title:
    # Цей join додає ЩЕ ОДИН JOIN до Books
        squery = query.join(models.Book).filter(models.Book.title.ilike(f"%{book_title}%"))

    # Сортування
    # Ці join додають ЩЕ ОДИН JOIN до Books та ЩЕ ОДИН JOIN до Locations
    query = query.join(models.Book).join(models.Location).order_by(models.Book.title, models.Location.address)

    stock_levels = query.all()
    return stock_levels

# --- Ендпоінт для оновлення кількості ---
@stock_router.put("/{book_id}/{location_id}", response_model=schemas.BookAmountLocationRead)
async def update_stock_level(
    book_id: int,
    location_id: int,
    stock_update: schemas.BookAmountLocationUpdate, # Використовуємо схему з валідацією
    db: Session = Depends(database.get_db),
    # Доступно ТІЛЬКИ менеджерам
    current_manager: models.Employee = Depends(get_current_manager_user) # Використовуємо залежність для менеджера
):
    # Перевірка, чи менеджер оновлює свою локацію
    if current_manager.location_id != location_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Managers can only update stock for their own location"
        )

    # Знаходимо запис у базі даних
    db_stock = db.query(models.BookAmountLocation).filter(
        models.BookAmountLocation.book_id == book_id,
        models.BookAmountLocation.location_id == location_id
    ).first()

    if not db_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock record not found for this book and location"
        )

    # Оновлюємо кількість (валідація >= 0 відбувається у схемі stock_update)
    db_stock.quantity = stock_update.quantity
    try:
        db.commit()
        db.refresh(db_stock)
        # Потрібно завантажити зв'язки для відповіді (якщо вони не завантажені автоматично після refresh)
        # Якщо використовуєте Pydantic v1, може знадобитись db.refresh(db_stock, ['book', 'location'])
        return db_stock
    except Exception as e:
        db.rollback()
        print(f"Error updating stock: {e}") # Логування помилки
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update stock quantity")
    
