import pyodbc
from faker import Faker
import random
from datetime import datetime, date, time
import hashlib
import sys

DB_SERVER = 'YOUR_SERVER_NAME' # Замініть на ім'я вашого сервера
DB_DATABASE = 'BookStoreSystem'
DB_DRIVER = '{ODBC Driver 17 for SQL Server}' # Або інший драйвер

NUM_AUTHORS = 200
NUM_CATEGORIES = 20
NUM_PUBLISHERS = 50
NUM_LOCATIONS = 15
NUM_EMPLOYEES = 50
NUM_CLIENTS = 1000
NUM_BOOKS = 1000

fake = Faker('uk_UA')

ROLES_PREDEFINED = ['Administrator', 'Location Manager', 'Cashier']
LOCATION_TYPES = ['bookstore', 'warehouse']

def generate_password_hash(password="password123"):
    return hashlib.sha256(password.encode()).hexdigest()

def get_inserted_ids(cursor, num_inserted, table_name, id_column_name):
    if num_inserted <= 0:
        return []
    try:
        cursor.execute(f"SELECT TOP ({num_inserted}) {id_column_name} FROM {table_name} ORDER BY {id_column_name} DESC")
        all_inserted_ids = [row[0] for row in cursor.fetchall()]
        all_inserted_ids.reverse()
        return all_inserted_ids
    except pyodbc.Error as e:
        print(f"Error retrieving IDs from {table_name}: {e}")
        return []

def generate_roles(cursor):
    role_ids = {}
    inserted_count = 0
    for role_name in ROLES_PREDEFINED:
        try:
            cursor.execute("SELECT role_id FROM Roles WHERE role_name = ?", (role_name,))
            existing_role = cursor.fetchone()
            if existing_role:
                role_ids[role_name] = existing_role.role_id
            else:
                cursor.execute("INSERT INTO Roles (role_name) OUTPUT INSERTED.role_id VALUES (?)", (role_name,))
                role_ids[role_name] = cursor.fetchone().role_id
                inserted_count += 1
        except pyodbc.Error as e:
            print(f"Error inserting/fetching role '{role_name}': {e}")
            raise
    print(f"Roles prepared/inserted: {len(role_ids)} ({inserted_count} new). IDs: {role_ids}")
    return role_ids

def generate_authors(cursor, num_records):
    authors = []
    for _ in range(num_records):
        first_name = fake.first_name()
        last_name = fake.last_name()
        birth_date = fake.date_of_birth(minimum_age=18, maximum_age=90)
        authors.append((first_name, last_name, birth_date))

    if not authors: return []
    try:
        cursor.executemany("""
            INSERT INTO Authors (first_name, last_name, birth_date)
            VALUES (?, ?, ?)
        """, authors)
        return get_inserted_ids(cursor, len(authors), 'Authors', 'author_id')
    except pyodbc.Error as e:
        print(f"Database error inserting authors: {e}")
        conn.rollback()
        return []

def generate_categories(cursor, num_records):
    categories = []
    category_names = ["Художня література", "Наукова фантастика", "Детективи", "Історичні романи", "Дитячі книги", "Науково-популярна", "Бізнес-література", "Психологія", "Кулінарія", "Мистецтво", "Поезія", "Трилери", "Біографії", "Підручники", "Комікси", "Манга", "Саморозвиток", "Езотерика", "Подорожі", "Фентезі"]
    k = min(num_records, len(category_names))
    selected_names = random.sample(category_names, k)

    for name in selected_names:
        description = fake.sentence(nb_words=10)
        categories.append((name, description))

    if len(categories) < num_records:
        for _ in range(num_records - len(categories)):
            name = fake.bs().capitalize() + " " + fake.word().capitalize()
            description = fake.sentence(nb_words=10)
            categories.append((name, description))


    if not categories: return []
    try:
        cursor.executemany("""
            INSERT INTO Categories (name, description)
            VALUES (?, ?)
        """, categories)
        return get_inserted_ids(cursor, len(categories), 'Categories', 'category_id')
    except pyodbc.Error as e:
        print(f"Database error inserting categories: {e}")
        conn.rollback()
        return []

def generate_publishers(cursor, num_records):
    publishers = []
    fake.unique.clear()
    for _ in range(num_records):
        name = fake.company()
        phone = fake.phone_number()
        try:
            email = fake.unique.company_email()
        except:
            email = f"pub-{fake.user_name()}@example.com"
        publishers.append((name, phone, email))

    if not publishers: return []
    try:
        cursor.executemany("""
            INSERT INTO Publishers (name, phone_number, email)
            VALUES (?, ?, ?)
        """, publishers)
        return get_inserted_ids(cursor, len(publishers), 'Publishers', 'publisher_id')
    except pyodbc.Error as e:
        print(f"Database error inserting publishers: {e}")
        conn.rollback()
        return []

def generate_locations(cursor, num_records):
    locations = []
    for _ in range(num_records):
        location_type = random.choice(LOCATION_TYPES)
        address = fake.address()
        phone = fake.phone_number()
        email = fake.company_email() if random.random() > 0.3 else None
        locations.append((location_type, address, phone, email))

    if not locations: return []
    try:
        cursor.executemany("""
            INSERT INTO Locations (location_type, address, phone_number, email)
            VALUES (?, ?, ?, ?)
        """, locations)
        return get_inserted_ids(cursor, len(locations), 'Locations', 'location_id')
    except pyodbc.Error as e:
        print(f"Database error inserting locations: {e}")
        conn.rollback()
        return []

def generate_employees(cursor, num_records, role_ids_map, location_ids):
    employees = []
    fake.unique.clear()
    attempts = 0
    max_attempts = num_records * 2

    admin_id = role_ids_map.get('Administrator')
    manager_id = role_ids_map.get('Location Manager')
    cashier_id = role_ids_map.get('Cashier')

    num_admins = 1
    num_managers = max(1, int(num_records * 0.1))
    num_cashiers = num_records - num_admins - num_managers

    available_location_ids = list(location_ids) if location_ids else [None]

    while len(employees) < num_records and attempts < max_attempts:
        attempts += 1
        first_name = fake.first_name()
        last_name = fake.last_name()

        try:
            phone_number = fake.unique.phone_number()
            email = fake.unique.email()
        except Exception:
            print(f"Warning: Could not generate unique phone/email on attempt {attempts}.")
            continue

        password_hash = generate_password_hash(email.split('@')[0]) # Use part of email for demo password

        role_id = cashier_id # Default
        location_id = random.choice(available_location_ids) if available_location_ids != [None] else None

        if len([e for e in employees if e[2] == admin_id]) < num_admins:
            role_id = admin_id
            location_id = None # Admins might not be tied to a specific location
        elif len([e for e in employees if e[2] == manager_id]) < num_managers:
            role_id = manager_id
            if not location_id and available_location_ids != [None]: # Ensure manager has a location
                 location_id = random.choice(available_location_ids)
        else: # Assign Cashier
             role_id = cashier_id
             if not location_id and available_location_ids != [None]: # Ensure cashier has a location
                 location_id = random.choice(available_location_ids)

        # Ensure location_id is None if no locations were generated
        if not location_ids:
            location_id = None


        employees.append((first_name, last_name, role_id, location_id, phone_number, email, password_hash))

    if len(employees) < num_records:
       print(f"Warning: Generated only {len(employees)} out of {num_records} employees.")

    if not employees:
        print("Error: Failed to generate any employee data.")
        return []

    try:
        cursor.executemany("""
            INSERT INTO Employees (first_name, last_name, role_id, location_id, phone_number, email, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, employees)
        return get_inserted_ids(cursor, len(employees), 'Employees', 'employee_id')
    except pyodbc.IntegrityError as e:
        print(f"Integrity error inserting employees: {e}")
        conn.rollback()
        return []
    except pyodbc.Error as e:
        print(f"Database error inserting employees: {e}")
        conn.rollback()
        return []


def generate_clients(cursor, num_records):
    clients = []
    fake.unique.clear()
    attempts = 0
    max_attempts = num_records * 2

    while len(clients) < num_records and attempts < max_attempts:
        attempts += 1
        first_name = fake.first_name()
        last_name = fake.last_name()
        try:
            phone_number = fake.unique.phone_number()
            email = fake.unique.email()
        except Exception:
            print(f"Warning: Could not generate unique phone/email for client on attempt {attempts}.")
            continue

        password_hash = generate_password_hash(email.split('@')[0]) if random.random() > 0.7 else None # Some clients might not have passwords

        clients.append((first_name, last_name, phone_number, email, password_hash))

    if len(clients) < num_records:
        print(f"Warning: Generated only {len(clients)} out of {num_records} clients.")

    if not clients:
        print("Error: Failed to generate any client data.")
        return []

    try:
        cursor.executemany("""
            INSERT INTO Clients (first_name, last_name, phone_number, email, password_hash)
            VALUES (?, ?, ?, ?, ?)
        """, clients)
        return get_inserted_ids(cursor, len(clients), 'Clients', 'client_id')
    except pyodbc.IntegrityError as e:
        print(f"Integrity error inserting clients: {e}")
        conn.rollback()
        return []
    except pyodbc.Error as e:
        print(f"Database error inserting clients: {e}")
        conn.rollback()
        return []

def generate_books(cursor, num_records, author_ids, category_ids, publisher_ids):
    if not author_ids or not category_ids or not publisher_ids:
        print("Error: Missing author, category, or publisher IDs. Cannot generate books.")
        return []

    books = []
    current_year = date.today().year
    for _ in range(num_records):
        title = ' '.join(fake.words(nb=random.randint(2, 6))).capitalize()
        author_id = random.choice(author_ids)
        category_id = random.choice(category_ids)
        publisher_id = random.choice(publisher_ids)
        publication_year = random.randint(1950, current_year)
        description = fake.text(max_nb_chars=500) if random.random() > 0.2 else None
        price = round(random.uniform(50.0, 1500.0), 2)
        discount = round(random.uniform(0.0, 30.0), 2) if random.random() > 0.6 else 0.00

        books.append((title, author_id, category_id, publisher_id, publication_year, description, price, discount))

    if not books: return []
    try:
        cursor.executemany("""
            INSERT INTO Books (title, author_id, category_id, publisher_id, publication_year, description, price, discount_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, books)
        return get_inserted_ids(cursor, len(books), 'Books', 'book_id')
    except pyodbc.Error as e:
        print(f"Database error inserting books: {e}")
        conn.rollback()
        return []


conn = None
all_successful = True

try:
    connection_string = (
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"Trusted_Connection=yes;"
    )
    print(f"Connecting to: SERVER={DB_SERVER}, DATABASE={DB_DATABASE}...")
    conn = pyodbc.connect(connection_string, autocommit=False)
    cursor = conn.cursor()
    print("Connection successful.")

    print("\n--- Generating Roles ---")
    role_ids_map = generate_roles(cursor)
    if not role_ids_map or len(role_ids_map) != len(ROLES_PREDEFINED):
         all_successful = False
         raise Exception("Critical error: Failed to prepare roles.")

    print(f"\n--- Generating {NUM_AUTHORS} Authors ---")
    author_ids = generate_authors(cursor, NUM_AUTHORS)
    if not author_ids and NUM_AUTHORS > 0: all_successful = False; print("Warning: Failed to generate authors.")
    print(f"Generated {len(author_ids)} authors.")

    print(f"\n--- Generating {NUM_CATEGORIES} Categories ---")
    category_ids = generate_categories(cursor, NUM_CATEGORIES)
    if not category_ids and NUM_CATEGORIES > 0: all_successful = False; print("Warning: Failed to generate categories.")
    print(f"Generated {len(category_ids)} categories.")

    print(f"\n--- Generating {NUM_PUBLISHERS} Publishers ---")
    publisher_ids = generate_publishers(cursor, NUM_PUBLISHERS)
    if not publisher_ids and NUM_PUBLISHERS > 0: all_successful = False; print("Warning: Failed to generate publishers.")
    print(f"Generated {len(publisher_ids)} publishers.")

    print(f"\n--- Generating {NUM_LOCATIONS} Locations ---")
    location_ids = generate_locations(cursor, NUM_LOCATIONS)
    if not location_ids and NUM_LOCATIONS > 0: all_successful = False; print("Warning: Failed to generate locations.")
    print(f"Generated {len(location_ids)} locations.")

    print(f"\n--- Generating {NUM_EMPLOYEES} Employees ---")
    employee_ids = generate_employees(cursor, NUM_EMPLOYEES, role_ids_map, location_ids)
    if not employee_ids and NUM_EMPLOYEES > 0:
        all_successful = False
        raise Exception("Critical error: Failed to generate employees.")
    print(f"Generated {len(employee_ids)} employees.")

    print(f"\n--- Generating {NUM_CLIENTS} Clients ---")
    client_ids = generate_clients(cursor, NUM_CLIENTS)
    if not client_ids and NUM_CLIENTS > 0:
         all_successful = False
         print("Warning: Failed to generate clients.")
    print(f"Generated {len(client_ids)} clients.")

    print(f"\n--- Generating {NUM_BOOKS} Books ---")
    if author_ids and category_ids and publisher_ids:
        book_ids = generate_books(cursor, NUM_BOOKS, author_ids, category_ids, publisher_ids)
        if not book_ids and NUM_BOOKS > 0: all_successful = False; print("Warning: Failed to generate books.")
        print(f"Generated {len(book_ids)} books.")
    else:
        print("Skipping book generation due to missing prerequisite IDs.")


    if all_successful:
        print("\nAll generation steps attempted. Committing transaction...")
        conn.commit()
        print("\nData generation completed successfully!")
    else:
        print("\nErrors or critical warnings occurred during generation. Rolling back transaction...")
        conn.rollback()
        print("Changes were not saved to the database.")


except pyodbc.Error as ex:
    sqlstate = ex.args[0] if len(ex.args) > 0 else 'N/A'
    print(f"\n!!! Database Error (pyodbc): SQLSTATE={sqlstate} !!!")
    print(ex)
    if conn:
        print("Rolling back transaction...")
        conn.rollback()
    all_successful = False
except Exception as e:
    print(f"\n!!! An unexpected Python error occurred: {e} !!!")
    import traceback
    traceback.print_exc()
    if conn:
        print("Rolling back transaction...")
        conn.rollback()
    all_successful = False
finally:
    if conn:
        conn.close()
        print("\nDatabase connection closed.")

if not all_successful:
     sys.exit(1)
