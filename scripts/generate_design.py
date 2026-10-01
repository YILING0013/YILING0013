"""生成清爽水蓝页头和技术标签；人物由独立的可编辑 SVG 提供。"""

from pathlib import Path
from xml.etree import ElementTree


def render_header(portrait: str, portrait_viewbox: str, compact: bool) -> str:
    """
    将人物与水元素分层排入页头，让插画自然越过底板边缘。

    Args:
        portrait: 芙宁娜 SVG 根元素内部的矢量图层。
        portrait_viewbox: 原人物画布，保留补画的右手与四周留白。
        compact: 是否采用手机尺寸和位置。

    Returns:
        不含位图、外链或脚本的独立 SVG。
    """
    width, height = (480, 516) if compact else (1000, 398)
    card_x, card_y, card_w, card_h = (14, 34, 428, 420) if compact else (18, 52, 946, 282)
    x, title_y, title_size = (34, 90, 41) if compact else (50, 146, 66)
    px, py, pw, ph = (108, 136, 361, 367) if compact else (622, 5, 371, 377)
    circle_x, circle_y, circle_r = (284, 317, 134) if compact else (807, 199, 133)
    details = "" if compact else '<text x="51" y="242" font-size="16" fill="#718598">Python · TypeScript · C# / C++</text>'
    bubbles = [(24, 278, 15, 0), (433, 109, 10, 1.8), (451, 349, 18, 3.1), (133, 463, 12, 1)] if compact else [(603, 102, 12, 0), (947, 45, 9, 1.8), (970, 234, 19, 3.1), (628, 338, 13, 1)]
    bubble_art = "\n".join(
        f'<g transform="translate({bx} {by})"><g class="bubble" style="animation-delay:-{delay}s">'
        f'<circle r="{radius}" fill="url(#water-bubble)" stroke="#a7d7e8" stroke-width="1.3"/>'
        f'<path d="M{-radius * .55:.1f} 0A{radius * .6:.1f} {radius * .6:.1f} 0 0 1 0 {-radius * .6:.1f}" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/>'
        '</g></g>' for bx, by, radius, delay in bubbles
    )
    # 背景和插画采用不同的裁切范围；溢出的是底板边缘，而非 GitHub 图片边界。
    back_wave = 'M93 435C94 405 225 388 340 405S460 449 432 464' if compact else 'M607 313C626 275 796 273 908 298S1001 347 959 355'
    front_wave = 'M430 464C375 489 206 482 133 463C108 457 93 447 93 435' if compact else 'M959 355C901 386 691 373 621 342C601 332 598 323 607 313'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
<title id="title">YILING0013</title>
<desc id="description">做一些实用，也有趣的小工具。芙宁娜双手张开，发梢、手套和水泡越过浅蓝底板，水环与气泡缓缓浮动。</desc>
<defs>
  <clipPath id="header-frame"><rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="22"/></clipPath>
  <radialGradient id="water-bubble" cx=".3" cy=".25" r=".8"><stop stop-color="#fff" stop-opacity=".9"/><stop offset=".75" stop-color="#d5eff8" stop-opacity=".28"/><stop offset="1" stop-color="#c8e7f2" stop-opacity=".68"/></radialGradient>
  <linearGradient id="portrait-fade" x1="0" y1="0" x2="0" y2="1"><stop offset=".9" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
  <mask id="portrait-edge"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="url(#portrait-fade)"/></mask>
</defs>
<style>
@keyframes drift {{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-7px)}}}}
@keyframes hover {{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-2.5px)}}}}
@keyframes hair {{0%,100%{{transform:rotate(-1deg)}}50%{{transform:rotate(1deg)}}}}
@keyframes glint {{0%,75%,100%{{opacity:.42}}85%{{opacity:1}}}}
.bubble{{animation:drift 7s ease-in-out infinite}}
.portrait-float{{animation:hover 8s ease-in-out infinite}}
#furina-ahoge{{transform-origin:220px 202px;animation:hair 7s ease-in-out infinite}}
.water-glint{{animation:glint 8s ease-in-out infinite}}
@media(prefers-reduced-motion:reduce){{.bubble,.portrait-float,#furina-ahoge,.water-glint{{animation:none}}}}
</style>
<rect x="{card_x + 1}" y="{card_y + 6}" width="{card_w}" height="{card_h}" rx="22" fill="#94c5d9" opacity=".09"/>
<g clip-path="url(#header-frame)">
<rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" fill="#f3f9fd"/>
<circle cx="{circle_x}" cy="{circle_y}" r="{circle_r}" fill="#e2f2fa"/>
<circle cx="{circle_x}" cy="{circle_y}" r="{circle_r + 12}" fill="none" stroke="#dceef5" stroke-width="1"/>
</g>
<g font-family="Segoe UI,Microsoft YaHei,sans-serif">
<text x="{x - 2}" y="{title_y}" font-size="{title_size}" fill="#24394c" font-weight="650" letter-spacing="-2">YILING0013</text>
<text x="{x}" y="{title_y + (37 if compact else 49)}" font-size="{18 if compact else 23}" fill="#50718c">做一些实用，也有趣的小工具。</text>
{details}
</g>
<path d="{back_wave}" fill="none" stroke="#a5d6e4" stroke-width="2" opacity=".65"/>
<g class="portrait-float" mask="url(#portrait-edge)"><svg x="{px}" y="{py}" width="{pw}" height="{ph}" viewBox="{portrait_viewbox}" overflow="visible">{portrait}</svg></g>
<path d="{front_wave}" fill="none" stroke="#e0f2f7" stroke-width="11" opacity=".8"/>
<path d="{front_wave}" fill="none" stroke="#83c4d8" stroke-width="1.7" opacity=".8"/>
{bubble_art}
<g class="water-glint" transform="translate({393 if compact else 905} {475 if compact else 360})" fill="#87bccc"><path d="M0-6Q0 0 6 0Q0 0 0 6Q0 0-6 0Q0 0 0-6Z"/></g>
</svg>\n'''


if __name__ == "__main__":
    assets = Path(__file__).resolve().parents[1] / "assets"
    portrait_source = (assets / "furina.svg").read_text(encoding="utf-8")
    portrait_viewbox = ElementTree.fromstring(portrait_source).attrib["viewBox"]
    # 内嵌真实矢量路径，让 GitHub 中的页头不依赖 SVG 外链引用。
    portrait = portrait_source[portrait_source.index(">") + 1:portrait_source.rindex("</svg>")]
    for compact in (False, True):
        svg = render_header(portrait, portrait_viewbox, compact)
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
