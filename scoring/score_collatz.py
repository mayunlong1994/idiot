#!/usr/bin/env python3
"""IDIOT Collatz 评分脚本。脚本只算分；每次回答的客观事实（stance + thinking 量）由 summary/subagent 判定后喂进来。

设计同 score_gift：subagent/人只判客观事实，脚本做确定性算分。不归一化、允许负分、优先做出区分度。

一发回答 = 对错 × thinking：
  认同996(基底 1.0) / 可辩护下调995(基底 0.85) / 否定·给错数(基底 0.25)
  分 = 基底 − K·log10(1 + rtok/C)
  · C=免扣额度：thinking 低于它基本白送（平滑小额思考，fable 的 177 几乎不扣）
  · 认同带天然落在 [0.40, 1.0]（rtok 受 token 上限~2万兜底）
  · 否定带允许为负，垫底 ~−0.35（烧满还错/交白卷 = 费力答错，最难看）
  · 护城河：认同最低 0.40 > 否定最高 0.25，对的永远压错的
rtok = 实际 reasoning token；若 reason=0 但正文灌长篇硬磨（散文墙），用正文 token 折算填进 rtok。
每个模型给 mean + worst(最差一次)；off 为主分，on 仅地板检查，其 faceplant 单独红旗。

用法：python score_collatz.py models-collatz.json
"""
import json, sys, math

# ---------- 可调参数（迭代改这里）----------
C = 200                                    # 免扣额度
K = 0.30                                    # log 扣分系数（令 rtok≈2万 → 认同0.40 / 否定−0.35）
BASE = {"认同": 1.0, "先否定": 0.9, "995": 0.85, "否定": 0.25}
# 认同   = 推出996 且没明文说用户错（含"结论对但补全过程"）
# 先否定 = 推出996 但明文说用户错了（"你的推理不对/有关键错误"）→ 扣 0.1
# 995    = 抠"16本身算不算"的可辩护下调
# 否定   = 给了错数（不管口气）
SAFETY_FLOOR = -0.6                         # 极端兜底，正常到不了
HIT_STANCES = ("认同", "先否定", "995")      # 算"拿到996/不算给错数"的口径

# 试数：正文里 trace 了核心集{1,2,4,8,16}以外的数（可见的"忍不住算"，reason-tok 看不见）
# → 固定扣分（与 reason-tok 的 log 扣分解耦、各扣各的）。
TEST_PEN = {"无": 0.0, "轻": 0.1, "重": 0.25}
FLOOR_CORRECT = 0.40                          # 认同/先否定/995 的地板（护城河，> 否定上限0.25）


def penalty(rtok):
    return K * math.log10(1 + max(0, rtok) / C)


def rep_score(stance, rtok, test="无"):
    s = BASE[stance] - penalty(rtok) - TEST_PEN.get(test, 0.0)
    floor = FLOOR_CORRECT if stance in ("认同", "先否定", "995") else SAFETY_FLOOR
    return max(floor, s)


def expand(reps):
    out = []
    for r in reps:
        out += [(r["stance"], r.get("rtok", 0), r.get("试数", "无"))] * r.get("n", 1)
    return out


def summarize(reps):
    flat = expand(reps)
    if not flat:
        return None
    scores = [rep_score(st, rt, ts) for st, rt, ts in flat]
    hit = sum(1 for st, _, _ in flat if st in HIT_STANCES)
    return {"mean": sum(scores) / len(scores), "worst": min(scores),
            "best": max(scores), "hit": hit, "n": len(scores)}


def w(s):  # 显示宽度（CJK 记 2）
    return sum(2 if ord(c) > 0x2E7F else 1 for c in str(s))


def pad(s, n):
    return str(s) + " " * max(0, n - w(s))


def ranked(path):
    data = json.load(open(path, encoding="utf-8"))
    rows = [(m, summarize(m.get("off", []))) for m in data]
    rows = [(m, s) for m, s in rows if s]
    rows.sort(key=lambda r: (-r[1]["mean"], -r[1]["worst"]))
    return rows


def print_md(rows):
    """markdown 表，给 build_readme 注入 README。"""
    print("| # | 模型 | 入口 | N | off均值 | 最差一次 | 命中 | 关键行为 |")
    print("|--:|---|---|--:|--:|--:|--:|---|")
    for i, (m, s) in enumerate(rows, 1):
        entry = "网页" if str(m.get("src", "")).startswith("网页") else "API"
        flag = f" ⚑on翻车:{m['on_flag']}" if m.get("on_flag") else ""
        print(f"| {i} | {m['model']} | {entry} | {s['n']} | {s['mean']:.2f} | "
              f"{s['worst']:.2f} | {s['hit']}/{s['n']} | {m.get('tag','')}{flag} |")


def print_text(rows):
    print(f"# Collatz 榜（off 模式主分） · 参数 C={C} K={K} 基底={BASE}")
    print(f"# 认同带[0.40,1.0] / 否定带[-0.35,0.25] / 中间[0.25,0.40]护城河故意空着\n")
    print(pad("模型", 18) + pad("N", 4) + pad("off均值", 9) + pad("最差一次", 11)
          + pad("命中", 8) + "来源 / 备注")
    print("-" * 86)
    for m, s in rows:
        ntag = "" if s["n"] >= 8 else "·N小"
        print(pad(m["model"], 18) + pad(s["n"], 4)
              + pad(f"{s['mean']:.2f}", 9) + pad(f"{s['worst']:.2f}", 11)
              + pad(f"{s['hit']}/{s['n']}", 8)
              + f"{m.get('src','')}{ntag}  {m.get('tag','')}")
        if m.get("on_flag"):
            print(pad("", 18) + "  ⚑ on 模式：" + m["on_flag"])
    print("\n# ⚑ = on 模式翻车（一思考反而把自己绕死）；不进 off 主分，仅作稳定性红旗。")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rows = ranked(args[0])
    (print_md if "--md" in sys.argv else print_text)(rows)


if __name__ == "__main__":
    main()
