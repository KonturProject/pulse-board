const METRICS = {
  runrate_money: ['Ран-рейт, деньги', 'pct'], runrate_pcs: ['Ран-рейт, штуки', 'pct'],
  quality_invoices: ['Качественные счета на чел.', 'num'], long_presentations: ['Длинные презентации на чел.', 'num'],
  taken: ['Взятые, % плана', 'pct'], completed: ['Завершённые на чел.', 'num'],
  ns1_attempts: ['Попытки в НС1', 'num'], attempts_300: ['Попытки в 300+', 'num'],
  oz_attempts: ['Попытки в ОЗ', 'num'], oz_speed_30: ['ОЗ за 30 мин', 'pct'],
  ak_rg_feedback: ['АК: ОС руководителя', 'score'], ak_robot_coverage: ['АК: охват роботом', 'pct'],
  ak_pay_term_primary: ['АК: срок оплаты, первичка', 'pct'], ak_pay_term_ns: ['АК: срок оплаты, НС', 'pct'],
  orders_extra_seats: ['Доп. места на чел.', 'num'], orders_schools: ['Школы на чел.', 'num'],
  orders_periodicals: ['Периодика на чел.', 'num'],
}
const NORM_KEYS = Object.keys(METRICS)
const $ = (s) => document.querySelector(s)
let cfg = null
let lastItems = []

const fmt = (v, unit) => v == null ? '—'
  : unit === 'pct' ? `${Math.round(v * 100)}%`
  : unit === 'score' ? `${Math.round(v)}` : v.toFixed(1).replace('.', ',')
const fmtDate = (d) => d ? new Date(d + 'T00:00').toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }) : ''

function toast(text) {
  const t = $('#toast'); t.textContent = text; t.classList.add('show')
  setTimeout(() => t.classList.remove('show'), 2600)
}

async function api(method, path, body, raw) {
  const res = await fetch(path, { method, body: raw ?? (body ? JSON.stringify(body) : undefined),
    headers: raw ? {} : { 'Content-Type': 'application/json' } })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || res.statusText)
  return data
}

function statusCell(source) {
  const it = lastItems.find((i) => i.source === source)
  if (!it) return '<span class="st"><small>ещё не собирали</small></span>'
  if (it.error) return `<span class="st err">✗ ошибка<small>${it.error}</small></span>`
  const when = it.data_date ? `данные за ${fmtDate(it.data_date)}` : 'недельный отчёт'
  if (it.warnings.length) return `<span class="st warn">⚠ ${when}<small>${it.warnings.join('; ')}</small></span>`
  return `<span class="st ok">✓ ${when}<small>${it.facts} записей</small></span>`
}

function renderReports() {
  const tb = $('#reports tbody')
  tb.innerHTML = ''
  for (const [key, r] of Object.entries(cfg.reports)) {
    const tr = document.createElement('tr')
    tr.dataset.source = key
    tr.innerHTML = `<td><b>${cfg.names[key] || key}</b></td>
      <td class="folder"><input data-f="folder" value="${r.folder}" placeholder="\\\\server\\reports\\…" aria-label="Папка: ${cfg.names[key]}"></td>
      <td class="pattern"><input data-f="pattern" value="${r.pattern}" aria-label="Шаблон: ${cfg.names[key]}"></td>
      <td>${statusCell(key)}</td>
      <td><label class="pick">файл вручную<input type="file" hidden accept=".xlsx,.xlsb,.xlsm"></label></td>`
    tr.querySelectorAll('input[data-f]').forEach((inp) => inp.addEventListener('change', () => {
      cfg.reports[key][inp.dataset.f] = inp.value.trim(); saveConfig('Путь сохранён')
    }))
    tr.querySelector('input[type=file]').addEventListener('change', (e) => upload(key, e.target.files[0]))
    tr.addEventListener('dragover', (e) => { e.preventDefault(); tr.classList.add('drag') })
    tr.addEventListener('dragleave', () => tr.classList.remove('drag'))
    tr.addEventListener('drop', (e) => { e.preventDefault(); tr.classList.remove('drag'); upload(key, e.dataTransfer.files[0]) })
    tb.appendChild(tr)
  }
}

async function upload(source, file) {
  if (!file) return
  await api('POST', `/api/upload?source=${source}&name=${encodeURIComponent(file.name)}`, null, file)
  toast(`«${file.name}» будет взят при следующем сборе`)
}

function renderNorms() {
  const tb = $('#norms tbody')
  tb.innerHTML = NORM_KEYS.map((k) => {
    const n = cfg.norms[k] || {}, unit = METRICS[k][1]
    const show = (v) => v == null ? '' : unit === 'pct' ? Math.round(v * 100) : v
    return `<tr data-k="${k}"><td>${METRICS[k][0]}${unit === 'pct' ? ', %' : ''}</td>
      <td><input data-n="floor" type="number" step="0.1" value="${show(n.floor)}"></td>
      <td><input data-n="target" type="number" step="0.1" value="${show(n.target)}"></td></tr>`
  }).join('')
  $('#duck').value = Math.round(cfg.duck_threshold * 100)
}

function readNorms() {
  for (const tr of document.querySelectorAll('#norms tbody tr')) {
    const k = tr.dataset.k, unit = METRICS[k][1], n = { ...(cfg.norms[k] || {}) }
    for (const inp of tr.querySelectorAll('input')) {
      const raw = inp.value.trim().replace(',', '.')
      if (raw === '') delete n[inp.dataset.n]
      else n[inp.dataset.n] = unit === 'pct' ? Number(raw) / 100 : Number(raw)
    }
    if (Object.keys(n).length) cfg.norms[k] = n; else delete cfg.norms[k]
  }
  cfg.duck_threshold = Number($('#duck').value) / 100
}

function renderLink() {
  $('#link').textContent = cfg.link || 'Ссылка появится после первой публикации'
  $('#site').value = cfg.site_url || ''
}

async function saveConfig(msg) {
  cfg = await api('PUT', '/api/config', cfg)
  renderLink()
  if (msg) toast(msg)
}

async function renderSummary() {
  const p = await api('GET', '/api/preview')
  const week = p.weeks[p.weeks.length - 1]
  const groups = Object.keys(p.entities).filter((k) => k.startsWith('g:'))
  $('#summary thead').innerHTML = `<tr><th>Показатель, неделя ${week.split('.')[1]}</th>${groups.map((g) => `<th>${p.entities[g].label}</th>`).join('')}<th>Направление</th></tr>`
  $('#summary tbody').innerHTML = Object.entries(METRICS).filter(([k]) => p.values[k]).map(([k, [label, unit]]) => {
    const v = p.values[k][week] || {}
    return `<tr><td>${label}</td>${groups.map((g) => `<td class="num">${fmt(v[g], unit)}</td>`).join('')}<td class="num"><b>${fmt(v.dir, unit)}</b></td></tr>`
  }).join('')
  $('#summary-note').textContent = p.dataDate ? `Данные по ${fmtDate(p.dataDate)}. Проверьте цифры перед публикацией.` : ''
  $('#summary-card').hidden = false
}

async function poll() {
  const pr = await api('GET', '/api/progress')
  $('#log').innerHTML = pr.log.map((l) => `<li>${l}</li>`).join('')
  if (pr.running) return setTimeout(poll, 700)
  lastItems = pr.items
  renderReports()
  $('#collect').disabled = false
  const ok = pr.items.filter((i) => !i.error).length
  $('#status').textContent = `Собрано ${ok} из ${pr.items.length} отчётов`
  $('#publish').disabled = ok === 0
  if (ok) await renderSummary()
}

$('#collect').addEventListener('click', async () => {
  $('#collect').disabled = true
  $('#publish').disabled = true
  $('#progress-card').hidden = false
  $('#status').textContent = 'Собираю отчёты… большие файлы читаются до пары минут'
  await api('POST', '/api/collect', {})
  poll()
})

$('#publish').addEventListener('click', async () => {
  $('#publish').disabled = true
  $('#status').textContent = 'Шифрую и публикую…'
  try {
    const r = await api('POST', '/api/publish', {})
    cfg = await api('GET', '/api/config'); renderLink()
    $('#status').textContent = 'Опубликовано. Сайт обновится через 1–2 минуты.'
    toast('Опубликовано')
  } catch (e) {
    $('#status').textContent = `Не удалось опубликовать: ${e.message}`
    $('#publish').disabled = false
  }
})

$('#save-norms').addEventListener('click', () => { readNorms(); saveConfig('Нормативы сохранены — войдут в следующую публикацию') })
$('#site').addEventListener('change', () => { cfg.site_url = $('#site').value.trim(); saveConfig('Адрес сайта сохранён') })
$('#copy').addEventListener('click', async () => {
  if (!cfg.link) return toast('Сначала опубликуйте данные')
  await navigator.clipboard.writeText(cfg.link); toast('Ссылка скопирована')
})
$('#phrase').addEventListener('click', async () => {
  if (!confirm('Сменить код доступа? Старая ссылка перестанет работать после следующей публикации.')) return
  const r = await api('POST', '/api/phrase', {}); cfg.link = r.link; renderLink()
  toast(r.warning || 'Код сменён и данные перешифрованы — разошлите новую ссылку')
})

;(async () => {
  cfg = await api('GET', '/api/config')
  renderReports(); renderNorms(); renderLink()
  $('#status').textContent = 'Готово к сбору'
})()
