from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_ # Додаємо and_
from datetime import datetime, timedelta, date # Додаємо date
from typing import List, Annotated
import database, models, schemas, oauth2
from pydantic import BaseModel

dashboard_router = APIRouter(
    prefix="/api/v1/dashboard", # Префікс для всіх ендпоінтів цього роутера
    tags=['Dashboard']
)

# --- Схеми для відповіді ---
class PopularBook(BaseModel):
    book_id: int
    title: str
    total_quantity: int
    class Config: from_attributes=True


class LowStockItem(BaseModel):
    book_id: int
    title: str
    location_id: int
    location_address: str
    quantity: int
    class Config: from_attributes=True

class DashboardMetrics(BaseModel):
    revenue_last_week: float
    popular_books_last_week: List[PopularBook]
    low_stock_items: List[LowStockItem]
    new_orders_today: int
    class Config: from_attributes=True

@dashboard_router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    # --- 1. Дохід за останній тиждень ---
    seven_days_ago = datetime.utcnow() - timedelta(days=7) # Використовуємо UTCNow для узгодженості

    # --- !!! ВИПРАВЛЕНО: Розрахунок доходу через BookAmountOrder !!! ---
    revenue_result = db.query(func.sum(models.BookAmountOrder.sold_by_price * models.BookAmountOrder.quantity))\
                       .join(models.Order, models.BookAmountOrder.order_id == models.Order.order_id)\
                       .filter(
                           models.Order.order_date >= seven_days_ago,
                           # Використовуємо статуси, які означають отриманий дохід
                           models.Order.status.in_(['paid', 'shipped', 'delivered', 'received', 'completed'])
                       ).scalar()
    # --- КІНЕЦЬ ВИПРАВЛЕННЯ ---

    revenue_last_week = float(revenue_result) if revenue_result is not None else 0.0

    # --- 2. Найпопулярніші книги ---
    popular_books_query = db.query(
                           models.Book.book_id,
                           models.Book.title,
                           func.sum(models.BookAmountOrder.quantity).label('total_quantity')
                       )\
                       .join(models.BookAmountOrder, models.Book.book_id == models.BookAmountOrder.book_id)\
                       .join(models.Order, models.BookAmountOrder.order_id == models.Order.order_id)\
                       .filter(
                           models.Order.order_date >= seven_days_ago,
                           models.Order.status.in_(['paid', 'shipped', 'delivered', 'received', 'completed']) # Враховуємо тільки продані
                       )\
                       .group_by(models.Book.book_id, models.Book.title)\
                       .order_by(desc('total_quantity'))\
                       .limit(5)\
                       .all()
    popular_books_last_week = [PopularBook(book_id=b.book_id, title=b.title, total_quantity=b.total_quantity or 0) for b in popular_books_query]


    # --- 3. Товари, що потребують поповнення ---
    low_stock_threshold = 10
    low_stock_query = db.query(
                           models.Book.book_id,
                           models.Book.title,
                           models.Location.location_id,
                           models.Location.address.label('location_address'),
                           models.BookAmountLocation.quantity
                       )\
                       .join(models.BookAmountLocation, models.Book.book_id == models.BookAmountLocation.book_id)\
                       .join(models.Location, models.BookAmountLocation.location_id == models.Location.location_id)\
                       .filter(
                           models.Location.location_type == 'bookstore', # Тільки книгарні
                           models.BookAmountLocation.quantity < low_stock_threshold
                       )\
                       .order_by(models.Location.address, models.BookAmountLocation.quantity)\
                       .limit(10)\
                       .all()
    low_stock_items = [LowStockItem(book_id=i.book_id, title=i.title, location_id=i.location_id, location_address=i.location_address, quantity=i.quantity or 0) for i in low_stock_query]

    # --- 4. Кількість нових замовлень сьогодні ---
    start_of_today_utc = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    new_orders_count = db.query(func.count(models.Order.order_id))\
                       .filter(
                           models.Order.order_date >= start_of_today_utc,
                           # Статуси, що вважаються "новими"
                           models.Order.status.in_(['pending', 'paid'])
                       ).scalar()
    new_orders_today = new_orders_count if new_orders_count is not None else 0

    # Формуємо результат
    return DashboardMetrics(
        revenue_last_week=revenue_last_week,
        popular_books_last_week=popular_books_last_week,
        low_stock_items=low_stock_items,
        new_orders_today=new_orders_today
    )
