from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL, Text, Date, Time, Boolean # Додайте необхідні типи
from sqlalchemy.orm import relationship
from database import Base # Імпортуємо Base з database.py
from datetime import datetime
from sqlalchemy.sql import func, text
class Role(Base):
    __tablename__ = "Roles" # Назва таблиці у вашій БД

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)

    # Зв'язок: один Role має багато Employees
    employees = relationship("Employee", back_populates="role")

class Employee(Base):
    __tablename__ = "Employees" # Назва таблиці у вашій БД

    employee_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    role_id = Column(Integer, ForeignKey("Roles.role_id"), nullable=False)
    location_id = Column(Integer, ForeignKey("Locations.location_id"), nullable=True) # Додаємо location_id, якщо він потрібен
    phone_number = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False) # Назва стовпця з хешем пароля

    # Зв'язок: один Employee належить одному Role
    role = relationship("Role", back_populates="employees")
    location = relationship("Location")
    # Можна додати зв'язок з Location, якщо таблиця Locations також змодельована
    # location = relationship("Location") # Потрібна модель Location

# !!! ВАЖЛИВО: Додайте тут інші моделі (Locations, Books тощо), якщо вони потрібні для логіки
# Наприклад, модель Locations для зв'язку з Employees:
class Location(Base):
    __tablename__ = "Locations"
    location_id = Column(Integer, primary_key=True, index=True)
    location_type = Column(String(10), nullable=False)
    address = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True) # Змінено на nullable=True відповідно до hhh.sql
    email = Column(String(100), nullable=True)
    orders = relationship("Order", back_populates="location")
    stock_levels = relationship("BookAmountLocation", back_populates="location")
    # Додайте зв'язок з Employee, якщо потрібно
    employees = relationship("Employee", back_populates="location")

class Author(Base):
    __tablename__ = "Authors"
    author_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    birth_date = Column(Date, nullable=True)
    # Add relationship
    books = relationship("Book", back_populates="author")

class Category(Base):
    __tablename__ = "Categories"
    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    # Add relationship
    books = relationship("Book", back_populates="category")

class Publisher(Base):
    __tablename__ = "Publishers"
    publisher_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=True) # Змінено розмір та nullable
    phone_number = Column(String(20), nullable=True) # Додано з hhh.sql (було NOT NULL)
    email = Column(String(100), nullable=True) # Додано з hhh.sql (було NOT NULL)
    books = relationship("Book", back_populates="publisher")

class Book(Base):
    __tablename__ = "Books"
    book_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True) # Index title
    author_id = Column(Integer, ForeignKey("Authors.author_id"), nullable=False)
    category_id = Column(Integer, ForeignKey("Categories.category_id"), nullable=False)
    publisher_id = Column(Integer, ForeignKey("Publishers.publisher_id"), nullable=False)
    publication_year = Column(Integer)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    discount_percentage = Column(DECIMAL(5, 2), default=0)
    # final_price is computed in DB, can be queried but not directly mapped unless using specific techniques

    # Relationships
    author = relationship("Author", back_populates="books")
    category = relationship("Category", back_populates="books")
    publisher = relationship("Publisher", back_populates="books")
    order_items = relationship("BookAmountOrder", back_populates="book")
    stock_levels = relationship("BookAmountLocation", back_populates="book")

class Client(Base):
    __tablename__ = "Clients"
    client_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    phone_number = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(256))
    # Add relationship
    orders = relationship("Order", back_populates="client")


class Order(Base):
    __tablename__ = "Orders"
    order_id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("Clients.client_id"), nullable=False)
    # Змінено на nullable=True
    location_id = Column(Integer, ForeignKey("Locations.location_id"), nullable=True)
    # employee_id видалено
    # Використовуємо server_default для GETDATE()
    order_date = Column(DateTime, nullable=False, server_default=text('GETDATE()'))
    delivery_address = Column(String(255), nullable=False) # Додано
    receipt_number = Column(String(50), nullable=False)   # Додано
    # Змінено default статусу на 'paid'
    status = Column(String(10), nullable=False, server_default='paid', index=True)
    receiving_date = Column(DateTime, nullable=True) # Додано

    # Relationships
    client = relationship("Client", back_populates="orders")
    location = relationship("Location", back_populates="orders")
    # employee relationship видалено
    # Використовуємо "BookAmountOrder" як target для relationship
    items = relationship("BookAmountOrder", back_populates="order", cascade="all, delete-orphan")
class BookAmountOrder(Base):
    __tablename__ = "BookAmountOrder"
    # PK тепер record_id
    record_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("Orders.order_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("Books.book_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1) # Додано default 1
    # Змінено назву та nullable
    sold_by_price = Column(DECIMAL(10, 2), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="items")
    book = relationship("Book", back_populates="order_items")

class BookAmountLocation(Base):
    __tablename__ = "BookAmountLocation"
    record_id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("Locations.location_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("Books.book_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0) # default 0 може бути логічнішим

    location = relationship("Location", back_populates="stock_levels")
    book = relationship("Book", back_populates="stock_levels")

class WorkingHours(Base):
     __tablename__ = "WorkingHours"
     location_id = Column(Integer, ForeignKey("Locations.location_id"), primary_key=True)
     weekdays_start = Column(Time, nullable=False)
     weekdays_end = Column(Time, nullable=False)
     saturday_start = Column(Time, nullable=True)
     saturday_end = Column(Time, nullable=True)
     sunday_start = Column(Time, nullable=True)
     sunday_end = Column(Time, nullable=True)

     location = relationship("Location") # Додамо зв'язок