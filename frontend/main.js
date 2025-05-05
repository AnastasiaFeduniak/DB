document.addEventListener('DOMContentLoaded', () => {
    // --- Отримуємо елементи DOM ---
    const token = localStorage.getItem('accessToken');
    console.log('Token on load:', token); // Додано для перевірки
    const userInfoSpan = document.getElementById('user-info');
    const exportDropdownToggle = document.querySelector('.sidebar-nav .dropdown-toggle'); // Посилання "Export"
    const exportDropdownMenu = document.getElementById('export-dropdown-menu');       // Сам випадний список <ul>
    const employeeSearchButton = document.getElementById('employee-search-button');
    const logoutButton = document.getElementById('logout-button');
    const employeeListContainer = document.getElementById('employee-list-container');
    const sidebar = document.getElementById('sidebar');
    const clientSearchInput = document.getElementById('client-search-input');
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    const currentSectionTitle = document.getElementById('current-section-title');
    const menuToggleButton = document.getElementById('menu-toggle');
    const sidebarNav = document.querySelector('.sidebar-nav'); // Отримуємо <nav class="sidebar-nav">
    const employeesContentSection = document.getElementById('employees-content'); // <-- ОГОЛОШЕННЯ МАЄ БУТИ ДО ВИКОРИСТАННЯ
    const stockListContainer = document.getElementById('stock-list-container');
    let currentUser = null;
    const ordersContentSection = document.getElementById('recent-orders-content');
    const orderSearchInput = document.getElementById('order-search-input');
    const orderSearchButton = document.getElementById('order-search-button'); // <--- ОГОЛОШЕННЯ
    const orderStatusFilter = document.getElementById('order-status-filter');
    const orderDateFromInput = document.getElementById('order-date-from');
    const orderDateToInput = document.getElementById('order-date-to');
    const orderFilterButton = document.getElementById('order-filter-button');
    const orderListContainer = document.getElementById('order-list-container');
    const orderDetailsModal = document.getElementById('order-details-modal');
    const orderDetailsContent = document.getElementById('order-details-content');
    const orderDetailsTitle = document.getElementById('order-details-title');
    const orderDetailsError = document.getElementById('order-details-error');
    const closeOrderDetailsBtn = document.getElementById('close-order-details-btn');
    const orderStatusUpdateSection = document.getElementById('order-status-update-section');
    const orderNewStatusSelect = document.getElementById('order-new-status-select');
    const updateOrderStatusButton = document.getElementById('update-order-status-button');
    const orderStatusUpdateMessage = document.getElementById('order-status-update-message');
    const orderDetailsIdInput = document.getElementById('order-details-id');
    const clientsContentSection = document.getElementById('clients-content');
    const addClientButton = document.getElementById('add-client-button');
    const clientFormModal = document.getElementById('client-form-modal');
    const clientForm = document.getElementById('client-form');
    const clientFormTitle = document.getElementById('client-form-title');
    const clientFormError = document.getElementById('client-form-error');
    const clientIdInput = document.getElementById('client-id'); // Приховане поле ID
    // Поля форми (переконайтеся, що ID відповідають вашому HTML)
    const clientFirstNameInput = document.getElementById('client-first-name');
    const clientLastNameInput = document.getElementById('client-last-name');
    const clientEmailInput = document.getElementById('client-email');
    const clientPhoneInput = document.getElementById('client-phone');

    const clientSearchButton = document.getElementById('client-search-button');
    const clientListContainer = document.getElementById('client-list-container');
    const stockContentSection = document.getElementById('stock-content');

    // --- 1. Перевірка автентифікації ---
    if (!token) {
        console.error("No token found, redirecting to login.");
        // window.location.href = '/login.html'; // Розкоментуйте для перенаправлення
        return; // Зупиняємо виконання, якщо немає токена
    }

    // --- 2. Отримання інформації про користувача ---
    async function fetchUserInfo() {
        console.log("Fetching user info...");
        try {
            const response = await fetch('http://localhost:7000/api/v1/users/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (!response.ok) {
                if (response.status === 401) {
                    console.error("Unauthorized (401). Token might be invalid or expired. Removing token.");
                    localStorage.removeItem('accessToken');
                    // window.location.href = '/login.html'; // Розкоментуйте для перенаправлення
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            currentUser = await response.json();
            console.log("User info received:", currentUser);
            displayUserInfo();
            setupRoleBasedUI();
            // Завантажуємо метрики ТІЛЬКИ ПІСЛЯ отримання інфо про користувача, щоб UI був готовий
            fetchDashboardMetrics();
        } catch (error) {
            console.error("Failed to fetch user info:", error);
            userInfoSpan.textContent = 'Помилка завантаження користувача';
            // Можливо, обробити помилку більш явно
        }
    }

    function displayUserInfo() {
        if (currentUser) {
            userInfoSpan.textContent = `${currentUser.first_name || ''} ${currentUser.last_name || ''} (${currentUser.role_name || 'N/A'})`;
        } else {
             userInfoSpan.textContent = 'Не вдалося завантажити дані';
        }
    }

    // --- 3. Налаштування UI залежно від ролі ---
    function setupRoleBasedUI() {
        // Очищаємо попередні ролі на body, якщо вони є
        document.body.className = document.body.className.replace(/role-\S+/g, '').trim();

        if (!currentUser || !currentUser.role_name) {
             console.warn("User role not available for UI setup.");
             return;
        }
        const roleClass = `role-${currentUser.role_name.replace(/\s+/g, '-')}`; // Замінюємо пробіли на тире
        console.log("Applying role class:", roleClass);
        document.body.classList.add(roleClass);

        // Приховуємо/показуємо елементи навігації залежно від ролі
        document.querySelectorAll('.sidebar-nav .role-section').forEach(item => {
            item.style.display = 'none'; // Спершу ховаємо все
        });
        
        if (currentUser.role_name === 'Administrator') {
             document.querySelectorAll('.sidebar-nav .admin-only').forEach(item => item.style.display = '');
        } else if (currentUser.role_name === 'Location Manager') {
            document.querySelectorAll('.sidebar-nav .manager-only').forEach(item => item.style.display = '');
        } else if (currentUser.role_name === 'Cashier') {
            document.querySelectorAll('.sidebar-nav .cashier-only').forEach(item => item.style.display = '');
        }
         // Загальні елементи (якщо потрібно)
         document.querySelectorAll('.sidebar-nav li:not(.role-section)').forEach(item => item.style.display = '');
    }

     // --- 4. Отримання та відображення метрик дашборду ---
     async function fetchDashboardMetrics() {
         const dashboardContent = document.getElementById('dashboard-content');
         if(!dashboardContent || !dashboardContent.classList.contains('active')) {
             console.log("Dashboard not active, skipping metrics fetch.");
             return; // Не завантажувати, якщо секція не активна
         }

        console.log("Fetching dashboard metrics...");
        const revenueEl = document.getElementById('metric-revenue');
        const popularBooksEl = document.getElementById('metric-popular-books');
        const lowStockEl = document.getElementById('metric-low-stock');
        const newOrdersEl = document.getElementById('metric-new-orders');

        // Перевірка наявності елементів
        if (!revenueEl || !popularBooksEl || !lowStockEl || !newOrdersEl) {
            console.error("One or more dashboard metric elements not found.");
            return;
        }

        revenueEl.textContent = 'Завантаження...';
        popularBooksEl.innerHTML = '<li>Завантаження...</li>';
        lowStockEl.innerHTML = '<li>Завантаження...</li>';
        newOrdersEl.textContent = 'Завантаження...';

        try {
             const response = await fetch('http://localhost:7000/api/v1/dashboard/metrics', {
                 headers: {
                     'Authorization': `Bearer ${token}`
                 }
             });
             if (!response.ok) {
                 throw new Error(`HTTP error! status: ${response.status}`);
             }
             const metrics = await response.json();
             console.log("Dashboard metrics received:", metrics);

             revenueEl.textContent = `${(metrics.revenue_last_week || 0).toFixed(2)} грн`;
             newOrdersEl.textContent = metrics.new_orders_today || 0;

             if (metrics.popular_books_last_week && metrics.popular_books_last_week.length > 0) {
                 popularBooksEl.innerHTML = metrics.popular_books_last_week
                    .map(book => `<li>${book.title || 'Без назви'} (${book.total_quantity || 0} шт.)</li>`)
                    .join('');
             } else {
                 popularBooksEl.innerHTML = '<li>Немає даних</li>';
             }

             if (metrics.low_stock_items && metrics.low_stock_items.length > 0) {
                 lowStockEl.innerHTML = metrics.low_stock_items
                    .map(item => `<li>${item.title || 'Без назви'} (${item.location_address || 'N/A'}): ${item.quantity || 0} шт.</li>`)
                    .join('');
             } else {
                 lowStockEl.innerHTML = '<li>Немає позицій</li>';
             }

         } catch (error) {
             console.error("Failed to fetch dashboard metrics:", error);
             revenueEl.textContent = 'Помилка';
             popularBooksEl.innerHTML = '<li>Помилка</li>';
             lowStockEl.innerHTML = '<li>Помилка</li>';
             newOrdersEl.textContent = 'Помилка';
         }
     }


    // --- 5. Навігація між секціями ---
    function showSection(sectionId) {
        console.log("Showing section:", sectionId);
        contentSections.forEach(section => {
            section.classList.remove('active');
        });
        const activeSection = document.getElementById(sectionId);
        if (activeSection) {
            activeSection.classList.add('active');
            const link = document.querySelector(`.nav-link[data-section="${sectionId}"]`);
            currentSectionTitle.textContent = link ? link.textContent.trim() : 'Розділ';
        } else {
             console.warn(`Section with ID "${sectionId}" not found. Falling back to dashboard.`);
             const dashboardSection = document.getElementById('dashboard-content');
             if (dashboardSection) dashboardSection.classList.add('active');
             currentSectionTitle.textContent = 'Дашборд';
        }
    }

    // Обробник кліків на навігації
    if (sidebarNav) {
        sidebarNav.addEventListener('click', (event) => {
            const link = event.target.closest('a.nav-link');
            if (link && link.dataset.section) {
                event.preventDefault(); // Забороняємо стандартний перехід по якорю

                const sectionId = link.dataset.section;
                console.log(`Navigation click: section=${sectionId}`);

                // Оновлюємо активний клас для посилань
                navLinks.forEach(navLink => navLink.classList.remove('active'));
                link.classList.add('active');

                // Показуємо відповідну секцію
                showSection(sectionId);

                // Оновлюємо URL (необов'язково, але корисно для посилань та оновлення)
                 history.pushState(null, '', `#${sectionId}`);


                 // Закриваємо бокове меню на мобільних пристроях після кліку
                 if (window.innerWidth <= 768) {
                     sidebar.classList.remove('open');
                 }

                 // Якщо це секція дашборду, оновлюємо метрики
                 if (sectionId === 'dashboard-content') {
                     fetchDashboardMetrics();
                 }
            }
        });
    } else {
        console.error("Sidebar navigation element not found!");
    }


     // --- 6. Обробка виходу (Logout) ---
     if (logoutButton) {
        logoutButton.addEventListener('click', () => {
            console.log("Logging out...");
            localStorage.removeItem('accessToken');
            // localStorage.removeItem('userRole'); // Можливо, вже не використовується
            window.location.href = '/login.html'; // Перенаправляємо на сторінку входу
        });
     } else {
         console.error("Logout button not found!");
     }

    // --- 7. Мобільне меню ---
    if (menuToggleButton) {
        menuToggleButton.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    } else {
        console.error("Menu toggle button not found!");
    }

    // --- 8. Ініціалізація після завантаження DOM ---
    console.log("DOM fully loaded and parsed. Initializing...");
    fetchUserInfo(); // Запускаємо отримання даних користувача

    // Показуємо початкову секцію на основі URL або за замовчуванням
    let initialSectionId = window.location.hash.substring(1);
    if (!initialSectionId || !document.getElementById(initialSectionId)) {
        console.log("No valid initial section in URL hash, defaulting to dashboard.");
        initialSectionId = 'dashboard-content';
        history.replaceState(null, '', '#dashboard-content'); // Оновлюємо URL без додавання в історію
    }

    console.log("Initial section ID:", initialSectionId);
    const initialLink = document.querySelector(`.nav-link[data-section="${initialSectionId}"]`);
    if(initialLink) {
        navLinks.forEach(navLink => navLink.classList.remove('active'));
        initialLink.classList.add('active');
    } else {
        // Якщо посилання для початкової секції не знайдено, активуємо дашборд
        const dashboardLink = document.querySelector('.nav-link[data-section="dashboard-content"]');
        if (dashboardLink) dashboardLink.classList.add('active');
    }
    showSection(initialSectionId); // Показуємо початкову секцію


    //=========================================================================//
    //========= ПОЧАТОК БЛОКУ УПРАВЛІННЯ КНИГАМИ (ПЕРЕМІЩЕНО СЮДИ) ==========//
    //=========================================================================//

    console.log("Initializing Book Management section...");

    // Отримуємо елементи DOM для секції книг (перевіряємо наявність)
    const booksContentSection = document.getElementById('books-content');
    const bookSearchInput = document.getElementById('book-search-input');
    const bookSearchButton = document.getElementById('book-search-button');
    const addBookButton = document.getElementById('add-book-button');
    const bookListContainer = document.getElementById('book-list-container');
    const bookFormModal = document.getElementById('book-form-modal');
    const bookForm = document.getElementById('book-form');
    const bookFormTitle = document.getElementById('book-form-title');
    const bookFormError = document.getElementById('book-form-error');
    const bookIdInput = document.getElementById('book-id'); // Hidden input

    // Dropdowns in the form
    const authorSelect = document.getElementById('book-author');
    const categorySelect = document.getElementById('book-category');
    const publisherSelect = document.getElementById('book-publisher');

    // Store dropdown data to avoid refetching
    let authorsList = [];
    let categoriesList = [];
    let publishersList = [];
    let isDropdownDataFetched = false; // Прапорець, щоб не завантажувати дані списків повторно

    // --- Допоміжні функції для книг ---

    // Заповнення <select> елемента
    function populateSelect(selectElement, data, valueField, textField) {
        if (!selectElement) {
            console.error(`Select element not found for populating.`);
            return;
        }
        // Очищуємо попередні опції, залишаючи плейсхолдер
        const placeholderText = `Select ${selectElement.id.split('-')[1]}...`;
        selectElement.innerHTML = `<option value="">${placeholderText}</option>`;
        if (!data || data.length === 0) {
            console.warn(`No data provided to populate select element ${selectElement.id}`);
            return;
        }
        data.forEach(item => {
            const option = document.createElement('option');
            option.value = item[valueField];
            option.textContent = item[textField];
            selectElement.appendChild(option);
        });
    }

    // Отримання даних для випадаючих списків
    async function fetchDropdownData() {
        // Перевіряємо токен ТУТ, всередині функції
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) {
            console.error("Cannot fetch dropdown data: token is missing.");
            return;
        }
        // Перевіряємо, чи дані вже завантажені
        if (isDropdownDataFetched) {
            console.log("Dropdown data already fetched, skipping.");
            return;
        }
        console.log("Fetching dropdown data...");

        try {
            // Використовуємо Promise.all для паралельного завантаження
            const [authorsRes, categoriesRes, publishersRes] = await Promise.all([
                fetch('http://localhost:7000/api/v1/authors/list', { headers: { 'Authorization': `Bearer ${currentToken}` } }),
                fetch('http://localhost:7000/api/v1/categories/list', { headers: { 'Authorization': `Bearer ${currentToken}` } }),
                fetch('http://localhost:7000/api/v1/publishers/list', { headers: { 'Authorization': `Bearer ${currentToken}` } })
            ]);

            // Перевірка відповідей
            if (!authorsRes.ok) throw new Error(`Authors fetch failed: ${authorsRes.status}`);
            if (!categoriesRes.ok) throw new Error(`Categories fetch failed: ${categoriesRes.status}`);
            if (!publishersRes.ok) throw new Error(`Publishers fetch failed: ${publishersRes.status}`);

            authorsList = await authorsRes.json();
            categoriesList = await categoriesRes.json();
            publishersList = await publishersRes.json();

            isDropdownDataFetched = true; // Встановлюємо прапорець
            console.log("Dropdown data fetched successfully.");

            // Не заповнюємо тут, заповнимо при відкритті форми
        } catch (error) {
            console.error("Error fetching dropdown data:", error);
            isDropdownDataFetched = false; // Скидаємо прапорець у разі помилки
             // Можна показати повідомлення користувачу
             if(bookFormError) bookFormError.textContent = "Помилка завантаження даних для списків.";
        }
    }


    // --- Функції управління книгами ---

    // Відображення таблиці книг
    function renderBookTable(books) {
        if (!bookListContainer) {
            console.error("Book list container not found for rendering.");
            return;
        }

        if (!books || books.length === 0) {
            bookListContainer.innerHTML = '<p>Книги не знайдено.</p>';
            return;
        }

        // Перевірка ролі для відображення кнопок дій
        const isAdmin = document.body.classList.contains('role-Administrator');

        let tableHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Назва</th>
                        <th>Автор</th>
                        <th>Категорія</th>
                        <th>Видавець</th>
                        <th>Рік</th>
                        <th>Ціна</th>
                        <th>Знижка</th>
                        ${isAdmin ? '<th>Дії</th>' : ''}
                    </tr>
                </thead>
                <tbody>
        `;

        books.forEach(book => {
            // Використовуємо ?? для значень за замовчуванням
            tableHTML += `
                <tr>
                    <td>${book.title ?? 'N/A'}</td>
                    <td>${book.author_name ?? 'N/A'}</td>
                    <td>${book.category_name ?? 'N/A'}</td>
                    <td>${book.publisher_name ?? 'N/A'}</td>
                    <td>${book.publication_year ?? 'N/A'}</td>
                    <td>${book.price !== null && book.price !== undefined ? book.price.toFixed(2) + ' грн' : 'N/A'}</td>
                    <td>${book.discount_percentage !== null && book.discount_percentage !== undefined ? book.discount_percentage.toFixed(2) + '%' : '0.00%'}</td>
                    ${isAdmin ? `
                    <td class="action-cell">
                        <button class="action-button edit-btn admin-only" data-id="${book.book_id}">Ред.</button>
                        <button class="action-button delete-btn admin-only" data-id="${book.book_id}">Вид.</button>
                    </td>` : ''}
                </tr>
            `;
        });

        tableHTML += `</tbody></table>`;
        bookListContainer.innerHTML = tableHTML;
    }

    // Завантаження книг з бекенду
    async function loadBooks(searchTerm = '') {
         // Перевіряємо токен ТУТ, всередині функції
        const currentToken = localStorage.getItem('accessToken');
        if (!bookListContainer) {
             console.error("Book list container not found for loading books.");
             return;
        }
        if (!currentToken) {
            console.error("Cannot load books: token is missing.");
            bookListContainer.innerHTML = '<p>Помилка: Необхідна авторизація.</p>';
            return;
        }

        console.log(`Loading books... Search term: "${searchTerm}"`);
        bookListContainer.innerHTML = '<p>Завантаження книг...</p>';

        let url = 'http://localhost:7000/api/v1/books';
        if (searchTerm) {
            url += `?search=${encodeURIComponent(searchTerm)}`;
        }

        try {
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${currentToken}` }
            });
            if (!response.ok) {
                // Обробка можливих помилок відповіді
                 if (response.status === 401) throw new Error('Помилка авторизації (401).');
                 throw new Error(`HTTP помилка! Статус: ${response.status}`);
            }
            const books = await response.json();
            console.log("Books loaded:", books);
            renderBookTable(books);
        } catch (error) {
            console.error("Failed to load books:", error);
            bookListContainer.innerHTML = `<p>Помилка завантаження книг: ${error.message}</p>`;
        }
    }

    // Відкриття модального вікна для додавання/редагування
    async function openBookForm(book = null) { // Робимо асинхронною для await fetchDropdownData
        if (!bookFormModal || !bookForm) {
            console.error("Book form modal or form element not found.");
            return;
        }

        console.log("Opening book form. Book data:", book);

        // Спочатку завантажуємо/перевіряємо дані для списків
        await fetchDropdownData();

        // Перевіряємо, чи дані списків завантажились
        if (!isDropdownDataFetched) {
            alert("Не вдалося завантажити дані для списків. Неможливо відкрити форму.");
            return;
        }

        // Заповнюємо списки
        populateSelect(authorSelect, authorsList, 'author_id', 'full_name');
        populateSelect(categorySelect, categoriesList, 'category_id', 'name');
        populateSelect(publisherSelect, publishersList, 'publisher_id', 'name');

        // Скидаємо форму та повідомлення про помилку
        bookForm.reset();
        if (bookFormError) bookFormError.textContent = '';
        if (bookIdInput) bookIdInput.value = ''; // Очищаємо приховане ID

        if (book) {
            // Режим редагування
            if(bookFormTitle) bookFormTitle.textContent = 'Редагувати книгу';
            if(bookIdInput) bookIdInput.value = book.book_id;
            // Використовуємо getElementById для полів форми для надійності
            const titleInput = document.getElementById('book-title');
            const yearInput = document.getElementById('book-year');
            const priceInput = document.getElementById('book-price');
            const discountInput = document.getElementById('book-discount');
            const descriptionInput = document.getElementById('book-description');

            if(titleInput) titleInput.value = book.title ?? '';
            if(authorSelect) authorSelect.value = book.author_id ?? '';
            if(categorySelect) categorySelect.value = book.category_id ?? '';
            if(publisherSelect) publisherSelect.value = book.publisher_id ?? '';
            if(yearInput) yearInput.value = book.publication_year ?? '';
            if(priceInput) priceInput.value = (book.price !== null && book.price !== undefined) ? book.price : '';
            if(discountInput) discountInput.value = (book.discount_percentage !== null && book.discount_percentage !== undefined) ? book.discount_percentage : 0;
            if(descriptionInput) descriptionInput.value = book.description ?? '';
        } else {
            // Режим додавання
            if(bookFormTitle) bookFormTitle.textContent = 'Додати нову книгу';
        }

        bookFormModal.classList.add('show'); // Показуємо модальне вікно
    }

    // Закриття модального вікна
    function closeBookForm() {
        if (bookFormModal) {
            bookFormModal.classList.remove('show');
            console.log("Book form closed.");
        }
    }

    // Обробка відправки форми (додавання/редагування)
    async function saveBook(event) {
        event.preventDefault(); // Запобігаємо стандартній відправці форми
        // Перевіряємо токен
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) {
             if (bookFormError) bookFormError.textContent = 'Помилка: Необхідна авторизація.';
             console.error("Cannot save book: token is missing.");
             return;
        }
        if (!bookForm) {
             console.error("Book form not found for saving.");
             return;
        }

        if (bookFormError) bookFormError.textContent = ''; // Очищаємо попередні помилки

        const bookId = bookIdInput ? bookIdInput.value : null;
        const isEditing = !!bookId;
        console.log(`Saving book. Editing: ${isEditing}, ID: ${bookId}`);

        // Збираємо дані з форми
        const bookData = {
            title: document.getElementById('book-title')?.value.trim() ?? '',
            author_id: parseInt(document.getElementById('book-author')?.value) || null,
            category_id: parseInt(document.getElementById('book-category')?.value) || null,
            publisher_id: parseInt(document.getElementById('book-publisher')?.value) || null,
            publication_year: parseInt(document.getElementById('book-year')?.value) || null,
            price: parseFloat(document.getElementById('book-price')?.value) || null,
            discount_percentage: parseFloat(document.getElementById('book-discount')?.value) || 0,
            description: document.getElementById('book-description')?.value.trim() ?? ''
        };

        // --- Проста валідація на клієнті ---
        let validationError = '';
        if (!bookData.title) validationError += 'Назва є обов\'язковою. ';
        if (!bookData.author_id) validationError += 'Автор є обов\'язковим. ';
        if (!bookData.category_id) validationError += 'Категорія є обов\'язковою. ';
        if (!bookData.publisher_id) validationError += 'Видавець є обов\'язковим. ';
        if (!bookData.publication_year || bookData.publication_year < 1000 || bookData.publication_year > new Date().getFullYear() + 1) {
             validationError += 'Некоректний рік публікації. ';
        }
        if (bookData.price === null || isNaN(bookData.price) || bookData.price < 0) {
            validationError += 'Некоректна ціна. ';
        }
         if (isNaN(bookData.discount_percentage) || bookData.discount_percentage < 0 || bookData.discount_percentage > 100) {
             validationError += 'Некоректна знижка (0-100). ';
         }

        if (validationError) {
             if (bookFormError) bookFormError.textContent = validationError.trim();
             console.warn("Book form validation failed:", validationError);
             return;
        }
        // --- Кінець валідації ---

        const url = isEditing
            ? `http://localhost:7000/api/v1/books/${bookId}`
            : 'http://localhost:7000/api/v1/books';
        const method = isEditing ? 'PUT' : 'POST';

        console.log(`Sending request to ${url} with method ${method}`);

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${currentToken}`
                },
                body: JSON.stringify(bookData)
            });

            if (!response.ok) {
                 // Спробуємо отримати деталі помилки з тіла відповіді
                 let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                 try {
                     const errorData = await response.json();
                     errorDetail = errorData.detail || errorDetail;
                 } catch (e) {
                     console.warn("Could not parse error response body.");
                 }
                 throw new Error(errorDetail);
            }

            // Успіх
            console.log(`Book ${isEditing ? 'updated' : 'created'} successfully.`);
            closeBookForm();
            // Оновлюємо список книг, зберігаючи поточний пошуковий термін
            const currentSearchTerm = bookSearchInput ? bookSearchInput.value.trim() : '';
            loadBooks(currentSearchTerm);

        } catch (error) {
            console.error("Failed to save book:", error);
            if (bookFormError) bookFormError.textContent = `Помилка збереження: ${error.message}`;
        }
    }

    // Обробка видалення книги
    async function deleteBook(bookId) {
         // Перевіряємо токен
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) {
            console.error("Cannot delete book: token is missing.");
            alert('Помилка: Необхідна авторизація.');
            return;
        }
        if (!bookId) {
             console.error("Cannot delete book: ID is missing.");
             return;
        }

        console.log(`Attempting to delete book ID: ${bookId}`);
        if (!confirm(`Ви впевнені, що хочете видалити книгу ID: ${bookId}?`)) {
            console.log("Book deletion cancelled by user.");
            return;
        }

        const url = `http://localhost:7000/api/v1/books/${bookId}`;

        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${currentToken}` }
            });

            if (!response.ok) {
                 // Спробуємо отримати деталі помилки
                 let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                 // 204 No Content також вважається успішним видаленням, але fetch може не кинути помилку
                 if (response.status !== 204) {
                     try {
                         const errorData = await response.json();
                         errorDetail = errorData.detail || errorDetail;
                     } catch (e) {
                          console.warn("Could not parse error response body for delete.");
                     }
                     throw new Error(errorDetail);
                 }
            }

            // Успіх (включаючи 204 No Content)
            console.log(`Book ${bookId} deleted successfully.`);
            // Оновлюємо список
            const currentSearchTerm = bookSearchInput ? bookSearchInput.value.trim() : '';
            loadBooks(currentSearchTerm);

        } catch (error) {
            console.error("Failed to delete book:", error);
            alert(`Помилка видалення книги: ${error.message}`); // Показуємо повідомлення користувачу
        }
    }

    // --- Налаштування слухачів подій для книг ---

    // MutationObserver для завантаження даних при активації секції
    const observer = new MutationObserver((mutationsList) => {
        for(let mutation of mutationsList) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const targetElement = mutation.target;
                // Перевірка для книг
                if (targetElement.id === 'books-content' && targetElement.classList.contains('active')) {
                    console.log("Books section activated via MutationObserver, loading books...");
                    loadBooks();
                    fetchDropdownData(); // Для форми книг
                }
                // Перевірка для авторів
                else if (targetElement.id === 'authors-content' && targetElement.classList.contains('active')) {
                    console.log("Authors section activated via MutationObserver, loading authors...");
                    loadAuthors(); // Завантажуємо авторів
                }
                // Перевірка для категорій
                else if (targetElement.id === 'categories-content' && targetElement.classList.contains('active')) {
                    console.log("Categories section activated via MutationObserver, loading categories...");
                    loadCategories(); // Завантажуємо категорії
                }
                // Перевірка для клієнтів
                else if (targetElement.id === 'clients-content' && targetElement.classList.contains('active')) {
                    console.log("Clients section activated via MutationObserver, loading clients...");
                    loadClients(); // Викликаємо завантаження клієнтів
                }
                // ---> ДОДАЙТЕ ЦЕЙ БЛОК else if <---
                else if (targetElement.id === 'employees-content' && targetElement.classList.contains('active')) {
                    console.log("Employees section activated via MutationObserver, loading employees...");
                    loadEmployees();
                        //fetchEmployeeDropdownData(); // Завантажуємо дані для форми
                }
                // Не забудьте додати виклик loadStockData в MutationObserver
                 else if (targetElement.id === 'stock-content' && targetElement.classList.contains('active')) {
                 console.log("Stock section activated, loading stock data...");
                 loadStockData(); // Завантажити з початковими фільтрами
                    }
                else if (targetElement.id === 'recent-orders-content' && targetElement.classList.contains('active')) {
                        console.log("Orders section activated via MutationObserver, loading orders...");
                        loadOrders(); // Викликаємо завантаження замовлень
                    }
            }
        }
    });

    const ordersContentSectionObserverTarget = document.getElementById('recent-orders-content'); // Можна використати змінну з початку
    if (ordersContentSectionObserverTarget) {
        console.log("Setting up MutationObserver for orders section.");
        observer.observe(ordersContentSectionObserverTarget, { attributes: true });
        // Перевіряємо, чи секція вже активна при ініціалізації (на випадок #orders в URL)
        if (ordersContentSectionObserverTarget.classList.contains('active')) {
            console.log("Orders section already active on init, loading orders...");
            loadOrders();
        }
    } else {
        console.error("Orders content section (#recent-orders-content) not found for MutationObserver setup!");
    }
    document.getElementById('stock-search-button')?.addEventListener('click', () => {
        const searchTerm = document.getElementById('stock-book-search-input')?.value.trim();
        loadStockData(searchTerm);
     });
     document.getElementById('stock-book-search-input')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
             loadStockData(e.target.value.trim());
         }
     });
     if (stockContentSection) { // Використовуємо змінну, оголошену на початку
        console.log("Setting up MutationObserver for stock section.");
        observer.observe(stockContentSection, { attributes: true }); // Спостерігаємо за атрибутами
    } else {
        console.error("Stock content section (#stock-content) not found for MutationObserver setup!");
    }
    // Запускаємо спостереження, якщо секція книг існує
    if (booksContentSection) {
        console.log("Setting up MutationObserver for books section.");
        observer.observe(booksContentSection, { attributes: true }); // Спостерігаємо за атрибутами
    } else {
         console.error("Books content section not found for MutationObserver setup!");
    }

    // Кнопка Пошуку
    const booksContentSectionObserverTarget = document.getElementById('books-content');
    if (booksContentSectionObserverTarget) {
         observer.observe(booksContentSectionObserverTarget, { attributes: true });
    } else { console.error("Books content section not found for MutationObserver!"); }

    if (employeesContentSection) {
        console.log("Setting up MutationObserver for employees section.");
        observer.observe(employeesContentSection, { attributes: true });
    } else {
        console.error("Employees content section (#employees-content) not found for MutationObserver setup!");
    }

    const authorsContentSectionObserverTarget = document.getElementById('authors-content');
    if (authorsContentSectionObserverTarget) {
        console.log("Setting up MutationObserver for authors section.");
        observer.observe(authorsContentSectionObserverTarget, { attributes: true });
    } else { console.error("Authors content section not found for MutationObserver!"); }

    // Спостерігаємо за секцією категорій
    const categoriesContentSectionObserverTarget = document.getElementById('categories-content');
    if (categoriesContentSectionObserverTarget) {
        console.log("Setting up MutationObserver for categories section.");
        observer.observe(categoriesContentSectionObserverTarget, { attributes: true });
    } else { console.error("Categories content section not found for MutationObserver!"); }

    const clientsContentSectionObserverTarget = document.getElementById('clients-content');

    // ... (код налаштування observer.observe для books, authors, categories) ...

    // ---> ДОДАЙТЕ ЦЕЙ БЛОК <---
    // Спостерігаємо за секцією клієнтів
    if (clientsContentSectionObserverTarget) {
        console.log("Setting up MutationObserver for clients section.");
        observer.observe(clientsContentSectionObserverTarget, { attributes: true });
    } else {
        console.error("Clients content section not found for MutationObserver setup!");
    }
    // Пошук при натисканні Enter у полі пошуку
    if (bookSearchInput) {
        bookSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadBooks(bookSearchInput.value.trim());
            }
        });
    }

    if (bookSearchButton) {
        bookSearchButton.addEventListener('click', () => {
            // Перевіряємо наявність поля вводу перед використанням
            loadBooks(bookSearchInput ? bookSearchInput.value.trim() : '');
        });
    }

    // Відправка форми
    if (bookForm) {
        bookForm.addEventListener('submit', saveBook);
    }

if (bookListContainer) {
    bookListContainer.addEventListener('click', async (event) => {
        const target = event.target; // Елемент, на який клікнули
        const bookId = target.dataset.id; // Отримуємо ID з data-id атрибута

        // --- ДОДАНО ПЕРЕВІРКУ РОЛІ ---
        // Перевіряємо, чи користувач є адміністратором перед виконанням дій редагування/видалення
        const isCurrentUserAdmin = currentUser && currentUser.role_name === 'Administrator';

        // Перевіряємо, чи клікнули на кнопку Редагувати
        if (target.classList.contains('edit-btn') && bookId) {
            // --- ДОДАНО ПЕРЕВІРКУ РОЛІ ---
            if (!isCurrentUserAdmin) {
                 console.warn("Edit action prevented: User is not an Administrator.");
                 return; // Не виконувати дію, якщо не адмін
            }
            console.log(`Edit button clicked for book ID: ${bookId}`);
            // Перевіряємо токен перед запитом (вже є, але для повноти)
            const currentToken = localStorage.getItem('accessToken');
            if (!currentToken) {
                alert("Помилка: Необхідна авторизація.");
                return;
            }
            // Отримуємо повні дані книги для редагування
            try {
                 const response = await fetch(`http://localhost:7000/api/v1/books/${bookId}`, {
                     headers: { 'Authorization': `Bearer ${currentToken}` }
                 });
                 if (!response.ok) throw new Error('Не вдалося завантажити деталі книги');
                 const bookDetails = await response.json();
                 openBookForm(bookDetails); // Відкриваємо форму в режимі редагування
            } catch (error) {
                 console.error("Error fetching book details for edit:", error);
                 alert(`Не вдалося завантажити деталі книги для редагування: ${error.message}`);
            }

        // Перевіряємо, чи клікнули на кнопку Видалити
        } else if (target.classList.contains('delete-btn') && bookId) {
             // --- ДОДАНО ПЕРЕВІРКУ РОЛІ ---
            if (!isCurrentUserAdmin) {
                 console.warn("Delete action prevented: User is not an Administrator.");
                 return; // Не виконувати дію, якщо не адмін
            }
            console.log(`Delete button clicked for book ID: ${bookId}`);
            deleteBook(bookId); // Викликаємо функцію видалення
        }
    });
}
    // Закриття модального вікна при кліку поза ним або на кнопку закриття
    if (bookFormModal) {
         // Клік на фон
        bookFormModal.addEventListener('click', (event) => {
            if (event.target === bookFormModal) { // Перевіряємо, чи клік був саме на фоні
                closeBookForm();
            }
        });
        // Кнопка закриття (хрестик)
        const closeButton = bookFormModal.querySelector('.close-button');
        if (closeButton) {
            closeButton.addEventListener('click', closeBookForm);
        }
        // Кнопка "Cancel"
         const cancelButton = bookFormModal.querySelector('.cancel-button');
         if (cancelButton) {
             cancelButton.addEventListener('click', closeBookForm);
         }
    }

    //=========================================================================//
    //=========== КІНЕЦЬ БЛОКУ УПРАВЛІННЯ КНИГАМИ ==========================//
    //=========================================================================//
    //=========================================================================//
    //========= ПОЧАТОК БЛОКУ УПРАВЛІННЯ АВТОРАМИ ===========================//
    //=========================================================================//

    console.log("Initializing Author Management section...");

    const authorsContentSection = document.getElementById('authors-content');
    const authorSearchInput = document.getElementById('author-search-input');
    const authorSearchButton = document.getElementById('author-search-button');
    const addAuthorButton = document.getElementById('add-author-button');
    const authorListContainer = document.getElementById('author-list-container');
    const authorFormModal = document.getElementById('author-form-modal');
    const authorForm = document.getElementById('author-form');
    const authorFormTitle = document.getElementById('author-form-title');
    const authorFormError = document.getElementById('author-form-error');
    const authorIdInput = document.getElementById('author-id');

    function renderAuthorTable(authors) {
        if (!authorListContainer) return;
        if (!authors || authors.length === 0) {
            authorListContainer.innerHTML = '<p>Авторів не знайдено.</p>';
            return;
        }
        const canManage = currentUser && (currentUser.role_name === 'Administrator');
        let tableHTML = `<table class="data-table"><thead><tr>
                        <th>Ім'я</th><th>Прізвище</th><th>Дата народження</th>
                        ${canManage ? '<th>Дії</th>' : ''}</tr></thead><tbody>`;
        authors.forEach(author => {
            let birthDateFormatted = 'N/A';
            if (author.birth_date) {
                 try {
                     const dateObj = new Date(author.birth_date + 'T00:00:00Z'); // Assume UTC if no timezone
                     if (!isNaN(dateObj.getTime())) birthDateFormatted = dateObj.toLocaleDateString('uk-UA');
                 } catch (e) { console.error(`Error formatting date: ${author.birth_date}`, e); }
            }
            tableHTML += `
            <tr>
                <td>${author.first_name ?? ''}</td>
                <td>${author.last_name ?? ''}</td>
                <td>${birthDateFormatted}</td>
                ${canManage ? `
                <td class="action-cell">
                    <button class="action-button edit-btn" data-id="${author.author_id}">Edit</button>
                    <button class="action-button delete-btn" data-id="${author.author_id}">Delete</button>
                </td>
                ` : ''}
            </tr>
        `;
    });
        tableHTML += `</tbody></table>`;
        if (authorListContainer) authorListContainer.innerHTML = tableHTML;
    }

    async function loadAuthors(searchTerm = '') {
        const currentToken = localStorage.getItem('accessToken');
        if (!authorListContainer) return;
        if (!currentToken) { authorListContainer.innerHTML = '<p>Помилка: Необхідна авторизація.</p>'; return; }
        console.log(`Loading authors... Search: "${searchTerm}"`);
        authorListContainer.innerHTML = '<p>Завантаження авторів...</p>';
        let url = 'http://localhost:7000/api/v1/authors/' + (searchTerm ? `?search=${encodeURIComponent(searchTerm)}` : '');
        try {
            const response = await fetch(url, { headers: { 'Authorization': `Bearer ${currentToken}` } });
            if (!response.ok) throw new Error(`HTTP помилка! Статус: ${response.status}`);
            const authors = await response.json();
            renderAuthorTable(authors);
        } catch (error) {
            console.error("Failed to load authors:", error);
            authorListContainer.innerHTML = `<p>Помилка завантаження авторів: ${error.message}</p>`;
        }
    }

    function openAuthorForm(author = null) {
        if (!authorFormModal || !authorForm || !authorIdInput) return;
        authorForm.reset();
        if (authorFormError) authorFormError.textContent = '';
        authorIdInput.value = '';

        if (author) {
            if(authorFormTitle) authorFormTitle.textContent = 'Редагувати автора';
            authorIdInput.value = author.author_id;
            document.getElementById('author-first-name').value = author.first_name ?? '';
            document.getElementById('author-last-name').value = author.last_name ?? '';
            document.getElementById('author-birth-date').value = author.birth_date ? author.birth_date.split('T')[0] : '';
        } else {
            if(authorFormTitle) authorFormTitle.textContent = 'Додати нового автора';
        }
        authorFormModal.classList.add('show');
    }

    function closeAuthorForm() {
        if (authorFormModal) authorFormModal.classList.remove('show');
    }

    async function saveAuthor(event) {
        event.preventDefault();
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) { if (authorFormError) authorFormError.textContent = 'Помилка: Необхідна авторизація.'; return; }
        if (!authorForm || !authorIdInput) return;
        if (authorFormError) authorFormError.textContent = '';

        const authorId = authorIdInput.value;
        const isEditing = !!authorId;

        const authorData = {
            first_name: document.getElementById('author-first-name')?.value.trim() || null,
            last_name: document.getElementById('author-last-name')?.value.trim(),
            birth_date: document.getElementById('author-birth-date')?.value || null
        };

        let validationError = '';
        if (!authorData.last_name) validationError += 'Прізвище обов\'язкове. ';
        if (authorData.birth_date && new Date(authorData.birth_date) > new Date()) validationError += 'Дата народження не може бути у майбутньому. ';
        if (validationError) { if (authorFormError) authorFormError.textContent = validationError.trim(); return; }

        // Видаляємо null значення для PUT, щоб не перезаписувати існуючі дані null-ами, ЯКЩО бекенд не обробляє exclude_unset=True коректно для null
        let dataToSend = {...authorData};
        if (isEditing) {
            Object.keys(dataToSend).forEach(key => {
                if (dataToSend[key] === null || dataToSend[key] === '') { // Важливо: відрізняти порожній рядок від null, якщо потрібно
                    // Зазвичай для PUT/PATCH краще відправляти тільки змінені поля.
                    // Якщо бекенд використовує model_dump(exclude_unset=True), то null-значення будуть проігноровані.
                    // Якщо ж бекенд очікує null для очищення поля, залишаємо як є.
                    // Припускаємо, що Pydantic `AuthorUpdate` схема обробляє `Optional` коректно.
                     if (dataToSend[key] === null) delete dataToSend[key]; // Або надсилати null, якщо API це підтримує для очищення
                }
            });
             // Якщо жодне поле не змінилося (або всі стали null/порожніми), можемо не відправляти запит
            if (Object.keys(dataToSend).length === 0 && isEditing){
                 console.log("No actual changes detected for author update.");
                 closeAuthorForm();
                 return;
            }
        }


        const url = isEditing ? `http://localhost:7000/api/v1/authors/${authorId}` : 'http://localhost:7000/api/v1/authors/';
        const method = isEditing ? 'PUT' : 'POST';

        console.log(`Sending request to ${url} with method ${method}. Data:`, dataToSend);


        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
                body: JSON.stringify(dataToSend) // Відправляємо підготовлені дані
            });
            if (!response.ok) {
                 let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                 try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
                 throw new Error(errorDetail);
            }
            closeAuthorForm();
            loadAuthors(authorSearchInput ? authorSearchInput.value.trim() : '');
        } catch (error) {
            console.error("Failed to save author:", error);
            if (authorFormError) authorFormError.textContent = `Помилка: ${error.message}`;
        }
    }

    async function deleteAuthor(authorId) {
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) { alert('Помилка: Необхідна авторизація.'); return; }
        if (!authorId || !confirm(`Видалити автора ID: ${authorId}?`)) return;

        const url = `http://localhost:7000/api/v1/authors/${authorId}`;
        try {
            const response = await fetch(url, { method: 'DELETE', headers: { 'Authorization': `Bearer ${currentToken}` } });
             if (response.status !== 204 && !response.ok) {
                 let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                 try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
                 throw new Error(errorDetail);
             }
             console.log(`Author ${authorId} deleted successfully.`);
             loadAuthors(authorSearchInput ? authorSearchInput.value.trim() : '');
        } catch (error) {
            console.error("Failed to delete author:", error);
            alert(`Помилка видалення: ${error.message}`);
        }
    }

    // --- Слухачі подій для авторів ---
    if (authorSearchButton) authorSearchButton.addEventListener('click', () => loadAuthors(authorSearchInput?.value.trim()));
    if (authorSearchInput) authorSearchInput.addEventListener('keypress', (e) => e.key === 'Enter' && loadAuthors(authorSearchInput.value.trim()));
    if (addAuthorButton) addAuthorButton.addEventListener('click', () => openAuthorForm());
    if (authorForm) authorForm.addEventListener('submit', saveAuthor);
    if (authorListContainer) {
        authorListContainer.addEventListener('click', async (event) => {
            const target = event.target;
            const authorId = target.dataset.id;

            // !!! ВИПРАВЛЕНО: Перевіряємо роль 'Manager' !!!
            const isManager = currentUser && (currentUser.role_name === 'Manager');

            // !!! ВИПРАВЛЕНО: Шукаємо класи 'edit-btn' та 'delete-btn' !!!
            if (target.classList.contains('edit-btn') && authorId) {
                // Перевіряємо права тут (хоча кнопки і так видимі лише для Manager)
                if (!isManager) {
                     console.warn("Edit button clicked, but user is not a Manager (should not happen if UI is correct).");
                     return;
                }
                const currentToken = localStorage.getItem('accessToken');
                if (!currentToken) { alert("Потрібна авторизація."); return; }
                try {
                    // Отримуємо деталі автора для редагування
                    const response = await fetch(`http://localhost:7000/api/v1/authors/${authorId}`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
                    if (!response.ok) throw new Error('Не вдалося завантажити деталі автора');
                    openAuthorForm(await response.json()); // Відкриваємо форму
                } catch (error) {
                    console.error("Error fetching author details for edit:", error);
                    alert(`Помилка завантаження для редагування: ${error.message}`);
                 }
            } else if (target.classList.contains('delete-btn') && authorId) {
                 // Перевіряємо права тут
                if (!isManager) {
                    console.warn("Delete button clicked, but user is not a Manager (should not happen if UI is correct).");
                    return;
                }
                deleteAuthor(authorId); // Викликаємо функцію видалення
            }
            // Немає сенсу перевіряти else if !isManager, бо кнопки і так не мають бути видимі
        });
    }
    //=========================================================================//
    //========= КІНЕЦЬ БЛОКУ УПРАВЛІННЯ АВТОРАМИ =============================//
    //=========================================================================//


    //=========================================================================//
    //========= ПОЧАТОК БЛОКУ УПРАВЛІННЯ КАТЕГОРІЯМИ ========================//
    //=========================================================================//

    console.log("Initializing Category Management section...");

    const categoriesContentSection = document.getElementById('categories-content');
    const categorySearchInput = document.getElementById('category-search-input');
    const categorySearchButton = document.getElementById('category-search-button');
    const addCategoryButton = document.getElementById('add-category-button');
    const categoryListContainer = document.getElementById('category-list-container');
    const categoryFormModal = document.getElementById('category-form-modal');
    const categoryForm = document.getElementById('category-form');
    const categoryFormTitle = document.getElementById('category-form-title');
    const categoryFormError = document.getElementById('category-form-error');
    const categoryIdInput = document.getElementById('category-id');

    function renderCategoryTable(categories) {
        if (!categoryListContainer) return;
        if (!categories || categories.length === 0) {
            categoryListContainer.innerHTML = '<p>Категорії не знайдено.</p>';
            return;
        }
        const canManage = currentUser && (currentUser.role_name === 'Administrator');
        console.log(canManage, currentUser.role_name)
        let tableHTML = `<table class="data-table"><thead><tr>
                        <th>Назва</th><th>Опис</th>
                        ${canManage ? '<th>Дії</th>' : ''}</tr></thead><tbody>`;
        
        categories.forEach(category => {
            tableHTML += `<tr>
                    <td>${category.name ?? 'N/A'}</td>
                    <td>${category.description ?? ''}</td>
                    ${canManage ? `<td class="action-cell">
                        <button class="action-button edit-category-btn" data-id="${category.category_id}">Ред.</button>
                        <button class="action-button delete-category-btn" data-id="${category.category_id}">Вид.</button>
                    </td>` : ''}</tr>`;
        });
        tableHTML += `</tbody></table>`;
        categoryListContainer.innerHTML = tableHTML;
        setupRoleBasedUI();
    }

    async function loadCategories(searchTerm = '') {
        const currentToken = localStorage.getItem('accessToken');
        if (!categoryListContainer) return;
        if (!currentToken) { categoryListContainer.innerHTML = '<p>Помилка: Необхідна авторизація.</p>'; return; }
        console.log(`Loading categories... Search: "${searchTerm}"`);
        categoryListContainer.innerHTML = '<p>Завантаження категорій...</p>';
        let url = 'http://localhost:7000/api/v1/categories/' + (searchTerm ? `?search=${encodeURIComponent(searchTerm)}` : '');
        try {
            const response = await fetch(url, { headers: { 'Authorization': `Bearer ${currentToken}` } });
            if (!response.ok) throw new Error(`HTTP помилка! Статус: ${response.status}`);
            const categories = await response.json();
            renderCategoryTable(categories);
        } catch (error) {
            console.error("Failed to load categories:", error);
            categoryListContainer.innerHTML = `<p>Помилка завантаження категорій: ${error.message}</p>`;
        }
    }

    function openCategoryForm(category = null) {
        if (!categoryFormModal || !categoryForm || !categoryIdInput) return;
        categoryForm.reset();
        if (categoryFormError) categoryFormError.textContent = '';
        categoryIdInput.value = '';

        if (category) {
            if(categoryFormTitle) categoryFormTitle.textContent = 'Редагувати категорію';
            categoryIdInput.value = category.category_id;
            document.getElementById('category-name').value = category.name ?? '';
            document.getElementById('category-description').value = category.description ?? '';
        } else {
            if(categoryFormTitle) categoryFormTitle.textContent = 'Додати нову категорію';
        }
        categoryFormModal.classList.add('show');
    }

    function closeCategoryForm() {
        if (categoryFormModal) categoryFormModal.classList.remove('show');
    }

    async function saveCategory(event) {
        event.preventDefault();
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) { if (categoryFormError) categoryFormError.textContent = 'Помилка: Необхідна авторизація.'; return; }
        if (!categoryForm || !categoryIdInput) return;
        if (categoryFormError) categoryFormError.textContent = '';

        const categoryId = categoryIdInput.value;
        const isEditing = !!categoryId;

        const categoryData = {
            name: document.getElementById('category-name')?.value.trim(),
            description: document.getElementById('category-description')?.value.trim() || null
        };

        let validationError = '';
        if (!categoryData.name) validationError += 'Назва категорії обов\'язкова. ';
        if (validationError) { if (categoryFormError) categoryFormError.textContent = validationError.trim(); return; }

        // Prepare data for PUT: only send non-null fields if backend expects partial updates
        let dataToSend = {...categoryData};
         if (isEditing) {
             Object.keys(dataToSend).forEach(key => {
                 if (dataToSend[key] === null) {
                    // Якщо API очікує null для очищення, залишаємо.
                    // Якщо API очікує відсутність поля, видаляємо:
                    // delete dataToSend[key];
                 }
             });
             // Якщо нічого не змінилось, можна не відправляти запит
              // if (Object.keys(dataToSend).length === 0) { closeCategoryForm(); return; }
         }


        const url = isEditing ? `http://localhost:7000/api/v1/categories/${categoryId}` : 'http://localhost:7000/api/v1/categories/';
        const method = isEditing ? 'PUT' : 'POST';

        console.log(`Sending request to ${url} with method ${method}. Data:`, dataToSend);


        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
                body: JSON.stringify(dataToSend)
            });
            if (!response.ok) {
                 let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                 try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
                 throw new Error(errorDetail);
            }
            closeCategoryForm();
            loadCategories(categorySearchInput ? categorySearchInput.value.trim() : '');
        } catch (error) {
            console.error("Failed to save category:", error);
            if (categoryFormError) categoryFormError.textContent = `Помилка: ${error.message}`;
        }
    }

    async function deleteCategory(categoryId) {
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) { alert('Помилка: Необхідна авторизація.'); return; }
        if (!categoryId || !confirm(`Видалити категорію ID: ${categoryId}?`)) return;

        const url = `http://localhost:7000/api/v1/categories/${categoryId}`;
        try {
            const response = await fetch(url, { method: 'DELETE', headers: { 'Authorization': `Bearer ${currentToken}` } });
             if (response.status !== 204 && !response.ok) {
                 let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                 try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
                 throw new Error(errorDetail);
             }
             console.log(`Category ${categoryId} deleted successfully.`);
             loadCategories(categorySearchInput ? categorySearchInput.value.trim() : '');
        } catch (error) {
            console.error("Failed to delete category:", error);
            alert(`Помилка видалення: ${error.message}`);
        }
    }

    // --- Слухачі подій для категорій ---
    if (categorySearchButton) categorySearchButton.addEventListener('click', () => loadCategories(categorySearchInput?.value.trim()));
    if (categorySearchInput) categorySearchInput.addEventListener('keypress', (e) => e.key === 'Enter' && loadCategories(categorySearchInput.value.trim()));
    if (addCategoryButton) addCategoryButton.addEventListener('click', () => openCategoryForm());
    if (categoryForm) categoryForm.addEventListener('submit', saveCategory);
    if (categoryListContainer) categoryListContainer.addEventListener('click', async (event) => {
        const target = event.target; const categoryId = target.dataset.id;
        const canManage = currentUser && (currentUser.role_name === 'Administrator');
        if (target.classList.contains('edit-category-btn') && categoryId && canManage) {
             const currentToken = localStorage.getItem('accessToken');
             if (!currentToken) { alert("Потрібна авторизація."); return; }
             try {
                  const response = await fetch(`http://localhost:7000/api/v1/categories/${categoryId}`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
                  if (!response.ok) throw new Error('Не вдалося завантажити деталі категорії');
                  openCategoryForm(await response.json());
             } catch (error) { alert(`Помилка завантаження для редагування: ${error.message}`); }
        } else if (target.classList.contains('delete-category-btn') && categoryId && canManage) {
             deleteCategory(categoryId);
        } else if ((target.classList.contains('edit-category-btn') || target.classList.contains('delete-category-btn')) && !canManage) {
             console.warn("Action prevented: Insufficient permissions.");
        }
    });
    if (categoryFormModal) {
        categoryFormModal.addEventListener('click', (event) => event.target === categoryFormModal && closeCategoryForm());
        categoryFormModal.querySelector('.close-button')?.addEventListener('click', closeCategoryForm);
        categoryFormModal.querySelector('.cancel-button')?.addEventListener('click', closeCategoryForm);
    }

    //=========================================================================//
    //========= КІНЕЦЬ БЛОКУ УПРАВЛІННЯ КАТЕГОРІЯМИ ==========================//
    //=========================================================================//

    // Відображення таблиці клієнтів
    function renderClientTable(clients) {
        if (!clientListContainer) {
            console.error("Client list container not found!");
            return;
        }
        // !!! ДОДАНО ПЕРЕВІРКУ currentUser !!!
        if (!currentUser) {
            console.error("renderClientTable called before currentUser was fetched.");
            clientListContainer.innerHTML = '<p>Помилка: Дані користувача ще не завантажено.</p>';
            return;
        }
        clientListContainer.innerHTML = ''; // Очищення


        if (!clients || clients.length === 0) {
            clientListContainer.innerHTML = '<p>Клієнтів не знайдено.</p>';
            return;
        }
        const showActions = currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager';

        // Кнопки Дій БУДУТЬ ЗАВЖДИ, бо всі можуть редагувати/видаляти
        let tableHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Ім'я</th>
                        <th>Прізвище</th>
                        <th>Телефон</th>
                        <th>Email</th>
                        <th>Дії</th>
                    </tr>
                </thead>
                <tbody>
        `;
        console.log(tableHTML)

        clients.forEach(client => {
            tableHTML += `
                <tr>
            <td>${client.first_name ?? ''}</td>
            <td>${client.last_name ?? ''}</td>
            <td>${client.phone_number ?? 'N/A'}</td>
            <td>${client.email ?? ''}</td>
            <td class="action-cell">
                <button class="edit-client-btn" data-id="${client.client_id}">Ред.</button>
                <button class="delete-client-btn" data-id="${client.client_id}">Вид.</button>
            </td>
        </tr>
                `;
                });

        tableHTML += `</tbody></table>`;
        clientListContainer.innerHTML = tableHTML;

        // setupRoleBasedUI(); // Викликати НЕ ПОТРІБНО для цих кнопок, але може бути потрібно для інших елементів сторінки
    }

    // Завантаження клієнтів з бекенду
    async function loadClients(searchTerm = '') {
        const currentToken = localStorage.getItem('accessToken'); // Потрібен токен для будь-якого запиту
        if (!clientListContainer) {
            console.error("Client list container not found.");
            return;
        }
        if (!currentToken) {
            console.error("Cannot load clients: token is missing.");
            clientListContainer.innerHTML = '<p>Помилка: Необхідна авторизація.</p>';
            return;
        }

        console.log(`Loading clients... Search term: "${searchTerm}"`);
        clientListContainer.innerHTML = '<p>Завантаження клієнтів...</p>';

        let url = 'http://localhost:7000/api/v1/clients/'; // Використовуємо новий префікс
        if (searchTerm) {
            url += `?search=${encodeURIComponent(searchTerm)}`;
        }

        try {
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${currentToken}` }
            });
            console.log("fffff")
            if (!response.ok) {
                console.log("wwwww")
                console.log(response)
                if (response.status === 401) throw new Error('Помилка авторизації (401).');
                throw new Error(`HTTP помилка! Статус: ${response.status}`);
            }
            console.log("3333333333")
            const clients = await response.json();
            console.log(".,,,,,,,,,,,,")
            console.log("Clients loaded:", clients);
            renderClientTable(clients);
        } catch (error) {
            console.error("Failed to load clients:", error);
            clientListContainer.innerHTML = `<p>Помилка завантаження клієнтів: ${error.message}</p>`;
        }
    }

    // Відкриття модального вікна для додавання/редагування клієнта
    function openClientForm(client = null) {
        if (!clientFormModal || !clientForm) {
            console.error("Client form modal or form element not found.");
            return;
        }
        console.log("Opening client form. Client data:", client);

        // Скидаємо форму та повідомлення про помилку
        clientForm.reset();
        if (clientFormError) clientFormError.textContent = '';
        if (clientIdInput) clientIdInput.value = '';

        if (client) {
            // Режим редагування
            if(clientFormTitle) clientFormTitle.textContent = 'Редагувати клієнта';
            if(clientIdInput) clientIdInput.value = client.client_id;

            document.getElementById('client-first-name').value = client.first_name ?? '';
            document.getElementById('client-last-name').value = client.last_name ?? '';
            document.getElementById('client-phone').value = client.phone_number ?? '';
            document.getElementById('client-email').value = client.email ?? '';
        } else {
            // Режим додавання
            if(clientFormTitle) clientFormTitle.textContent = 'Додати нового клієнта';
        }

        clientFormModal.classList.add('show');
    }

    // Закриття модального вікна клієнта
    function closeClientForm() {
        if (clientFormModal) {
            clientFormModal.classList.remove('show');
            console.log("Client form closed.");
        }
    }

    // Обробка відправки форми клієнта (додавання/редагування)
    async function saveClient(event) {
        event.preventDefault();
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) {
            if (clientFormError) clientFormError.textContent = 'Помилка: Необхідна авторизація.';
            console.error("Cannot save client: token is missing.");
            return;
        }
        if (!clientForm || !clientIdInput) return;

        if (clientFormError) clientFormError.textContent = '';

        const clientId = clientIdInput.value;
        const isEditing = !!clientId;
        console.log(`Saving client. Editing: ${isEditing}, ID: ${clientId}`);

        // Збираємо дані з форми
        const clientData = {
            first_name: document.getElementById('client-first-name')?.value.trim() || null,
            last_name: document.getElementById('client-last-name')?.value.trim() || null,
            phone_number: document.getElementById('client-phone')?.value.trim(),
            email: document.getElementById('client-email')?.value.trim() || null
        };

        // Проста валідація на клієнті
        let validationError = '';
        if (!clientData.phone_number) validationError += 'Номер телефону є обов\'язковим. ';
        // Проста перевірка email (браузер також валідує type="email")
        if (clientData.email && !/\S+@\S+\.\S+/.test(clientData.email)) {
             validationError += 'Некоректний формат Email. ';
        }
         // Можна додати валідацію формату телефону, якщо потрібно
        // if (clientData.phone_number && !/^\+?[0-9\s\-()]+$/.test(clientData.phone_number)) {
        //     validationError += 'Некоректний формат телефону. ';
        // }


        if (validationError) {
            if (clientFormError) clientFormError.textContent = validationError.trim();
            console.warn("Client form validation failed:", validationError);
            return;
        }

        // Для PUT краще відправляти тільки змінені дані, але API має обробляти exclude_unset=True
        // Наразі відправляємо всі дані, зібрані з форми
        let dataToSend = {};
         if (isEditing) {
              // Для PUT збираємо тільки ті поля, що є в формі
               dataToSend = clientData;
               // Можна додати логіку порівняння зі старими даними, щоб відправляти тільки зміни
         } else {
               // Для POST відправляємо всі зібрані дані
               dataToSend = clientData;
         }
         // Видаляємо null значення, якщо API НЕ очікує їх для очищення полів при PUT
          Object.keys(dataToSend).forEach(key => {
               if (dataToSend[key] === null && isEditing) { // Тільки для редагування і тільки якщо null
                   // delete dataToSend[key]; // Розкоментуйте, якщо API не приймає null для очищення
               }
          });


        const url = isEditing
            ? `http://localhost:7000/api/v1/clients/${clientId}`
            : 'http://localhost:7000/api/v1/clients/';
        const method = isEditing ? 'PUT' : 'POST';

        console.log(`Sending request to ${url} with method ${method}. Data:`, dataToSend);

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${currentToken}`
                },
                body: JSON.stringify(dataToSend)
            });

            if (!response.ok) {
                let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || errorDetail; // Часто API повертає деталі помилки
                } catch (e) { console.warn("Could not parse error response body."); }
                throw new Error(errorDetail);
            }

            console.log(`Client ${isEditing ? 'updated' : 'created'} successfully.`);
            closeClientForm();
            loadClients(clientSearchInput ? clientSearchInput.value.trim() : ''); // Оновлюємо список
        } catch (error) {
            console.error("Failed to save client:", error);
            if (clientFormError) clientFormError.textContent = `Помилка збереження: ${error.message}`;
        }
    }

    // Обробка видалення клієнта
    async function deleteClient(clientId) {
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) {
            alert('Помилка: Необхідна авторизація.');
            return;
        }
        if (!clientId) {
            console.error("Cannot delete client: ID is missing.");
            return;
        }

        console.log(`Attempting to delete client ID: ${clientId}`);
        if (!confirm(`Ви впевнені, що хочете видалити клієнта ID: ${clientId}? Це може бути неможливо, якщо у клієнта є замовлення.`)) {
            console.log("Client deletion cancelled by user.");
            return;
        }

        const url = `http://localhost:7000/api/v1/clients/${clientId}`;

        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${currentToken}` }
            });

            if (response.status === 204) { // Успішне видалення
                console.log(`Client ${clientId} deleted successfully.`);
                loadClients(clientSearchInput ? clientSearchInput.value.trim() : ''); // Оновлюємо список
                return;
            }

            // Якщо не 204, обробляємо як помилку
            let errorDetail = `HTTP помилка! Статус: ${response.status}`;
            try {
                const errorData = await response.json();
                errorDetail = errorData.detail || errorDetail; // Напр., помилка 409 Conflict, якщо є замовлення
            } catch (e) { console.warn("Could not parse error response body for delete client."); }
            throw new Error(errorDetail);

        } catch (error) {
            console.error("Failed to delete client:", error);
            alert(`Помилка видалення клієнта: ${error.message}`);
        }
    }


    // --- Налаштування слухачів подій для клієнтів ---

    // Кнопка Пошуку
    if (clientSearchButton) {
        clientSearchButton.addEventListener('click', () => {
            loadClients(clientSearchInput ? clientSearchInput.value.trim() : '');
        });
    }
    // Пошук при натисканні Enter
    if (clientSearchInput) {
        clientSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadClients(clientSearchInput.value.trim());
            }
        });
    }

    // Кнопка "Додати нового клієнта"
    if (addClientButton) {
        addClientButton.addEventListener('click', () => {
            openClientForm(); // Відкриваємо форму в режимі додавання
        });
    }

    // Відправка форми клієнта
    if (clientForm) {
        clientForm.addEventListener('submit', saveClient);
    }

    // Обробка кліків на кнопки редагування/видалення в таблиці клієнтів
    if (clientListContainer) {
        clientListContainer.addEventListener('click', async (event) => {
            const target = event.target;
            const clientId = target.dataset.id;

             // Перевірка ролі НЕ ПОТРІБНА, бо всі можуть редагувати/видаляти

            if (target.classList.contains('edit-client-btn') && clientId) {
                console.log(`Edit button clicked for client ID: ${clientId}`);
                const currentToken = localStorage.getItem('accessToken');
                if (!currentToken) { alert("Помилка: Необхідна авторизація."); return; }
                // Отримуємо деталі клієнта для редагування
                try {
                    const response = await fetch(`http://localhost:7000/api/v1/clients/${clientId}`, {
                        headers: { 'Authorization': `Bearer ${currentToken}` }
                    });
                    if (!response.ok) throw new Error('Не вдалося завантажити деталі клієнта');
                    const clientDetails = await response.json();
                    openClientForm(clientDetails); // Відкриваємо форму в режимі редагування
                } catch (error) {
                    console.error("Error fetching client details for edit:", error);
                    alert(`Не вдалося завантажити деталі клієнта для редагування: ${error.message}`);
                }
            } else if (target.classList.contains('delete-client-btn') && clientId) {
                console.log(`Delete button clicked for client ID: ${clientId}`);
                deleteClient(clientId); // Викликаємо функцію видалення
            }
        });
    }

    // Закриття модального вікна клієнта
    if (clientFormModal) {
        // Клік на фон
        clientFormModal.addEventListener('click', (event) => {
            if (event.target === clientFormModal) closeClientForm();
        });
        // Кнопка закриття (хрестик)
        const closeButton = clientFormModal.querySelector('.close-button');
        if (closeButton) closeButton.addEventListener('click', closeClientForm);
        // Кнопка "Cancel"
        const cancelButton = clientFormModal.querySelector('.cancel-button');
        if (cancelButton) cancelButton.addEventListener('click', closeClientForm);
    }


    // Додавання обробки для нової секції в loadSectionData
    // Знайдіть функцію loadSectionData і додайте case:
    /*
    function loadSectionData(sectionId) {
        console.log(`Loading data for section: ${sectionId}`);
        switch (sectionId) {
            // ... існуючі case ...
            case 'categories-content':
                loadCategories();
                break;
            case 'clients-content': // <-- Додати цей case
                loadClients();
                break;
            // ... інші case ...
            default:
                console.log(`No specific data load function for section: ${sectionId}`);
        }
    }
    */
    // Переконайтесь, що ви додали case 'clients-content': loadClients();
    // в існуючу функцію loadSectionData

    //=========================================================================//
    //=========== КІНЕЦЬ БЛОКУ УПРАВЛІННЯ КЛІЄНТАМИ ===========================//
    //=========================================================================//

    //=========================================================================//
    //========= ПОЧАТОК БЛОКУ УПРАВЛІННЯ СПІВРОБІТНИКАМИ =====================//
    //=========================================================================//

    console.log("Initializing Employee Management section...");

    // --- DOM елементи для співробітників ---
    const employeeSearchInput = document.getElementById('employee-search-input');
    const addEmployeeButton = document.getElementById('add-employee-button');
    const employeeFormModal = document.getElementById('employee-form-modal');
    const employeeForm = document.getElementById('employee-form');
    const employeeFormTitle = document.getElementById('employee-form-title');
    const employeeFormError = document.getElementById('employee-form-error');
    const employeeIdInput = document.getElementById('employee-id');
    const employeeRoleSelect = document.getElementById('employee-role');
    const employeeLocationSelect = document.getElementById('employee-location');
    const passwordInput = document.getElementById('employee-password');
    const passwordHelpText = document.getElementById('password-help');


    // --- Змінні для даних дропдаунів ---
    let rolesList = [];
    let locationsList = [];
    let isEmployeeDropdownDataFetched = false;

    // --- Функція завантаження даних для дропдаунів ---
    async function fetchEmployeeDropdownData() {
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken || isEmployeeDropdownDataFetched) return;
         // Перевіряємо чи користувач Менеджер або Адмін перед запитом?
         // Можна додати перевірку currentUser тут, якщо потрібно оптимізувати
        console.log("Fetching dropdown data for employees...");

        try {
            const [rolesRes, locationsRes] = await Promise.all([
                fetch(`http://localhost:7000/api/v1/employees/roles/list`, { headers: { 'Authorization': `Bearer ${currentToken}` } }),
                fetch(`http://localhost:7000/api/v1/employees/locations/list`, { headers: { 'Authorization': `Bearer ${currentToken}` } })
            ]);

            if (!rolesRes.ok) throw new Error(`Roles fetch failed: ${rolesRes.status}`);
            if (!locationsRes.ok) throw new Error(`Locations fetch failed: ${locationsRes.status}`);

            rolesList = await rolesRes.json();
            locationsList = await locationsRes.json();

            isEmployeeDropdownDataFetched = true;
            console.log("Employee dropdown data fetched successfully.");
            // Не заповнюємо одразу, заповнимо при відкритті форми
        } catch (error) {
            console.error("Error fetching employee dropdown data:", error);
            isEmployeeDropdownDataFetched = false;
             if(employeeFormError) employeeFormError.textContent = "Помилка завантаження списків ролей/локацій.";
        }
    }


    // --- Функції управління співробітниками ---

    // Відображення таблиці
    function renderEmployeeTable(employees) {
        if (!employeeListContainer) return;
         if (!employees || employees.length === 0) {
            employeeListContainer.innerHTML = '<p>Співробітників не знайдено.</p>';
            return;
        }

        // Перевіряємо, чи може поточний користувач редагувати/видаляти (Admin або Manager)
        const canManageEmployees = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Location Manager');

        let tableHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Ім'я</th>
                        <th>Прізвище</th>
                        <th>Телефон</th>
                        <th>Email</th>
                        <th>Роль</th>
                        <th>Локація</th>
                        ${canManageEmployees ? '<th>Дії</th>' : ''}
                    </tr>
                </thead>
                <tbody>
        `;

        // Знайдіть функцію renderEmployeeTable у main.js і замініть цикл forEach на цей:
employees.forEach(emp => {
    // Спочатку визначаємо HTML для кнопок, якщо вони потрібні
    let actionButtons = ''; // Порожній рядок для HTML кнопок
    
    // canManageEmployees має бути визначено раніше в функції
    // let canManageEmployees = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager'); 
    
    if (canManageEmployees) { // Перевіряємо загальний дозвіл на управління
        // Визначаємо, чи можна редагувати/видаляти *цього* співробітника
        let canEditThis = false;
        let canDeleteThis = false;

        if (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Location Manager') {
            canEditThis = true;
            canDeleteThis = (emp.employee_id != currentUser.employee_id); // Порівняння ID
        } else {
            if (emp.location_id == currentUser.location_id) { // Порівняння ID локацій
                if (emp.role_name !== 'Administrator' && emp.role_name !== 'Location Manager') {
                    canEditThis = true;
                    canDeleteThis = true;
                } else if (emp.employee_id == currentUser.employee_id) { // Порівняння ID
                    canEditThis = true;
                    canDeleteThis = false;
                }
            }
        }

        if (canEditThis) {
            // Додаємо пробіл після кнопки для кращого вигляду, якщо будуть обидві
            actionButtons += `<button class="action-button edit-employee-btn" data-id="${emp.employee_id}">Ред.</button> `; 
        }
        if (canDeleteThis) {
            actionButtons += `<button class="action-button delete-employee-btn" data-id="${emp.employee_id}">Вид.</button>`;
        }
    }

    // Тепер генеруємо весь рядок таблиці, використовуючи actionButtons
    // Переконайтесь, що всі `${...}` мають $ і немає зіпсованих символів
    tableHTML += `
        <tr>
            <td>${emp.employee_id}</td>
            <td>${emp.first_name ?? ''}</td>
            <td>${emp.last_name ?? ''}</td>
            <td>${emp.phone_number ?? 'N/A'}</td>
            <td>${emp.email ?? 'N/A'}</td>
            <td>${emp.role_name ?? 'N/A'}</td>
            <td>${emp.location_address ?? 'N/A'}</td>
            ${canManageEmployees ? `<td class="action-cell">${actionButtons.trim()}</td>` : ''} 
            
        </tr>
    `;
    // Примітка: Якщо canManageEmployees = false, комірка 'Дії' не буде додана. 
    // Це правильно, якщо ви також умовно додаєте заголовок 'Дії' <th>.
    // Перевірте початок renderEmployeeTable:
    /*
        let tableHTML = \`
            <table class="data-table">
                <thead>
                    <tr>
                        ... інші th ...
                        ${canManageEmployees ? '<th>Дії</th>' : ''} // <--- Заголовок теж має бути умовним
                    </tr>
                </thead>
                <tbody>
        \`;
    */
}); 

        tableHTML += `</tbody></table>`;
        employeeListContainer.innerHTML = tableHTML;
        setupRoleBasedUI(); // Потрібно викликати, щоб правильно показати/сховати кнопки з класом manager-only
    }


    // Завантаження співробітників
    // Завантаження співробітників
    async function loadEmployees(searchTerm = '') {
        const currentToken = localStorage.getItem('accessToken');
        if (!employeeListContainer) {
             console.error("Employee list container not found.");
             return;
        }
        if (!currentToken) {
            employeeListContainer.innerHTML = '<p>Помилка: Необхідна авторизація.</p>';
            return;
        }

        console.log(`Loading employees... Search term: "${searchTerm}"`);
        employeeListContainer.innerHTML = '<p>Завантаження співробітників...</p>';

        let url = `http://localhost:7000/api/v1/employees/`;
        if (searchTerm) {
            url += `?search=${encodeURIComponent(searchTerm)}`;
        }

        try {
            const response = await fetch(url, { headers: { 'Authorization': `Bearer ${currentToken}` } });
            if (!response.ok) {
                if (response.status === 401) throw new Error('Помилка авторизації (401).');
                // Бекенд поверне 403, якщо роль не дозволена *на бекенді*
                if (response.status === 403) throw new Error('Доступ заборонено сервером (403).');
                const errorData = await response.json().catch(() => ({})); // Спробувати отримати деталі
                throw new Error(errorData.detail || `HTTP помилка! Статус: ${response.status}`);
            }
            const employees = await response.json();
            console.log("Employees loaded:", employees);
            // Функція renderEmployeeTable тепер має враховувати роль для відображення кнопок
            renderEmployeeTable(employees);
        } catch (error) {
            console.error("Failed to load employees:", error);
            employeeListContainer.innerHTML = `<p>Помилка завантаження співробітників: ${error.message}</p>`;
        }
    }


    // Відкриття форми
   async function openEmployeeForm(employee = null) {
        if (!employeeFormModal || !employeeForm || !employeeRoleSelect || !employeeLocationSelect || !passwordInput || !passwordHelpText) return;

        // Завантажуємо дані для списків, якщо ще не завантажені
        await fetchEmployeeDropdownData();
        if (!isEmployeeDropdownDataFetched) {
            alert("Не вдалося завантажити дані для списків ролей/локацій.");
            return;
        }

        // Заповнюємо списки
        populateSelect(employeeRoleSelect, rolesList, 'role_id', 'role_name', 'Select Role...');
        populateSelect(employeeLocationSelect, locationsList, 'location_id', 'address', 'Select Location...');


        employeeForm.reset();
        if (employeeFormError) employeeFormError.textContent = '';
        if (employeeIdInput) employeeIdInput.value = '';

        // Налаштування поля пароля
        passwordInput.placeholder = "Leave blank to keep unchanged";
        passwordInput.required = false;
        passwordHelpText.style.display = 'none'; // Сховати підказку про обов'язковість

        if (employee) { // Режим редагування
            if(employeeFormTitle) employeeFormTitle.textContent = 'Редагувати співробітника';
            if(employeeIdInput) employeeIdInput.value = employee.employee_id;

            document.getElementById('employee-first-name').value = employee.first_name ?? '';
            document.getElementById('employee-last-name').value = employee.last_name ?? '';
            document.getElementById('employee-phone').value = employee.phone_number ?? '';
            document.getElementById('employee-email').value = employee.email ?? '';
            employeeRoleSelect.value = employee.role_id ?? '';
            employeeLocationSelect.value = employee.location_id ?? ''; // Може бути порожнім

            // Не заповнюємо пароль
             passwordInput.placeholder = "Leave blank to keep unchanged";
             passwordInput.required = false;
             passwordHelpText.style.display = 'none';

        } else { // Режим додавання
            if(employeeFormTitle) employeeFormTitle.textContent = 'Додати нового співробітника';
            // Пароль обов'язковий при створенні
            passwordInput.placeholder = "Enter password";
            passwordInput.required = true;
             passwordHelpText.style.display = 'block'; // Показати підказку
        }

         // Додаткові налаштування для Менеджера: обмежити вибір локації
         if (currentUser && currentUser.role_name === 'Location Manager' && currentUser.location_id) {
             employeeLocationSelect.value = currentUser.location_id;
             employeeLocationSelect.disabled = true; // Заборонити зміну
             // Можна також обмежити вибір ролей
         } else {
              employeeLocationSelect.disabled = false; // Дозволити зміну для Адміна
         }


        employeeFormModal.classList.add('show');
    }


    // Закриття форми
    function closeEmployeeForm() {
        if (employeeFormModal) {
             // Розблокувати select локації про всяк випадок
             if(employeeLocationSelect) employeeLocationSelect.disabled = false;
            employeeFormModal.classList.remove('show');
        }
    }

    // Збереження співробітника
    async function saveEmployee(event) {
        event.preventDefault();
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken || !currentUser || !employeeForm || !employeeIdInput || !passwordInput) return;
         if (employeeFormError) employeeFormError.textContent = '';

        const employeeId = employeeIdInput.value;
        const isEditing = !!employeeId;

        // Збираємо дані
        const employeeReqData = {
            first_name: document.getElementById('employee-first-name')?.value.trim(),
            last_name: document.getElementById('employee-last-name')?.value.trim(),
            phone_number: document.getElementById('employee-phone')?.value.trim(),
            email: document.getElementById('employee-email')?.value.trim(),
            role_id: parseInt(employeeRoleSelect?.value) || null,
            location_id: parseInt(employeeLocationSelect?.value) || null,
            password: passwordInput.value // Пароль беремо як є
        };


        // --- Валідація ---
        let validationError = '';
        if (!employeeReqData.first_name) validationError += 'Ім\'я обов\'язкове. ';
        if (!employeeReqData.last_name) validationError += 'Прізвище обов\'язкове. ';
        if (!employeeReqData.phone_number) validationError += 'Телефон обов\'язковий. ';
        if (!employeeReqData.email || !/\S+@\S+\.\S+/.test(employeeReqData.email)) validationError += 'Некоректний Email. ';
        if (!employeeReqData.role_id) validationError += 'Роль обов\'язкова. ';
        // Пароль: обов'язковий тільки при створенні, має бути > N символів
         if (!isEditing && !employeeReqData.password) {
             validationError += 'Пароль обов\'язковий при створенні. ';
         }
         if (employeeReqData.password && employeeReqData.password.length < 6) { // Перевірка довжини, якщо пароль введено
             validationError += 'Пароль має містити мінімум 6 символів. ';
         }

        if (validationError) {
             if (employeeFormError) employeeFormError.textContent = validationError.trim(); return;
        }
        // --- Кінець валідації ---


        // Формуємо дані для відправки (EmployeeCreate або EmployeeUpdate)
        let dataToSend = {};
        let url = '';
        let method = '';

        if (isEditing) {
            method = 'PUT';
            url = `http://localhost:7000/api/v1/employees/${employeeId}`;
            // Для PUT формуємо тільки ті поля, що є в EmployeeUpdate
            dataToSend = {
                 first_name: employeeReqData.first_name,
                 last_name: employeeReqData.last_name,
                 phone_number: employeeReqData.phone_number,
                 email: employeeReqData.email,
                 role_id: employeeReqData.role_id,
                 location_id: employeeReqData.location_id
             };
            // Додаємо пароль тільки якщо він був введений
             if (employeeReqData.password) {
                 dataToSend.password = employeeReqData.password;
             }
            // Тут можна додати логіку, щоб відправляти тільки змінені поля,
            // але припускаємо, що API обробить exclude_unset=True
        } else {
             method = 'POST';
             url = `http://localhost:7000/api/v1/employees/`;
             // Для POST відправляємо всі поля з EmployeeCreate
             dataToSend = employeeReqData; // Включаючи пароль
        }

        console.log(`Sending request to ${url} with method ${method}`);

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
                body: JSON.stringify(dataToSend)
            });

             if (!response.ok) {
                let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
                throw new Error(errorDetail);
            }

            console.log(`Employee ${isEditing ? 'updated' : 'created'} successfully.`);
            closeEmployeeForm();
            loadEmployees(employeeSearchInput ? employeeSearchInput.value.trim() : '');

        } catch (error) {
             console.error("Failed to save employee:", error);
             if (employeeFormError) employeeFormError.textContent = `Помилка: ${error.message}`;
        }
    }

    // Видалення співробітника
    async function deleteEmployee(employeeId) {
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken || !currentUser) { alert('Помилка: Необхідна авторизація.'); return; }
        if (!employeeId) return;

         // Додаткова перевірка на фронтенді (чи можна видаляти цього юзера)
         // Бекенд все одно перевірить, але це покращує UX
         if (employeeId == currentUser.employee_id) { // Порівнюємо як рядки або числа
             alert("Ви не можете видалити себе.");
             return;
         }
         // Можна додати перевірку ролі та локації як в renderEmployeeTable, якщо потрібно

        console.log(`Attempting to delete employee ID: ${employeeId}`);
         if (!confirm(`Видалити співробітника ID: ${employeeId}?`)) return;

         const url = `http://localhost:7000/api/v1/employees/${employeeId}`;

        try {
             const response = await fetch(url, { method: 'DELETE', headers: { 'Authorization': `Bearer ${currentToken}` } });
             if (response.status === 204) {
                 console.log(`Employee ${employeeId} deleted successfully.`);
                 loadEmployees(employeeSearchInput ? employeeSearchInput.value.trim() : '');
             } else if (!response.ok) {
                 let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                 try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
                 throw new Error(errorDetail);
             }
        } catch (error) {
             console.error("Failed to delete employee:", error);
             alert(`Помилка видалення: ${error.message}`);
        }
    }

    // --- Слухачі подій для співробітників ---
    if (employeeSearchButton) employeeSearchButton.addEventListener('click', () => loadEmployees(employeeSearchInput?.value.trim()));
    if (employeeSearchInput) employeeSearchInput.addEventListener('keypress', (e) => e.key === 'Enter' && loadEmployees(employeeSearchInput.value.trim()));
    if (addEmployeeButton) addEmployeeButton.addEventListener('click', () => openEmployeeForm());
    if (employeeForm) employeeForm.addEventListener('submit', saveEmployee);
    if (employeeListContainer) employeeListContainer.addEventListener('click', async (event) => {
         const target = event.target;
         const employeeId = target.dataset.id;
         const canManageEmployees = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Location Manager');

        if (!canManageEmployees) return; // Якщо не адмін/менеджер, нічого не робити

         if (target.classList.contains('edit-employee-btn') && employeeId) {
             // Перевірка прав на редагування *цього* співробітника (на фронтенді - необов'язково, бекенд перевірить)
             console.log(`Edit button clicked for employee ID: ${employeeId}`);
             const currentToken = localStorage.getItem('accessToken');
             if (!currentToken) { alert("Помилка: Необхідна авторизація."); return; }
             try {
                const response = await fetch(`http://localhost:7000/api/v1/employees/${employeeId}`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
                if(response.status === 403) throw new Error('Доступ заборонено');
                  console.log(response)
                  if (!response.ok) throw new Error('Не вдалося завантажити дані співробітника');
                  const employeeDetails = await response.json();
                  openEmployeeForm(employeeDetails);
             } catch (error) {
                  console.error("Error fetching employee details for edit:", error);
                  alert(`Не вдалося відкрити форму редагування: ${error.message}`);
             }
         } else if (target.classList.contains('delete-employee-btn') && employeeId) {
              // Перевірка прав на видалення *цього* співробітника (на фронтенді - необов'язково)
              console.log(`Delete button clicked for employee ID: ${employeeId}`);
             deleteEmployee(employeeId);
         }
     });
    if (employeeFormModal) {
         employeeFormModal.addEventListener('click', (event) => event.target === employeeFormModal && closeEmployeeForm());
         employeeFormModal.querySelector('.close-button')?.addEventListener('click', closeEmployeeForm);
         employeeFormModal.querySelector('.cancel-button')?.addEventListener('click', closeEmployeeForm);
    }


    //=========================================================================//
    //=========== КІНЕЦЬ БЛОКУ УПРАВЛІННЯ СПІВРОБІТНИКАМИ =====================//
    //=========================================================================//


    //=========================================================================//
    //=========== ПОЧАТОК БЛОКУ СТОКУ ======================================//
    //=========================================================================//

    async function loadStockData(bookTitle = '') {
        const currentToken = localStorage.getItem('accessToken');
        const stockListContainer = document.getElementById('stock-list-container');
        if (!stockListContainer || !currentToken) {
            if(stockListContainer) stockListContainer.innerHTML = '<p>Error: Authorization required or container not found.</p>';
            return;
        }
    
        stockListContainer.innerHTML = '<p>Loading stock levels...</p>';
        let url = 'http://localhost:7000/api/v1/stock/';
        const params = new URLSearchParams();
        if (bookTitle) {
            params.append('book_title', bookTitle);
        }
        // Для Адміна можна додати параметр location_id, якщо потрібно
        // if (currentUser.role_name === 'Administrator' && selectedLocationId) {
        //    params.append('location_id', selectedLocationId);
        // }
    
        const queryString = params.toString();
        if (queryString) {
            url += `?${queryString}`;
        }
    
        try {
            const response = await fetch(url, { headers: { 'Authorization': `Bearer ${currentToken}` } });
            if (!response.ok) {
                 const errorData = await response.json().catch(() => ({}));
                 throw new Error(errorData.detail || `HTTP Error! Status: ${response.status}`);
            }
            const stockData = await response.json();
            console.log(stockData)
            renderStockTable(stockData);
        } catch (error) {
            console.error("Failed to load stock data:", error);
            stockListContainer.innerHTML = `<p>Error loading stock data: ${error.message}</p>`;
        }
    }
    
    function renderStockTable(stockData) {
        const stockListContainer = document.getElementById('stock-list-container');
        if (!stockListContainer) return;
    
        if (!stockData || stockData.length === 0) {
            stockListContainer.innerHTML = '<p>No stock records found.</p>';
            return;
        }
    
        const isManager = currentUser && currentUser.role_name === 'Location Manager';
        const managerLocationId = currentUser?.location_id;
    
        let tableHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Book Title</th>
                        <th>Location</th>
                        <th>Quantity</th>
                        ${isManager ? '<th>Actions</th>' : ''}
                    </tr>
                </thead>
                <tbody>
        `;
    
        stockData.forEach(item => {
            // Перевірка наявності вкладених об'єктів перед доступом до їх властивостей
            const bookId = item.book?.book_id;
            const locationId = item.location?.location_id;
            const bookTitle = item.book?.title ?? 'N/A';
            const locationAddress = item.location?.address ?? 'N/A';
            const currentQuantity = item.quantity ?? 0; // Якщо quantity може бути null/undefined
    
            // Якщо bookId або locationId відсутні, можливо, краще пропустити цей рядок або показати помилку
            if (bookId === undefined || locationId === undefined) {
                console.warn("Skipping stock item due to missing book or location ID:", item);
                return; // Пропускаємо цей елемент масиву
            }
    
            const canEdit = isManager && (locationId === managerLocationId);
    
            // --- ЗМІНЕНО: Виправлено генерацію рядка таблиці ---
            tableHTML += `
                 <tr data-book-id="${bookId}" data-location-id="${locationId}">
                <td>${bookTitle}</td>
                <td>${locationAddress}</td>
                <td class="quantity-cell">${currentQuantity}</td>
                ${isManager ? `
                    <td class="action-cell update-stock-cell">
                            <input type="number" class="quantity-input" value="${currentQuantity}" min="0" step="1" style="width: 60px; margin-right: 5px;" aria-label="New quantity">
                            <button class="action-button save-stock-btn" title="Save new quantity">Save</button>
                            <span class="update-status" style="display: none; margin-left: 5px;"></span>
                    </td>
                ` : ''} 
            </tr>
        `;
            // --- КІНЕЦЬ ЗМІНИ ---
        });
    
        tableHTML += `</tbody></table>`;
        stockListContainer.innerHTML = tableHTML;
    }

    async function updateStockQuantity(bookId, locationId, newQuantity) {
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) {
            return { success: false, message: 'Authorization required.' };
        }
        if (isNaN(newQuantity) || newQuantity < 0) {
            return { success: false, message: 'Invalid quantity. Must be a non-negative number.' };
        }
    
        // --- ЗМІНЕНО: Виправлено URL ---
        const url = `http://localhost:7000/api/v1/stock/${bookId}/${locationId}`;
        // --- КІНЕЦЬ ЗМІНИ ---
        const data = { quantity: newQuantity };
    
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${currentToken}`
                },
                body: JSON.stringify(data)
            });
    
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP Error! Status: ${response.status}`);
            }
    
            const updatedStock = await response.json();
            console.log("Stock updated successfully:", updatedStock);
            return { success: true, updatedQuantity: updatedStock.quantity };
    
        } catch (error) {
            console.error("Failed to update stock quantity:", error);
            return { success: false, message: error.message };
        }
    }
    

    if (stockListContainer) {
        stockListContainer.addEventListener('click', async (event) => {
            if (event.target.classList.contains('save-stock-btn')) {
                const button = event.target;
                const row = button.closest('tr'); // Знаходимо рядок таблиці
                const input = row.querySelector('.quantity-input');
                const statusSpan = row.querySelector('.update-status'); // Елемент для статусу
                const quantityCell = row.querySelector('.quantity-cell'); // Комірка з поточною кількістю

                if (!row || !input || !statusSpan || !quantityCell) return;

                const bookId = row.dataset.bookId;
                const locationId = row.dataset.locationId;
                const newQuantity = parseInt(input.value, 10);

                // Базова перевірка на фронтенді
                if (isNaN(newQuantity) || newQuantity < 0) {
                    statusSpan.textContent = 'Invalid value!';
                    statusSpan.style.color = 'red';
                    statusSpan.style.display = 'inline';
                    return;
                }

                button.disabled = true; // Блокуємо кнопку під час запиту
                statusSpan.textContent = 'Saving...';
                statusSpan.style.color = 'orange';
                statusSpan.style.display = 'inline';

                const result = await updateStockQuantity(bookId, locationId, newQuantity);

                if (result.success) {
                    statusSpan.textContent = 'Saved!';
                    statusSpan.style.color = 'green';
                    // Оновлюємо значення в комірці кількості та в полі вводу
                    quantityCell.textContent = result.updatedQuantity;
                    input.value = result.updatedQuantity; // Синхронізуємо поле вводу
                    setTimeout(() => { statusSpan.style.display = 'none'; }, 2000); // Ховаємо повідомлення через 2 сек
                } else {
                    statusSpan.textContent = `Error: ${result.message}`;
                    statusSpan.style.color = 'red';
                     // Не ховаємо повідомлення про помилку автоматично
                }
                button.disabled = false; // Розблоковуємо кнопку
            }
        });}
     
    //=========================================================================//
    //=========== КІНЕЦЬ БЛОКУ СТОКУ ======================================//
    //=========================================================================//

    //=========================================================================//
    //             START OF CLIENT MANAGEMENT BLOCK                          //
    //=========================================================================//
    console.log("Initializing Client Management section...");

    // --- Отримуємо DOM Елементи для Клієнтів ---
    // --- Функції Управління Клієнтами ---

    /**
     * Відображає таблицю клієнтів.
     * @param {Array<object>} clients - Масив об'єктів клієнтів з API.
     */
    function renderClientTable(clients) {
        if (!clientListContainer) {
            console.error("Client list container not found!");
            return;
        }
        clientListContainer.innerHTML = ''; // Очищення

        if (!clients || clients.length === 0) {
            clientListContainer.innerHTML = '<p>Клієнтів не знайдено.</p>';
            return;
        }

        // Перевірка ролі для відображення стовпця "Дії"
        // Використовуємо змінну isAdminOrManager, визначену раніше
        const showActions = currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager';


        let tableHTML = `
            <table class="data-table client-table"> 
                <thead>
                    <tr>
                        <th>Ім'я</th>
                        <th>Прізвище</th>
                        <th>Email</th>
                        <th>Телефон</th>
                        ${showActions ? '<th>Дії</th>' : ''}
                    </tr>
                </thead>
                <tbody>
        `;

        clients.forEach(client => {
            tableHTML += `
                <tr>
                    <td>${client.first_name ?? ''}</td>
                    <td>${client.last_name ?? ''}</td>
                    <td>${client.email ?? ''}</td>
                    <td>${client.phone_number ?? ''}</td>
                    ${showActions ? `
                    <td class="action-cell">
                        <button class="action-button edit-btn" data-id="${client.client_id}">Ред.</button>
                        <button class="action-button delete-btn" data-id="${client.client_id}">Вид.</button>
                    </td>
                    ` : ''}
                </tr>
            `;
        });

        tableHTML += `</tbody></table>`;
        clientListContainer.innerHTML = tableHTML;
    }

    /**
     * Відображає таблицю клієнтів.
     * @param {Array<object>} clients - Масив об'єктів клієнтів з API.
     */
    async function loadClients(searchTerm = '') {
        const currentToken = localStorage.getItem('accessToken'); // Завжди перевіряємо токен
        if (!clientListContainer) {
            console.error("Client list container element not found.");
            return;
        }
        if (!currentToken) {
            console.error("Cannot load clients: token is missing.");
            clientListContainer.innerHTML = '<p>Помилка авторизації. Неможливо завантажити клієнтів.</p>';
            return;
        }

        clientListContainer.innerHTML = '<p>Завантаження клієнтів...</p>';
        // Перевірте правильність URL вашого API
        let url = 'http://localhost:7000/api/v1/clients';
        if (searchTerm) {
            // Припускаємо, що API підтримує пошук за іменем, прізвищем або email
            url += `?search=${encodeURIComponent(searchTerm)}`;
        }

        try {
            const response = await fetch(url, { headers: { 'Authorization': `Bearer ${currentToken}` } });
            if (!response.ok) {
                 let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                 try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
                 throw new Error(errorDetail);
            }
            const clients = await response.json();
            console.log("Clients loaded:", clients);
            renderClientTable(clients); // Відображаємо таблицю
        } catch (error) {
            console.error("Failed to load clients:", error);
            clientListContainer.innerHTML = `<p>Помилка завантаження клієнтів: ${error.message}</p>`;
        }
    }

    /**
     * Відкриває модальну форму для додавання/редагування клієнта.
     * @param {object|null} [client=null] - Об'єкт клієнта для редагування, або null для додавання.
     */
    function openClientForm(client = null) {
        if (!clientFormModal || !clientForm) {
            console.error("Client form modal or form element not found.");
            return;
        }
        clientForm.reset(); // Очищення полів форми
        if(clientFormError) clientFormError.textContent = ''; // Очищення помилок
        if(clientIdInput) clientIdInput.value = ''; // Очищення прихованого ID

        if (client) { // Режим редагування
            if(clientFormTitle) clientFormTitle.textContent = 'Редагувати клієнта';
            if(clientIdInput) clientIdInput.value = client.client_id;
            // Заповнюємо поля форми (переконайтесь, що ID елементів правильні)
            if(clientFirstNameInput) clientFirstNameInput.value = client.first_name ?? '';
            if(clientLastNameInput) clientLastNameInput.value = client.last_name ?? '';
            if(clientEmailInput) clientEmailInput.value = client.email ?? '';
            if(clientPhoneInput) clientPhoneInput.value = client.phone_number ?? '';
        } else { // Режим додавання
            if(clientFormTitle) clientFormTitle.textContent = 'Додати нового клієнта';
        }
        clientFormModal.classList.add('show'); // Показуємо модальне вікно
    }

    /**
     * Закриває модальну форму клієнта.
     */
    function closeClientForm() {
        if (clientFormModal) {
             clientFormModal.classList.remove('show');
             console.log("Client form closed.");
        }
     }

    /**
     * Обробляє відправку форми клієнта (додавання або редагування).
     * @param {Event} event - Подія відправки форми.
     */
    /**
     * Обробляє відправку форми клієнта (додавання або редагування).
     * @param {Event} event - Подія відправки форми.
     */
    async function saveClient(event) {
        event.preventDefault();
        const currentToken = localStorage.getItem('accessToken');

        // !!! ВИПРАВЛЕНО: Перевіряємо роль напряму через currentUser !!!
        const canPerformAction = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager');

        // Використовуємо canPerformAction у перевірці
        if (!currentToken || !canPerformAction) {
            if(clientFormError) clientFormError.textContent = 'Помилка: Необхідна авторизація або недостатньо прав.';
            console.error("Cannot save client: token or required role missing.");
            return;
        }

        // Перевірка наявності форми та необхідних елементів
        if (!clientForm || !clientIdInput /* || !clientLastNameInput || !clientEmailInput */) { // Перевірте, чи всі потрібні елементи існують
            console.error("Client form or required inputs missing.");
            if(clientFormError) clientFormError.textContent = 'Помилка: Форма або обов\'язкові поля відсутні.';
            return;
        }
        if(clientFormError) clientFormError.textContent = ''; // Очищення помилок

        const clientId = clientIdInput ? clientIdInput.value : null;
        const isEditing = !!clientId;

        // Збір даних з форми
        const clientData = {
            first_name: clientFirstNameInput?.value.trim() || null,
            last_name: clientLastNameInput?.value.trim(), // Припускаємо, що прізвище обов'язкове
            email: clientEmailInput?.value.trim() || null,
            phone_number: clientPhoneInput?.value.trim() || null
        };

        // Проста валідація на клієнті
        let validationError = '';
        if (!clientData.last_name) validationError += 'Прізвище є обов\'язковим. '; // Приклад
        // Додайте інші валідації за потребою (наприклад, для email, телефону)
        if (clientData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(clientData.email)) {
            validationError += 'Некоректний формат Email. ';
        }

        if (validationError) {
             if(clientFormError) clientFormError.textContent = validationError.trim();
             console.warn("Client form validation failed:", validationError);
             return;
        }

        // Визначення URL та методу запиту
        const url = isEditing ? `http://localhost:7000/api/v1/clients/${clientId}` : 'http://localhost:7000/api/v1/clients';
        const method = isEditing ? 'PUT' : 'POST';
        console.log(`Saving client (${method}) to ${url}`);

        // Формуємо дані для відправки
        let dataToSend = {...clientData};
        if (isEditing) {
            // Для PUT можна видалити null значення, якщо API не приймає їх для оновлення
            Object.keys(dataToSend).forEach(key => {
                if (dataToSend[key] === null) {
                    // delete dataToSend[key]; // Розкоментуйте, якщо бекенд не обробляє null при оновленні
                }
            });
        }


        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
                body: JSON.stringify(dataToSend) // Відправляємо підготовлені дані
            });
            if (!response.ok) {
                let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
                throw new Error(errorDetail);
            }
            console.log(`Client ${isEditing ? 'updated' : 'created'} successfully.`);
            closeClientForm();
            // Перезавантаження списку, зберігаючи пошуковий запит
            loadClients(clientSearchInput ? clientSearchInput.value.trim() : '');
        } catch (error) {
            console.error("Failed to save client:", error);
            if (clientFormError) clientFormError.textContent = `Помилка збереження клієнта: ${error.message}`;
        }
    }

    /**
     * Видаляє клієнта після підтвердження.
     * @param {string|number} clientId - ID клієнта для видалення.
     */
    async function deleteClient(clientId) {
        const currentToken = localStorage.getItem('accessToken');
        // Перевірка прав: тільки Адмін або Менеджерconst canPerformAction = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager');
        const canPerformAction = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager');

        if (!currentToken || !canPerformAction || !clientId) {
            alert('Помилка: Необхідна авторизація, недостатньо прав або недійсний ID.');
            console.error("Cannot delete client: token, required role or ID missing.");
            return;
        }
        // Запит підтвердження
        if (!confirm(`Ви впевнені, що хочете видалити клієнта ID: ${clientId}?`)) {
             console.log("Client deletion cancelled by user.");
             return;
        }

        // Перевірте правильність URL вашого API
        const url = `http://localhost:7000/api/v1/clients/${clientId}`;
        console.log(`Deleting client from ${url}`);
        try {
            const response = await fetch(url, { method: 'DELETE', headers: { 'Authorization': `Bearer ${currentToken}` } });
            // Перевірка успішного видалення (204 No Content або 200 OK)
            if (!response.ok && response.status !== 204) {
                let errorDetail = `HTTP помилка! Статус: ${response.status}`;
                try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
                throw new Error(errorDetail);
            }
            console.log(`Client ${clientId} deleted successfully.`);
            // Перезавантаження списку, зберігаючи пошуковий запит
            loadClients(clientSearchInput ? clientSearchInput.value.trim() : '');
        } catch (error) {
            console.error("Failed to delete client:", error);
            alert(`Помилка видалення клієнта: ${error.message}`);
        }
    }

    // --- Обробники Подій для Клієнтів ---

    // Кнопка пошуку
    if (clientSearchButton) {
         clientSearchButton.addEventListener('click', () => loadClients(clientSearchInput ? clientSearchInput.value.trim() : ''));
    }
    // Пошук при натисканні Enter
    if (clientSearchInput) {
         clientSearchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') loadClients(clientSearchInput.value.trim()); });
    }
    // Кнопка "Додати нового клієнта"
    if (addClientButton) {
         // Кнопка видима для всіх, але дію виконуємо тільки якщо є права
         addClientButton.addEventListener('click', () => {
            const canPerformAction = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager');
            if (!canPerformAction){
                 alert("Недостатньо прав для додавання клієнта.");
                 return;
             }
             openClientForm();
         });

    }
    // Відправка форми
    if (clientForm) {
         clientForm.addEventListener('submit', saveClient);
     }
    // Делегування подій для кнопок Редагувати/Видалити у списку
    if (clientListContainer) {
        clientListContainer.addEventListener('click', async (event) => {
            const target = event.target;
            const clientId = target.dataset.id;
            // Перевіряємо права перед дією
            const canPerformAction = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager');

            if (target.classList.contains('edit-btn') && clientId) {
                if (!canPerformAction) {
                     console.warn("Edit button clicked by unauthorized user.");
                     return;
                 }
                const currentToken = localStorage.getItem('accessToken');
                if(!currentToken) { alert("Authorization required."); return; }
                 try { // Отримуємо повні дані клієнта для редагування
                     // Перевірте правильність URL вашого API
                     const response = await fetch(`http://localhost:7000/api/v1/clients/${clientId}`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
                     if (!response.ok) throw new Error('Не вдалося завантажити деталі клієнта');
                     const clientDetails = await response.json();
                     openClientForm(clientDetails); // Відкриваємо форму з отриманими даними
                 } catch (error) {
                      console.error("Error fetching client details for edit:", error);
                      alert(`Помилка завантаження деталей клієнта: ${error.message}`);
                 }
            } else if (target.classList.contains('delete-btn') && clientId) {
                 if (!canPerformAction) {
                    console.warn("Delete button clicked by unauthorized user.");
                    return;
                 }
                 deleteClient(clientId); // Викликаємо функцію видалення
            }
        });
    }
    // Обробники закриття модального вікна
    if (clientFormModal) {
        // Закриття по кліку на фон
        clientFormModal.addEventListener('click', (event) => { if (event.target === clientFormModal) closeClientForm(); });
        // Кнопка закриття (Х)
        const closeBtn = clientFormModal.querySelector('.close-button');
        if(closeBtn) closeBtn.addEventListener('click', closeClientForm);
        // Кнопка "Cancel"
        const cancelBtn = clientFormModal.querySelector('.cancel-button');
        if(cancelBtn) cancelBtn.addEventListener('click', closeClientForm);
    }

    if (clientsContentSectionObserverTarget) {
        console.log("Setting up MutationObserver for clients section.");
        observer.observe(clientsContentSectionObserverTarget, { attributes: true });
        // Перевіряємо, чи секція вже активна при ініціалізації
        if (clientsContentSectionObserverTarget.classList.contains('active')) {
            console.log("Clients section already active on init, loading clients...");
            loadClients();
        }
    } else { console.error("Clients content section not found for MutationObserver!"); }


    //=========================================================================//
    //             END OF CLIENT MANAGEMENT BLOCK                            //
    //=========================================================================//
    

    //===============================================================//
    //             START OF ORDER MANAGEMENT BLOCK                           //
    //=========================================================================//
console.log("Initializing Order Management section...");

// --- Функції Управління Замовленнями ---

/**
 * Форматує статус замовлення для відображення.
 * @param {string} status - Статус з API.
 * @returns {string} - Відформатований статус.
 */
function formatOrderStatus(status) {
    if (!status) return 'N/A';
    // Простий приклад, можна додати класи для кольорів
    return status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * Відображає таблицю замовлень.
 * @param {Array<object>} orders - Масив об'єктів замовлень з API.
 */
function renderOrderTable(orders) {
    // Перевірка контейнера
    if (!orderListContainer) {
        console.error("Order list container (#order-list-container) not found!");
        return;
    }
    orderListContainer.innerHTML = ''; // Очищення перед рендерингом

    // Перевірка наявності даних
    if (!orders || orders.length === 0) {
        orderListContainer.innerHTML = '<p>Замовлень не знайдено.</p>';
        return;
    }

    // Перевірка прав поточного користувача (припускаємо, що currentUser вже завантажений)
    if (!currentUser) {
        console.error("renderOrderTable: currentUser is not available.");
        orderListContainer.innerHTML = '<p>Помилка: Не вдалося визначити права користувача.</p>';
        return;
    }
    // Припускаємо, що тільки Адмін/Менеджер можуть бачити деталі/оновлювати
    const canManageOrders = currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager';

    // Початок формування HTML таблиці
    let tableHTML = `
        <table class="data-table order-table">
            <thead>
                <tr>
                    <th>Order ID</th>
                    <th>Client</th>
                    <th>Order Date</th>
                    <th>Status</th>
                    <th>Receipt Number</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `; // Відкриваємо tbody тут

    // Цикл по замовленнях
    orders.forEach(order => {
        // Форматування дати
        const orderDateFormatted = order.order_date
            ? new Date(order.order_date).toLocaleString('uk-UA', { dateStyle: 'short', timeStyle: 'short' })
            : 'N/A';

        // Формування імені клієнта
        const clientName = order.client_name || // Спочатку беремо з OrderList, якщо є
                         (order.client?.first_name || order.client?.last_name
                            ? `${order.client.first_name ?? ''} ${order.client.last_name ?? ''}`.trim()
                            : (order.client?.email || `Client ID: ${order.client_id}` || 'N/A'));

        // Формування рядка таблиці з правильною інтерполяцією
        tableHTML += `
            <tr>
                <td>${order.order_id}</td>
                <td>${clientName}</td>
                <td>${orderDateFormatted}</td>
                <td>${formatOrderStatus(order.status)}</td>
                <td>${order.receipt_number ?? 'N/A'}</td> 
                <td class="action-cell">
                    <button class="action-button view-details-btn" data-id="${order.order_id}">Details</button>
                    ${canManageOrders ? `
                    ` : ''}
                </td>
            </tr>
        `; // Закриття </tr>
    }); // Кінець forEach

    tableHTML += `</tbody></table>`; // Закриваємо tbody та table ПІСЛЯ циклу

    orderListContainer.innerHTML = tableHTML; // Вставляємо готовий HTML
}
async function loadOrders() {
    const currentToken = localStorage.getItem('accessToken');
    if (!orderListContainer || !currentToken) {
        if(orderListContainer) orderListContainer.innerHTML = '<p>Помилка: Необхідна авторизація.</p>';
        console.log("dddddddd")
        return;
    }

    const searchTerm = orderSearchInput ? orderSearchInput.value.trim() : '';
    const statusFilter = orderStatusFilter ? orderStatusFilter.value : '';
    const dateFrom = orderDateFromInput ? orderDateFromInput.value : '';
    const dateTo = orderDateToInput ? orderDateToInput.value : '';

    console.log(`Loading orders... Search: "<span class="math-inline">\{searchTerm\}", Status\: "</span>{statusFilter}", From: "<span class="math-inline">\{dateFrom\}", To\: "</span>{dateTo}"`);
    orderListContainer.innerHTML = '<p>Завантаження замовлень...</p>';

    // Формуємо URL з параметрами
    // Припускаємо, що API ендпоінт для замовлень /api/v1/orders/
    const params = new URLSearchParams();
    if (searchTerm) params.append('search', searchTerm);
    if (statusFilter) params.append('status', statusFilter);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);
    // Бекенд має автоматично фільтрувати за локацією для Менеджера на основі токена

    const url = `http://localhost:7000/api/v1/orders/?${params.toString()}`;

    try {
        const response = await fetch(url, { headers: { 'Authorization': `Bearer ${currentToken}` } });
        if (!response.ok) {
            let errorDetail = `HTTP помилка! Статус: ${response.status}`;
            try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
            throw new Error(errorDetail);
        }
        const orders = await response.json();
        console.log("Orders loaded:", orders);
        renderOrderTable(orders);
    } catch (error) {
        console.error("Failed to load orders:", error);
        orderListContainer.innerHTML = `<p>Помилка завантаження замовлень: ${error.message}</p>`;
    }
}



async function showOrderDetails(orderId) {
    const currentToken = localStorage.getItem('accessToken');
    // Перевірка наявності елементів модального вікна, токена та ID
    if (!orderDetailsModal || !orderDetailsContent || !orderDetailsTitle || !currentToken || !orderId) {
        console.error("Order details modal elements or token/ID missing.");
        return;
    }

    console.log(`Showing details for order ID: ${orderId}`);
    // Встановлюємо початковий стан модального вікна
    orderDetailsContent.innerHTML = '<p>Завантаження деталей...</p>';
    orderDetailsTitle.textContent = `Order Details #${orderId}`;
    if(orderDetailsError) orderDetailsError.textContent = '';
    if(orderStatusUpdateMessage) orderStatusUpdateMessage.textContent = '';
    if(orderStatusUpdateSection) orderStatusUpdateSection.style.display = 'none';

    // Припускаємо ендпоінт /api/v1/orders/{order_id}
    const url = `http://localhost:7000/api/v1/orders/${orderId}`;

    try {
        const response = await fetch(url, { headers: { 'Authorization': `Bearer ${currentToken}` } });
        if (!response.ok) {
            let errorDetail = `HTTP помилка! Статус: ${response.status}`;
            try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
            throw new Error(errorDetail);
        }
        const order = await response.json(); // Очікуємо отримати схему OrderRead з бекенду
        console.log("Order details loaded:", order);

        // Розрахунок загальної суми на фронтенді (оскільки в БД її немає)
        let calculatedTotal = 0;
        if (order.items && order.items.length > 0) {
            calculatedTotal = order.items.reduce((sum, item) => {
                return sum + (item.quantity ?? 0) * (item.price_at_purchase ?? 0);
            }, 0);
        }

        // --- Формування HTML для деталей ---
        let detailsHTML = `
            <p><strong>Order ID:</strong> ${order.order_id}</p>
            <p><strong>Date:</strong> ${order.order_date ? new Date(order.order_date).toLocaleString('uk-UA') : 'N/A'}</p>
            <p><strong>Status:</strong> ${formatOrderStatus(order.status)}</p>
            <p><strong>Receipt Number:</strong> ${order.receipt_number ?? 'N/A'}</p>
            <p><strong>Delivery Address:</strong> ${order.delivery_address ?? 'N/A'}</p>
            <p><strong>Total Amount (Calculated):</strong> ${calculatedTotal.toFixed(2)} грн</p>
            <hr>
            <h4>Client Details</h4>
            <p><strong>Name:</strong> ${order.client?.first_name ?? ''} ${order.client?.last_name ?? ''}</p>
            <p><strong>Email:</strong> ${order.client?.email ?? 'N/A'}</p>
            <p><strong>Phone:</strong> ${order.client?.phone_number ?? 'N/A'}</p>
            <hr>
            <h4>Order Items</h4>
        `;

        if (order.items && order.items.length > 0) {
            detailsHTML += `
                <table class="data-table">
                    <thead><tr><th>Book Title</th><th>Quantity</th><th>Price per Item</th><th>Total</th></tr></thead>
                    <tbody>
            `;
            order.items.forEach(item => {
                const itemTotal = (item.quantity ?? 0) * (item.price_at_purchase ?? 0);
                detailsHTML += `
                    <tr>
                        <td>${item.book?.title ?? 'N/A'}</td>
                        <td>${item.quantity ?? 0}</td>
                        <td>${(item.price_at_purchase ?? 0).toFixed(2)} грн</td>
                        <td>${itemTotal.toFixed(2)} грн</td>
                    </tr>
                `;
            });
            detailsHTML += `</tbody></table>`;
        } else {
            detailsHTML += '<p>No items found in this order.</p>';
        }

        // Додаємо деталі локації, якщо є
        if(order.location) {
            detailsHTML += `<hr><h4>Location</h4><p>${order.location.address ?? 'N/A'}</p>`;
        }
        // Співробітника немає в моделі Orders згідно hhh.sql
        // if(order.employee) {
        //    detailsHTML += `<hr><h4>Processed By</h4><p>${order.employee.first_name ?? ''} ${order.employee.last_name ?? ''}</p>`;
        // }
        // --- КІНЕЦЬ Формування HTML ---

        orderDetailsContent.innerHTML = detailsHTML; // Вставляємо згенерований HTML

        // Показуємо секцію оновлення статусу, якщо користувач Адмін/Менеджер
        // Перевіряємо currentUser перед доступом до role_name
        const canManageOrders = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager');
        if (canManageOrders && orderStatusUpdateSection && orderNewStatusSelect && orderDetailsIdInput) {
             orderStatusUpdateSection.style.display = 'block';
             orderNewStatusSelect.value = order.status; // Встановлюємо поточний статус
             orderDetailsIdInput.value = order.order_id; // Зберігаємо ID
        }

        orderDetailsModal.classList.add('show'); // Показуємо модальне вікно

    } catch (error) {
        console.error("Failed to load order details:", error);
        orderDetailsContent.innerHTML = ''; // Очищаємо контент
        if(orderDetailsError) orderDetailsError.textContent = `Помилка завантаження деталей: ${error.message}`;
        orderDetailsModal.classList.add('show'); // Все одно показуємо вікно з помилкою
    }
}
function closeOrderDetailsModal() {
    if (orderDetailsModal) {
        orderDetailsModal.classList.remove('show');
        console.log("Order details modal closed.");
    }
}

/**
* Оновлює статус замовлення.
*/
async function handleUpdateOrderStatus() {
   const currentToken = localStorage.getItem('accessToken');
   const orderId = orderDetailsIdInput ? orderDetailsIdInput.value : null;
   const newStatus = orderNewStatusSelect ? orderNewStatusSelect.value : null;

   const canManageOrders = currentUser && (currentUser.role_name === 'Administrator' || currentUser.role_name === 'Manager');

   if (!currentToken || !canManageOrders || !orderId || !newStatus) {
       if(orderStatusUpdateMessage) orderStatusUpdateMessage.textContent = 'Error: Invalid data or permissions.';
       console.error("Cannot update status: missing token, permission, orderId, or newStatus.");
       return;
   }
   if(orderStatusUpdateMessage) orderStatusUpdateMessage.textContent = 'Updating...';
   if(updateOrderStatusButton) updateOrderStatusButton.disabled = true;

   // Припускаємо ендпоінт PUT /api/v1/orders/{order_id}/status
   const url = `http://localhost:7000/api/v1/orders/${orderId}/status`;

   try {
       const response = await fetch(url, {
           method: 'PUT',
           headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
           body: JSON.stringify({ status: newStatus })
       });
       if (!response.ok) {
           let errorDetail = `HTTP помилка! Статус: ${response.status}`;
           try { errorDetail = (await response.json()).detail || errorDetail; } catch (e) {}
           throw new Error(errorDetail);
       }
       const updatedOrder = await response.json(); // Очікуємо оновлене замовлення у відповідь
       console.log("Order status updated:", updatedOrder);
       if(orderStatusUpdateMessage) orderStatusUpdateMessage.textContent = 'Status Updated!';
        // Оновлюємо відображення статусу в модалці (необов'язково, бо список оновиться)
       const statusElement = orderDetailsContent.querySelector('p strong:contains("Status:")'); // Потрібно надійніше знаходити елемент
       if(statusElement && statusElement.nextSibling) {
           statusElement.nextSibling.textContent = ` ${formatOrderStatus(updatedOrder.status)}`;
       }

       loadOrders(); // Перезавантажуємо список замовлень після успішного оновлення

       setTimeout(() => { if(orderStatusUpdateMessage) orderStatusUpdateMessage.textContent = ''; }, 3000);

   } catch (error) {
       console.error("Failed to update order status:", error);
       if(orderStatusUpdateMessage) orderStatusUpdateMessage.textContent = `Error: ${error.message}`;
   } finally {
       if(updateOrderStatusButton) updateOrderStatusButton.disabled = false;
   }
}

// --- Обробники Подій для Замовлень ---

// Пошук та фільтри
if (orderSearchButton) {
   orderSearchButton.addEventListener('click', loadOrders);
}
if (orderFilterButton) { // Кнопка застосування фільтрів
   orderFilterButton.addEventListener('click', loadOrders);
}
if (orderSearchInput) {
   orderSearchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') loadOrders(); });
}
// Можна додати слухачі на зміну фільтрів, якщо потрібне автооновлення
// if (orderStatusFilter) orderStatusFilter.addEventListener('change', loadOrders);
// if (orderDateFromInput) orderDateFromInput.addEventListener('change', loadOrders);
// if (orderDateToInput) orderDateToInput.addEventListener('change', loadOrders);


// Клік на кнопку "Details" у таблиці
if (orderListContainer) {
  orderListContainer.addEventListener('click', (event) => {
      const target = event.target;
      if (target.classList.contains('view-details-btn')) {
          const orderId = target.dataset.id;
          if (orderId) {
              showOrderDetails(orderId);
          }
      }
      // Додайте обробку інших кнопок в рядку, якщо потрібно
  });
}

// Обробники закриття модального вікна деталей
if (orderDetailsModal) {
  // Клік на фон
  orderDetailsModal.addEventListener('click', (event) => { if (event.target === orderDetailsModal) closeOrderDetailsModal(); });
  // Кнопка закриття (Х) - знаходимо її всередині модалки
  const closeBtn = orderDetailsModal.querySelector('.close-button');
  if(closeBtn) closeBtn.addEventListener('click', closeOrderDetailsModal);
   // Кнопка "Close" внизу
   if(closeOrderDetailsBtn) closeOrderDetailsBtn.addEventListener('click', closeOrderDetailsModal);
}

// Кнопка оновлення статусу
if(updateOrderStatusButton) {
   updateOrderStatusButton.addEventListener('click', handleUpdateOrderStatus);
}


// --- Додаємо до MutationObserver ---
if (ordersContentSection) { // Використовуємо змінну, оголошену на початку
  console.log("Setting up MutationObserver for orders section.");
  observer.observe(ordersContentSection, { attributes: true });
  // Перевіряємо, чи секція вже активна при ініціалізації
  if (ordersContentSection.classList.contains('active')) {
      console.log("Orders section already active on init, loading orders...");
      loadOrders();
  }
} else {
  console.error("Orders content section (#recent-orders-content) not found for MutationObserver setup!");
}


//=========================================================================//
//             END OF ORDER MANAGEMENT BLOCK                             //
//=========================================================================//


const dropdownToggle = document.querySelector('.dropdown-toggle');
     if (dropdownToggle) {
         dropdownToggle.addEventListener('click', (event) => {
             event.preventDefault();
             const parentLi = event.target.closest('.dropdown-container');
             if (parentLi) {
                 parentLi.classList.toggle('open'); // Додає/видаляє клас 'open'
             }
         });
     }

     async function triggerDownload(url, defaultFilename) {
        const currentToken = localStorage.getItem('accessToken');
        if (!currentToken) {
            alert('Помилка: Необхідна авторизація для експорту.');
            return;
        }
        console.log(`Attempting to download from: ${url}`); // Лог

        // Додаємо індикатор завантаження
        const exportLink = exportDropdownToggle;
        const originalText = exportLink?.innerHTML || 'Export'; // Зберігаємо оригінальний текст
        if (exportLink) exportLink.innerHTML += ' <span class="spinner">(...)</span>';

        try {
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${currentToken}` }
            });

            if (!response.ok) {
                let errorDetail = `Помилка експорту (${response.status})`;
                try {
                    const errorText = await response.text();
                     try {
                         const errorData = JSON.parse(errorText);
                         errorDetail = errorData.detail || `${errorDetail}: ${errorText}`;
                     } catch (jsonError){
                        if (errorText.includes('<html')) {
                             errorDetail += " (Сервер повернув HTML сторінку помилки)";
                        } else {
                             errorDetail += `: ${errorText.substring(0, 200)}`;
                        }
                    }
                } catch (e) { /* Ігноруємо */ }
                throw new Error(errorDetail);
            }

            const disposition = response.headers.get('content-disposition');
            let filename = defaultFilename;
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) {
                  filename = matches[1].replace(/['"]/g, '');
                }
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(downloadUrl);

        } catch (error) {
            console.error('Помилка під час експорту:', error);
            alert(`Не вдалося експортувати дані: ${error.message}`);
        } finally {
             // Прибираємо індикатор завантаження
             if (exportLink) exportLink.innerHTML = originalText;
        }
    }

    if (exportDropdownMenu) {
        // Додаємо слухач на весь список <ul>
        exportDropdownMenu.addEventListener('click', (event) => {
            // Перевіряємо, чи клікнули саме на посилання <a> всередині <li>
            if (event.target.tagName === 'A') {
                event.preventDefault(); // Забороняємо стандартний перехід
                const target = event.target;

                if (target && target.dataset.format) {
                    const format = target.dataset.format; // Отримуємо формат з атрибута data-format

                    // --- Формуємо URL для ПОВНОГО експорту бази даних ---
                    let exportUrl;
                    let defaultFilename;

                    switch(format) {
                        case 'csv':
                            exportUrl = `http://localhost:7000/api/v1/export/full_database/zip`;
                            defaultFilename = `database_export_csv.zip`;
                            break;
                        case 'json':
                            exportUrl = `http://localhost:7000/api/v1/export/full_database/json`;
                            defaultFilename = `database_export.json`;
                            break;
                        case 'excel':
                            exportUrl = `http://localhost:7000/api/v1/export/full_database/excel`;
                            defaultFilename = `database_export.xlsx`;
                            break;
                        case 'pdf':
                            exportUrl = `http://localhost:7000/api/v1/export/full_database/pdf`;
                            defaultFilename = `database_export.pdf`;
                            break;
                         case 'zip': // Якщо ви додали ендпоінт для ZIP
                             exportUrl = `http://localhost:7000/api/v1/export/full_database/zip`;
                             defaultFilename = `database_export_csv.zip`;
                             break;
                        default:
                            console.error(`Непідтримуваний формат експорту: ${format}`);
                            alert(`Формат експорту '${format}' не підтримується.`);
                            return; // Виходимо, якщо формат невідомий
                    }

                    // Додаємо поточну дату/час до імені файлу
                    const now = new Date();
                    const timestamp = `${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}_${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}${now.getSeconds().toString().padStart(2, '0')}`;
                    defaultFilename = defaultFilename.replace('.', `_${timestamp}.`);

                    console.log(`Запит на повний експорт бази даних у форматі: ${format}`); // Лог

                    // Запускаємо завантаження
                    triggerDownload(exportUrl, defaultFilename);

                    // Закриваємо меню після кліку
                    const parentLi = target.closest('.dropdown-container');
                    if (parentLi) {
                        parentLi.classList.remove('open');
                    }
                }
            }
        });

         // Додаємо закриття меню при кліку поза ним (опціонально)
         document.addEventListener('click', (event) => {
             const openDropdown = document.querySelector('.dropdown-container.open');
             // Перевіряємо, чи клік був НЕ всередині відкритого контейнера меню
             if (openDropdown && !openDropdown.contains(event.target)) {
                 openDropdown.classList.remove('open');
             }
         });
    }
     
}); // Кінець document.addEventListener('DOMContentLoaded', ...)

console.log("main.js script loaded."); // Повідомлення в кінці файлу