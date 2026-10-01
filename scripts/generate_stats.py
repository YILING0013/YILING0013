"""读取 GitHub 官方公开仓库数据和贡献汇总，缓存快照并绘制主页 SVG 统计卡。"""

import argparse
import json
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta, timezone
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOGIN = "YILING0013"
PROJECTS = ("AI_NovelGenerator", "ChangeFolderIcon", "Shortcut_Hint", "novelai_local_web")
COLORS = ("#3a8dcc", "#53b9be", "#949bc4", "#caa763", "#85afca", "#a8bac8")
# 小字号采用同色系更深的文字色，保留浅色卡片的可读性。
TEXT_COLORS = ("#317eb6", "#327f86", "#69739c", "#906c2c", "#5d82ad", "#667b8d")


def github_json(*arguments: str) -> dict | list:
    """
    通过已登录的 GitHub CLI 读取 JSON；API 错误直接中止，避免发布错误的零值。

    Args:
        arguments: gh api 后的参数；不传入或输出凭据。

    Returns:
        GitHub 返回的 JSON 对象或数组。
    """
    result = subprocess.run(
        ["gh", "api", *arguments], check=True, capture_output=True, encoding="utf-8"
    )
    data = json.loads(result.stdout)
    if isinstance(data, dict) and "errors" in data:
        raise RuntimeError(f"GitHub API returned errors: {data['errors']}")
    return data


def svg_document(width: int, height: int, title: str, description: str, body: list[str]) -> str:
    """
    为统计内容添加统一背景、字体和无障碍说明。

    Args:
        width: SVG 画布宽度。
        height: SVG 画布高度。
        title: 图片标题。
        description: 统计口径和数据说明。
        body: 已绘制的 SVG 内容。

    Returns:
        完整 SVG 文本。
    """
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(title)}</title>',
        f'<desc id="description">{escape(description)}</desc>',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}'
        '.label{fill:#667b8d}.strong{fill:#24364a}.mono{font-family:Consolas,monospace}</style>',
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="16" '
        'fill="#f7fafc" stroke="#dbe8f2"/>',
        *body,
        '</svg>',
        '',
    ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cached", action="store_true", help="只读取已保存的快照重新绘图，不访问网络")
    parser.add_argument("--end", type=datetime.fromisoformat, help="最后一个完整 UTC 日，YYYY-MM-DD；默认昨天")
    args = parser.parse_args()
    cache_path = ROOT / "data" / "profile-stats.json"
    if args.cached:
        snapshot = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        now = datetime.now(timezone.utc)
        end = args.end.date() if args.end else now.date() - timedelta(days=1)
        if end >= now.date():
            raise ValueError("统计结束日期必须早于今天，确保只包含完整 UTC 日。")
        start = end - timedelta(days=364)
        user = github_json(f"users/{LOGIN}")
        # /users/{login}/repos 仅列公开仓库；不能替换为会读取私人仓库的 /user/repos。
        pages = github_json(f"users/{LOGIN}/repos?type=owner&per_page=100", "--paginate", "--slurp")
        owned = [repo for page in pages for repo in page if repo["owner"]["login"].lower() == LOGIN.lower()]
        if any(repo["private"] for repo in owned):
            raise ValueError("公开仓库端点返回了非公开数据，已停止。")
        nonfork = [repo for repo in owned if not repo["fork"]]
        repositories = []
        language_bytes = Counter()
        # 只保留项目卡和可核对统计所需的公开字段；不保存原始 API 响应。
        with ThreadPoolExecutor(max_workers=4) as pool:
            language_results = list(pool.map(
                github_json, [f"repos/{LOGIN}/{repo['name']}/languages" for repo in nonfork]
            ))
        for repo, languages in zip(nonfork, language_results, strict=True):
            language_bytes.update(languages)
            repositories.append({
                "name": repo["name"],
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "languages": languages,
            })
        query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
              restrictedContributionsCount
              totalCommitContributions
              totalIssueContributions
              totalPullRequestContributions
              totalPullRequestReviewContributions
              totalRepositoryContributions
              contributionCalendar {
                totalContributions
                weeks { firstDay contributionDays { date contributionCount color weekday } }
              }
            }
          }
        }
        """
        response = github_json(
            "graphql", "-f", f"query={query}", "-f", f"login={LOGIN}",
            "-f", f"from={datetime.combine(start, time.min, timezone.utc).isoformat()}",
            "-f", f"to={datetime.combine(end, time(23, 59, 59), timezone.utc).isoformat()}",
        )
        contributions = response["data"]["user"]["contributionsCollection"]
        calendar = contributions["contributionCalendar"]
        days = sorted([
            {**day, "week": index, "week_start": week["firstDay"]}
            for index, week in enumerate(calendar["weeks"])
            for day in week["contributionDays"]
            if start.isoformat() <= day["date"] <= end.isoformat()
        ], key=lambda day: day["date"])
        expected_dates = [(start + timedelta(days=index)).isoformat() for index in range(365)]
        if [day["date"] for day in days] != expected_dates:
            raise ValueError("GitHub 返回的贡献日历不包含连续 365 个完整 UTC 日。")
        count = sum(day["contributionCount"] for day in days)
        if count != calendar["totalContributions"]:
            raise ValueError("日贡献之和与 GitHub 日历总数不同，已停止。")
        streak, longest_streak = 0, 0
        for day in days:
            streak = streak + 1 if day["contributionCount"] > 0 else 0
            longest_streak = max(longest_streak, streak)
        total_bytes = sum(language_bytes.values())
        snapshot = {
            "schema_version": 1,
            "login": LOGIN,
            "generated_at": now.isoformat(),
            "period": {"start": start.isoformat(), "end": end.isoformat(), "timezone": "UTC", "days": 365},
            "scope": {
                "repositories": "Public repositories owned by YILING0013; forks excluded from stars, forks and code bytes; archived repositories included.",
                "contributions": "GitHub contribution-calendar totals. May include anonymous private contribution counts according to profile visibility and API permissions. No private repository metadata is requested or saved.",
                "languages": "GitHub Linguist code bytes across public owned non-fork repositories; not skill proficiency or time spent coding.",
                "sources": ["https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user", "https://docs.github.com/en/graphql/reference/users#contributionscollection"],
            },
            "totals": {
                "stars": sum(repo["stars"] for repo in repositories),
                "forks": sum(repo["forks"] for repo in repositories),
                "followers": user["followers"],
                "public_owned_repositories": len(owned),
                "public_nonfork_repositories": len(nonfork),
                "contributions": count,
                "active_days": sum(day["contributionCount"] > 0 for day in days),
                "longest_streak": longest_streak,
                "commits": contributions["totalCommitContributions"],
                "pull_requests": contributions["totalPullRequestContributions"],
                "issues": contributions["totalIssueContributions"],
                "reviews": contributions["totalPullRequestReviewContributions"],
                "created_repositories": contributions["totalRepositoryContributions"],
                "restricted_contributions": contributions["restrictedContributionsCount"],
                "language_bytes": total_bytes,
            },
            "repositories": sorted(repositories, key=lambda repo: (-repo["stars"], repo["name"])),
            "languages": [
                {"name": name, "bytes": size, "percent": size / total_bytes * 100}
                for name, size in language_bytes.most_common()
            ],
            "days": days,
        }
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    totals = snapshot["totals"]
    period = snapshot["period"]
    updated = snapshot["generated_at"][:10]
    output = ROOT / "assets" / "stats"
    output.mkdir(parents=True, exist_ok=True)
    overview = [
        '<text x="25" y="33" font-size="16" font-weight="600" class="strong">GitHub overview</text>',
        '<path d="M 25,48 H 415" stroke="#dbe8f2"/>',
    ]
    metrics = [
        ("stars", "Stars earned", 25, 82, TEXT_COLORS[0]),
        ("forks", "Project forks", 235, 82, TEXT_COLORS[0]),
        ("followers", "Followers", 25, 160, TEXT_COLORS[1]),
        ("public_owned_repositories", "Public repos", 235, 160, TEXT_COLORS[1]),
    ]
    for key, label, x, y, color in metrics:
        overview.extend([
            f'<text x="{x}" y="{y}" font-size="14" class="label">{label}</text>',
            f'<text x="{x}" y="{y + 36}" font-size="34" font-weight="700" fill="{color}">{totals[key]:,}</text>',
        ])
    overview.extend([
        '<path d="M 25,213 H 415" stroke="#dbe8f2"/>',
        f'<text x="25" y="233" font-size="11" class="label">Stars / forks: public, non-fork · {updated} UTC</text>',
    ])
    (output / "overview.svg").write_text(svg_document(
        440, 248, "GitHub overview", snapshot["scope"]["repositories"], overview
    ), encoding="utf-8")

    languages = snapshot["languages"]
    displayed = languages[:5]
    if len(languages) > 5:
        other_bytes = sum(language["bytes"] for language in languages[5:])
        displayed = displayed + [{"name": "Other", "bytes": other_bytes, "percent": other_bytes / totals["language_bytes"] * 100}]
    language_card = [
        '<text x="25" y="33" font-size="16" font-weight="600" class="strong">Languages</text>',
        '<text x="25" y="59" font-size="12" class="label">Public non-fork code bytes</text>',
        '<defs><clipPath id="bar"><rect x="25" y="76" width="390" height="14" rx="7"/></clipPath></defs>',
        '<g clip-path="url(#bar)">',
    ]
    x = 25.0
    for language, color in zip(displayed, COLORS, strict=False):
        width = language["percent"] * 3.9
        language_card.append(f'<rect x="{x:.4f}" y="76" width="{width:.4f}" height="14" fill="{color}"/>')
        x += width
    language_card.append('</g>')
    for index, language in enumerate(displayed):
        x = 25 + (index % 2) * 205
        y = 118 + (index // 2) * 34
        language_card.extend([
            f'<circle cx="{x + 4}" cy="{y - 4}" r="4" fill="{COLORS[index]}"/>',
            f'<text x="{x + 15}" y="{y}" font-size="14" class="strong">{escape(language["name"])}</text>',
            f'<text x="{x + 182}" y="{y}" text-anchor="end" font-size="14" class="label">{language["percent"]:.1f}%</text>',
        ])
    if not languages:
        language_card.append('<text x="25" y="138" font-size="16" class="label">No public code bytes detected</text>')
    language_card.extend([
        '<path d="M 25,213 H 415" stroke="#dbe8f2"/>',
        f'<text x="25" y="233" font-size="11" class="label">Code mix, not skill level · {updated} UTC</text>',
    ])
    (output / "languages.svg").write_text(svg_document(
        440, 248, "Languages", snapshot["scope"]["languages"] + " " +
        "; ".join(f"{language['name']}: {language['bytes']:,} bytes" for language in languages), language_card
    ), encoding="utf-8")

    streak_card = [
        f'<text x="25" y="25" font-size="14" class="label">Last 365 complete days · {period["start"]} — {period["end"]} UTC</text>',
        '<path d="M 282,45 V 113 M 560,45 V 113" stroke="#dbe8f2"/>',
    ]
    for x, key, label, color in [
        (140, "contributions", "Contributions", TEXT_COLORS[0]),
        (420, "active_days", "Active days", TEXT_COLORS[1]),
        (700, "longest_streak", "Longest streak", TEXT_COLORS[2]),
    ]:
        streak_card.extend([
            f'<text x="{x}" y="78" text-anchor="middle" font-size="38" font-weight="700" fill="{color}">{totals[key]:,}</text>',
            f'<text x="{x}" y="108" text-anchor="middle" font-size="21" class="strong">{label}</text>',
        ])
    (output / "streak.svg").write_text(svg_document(
        840, 132, "Contribution rhythm over the last 365 complete days",
        f"{totals['contributions']:,} contributions, {totals['active_days']} active days, "
        f"longest consecutive streak of {totals['longest_streak']} days within {period['start']} to {period['end']} UTC. "
        + snapshot["scope"]["contributions"], streak_card
    ), encoding="utf-8")

    # 手机使用独立画布，避免将桌面横条整体缩小后导致标签难以阅读。
    streak_mobile = [
        '<text x="25" y="27" font-size="16" font-weight="600" class="strong">Last 365 complete days</text>',
        f'<text x="25" y="49" font-size="13" class="label">{period["start"]} — {period["end"]} UTC</text>',
        '<path d="M 25,66 H 395 M 140,84 V 157 M 280,84 V 157" stroke="#dbe8f2"/>',
    ]
    for x, key, label, color in [
        (70, "contributions", "Contributions", TEXT_COLORS[0]),
        (210, "active_days", "Active days", TEXT_COLORS[1]),
        (350, "longest_streak", "Longest streak", TEXT_COLORS[2]),
    ]:
        streak_mobile.extend([
            f'<text x="{x}" y="121" text-anchor="middle" font-size="36" font-weight="700" fill="{color}">{totals[key]:,}</text>',
            f'<text x="{x}" y="148" text-anchor="middle" font-size="14" class="strong">{label}</text>',
        ])
    (output / "streak-mobile.svg").write_text(svg_document(
        420, 180, "Contribution rhythm over the last 365 complete days",
        f"{totals['contributions']:,} contributions, {totals['active_days']} active days, "
        f"longest consecutive streak of {totals['longest_streak']} days within {period['start']} to {period['end']} UTC. "
        + snapshot["scope"]["contributions"], streak_mobile
    ), encoding="utf-8")

    by_name = {repo["name"]: repo for repo in snapshot["repositories"]}
    for name in PROJECTS:
        repo = by_name[name]
        badge = [
            '<path d="M 110,6 V 22" stroke="#dbe8f2"/>',
            f'<text x="55" y="19" text-anchor="middle" font-size="13" fill="#906c2c">★ Stars {repo["stars"]:,}</text>',
            f'<text x="165" y="19" text-anchor="middle" font-size="13" fill="#327f86">⑂ Forks {repo["forks"]:,}</text>',
        ]
        (output / f"{name}.svg").write_text(svg_document(
            220, 28, f"{name} repository stats",
            f"{repo['stars']:,} stars and {repo['forks']:,} forks, retrieved {updated} UTC.", badge
        ), encoding="utf-8")
        badge_mobile = [
            '<path d="M 12,25 H 128" stroke="#dbe8f2"/>',
            '<text x="14" y="19" font-size="13" fill="#906c2c">★ Stars</text>',
            f'<text x="126" y="19" text-anchor="end" font-size="13" font-weight="600" fill="#906c2c">{repo["stars"]:,}</text>',
            '<text x="14" y="40" font-size="13" fill="#327f86">⑂ Forks</text>',
            f'<text x="126" y="40" text-anchor="end" font-size="13" font-weight="600" fill="#327f86">{repo["forks"]:,}</text>',
        ]
        (output / f"{name}-mobile.svg").write_text(svg_document(
            140, 48, f"{name} repository stats",
            f"{repo['stars']:,} stars and {repo['forks']:,} forks, retrieved {updated} UTC.", badge_mobile
        ), encoding="utf-8")
    print(json.dumps({"cache": str(cache_path), "assets": str(output), "period": period, "totals": totals}, ensure_ascii=False, indent=2))
