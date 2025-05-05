# routers/authors.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import database, models, schemas, oauth2
from dependencies import get_current_manager_user
from datetime import date # Переконайтесь, що date імпортовано

author_router = APIRouter(
    prefix="/api/v1/authors",
    tags=['Authors']
)

# GET / - Отримати список авторів (залишається без змін у логіці, але схема відповіді оновлена)
@author_router.get("/", response_model=List[schemas.Author])
async def get_authors(
    search: Optional[str] = Query(None, description="Search term for author first or last name"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    query = db.query(models.Author)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (models.Author.first_name.ilike(search_term)) |
            (models.Author.last_name.ilike(search_term))
        )
    authors = query.order_by(models.Author.last_name, models.Author.first_name).offset(skip).limit(limit).all()
    return authors

# GET /{author_id} - Отримати деталі автора (залишається без змін у логіці)
@author_router.get("/{author_id}", response_model=schemas.Author)
async def get_author_details(
    author_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    db_author = db.query(models.Author).filter(models.Author.author_id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found")
    return db_author

# POST / - Створити нового автора (оновлено для birth_date)
@author_router.post("/", response_model=schemas.Author, status_code=status.HTTP_201_CREATED)
async def create_author(
    author: schemas.AuthorCreate,
    db: Session = Depends(database.get_db),
    current_manager: models.Employee = Depends(get_current_manager_user)
):
    if not author.last_name:
         raise HTTPException(status_code=400, detail="Last name is required")

    # Тепер author.model_dump() включатиме birth_date, якщо воно передано
    db_author = models.Author(**author.model_dump())
    try:
        db.add(db_author)
        db.commit()
        db.refresh(db_author)
        return db_author
    except Exception as e:
        db.rollback()
        print(f"Error creating author: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create author")

# PUT /{author_id} - Оновити автора (оновлено для birth_date)
@author_router.put("/{author_id}", response_model=schemas.Author)
async def update_author(
    author_id: int,
    author: schemas.AuthorUpdate, # Схема оновлення тепер містить birth_date
    db: Session = Depends(database.get_db),
    current_manager: models.Employee = Depends(get_current_manager_user)
):
    db_author = db.query(models.Author).filter(models.Author.author_id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found")

    update_data = author.model_dump(exclude_unset=True)
    if not update_data:
         raise HTTPException(status_code=400, detail="No fields provided for update")

    for key, value in update_data.items():
        setattr(db_author, key, value) # Включаючи birth_date

    try:
        db.commit()
        db.refresh(db_author)
        return db_author
    except Exception as e:
        db.rollback()
        print(f"Error updating author {author_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update author")

# DELETE /{author_id} - Видалити автора (залишається без змін у логіці)
@author_router.delete("/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_author(
    author_id: int,
    db: Session = Depends(database.get_db),
    current_manager: models.Employee = Depends(get_current_manager_user)
):
    db_author = db.query(models.Author).filter(models.Author.author_id == author_id).first()
    if db_author is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Author not found")

    related_books = db.query(models.Book).filter(models.Book.author_id == author_id).count()
    if related_books > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete author (ID: {author_id}). Author is linked to {related_books} book(s)."
        )

    try:
        db.delete(db_author)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        print(f"Error deleting author {author_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete author")