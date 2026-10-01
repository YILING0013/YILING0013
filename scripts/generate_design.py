"""生成清爽水蓝页头和技术标签；人物由独立的可编辑 SVG 提供。"""

from pathlib import Path
from xml.etree import ElementTree


def render_header(portrait: str, compact: bool) -> str:
    """
    将用户参考图的矢量重绘排入简洁页头，手机使用上下布局。

    Args:
        portrait: 芙宁娜 SVG 根元素内部的矢量图层。
        compact: 是否采用手机尺寸和位置。

    Returns:
        不含位图、外链或脚本的独立 SVG。
    """
    width, height = (480, 422) if compact else (1000, 342)
    x, title_y, title_size = (28, 61, 41) if compact else (48, 118, 66)
    portrait_position = "x=\"127\" y=\"105\" width=\"277\" height=\"312\"" if compact else "x=\"601\" y=\"-2\" width=\"361\" height=\"355\""
    circle_x, circle_y, circle_r = (264, 280, 120) if compact else (788, 184, 142)
    details = "" if compact else '<text x="49" y="213" font-size="16" fill="#718598">Python · TypeScript · C# / C++</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">YILING0013</title>
<desc id="description">AI 创作与桌面工具。右侧为根据用户提供图片逐层重绘的芙宁娜 SVG。</desc>
<defs><clipPath id="header-frame"><rect width="{width}" height="{height}" rx="16"/></clipPath></defs>
<g clip-path="url(#header-frame)">
<rect width="{width}" height="{height}" fill="#f3f9fd"/>
<circle cx="{circle_x}" cy="{circle_y}" r="{circle_r}" fill="#e2f2fa"/>
<circle cx="{width - 29}" cy="{height - 42}" r="5" fill="none" stroke="#bcdeee" stroke-width="1.5"/>
<circle cx="{width - 64}" cy="38" r="9" fill="none" stroke="#c5e3ee" stroke-width="1.5"/>
<g font-family="Segoe UI,Microsoft YaHei,sans-serif">
<text x="{x - 2}" y="{title_y}" font-size="{title_size}" fill="#24394c" font-weight="650" letter-spacing="-2">YILING0013</text>
<text x="{x}" y="{title_y + (37 if compact else 49)}" font-size="{18 if compact else 23}" fill="#50718c">做一些实用，也有趣的小工具。</text>
{details}
</g>
<svg {portrait_position} viewBox="0 0 658 728">{portrait}</svg>
</g>
</svg>\n'''


if __name__ == "__main__":
    assets = Path(__file__).resolve().parents[1] / "assets"
    portrait_source = (assets / "furina.svg").read_text(encoding="utf-8")
    # 内嵌真实矢量路径，让 GitHub 中的页头不依赖 SVG 外链引用。
    portrait = portrait_source[portrait_source.index(">") + 1:portrait_source.rindex("</svg>")]
    for compact in (False, True):
        svg = render_header(portrait, compact)
        ElementTree.fromstring(svg)
        (assets / ("header-mobile.svg" if compact else "header.svg")).write_text(svg, encoding="utf-8", newline="\n")

    badges = [('python',
      'Python',
      96,
      '#f0a6cb',
      '<path d="M5 9V6q0-3 4-3h4q3 0 3 3v5H7q-4 0-4 4v1M17 11v3q0 3-4 3H9q-3 0-3-3v-3"/><circle cx="9" cy="6" '
      'r=".5" fill="currentColor"/><circle cx="13" cy="14" r=".5" fill="currentColor"/>'),
     ('typescript',
      'TypeScript',
      121,
      '#aaa0ff',
      '<rect x="3" y="3" width="14" height="14" rx="3"/><path d="M6 8h6m-3 0v6m5-5q-3-1-2 2l2 1q2 3-2 2"/>'),
     ('csharp-cpp',
      'C# / C++',
      114,
      '#f0a6cb',
      '<path d="m11 3 6 4v7l-6 4-7-4V7Z M10 8q-4-2-4 3t4 3m3-6v6m3-6v6m-4-4h5m-5 3h5"/>'),
     ('react',
      'React',
      88,
      '#7dd8d4',
      '<ellipse cx="10" cy="10" rx="8" ry="3"/><ellipse cx="10" cy="10" rx="8" ry="3" transform="rotate(60 10 '
      '10)"/><ellipse cx="10" cy="10" rx="8" ry="3" transform="rotate(120 10 10)"/><circle cx="10" cy="10" '
      'r="1.2" fill="currentColor" stroke="none"/>'),
     ('nextjs', 'Next.js', 101, '#aaa0ff', '<circle cx="10" cy="10" r="8"/><path d="M7 14V6l9 11M13 6v6"/>'),
     ('flask',
      'Flask',
      85,
      '#7dd8d4',
      '<path d="M7 3h6m-5 0v6l-5 7q-1 2 2 2h10q3 0 2-2l-5-7V3M6 13h8"/><circle cx="9" cy="15.5" r=".4" '
      'fill="currentColor"/>'),
     ('javascript',
      'JavaScript',
      125,
      '#efc58d',
      '<rect x="3" y="3" width="14" height="14" rx="3"/><path d="M10 7v6q0 3-3 1m8-6q-4-2-4 1 0 1 2 2t2 2q0 3-4 '
      '1"/>'),
     ('git',
      'Git',
      73,
      '#f0a6b0',
      '<path d="m3 9 6-6q1-1 2 0l6 6q1 1 0 2l-6 6q-1 1-2 0l-6-6q-1-1 0-2Z"/><path d="m7 5 7 7M9 7v8"/><circle '
      'cx="9" cy="7" r="1.3" fill="#161a2f"/><circle cx="9" cy="14" r="1.3" fill="#161a2f"/><circle cx="14" '
      'cy="12" r="1.3" fill="#161a2f"/>'),
     ('blender',
      'Blender',
      106,
      '#eeb282',
      '<ellipse cx="12" cy="12" rx="6" ry="5"/><circle cx="12" cy="12" r="2.3"/><path d="m4 3 8 4H3l5 4-6 4m3-8 '
      '3 4"/>'),
     ('unreal',
      'Unreal Engine',
      141,
      '#9fc6df',
      '<circle cx="10" cy="10" r="8"/><path d="m5 7 3-2v8q0 2 2 2l2-1V6l3-1m-3 1h2v8l-2 1M6 7h2"/>')]
    for index, (name, label, width, old_accent, drawing) in enumerate(badges):
        accent = ("#3c88b9", "#589a9b", "#747ea7", "#ae9267")[index % 4]
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="30" viewBox="0 0 {width} 30" role="img" aria-label="{label}">
<rect x=".5" y=".5" width="{width - 1}" height="29" rx="7" fill="#f6fafc" stroke="#deebf2"/>
<g transform="translate(8 5)" fill="none" color="{accent}" stroke="{accent}" stroke-width="1.15" stroke-linecap="round" stroke-linejoin="round">{drawing}</g>
<text x="35" y="19" fill="#405c71" font-family="Segoe UI,sans-serif" font-size="12">{label}</text>
</svg>\n'''
        ElementTree.fromstring(svg)
        (assets / "stack" / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    print("Generated two Furina headers and", len(badges), "light technology badges.")
