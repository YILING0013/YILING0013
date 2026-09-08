"""生成主页的静态视觉素材；修改设计后在本地运行，无需第三方图片服务。"""

from pathlib import Path


def render_header(compact: bool) -> str:
    """
    绘制带流线插画的个人页头，分别适配桌面和手机。

    Args:
        compact: 是否生成手机使用的紧凑布局。

    Returns:
        完整 SVG 文本。
    """
    colors = {
        "light": ("#f6f9f8", "#172c29", "#536c65", "#d8e6df", "#16856f", "#e3f2e8"),
        "dark": ("#101b20", "#ecf5ef", "#a0b6ac", "#293e3b", "#63d5b0", "#1c3b33"),
    }
    variables = ("background", "text", "muted", "border", "accent", "glow")
    styles = []
    for theme, palette in colors.items():
        rule = ":root{" + ";".join(f"--{name}:{color}" for name, color in zip(variables, palette)) + "}"
        styles.append(rule if theme == "light" else "@media(prefers-color-scheme:dark){" + rule + "}")
    background, text, muted, border, accent, glow = [f"var(--{name})" for name in variables]
    width, height = (480, 244) if compact else (960, 272)
    x = 28 if compact else 42
    name_y, name_size = (108, 46) if compact else (135, 66)
    subtitle_y = 148 if compact else 177
    art_transform = "translate(196 -70) scale(0.54)" if compact else "translate(583 0)"
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">YILING0013 — Developer and open-source builder</title>',
        '<desc id="desc">Practical tools. Creative possibilities. AI, web, and desktop.</desc>',
        '<style>' + "".join(styles) + '</style>',
        '<defs><radialGradient id="glow"><stop stop-color="' + glow + '"/><stop offset="1" stop-color="' + background + '"/></radialGradient>',
        f'<clipPath id="clip"><rect width="{width}" height="{height}" rx="18"/></clipPath></defs>',
        f'<g clip-path="url(#clip)"><rect width="{width}" height="{height}" fill="{background}"/>',
        f'<g transform="{art_transform}" fill="none">',
        '<circle cx="211" cy="132" r="188" fill="url(#glow)"/>',
    ]
    # 以有序的点阵和流线表现创作工具的精确感，避免抢过标题。
    for row in range(7):
        for column in range(10):
            svg.append(f'<circle cx="{64 + column * 28}" cy="{43 + row * 29}" r="1" fill="{accent}" opacity="0.18"/>')
    for index in range(8):
        offset = index * 13
        svg.append(
            f'<path d="M 20,{204 + offset} C 103,{212 + offset} 117,{93 + offset} 191,{96 + offset} '
            f'S 292,{182 + offset} 364,{48 + offset}" stroke="{accent}" '
            f'stroke-width="{1.6 if index == 3 else 1}" opacity="{0.78 if index == 3 else 0.17 + index * 0.035:.3f}"/>'
        )
    svg.extend([
        f'<circle cx="191" cy="135" r="4" fill="{background}" stroke="{accent}" stroke-width="1.5"/>',
        '</g>',
        '<g font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">',
        f'<text x="{x}" y="47" fill="{accent}" font-size="11" font-weight="600" letter-spacing="2.3">DEVELOPER / OPEN SOURCE</text>',
        f'<text x="{x - 2}" y="{name_y}" fill="{text}" font-size="{name_size}" font-weight="600" letter-spacing="-2.5">YILING0013</text>',
        f'<text x="{x}" y="{subtitle_y}" fill="{muted}" font-size="{17 if compact else 19}">Practical tools. Creative possibilities.</text>',
        f'<path d="M {x},{height - 51} h 27" stroke="{accent}" stroke-width="2"/>',
        f'<text x="{x + 39}" y="{height - 47}" fill="{muted}" font-size="11" letter-spacing="1.6">AI / WEB / DESKTOP</text>',
        '</g></g>',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="17.5" fill="none" stroke="{border}"/>',
        '</svg>',
    ])
    return "\n".join(svg) + "\n"


if __name__ == "__main__":
    assets = Path(__file__).resolve().parents[1] / "assets"
    # GitHub 会改写带主题条件的 picture source；宽度条件单独保留，主题放进 SVG。
    for compact in (False, True):
        suffix = "-mobile" if compact else ""
        (assets / f"header{suffix}.svg").write_text(
            render_header(compact), encoding="utf-8", newline="\n"
        )

    icons = {
        "book": '<path d="M12 9h8a4 4 0 0 1 4 4v23a7 7 0 0 0-6-3h-6V9Z M36 9h-8a4 4 0 0 0-4 4v23a7 7 0 0 1 6-3h6V9Z"/>',
        "folder": '<path d="M8 16v-5h13l4 5h15v21H8V16Z"/><path d="M8 18h32 M26 25l2 3 4 .5-3 2.5 1 4-4-2-3 2 .5-4-2.5-2.5 4-.5Z"/>',
        "keyboard": '<rect x="7" y="12" width="34" height="24" rx="4"/><path d="M13 19h2m6 0h2m6 0h2m5 0h1M13 25h2m6 0h2m6 0h2m5 0h1M17 31h15"/>',
        "image": '<rect x="9" y="9" width="30" height="30" rx="4"/><circle cx="29" cy="18" r="3"/><path d="m10 33 10-11 8 9 4-4 7 8"/>',
    }
    icon_dir = assets / "icons"
    icon_dir.mkdir(exist_ok=True)
    for name, drawing in icons.items():
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 48 48">'
            '<rect width="48" height="48" rx="12" fill="#dcf1e7"/>'
            '<g fill="none" stroke="#216c56" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
            + drawing + '</g></svg>\n'
        )
        (icon_dir / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")

    stack_dir = assets / "stack"
    stack_dir.mkdir(exist_ok=True)
    for name, label, width in [
        ("python", "Python", 83), ("typescript", "TypeScript", 108),
        ("csharp-cpp", "C# / C++", 100), ("react", "React", 76),
        ("nextjs", "Next.js", 88), ("flask", "Flask", 74),
    ]:
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="28" role="img" aria-label="{label}">'
            f'<rect x="0.5" y="0.5" width="{width - 1}" height="27" rx="7" fill="#18342e" stroke="#2a5044"/>'
            '<circle cx="13" cy="14" r="2.5" fill="#78cda9"/>'
            f'<text x="23" y="18" fill="#dcf3e6" font-family="Segoe UI, sans-serif" font-size="12">{label}</text></svg>\n'
        )
        (stack_dir / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    print("Generated two adaptive headers, four project icons, and six technology badges.")
