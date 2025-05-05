from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- НАЛАШТУЙТЕ ЦЕЙ РЯДОК ПІДКЛЮЧЕННЯ ---
# Формат для SQL Server з Windows Authentication:
# DATABASE_URL = "mssql+pyodbc://<Ім'я_Сервера>/<Назва_БД>?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

# Формат для SQL Server з SQL Server Authentication:
# DATABASE_URL = "mssql+pyodbc://<Ім'я_Користувача>:<Пароль>@<Ім'я_Сервера>/<Назва_БД>?driver=ODBC+Driver+17+for+SQL+Server"

# ВАШ РЯДОК ПІДКЛЮЧЕННЯ (замініть значення):
# Переконайтесь, що драйвер вказаний правильно (може бути 'SQL Server', 'SQL Server Native Client 11.0' тощо)
DATABASE_URL = "mssql+pyodbc://localhost\\SQLEXPRESS/BookStoreSystem?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
# Якщо використовуєте DSN (Data Source Name), налаштований у Windows ODBC Administrator:
# DATABASE_URL = "mssql+pyodbc://YourUsername:YourPassword@YourDsnName"


# Створення двигуна SQLAlchemy
# echo=True буде виводити SQL запити в консоль (корисно для дебагу)
engine = create_engine(DATABASE_URL, echo=True)

# Створення сесії для взаємодії з БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для моделей SQLAlchemy
Base = declarative_base()

# Функція-залежність для отримання сесії БД у ендпоінтах
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
