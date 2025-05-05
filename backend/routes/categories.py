# routers/categories.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import database, models, schemas, oauth2
from dependencies import get_current_manager_user

category_router = APIRouter(
    prefix="/api/v1/categories",
    tags=['Categories']
)

# GET / - Отримати список категорій (залишається без змін у логіці, але схема відповіді оновлена)
@category_router.get("/", response_model=List[schemas.Category])
async def get_categories(
    search: Optional[str] = Query(None, description="Search term for category name"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    query = db.query(models.Category)
    if search:
        query = query.filter(models.Category.name.ilike(f"%{search}%"))
    categories = query.order_by(models.Category.name).offset(skip).limit(limit).all()
    return categories

# GET /{category_id} - Отримати деталі категорії (залишається без змін у логіці)
@category_router.get("/{category_id}", response_model=schemas.Category)
async def get_category_details(
    category_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    db_category = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return db_category

# POST / - Створити нову категорію (оновлено для description)
@category_router.post("/", response_model=schemas.Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: schemas.CategoryCreate, # Схема тепер містить description
    db: Session = Depends(database.get_db),
    current_manager: models.Employee = Depends(get_current_manager_user)
):
    if not category.name:
        raise HTTPException(status_code=400, detail="Category name is required")
    existing_category = db.query(models.Category).filter(models.Category.name.ilike(category.name)).first()
    if existing_category:
         raise HTTPException(status_code=400, detail=f"Category with name '{category.name}' already exists")

    # Тепер category.model_dump() включатиме description, якщо воно передано
    db_category = models.Category(**category.model_dump())
    try:
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        return db_category
    except Exception as e:
        db.rollback()
        print(f"Error creating category: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create category")

# PUT /{category_id} - Оновити категорію (оновлено для description)
@category_router.put("/{category_id}", response_model=schemas.Category)
async def update_category(
    category_id: int,
    category: schemas.CategoryUpdate, # Схема тепер містить description
    db: Session = Depends(database.get_db),
    current_manager: models.Employee = Depends(get_current_manager_user)
):
    db_category = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    update_data = category.model_dump(exclude_unset=True)
    if not update_data:
         raise HTTPException(status_code=400, detail="No fields provided for update")

    # Перевірка унікальності імені, якщо воно змінюється
    if 'name' in update_data and update_data['name'].lower() != db_category.name.lower():
         existing = db.query(models.Category).filter(models.Category.name.ilike(update_data['name'])).first()
         if existing:
             raise HTTPException(status_code=400, detail=f"Category with name '{update_data['name']}' already exists")

    for key, value in update_data.items():
        setattr(db_category, key, value) # Включаючи description

    try:
        db.commit()
        db.refresh(db_category)
        return db_category
    except Exception as e:
        db.rollback()
        print(f"Error updating category {category_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update category")

# DELETE /{category_id} - Видалити категорію (залишається без змін у логіці)
@category_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(database.get_db),
    current_manager: models.Employee = Depends(get_current_manager_user)
):
    db_category = db.query(models.Category).filter(models.Category.category_id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    related_books = db.query(models.Book).filter(models.Book.category_id == category_id).count()
    if related_books > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete category (ID: {category_id}). Category is linked to {related_books} book(s)."
        )
    try:
        db.delete(db_category)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        print(f"Error deleting category {category_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete category")