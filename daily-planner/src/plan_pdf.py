"""Render the daily plan as a print-friendly A4 PDF via WeasyPrint."""

from __future__ import annotations

import datetime
from pathlib import Path

from weasyprint import HTML

from .urgency_scoring import ScoredTask

MS_PER_DAY = 86_400_000.0

_CSS = """
@page {
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: "Courier New", Courier, monospace;
    font-size: 11pt;
    color: #000;
    background: #fff;
}
header {
    border-bottom: 2px solid #000;
    padding-bottom: 4mm;
    margin-bottom: 6mm;
}
header h1 { font-size: 14pt; letter-spacing: 0.05em; }
header p  { font-size: 9pt; color: #333; margin-top: 1mm; }
table {
    width: 100%;
    border-collapse: collapse;
}
th {
    font-size: 8pt;
    text-align: left;
    border-bottom: 1px solid #000;
    padding: 1mm 2mm;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
td {
    padding: 2mm 2mm;
    vertical-align: top;
    border-bottom: 1px solid #ccc;
    font-size: 10pt;
}
.slot  { width: 7%; font-weight: bold; }
.fire  { width: 5%; text-align: center; }
.proj  { width: 20%; color: #444; font-size: 9pt; }
.title { width: 52%; }
.dl    { width: 16%; font-size: 9pt; color: #333; }
.notes-row td {
    border-bottom: none;
    height: 12mm;
}
footer {
    margin-top: 8mm;
    font-size: 8pt;
    color: #666;
    border-top: 1px solid #ccc;
    padding-top: 2mm;
}
"""


def _fmt_deadline(st: ScoredTask, now_ms: int) -> str:
    dl = st.task.deadline
    if not dl or dl.deadline_ms is None:
        return ""
    days = (dl.deadline_ms - now_ms) / MS_PER_DAY
    date_str = datetime.datetime.fromtimestamp(dl.deadline_ms / 1000, tz=datetime.timezone.utc).strftime("%d.%m")
    if st.is_overdue:
        return f"просрочено ({date_str})"
    return f"{date_str} (через {int(days)}д)"


def _build_html(slots: list[ScoredTask], now_ms: int, generated_at: str, plan_date: str) -> str:
    rows = []
    for i, st in enumerate(slots, 1):
        fire = "🔥" if st.on_fire else ""
        dl = _fmt_deadline(st, now_ms)
        rows.append(f"""
        <tr>
          <td class="slot">{i}</td>
          <td class="fire">{fire}</td>
          <td class="proj">{st.task.project_id}</td>
          <td class="title">{st.task.title}</td>
          <td class="dl">{dl}</td>
        </tr>
        <tr class="notes-row"><td colspan="5"></td></tr>
        """)

    rows_html = "".join(rows)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><style>{_CSS}</style></head>
<body>
<header>
  <h1>ПЛАН НА {plan_date}</h1>
  <p>Сгенерировано: {generated_at}</p>
</header>
<table>
  <thead>
    <tr>
      <th class="slot">#</th>
      <th class="fire"></th>
      <th class="proj">Проект</th>
      <th class="title">Задача</th>
      <th class="dl">Дедлайн</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>
<footer>autoGil daily-planner · M0 · LLM not used</footer>
</body>
</html>"""


def render_pdf(
    slots: list[ScoredTask],
    output_dir: Path,
    now_ms: int,
) -> Path:
    """Render plan PDF into output_dir. Returns path to written file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    dt = datetime.datetime.fromtimestamp(now_ms / 1000, tz=datetime.timezone.utc)
    plan_date = dt.strftime("%d.%m.%Y")
    generated_at = dt.strftime("%H:%M UTC")
    filename = f"plan_{dt.strftime('%Y-%m-%d')}.pdf"
    out_path = output_dir / filename

    html = _build_html(slots, now_ms, generated_at, plan_date)
    HTML(string=html).write_pdf(str(out_path))
    return out_path
