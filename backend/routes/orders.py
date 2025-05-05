# routers/orders.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload, selectinload, aliased
from sqlalchemy import or_, and_, func, cast, String as SQLString # Додано cast, String
from typing import List, Optional
from datetime import date, timedelta, datetime # Додано timedelta, datetime
import database, models, schemas, oauth2
from dependencies import get_current_admin_or_manager_user # Використовуємо об'єднану залежність

order_router = APIRouter(
    prefix="/api/v1/orders",
    tags=['Orders']
)

# --- Ендпоінти для Замовлень ---
@order_router.get("/", response_model=List[schemas.OrderList])
async def get_orders(
    response: Response,
    search: Optional[str] = Query(None, description="Search Order ID, Client, Receipt No."),
    status: Optional[str] = Query(None, description="Filter by status (paid, shipped, etc.)"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    location_id: Optional[int] = Query(None, description="Filter by location ID (Admin only)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(get_current_admin_or_manager_user)
):
    query = db.query(models.Order).options(
        joinedload(models.Order.client),
        joinedload(models.Order.location)
    )

    # Фільтрація за локацією
    target_location_id = None
    if current_user.role and current_user.role.role_name == 'Manager': # Або 'Location Manager'
        if not current_user.location_id:
            # Менеджер має бути прив'язаний до локації для перегляду замовлень локації
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager's location not set")
        target_location_id = current_user.location_id
    elif current_user.role and current_user.role.role_name == 'Administrator' and location_id is not None:
         target_location_id = location_id

    if target_location_id is not None:
         # Переконуємось, що location_id в Order nullable
         query = query.filter(models.Order.location_id == target_location_id)

    # Фільтр за статусом
    if status:
        query = query.filter(models.Order.status.ilike(f"%{status}%"))

    # Фільтр за датою
    if date_from:
        query = query.filter(models.Order.order_date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(models.Order.order_date < datetime.combine(date_to + timedelta(days=1), datetime.min.time()))

    # Фільтр пошуку
    if search:
        search_term = f"%{search}%"
        ClientAlias = aliased(models.Client)
        # Використовуємо outerjoin на випадок, якщо клієнта видалили, але замовлення залишилось (малоймовірно через FK)
        query = query.outerjoin(ClientAlias, models.Order.client_id == ClientAlias.client_id)

        search_filters = [
            ClientAlias.first_name.ilike(search_term),
            ClientAlias.last_name.ilike(search_term),
            ClientAlias.email.ilike(search_term),
            ClientAlias.phone_number.ilike(search_term),
            models.Order.receipt_number.ilike(search_term)
        ]
        try:
            int(search) # Перевірка, чи search є числом (для ID)
            search_filters.append(cast(models.Order.order_id, SQLString).ilike(search_term))
        except ValueError:
            pass
        query = query.filter(or_(*search_filters))

    # distinct перед count, якщо join може дублювати Orders
    total_count_query = query.distinct(models.Order.order_id).statement.with_only_columns(func.count()).order_by(None)
    total_count = db.execute(total_count_query).scalar_one_or_none() or 0


    # distinct() тут також важливий після join
    orders = query.order_by(models.Order.order_date.desc()).distinct().offset(skip).limit(limit).all()

    # Формуємо відповідь згідно schemas.OrderList
    result = []
    for order in orders:
         client_name = "N/A"
         if order.client:
             client_name = f"{order.client.first_name or ''} {order.client.last_name or ''}".strip() or order.client.email or f"Client ID: {order.client_id}"

         # Використовуємо from_orm для автоматичного мапінгу, де це можливо
         order_data = schemas.OrderList.model_validate(order) # Pydantic v2
         # Додаємо поля, яких немає в моделі напряму
         order_data.client_name = client_name
         order_data.location_address = order.location.address if order.location else None
         result.append(order_data)

    response.headers["X-Total-Count"] = str(total_count)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"

    return result

# GET /{order_id} - Отримати деталі замовлення
@order_router.get("/{order_id}", response_model=schemas.OrderRead)
async def get_order_details(
    order_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(get_current_admin_or_manager_user)
):
    query = db.query(models.Order).options(
        joinedload(models.Order.client),
        joinedload(models.Order.location),
        # selectinload для items, joinedload для book всередині items
        selectinload(models.Order.items).joinedload(models.BookAmountOrder.book)
    ).filter(models.Order.order_id == order_id)

    # Перевірка доступу для Менеджера
    if current_user.role and current_user.role.role_name == 'Manager':
        if not current_user.location_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager's location not set")
        # Перевіряємо, чи замовлення належить локації менеджера
        query = query.filter(models.Order.location_id == current_user.location_id)

    db_order = query.first()
    if db_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or access denied")

    # Pydantic v2 з from_attributes=True має коректно зібрати відповідь
    return db_order

# PUT /{order_id}/status - Оновити статус замовлення
@order_router.put("/{order_id}/status", response_model=schemas.OrderRead)
async def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(get_current_admin_or_manager_user)
):
    # Знаходимо замовлення
    query = db.query(models.Order).filter(models.Order.order_id == order_id)

    # Перевірка доступу для Менеджера
    if current_user.role and current_user.role.role_name == 'Manager':
        if not current_user.location_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager's location not set")
        query = query.filter(models.Order.location_id == current_user.location_id)

    db_order = query.first()
    if db_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found or access denied")

    # Валідація нового статусу (використовуємо ті, що є в CHECK constraint + ті, що може використовувати фронтенд)
    valid_statuses = ['received', 'delivered', 'shipped', 'paid', 'pending', 'cancelled']
    if status_update.status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status value. Allowed: {', '.join(valid_statuses)}")

    db_order.status = status_update.status
    # Оновлюємо дату отримання, якщо статус відповідний
    if status_update.status == 'received': # Або 'completed'? Уточнюйте логіку
         db_order.receiving_date = datetime.utcnow() # Використовуємо UTC для узгодженості

    try:
        db.commit()
        # Повертаємо оновлені деталі замовлення
        # Виклик get_order_details гарантує правильну структуру відповіді з усіма зв'язками
        return await get_order_details(order_id, db, current_user)
    except Exception as e:
        db.rollback()
        print(f"Error updating order {order_id} status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update order status")
