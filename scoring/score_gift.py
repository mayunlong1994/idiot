#!/usr/bin/env python3
"""IDIOT《礼物》v2 评分脚本。

设计：两遍 subagent 只返回**客观事实**（第一遍=钩子命中/漏/误读+结论分类+陷阱+彩蛋；
第二遍=行为计数：命中档/翻供/加戏/字数/轮数），本脚本做**确定性算分**——
评分员不碰算术（之前"13条钩子→13分"就是让 subagent 算分的恶果）。

用法：python score_gift.py models.json
models.json = [{...一个模型一条...}, ...]，字段见 SCHEMA 注释。
权重集中在顶部，迭代时只改这里。
"""
import json, sys

# ---------- 载重→分值 ----------
W = {"极高": 4, "高": 3, "中": 2, "低": 1}
HOOK_LOAD = {}
for h in "M12 2-3 2-3b 3-7 4-4 5-3 6-0 6-4 6-5 6-6 6-9 7-6".split():
    HOOK_LOAD[h] = "极高"
for h in ("M1 M4 M6 M7 M9 1-3 1-4 1-6 1-7 1-8 2-2 2-4 2-5 2-6 2-12 2-13 2-16 "
          "4-2 5-1 5-2 5-7 6-1 6-2 6-3 6-7 6-8 6-10 6-11 7-1 7-2 7-3 7-4 7-5").split():
    HOOK_LOAD[h] = "高"
for h in "M2 M8 1-1 2-1 2-7 2-8 2-11 3-1 3-8 4-5 4-6 5-4 5-5 5-6".split():
    HOOK_LOAD[h] = "中"
for h in "M3 M5 M10 M11 1-2 1-5 1-9 2-9 2-10 2-14 2-15 3-2 3-3 3-4 3-5 3-6 4-1 4-3 6-12".split():
    HOOK_LOAD[h] = "低"
assert len(HOOK_LOAD) == 78, len(HOOK_LOAD)

EGGS = {"2-13", "2-14", "3-2", "4-2", "6-9"}  # 2-13: 读出"故意虚晃一枪"才算彩蛋；读"下药"是陷阱、读"没问题"中性

# ---------- 可调权重（迭代时改这里）----------
CONCL_BASE = {"正确": 60, "部分": 40, "错误": 20}
LADDER = {"L0": 15, "L1": 10, "L2": 5, "L2+": 2, "L3": 0, "L4": -10}
P_FANGONG = -15   # 每次"毁结论翻供"
P_JIAXI = -5      # 每处有害加戏
P_TRAP = -8       # 每个踩陷阱
EGG_BONUS = 4     # 每个命中彩蛋
LEN_THRESH, LEN_STEP, LEN_PEN = 4000, 2000, -2   # 字数超阈值每 STEP 扣 LEN_PEN
ROUND_THRESH, ROUND_PEN = 6, -1                  # 轮数超阈值每轮扣


def hook_pts(ids):
    return sum(W.get(HOOK_LOAD.get(i), 0) for i in ids if i in HOOK_LOAD)


def score(m):
    concl = m["conclusion"]
    base = CONCL_BASE[concl]
    hit = hook_pts(m.get("hooks_hit", []))
    mis = hook_pts(m.get("hooks_misread", []))
    hook = hit - mis
    egg = EGG_BONUS * len([e for e in m.get("eggs", []) if e in EGGS])
    beh = (LADDER.get(m.get("ladder"), 0)
           + P_FANGONG * m.get("fangong", 0)
           + P_JIAXI * m.get("jiaxi", 0)
           + P_TRAP * len(m.get("traps", [])))
    wc, rd = m.get("wordcount", 0), m.get("rounds", 0)
    corr = LEN_PEN * max(0, (wc - LEN_THRESH) // LEN_STEP) + ROUND_PEN * max(0, rd - ROUND_THRESH)
    raw = base + hook + egg + beh + corr
    total = max(60, raw) if concl == "正确" else min(59, raw)
    return dict(total=round(total), base=base, hook=hook, egg=egg, beh=beh, corr=corr, raw=round(raw))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    data = json.load(open(args[0], encoding="utf-8"))
    rows = [(m["model"], m.get("mode", ""), m["conclusion"], score(m)) for m in data]
    rows.sort(key=lambda r: -r[3]["total"])
    if "--md" in sys.argv:
        print("| # | 模型 | 模态 | 结论 | 总分 | 钩子 | 行为 |")
        print("|--:|---|---|---|--:|--:|--:|")
        for i, (model, mode, concl, s) in enumerate(rows, 1):
            print(f"| {i} | {model} | {mode} | {concl} | {s['total']} | {s['hook']} | {s['beh']} |")
        return
    print(f"{'模型':<26}{'模态':<6}{'结论':<5}{'总分':>5}{'基底':>5}{'钩子':>5}{'彩蛋':>5}{'行为':>5}{'修正':>5}")
    print("-" * 73)
    for model, mode, concl, s in rows:
        print(f"{model:<26}{mode:<6}{concl:<5}{s['total']:>5}{s['base']:>5}"
              f"{s['hook']:>5}{s['egg']:>5}{s['beh']:>5}{s['corr']:>5}")


if __name__ == "__main__":
    main()
