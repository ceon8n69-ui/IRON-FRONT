# GitHub и Railway: настройка владельцем

## Подключённая инфраструктура

- GitHub: https://github.com/ceon8n69-ui/IRON-FRONT
- Railway: https://railway.com/project/62ffbe85-a212-4c3d-906d-67734560fce7
- API: https://api-production-3dbd1.up.railway.app
- Telegram bot: @Ironfrontwaw_bot. Владелец должен внести его BOT_TOKEN в секреты API и bot. Токен не хранится в репозитории.
- PostgreSQL и Redis созданы в отдельном проекте. API и worker используют ссылки на их private-network URLs.

## Публикация исходников

Распакуйте архив, создайте пустой репозиторий `iron-front` (без README), затем в каталоге:

```sh
git init -b main
git add .
git commit -m "Implement initial IRON FRONT vertical slice"
git remote add origin https://github.com/YOUR_ACCOUNT/iron-front.git
git push -u origin main
```

Архив содержит `iron-front.bundle`: локальный commit можно восстановить командой `git clone /path/to/iron-front.bundle iron-front` вместо создания истории заново. Bundle не содержит секретов и зависимостей.

## Сервисы Railway

Создать PostgreSQL с постоянным volume и резервным копированием, Redis и три сервиса из одного репозитория:

| Сервис | Команда | Healthcheck | Pre-deploy |
|---|---|---|---|
| api | Dockerfile CMD | /health | alembic upgrade head && python -m app.seed |
| worker | python -m app.worker | отключить | отключить |
| bot | python -m app.bot | отключить | отключить |

Настройки сервиса задаются через Railway API/dashboard: старый выбор railway.json Railway отклоняет как deprecated. Файлы railway*.json удалены. Для worker и bot не назначать healthcheck/pre-deploy: они не запускают HTTP-сервер и не должны выполнять миграции параллельно API. Первый запуск worker — после успешной миграции API. Worker использует одну реплику в срезе; несколько реплик требуют дополнительной нагрузки и проверки fairness.

Переменные API/worker: `APP_ENV=production`, `DATABASE_URL=${{Postgres.DATABASE_URL}}`, `REDIS_URL=${{Redis.REDIS_URL}}`, `BOT_TOKEN=<secret>`. Конкретные имена сервисов сверить в проекте.

Переменные bot: `BOT_TOKEN=<secret>`, `APP_URL=https://<api-domain>`. Для бота используется long polling: только одна реплика и отсутствие webhook у этого отдельного бота. Изменение существующего webhook выполнять только после проверки, что это именно IRON FRONT.

Выдать API HTTPS-домен. Установить этот URL для Mini App в BotFather. Не отдавать Vite dev server в production. У API и клиента один origin; токены не передаются в query string.

## Release gates

1. GitHub CI: все тесты без пропусков, миграции и сборка зелёные.
2. Railway deployment terminal status SUCCESS; `/health` возвращает 200.
3. Вход двух независимых пользователей через реальный Telegram.
4. Первый цикл, закрытие приложения, повторный вход и сохранность предмета.
5. Перезапуск API/worker во время постройки; очередь завершается однократно.
6. Разрыв WS и восстановление состояния.
7. iOS/Android: safe areas, камера, скролл, кнопки, память и FPS.
8. Автоматические резервные копии и пробное восстановление на отдельном окружении.

До этих проверок статус проекта — alpha, не production-ready. Первая миграция применяется только к новой БД. Для будущих миграций с существующими данными сначала snapshot/backup. Не применять downgrade к production для отката приложения: сначала вернуть совместимую версию кода и проанализировать схему.
