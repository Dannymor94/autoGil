# skills/urgency-scoring/SKILL.md

## Purpose
Детерминированный скор срочности и флаг `горит`. Без LLM.

## Вход
Кандидат: `createdAt`, `deadline`, `completed`, `columnId`. Учитываются только `completed==false` И `columnId ∉ final_columns`.

## Формула (TUNABLE — вынести в конфиг)
- `AGE_CAP=30`, `HORIZON=14`, `FLAME_DAYS=3`, `W_D=0.7`, `W_A=0.3`.
- `age_score = clamp(days_since(createdAt)/AGE_CAP, 0, 1)`
- `deadline_score = 0` если нет дедлайна; иначе `clamp((HORIZON - days_to_deadline)/HORIZON, 0, 1)`; просрочка → `1`.
- `score = W_D*deadline_score + W_A*age_score`
- `горит = overdue OR days_to_deadline<=FLAME_DAYS OR age_score>=0.8`

## Rules
- Возраст учитывается ТОЛЬКО для незакрытых не-финальных задач (иначе старая закрытая шумит).
- Все пороги в конфиге, не хардкод.

## Tests
- Просрочена → горит, score высокий.
- Свежая без дедлайна → low.
- Старая (>24д) без дедлайна → age_score высокий, горит по возрасту.
- Граничные: ровно FLAME_DAYS, ровно AGE_CAP.
