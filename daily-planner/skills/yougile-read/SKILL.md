# skills/yougile-read/SKILL.md

## Purpose
Чтение задач из YouGile API v2 для планировщика. Только чтение.

## ВАЖНО перед стартом
Проверить, нет ли готового клиента YouGile в «Созвон→Задачи». Если есть — переиспользовать, НЕ писать заново.

## Endpoint
- `GET get_user_tasks(me)` → все задачи через проекты. База: `https://yougile.com/api-v2/`. Auth: API-ключ.
- `projectId`-фильтр НЕ поддерживается. Группировать локально по `boardId`/`projectId`.
- Учитывать пагинацию и лимиты запросов (бэкофф на 429).

## Маппинг полей
`id, title, projectId, boardId, columnId, createdAt(ms), deadline{deadline,startDate,withTime}, timeTracking.plan(h), completed(bool)`.
Отсутствующие поля → безопасные дефолты (`deadline=None`, `plan=None`).

## Rules
- Чистое чтение, без побочных эффектов.
- Никаких записей/перемещений в M0.

## Tests (mock-first)
- Фикстуры = реальные ответы `get_user_tasks`. Мок строится против реального интерфейса.
- Кейсы: задача без дедлайна, без plan, completed=true, несколько проектов.
