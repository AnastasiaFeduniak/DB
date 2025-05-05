from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date
from datetime import datetime
# Схема для відповіді з токеном
class Token(BaseModel):
    access_token: str
    token_type: str

# Схема для даних всередині токена
class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None

# Схема для представлення користувача (без пароля)
class User(BaseModel):
    employee_id: int
    email: EmailStr
    first_name: str
    last_name: str
    role_name: str # Назва ролі важлива для фронтенду

    class Config:
        # У Pydantic v1: orm_mode = True
        # У Pydantic v2: from_attributes = True
        from_attributes = True # Дозволяє створювати схему з об'єкта SQLAlchemy

# Схема для внутрішнього використання (з хешем пароля)
# Використовується для отримання даних з БД
class UserInDB(User):
    password_hash: str
    role_id: int # Може бути корисно мати і ID ролі

class PopularBook(BaseModel):
    book_id: int
    title: str
    total_quantity: int

    class Config:
        from_attributes = True

class LowStockItem(BaseModel):
    book_id: int
    title: str
    location_id: int
    location_address: str
    quantity: int

    class Config:
        from_attributes = True

class DashboardMetrics(BaseModel):
    revenue_last_week: float
    popular_books_last_week: List[PopularBook]
    low_stock_items: List[LowStockItem]
    new_orders_today: int

    class Config:
        from_attributes = True

# Add other schemas as needed for Books, Authors etc.
class BookBase(BaseModel):
    title: str
    author_id: int
    category_id: int
    publisher_id: int
    publication_year: int
    description: Optional[str] = None
    price: float # Use float for Pydantic, SQLAlchemy handles DECIMAL
    discount_percentage: Optional[float] = 0

class BookDisplay(BookBase): # Schema for displaying book info
    book_id: int
    # Add author/category/publisher names if needed after joining in query
    # author_name: str
    # category_name: str
    # publisher_name: str

    class Config:
        from_attributes = True
# Add schemas for Author, Category, Publisher, Employee etc.

class BookBase(BaseModel):
    # Базова схема з полями, що є і при створенні, і при відповіді
    title: str = Field(..., min_length=1, max_length=255) # Обов'язкове поле
    author_id: int
    category_id: int
    publisher_id: int
    publication_year: int = Field(..., gt=1449) # Рік має бути > 1449
    price: float = Field(..., gt=0) # Ціна має бути > 0
    discount_percentage: float = Field(default=0.0, ge=0, le=100) # Від 0 до 100, за замовч. 0
    description: Optional[str] = None # Необов'язкове поле

class BookCreate(BookBase):
    # Схема для створення книги (успадковує всі поля з BookBase)
    pass

class BookUpdate(BaseModel): # НЕ успадковуємо від BookBase, бо поля опціональні
    # Схема для оновлення (всі поля необов'язкові)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author_id: Optional[int] = None
    category_id: Optional[int] = None
    publisher_id: Optional[int] = None
    publication_year: Optional[int] = Field(None, gt=1449)
    price: Optional[float] = Field(None, gt=0)
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    description: Optional[str] = None

class Book(BookBase): # <--- ОСЬ ЦЕЙ КЛАС ПОТРІБЕН для BookListResponse
    # Схема для відповіді API (включає book_id)
    book_id: int
    # Якщо ваша SQLAlchemy модель обчислює final_price, додайте його:
    # final_price: Optional[float] = None

    class Config:
        from_attributes = True # Для Pydantic v2 (або orm_mode = True для v1)
# --- КІНЕЦЬ СХЕМ ДЛЯ КНИГ ---

# --- ДОДАЙТЕ АБО ПЕРЕВІРТЕ СХЕМИ ДЛЯ СПИСКІВ (для dropdown) ---
class SimpleAuthorListItem(BaseModel):
    author_id: int
    full_name: str


class SimpleCategoryListItem(BaseModel):
    category_id: int
    name: str

class SimplePublisherListItem(BaseModel):
    publisher_id: int
    name: str
class AuthorBase(BaseModel):
    first_name: Optional[str] = None
    last_name: str
    birth_date: Optional[date] = None # Додано поле дати народження

class AuthorCreate(AuthorBase):
    # last_name успадковується і є обов'язковим
     pass

class AuthorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None # Додано поле дати народження

class Author(AuthorBase):
    author_id: int

    class Config:
        from_attributes = True

# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None # Додано поле опису

class CategoryCreate(CategoryBase):
     pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None # Додано поле опису

class Category(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True

class ClientBase(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    # Зробимо телефон обов'язковим і email опціональним, але унікальним
    phone_number: str = Field(..., max_length=20) # ... означає обов'язкове поле
    email: Optional[EmailStr] = Field(None, max_length=100)
    # password: Optional[str] = None # Якщо потрібно створювати пароль

class ClientCreate(ClientBase):
    # Можна додати специфічні поля для створення, якщо потрібно
    pass

class ClientUpdate(BaseModel): # Окремо, щоб всі поля були Optional
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=100)
    # password: Optional[str] = None # Якщо дозволено оновлювати пароль

class Client(ClientBase): # Схема для відповіді API
    client_id: int
    # Можна додати поля, що не входять в Base, якщо потрібно

    class Config:
        from_attributes = True # Обов'язково для Pydantic v2
# --- End Client Schemas ---

class SimpleRoleListItem(BaseModel):
    role_id: int
    role_name: str
    class Config: from_attributes = True

class SimpleLocationListItem(BaseModel):
    location_id: int
    address: str # Або інше поле для ідентифікації локації
    class Config: from_attributes = True

# --- Employee Schemas ---
class EmployeeBase(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    phone_number: str = Field(..., max_length=20)
    email: EmailStr = Field(..., max_length=100)
    role_id: int
    location_id: Optional[int] = None # Може бути null для деяких ролей? Або обов'язковим?

class EmployeeCreate(EmployeeBase):
    password: str = Field(..., min_length=6) # Додаємо поле паролю для створення

class EmployeeUpdate(BaseModel): # Окремо, щоб всі поля були Optional
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = Field(None, max_length=100)
    role_id: Optional[int] = None
    location_id: Optional[int] = None
    password: Optional[str] = Field(None, min_length=6) # Пароль необов'язковий при оновленні
    # is_active: Optional[bool] = None # Можна додати поле активності

class EmployeeRead(EmployeeBase): # Схема для відповіді API
    employee_id: int
    role_name: str # Додаємо ім'я ролі
    location_address: Optional[str] = None # Додаємо адресу локації
    # is_active: bool # Якщо додавали поле активності

    class Config:
        from_attributes = True

class BookSimple(BaseModel):
    book_id: int
    title: str

    class Config:
        from_attributes = True # Для Pydantic v2

class LocationSimple(BaseModel):
    location_id: int
    address: str # Або інше поле, що ідентифікує локацію

    class Config:
        from_attributes = True

# Схема для читання даних про залишки
class BookAmountLocationRead(BaseModel):
    quantity: int
    book: BookSimple
    location: LocationSimple

    class Config:
        from_attributes = True

# Схема для оновлення кількості
class BookAmountLocationUpdate(BaseModel):
    # Використовуємо Field для валідації: кількість не може бути від'ємною
    quantity: int = Field(..., ge=0) 

class BookInOrder(BaseModel):
     book_id: int
     title: Optional[str] = None
     class Config: from_attributes = True

class ClientInOrder(BaseModel):
    client_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str # NOT NULL в моделі
    phone_number: str # NOT NULL в моделі
    class Config: from_attributes = True

class LocationInOrder(BaseModel):
    location_id: int
    address: Optional[str] = None
    class Config: from_attributes = True

# --- Схеми для Елементів Замовлення (BookAmountOrder) ---
class OrderItemBase(BaseModel): # Називаємо OrderItem
    book_id: int
    quantity: int = Field(..., gt=0)
    # Змінено назву, зроблено опціональним
    sold_by_price: Optional[float] = Field(None, ge=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemRead(OrderItemBase):
    record_id: int # Змінено PK
    order_id: int
    book: Optional[BookInOrder] = None
    class Config: from_attributes = True

# --- Схема для Оновлення Статусу ---
class OrderStatusUpdate(BaseModel):
    # Додаємо валідацію можливих статусів згідно hhh.sql
    status: str = Field(..., pattern=r'^(received|delivered|shipped|paid|pending|cancelled)$') # Додано pending/cancelled

# --- Схеми для Замовлення (Order) ---
class OrderBase(BaseModel):
    client_id: int
    location_id: Optional[int] = None # Nullable
    order_date: Optional[datetime] = None # Може бути None при створенні? Або встановлюватись на бекенді
    status: str = "paid" # Default згідно hhh.sql
    # Додано поля з hhh.sql
    delivery_address: str
    receipt_number: str
    receiving_date: Optional[datetime] = None # Nullable
    # Видалено total_amount, employee_id

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = [] # Може бути порожнім при створенні?

class OrderRead(OrderBase): # Повна схема для відповіді Get Details
    order_id: int
    client: Optional[ClientInOrder] = None
    location: Optional[LocationInOrder] = None
    # employee видалено
    items: List[OrderItemRead] = []
    class Config: from_attributes = True

# Схема для списку замовлень (GET /orders/)
class OrderList(BaseModel):
     order_id: int
     order_date: Optional[datetime] = None
     status: str
     # total_amount видалено
     client_id: int
     client_name: Optional[str] = None # Для зручності
     receipt_number: Optional[str] = None # Додано
     location_id: Optional[int] = None
     location_address: Optional[str] = None # Додано
     # Додамо поля, що є в моделі і можуть бути корисні
     delivery_address: Optional[str] = None
     receiving_date: Optional[datetime] = None

     class Config:
         from_attributes = True