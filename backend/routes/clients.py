# routers/clients.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import database, models, schemas, oauth2 # Переконайтесь, що oauth2 імпортовано

client_router = APIRouter(
    prefix="/api/v1/clients",
    tags=['Clients']
)

# --- CRUD Endpoints for Clients ---

# GET / - Отримати список клієнтів (доступно всім залогіненим)
@client_router.get("/", response_model=List[schemas.Client])
async def get_clients(
    search: Optional[str] = Query(None, description="Search term for first name, last name, email, or phone"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token) # Будь-який залогінений співробітник
):
    query = db.query(models.Client)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Client.first_name.ilike(search_term),
                models.Client.last_name.ilike(search_term),
                models.Client.email.ilike(search_term),
                models.Client.phone_number.ilike(search_term)
            )
        )
    clients = query.order_by(models.Client.last_name, models.Client.first_name).offset(skip).limit(limit).all()
    return clients

# GET /{client_id} - Отримати деталі клієнта (доступно всім залогіненим)
@client_router.get("/{client_id}", response_model=schemas.Client)
async def get_client_details(
    client_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    db_client = db.query(models.Client).filter(models.Client.client_id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return db_client

# POST / - Створити нового клієнта (доступно всім залогіненим)
@client_router.post("/", response_model=schemas.Client, status_code=status.HTTP_201_CREATED)
async def create_client(
    client: schemas.ClientCreate,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    # Перевірка на унікальність телефону та email (якщо email надано)
    existing_phone = db.query(models.Client).filter(models.Client.phone_number == client.phone_number).first()
    if existing_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Phone number {client.phone_number} already registered.")
    if client.email:
        existing_email = db.query(models.Client).filter(models.Client.email.ilike(client.email)).first()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email {client.email} already registered.")

    # Тут можна додати хешування пароля, якщо він є у схемі ClientCreate
    # hashed_password = oauth2.get_password_hash(client.password) if client.password else None
    client_data = client.model_dump()
    # if 'password' in client_data: # Замінити пароль на хеш
    #     client_data['password_hash'] = hashed_password
    #     del client_data['password']

    db_client = models.Client(**client_data)
    try:
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client
    except Exception as e:
        db.rollback()
        print(f"Error creating client: {e}") # Логування помилки
        # Перевірка на конкретну помилку унікальності, якщо можливо
        if "UNIQUE constraint failed" in str(e):
             # Можна спробувати визначити, яке поле спричинило помилку
             if client.email and db.query(models.Client).filter(models.Client.email.ilike(client.email)).count() > 1:
                  detail = "Email already exists (concurrent request?)"
             elif db.query(models.Client).filter(models.Client.phone_number == client.phone_number).count() > 1:
                  detail = "Phone number already exists (concurrent request?)"
             else:
                 detail = "Unique constraint failed."
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create client")


# PUT /{client_id} - Оновити клієнта (доступно всім залогіненим)
@client_router.put("/{client_id}", response_model=schemas.Client)
async def update_client(
    client_id: int,
    client: schemas.ClientUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    db_client = db.query(models.Client).filter(models.Client.client_id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    update_data = client.model_dump(exclude_unset=True) # Оновлюємо тільки передані поля

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")

    # Перевірка унікальності, якщо телефон або email змінюються
    if 'phone_number' in update_data and update_data['phone_number'] != db_client.phone_number:
        existing = db.query(models.Client).filter(models.Client.phone_number == update_data['phone_number']).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Phone number {update_data['phone_number']} already registered.")
    if 'email' in update_data and update_data['email'] and update_data['email'].lower() != (db_client.email or '').lower():
         existing = db.query(models.Client).filter(models.Client.email.ilike(update_data['email'])).first()
         if existing:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email {update_data['email']} already registered.")

    # Тут оновлення пароля, якщо потрібно
    # if 'password' in update_data and update_data['password']:
    #     hashed_password = oauth2.get_password_hash(update_data['password'])
    #     db_client.password_hash = hashed_password
    #     del update_data['password'] # Видаляємо звичайний пароль з даних для setattr

    for key, value in update_data.items():
        setattr(db_client, key, value)

    try:
        db.commit()
        db.refresh(db_client)
        return db_client
    except Exception as e:
        db.rollback()
        print(f"Error updating client {client_id}: {e}")
         # Перевірка на конкретну помилку унікальності
        if "UNIQUE constraint failed" in str(e):
             # Спробувати визначити поле
             detail = "Unique constraint failed during update."
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update client")

# DELETE /{client_id} - Видалити клієнта (доступно всім залогіненим)
@client_router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    db_client = db.query(models.Client).filter(models.Client.client_id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    # Перевірка наявності пов'язаних замовлень
    related_orders = db.query(models.Order).filter(models.Order.client_id == client_id).count()
    if related_orders > 0:
        # Можна або заборонити видалення, або реалізувати анонімізацію/архівацію
        # Наразі забороняємо:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete client (ID: {client_id}). Client has {related_orders} associated order(s)."
        )

    try:
        db.delete(db_client)
        db.commit()
        # Для статусу 204 не потрібно повертати тіло
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        db.rollback()
        print(f"Error deleting client {client_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete client")