# SwapBot

Telegram-бот для обмена вещами: объявления, просмотр, предложения обмена, профиль, избранное.

## Структура проекта

```
swap_bot/
├── app/
│   ├── bot.py           # Точка входа бота
│   ├── config.py        # Конфигурация и константы
│   ├── handlers/        # start, profile, ads, browse, chat, admin, payments
│   ├── database/        # БД (SQLite), models, crud, migrations
│   ├── services/        # AI, avito, gamification, security (заглушки)
│   ├── keyboards/
│   ├── states/
│   ├── utils/
│   └── middlewares/
├── admin/               # Админ-панель (FastAPI)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env                 # BOT_TOKEN, DB_PATH, …
```

## Запуск локально (без Docker)

1. Клонируйте репозиторий и перейдите в каталог:
   ```bash
   cd swap_bot
   ```

2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Создайте файл `.env` в корне проекта:
   ```env
   BOT_TOKEN=123456:ABC...   # от @BotFather
   DB_PATH=bot.db
   ADMIN_IDS=123456789       # через запятую, опционально
   ```

4. Запустите бота:
   ```bash
   python -m app.bot
   ```

Бот будет работать, пока процесс не остановить (`Ctrl+C`). Локально используется SQLite (`bot.db`), Redis/Celery не нужны.

## Запуск в Docker (локально на ноуте)

1. Убедитесь, что установлены [Docker](https://docs.docker.com/get-docker/) и Docker Compose.

2. В корне проекта создайте `.env` с `BOT_TOKEN` (и при необходимости `DB_PATH`).

3. Соберите и запустите:
   ```bash
   docker-compose up -d
   ```

4. Просмотр логов:
   ```bash
   docker-compose logs -f bot
   ```

5. Остановка:
   ```bash
   docker-compose down
   ```

Контейнер с ботом перезапускается при падении (`restart: unless-stopped`). База SQLite хранится в volume `bot_data`, данные сохраняются между перезапусками. Так можно держать бота включённым несколько дней или дольше.

## Админ-панель (опционально)

```bash
pip install fastapi uvicorn
uvicorn admin.main:app --host 0.0.0.0 --port 8000
```

Документация API: http://localhost:8000/docs

## Ответы на вопросы

- **Бот в Telegram или встроенное приложение?**  
  Обычный Telegram-бот. Mini App / Web App не используется.

- **Можно ли держать бота в Docker несколько дней?**  
  Да. `docker-compose up -d` держит контейнер запущенным, при сбоях он перезапускается. Останавливайте явно через `docker-compose down` при необходимости.

- **Локально без Docker**  
  Достаточно `python -m app.bot` и `.env` с `BOT_TOKEN`. Redis/Postgres не требуются.
