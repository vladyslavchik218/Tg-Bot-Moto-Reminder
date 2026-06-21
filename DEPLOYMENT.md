# 🚀 Деплой на Railway.app (безкоштовно)

Railway.app надає безкоштовний план з $5 кредитами на місяць, що достатньо для запуску Telegram бота.

## Крок 1: Підготовка проекту

1. Створіть файл `requirements.txt` (вже існує):
```txt
python-telegram-bot==20.7
python-dotenv==1.0.0
```

2. Створіть файл `Procfile`:
```bash
web: python bot.py
```

3. Створіть файл `.env.example` (вже існує):
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Крок 2: Створення GitHub репозиторію

1. Ініціалізуйте git:
```bash
git init
```

2. Додайте `.gitignore`:
```bash
echo ".env" >> .gitignore
echo "motorcycle_diary.db" >> .gitignore
echo "__pycache__" >> .gitignore
```

3. Зробіть перший коміт:
```bash
git add .
git commit -m "Initial commit"
```

4. Створіть репозиторій на GitHub (github.com/new)
5. Підключіть локальний репозиторій:
```bash
git remote add origin https://github.com/YOUR_USERNAME/motorcycle-diary-bot.git
git branch -M main
git push -u origin main
```

## Крок 3: Деплой на Railway.app

1. Зареєструйтесь на [railway.app](https://railway.app)
2. Натисніть "New Project" → "Deploy from GitHub repo"
3. Виберіть ваш репозиторій
4. Railway автоматично визначить Python проект
5. Додайте змінні середовища:
   - Натисніть на ваш проект → "Variables"
   - Додайте `TELEGRAM_BOT_TOKEN` з вашим токеном бота

## Крок 4: Налаштування Railway

1. У налаштуваннях проекту змініть команду запуску:
   ```
   python bot.py
   ```

2. Railway автоматично запустить бота

## Крок 5: Моніторинг

- Переглядайте логи в Railway dashboard
- Бот буде автоматично перезапускатися при помилках

## Альтернативні безкоштовні варіанти:

### Render.com
- Безкоштовний план для веб-сервісів
- Підтримує Python
- Автоматичний деплой з GitHub

### PythonAnywhere
- Безкоштовний план з обмеженнями
- Підтримує Python
- Потрібен webhook для Telegram бота

### Fly.io
- Безкоштовний план з обмеженнями
- Підтримує Python
- Потрібен webhook для Telegram бота

 Railway.app - найкращий варіант для Telegram бота, оскільки не потребує webhook і працює з polling.
