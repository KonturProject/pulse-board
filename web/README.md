# Дашборд (web)

Статический сайт на Vite + React + TypeScript. Расшифровывает `public/data/dashboard.enc.json` кодом из
ссылки и показывает экраны: главный, рейтинг руководителей, экран группы.

```bash
npm ci
npm test          # Vitest
npm run dev       # локально; данные — web/public/data (для проверки можно зашифровать тестовым кодом)
npm run build     # сборка в dist/ — её выкладывает GitHub Actions
```

Устройство и правила расчёта — в [../docs/PROJECT.md](../docs/PROJECT.md).
