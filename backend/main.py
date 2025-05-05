from fastapi import FastAPI
from routes.authentification import router 
from routes.dashboard import dashboard_router
from database import engine # Імпортуємо двигун для створення таблиць (опціонально)
import models # Імпортуємо моделі для створення таблиць (опціонально)
from fastapi.middleware.cors import CORSMiddleware # Імпортуємо CORS
from routes.books import book_router
from routes.authors import author_router
from routes.categories import category_router
from routes.clients import client_router
from routes.stock import stock_router
from routes.employees import employee_router
from routes.orders import order_router
from routes.exports import export_router
# --- Створення таблиць у БД (Якщо вони ще не створені) ---
# Розкоментуйте цю лінію, ЯКЩО ви хочете, щоб SQLAlchemy
# спробував створити таблиці на основі ваших моделей при старті додатку.
# УВАГА: Це не замінює повноцінні міграції (як Alembic) і може бути небезпечним
# для існуючих баз даних. Краще створювати таблиці окремим SQL скриптом.
# models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- CORS Middleware (Дуже важливо для взаємодії з фронтендом) ---
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
    "http://localhost:5500" # Стандартний порт Live Server у VS Code
    # Додайте сюди URL вашого фронтенду
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Дозволені джерела
    allow_credentials=True,
    allow_methods=["*"], # Дозволити всі методи (GET, POST, PUT, DELETE тощо)
    allow_headers=["*"], # Дозволити всі заголовки
)


# Підключення маршрутизатора автентифікації
app.include_router(router)
app.include_router(dashboard_router)
app.include_router(book_router)
app.include_router(category_router)
app.include_router(author_router)
app.include_router(employee_router)
app.include_router(client_router)
app.include_router(stock_router)
app.include_router(order_router)
app.include_router(export_router)
# Додайте тут інші маршрутизатори для книг, замовлень тощо

@app.get("/")
def read_root():
    return {"message": "Bookstore API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)