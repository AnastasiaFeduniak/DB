from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, ColumnProperty
from sqlalchemy.inspection import inspect as sqlalchemy_inspect # Для отримання імен стовпців
import database, models, oauth2
import io
import csv
import zipfile # Стандартна бібліотека для роботи з zip
from fastapi.responses import StreamingResponse, JSONResponse
from decimal import Decimal # Для коректної обробки Decimal
from datetime import date, datetime, time 
from dependencies import get_current_admin_user
import pandas as pd 
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
export_router = APIRouter(
    prefix="/api/v1/export",
    tags=['Export']
)


current_dir = os.path.dirname(os.path.abspath(__file__))

FONT_PATH_NORMAL = os.path.join(current_dir, 'dejavusans.ttf')
FONT_PATH_BOLD = os.path.join(current_dir, 'dejavusansbold.ttf')
FONT_NAME_NORMAL = 'DejaVuSans'
FONT_NAME_BOLD = 'DejaVuSans-Bold'


if not os.path.exists(FONT_PATH_NORMAL):
    print(f"ПОМИЛКА: Файл шрифту НЕ ЗНАЙДЕНО: {FONT_PATH_NORMAL}")
    # Можна викинути помилку або використати резервний варіант
    # raise FileNotFoundError(f"Font file not found: {FONT_PATH_NORMAL}")
if not os.path.exists(FONT_PATH_BOLD):
     print(f"ПОМИЛКА: Файл жирного шрифту НЕ ЗНАЙДЕНО: {FONT_PATH_BOLD}")
     # raise FileNotFoundError(f"Bold font file not found: {FONT_PATH_BOLD}")
try:
    # Реєструємо звичайний та жирний варіанти
    if os.path.exists(FONT_PATH_NORMAL):
        pdfmetrics.registerFont(TTFont(FONT_NAME_NORMAL, FONT_PATH_NORMAL))
    if os.path.exists(FONT_PATH_BOLD):
         pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, FONT_PATH_BOLD))
         # Пов'язуємо жирний шрифт з тегом <b> для основного шрифту
         if os.path.exists(FONT_PATH_NORMAL):
             pdfmetrics.registerFontFamily(FONT_NAME_NORMAL, normal=FONT_NAME_NORMAL, bold=FONT_NAME_BOLD, italic=None, boldItalic=None) # Припускаємо, що немає italic
         else: # Якщо немає звичайного, реєструємо тільки жирний
             pdfmetrics.registerFontFamily(FONT_NAME_BOLD, normal=FONT_NAME_BOLD) # Вказуємо жирний як 'normal' для цього сімейства

    print(f"Шрифти зареєстровані: Normal='{FONT_NAME_NORMAL}', Bold='{FONT_NAME_BOLD}'")

except Exception as font_error:
     print(f"ПОМИЛКА РЕЄСТРАЦІЇ ШРИФТУ: {font_error}")

@export_router.get("/full_database/zip")
async def export_full_database_zip(
    db: Session = Depends(database.get_db),
    current_admin: models.Employee = Depends(get_current_admin_user) # Захист ендпоінта
):
    """
    Експортує дані з усіх визначених таблиць у окремі CSV-файли,
    запаковані в один ZIP-архів.
    УВАГА: Може бути ресурсоємно для великих баз даних!
    """

    # Список моделей для експорту (визначте тут всі моделі з models.py)
    # Це надійніше, ніж намагатися автоматично знайти всі підкласи Base
    MODELS_TO_EXPORT = [
        models.Role,
        models.Location,
        models.Employee,
        models.Author,
        models.Category,
        models.Publisher,
        models.Book,
        models.Client,
        models.Order,
        models.BookAmountOrder,
        models.BookAmountLocation,
        models.WorkingHours,
        # Додайте сюди будь-які інші ваші моделі...
    ]

    # Створюємо буфер в пам'яті для zip-файлу
    zip_buffer = io.BytesIO()

    try:
        # Створюємо ZipFile для запису в буфер
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for model in MODELS_TO_EXPORT:
                table_name = model.__tablename__
                print(f"Exporting table: {table_name}") # Логування прогресу

                # Створюємо буфер для CSV-файлу поточної таблиці
                csv_output = io.StringIO()
                csv_writer = csv.writer(csv_output)

                try:
                    # Отримуємо інспектор моделі для доступу до стовпців
                    mapper = sqlalchemy_inspect(model)
                    column_names = []
                    # Фільтруємо, щоб отримати тільки реальні стовпці таблиці, а не relationships
                    for prop in mapper.iterate_properties:
                        if isinstance(prop, ColumnProperty):
                             # Перевіряємо, чи є у властивості вираз (тобто це стовпець)
                            if hasattr(prop.expression, 'key'):
                                column_key = prop.expression.key
                                # !!! ВАЖЛИВО: Пропускаємо чутливі стовпці !!!
                                if column_key.lower() == 'password_hash':
                                     print(f"  Skipping sensitive column: {column_key}")
                                     continue
                                column_names.append(column_key)
                            else:
                                print(f"  Skipping property without expression key: {prop}")


                    if not column_names:
                        print(f"  No columns found for table {table_name}. Skipping.")
                        continue

                    # Записуємо заголовки
                    csv_writer.writerow(column_names)

                    # Отримуємо всі дані з таблиці
                    # УВАГА: Для дуже великих таблиць краще використовувати потокову обробку (yield_per),
                    # але для простоти тут завантажуємо все одразу.
                    table_data = db.query(model).all()

                    # Записуємо дані
                    for row_obj in table_data:
                        row_values = []
                        for col_name in column_names:
                            value = getattr(row_obj, col_name, None)
                            # Обробка специфічних типів для CSV
                            if isinstance(value, Decimal):
                                value = float(value) # Конвертуємо Decimal у float
                            elif isinstance(value, (datetime, date, time)):
                                value = value.isoformat() # Конвертуємо дати/час у ISO формат
                            elif isinstance(value, bool):
                                value = str(value) # Конвертуємо bool у рядок
                            # Додайте іншу необхідну обробку типів тут
                            row_values.append(value)
                        csv_writer.writerow(row_values)

                    # Отримуємо вміст CSV як рядок і додаємо в zip-архів
                    csv_output.seek(0)
                    # Використовуємо ім'я таблиці як ім'я файлу всередині архіву
                    zip_file.writestr(f"{table_name}.csv", csv_output.getvalue())
                    print(f"  Successfully added {table_name}.csv to archive.")

                except Exception as table_error:
                    print(f"  Error processing table {table_name}: {table_error}")
                    # Можна записати файл з помилкою в архів або просто пропустити
                    error_message = f"Error exporting table {table_name}: {table_error}"
                    zip_file.writestr(f"{table_name}_ERROR.txt", error_message)

    except Exception as zip_error:
        print(f"Error creating zip archive: {zip_error}")
        # Якщо помилка на рівні створення zip, повертаємо помилку сервера
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create zip archive: {zip_error}"
        )

    # Переміщуємо вказівник на початок буфера zip-файлу
    zip_buffer.seek(0)

    # Повертаємо zip-архів як відповідь
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        }
    )

@export_router.get("/full_database/excel")
async def export_full_database_excel(
    db: Session = Depends(database.get_db),
    current_admin: models.Employee = Depends(get_current_admin_user) # Захист ендпоінта
):
    """
    Експортує дані з усіх визначених таблиць у один Excel (.xlsx) файл,
    де кожна таблиця знаходиться на окремому аркуші.
    УВАГА: Може бути ресурсоємно для великих баз даних!
    """

    # Список моделей для експорту (той самий, що й для ZIP)
    MODELS_TO_EXPORT = [
        models.Role, models.Location, models.Employee, models.Author, models.Category,
        models.Publisher, models.Book, models.Client, models.Order,
        models.BookAmountOrder, models.BookAmountLocation, models.WorkingHours,
        # Додайте інші ваші моделі...
    ]

    # Створюємо буфер в пам'яті для Excel-файлу
    excel_buffer = io.BytesIO()

    try:
        # Використовуємо pandas ExcelWriter для запису на різні аркуші
        # engine='openpyxl' - використовуємо бібліотеку openpyxl
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            for model in MODELS_TO_EXPORT:
                table_name = model.__tablename__
                 # Обмеження Excel на довжину імені аркуша (31 символ)
                sheet_name = table_name[:31]
                print(f"Exporting table: {table_name} to sheet: {sheet_name}")

                try:
                    # --- Отримання даних за допомогою pandas.read_sql ---
                    # Це ефективніше, ніж db.query(model).all() для pandas
                    query = db.query(model)
                    df = pd.read_sql(query.statement, db.bind)

                    # --- !!! ВАЖЛИВО: Видаляємо чутливі стовпці !!! ---
                    columns_to_drop = ['password_hash'] # Додайте інші чутливі стовпці
                    for col in columns_to_drop:
                        if col in df.columns:
                            df = df.drop(columns=[col])
                            print(f"  Dropped sensitive column: {col}")

                    if df.empty and not query.column_descriptions:
                         print(f"  Skipping empty table with no columns defined in query: {table_name}")
                         continue # Пропускаємо, якщо таблиця порожня і немає опису стовпців
                    elif df.empty:
                         print(f"  Table {table_name} is empty, writing headers only.")
                         # Якщо таблиця пуста, але стовпці є, створимо пустий DataFrame з правильними заголовками
                         mapper = sqlalchemy_inspect(model)
                         column_names = []
                         for prop in mapper.iterate_properties:
                              if isinstance(prop, ColumnProperty) and hasattr(prop.expression, 'key'):
                                   column_key = prop.expression.key
                                   if column_key.lower() not in [c.lower() for c in columns_to_drop]: # Перевірка, чи не чутливий
                                        column_names.append(column_key)
                         df = pd.DataFrame(columns=column_names) # Створюємо DataFrame лише з заголовками

                    # --- Запис DataFrame на аркуш Excel ---
                    # index=False - не записувати індекс DataFrame як стовпець в Excel
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"  Successfully wrote {table_name} to sheet {sheet_name}.")

                except Exception as table_error:
                    print(f"  Error processing table {table_name} for Excel: {table_error}")
                    # Можна створити аркуш з повідомленням про помилку
                    error_df = pd.DataFrame({'Error': [f"Could not export table {table_name}: {table_error}"]})
                    error_df.to_excel(writer, sheet_name=f"{sheet_name}_ERROR", index=False)

        # ExcelWriter автоматично зберігає файл у буфер при виході з блоку 'with'

    except Exception as excel_error:
        print(f"Error creating Excel file: {excel_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create Excel file: {excel_error}"
        )

    # Переміщуємо вказівник на початок буфера Excel-файлу
    excel_buffer.seek(0)

    # Повертаємо Excel-файл як відповідь
    return StreamingResponse(
        excel_buffer,
        # Правильний media type для .xlsx файлів
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        }
    )

def json_converter(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    elif isinstance(value, Decimal):
        # Конвертуємо Decimal у float або string на ваш вибір
        # float може мати проблеми з точністю, string безпечніший
        return str(value)
        # return float(value)
    # Можна додати обробку інших типів тут
    return value


@export_router.get("/full_database/json", response_class=JSONResponse)
async def export_full_database_json(
    db: Session = Depends(database.get_db),
    current_admin: models.Employee = Depends(get_current_admin_user) # Захист ендпоінта
):
    """
    Експортує дані з усіх визначених таблиць у один JSON файл.
    Структура: { "table_name": [ {row_data}, ... ], ... }
    УВАГА: Може бути ресурсоємно для великих баз даних!
    """

    # Список моделей для експорту (той самий)
    MODELS_TO_EXPORT = [
        models.Role, models.Location, models.Employee, models.Author, models.Category,
        models.Publisher, models.Book, models.Client, models.Order,
        models.BookAmountOrder, models.BookAmountLocation, models.WorkingHours,
        # Додайте інші ваші моделі...
    ]

    full_export_data = {} # Словник для зберігання даних усіх таблиць

    try:
        for model in MODELS_TO_EXPORT:
            table_name = model.__tablename__
            print(f"Exporting table: {table_name} for JSON")

            try:
                # Отримуємо інспектор моделі
                mapper = sqlalchemy_inspect(model)
                column_names = []
                 # Фільтруємо стовпці
                for prop in mapper.iterate_properties:
                    if isinstance(prop, ColumnProperty) and hasattr(prop.expression, 'key'):
                        column_key = prop.expression.key
                        # !!! Пропускаємо чутливі стовпці !!!
                        if column_key.lower() == 'password_hash':
                             print(f"  Skipping sensitive column: {column_key}")
                             continue
                        column_names.append(column_key)

                if not column_names:
                    print(f"  No columns found for table {table_name}. Skipping.")
                    continue

                # Запитуємо дані з бази
                table_data_query = db.query(model).all()

                table_rows_list = []
                for row_obj in table_data_query:
                    row_dict = {}
                    for col_name in column_names:
                        value = getattr(row_obj, col_name, None)
                        # Конвертуємо значення у JSON-сумісний формат
                        row_dict[col_name] = json_converter(value)
                    table_rows_list.append(row_dict)

                # Додаємо дані таблиці до загального словника
                full_export_data[table_name] = table_rows_list
                print(f"  Successfully processed {table_name} for JSON export.")

            except Exception as table_error:
                 print(f"  Error processing table {table_name} for JSON: {table_error}")
                 # Записуємо інформацію про помилку в JSON
                 full_export_data[f"{table_name}_ERROR"] = f"Could not export table: {table_error}"

    except Exception as export_error:
        print(f"Error during JSON export process: {export_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not process database for JSON export: {export_error}"
        )

    # Створюємо JSON відповідь. JSONResponse автоматично серіалізує словник.
    # json.dumps не потрібен напряму, але може бути корисний для логування
    # print(json.dumps(full_export_data, indent=4)) # Для відладки

    return JSONResponse(
        content=full_export_data,
        headers={
            # Цей заголовок підкаже браузеру завантажити файл
            "Content-Disposition": f"attachment; filename=database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )

@export_router.get("/full_database/pdf")
async def export_full_database_pdf(
    db: Session = Depends(database.get_db),
    current_admin: models.Employee = Depends(get_current_admin_user)
):
    """
    Експортує дані у PDF з підтримкою кирилиці (використовує DejaVuSans).
    """
    MODELS_TO_EXPORT = [
        models.Role, models.Location, models.Employee, models.Author, models.Category,
        models.Publisher, models.Book, models.Client, models.Order,
        models.BookAmountOrder, models.BookAmountLocation, models.WorkingHours,
    ]

    pdf_buffer = io.BytesIO()

    try:
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                               leftMargin=0.5*inch, rightMargin=0.5*inch,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)

        # --- Налаштування стилів з новим шрифтом ---
        styles = getSampleStyleSheet()
        # Створюємо копії стандартних стилів і змінюємо шрифт
        # Перевіряємо, чи шрифт було зареєстровано
        registered_normal_font = FONT_NAME_NORMAL if pdfmetrics.getFont(FONT_NAME_NORMAL) else 'Helvetica'
        registered_bold_font = FONT_NAME_BOLD if pdfmetrics.getFont(FONT_NAME_BOLD) else 'Helvetica-Bold'

        style_normal = ParagraphStyle(
            name='MyNormal',
            parent=styles['Normal'],
            fontName=registered_normal_font, # Встановлюємо наш шрифт
            fontSize=9, # Зменшимо розмір для таблиць
            leading=11 # Міжрядковий інтервал
        )
        style_h1 = ParagraphStyle(
            name='MyH1',
            parent=styles['h1'],
            fontName=registered_bold_font, # Використовуємо жирний
            alignment=1 # CENTER
        )
        style_h2 = ParagraphStyle(
            name='MyH2',
            parent=styles['h2'],
            fontName=registered_bold_font # Використовуємо жирний
        )
        style_italic = ParagraphStyle( # Якщо потрібен курсив, треба реєструвати italic шрифт
             name='MyItalic',
             parent=styles['Italic'],
             fontName=registered_normal_font # Або назву курсивного шрифту, якщо є
        )
        style_header = ParagraphStyle( # Стиль для заголовків таблиці
             name='TableHeader',
             parent=style_normal,
             fontName=registered_bold_font # Жирний шрифт для заголовків
        )
        # --- Кінець налаштування стилів ---

        story = []

        title = "Повний експорт бази даних BookWorld"
        story.append(Paragraph(title, style_h1)) # Використовуємо новий стиль
        story.append(Spacer(1, 0.2*inch))

    except Exception as doc_error:
         print(f"Error initializing PDF document or styles: {doc_error}")
         raise HTTPException(status_code=500, detail=f"Failed to initialize PDF document/styles: {doc_error}")


    try:
        for model in MODELS_TO_EXPORT:
            table_name = model.__tablename__
            print(f"Exporting table: {table_name} for PDF")

            try:
                story.append(Paragraph(f"Таблиця: {table_name}", style_h2)) # Новий стиль
                story.append(Spacer(1, 0.1*inch))

                mapper = sqlalchemy_inspect(model)
                column_names = []
                sensitive_columns = ['password_hash']
                for prop in mapper.iterate_properties:
                    if isinstance(prop, ColumnProperty) and hasattr(prop.expression, 'key'):
                        column_key = prop.expression.key
                        if column_key.lower() in [c.lower() for c in sensitive_columns]:
                            continue
                        column_names.append(column_key)

                if not column_names:
                    story.append(Paragraph("<i>(Немає стовпців для відображення)</i>", style_italic)) # Новий стиль
                    story.append(Spacer(1, 0.2*inch))
                    continue

                table_data_query = db.query(model).all()

                # --- Підготовка даних з новими стилями ---
                # Використовуємо style_header для заголовків
                header_row = [Paragraph(f'{col}', style_header) for col in column_names]
                data_for_table = [header_row]

                if not table_data_query:
                     # Використовуємо style_normal і курсивний тег
                    data_for_table.append([Paragraph("<i>(Немає даних)</i>", style_normal)] * len(column_names))
                else:
                    for row_obj in table_data_query:
                        row_values = []
                        for col_name in column_names:
                            value = getattr(row_obj, col_name, None)
                            if value is None: cell_content = ""
                            elif isinstance(value, (datetime, date, time)): cell_content = value.isoformat()
                            elif isinstance(value, (Decimal, float, int, bool)): cell_content = str(value)
                            else: cell_content = str(value)
                            # Використовуємо style_normal для звичайних комірок
                            row_values.append(Paragraph(cell_content, style_normal))
                        data_for_table.append(row_values)

                # --- Створення та стилізація таблиці ---
                if data_for_table:
                    table = Table(data_for_table, repeatRows=1)
                    table_style = TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.grey),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        # ('FONTNAME', (0,0), (-1,0), registered_bold_font), # Вже встановлено через стиль Paragraph
                        ('BOTTOMPADDING', (0,0), (-1,0), 6), # Зменшимо трохи
                        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F0F0F0')), # Світліший фон
                        ('GRID', (0,0), (-1,-1), 0.5, colors.grey) # Тонша сітка
                    ])
                    table.setStyle(table_style)
                    story.append(table)
                    print(f"  Successfully prepared table {table_name} for PDF.")
                else:
                    story.append(Paragraph("<i>(Не вдалося створити таблицю)</i>", style_italic))

                story.append(Spacer(1, 0.3*inch))

            except Exception as table_error:
                print(f"  Error processing table {table_name} for PDF: {table_error}")
                story.append(Paragraph(f"<i>Помилка при обробці таблиці {table_name}: {table_error}</i>", style_italic))
                story.append(Spacer(1, 0.2*inch))

        # --- Генерація PDF документу ---
        print("Building PDF document...")
        doc.build(story)
        print("PDF document built successfully.")

    except Exception as pdf_error:
        print(f"Error generating PDF content: {pdf_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not generate PDF content: {pdf_error}"
        )

    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        }
    )