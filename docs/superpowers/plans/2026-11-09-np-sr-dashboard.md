# Пульс направления — план реализации

> **Исторический документ** — план первого запуска (09.11.2026), выполнен. Актуальное устройство проекта — [docs/PROJECT.md](../../PROJECT.md); изменения после запуска — раздел 0 [дизайна](../specs/2026-11-09-np-sr-dashboard-design.md).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** локальная админка собирает 8 Excel-отчётов из сетевых папок, считает фокусные показатели 6 групп НП СР, копит историю и публикует зашифрованные данные на GitHub Pages, где статический дашборд показывает тепловую карту групп, карточки групп и провал до сотрудников.

**Architecture:** две части в одном репозитории. `admin/` — Python-пакет `npsr_admin`: парсеры отчётов → «факты» (числитель/знаменатель) → локальная SQLite-история → агрегированный JSON → шифрование (AES-GCM/PBKDF2, конверт Stepper Game) → `git push`. `web/` — Vite + React + TypeScript, расшифровывает данные в браузере по фразе из `#/?k=`, оценивает зоны и рисует экраны (SVG без библиотек графиков). GitHub Actions собирает `web/` и деплоит на Pages.

**Tech Stack:** Python 3.14 (`pyxlsb`, `openpyxl`, `cryptography`, `pytest`, stdlib `http.server`, `sqlite3`); Node 22, Vite, React 19, TypeScript, Vitest; GitHub Pages + Actions; `gh` (аккаунт `KonturProject`).

**Spec:** `docs/superpowers/specs/2026-11-09-np-sr-dashboard-design.md`

## Global Constraints

- Группы — ровно 6: ключи `СР1, СР2, СР3, СР5, СР6, СР9`; филиалы: Тверь (СР1, СР2, СР3, СР6, СР9), Москва (СР5). «Ученики», «СР4_Упр», «КЦПК_НП_СР_Москва» и всё вне НП СР отбрасываются парсером.
- В git никогда: `*.xls*`, `*.xlsb`, `*.xlsm`, `.superpowers/`, локальная история, конфиг с путями. Проверка `scripts/check_public.py` в pre-commit и в CI.
- Шифрование: AES-GCM 256, PBKDF2-SHA-256, 250 000 итераций, соль 16 байт, IV 12 байт; конверт `{v:1, alg:"AES-GCM", kdf:"PBKDF2-SHA256", iter, salt, iv, ciphertext}` (base64) — байт-в-байт совместим с `stepper game/src/data/crypto.ts`.
- Фраза — 4 слова из списка `stepper game/src/admin/words.ts` + 2 цифры, через `-`. Ссылка: `https://konturproject.github.io/<repo>/#/?k=<фраза>`; фраза уходит в localStorage и стирается из адреса.
- Неделя = ISO-неделя, формат `"2026.45"`. «Вчера» = последний рабочий день (пн → пт; праздники не учитываются).
- Окно публикации: 4 недели, включая текущую.
- Нормативы по умолчанию: ран-рейт 100 (ступени 120, 140); кач. счета 4/чел./день; длинные презентации floor 1,2 / target 1,5; попытки НС1 5; попытки 300+ 3,8; попытки ОЗ 6,5; скорость ОЗ 95%; порог «утёнка» 15%. Остальные — без абсолютного норматива.
- Админка слушает только `127.0.0.1`.
- Палитра (из согласованного макета): `--bg #EEF2F4, --card #FFF, --ink #1F2A33, --muted #6B7A86, --red #D9474F, --green #2E9E6A, --amber #E39B2E, --blue #3A7BBF`; шрифт Onest. Красный — только «утёнок».

## Review Focus

1. Отчёт без СР9 или вообще без какой-то группы → прочерк в ячейке, без исключения и без окраски (тест в Task 4 и Task 13).
2. Сводная в отчёте сдвинута на строку/столбец или фильтр сохранён иначе → парсер находит шапку по тексту; при отсутствии шапки — понятное предупреждение в сводке, а не падение всего сбора (тест в Task 3).
3. Сетевая папка недоступна или в ней нет файла по шаблону → этот отчёт помечен «не найден», остальные собираются (тест в Task 11).
4. Неверная фраза или старая ссылка после смены фразы → экран «Введите код доступа» с текстом «Код не подходит», без белого экрана (тест в Task 14).
5. Повторный сбор того же дня или отчёт с пересчитанными прошлыми днями → новый снимок перекрывает старый, дубли не копятся (тест в Task 10).

---

## Структура файлов

```
.gitignore, README.md
scripts/check_public.py              # запрет Excel/истории в git
admin/pyproject.toml
admin/npsr_admin/
  model.py        # Fact, ParseResult, Source
  groups.py       # справочник групп, match_group()
  weeks.py        # iso_week(), last_working_day()
  excel.py        # iter_rows() для xlsx/xlsm/xlsb, find_row()
  parsers/__init__.py   # REGISTRY: id -> parse()
  parsers/oper.py, funnel_days.py, gkg.py, attempts300.py,
          ak.py, orders.py, oz_speed.py, oz_attempts.py
  store.py        # SQLite снимки
  aggregate.py    # факты -> dashboard payload
  crypto.py       # encrypt_json / decrypt_json
  phrase.py       # new_phrase(), WORDS
  config.py       # локальный конфиг (%LOCALAPPDATA%\npsr-dashboard)
  collect.py      # поиск свежих файлов, запуск парсеров
  publish.py      # шифрование + git commit/push
  server.py, __main__.py
  ui/index.html, ui/app.js, ui/style.css
admin/tests/...
Запустить админку.bat
web/ (Vite) src/: crypto.ts, data.ts, access.tsx, eval.ts, format.ts,
     App.tsx, screens/Main.tsx, screens/Group.tsx,
     ui/Ring.tsx, ui/Heatmap.tsx, ui/GroupCard.tsx, ui/Trend.tsx, styles.css
web/tests/...
web/public/data/            # сюда publish кладёт *.enc.json + version.json
.github/workflows/deploy.yml
```

Локальное состояние админки (вне репозитория): `%LOCALAPPDATA%\npsr-dashboard\{config.json, history.sqlite, cache\}`; путь переопределяется переменной `NPSR_HOME` (для тестов).

Образцы отчётов лежат в корне проекта; тесты парсеров берут их через фикстуру `sample(name)`, которая делает `pytest.skip`, если файла нет (в CI файлов нет).

---

### Task 1: Каркас репозитория, модель фактов, группы, недели

**Files:**
- Create: `.gitignore`, `scripts/check_public.py`, `admin/pyproject.toml`, `admin/npsr_admin/{__init__,model,groups,weeks}.py`, `admin/tests/conftest.py`, `admin/tests/test_groups.py`, `admin/tests/test_weeks.py`, `admin/tests/test_check_public.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) Fact(metric: str, period: str, group: str, employee: str | None, num: float, den: float)` — `period` = `"YYYY-MM-DD"` (дневной) или `"YYYY.WW"` (недельный); значение показателя = `sum(num)/sum(den)` на любом уровне агрегации.
  - `@dataclass ParseResult(source: str, data_date: date | None, facts: list[Fact], warnings: list[str])`
  - `GROUPS: dict[str, Group]`, `Group(key, label, branch)`; `match_group(name: str) -> str | None`
  - `iso_week(d: date) -> str`; `last_working_day(today: date) -> date`
  - фикстура `sample(name: str) -> Path` в `conftest.py`
  - `check_public.main(paths: list[str]) -> int` (0 — чисто, 1 — запрещённые файлы)

- [ ] **Step 1: git init, `.gitignore`** — игнор: `*.xls`, `*.xlsx`, `*.xlsb`, `*.xlsm`, `.superpowers/`, `__pycache__/`, `node_modules/`, `web/dist/`, `.venv/`. Создать venv `admin/.venv`, `pip install -e admin[dev]` (`cryptography`, `pyxlsb`, `openpyxl`, `pytest`).
- [ ] **Step 2: тесты**

```python
def test_match_group_variants():
    assert match_group("КЦПК_НП_СР_Тверь_СР1_ГБ") == "СР1"
    assert match_group("АП_НП_СР_Москва_СР5_ГБ_УД") == "СР5"
    assert match_group("КЦПК_НП_СР_Тверь_СР9_ГБА") == "СР9"
    assert match_group("КЦПК_НП_СР_Тверь_Ученики") is None
    assert match_group("КЦПК_НП_СР_Тверь_СР4_Упр") is None
    assert match_group("КЦПК_НП_СР_Москва") is None
    assert match_group("АП_НП_СС_ННовгород_СС4_СГБ") is None
    assert GROUPS["СР5"].branch == "Москва" and GROUPS["СР1"].branch == "Тверь"

def test_weeks():
    assert iso_week(date(2026, 11, 2)) == "2026.45"
    assert iso_week(date(2026, 11, 8)) == "2026.45"
    assert last_working_day(date(2026, 11, 9)) == date(2026, 11, 6)   # пн -> пт
    assert last_working_day(date(2026, 11, 10)) == date(2026, 11, 9)

def test_check_public_rejects_excel():
    assert check_public.main(["a/Опер_отчет.xlsb", "web/src/App.tsx"]) == 1
    assert check_public.main(["web/public/data/dashboard.enc.json"]) == 0
```

- [ ] **Step 3: прогнать — FAIL** (`cd admin && pytest -q`)
- [ ] **Step 4: реализовать.** `match_group` — регэксп `НП_СР_.*?_СР(\d)` по допустимым номерам {1,2,3,5,6,9}. `check_public` запрещает расширения Excel, `.superpowers/`, `*.sqlite`, `config.json` вне `web/`.
- [ ] **Step 5: PASS; подключить `check_public.py` как `.git/hooks/pre-commit` (по `git diff --cached --name-only`); commit** `feat: scaffold, fact model, groups, weeks`

### Task 2: Чтение Excel и поиск шапки

**Files:** Create `admin/npsr_admin/excel.py`, `admin/tests/test_excel.py`

**Interfaces:**
- Produces: `iter_rows(path: Path, sheet: str) -> Iterator[list[object]]` (значения ячеек; xlsb через `pyxlsb`, xlsx/xlsm через `openpyxl` read_only, data_only); `find_row(rows: Iterable[list], *labels: str, limit: int = 60) -> tuple[int, list] | None` (первая строка, содержащая все labels как подстроки ячеек); `excel_date(v) -> date | None` (serial-число Excel, `datetime`, строка `YYYY-MM-DD`).

- [ ] **Step 1: тесты** — на сгенерированном в `tmp_path` xlsx (openpyxl): шапка на 5-й строке с «Директор», «Группа» → `find_row(...)[0] == 4`; `excel_date(46332.0) == date(2026, 11, 6)`; на образце `sample("Опер_отчет_2026119.xlsb")` лист `Свод` находит строку с «Директор», «Филиал», «Группа», «Сотрудник».
- [ ] **Step 2: FAIL → реализовать → PASS → commit** `feat: excel reader helpers`

### Task 3: Парсер Опер_отчета (ран-рейт)

**Files:** Create `admin/npsr_admin/parsers/{__init__,oper}.py`, `admin/tests/parsers/test_oper.py`

**Interfaces:**
- Consumes: Task 1–2.
- Produces: `oper.parse(path: Path) -> ParseResult`, `source="oper"`. Метрики: `runrate_money`, `runrate_pcs`: для каждого дня `d` месяца с данными — `Fact(period=d, num=факт нарастающим с 1-го числа по d, den=план нарастающим по d)` по сотрудникам (строки «План»/«Факт» листов `Деньги_по дням` / `Штуки_по дням`). `data_date` = последний день с ненулевым фактом по направлению. `parsers.REGISTRY: dict[str, Callable[[Path], ParseResult]]`.

- [ ] **Step 1: тест сверки** — для `sample("Опер_отчет_2026119.xlsb")`: сумма фактов `runrate_money` по всем 6 группам на `data_date`, делённая на сумму планов, совпадает (±0,001) с `% вып_на дату` строки направления «директор» листа `Свод` (значение читать из того же файла в тесте); `data_date == date(2026, 11, 6)`; нет фактов с `group` вне `GROUPS`.
- [ ] **Step 2: тест устойчивости** — файл без листа `Деньги_по дням` → `ParseResult` с `warnings` содержащим `"Деньги_по дням"` и пустыми фактами по деньгам, без исключения.
- [ ] **Step 3: FAIL → реализовать** (шапку и колонки дат искать через `find_row(..., "Директор", "Филиал")` и строку с serial-датами; строки сотрудника = непустой столбец «Сотрудник»). **→ PASS → commit** `feat: oper report parser`

### Task 4: Парсер дневной воронки

**Files:** Create `admin/npsr_admin/parsers/funnel_days.py`, `admin/tests/parsers/test_funnel_days.py`

**Interfaces:**
- Produces: `funnel_days.parse(path) -> ParseResult`, `source="funnel"`. Лист `ВОРОНКА Первичная кампания`; блоки ищутся по заголовкам строки 4. Дневные факты по сотруднику:
  - `staff` — `num=1, den=1`, если у сотрудника на дату есть план (блок «Взятые», подзаголовок «План» > 0);
  - `quality_invoices` — `num=«Качественные счета, шт.»`, `den=1` (только при наличии плана в этот день);
  - `long_presentations` — `num=«Разговоры от 20 минут, шт.»`, `den=1` (то же условие);
  - `taken` — `num=факт «Взятые»`, `den=план «Взятые»`;
  - `completed` — `num=«Завершенные»`, `den=1` (при плане).
  Удельные «на человека в день» получаются автоматически: `sum(num)/sum(den)`.

- [ ] **Step 1: тест сверки** — для образца: по группе СР1 за неделю `2026.45` сумма `quality_invoices.num` совпадает с итоговой строкой группы в том же блоке листа; ни одного факта для «Ученики»; СР9 присутствует.
- [ ] **Step 2: тест** — сотрудник без плана в день → для этого дня нет фактов `quality_invoices/long_presentations/completed/staff`.
- [ ] **Step 3: FAIL → реализовать → PASS → commit** `feat: daily funnel parser`

### Task 5: Парсеры недельных сводных: ГкГ (НС1) и Попытки 300+

**Files:** Create `admin/npsr_admin/parsers/{gkg,attempts300}.py`, тесты рядом.

**Interfaces:**
- Produces:
  - `gkg.parse(path) -> ParseResult`, `source="gkg"`: метрика `ns1_attempts` (лист `Звонков на цепочку длит`, только ветка НС1, «Текущий год»), `period="YYYY.WW"`, `num=значение, den=1` на самом глубоком доступном уровне; плюс `ns1_attempts_ly` (прошлый год) для ГкГ. Если групп в сводной нет — факты с `group="*"` (уровень направления) и предупреждение «сводная свёрнута до филиала — разверните до групп».
  - `attempts300.parse(path) -> ParseResult`, `source="attempts300"`: метрика `attempts_300` из листа `НП СР по менеджерам`, по менеджеру и неделе.
- Примечание: сводные дают средние, не суммы — поэтому `den=1`, а агрегация группы берёт значение строки группы из сводной (`employee=None`), а не среднее сотрудников. Агрегатор (Task 10) для факта с `employee=None` использует его как значение группы.

- [ ] **Step 1: тесты** — образец ГкГ: есть факт `ns1_attempts` для `group="*"` и недели `2026.45`, равный значению строки НС1 «1» в сводной; предупреждение про свёрнутую сводную присутствует. Образец 300+: факты есть для 5 групп (без СР9), значение группы СР1 за последнюю неделю равно строке группы в сводной.
- [ ] **Step 2: FAIL → реализовать → PASS → commit** `feat: weekly pivot parsers (gkg, 300+)`

### Task 6: Парсер аудиоконтроля

**Files:** Create `admin/npsr_admin/parsers/ak.py`, тест.

**Interfaces:**
- Produces: `ak.parse(path) -> ParseResult`, `source="ak"`, все `period="YYYY.WW"` (из `t Неделя`), читается лист `DATA_po_kriter` потоково:
  - `ak_rg_feedback` — карта `АП_ОС_Практика_РГ 2.0`: `num=сумма «_ Оценка по критерию»×кол-во`, `den=кол-во оценок`; `employee=None` (оценка руководителя группы, группа — по `М Подразделение`);
  - `ak_robot_coverage` — `num`=число уникальных менеджеров группы с оценкой в картах `АП_МП_Оценка робота` или `Оценка робота_НС_new` за неделю, `den`=штат группы за неделю (уникальные сотрудники с `staff` из воронки) — **знаменатель подставляет агрегатор** (Task 10); парсер отдаёт `den=0` и помечает метрику как `needs_staff`;
  - `ak_pay_term_primary` / `ak_pay_term_ns` — тип критерия `3. Срок оплаты` в карте `АП_МП_Оценка робота` / `Оценка робота_НС_new`: `num`=число оценок 100, `den`=число оценок, по менеджеру.
- [ ] **Step 1: тесты** — на синтетическом xlsx из 6 строк (карты/группы/оценки 0 и 100) проверить все 4 метрики; на образце — парсер завершается < 120 с и выдаёт ≥1 факт каждой метрики.
- [ ] **Step 2: FAIL → реализовать → PASS → commit** `feat: audio control parser`

### Task 7: Парсер свода по заказам

**Files:** Create `admin/npsr_admin/parsers/orders.py`, тест.

**Interfaces:**
- Produces: `orders.parse(path) -> ParseResult`, `source="orders"`; метрики `orders_extra_seats`, `orders_schools`, `orders_periodicals` из листов `НП СР допместа`, `НП СР РС Школы`, `НП СР РС Периодика`: число счетов по сотруднику и периоду, `den=0` + `needs_staff` (на сотрудника — знаменатель из штата, Task 10). Период — самый мелкий доступный в листе (день или неделя); исполнитель сначала выводит структуру этих трёх листов (первые 40 строк) и фиксирует её в docstring модуля.
- [ ] **Step 1: тест сверки** — по каждому листу сумма счетов по 6 группам за последний период совпадает с итогом направления в том же листе.
- [ ] **Step 2: FAIL → реализовать → PASS → commit** `feat: orders summary parser`

### Task 8: Парсеры ОЗ: скорость взятия и попытки

**Files:** Create `admin/npsr_admin/parsers/{oz_speed,oz_attempts}.py`, тесты.

**Interfaces:**
- Produces:
  - `oz_speed.parse(path) -> ParseResult`, `source="oz_speed"`: лист `Исходник`, строки с `ChefDir_Name` начинающимся на `директор` и `VTM_CAN_CALL_THIS_DAY == 1`; метрика `oz_speed_30`: по `CR_DATE`, группе (`BusinessUnit_Name`), сотруднику (`Operator_Name`): `num=sum(WORKED_IN_TIME_DAY_2_DAY_30)`, `den=count`.
  - `oz_attempts.parse(path) -> ParseResult`, `source="oz_attempts"`: лист `Источник`, строки, где по справочнику «Нужно ли делать >1 попытки» = `Нужно`; метрика `oz_attempts`: по `Дата`, `Подразделение`, `Менеджер`: `num=sum(Кол_во_звонков)`, `den=число строк (ПИНов)`.
- [ ] **Step 1: тесты сверки** — `oz_speed`: по направлению за неделю `2026.44` отношение `num/den` для «Электронный сервис» совпадает (±0,005) со значением «Отработно ДвД за 30 мин»/«Создано» в сводной `New` (строка недели 2026.44 → «Электронный сервис»); если не совпадает — тест выводит обе цифры, и исполнитель уточняет фильтр (по `Type_Back_Call == "Электронный сервис"` вместо `ChefDir_Name`), фиксируя выбор в docstring. `oz_attempts`: значение по направлению за неделю `2026.45` совпадает со «Ср попытки любые» итога листа `Попытки`.
- [ ] **Step 2: FAIL → реализовать (openpyxl read_only; лист 100 тыс. строк читать потоково) → PASS → commit** `feat: callback parsers`

### Task 9: Шифрование и фраза (Python ↔ браузер)

**Files:** Create `admin/npsr_admin/{crypto,phrase}.py`, `admin/tests/test_crypto.py`, `web/src/crypto.ts` (копия `stepper game/src/data/crypto.ts` без изменений), `web/tests/crypto.interop.test.ts`, фикстура `web/tests/fixtures/envelope.json` (генерирует Python-тест).

**Interfaces:**
- Produces: `encrypt_json(value: object, phrase: str, salt: bytes) -> dict` (конверт), `decrypt_json(env: dict, phrase: str) -> object`, `new_salt() -> bytes`; `new_phrase() -> str`; TS: `encryptJson`, `decryptJson`, `DecryptError` (как в Stepper).
- [ ] **Step 1: тесты** — Python round-trip; неверная фраза → `InvalidTag`; `new_phrase()` соответствует `^[a-z]+(-[a-z]+){3}-\d{2}$`. Python-тест пишет `envelope.json` (`{"phrase":"arbuz-volk-luna-sad-42","env":{...},"plain":{"hello":"мир"}}`); Vitest-тест расшифровывает его `decryptJson` и сравнивает с `plain`; второй Vitest-тест шифрует в TS, Python-тест (`test_decrypts_ts_envelope`) расшифровывает файл `web/tests/fixtures/envelope_ts.json`.
- [ ] **Step 2: FAIL → реализовать (`cryptography.hazmat` PBKDF2HMAC + AESGCM; iter 250 000) → PASS обоих наборов → commit** `feat: interoperable encryption`

(Vite-проект `web/` создаётся в этом шаге минимально: `npm create vite@latest web -- --template react-ts`, + `vitest`.)

### Task 10: История и агрегация в payload

**Files:** Create `admin/npsr_admin/{store,aggregate}.py`, тесты.

**Interfaces:**
- Consumes: `Fact`, `ParseResult`, `GROUPS`, `iso_week`.
- Produces:
  - `Store(path: Path)`: `save(result: ParseResult) -> None` — в одной транзакции удаляет факты того же `source` за периоды, присутствующие в `result`, и вставляет новые; `facts(since: date) -> list[Fact]`; `sources() -> list[SourceInfo(source, data_date, collected_at)]`.
  - `build_payload(facts: list[Fact], sources: list[SourceInfo], norms: dict, today: date) -> dict` — схема `schemaVersion: 1`:

```json
{ "schemaVersion": 1, "generatedAt": "...", "dataDate": "2026-11-06",
  "weeks": ["2026.42","2026.43","2026.44","2026.45"],
  "days": {"2026.45": ["2026-11-02", "..."]},
  "sources": [{"id":"oper","dataDate":"2026-11-06","stale":false}],
  "norms": {"quality_invoices": {"target":4}, "long_presentations": {"floor":1.2,"target":1.5}, "...": {}},
  "duckThreshold": 0.15,
  "entities": {"dir":{"label":"Направление"}, "br:Тверь":{}, "g:СР1":{"label":"СР1 ГБ","branch":"Тверь"}, "e:СР1:Иванова И.И.":{"group":"СР1"}},
  "values": {"quality_invoices": {"2026-11-06": {"g:СР1": 3.9, "e:СР1:Иванова И.И.": 5}, "2026.45": {}, "2026.45~2026-11-06": {}}}
}
```
  Ключ `"2026.45~2026-11-06"` — накопленный итог недели по указанный день (для абсолютного слоя оценки). Значение = `sum(num)/sum(den)` по всем фактам уровня; метрики `needs_staff` получают `den` из `staff` (дни присутствия для «на человека», уникальные сотрудники для `ak_robot_coverage`). Факт с `employee=None` задаёт значение группы напрямую. Окно — 4 ISO-недели, заканчивая неделей `last_working_day(today)`. `stale` = `data_date < last_working_day(today) - allowed_lag` (по умолчанию 1 рабочий день).
- [ ] **Step 1: тесты** — (а) повторный `save` того же источника за тот же день не дублирует факты; (б) пересчёт: второй `save` с другим значением за прошлый день перекрывает старое; (в) `build_payload` на 3 синтетических фактах: группа = сумма num / сумма den, направление и филиал считаются, группа без фактов отсутствует в `values` (не ноль); (г) `"2026.45~2026-11-04"` учитывает только 2–4 ноября; (д) окно отсекает неделю `2026.41` при `today=2026-11-09`.
- [ ] **Step 2: FAIL → реализовать → PASS → commit** `feat: snapshot store and payload aggregation`

### Task 11: Конфиг и сбор из папок

**Files:** Create `admin/npsr_admin/{config,collect}.py`, тесты.

**Interfaces:**
- Produces:
  - `Config` (dataclass, JSON в `$NPSR_HOME/config.json`): `reports: dict[str, ReportCfg(folder: str, pattern: str, allowed_lag: int = 1)]`, `norms: dict`, `duck_threshold: float = 0.15`, `phrase: str | None`, `repo_dir: str`; `load_config() -> Config`, `save_config(cfg) -> None`. Шаблоны по умолчанию: `oper: "Опер_отчет_*.xlsb"`, `funnel: "АП_НП_СР_Воронка_Дни*.xlsx"`, `gkg: "АП_НП_СР_Воронка_ГкГ_НС*.xlsb"`, `attempts300: "*Попытки в 300+*.xlsx"`, `ak: "АП_НП_СР_АК*.xlsb"`, `orders: "АП_Свод_по_заказам*.xlsb"`, `oz_speed: "АП_НП_Обратный звонок_new*.xlsm"`, `oz_attempts: "АП_НП_СР_Попытки в первичке ПИНы_ОЗ*.xlsx"`.
  - `find_latest(folder: Path, pattern: str) -> Path | None` (по mtime).
  - `collect(cfg: Config, store: Store, files: dict[str, Path] | None = None, progress: Callable[[str], None] = print) -> list[CollectItem(source, file, data_date, warnings, error)]` — копирует файл в `$NPSR_HOME/cache/`, парсит, сохраняет; ошибка одного источника не останавливает остальные; `files` — ручные файлы (drag-and-drop) поверх папок.
- [ ] **Step 1: тесты** — `find_latest` выбирает самый новый из двух подходящих; недоступная папка → `CollectItem.error == "папка недоступна: <путь>"`, остальные источники собраны; источник, чей парсер бросил исключение, → `error` с текстом исключения.
- [ ] **Step 2: FAIL → реализовать → PASS → commit** `feat: config and folder collection`

### Task 12: Публикация

**Files:** Create `admin/npsr_admin/publish.py`, тест.

**Interfaces:**
- Produces: `publish(payload: dict, cfg: Config, push: bool = True) -> PublishResult(commit: str | None, files: list[str])` — пишет `web/public/data/dashboard.enc.json` (конверт) и открытый `web/public/data/version.json` `{"rev": <sha256 конверта>, "generatedAt": ...}`; затем `check_public.main` по изменённым файлам, `git add` только этих двух файлов, `git commit -m "data: <dataDate>"`, `git push`. `change_phrase(cfg) -> str` — новая фраза, сохраняет в конфиг; следующий `publish` шифрует новой. `share_link(cfg) -> str`.
- [ ] **Step 1: тесты** (на временном git-репозитории, `push=False`) — после `publish` в коммите ровно 2 файла; `dashboard.enc.json` расшифровывается фразой из конфига; в рабочей папке лежит `x.xlsb` — он не попадает в коммит; `share_link` = `https://konturproject.github.io/<repo>/#/?k=<фраза>`.
- [ ] **Step 2: FAIL → реализовать → PASS → commit** `feat: encrypted publish`

### Task 13: Админка (сервер + интерфейс + ярлык)

**Files:** Create `admin/npsr_admin/{server,__main__}.py`, `admin/npsr_admin/ui/{index.html,app.js,style.css}`, `Запустить админку.bat`, тест `admin/tests/test_server.py`.

**Interfaces:**
- Consumes: Task 10–12.
- Produces: HTTP на `127.0.0.1:8765` (свободный порт, если занят): `GET /` (UI), `GET/PUT /api/config`, `POST /api/collect` (запускает сбор в потоке), `GET /api/progress` (строки прогресса + итог `CollectItem[]`), `POST /api/upload?source=<id>` (тело — файл), `POST /api/publish`, `POST /api/phrase` (смена фразы), `GET /api/preview` (payload без шифрования — для сводки). `python -m npsr_admin` стартует сервер и открывает браузер; `.bat` запускает `admin\.venv\Scripts\pythonw.exe -m npsr_admin`.
- UI: три зоны на одной странице — «Источники» (таблица 8 отчётов: путь к папке, шаблон, последний файл, дата данных, статус ✓/⚠/✗, зона drop для ручного файла), кнопки **«Собрать отчёты»** и **«Опубликовать»** (вторая активна после успешного сбора), «Нормативы» (редактируемая таблица), «Ссылка для руководителей» (поле + «Скопировать» + «Сменить код»). Стиль — палитра из Global Constraints.
- [ ] **Step 1: тест** — сервер в потоке на свободном порту: `PUT /api/config` затем `GET` возвращает сохранённый путь; `POST /api/collect` с `NPSR_HOME`-конфигом на пустую папку завершается, и `/api/progress` содержит `error` для всех 8 источников; сервер отказывает в запросе с `Host`, отличным от `127.0.0.1`/`localhost` (403).
- [ ] **Step 2: FAIL → реализовать → PASS**
- [ ] **Step 3: ручная проверка** — запустить `.bat`, указать для всех 8 отчётов папку проекта (там лежат образцы), «Собрать отчёты»: все ✓ или ⚠ с понятным текстом; сводка показывает дату данных 06.11.2026 для Опер_отчета. Скриншот в браузере.
- [ ] **Step 4: commit** `feat: local admin app`

### Task 14: Дашборд: доступ, загрузка данных, оценка зон

**Files:** Create `web/src/{data,access,eval,format}.ts(x)`, `web/tests/{eval,data}.test.ts`.

**Interfaces:**
- Consumes: `decryptJson` (Task 9), схема payload (Task 10).
- Produces:
  - `loadDashboard(phrase: string) -> Promise<Payload>` (fetch `data/dashboard.enc.json?v=<rev из version.json>`, `cache: "no-store"` для `version.json`); `DecryptError` → экран доступа.
  - `readPhrase(): string | null` — из `#/?k=` (сохранить в localStorage, убрать из адреса через `history.replaceState`) или из localStorage (в try/catch).
  - `zone(args: {value: number | undefined, absolute: number | undefined, peers: number[], norm?: {floor?: number, target?: number}, duck: number}) -> {zone: "good" | "risk" | "bad" | "none", best: boolean}` — порядок: нет значения → `none`; `value < mean(peers)*(1-duck)` или `absolute < floor` → `bad`; `absolute < target` (или, без норматива, `value < mean(peers)`) → `risk`; иначе `good`; `best` = значение равно максимуму peers. `absolute` — недельный накопленный итог (в режиме «неделя» = `value`).
  - `runrateTier(v: number) -> "below" | "ok" | "super" | "top"` (пороги 100 / 120 / 140; подписи «ниже плана», «круто», «супер», «отличный кайф»).
  - `fmt(metric: string, v: number) -> string` (проценты без знаков после запятой, удельные — 1 знак, запятая как разделитель).
- [ ] **Step 1: тесты**

```ts
const peers = [3.9, 3.1, 4.4, 2.6, 4.1, 3.5]
expect(zone({value: 2.6, absolute: 2.6, peers, norm: {target: 4}, duck: .15})).toEqual({zone: "bad", best: false})
expect(zone({value: 3.1, absolute: 3.1, peers, norm: {target: 4}, duck: .15})).toEqual({zone: "risk", best: false})
expect(zone({value: 4.4, absolute: 4.4, peers, norm: {target: 4}, duck: .15})).toEqual({zone: "good", best: true})
expect(zone({value: 1.3, absolute: 1.1, peers: [1.3,1.4], norm: {floor: 1.2, target: 1.5}, duck: .15}).zone).toBe("bad")
expect(zone({value: undefined, absolute: undefined, peers, duck: .15}).zone).toBe("none")
// холодный день: все просели одинаково — никто не «утёнок»
expect(zone({value: 2.0, absolute: 3.8, peers: [2.0,2.1,1.9,2.0,2.2,2.0], norm: {target: 4}, duck: .15}).zone).toBe("risk")
expect(runrateTier(99.9)).toBe("below"); expect(runrateTier(120)).toBe("super"); expect(runrateTier(140)).toBe("top")
```

  Плюс тест `readPhrase`: при `location.hash = "#/?k=abc"` возвращает `"abc"`, после вызова hash не содержит `k=`. Тест загрузки: неверная фраза → `DecryptError`.
- [ ] **Step 2: FAIL → реализовать → PASS → commit** `feat: dashboard data access and zone evaluation`

### Task 15: Главный экран

**Files:** Create `web/src/App.tsx`, `web/src/screens/Main.tsx`, `web/src/ui/{Ring,Heatmap,GroupCard}.tsx`, `web/src/styles.css`, тест `web/tests/main.test.tsx` (Vitest + Testing Library).

**Interfaces:**
- Consumes: Task 14.
- Produces: маршруты `#/` (главный), `#/g/<ключ группы>` (Task 16). `Heatmap({rows: {entity, label, href?}[], metrics: MetricDef[], period, payload})`, `Ring({value, size: "lg" | "sm", label})`, `GroupCard({group, period, payload})`. `METRICS: MetricDef[]` в `web/src/metrics.ts` — порядок колонок: `runrate_money, quality_invoices, long_presentations, taken, ns1_attempts, attempts_300, oz_attempts, oz_speed_30, ak_rg_feedback, ak_robot_coverage, ak_pay_term_primary, ak_pay_term_ns, orders_extra_seats, orders_schools, orders_periodicals`; у каждого — `label`, `granularity: "day" | "week"`, `unit`.
- Экран (по макету А+Б, `.superpowers/brainstorm/*/content/layout.html`): шапка с выбором недели (4 чипа) и дня (дни недели + «вся неделя», по умолчанию `dataDate`); слева крупное кольцо ран-рейта по деньгам + малое по штукам + подпись ступени; 3 KPI (кач. счета, скорость ОЗ, попытки 300+); тепловая карта: 6 групп, затем «Тверь», «Москва», «Направление»; недельные метрики в дневном режиме — значение недели с пометкой «нед.»; ниже 6 карточек групп. Плашка «Данные за 06.11, обновлено …», устаревшие источники — значок ⚠ в заголовке их колонок. Легенда зон.
- [ ] **Step 1: тест** — на фикстуре payload (6 групп, СР9 без `attempts_300`): в таблице 9 строк; ячейка СР9 × `attempts_300` содержит «—» и не имеет классов зон; клик по строке СР1 меняет hash на `#/g/СР1`.
- [ ] **Step 2: FAIL → реализовать → PASS**
- [ ] **Step 3: визуальная проверка** — `npm run dev` с локальным payload (`publish(push=False)` из Task 12 на образцах), скриншоты при 1280 px и 375 px; горизонтальный скролл только у таблицы, не у страницы. Сверить с макетом.
- [ ] **Step 4: commit** `feat: main dashboard screen`

### Task 16: Экран группы и динамика сотрудника

**Files:** Create `web/src/screens/Group.tsx`, `web/src/ui/Trend.tsx`, тест `web/tests/group.test.tsx`.

**Interfaces:**
- Consumes: Task 14–15 (`Heatmap`, `GroupCard`, `zone`).
- Produces: `#/g/<ключ>`: паспорт группы (крупный `GroupCard`), кнопки всех 6 групп, тепловая карта «сотрудники группы × показатели» (peers для зон — сотрудники всего направления), клик по ячейке → `Trend({entity, metric, payload})`: линия по дням 4 недель (недельные метрики — ступеньки), пунктир норматива, точки окрашены по зоне.
- [ ] **Step 1: тест** — на фикстуре: `#/g/СР2` показывает только сотрудников СР2; клик по ячейке открывает `Trend` с 4 неделями по оси; кнопка «СР3» переводит на `#/g/СР3`; неизвестный ключ группы → редирект на `#/`.
- [ ] **Step 2: FAIL → реализовать → PASS → визуальная проверка (1280/375) → commit** `feat: group screen and employee trend`

### Task 17: Репозиторий, деплой, сквозная проверка

**Files:** Create `.github/workflows/deploy.yml`, `README.md` (как запустить админку, как сменить код), `web/vite.config.ts` (`base: "/<repo>/"`).

- [ ] **Step 1:** имя репозитория — нейтральное, например `pulse-board` (подтвердить с автором при создании). `gh repo create KonturProject/<repo> --public --source . --push` — **только после** `git ls-files | python scripts/check_public.py` = 0.
- [ ] **Step 2:** workflow: на push в `main` — `python scripts/check_public.py $(git ls-files)`, `npm ci && npm test && npm run build` в `web/`, деплой `web/dist` через `actions/deploy-pages`. Включить Pages (Source: GitHub Actions) через `gh api`.
- [ ] **Step 3: сквозная проверка** — админка: сбор образцов → «Опубликовать» → через 1–2 мин открыть ссылку из админки во встроенном браузере: главный экран с данными за 06.11.2026; ссылка без `k=` в новом профиле → экран кода доступа; неверный код → «Код не подходит». Смена кода → старая ссылка перестаёт открывать данные, новая открывает.
- [ ] **Step 4: commit** `chore: deploy pipeline and README`
