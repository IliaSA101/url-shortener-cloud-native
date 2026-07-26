<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Native Shortener</title>
    <!-- Подключаем собранные стили и скрипты (Vite + Tailwind) -->
    @vite(['resources/css/app.css', 'resources/js/app.js'])
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">

    <div class="bg-white p-8 rounded-xl shadow-lg w-full max-w-lg relative">
        <h1 class="text-2xl font-bold text-gray-800 mb-6 text-center">URL Shortener</h1>

        <!-- Форма -->
        <form id="shorten-form" class="space-y-4">
            <div>
                <label for="url" class="block text-sm font-medium text-gray-700">Оригинальный URL</label>
                <input type="url" id="url" required placeholder="https://example.com" 
                    class="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                <!-- Контейнер для ошибки валидации -->
                <p id="error-message" class="text-red-500 text-sm mt-1 hidden"></p>
            </div>

            <button type="submit" id="submit-btn" 
                class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                Сократить
            </button>
        </form>

        <!-- Результат -->
        <div id="result-container" class="mt-6 p-4 bg-green-50 rounded-md hidden">
            <p class="text-sm text-green-800">Успешно! Ваша короткая ссылка:</p>
            <a id="short-link" href="#" target="_blank" class="text-lg font-bold text-blue-600 hover:underline break-all"></a>
        </div>
    </div>

    <script type="module">
        document.getElementById('shorten-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const urlInput = document.getElementById('url').value;
            const submitBtn = document.getElementById('submit-btn');
            const errorMsg = document.getElementById('error-message');
            const resultContainer = document.getElementById('result-container');
            const shortLink = document.getElementById('short-link');

            // Сброс состояния
            errorMsg.classList.add('hidden');
            resultContainer.classList.add('hidden');
            submitBtn.disabled = true;
            submitBtn.innerText = 'Загрузка...';

            try {
                // Вызываем наш API. Axios уже доступен глобально через window.axios
                const response = await window.axios.post('/api/links', {
                    original_url: urlInput
                });

                // Показываем результат
                shortLink.href = response.data.short_url;
                shortLink.innerText = response.data.short_url;
                resultContainer.classList.remove('hidden');
                document.getElementById('url').value = ''; 

            } catch (error) {
                // Обработка ошибок (валидация или Rate Limit из будущего #15)
                errorMsg.classList.remove('hidden');
                if (error.response?.status === 422) {
                    errorMsg.innerText = error.response.data.errors.original_url[0];
                } else if (error.response?.status === 429) {
                    errorMsg.innerText = 'Слишком много запросов. Подождите.';
                } else {
                    errorMsg.innerText = 'Произошла ошибка при сокращении ссылки.';
                }
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Сократить';
            }
        });
    </script>
</body>
</html>