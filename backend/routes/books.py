from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional # Annotated might not be needed here unless for specific deps
import database, models, schemas, oauth2 # Assuming these exist
from pydantic import BaseModel
from datetime import datetime, timedelta, date # Потрібно імпортувати datetime, timedelta, date
book_router = APIRouter(
    prefix="/api/v1", # Base prefix for book-related routes
    tags=['Books']    # Tag for Swagger UI grouping
)

# Dependency for Admin Role Check
async def get_current_admin_user(current_user: models.Employee = Depends(oauth2.get_current_user_from_token)) -> models.Employee:
    if not current_user.role or current_user.role.role_name != 'Administrator':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted"
        )
    return current_user

# --- Endpoints for Dropdown Lists ---

class SimpleListItem(BaseModel):
    id: int
    name: str

class SimpleAuthorListItem(BaseModel):
    author_id: int
    full_name: str # Assuming your Author model has first/last name

class SimpleCategoryListItem(BaseModel):
    category_id: int
    name: str

class SimplePublisherListItem(BaseModel):
    publisher_id: int
    name: str


@book_router.get("/authors/list", response_model=List[SimpleAuthorListItem])
async def get_authors_list(db: Session = Depends(database.get_db), current_user: models.Employee = Depends(oauth2.get_current_user_from_token)):
     authors = db.query(models.Author.author_id, models.Author.first_name, models.Author.last_name).order_by(models.Author.last_name, models.Author.first_name).all()
     # Combine first and last names
     return [SimpleAuthorListItem(author_id=a.author_id, full_name=f"{a.first_name or ''} {a.last_name or ''}".strip()) for a in authors]


@book_router.get("/categories/list", response_model=List[SimpleCategoryListItem])
async def get_categories_list(db: Session = Depends(database.get_db), current_user: models.Employee = Depends(oauth2.get_current_user_from_token)):
    categories = db.query(models.Category.category_id, models.Category.name).order_by(models.Category.name).all()
    return categories

@book_router.get("/publishers/list", response_model=List[SimplePublisherListItem])
async def get_publishers_list(db: Session = Depends(database.get_db), current_user: models.Employee = Depends(oauth2.get_current_user_from_token)):
    publishers = db.query(models.Publisher.publisher_id, models.Publisher.name).order_by(models.Publisher.name).all()
    return publishers


# --- Endpoints for Books CRUD ---

# Define response model for Book list to include related names
class BookListResponse(schemas.Book): # Inherit from base Book schema
    author_name: Optional[str] = None
    category_name: Optional[str] = None
    publisher_name: Optional[str] = None

    class Config:
        from_attributes = True


@book_router.get("/books", response_model=List[BookListResponse])
async def get_books(
    search: Optional[str] = Query(None, description="Search term for book title"),
    skip: int = 0,
    limit: int = 100, # Add pagination later if needed
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token) # All roles can view
):
    query = db.query(models.Book)\
              .options(
                  joinedload(models.Book.author),
                  joinedload(models.Book.category),
                  joinedload(models.Book.publisher)
              )

    if search:
        query = query.filter(models.Book.title.ilike(f"%{search}%")) # Case-insensitive search

    books = query.order_by(models.Book.title).offset(skip).all()

    # Prepare response with related names
    response_list = []
    for book in books:
        book_data = schemas.Book.model_validate(book) # Use new Pydantic v2 method
        # Create the response object, copying base data and adding names
        response_item = BookListResponse(
            **book_data.model_dump(), # Use new Pydantic v2 method
            author_name=f"{book.author.first_name or ''} {book.author.last_name or ''}".strip() if book.author else None,
            category_name=book.category.name if book.category else None,
            publisher_name=book.publisher.name if book.publisher else None
        )
        response_list.append(response_item)

    return response_list


@book_router.get("/books/{book_id}", response_model=schemas.Book) # Return base Book schema for details
async def get_book_details(
    book_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token) # All roles can view details
):
    db_book = db.query(models.Book).filter(models.Book.book_id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return db_book


@book_router.post("/books", response_model=schemas.Book, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: schemas.BookCreate, # Use BookCreate schema (doesn't include book_id)
    db: Session = Depends(database.get_db),
    # Protect endpoint: only Admin can create
    current_admin: models.Employee = Depends(get_current_admin_user)
):
    # Basic validation (more can be added)
    # Check if related entities exist (optional, depends on FK constraints)
    author = db.query(models.Author).filter(models.Author.author_id == book.author_id).first()
    if not author: raise HTTPException(status_code=400, detail=f"Author with id {book.author_id} not found")
    # Add similar checks for category and publisher...

    # Check year constraint (already in DB check, but good practice)
    current_year = datetime.now().year
    if book.publication_year < 1450 or book.publication_year > current_year:
         raise HTTPException(status_code=400, detail="Invalid publication year")
    if book.price < 0: raise HTTPException(status_code=400, detail="Price cannot be negative")
    if book.discount_percentage < 0 or book.discount_percentage > 100: raise HTTPException(status_code=400, detail="Invalid discount percentage")

    # Create new SQLAlchemy model instance
    db_book = models.Book(**book.model_dump()) # Use new Pydantic v2 method

    try:
        db.add(db_book)
        db.commit()
        db.refresh(db_book) # Refresh to get the generated book_id and computed fields
        return db_book
    except Exception as e:
        db.rollback()
        print(f"Error creating book: {e}") # Log the error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create book")


@book_router.put("/books/{book_id}", response_model=schemas.Book)
async def update_book(
    book_id: int,
    book: schemas.BookUpdate, # Use BookUpdate schema
    db: Session = Depends(database.get_db),
    # Protect endpoint: only Admin can update
    current_admin: models.Employee = Depends(get_current_admin_user)
):
    db_book = db.query(models.Book).filter(models.Book.book_id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Update model fields from the request data
    update_data = book.model_dump(exclude_unset=True) # Don't update fields not present in request

     # Validate related IDs if they are being updated
    if 'author_id' in update_data and not db.query(models.Author).filter(models.Author.author_id == update_data['author_id']).first():
         raise HTTPException(status_code=400, detail=f"Author with id {update_data['author_id']} not found")
    # Add similar checks for category and publisher...

    # Validate year/price/discount if updated
    if 'publication_year' in update_data:
        current_year = datetime.now().year
        if update_data['publication_year'] < 1450 or update_data['publication_year'] > current_year:
            raise HTTPException(status_code=400, detail="Invalid publication year")
    if 'price' in update_data and update_data['price'] < 0:
         raise HTTPException(status_code=400, detail="Price cannot be negative")
    if 'discount_percentage' in update_data and (update_data['discount_percentage'] < 0 or update_data['discount_percentage'] > 100):
        raise HTTPException(status_code=400, detail="Invalid discount percentage")


    for key, value in update_data.items():
        setattr(db_book, key, value)

    try:
        db.commit()
        db.refresh(db_book)
        return db_book
    except Exception as e:
        db.rollback()
        print(f"Error updating book {book_id}: {e}") # Log the error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update book")


@book_router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: int,
    db: Session = Depends(database.get_db),
    # Protect endpoint: only Admin can delete
    current_admin: models.Employee = Depends(get_current_admin_user)
):
    db_book = db.query(models.Book).filter(models.Book.book_id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    try:
        db.delete(db_book)
        db.commit()
        # No content to return on successful delete
        return None # Or use Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        db.rollback()
        # Check for foreign key constraint violation (e.g., book is in an order)
        # This depends on DB specifics, might need more specific error handling
        print(f"Error deleting book {book_id}: {e}") # Log the error
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cannot delete book (ID: {book_id}). It might be referenced in orders or stock records.")