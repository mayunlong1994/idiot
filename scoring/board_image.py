#!/usr/bin/env python3
"""把榜单生成 SVG 海报（自包含，可直接用浏览器打开 / 转图）。模型更新后重跑即可。

用法：
  python scoring/board_image.py collatz                      # Collatz 榜（普通）
  python scoring/board_image.py gift                         # 《礼物》榜（网页 chat + API 合并）
  python scoring/board_image.py collatz --highlight "GLM-5.2,GLM智谱"   # 高亮某些模型（子串匹配，可选）
  python scoring/board_image.py gift --out my.svg            # 指定输出路径
默认输出到 scoring/board-<test>.svg。

转 PNG/JPG：用浏览器打开 SVG 另存为图片；或 `pip install cairosvg && cairosvg board-x.svg -o board-x.jpg`。
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FOOT = "github.com/mayunlong1994/idiot"
STYLE = """<style>
text{font-family:'Microsoft YaHei','PingFang SC','Noto Sans CJK SC','Segoe UI',sans-serif}
.th{fill:#1A1A1A}.t{fill:#2C2C2A}.ts{fill:#6B6B6B}
.win{fill:#27500A}.lose{fill:#791F1F}
.c-green rect{fill:#EAF3DE}.c-green text{fill:#27500A}
.c-teal rect{fill:#E1F5EE}.c-teal text{fill:#085041}
.c-amber rect{fill:#FAEEDA}.c-amber text{fill:#633806}
.c-coral rect{fill:#FAECE7}.c-coral text{fill:#712B13}
.c-red rect{fill:#FCEBEB}.c-red text{fill:#791F1F}
.hl{fill:#EEEDFE}.divider{stroke:#111;stroke-opacity:0.18}
</style>"""


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def head(W, H, title, subs):
    o = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" role="img">',
         f'<title>{esc(title)}</title>', STYLE, f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
         f'<text x="24" y="40" class="th" style="font-size:23px">{esc(title)}</text>']
    for k, s in enumerate(subs):
        o.append(f'<text x="24" y="{66 + k*20}" class="ts" style="font-size:{13 if k == 0 else 12}px">{esc(s)}</text>')
    return o


def hit(name, terms):
    return any(term and term in name for term in terms)


def collatz_svg(hl):
    from score_collatz import ranked
    rows = ranked(os.path.join(HERE, "models-collatz.json"))
    NOTE = {
     "Qwen3.7 Max": "零思考 · 8/8 稳", "Grok 4.3": "2.1 秒秒答", "Fable-5": "纯结构 · 几乎没想",
     "GPT-5.5": "强,偶发 1 次 920", "GPT-5.3 Codex": "强,1 次 626", "Opus 4.7": "对,但先说你错",
     "DeepSeek V4 Pro": "抠 16 边界 → 995", "Sonnet 4.6": "先说你错 + 试数",
     "豆包 Seed 1.6": "先说你错 + 试数", "MiMo v2.5 Pro": "先否定;开推理翻车",
     "GLM-5.2": "off 不稳 5/8", "DeepSeek V4 Flash": "对,却试了 7 个数",
     "豆包 Seed 1.6 Flash": "先否定 + 成片枚举", "Kimi K2.6": "先否定 + 成片试数",
     "Gemini 3.1 Pro": "关不掉推理", "Gemini 3.5 Flash": "关不掉推理", "MiniMax M2.7": "思维链成片枚举",
     "GPT-5.4": "没题感 2/9", "混元 hy3": "读反题;开推理翻车", "Claude Haiku 4.5": "假装跑代码报 990",
     "GLM 5.1": "自创理论硬算 → 668", "Gemini(web)": "只想了几秒", "Opus(web)": "先说你判断错了",
     "Sonnet(web)": "≈opus,先说你错", "Kimi(web)": "先否定后自纠", "mimo(web)": "开了超长思考",
     "DeepSeek(web)": "超长思考 + 试数", "豆包(web)": "逻辑说反,不给数", "Grok(web)": "不算,只敢估",
     "千问(web)": "→ 14", "GPT-5.4(web)": "读反题 → 336", "混元3(web)": "→ 23",
     "GLM智谱新站(web)": "想通了却改成 999", "GLM5.1(web)": "手画反推树 → 39",
     "GLM智谱清言(web)": "读反题 · 手算 4000 行 → 28",
    }

    def cls(s):
        return ("c-green" if s >= 0.85 else "c-teal" if s >= 0.55 else
                "c-amber" if s >= 0.25 else "c-coral" if s >= 0 else "c-red")

    W, RH, TOP, FT = 680, 30, 84, 44
    H = TOP + 30 + len(rows) * RH + FT
    o = head(W, H, "IDIOT · Collatz 榜",
             ["一道一句话能秒的题，测大模型敢不敢不思考 · 分越高越好"])
    for x, t, a in [(20, "#", "start"), (46, "模型", "start"), (300, "入口", "middle"),
                    (340, "均值", "middle"), (392, "最差", "middle"), (430, "一句话", "start")]:
        o.append(f'<text x="{x}" y="{TOP+20}" class="ts" text-anchor="{a}" style="font-size:12px">{t}</text>')
    o.append(f'<line x1="20" y1="{TOP+28}" x2="{W-16}" y2="{TOP+28}" class="divider"/>')
    y = TOP + 30
    for i, (m, s) in enumerate(rows, 1):
        name, cy = m["model"], y + RH / 2
        entry = "网页" if str(m.get("src", "")).startswith("网页") else "API"
        h = hit(name, hl)
        if h:
            o.append(f'<rect x="12" y="{y+2}" width="{W-26}" height="{RH-4}" rx="6" class="hl"/>')
            o.append(f'<rect x="12" y="{y+2}" width="4" height="{RH-4}" fill="#7F77DD"/>')
        o.append(f'<text x="34" y="{cy+4}" class="ts" text-anchor="end" style="font-size:12px">{i}</text>')
        o.append(f'<text x="46" y="{cy+4}" class="t" style="font-size:13px;font-weight:{500 if h else 400}">{esc(name)}</text>')
        o.append(f'<text x="300" y="{cy+4}" class="ts" text-anchor="middle" style="font-size:11px">{entry}</text>')
        o.append(f'<g class="{cls(s["mean"])}"><rect x="320" y="{cy-10}" width="42" height="20" rx="5"/>'
                 f'<text x="341" y="{cy+4}" text-anchor="middle" style="font-size:12px">{s["mean"]:.2f}</text></g>')
        o.append(f'<text x="392" y="{cy+4}" class="ts" text-anchor="middle" style="font-size:12px">{s["worst"]:.2f}</text>')
        o.append(f'<text x="430" y="{cy+4}" class="t" style="font-size:12px">{esc(NOTE.get(name, ""))}</text>')
        y += RH
    o.append(f'<text x="24" y="{H-16}" class="ts" style="font-size:12px">{FOOT}</text></svg>')
    return "\n".join(o)


def gift_svg(hl):
    from score_gift import score
    api = json.load(open(os.path.join(HERE, "models_api.json"), encoding="utf-8"))
    chat = json.load(open(os.path.join(HERE, "models_chat.json"), encoding="utf-8"))
    rows = sorted(((m["model"], m.get("mode", "api"), m["conclusion"], score(m)) for m in api + chat),
                  key=lambda r: -r[3]["total"])
    NOTE = {
     ("Fable-5", "api"): "断档第一 · R0 自达", ("GPT-5.5", "api"): "R0 自达 · 零翻供",
     ("Gemini 3.5 Flash", "api"): "又快又准 · 微加戏", ("Qwen3.7 Max", "api"): "R0 自达 · 干净",
     ("Opus 4.7", "api"): "钩子多,翻供 + 加戏", ("GLM-5.2", "api"): "正确但靠后(钩子修正→117)",
     ("DeepSeek V4 Flash", "api"): "挖 118 钩子,结论没站住", ("Sonnet 4.6", "api"): "钩子多,翻供",
     ("MiMo v2.5 Pro", "api"): "骑墙 · 洗白真凶", ("DeepSeek V4 Pro", "api"): "渐进卷入 · 飘",
     ("Grok 4.3", "api"): "读反 · 林夏成猎物", ("混元 hy3", "api"): "看见了死活洗白", ("豆包", "api"): "读反极性",
     ("Fable-5", "chat"): "L0 自达 · 干净", ("DeepSeek V4 Flash", "chat"): "一次'再想想'就全达",
     ("GLM-5.2 智谱清言", "chat"): "旧站读对了", ("Gemini", "chat"): "L0 · 漏斗比喻",
     ("Opus 4.7", "chat"): "钩子多但 L3 + 翻供", ("豆包", "chat"): "L2 · 读对",
     ("MiMo v2.5 Pro", "chat"): "钩子最多却骑墙", ("GPT-5.5", "chat"): "提问被喂答案,失分",
     ("Grok 4.3", "chat"): "L4", ("Qwen3.7 Max", "chat"): "L4", ("DeepSeek V4 Pro", "chat"): "L1 但仅部分",
     ("Sonnet 4.6", "chat"): "L4 · 翻供", ("GLM-5.2 智谱新站", "chat"): "读反极性 · 程野无辜",
     ("混元 hy3", "chat"): "死活洗白 · 垫底",
    }
    CC = {"正确": "c-green", "部分": "c-amber", "错误": "c-red"}

    W, RH, TOP, FT = 680, 32, 100, 44
    H = TOP + 32 + len(rows) * RH + FT
    o = head(W, H, "IDIOT ·《礼物》榜",
             ["表层治愈、真相复仇的短篇,测不被推 / 不加戏 / 看穿并串线索",
              "结论错就封死 59 分(挖再多线索也没用) · 网页 chat 与 API 合并排"])
    for x, t, a in [(20, "#", "start"), (46, "模型", "start"), (250, "入口", "middle"),
                    (295, "结论", "middle"), (360, "总分", "end"), (374, "一句话", "start")]:
        o.append(f'<text x="{x}" y="{TOP+22}" class="ts" text-anchor="{a}" style="font-size:12px">{t}</text>')
    o.append(f'<line x1="20" y1="{TOP+30}" x2="{W-16}" y2="{TOP+30}" class="divider"/>')
    y = TOP + 32
    for i, (name, mode, concl, s) in enumerate(rows, 1):
        cy = y + RH / 2
        entry = "网页" if mode == "chat" else "API"
        h = hit(name, hl)
        if h:
            o.append(f'<rect x="12" y="{y+3}" width="{W-26}" height="{RH-6}" rx="6" class="hl"/>')
            o.append(f'<rect x="12" y="{y+3}" width="4" height="{RH-6}" fill="#7F77DD"/>')
        o.append(f'<text x="34" y="{cy+4}" class="ts" text-anchor="end" style="font-size:12px">{i}</text>')
        o.append(f'<text x="46" y="{cy+4}" class="t" style="font-size:13px;font-weight:{500 if h else 400}">{esc(name)}</text>')
        o.append(f'<text x="250" y="{cy+4}" class="ts" text-anchor="middle" style="font-size:11px">{entry}</text>')
        o.append(f'<g class="{CC[concl]}"><rect x="271" y="{cy-9}" width="48" height="18" rx="5"/>'
                 f'<text x="295" y="{cy+4}" text-anchor="middle" style="font-size:11px">{concl}</text></g>')
        o.append(f'<text x="360" y="{cy+5}" class="{"win" if s["total"]>=60 else "lose"}" text-anchor="end" '
                 f'style="font-size:15px;font-weight:500">{s["total"]}</text>')
        o.append(f'<text x="374" y="{cy+4}" class="t" style="font-size:12px">{esc(NOTE.get((name, mode), ""))}</text>')
        y += RH
    o.append(f'<text x="24" y="{H-16}" class="ts" style="font-size:12px">{FOOT}</text></svg>')
    return "\n".join(o)


def main():
    a = sys.argv[1:]
    which = next((x for x in a if not x.startswith("--")), "collatz")
    hl = []
    if "--highlight" in a:
        hl = [t.strip() for t in a[a.index("--highlight") + 1].split(",") if t.strip()]
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(HERE, f"board-{which}.svg")
    svg = gift_svg(hl) if which == "gift" else collatz_svg(hl)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"已写 {out}（{len(hl)} 个高亮）")


if __name__ == "__main__":
    main()
