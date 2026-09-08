"""从 GitHub 官方 API 读取贡献数，生成主页使用的两种主题 SVG。"""

import json
import math
import subprocess
from datetime import datetime, time, timedelta, timezone
from pathlib import Path


def render_graph(days: list[dict], theme: str) -> str:
    """
    将每日贡献数绘制为带日期范围和统计摘要的 SVG 折线图。

    Args:
        days: 按日期排列的每日记录，包含 date 和 contributionCount。
        theme: 图片主题，light 或 dark。

    Returns:
        可直接保存为 SVG 文件的文本。
    """
    palette = {
        "light": ("#ffffff", "#1f2328", "#59636e", "#d1d9e0", "#078574"),
        "dark": ("#0d1117", "#f0f6fc", "#9198a1", "#30363d", "#3dd6b0"),
    }
    background, foreground, muted, border, accent = palette[theme]
    counts = [day["contributionCount"] for day in days]
    total = sum(counts)
    active = sum(count > 0 for count in counts)
    peak = max(counts)
    # 纵轴从零开始；无贡献时仍保留有效刻度，避免除零或夸大波动。
    ceiling = max(4, math.ceil(peak / 4) * 4)
    left, right, top, bottom = 48, 808, 94, 194
    points = [
        (left + index * (right - left) / (len(days) - 1),
         bottom - count / ceiling * (bottom - top))
        for index, count in enumerate(counts)
    ]
    line = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    area = f"{line} L {right},{bottom} L {left},{bottom} Z"
    start = days[0]["date"]
    end = days[-1]["date"]
    description = (
        f"{total} contributions across {active} active days, {start} to {end} UTC. "
        f"Daily peak: {peak}. "
        + "; ".join(f'{day["date"]}: {day["contributionCount"]}' for day in days)
    )
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="840" height="254" '
        'viewBox="0 0 840 254" role="img" aria-labelledby="title description">',
        '<title id="title">Contribution activity · Last 30 days</title>',
        f'<desc id="description">{description}</desc>',
        '<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0%" stop-color="{accent}" stop-opacity="0.18"/>',
        f'<stop offset="100%" stop-color="{accent}" stop-opacity="0.02"/>',
        '</linearGradient></defs>',
        f'<rect x="0.5" y="0.5" width="839" height="253" rx="12" '
        f'fill="{background}" stroke="{border}"/>',
        '<g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">',
        f'<text x="28" y="39" fill="{foreground}" font-size="24" font-weight="600">'
        f'{total:,} <tspan font-size="15" font-weight="400" fill="{muted}">contributions</tspan></text>',
        f'<text x="28" y="63" fill="{muted}" font-size="12">'
        f'{active} active days · {peak} daily peak</text>',
        f'<text x="808" y="38" text-anchor="end" fill="{muted}" font-size="12">LAST 30 DAYS</text>',
    ]
    for tick in (0, ceiling // 2, ceiling):
        y = bottom - tick / ceiling * (bottom - top)
        svg.append(
            f'<path d="M {left},{y} H {right}" stroke="{border}" stroke-dasharray="3 5"/>'
            f'<text x="36" y="{y + 4}" text-anchor="end" fill="{muted}" font-size="11">{tick}</text>'
        )
    svg.extend([
        f'<path d="{area}" fill="url(#area)"/>',
        f'<path d="{line}" fill="none" stroke="{accent}" stroke-width="2.5" '
        'stroke-linecap="round" stroke-linejoin="round"/>',
    ])
    for index in (0, 7, 14, 21, len(days) - 1):
        x = points[index][0]
        label = datetime.fromisoformat(days[index]["date"]).strftime("%b %d")
        anchor = "start" if index == 0 else "end" if index == len(days) - 1 else "middle"
        svg.append(f'<text x="{x:.2f}" y="217" text-anchor="{anchor}" '
                   f'fill="{muted}" font-size="11">{label}</text>')
    svg.extend([
        f'<text x="28" y="239" fill="{muted}" font-size="10">GitHub contributions · Updated daily</text>',
        f'<text x="808" y="239" text-anchor="end" fill="{muted}" font-size="10">{start} — {end} UTC</text>',
        '</g></svg>',
    ])
    return "\n".join(svg) + "\n"


if __name__ == "__main__":
    # 只展示完整 UTC 日，避免把当天尚未结束的数据画成突然下跌。
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=30)
    end = today - timedelta(days=1)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }
    """
    result = subprocess.run([
        "gh", "api", "graphql", "-f", f"query={query}",
        "-f", "login=YILING0013",
        "-f", f"from={datetime.combine(start, time.min, timezone.utc).isoformat()}",
        "-f", f"to={datetime.combine(end, time(23, 59, 59), timezone.utc).isoformat()}",
    ], check=True, stdout=subprocess.PIPE, text=True, encoding="utf-8")
    response = json.loads(result.stdout)
    if response.get("errors"):
        raise RuntimeError(response["errors"])
    weeks = response["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [
        day for week in weeks for day in week["contributionDays"]
        if start.isoformat() <= day["date"] <= end.isoformat()
    ]
    if len(days) != 30:
        raise ValueError(f"Expected 30 complete contribution days, received {len(days)}")
    # API 失败时不覆盖文件，主页继续展示上次成功生成的图片。
    assets = Path(__file__).resolve().parents[1] / "assets"
    assets.mkdir(exist_ok=True)
    for theme in ("light", "dark"):
        (assets / f"activity-{theme}.svg").write_text(render_graph(days, theme), encoding="utf-8", newline="\n")
    print(f"Generated activity graphs: {start} to {end}, {sum(day['contributionCount'] for day in days)} contributions")
