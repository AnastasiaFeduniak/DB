// Отримуємо елементи DOM
const loginForm = document.getElementById('login-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const errorMessageDiv = document.getElementById('error-message');

// Додаємо обробник події для відправки форми
loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorMessageDiv.textContent = '';
    const email = emailInput.value.trim();
    const password = passwordInput.value.trim();

    if (!email || !password) {
        errorMessageDiv.textContent = 'Будь ласка, заповніть обидва поля.';
        return;
    }

    const loginData = new URLSearchParams();
    loginData.append('username', email);
    loginData.append('password', password);

    try {
        // !!! ВИПРАВЛЕННЯ ТУТ: Вказуємо повний URL до FastAPI !!!
        const apiUrl = 'http://localhost:7000/api/v1/login/token'; // Замініть порт 7000, якщо ваш FastAPI працює на іншому
        console.log("Sending login request to:", apiUrl);
        const response = await fetch(apiUrl, { // Використовуємо apiUrl
            method: 'POST',
            body: loginData
        });

        const result = await response.json();

        if (!response.ok) {
            errorMessageDiv.textContent = result.detail || `Помилка ${response.status}: Не вдалося увійти.`;
        } else {
            console.log('Login successful:', result);
            if (result.access_token) {
                localStorage.setItem('accessToken', result.access_token);
                // Можливо, отримати роль з токена або окремим запитом і зберегти
                // const payload = JSON.parse(atob(result.access_token.split('.')[1]));
                // localStorage.setItem('userRole', payload.role);
                window.location.href = '/index.html'; // Перенаправлення на головну
            } else {
                 errorMessageDiv.textContent = 'Помилка: Токен доступу не отримано.';
            }
        }
    } catch (error) {
        console.error('Login request failed:', error);
        errorMessageDiv.textContent = 'Помилка мережі або сервера. Переконайтесь, що бекенд запущено та доступно.';
    }
});