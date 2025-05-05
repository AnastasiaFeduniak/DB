# routers/employees.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
import database, models, schemas, oauth2

employee_router = APIRouter(
    prefix="/api/v1/employees",
    tags=['Employees']
)

# --- Helper Functions / Dependencies ---
# (Можна винести в окремий файл dependencies.py)
def check_employee_permission(target_employee: models.Employee, current_user: models.Employee):
    """Перевіряє, чи має поточний користувач право на дію з цільовим співробітником."""
    if current_user.role.role_name == 'Administrator':
        return True # Адмін може все (майже)

    if current_user.role.role_name == 'Manager':
        # Менеджер може діяти тільки в межах своєї локації
        if target_employee.location_id != current_user.location_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted on employees outside your location")
        # Менеджер не може редагувати/видаляти Адміна або іншого Менеджера (правило?)
        if target_employee.role.role_name in ['Administrator', 'Manager'] and target_employee.employee_id != current_user.employee_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers cannot modify other Managers or Administrators")
        return True

    # Інші ролі (напр. Cashier) не мають доступу
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")

# --- Endpoints for Dropdowns ---
@employee_router.get("/roles/list", response_model=List[schemas.SimpleRoleListItem])
async def get_roles_list(db: Session = Depends(database.get_db), current_user: models.Employee = Depends(oauth2.get_current_user_from_token)):
    # Можливо, обмежити ролі, які може бачити менеджер? Наразі показуємо всі.
    roles = db.query(models.Role).order_by(models.Role.role_name).all()
    return roles

@employee_router.get("/locations/list", response_model=List[schemas.SimpleLocationListItem])
async def get_locations_list(db: Session = Depends(database.get_db), current_user: models.Employee = Depends(oauth2.get_current_user_from_token)):
    # Менеджер бачить тільки свою локацію в списку? Або всі для адміна?
    query = db.query(models.Location)
    if current_user.role.role_name == 'Manager' and current_user.location_id:
         query = query.filter(models.Location.location_id == current_user.location_id)
    locations = query.order_by(models.Location.address).all()
    # Або для простоти поки що показуємо всі локації всім, хто має доступ до створення/редагування
    # locations = db.query(models.Location).order_by(models.Location.address).all()
    return locations


# --- CRUD Endpoints for Employees ---

# GET / - Отримати список співробітників
@employee_router.get("/", response_model=List[schemas.EmployeeRead])
async def get_employees(
    search: Optional[str] = Query(None, description="Search term for first name, last name, email, or phone"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    query = db.query(models.Employee).options(
        joinedload(models.Employee.role),
        joinedload(models.Employee.location)
    )

    # Фільтрація за локацією для Менеджера
    if current_user.role.role_name == 'Location Manager' or current_user.role.role_name == 'Cashier':
        if not current_user.location_id:
             # Менеджер без локації не може бачити співробітників? Або помилка даних?
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manager's location not set")
        query = query.filter(models.Employee.location_id == current_user.location_id)

    # Пошук
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Employee.first_name.ilike(search_term),
                models.Employee.last_name.ilike(search_term),
                models.Employee.email.ilike(search_term),
                models.Employee.phone_number.ilike(search_term)
            )
        )

    employees = query.order_by(models.Employee.last_name, models.Employee.first_name).offset(skip).all()

    # Перетворюємо результат на схему EmployeeRead
    result = []
    for emp in employees:
         result.append(schemas.EmployeeRead(
             employee_id=emp.employee_id,
             first_name=emp.first_name,
             last_name=emp.last_name,
             phone_number=emp.phone_number,
             email=emp.email,
             role_id=emp.role_id,
             location_id=emp.location_id,
             role_name=emp.role.role_name if emp.role else "N/A",
             location_address=emp.location.address if emp.location else None
             # is_active=emp.is_active # Якщо є поле активності
         ))
    return result

# GET /{employee_id} - Отримати деталі співробітника
@employee_router.get("/{employee_id}", response_model=schemas.EmployeeRead)
async def get_employee_details(
    employee_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    if current_user.role.role_name not in ['Administrator', 'Manager']:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view employee details")

    db_employee = db.query(models.Employee).options(
        joinedload(models.Employee.role),
        joinedload(models.Employee.location)
    ).filter(models.Employee.employee_id == employee_id).first()

    if db_employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Перевірка прав доступу для Менеджера
    if current_user.role.role_name == 'Manager':
        if db_employee.location_id != current_user.location_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to employee details from other locations")

    # Перетворюємо на схему
    return schemas.EmployeeRead(
             employee_id=db_employee.employee_id,
             first_name=db_employee.first_name,
             last_name=db_employee.last_name,
             phone_number=db_employee.phone_number,
             email=db_employee.email,
             role_id=db_employee.role_id,
             location_id=db_employee.location_id,
             role_name=db_employee.role.role_name if db_employee.role else "N/A",
             location_address=db_employee.location.address if db_employee.location else None
             # is_active=db_employee.is_active
         )


# POST / - Створити нового співробітника
@employee_router.post("/", response_model=schemas.EmployeeRead, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee: schemas.EmployeeCreate,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    # Перевірка прав: тільки Admin або Manager
    if current_user.role.role_name not in ['Administrator', 'Manager']:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create employees")

    # Перевірка для Менеджера: може створювати тільки в своїй локації
    if current_user.role.role_name == 'Manager':
        if not current_user.location_id:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Manager's location not set")
        if employee.location_id != current_user.location_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers can only create employees for their own location")
        # Додатково: Менеджер може створювати тільки ролі нижче за себе?
        target_role = db.query(models.Role).filter(models.Role.role_id == employee.role_id).first()
        if not target_role or target_role.role_name in ['Administrator', 'Manager']:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers cannot assign Administrator or Manager roles")

    # Перевірка унікальності email / телефону
    existing_email = db.query(models.Employee).filter(models.Employee.email.ilike(employee.email)).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email {employee.email} already exists.")
    existing_phone = db.query(models.Employee).filter(models.Employee.phone_number == employee.phone_number).first()
    if existing_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Phone number {employee.phone_number} already exists.")

    # Перевірка існування role_id та location_id
    if not db.query(models.Role).filter(models.Role.role_id == employee.role_id).first():
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role with id {employee.role_id} not found.")
    if employee.location_id and not db.query(models.Location).filter(models.Location.location_id == employee.location_id).first():
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Location with id {employee.location_id} not found.")

    employee_data = employee.model_dump(exclude={'password'}) # Виключаємо звичайний пароль
    employee_data['password_hash'] = employee.password

    db_employee = models.Employee(**employee_data)
    try:
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        # Потрібно завантажити зв'язки для відповіді EmployeeRead
        db.refresh(db_employee, attribute_names=['role', 'location'])

        return schemas.EmployeeRead(
             employee_id=db_employee.employee_id,
             first_name=db_employee.first_name,
             last_name=db_employee.last_name,
             phone_number=db_employee.phone_number,
             email=db_employee.email,
             role_id=db_employee.role_id,
             location_id=db_employee.location_id,
             role_name=db_employee.role.role_name if db_employee.role else "N/A",
             location_address=db_employee.location.address if db_employee.location else None
             # is_active=db_employee.is_active
         )
    except Exception as e:
        db.rollback()
        print(f"Error creating employee: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create employee")


# PUT /{employee_id} - Оновити співробітника
@employee_router.put("/{employee_id}", response_model=schemas.EmployeeRead)
async def update_employee(
    employee_id: int,
    employee_data: schemas.EmployeeUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    db_employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if db_employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Перевірка прав доступу (Менеджер може редагувати тільки своїх)
    check_employee_permission(db_employee, current_user)

    update_data = employee_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")

    # Перевірка унікальності при зміні email / телефону
    if 'email' in update_data and update_data['email'].lower() != db_employee.email.lower():
        existing = db.query(models.Employee).filter(models.Employee.email.ilike(update_data['email'])).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Email {update_data['email']} already exists.")
    if 'phone_number' in update_data and update_data['phone_number'] != db_employee.phone_number:
         existing = db.query(models.Employee).filter(models.Employee.phone_number == update_data['phone_number']).first()
         if existing:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Phone number {update_data['phone_number']} already exists.")

     # Перевірка існування role_id / location_id, якщо вони змінюються
    if 'role_id' in update_data:
         new_role = db.query(models.Role).filter(models.Role.role_id == update_data['role_id']).first()
         if not new_role:
              raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role with id {update_data['role_id']} not found.")
         # Заборона Менеджеру підвищувати роль до Admin/Manager?
         if current_user.role.role_name == 'Manager' and new_role.role_name in ['Administrator', 'Manager']:
              raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers cannot assign Administrator or Manager roles")
    if 'location_id' in update_data:
         if update_data['location_id'] and not db.query(models.Location).filter(models.Location.location_id == update_data['location_id']).first():
              raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Location with id {update_data['location_id']} not found.")
          # Заборона Менеджеру змінювати локацію?
         if current_user.role.role_name == 'Manager' and update_data['location_id'] != current_user.location_id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers cannot change employee location")


    # Оновлення пароля
    if 'password' in update_data and update_data['password']:
        hashed_password = oauth2.get_password_hash(update_data['password'])
        db_employee.password_hash = hashed_password
        del update_data['password'] # Видаляємо звичайний пароль

    for key, value in update_data.items():
        setattr(db_employee, key, value)

    try:
        db.commit()
        db.refresh(db_employee)
        # Потрібно завантажити зв'язки для відповіді EmployeeRead
        db.refresh(db_employee, attribute_names=['role', 'location'])

        return schemas.EmployeeRead(
             employee_id=db_employee.employee_id,
             first_name=db_employee.first_name,
             last_name=db_employee.last_name,
             phone_number=db_employee.phone_number,
             email=db_employee.email,
             role_id=db_employee.role_id,
             location_id=db_employee.location_id,
             role_name=db_employee.role.role_name if db_employee.role else "N/A",
             location_address=db_employee.location.address if db_employee.location else None
             # is_active=db_employee.is_active
         )
    except Exception as e:
        db.rollback()
        print(f"Error updating employee {employee_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not update employee")


# DELETE /{employee_id} - Видалити співробітника
@employee_router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.Employee = Depends(oauth2.get_current_user_from_token)
):
    db_employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if db_employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Не можна видалити себе
    if db_employee.employee_id == current_user.employee_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete yourself")

    # Перевірка прав доступу (Менеджер може видаляти тільки своїх і не вищих за рангом)
    check_employee_permission(db_employee, current_user)

    # Додатково: перевірка на пов'язані сутності (наприклад, чи обробляв замовлення)
    # Можливо, краще деактивувати, а не видаляти? (Потрібно додати поле is_active)

    try:
        db.delete(db_employee)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        db.rollback()
        print(f"Error deleting employee {employee_id}: {e}")
        # Перевірка на Foreign Key constraint, якщо співробітник десь використовується
        # if "FOREIGN KEY constraint failed" in str(e):
        #     raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete employee, referenced elsewhere.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not delete employee")