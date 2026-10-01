"""用统计快照绘制清爽的贡献日历与水滴动效，无需额外网络请求。"""

import json
from datetime import date
from pathlib import Path
from xml.etree import ElementTree


def render_calendar(days: list[dict], compact: bool) -> str:
    """
    将真实每日贡献绘成日历，让水滴缓慢经过活跃日期。

    Args:
        days: 按日期升序排列的每日记录，包含 date 和 contributionCount。
        compact: 手机布局将一年的周数分成上下两段，保持格子可辨认。

    Returns:
        含纯 CSS 动画和减少动态效果支持的 SVG 文本。
    """
    width, height = (420, 365) if compact else (840, 236)
    left, top, step = (35, 92, 13) if compact else (71, 88, 13)
    columns = 27 if compact else 53
    offset = (date.fromisoformat(days[0]["date"]).weekday() + 1) % 7
    total = sum(day["contributionCount"] for day in days)
    active = sum(day["contributionCount"] > 0 for day in days)
    peak = max(day["contributionCount"] for day in days)
    colors = ("#e8f0f5", "#bcdceb", "#86bfd9", "#559abc", "#346e95")
    cells, positions, months = [], [], set()
    for index, day in enumerate(days):
        week, weekday = divmod(index + offset, 7)
        panel, column = divmod(week, columns)
        x, y = left + column * step, top + panel * 125 + weekday * step
        count = day["contributionCount"]
        level = 0 if not count else min(4, max(1, (count * 4 + peak - 1) // peak))
        cells.append(f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{colors[level]}"><title>{day["date"]}: {count} contributions</title></rect>')
        if count:
            positions.append((x + 5, y + 4))
        current_date = date.fromisoformat(day["date"])
        if current_date.day <= 7 and (panel, current_date.month) not in months:
            months.add((panel, current_date.month))
            cells.append(f'<text x="{x}" y="{top + panel * 125 - 12}" class="minor">{current_date.strftime("%b")}</text>')

    # 没有活跃记录时，水滴停在日历外；不把零贡献伪装成有贡献。
    route = positions if positions else [(width - 35, 36)]
    route = route + [route[0]]
    keyframes = "".join(
        f'{index / (len(route) - 1) * 100:.2f}%{{transform:translate({x}px,{y}px)}}'
        for index, (x, y) in enumerate(route)
    )
    initial_x, initial_y = route[0]
    last_x, last_y = route[-2]
    baseline = height - 25
    legend_x = width - 110
    legend = "".join(f'<rect x="{legend_x + i * 13}" y="{baseline - 8}" width="9" height="9" rx="2" fill="{color}"/>' for i, color in enumerate(colors))
    axis = "".join(
        f'<text x="{left - 23}" y="{top + panel * 125 + row * step + 8}" class="minor">{label}</text>'
        for panel in range(2 if compact else 1)
        for row, label in [(1, "M"), (3, "W"), (5, "F")]
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">Contribution calendar</title>
<desc id="description">{days[0]['date']} to {days[-1]['date']} UTC. {total} GitHub calendar contributions across {active} active days. A decorative water droplet visits active dates; cell colors retain the real counts.</desc>
<style>
text{{font-family:Segoe UI,Microsoft YaHei,sans-serif;fill:#24364a}}.minor{{font-size:10px;fill:#667b8d}}
.droplet{{transform:translate({initial_x}px,{initial_y}px);animation:roam 48s linear infinite}}
@keyframes roam{{{keyframes}}}
@media(prefers-reduced-motion:reduce){{.droplet{{animation:none;transform:translate({last_x}px,{last_y}px)}}}}
</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" fill="#f7fafc" stroke="#dbe8f2"/>
<text x="24" y="33" font-size="19" font-weight="600">Contribution calendar</text>
<text x="24" y="55" font-size="12" fill="#667b8d">{total} contributions · {active} active days · 365 days</text>
{axis}{''.join(cells)}
<g class="droplet">
  <path d="M0-9C-2-4-6-1-6 3a6 6 0 0 0 12 0C6-1 2-4 0-9Z" fill="#57a6cd" stroke="#ffffff" stroke-width="1.3"/>
  <path d="M-3 2q-1 4 3 4" fill="none" stroke="#dff8ff" stroke-width="1.5" stroke-linecap="round"/>
</g>
<text x="24" y="{baseline}" class="minor">{days[0]['date']} — {days[-1]['date']} UTC</text>
{legend}<text x="{width - 20}" y="{baseline}" text-anchor="end" class="minor">+</text>
</svg>'''
    return svg + "\n"


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    snapshot = json.loads((root / "data/profile-stats.json").read_text(encoding="utf-8"))
    for compact in (False, True):
        suffix = "-mobile" if compact else ""
        svg = render_calendar(snapshot["days"], compact)
        ElementTree.fromstring(svg)
        (root / "assets" / f"contribution-calendar{suffix}.svg").write_text(svg, encoding="utf-8", newline="\n")
    print("Generated desktop and mobile contribution calendars.")
