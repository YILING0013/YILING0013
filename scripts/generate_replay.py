"""保留人物原始 SVG 图层，生成 52 秒绘制演示和可离线操作的过程播放器。"""

import argparse
import copy
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
SHAPES = {"path", "ellipse", "circle", "rect", "line", "polyline", "polygon"}
STAGES = [(0, "构图"), (5, "轮廓"), (14, "底色"), (23, "阴影"), (32, "五官"), (41, "细节"), (48, "成稿")]


def copy_layers(source: ET.Element, prefix: str) -> ET.Element:
    """
    原样复制绘画层级，并为副本的 ID 加前缀，避免多层回放产生重名。

    Args:
        source: 原始 SVG 根节点。
        prefix: 副本使用的类名和 ID 前缀。

    Returns:
        保留顺序、变换和原始呈现属性的 SVG 分组。
    """
    group = ET.Element(f"{{{NS}}}g", {"class": prefix})
    for child in source:
        if child.tag.split("}")[-1] not in {"title", "desc", "defs", "metadata", "style"}:
            group.append(copy.deepcopy(child))
    ids = {element.attrib["id"]: f'{prefix}-{element.attrib["id"]}' for element in group.iter() if "id" in element.attrib}
    for element in group.iter():
        for name, value in list(element.attrib.items()):
            if name == "id":
                element.set(name, ids[value])
            else:
                for old, new in ids.items():
                    value = value.replace(f"url(#{old})", f"url(#{new})")
                    if name.split("}")[-1] == "href" and value == f"#{old}":
                        value = f"#{new}"
                element.set(name, value)
    return group


def frame(seconds: float, declarations: str) -> str:
    """
    将真实秒数换算为统一 52 秒时间轴上的 CSS 关键帧。

    Args:
        seconds: 该关键帧所处秒数。
        declarations: 该时刻的 SVG 呈现属性。

    Returns:
        一条可直接放入 @keyframes 的 CSS 片段。
    """
    return f"{seconds / 52 * 100:.5f}%{{{declarations}}}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html-output", type=Path, default=ROOT / "outputs" / "furina-process.html", help="离线播放器保存路径")
    args = parser.parse_args()
    source = ET.parse(ROOT / "assets" / "furina.svg").getroot()
    viewbox = source.attrib["viewBox"]
    _, _, width, height = map(float, viewbox.replace(",", " ").split())
    # 生成物必须完全离线；发现位图或外部资源时直接报错，不静默删掉人物内容。
    for element in source.iter():
        if element.tag.split("}")[-1] in {"script", "image", "foreignObject"}:
            raise ValueError("人物源图包含脚本、位图或 HTML，不能生成纯 SVG 回放。")
        if any(name.split("}")[-1] == "href" and not value.startswith("#") for name, value in element.attrib.items()):
            raise ValueError("人物源图含外部资源引用，不能生成离线回放。")

    parents = {child: parent for parent in source.iter() for child in parent}
    sequence = []
    group_counts = Counter()
    for element in source.iter():
        tag = element.tag.split("}")[-1]
        if tag not in SHAPES:
            continue
        ancestors, cursor = [], element
        while cursor is not source:
            ancestors.append(cursor)
            cursor = parents[cursor]
        if any(item.tag.split("}")[-1] == "defs" for item in ancestors):
            continue
        semantic = next((item.attrib["id"] for item in ancestors if item.tag.endswith("}g") and item.attrib.get("id", "").startswith("furina-")), "furina-body")
        index = group_counts[semantic]
        group_counts[semantic] += 1
        inherited = {}
        for ancestor in reversed(ancestors):
            inherited.update({name: value for name, value in ancestor.attrib.items() if name in {"fill", "stroke", "fill-opacity"}})
        fill = inherited.get("fill", "black")
        stroke = inherited.get("stroke", "none")
        # 阶段来自人物的真实语义图层；只是演示顺序，不冒充原作者的绘制录像。
        if "face" in semantic:
            stage = "base" if index == 0 else "shadow" if index <= 3 else "face"
        elif "collar" in semantic:
            stage = "base" if index in {0, 3, 5} else "shadow" if index == 4 else "detail"
        elif fill == "none" or fill in {"#e8d6b4", "#dac9ab", "#e0d1b0", "#e3d5ab"}:
            stage = "detail"
        elif stroke == "none" or ("hair" in semantic and fill not in {"#fffefe", "#fafcfd", "#f9fcfd", "#fcfdfd", "#fdfefe", "#fafdfd"}) or ("dress" in semantic and fill in {"#6d8cba", "#6688b7"}):
            stage = "shadow"
        else:
            stage = "base"
        sequence.append({"group": semantic, "index": index, "stage": stage, "opacity": element.attrib.get("opacity", "1"), "fill_opacity": inherited.get("fill-opacity", "1")})

    replay = ET.Element(f"{{{NS}}}svg", {
        "width": f"{width:g}", "height": f"{height:g}", "viewBox": viewbox,
        "role": "img", "aria-labelledby": "replay-title replay-desc", "class": "replay-root",
    })
    ET.SubElement(replay, f"{{{NS}}}title", {"id": "replay-title"}).text = "芙宁娜 · SVG 绘制过程"
    ET.SubElement(replay, f"{{{NS}}}desc", {"id": "replay-desc"}).text = "52 秒分阶段演示：构图、轮廓、底色、阴影、五官、细节、成稿。根据完成的 SVG 模拟合理绘制顺序，并非原作者的实时绘画录像；所有路径、渐变、分组和最终遮挡均来自原始矢量图。减少动态效果模式显示成稿。"
    for child in source:
        if child.tag.split("}")[-1] in {"defs", "style"}:
            replay.append(copy.deepcopy(child))

    sketch = copy_layers(source, "replay-sketch")
    art = copy_layers(source, "replay-art")
    finished = copy_layers(source, "replay-finished")
    css = [
        ".replay-root{--replay-offset:0s;--replay-state:running;--replay-repeat:infinite}",
        ".replay-sketch,.replay-art,.replay-finished,.replay-shape,.replay-guide{animation-duration:52s;animation-timing-function:linear;animation-fill-mode:both;animation-delay:var(--replay-offset);animation-play-state:var(--replay-state);animation-iteration-count:var(--replay-repeat)}",
        ".replay-sketch{animation-name:sketch-layer}.replay-art{animation-name:art-layer}.replay-finished{animation-name:finished-layer}",
        "@keyframes sketch-layer{" + frame(0, "opacity:1") + frame(8, "opacity:1") + frame(14, "opacity:0") + frame(52, "opacity:0") + "}",
        "@keyframes art-layer{" + frame(0, "opacity:1") + frame(48, "opacity:1") + frame(48.02, "opacity:0") + frame(52, "opacity:0") + "}",
        "@keyframes finished-layer{" + frame(0, "opacity:0") + frame(48, "opacity:0") + frame(48.02, "opacity:1") + frame(52, "opacity:1") + "}",
    ]
    sketch_shapes = [item for item in sketch.iter() if item.tag.split("}")[-1] in SHAPES]
    sketch_parents = {child: parent for parent in sketch.iter() for child in parent}
    guide_index = 0
    for shape, information in zip(sketch_shapes, sequence, strict=True):
        if information["index"] != 0:
            sketch_parents[shape].remove(shape)
            continue
        shape.attrib.update({"class": "replay-guide", "fill": "none", "stroke": "#a5c7d8", "stroke-width": "2", "pathLength": "100", "stroke-dasharray": "100", "style": f"animation-name:guide-{guide_index}"})
        start = guide_index * 0.22
        css.append(f"@keyframes guide-{guide_index}{{" + frame(0, "opacity:0;stroke-dashoffset:100") + frame(start, "opacity:0;stroke-dashoffset:100") + frame(start + 0.1, "opacity:.8;stroke-dashoffset:100") + frame(start + 2.3, "opacity:.8;stroke-dashoffset:0") + frame(52, "opacity:.8;stroke-dashoffset:0") + "}")
        guide_index += 1

    stage_counts = Counter(item["stage"] for item in sequence)
    stage_positions = Counter()
    art_shapes = [item for item in art.iter() if item.tag.split("}")[-1] in SHAPES]
    for index, (shape, information) in enumerate(zip(art_shapes, sequence, strict=True)):
        stage = information["stage"]
        fraction = stage_positions[stage] / max(1, stage_counts[stage] - 1)
        stage_positions[stage] += 1
        opacity, fill_opacity = information["opacity"], information["fill_opacity"]
        shape.attrib.update({"class": "replay-shape", "pathLength": "100", "stroke-dasharray": "100", "style": shape.attrib.get("style", "") + f";animation-name:shape-{index}"})
        hidden = "opacity:0;fill-opacity:0;stroke-dashoffset:100"
        outlined = f"opacity:{opacity};fill-opacity:0;stroke-dashoffset:0"
        complete = f"opacity:{opacity};fill-opacity:{fill_opacity};stroke-dashoffset:0"
        frames = frame(0, hidden)
        if stage == "base":
            start, color_start = 5 + fraction * 6.5, 14 + fraction * 6.5
            frames += frame(start, hidden) + frame(start + 0.08, f"opacity:{opacity};fill-opacity:0;stroke-dashoffset:100")
            frames += frame(start + 2.1, outlined) + frame(color_start, outlined) + frame(color_start + 2, complete)
        else:
            start = {"shadow": 23, "face": 32, "detail": 41}[stage] + fraction * 5
            frames += frame(start, hidden) + frame(start + 0.08, f"opacity:{opacity};fill-opacity:0;stroke-dashoffset:100") + frame(start + 1.5, complete)
        css.append(f"@keyframes shape-{index}{{" + frames + frame(52, complete) + "}")
    css.append("@media(prefers-reduced-motion:reduce){svg:not(.interactive) .replay-sketch,svg:not(.interactive) .replay-art{animation:none;opacity:0}svg:not(.interactive) .replay-finished{animation:none;opacity:1}svg:not(.interactive) .replay-shape,svg:not(.interactive) .replay-guide{animation:none}}")
    ET.SubElement(replay, f"{{{NS}}}style").text = "\n".join(css)
    replay.extend([sketch, art, finished])
    svg_text = "\n".join(line.rstrip() for line in ET.tostring(replay, encoding="unicode").splitlines()) + "\n"
    svg_output = ROOT / "assets" / "furina-drawing.svg"
    svg_output.write_text(svg_text, encoding="utf-8", newline="\n")

    # 播放器用暂停的同一条 CSS 时间轴精确定位，拖动进度不会重新拼接或改变人物图层。
    replay.set("class", "replay-root interactive")
    replay.set("style", "--replay-offset:-52s;--replay-state:paused;--replay-repeat:1")
    inline_svg = ET.tostring(replay, encoding="unicode")
    buttons = "".join(f'<button type="button" class="step" data-start="{start}" aria-pressed="{str(index == 6).lower()}"><span>{index + 1:02}</span>{name}</button>' for index, (start, name) in enumerate(STAGES))
    html = r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
<title>芙宁娜 · SVG 绘制过程</title>
<style>
:root{font-family:Inter,"Segoe UI","Microsoft YaHei",sans-serif;color:#24364a;background:#f1f7fb;color-scheme:light;font-synthesis:none}
*{box-sizing:border-box}body{margin:0}button,input,select{font:inherit}button,select{touch-action:manipulation}button{cursor:pointer}button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #96c8e5;outline-offset:3px}
.page{max-width:1160px;margin:auto;padding:40px 32px 28px}.eyebrow{font-size:13px;color:#52758d;letter-spacing:.02em;margin:0 0 10px}h1{font-size:clamp(27px,3.5vw,38px);font-weight:650;letter-spacing:-.035em;margin:0 0 12px}.intro{font-size:14px;line-height:1.8;color:#647c8e;margin:0;max-width:620px}
.layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(300px,1fr);gap:24px;margin-top:27px;align-items:start}.canvas{background:#fff;border:1px solid #dbe8f2;border-radius:18px;min-height:360px;position:relative;overflow:hidden;padding:25px 12px 10px;box-shadow:0 6px 28px #36546c05}.canvas-label{position:absolute;left:22px;top:17px;font-size:11px;color:#7890a1;z-index:1}.canvas .replay-root{width:100%;height:auto;display:block;max-height:680px}.panel{background:#f9fcfe;border:1px solid #dbe8f2;border-radius:18px;padding:27px 24px}.panel-heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px}.panel-heading h2{font-size:17px;font-weight:600;margin:0}.status{font-size:12px;padding:5px 9px;border:1px solid #d8e8f2;border-radius:20px;color:#4b7894;background:#eff7fc}
.stages{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:23px}.step{border:1px solid #e0eaf1;color:#536c80;background:#fff;border-radius:10px;padding:12px 10px;text-align:left;display:flex;align-items:center;gap:9px;font-size:13px;transition:background .15s,border-color .15s}.step span{color:#8ba5b7;font-size:11px;font-variant-numeric:tabular-nums}.step[aria-pressed=true]{border-color:#82b5d3;background:#eaf5fc;color:#286c96}.step[aria-pressed=true] span{color:#508aaf}.step:hover{background:#eff7fc}
.readout{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#607c91;margin-bottom:5px}.readout output{font-variant-numeric:tabular-nums}#progress{width:100%;margin:6px 0 18px;accent-color:#3c8dbc;cursor:ew-resize;height:20px}.controls{display:flex;gap:8px;align-items:center}.control{border:1px solid #d4e4ee;border-radius:9px;background:#fff;color:#42627b;padding:10px 15px;font-size:13px}.primary{background:#3d87b2;border-color:#3d87b2;color:#fff;min-width:80px}.control:hover{filter:brightness(.97)}.speed{margin-left:auto;display:flex;align-items:center;gap:7px;color:#7890a1;font-size:12px}.speed select{border:1px solid #d4e4ee;border-radius:8px;background:#fff;color:#42627b;padding:8px 4px;font-size:12px}.note{margin:24px 0 0;border-top:1px solid #e1eaf1;padding-top:18px;font-size:12px;line-height:1.9;color:#7890a1}.note strong{font-weight:500;color:#587489}.footer{font-size:11px;line-height:1.8;color:#8aa0af;margin:20px 0 0}
@media(max-width:760px){.page{padding:25px 17px}.layout{grid-template-columns:1fr;gap:17px;margin-top:20px}.canvas{padding:29px 8px 6px;min-height:0}.canvas .replay-root{max-height:600px}.panel{padding:23px 20px}.stages{grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}.step{flex-direction:column;gap:5px;padding:11px 4px;text-align:center}.intro{font-size:13px}.footer{margin-top:16px}}
@media(prefers-reduced-motion:reduce){.step{transition:none}}
</style>
</head>
<body><main class="page">
<header><p class="eyebrow">Furina / Vector study</p><h1>芙宁娜的绘制过程</h1><p class="intro">从线稿、铺色到五官与细节，回放这张插画的完成过程。</p></header>
<div class="layout">
<section class="canvas" aria-label="芙宁娜绘制过程画布"><span class="canvas-label">SVG · 原始矢量图层</span>__INLINE_SVG__</section>
<section class="panel" aria-label="绘制回放控制">
<div class="panel-heading"><h2>绘制过程</h2><span class="status" id="stage-label" aria-live="polite">成稿</span></div>
<div class="stages" aria-label="选择绘制阶段">__STAGES__</div>
<div class="readout"><label for="progress">进度</label><output id="time" for="progress" aria-live="off">00:52 / 00:52</output></div>
<input id="progress" type="range" min="0" max="52" step="0.05" value="52" aria-label="绘制进度，单位秒" aria-valuetext="52 秒，成稿">
<div class="controls"><button type="button" id="play" class="control primary">播放</button><button type="button" id="replay" class="control">重播</button><label class="speed">倍速<select id="speed" aria-label="播放速度"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label></div>
<p class="note"><strong>这是绘制顺序演示。</strong><br>根据完成的 SVG 模拟合理的绘制过程，并非原作者的实时绘画录像。人物路径、渐变和前后遮挡来自同一份矢量成稿。</p>
</section></div>
<p class="footer">52 秒 · 7 个阶段 · 可拖动进度或点击阶段跳转 · 本文件完全离线可用</p>
</main>
<script>
const drawing=document.querySelector('.replay-root');
const progress=document.getElementById('progress');
const play=document.getElementById('play');
const time=document.getElementById('time');
const stageLabel=document.getElementById('stage-label');
const speed=document.getElementById('speed');
const steps=[...document.querySelectorAll('.step')];
let position=52,playing=false,lastFrame=0,animationFrame=0,currentStage=6;

// 所有 SVG 动画保持暂停；统一改变时间偏移，保证快进、后退与倍速共用同一幅画。
/** 根据当前秒数更新画面、进度和阶段按钮。 */
function update(){
  drawing.style.setProperty('--replay-offset',`${-position}s`);
  progress.value=position;
  time.textContent=`00:${String(Math.floor(position)).padStart(2,'0')} / 00:52`;
  const stage=steps.findLastIndex(button=>position>=Number(button.dataset.start));
  if(stage!==currentStage){
    currentStage=stage;
    steps.forEach((button,index)=>button.setAttribute('aria-pressed',String(index===stage)));
    stageLabel.textContent=steps[stage].textContent.replace(/^\d+/, '');
  }
  progress.setAttribute('aria-valuetext',`${position.toFixed(1)} 秒，${stageLabel.textContent}`);
  play.textContent=playing?'暂停':'播放';
  play.setAttribute('aria-label',playing?'暂停绘制回放':'播放绘制回放');
}

/** 按实际经过时间推进播放；now 为浏览器提供的帧时间戳，单位毫秒。 */
function tick(now){
  if(!playing)return;
  position=Math.min(52,position+(now-lastFrame)/1000*Number(speed.value));
  lastFrame=now;
  if(position===52)playing=false;
  update();
  if(playing)animationFrame=requestAnimationFrame(tick);
}

/** 停止帧循环并保留当前画面，供暂停、拖动和阶段跳转共用。 */
function pause(){
  playing=false;
  cancelAnimationFrame(animationFrame);
  update();
}

/** 从当前位置开始播放；停在成稿时自动回到起点。 */
function start(){
  if(position>=52)position=0;
  playing=true;
  lastFrame=performance.now();
  update();
  cancelAnimationFrame(animationFrame);
  animationFrame=requestAnimationFrame(tick);
}

play.addEventListener('click',()=>playing?pause():start());
document.getElementById('replay').addEventListener('click',()=>{position=0;start()});
progress.addEventListener('input',()=>{position=Number(progress.value);pause()});
steps.forEach(button=>button.addEventListener('click',()=>{position=Number(button.dataset.start);if(position===48)position=52;pause()}));
document.addEventListener('keydown',event=>{
  if(event.code==='Space'&&!['INPUT','SELECT','BUTTON'].includes(document.activeElement.tagName)){
    event.preventDefault();playing?pause():start();
  }
});
update();
</script></body></html>
'''.replace("__INLINE_SVG__", inline_svg).replace("__STAGES__", buttons)
    args.html_output.parent.mkdir(parents=True, exist_ok=True)
    args.html_output.write_text(html, encoding="utf-8", newline="\n")
    # 先验证输出 XML，再交给浏览器验证交互和视觉。
    ET.fromstring(svg_text)
    print(f"Generated {len(sequence)} animated shapes across {len(group_counts)} semantic groups; source viewBox={viewbox}.")
    print(f"SVG: {svg_output}\nOffline player: {args.html_output}")
