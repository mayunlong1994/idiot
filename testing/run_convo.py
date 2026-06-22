#!/usr/bin/env python3
"""IDIOT · 多轮自适应跑法（《礼物》）—— 全自动，内置 API 裁判，无需人工/subagent。

对每个模型 × 每个 rep：
  1. 发小说全文 + R0，逐级走阶梯(R0..R4)，每轮后用裁判模型判是否到达「核心读法」三要素，命中即停（记命中档）。
  2. 到位后追问诊断 D1/D2/D3（L4 未到位则跳过）。
  3. 用裁判模型按 rubric 给整段对话打质量分。
  4. 落盘 transcript + verdict，多 rep 聚合成 summary。

用法：
  py run_convo.py --model anthropic/claude-opus-4.7 --reps 3
  py run_convo.py --model openai/gpt-5.5 --judge google/gemini-3.1-pro-preview --reps 5 --provider OpenAI
裁判别用被测模型自己（避免自评）。Key 见 ../openrouter.txt 或环境变量 OPENROUTER_API_KEY。
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
API_URL = "https://openrouter.ai/api/v1/chat/completions"
LEVELS = ["L0", "L1", "L2", "L2+", "L3"]          # 对应 ladder 各级命中
BASE = {"L0": 0.90, "L1": 0.80, "L2": 0.65, "L2+": 0.65, "L3": 0.45, "L4": 0.15}


def load_key():
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"].strip()
    for p in (os.path.join(REPO, "openrouter.txt"), os.path.join(HERE, "openrouter.txt")):
        if os.path.exists(p):
            return open(p, encoding="utf-8").read().strip()
    sys.exit("找不到 API key：设环境变量 OPENROUTER_API_KEY 或在仓库根放 openrouter.txt")


def chat(key, model, msgs, reasoning="default", provider=None, max_tokens=20000, timeout=300):
    payload = {"model": model, "messages": msgs, "max_tokens": max_tokens}
    if reasoning == "off":
        payload["reasoning"] = {"enabled": False}
    elif reasoning == "on":
        payload["reasoning"] = {"enabled": True}
    if provider:
        payload["provider"] = {"order": [provider], "allow_fallbacks": False}
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode())
    ch = (data.get("choices") or [{}])[0]
    m = ch.get("message", {}) or {}
    u = data.get("usage") or {}
    return m.get("content") or "", {"cost": u.get("cost") or 0,
        "reasoning_tokens": (u.get("completion_tokens_details") or {}).get("reasoning_tokens"),
        "finish": ch.get("finish_reason"), "provider": data.get("provider")}


def judge_json(key, judge, prompt, timeout=300):
    """调裁判，强制 JSON 输出，容错解析。"""
    content, meta = chat(key, judge, [{"role": "user", "content": prompt}],
                         reasoning="default", max_tokens=4000, timeout=timeout)
    try:
        s = content[content.index("{"):content.rindex("}") + 1]
        return json.loads(s), meta
    except Exception:
        return {"_parse_fail": True, "raw": content[:500]}, meta


def transcript_text(msgs):
    out = []
    for m in msgs:
        if m["role"] == "system":
            continue
        who = "【人类】" if m["role"] == "user" else "【模型】"
        out.append(f"{who}\n{m['content']}\n")
    return "\n".join(out)


def run_rep(key, args, proto, story, answer_key, rubric, rep):
    msgs = []
    if proto.get("system"):
        msgs.append({"role": "system", "content": proto["system"]})
    cost = 0.0
    metas = []
    level = "L4"
    # ---- 阶梯：命中即停 ----
    for i, rung in enumerate(proto["ladder"]):
        text = proto["turns"][rung]
        if i == 0:
            text = story + "\n\n---\n\n" + text
        msgs.append({"role": "user", "content": text})
        content, meta = chat(key, args.model, msgs, args.reasoning, args.provider, args.max_tokens, args.timeout)
        msgs.append({"role": "assistant", "content": content})
        cost += meta["cost"]; metas.append((rung, meta))
        hp = (f"你是《礼物》阅读测试的判定器，死锚下面的答案键。判断被测模型【自己】"
              f"（不是人类提问里）有没有同时说出核心读法三要素：①复仇框架（表层治愈、真相是复仇）"
              f"②林夏是知情/主动/伪装潜入的复仇执行者 ③营地是有预谋分工的共谋处决。"
              f"三条都由模型主动表达才 hit=true；只附和人类喂的命题或只对一两条则 false。"
              f"只输出 JSON：{{\"hit\":true/false,\"elements\":{{\"revenge\":bool,\"linxia_active\":bool,\"camp_conspiracy\":bool}}}}\n\n"
              f"[答案键]\n{answer_key}\n\n[对话(截至目前)]\n{transcript_text(msgs)}")
        verdict, jmeta = judge_json(key, args.judge, hp, args.timeout)
        cost += jmeta["cost"]
        if verdict.get("hit"):
            level = LEVELS[i]
            break
    # ---- 诊断段：仅到位时问 ----
    if level != "L4":
        for d in proto["diagnostics"]:
            msgs.append({"role": "user", "content": proto["turns"][d]})
            content, meta = chat(key, args.model, msgs, args.reasoning, args.provider, args.max_tokens, args.timeout)
            msgs.append({"role": "assistant", "content": content})
            cost += meta["cost"]; metas.append((d, meta))
    # ---- 终局评分 ----
    sp = (f"你是《礼物》阅读测试的评分器，死锚[答案键]与[评分标准]。这段对话里被测模型的命中档已判为 {level}。"
          f"统计：编造/加戏处数(含坐实'故意留白'的人物身世)、踩陷阱(暗向/亮向)、翻供(把已说出的真读法又否认)次数；"
          f"再按 rubric 算质量分(基底+微调，封顶0.95、地板0.15；加戏即使自己收回也照扣、且不给干净加分)。"
          f"只输出 JSON：{{\"命中档\":\"{level}\",\"base\":0.0,\"fabrications\":0,\"traps\":[],\"retractions\":0,"
          f"\"quality_score\":0.0,\"one_liner\":\"≤40字\"}}\n\n"
          f"[答案键]\n{answer_key}\n\n[评分标准]\n{rubric}\n\n[完整对话]\n{transcript_text(msgs)}")
    score, smeta = judge_json(key, args.judge, sp, args.timeout)
    cost += smeta["cost"]
    score.setdefault("命中档", level)
    score["_cost"] = round(cost, 4)
    score["_turns"] = [(r, mt["finish"], mt["reasoning_tokens"]) for r, mt in metas]
    return msgs, level, score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--protocol", default="gift")
    ap.add_argument("--judge", default="google/gemini-3.1-pro-preview", help="裁判模型（别用被测模型自己）")
    ap.add_argument("--name", default=None, help="输出目录名，默认取 slug 末段")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--provider", default=None)
    ap.add_argument("--reasoning", default="default", choices=["default", "off", "on"])
    ap.add_argument("--max_tokens", type=int, default=20000)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()
    key = load_key()

    pdir = os.path.join(REPO, "tests", args.protocol)
    proto = json.load(open(os.path.join(pdir, "protocol.json"), encoding="utf-8"))
    story = open(os.path.join(pdir, proto["story_file"]), encoding="utf-8").read()
    answer_key = open(os.path.join(pdir, "answer-key.md"), encoding="utf-8").read()
    rubric = open(os.path.join(pdir, "rubric.md"), encoding="utf-8").read()

    short = args.name or args.model.split("/")[-1].replace(":", "_")
    outdir = os.path.join(HERE, "transcripts", args.protocol, short)
    os.makedirs(outdir, exist_ok=True)
    print(f"模型 {args.model} | 裁判 {args.judge} | reps {args.reps} | 输出 {outdir}\n")

    rows = []
    for rep in range(1, args.reps + 1):
        try:
            msgs, level, score = run_rep(key, args, proto, story, answer_key, rubric, rep)
        except Exception as e:
            print(f"  rep{rep}  [ERROR] {e}")
            rows.append({"rep": rep, "error": str(e)})
            continue
        open(os.path.join(outdir, f"rep{rep}-transcript.md"), "w", encoding="utf-8").write(
            f"# {args.model} — rep{rep}（命中档 {level}）\n\n" + transcript_text(msgs))
        open(os.path.join(outdir, f"rep{rep}-verdict.json"), "w", encoding="utf-8").write(
            json.dumps(score, ensure_ascii=False, indent=1))
        rows.append({"rep": rep, **score})
        print(f"  rep{rep}  命中档={level}  质量分={score.get('quality_score')}  "
              f"加戏={score.get('fabrications')} 翻供={score.get('retractions')} 陷阱={score.get('traps')}  "
              f"${score.get('_cost')}")

    # 聚合
    qs = [r["quality_score"] for r in rows if isinstance(r.get("quality_score"), (int, float))]
    levels = [r.get("命中档") for r in rows if r.get("命中档")]
    total = round(sum(r.get("_cost", 0) for r in rows), 4)
    mean = round(sum(qs) / len(qs), 3) if qs else None
    lines = [f"# 《礼物》结果 — {args.model}", "",
             f"裁判 {args.judge} · reps {args.reps} · {datetime.now():%Y-%m-%d %H:%M}", "",
             f"- 命中档分布：{levels}",
             f"- 质量分：均值 {mean}，范围 {min(qs) if qs else '-'}~{max(qs) if qs else '-'}",
             f"- 总花费：${total}", "",
             "| rep | 命中档 | 质量分 | 加戏 | 翻供 | 陷阱 | 一句话 |",
             "|--:|---|--:|--:|--:|---|---|"]
    for r in rows:
        if r.get("error"):
            lines.append(f"| {r['rep']} | ERR | | | | | {r['error']} |")
        else:
            lines.append(f"| {r['rep']} | {r.get('命中档')} | {r.get('quality_score')} | "
                         f"{r.get('fabrications')} | {r.get('retractions')} | {','.join(r.get('traps') or [])} | {r.get('one_liner','')} |")
    summary = "\n".join(lines) + "\n"
    open(os.path.join(outdir, "summary.md"), "w", encoding="utf-8").write(summary)
    print("\n" + summary)


if __name__ == "__main__":
    main()
