import hashlib
import random
import sys
from datetime import date, datetime, timedelta

from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mssql+pyodbc://localhost\\SQLEXPRESS/BookStoreSystem?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

engine = create_engine(DATABASE_URL, echo=False) # Set echo=True for debugging SQL
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

NUM_AUTHORS = 200
NUM_CATEGORIES = 20
NUM_PUBLISHERS = 50
NUM_LOCATIONS = 15
NUM_EMPLOYEES = 50
NUM_CLIENTS = 1000
NUM_BOOKS = 1000

fake = Faker('en_US')

ROLES_PREDEFINED = ['Administrator', 'Location Manager', 'Cashier']
LOCATION_TYPES = ['bookstore', 'warehouse']

def generate_password_hash(password="password123"):
    return hashlib.sha256(password.encode()).hexdigest()

def get_inserted_ids(session, num_inserted, table_name, id_column_name):
    if num_inserted <= 0:
        return []
    try:
        result = session.execute(text(f"SELECT TOP ({num_inserted}) {id_column_name} FROM {table_name} ORDER BY {id_column_name} DESC"))
        all_inserted_ids = [row[0] for row in result.fetchall()]
        all_inserted_ids.reverse()
        return all_inserted_ids
    except Exception as e:
        print(f"Error retrieving IDs from {table_name}: {e}")
        return []

def generate_roles(session):
    role_ids = {}
    inserted_count = 0
    for role_name in ROLES_PREDEFINED:
        try:
            result = session.execute(text("SELECT role_id FROM Roles WHERE role_name = :role_name"), {'role_name': role_name})
            existing_role = result.fetchone()
            if existing_role:
                role_ids[role_name] = existing_role[0]
            else:
                result = session.execute(
                    text("INSERT INTO Roles (role_name) OUTPUT INSERTED.role_id VALUES (:role_name)"),
                    {'role_name': role_name}
                )
                role_ids[role_name] = result.fetchone()[0]
                inserted_count += 1
        except Exception as e:
            print(f"Error inserting/fetching role '{role_name}': {e}")
            raise
    print(f"Roles prepared/inserted: {len(role_ids)} ({inserted_count} new). IDs: {role_ids}")
    return role_ids

def generate_authors(session, num_records):
    authors_data = []
    for _ in range(num_records):
        authors_data.append({
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'birth_date': fake.date_of_birth(minimum_age=18, maximum_age=90)
        })

    if not authors_data: return []
    try:
        session.execute(
            text("""
                INSERT INTO Authors (first_name, last_name, birth_date)
                VALUES (:first_name, :last_name, :birth_date)
            """),
            authors_data
        )
        session.flush()
        return get_inserted_ids(session, len(authors_data), 'Authors', 'author_id')
    except Exception as e:
        print(f"Database error inserting authors: {e}")
        session.rollback()
        return []

def generate_categories(session, num_records):
    categories_data = []
    category_names = ["Fiction", "Science Fiction", "Mystery", "Historical Fiction", "Children's Books", "Non-fiction", "Business", "Psychology", "Cookbooks", "Art", "Poetry", "Thrillers", "Biographies", "Textbooks", "Comics", "Manga", "Self-Help", "Esotericism", "Travel", "Fantasy"]
    k = min(num_records, len(category_names))
    selected_names = random.sample(category_names, k)

    for name in selected_names:
        categories_data.append({
            'name': name,
            'description': fake.sentence(nb_words=10)
        })

    if len(categories_data) < num_records:
        for _ in range(num_records - len(categories_data)):
             categories_data.append({
                'name': fake.bs().capitalize() + " " + fake.word().capitalize(),
                'description': fake.sentence(nb_words=10)
            })

    if not categories_data: return []
    try:
        session.execute(
            text("""
                INSERT INTO Categories (name, description)
                VALUES (:name, :description)
            """),
            categories_data
        )
        session.flush()
        return get_inserted_ids(session, len(categories_data), 'Categories', 'category_id')
    except Exception as e:
        print(f"Database error inserting categories: {e}")
        session.rollback()
        return []

def generate_publishers(session, num_records):
    publishers_data = []
    fake.unique.clear()
    for _ in range(num_records):
        try:
            email_val = fake.unique.company_email()
        except:
            email_val = f"pub-{fake.user_name()}@example.com"

        publishers_data.append({
            'name': fake.company(),
            'phone_number': fake.phone_number(),
            'email': email_val
        })

    if not publishers_data: return []
    try:
        session.execute(
            text("""
                INSERT INTO Publishers (name, phone_number, email)
                VALUES (:name, :phone_number, :email)
            """),
            publishers_data
        )
        session.flush()
        return get_inserted_ids(session, len(publishers_data), 'Publishers', 'publisher_id')
    except Exception as e:
        print(f"Database error inserting publishers: {e}")
        session.rollback()
        return []

def generate_locations(session, num_records):
    locations_data = []
    for _ in range(num_records):
        locations_data.append({
            'location_type': random.choice(LOCATION_TYPES),
            'address': fake.address(),
            'phone_number': fake.phone_number(),
            'email': fake.company_email() if random.random() > 0.3 else None
        })

    if not locations_data: return []
    try:
        session.execute(
            text("""
                INSERT INTO Locations (location_type, address, phone_number, email)
                VALUES (:location_type, :address, :phone_number, :email)
            """),
            locations_data
        )
        session.flush()
        return get_inserted_ids(session, len(locations_data), 'Locations', 'location_id')
    except Exception as e:
        print(f"Database error inserting locations: {e}")
        session.rollback()
        return []

def generate_employees(session, num_records, role_ids_map, location_ids):
    employees_data = []
    employees_in_memory = [] # Track generated employees before insertion
    fake.unique.clear()
    attempts = 0
    max_attempts = num_records * 2

    admin_id = role_ids_map.get('Administrator')
    manager_id = role_ids_map.get('Location Manager')
    cashier_id = role_ids_map.get('Cashier')

    if not all([admin_id, manager_id, cashier_id]):
        print("Error: Could not find predefined role IDs. Aborting employee generation.")
        return []

    num_admins = 1
    num_managers = max(1, int(num_records * 0.1))
    num_cashiers = num_records - num_admins - num_managers

    available_location_ids = list(location_ids) if location_ids else [None]

    while len(employees_data) < num_records and attempts < max_attempts:
        attempts += 1
        try:
            phone_val = fake.unique.phone_number()
            email_val = fake.unique.email()
        except Exception:
            print(f"Warning: Could not generate unique phone/email on attempt {attempts}.")
            continue

        role_id = cashier_id
        location_id = random.choice(available_location_ids) if available_location_ids != [None] else None

        if len([e for e in employees_in_memory if e['role_id'] == admin_id]) < num_admins:
            role_id = admin_id
            location_id = None
        elif len([e for e in employees_in_memory if e['role_id'] == manager_id]) < num_managers:
            role_id = manager_id
            if not location_id and available_location_ids != [None]:
                 location_id = random.choice(available_location_ids)
        else:
             role_id = cashier_id
             if not location_id and available_location_ids != [None]:
                 location_id = random.choice(available_location_ids)

        if not location_ids:
            location_id = None

        emp_record = {
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'role_id': role_id,
            'location_id': location_id,
            'phone_number': phone_val,
            'email': email_val,
            'password_hash': generate_password_hash(email_val.split('@')[0])
        }
        employees_data.append(emp_record)
        employees_in_memory.append(emp_record) # Add to temporary list

    if len(employees_data) < num_records:
       print(f"Warning: Generated only {len(employees_data)} out of {num_records} employees.")

    if not employees_data:
        print("Error: Failed to generate any employee data.")
        return []

    try:
        session.execute(
            text("""
                INSERT INTO Employees (first_name, last_name, role_id, location_id, phone_number, email, password_hash)
                VALUES (:first_name, :last_name, :role_id, :location_id, :phone_number, :email, :password_hash)
            """),
            employees_data
        )
        session.flush()
        return get_inserted_ids(session, len(employees_data), 'Employees', 'employee_id')
    except Exception as e:
        print(f"Database error inserting employees: {e}")
        session.rollback()
        return []

def generate_clients(session, num_records):
    clients_data = []
    fake.unique.clear()
    attempts = 0
    max_attempts = num_records * 2

    while len(clients_data) < num_records and attempts < max_attempts:
        attempts += 1
        try:
            phone_val = fake.unique.phone_number()
            email_val = fake.unique.email()
        except Exception:
            print(f"Warning: Could not generate unique phone/email for client on attempt {attempts}.")
            continue

        clients_data.append({
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'phone_number': phone_val,
            'email': email_val,
            'password_hash': generate_password_hash(email_val.split('@')[0]) if random.random() > 0.7 else None
        })

    if len(clients_data) < num_records:
        print(f"Warning: Generated only {len(clients_data)} out of {num_records} clients.")

    if not clients_data:
        print("Error: Failed to generate any client data.")
        return []

    try:
        session.execute(
            text("""
                INSERT INTO Clients (first_name, last_name, phone_number, email, password_hash)
                VALUES (:first_name, :last_name, :phone_number, :email, :password_hash)
            """),
            clients_data
        )
        session.flush()
        return get_inserted_ids(session, len(clients_data), 'Clients', 'client_id')
    except Exception as e:
        print(f"Database error inserting clients: {e}")
        session.rollback()
        return []

def generate_books(session, num_records, author_ids, category_ids, publisher_ids):
    if not author_ids or not category_ids or not publisher_ids:
        print("Error: Missing author, category, or publisher IDs. Cannot generate books.")
        return []

    books_data = []
    current_year = date.today().year
    for _ in range(num_records):
        title_part1 = fake.catch_phrase()
        title_part2 = fake.bs()
        title = f"{title_part1}: {title_part2}" if random.random() > 0.5 else fake.sentence(nb_words=random.randint(3, 7)).replace('.', '')
        title = title[:255]

        books_data.append({
            'title': title,
            'author_id': random.choice(author_ids),
            'category_id': random.choice(category_ids),
            'publisher_id': random.choice(publisher_ids),
            'publication_year': random.randint(1450, current_year),
            'description': fake.text(max_nb_chars=500) if random.random() > 0.2 else None,
            'price': round(random.uniform(5.0, 200.0), 2),
            'discount_percentage': round(random.uniform(0.0, 30.0), 2) if random.random() > 0.6 else 0.00
        })

    if not books_data: return []
    try:
        session.execute(
            text("""
                INSERT INTO Books (title, author_id, category_id, publisher_id, publication_year, description, price, discount_percentage)
                VALUES (:title, :author_id, :category_id, :publisher_id, :publication_year, :description, :price, :discount_percentage)
            """),
            books_data
        )
        session.flush()
        return get_inserted_ids(session, len(books_data), 'Books', 'book_id')
    except Exception as e:
        print(f"Database error inserting books: {e}")
        session.rollback()
        return []


# --- Main Execution Logic ---
session = None
all_successful = True

try:
    print(f"Connecting to database using SQLAlchemy: {DATABASE_URL}...")
    session = SessionLocal()
    print("Connection successful. Starting data generation...")

    print("\n--- Generating Roles ---")
    role_ids_map = generate_roles(session)
    if not role_ids_map or len(role_ids_map) < len(ROLES_PREDEFINED):
         all_successful = False
         raise Exception("Critical error: Failed to prepare roles.")

    print(f"\n--- Generating {NUM_AUTHORS} Authors ---")
    author_ids = generate_authors(session, NUM_AUTHORS)
    if not author_ids and NUM_AUTHORS > 0: all_successful = False; print("Warning: Failed to generate authors.")
    print(f"Generated {len(author_ids)} authors.")

    print(f"\n--- Generating {NUM_CATEGORIES} Categories ---")
    category_ids = generate_categories(session, NUM_CATEGORIES)
    if not category_ids and NUM_CATEGORIES > 0: all_successful = False; print("Warning: Failed to generate categories.")
    print(f"Generated {len(category_ids)} categories.")

    print(f"\n--- Generating {NUM_PUBLISHERS} Publishers ---")
    publisher_ids = generate_publishers(session, NUM_PUBLISHERS)
    if not publisher_ids and NUM_PUBLISHERS > 0: all_successful = False; print("Warning: Failed to generate publishers.")
    print(f"Generated {len(publisher_ids)} publishers.")

    print(f"\n--- Generating {NUM_LOCATIONS} Locations ---")
    location_ids = generate_locations(session, NUM_LOCATIONS)
    if not location_ids and NUM_LOCATIONS > 0: all_successful = False; print("Warning: Failed to generate locations.")
    print(f"Generated {len(location_ids)} locations.")

    print(f"\n--- Generating {NUM_EMPLOYEES} Employees ---")
    employee_ids = generate_employees(session, NUM_EMPLOYEES, role_ids_map, location_ids)
    if not employee_ids and NUM_EMPLOYEES > 0:
        all_successful = False
        raise Exception("Critical error: Failed to generate employees.")
    print(f"Generated {len(employee_ids)} employees.")

    print(f"\n--- Generating {NUM_CLIENTS} Clients ---")
    client_ids = generate_clients(session, NUM_CLIENTS)
    if not client_ids and NUM_CLIENTS > 0:
         all_successful = False
         print("Warning: Failed to generate clients.")
    print(f"Generated {len(client_ids)} clients.")

    print(f"\n--- Generating {NUM_BOOKS} Books ---")
    if author_ids and category_ids and publisher_ids:
        book_ids = generate_books(session, NUM_BOOKS, author_ids, category_ids, publisher_ids)
        if not book_ids and NUM_BOOKS > 0: all_successful = False; print("Warning: Failed to generate books.")
        print(f"Generated {len(book_ids)} books.")
    else:
        print("Skipping book generation due to missing prerequisite IDs (authors, categories, or publishers).")


    # --- Final Commit/Rollback ---
    if all_successful:
        print("\nAll generation steps attempted. Committing transaction...")
        session.commit()
        print("\nData generation completed successfully!")
    else:
        print("\nErrors or critical warnings occurred during generation. Rolling back transaction...")
        session.rollback()
        print("Changes were not saved to the database.")


except Exception as e:
    print(f"\n!!! An unexpected error occurred: {e} !!!")
    import traceback
    traceback.print_exc()
    if session:
        print("Rolling back transaction due to error...")
        session.rollback()
    all_successful = False
finally:
    if session:
        session.close()
        print("\nDatabase session closed.")

if not all_successful:
     sys.exit(1)
