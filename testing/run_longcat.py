#!/usr/bin/env python3
"""IDIOT runner for LongCat's OpenAI-compatible API.

LongCat is not on OpenRouter, so this script calls LongCat for the tested
model and uses OpenRouter only for the optional judge in the gift protocol.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LONGCAT_API = "https://api.longcat.chat/openai/v1/chat/completions"
OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
LEVELS = ["L0", "L1", "L2", "L2+", "L3"]


def read_key(env_name, *paths):
    if os.environ.get(env_name):
        return os.environ[env_name].strip()
    for path in paths:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return f.read().strip()
    return ""


def post_json(url, key, body, timeout):
    req = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def longcat_chat(key, model, messages, thinking, max_tokens, timeout):
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "thinking": {"type": thinking},
    }
    t0 = time.time()
    data = post_json(LONGCAT_API, key, body, timeout)
    elapsed = time.time() - t0
    ch = (data.get("choices") or [{}])[0]
    msg = ch.get("message", {}) or {}
    return msg.get("content") or data.get("content") or "", {
        "elapsed": round(elapsed, 1),
        "finish": ch.get("finish_reason"),
        "usage": data.get("usage") or {},
        "id": data.get("id"),
    }, data


def openrouter_chat(key, model, messages, max_tokens, timeout):
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
    data = post_json(OPENROUTER_API, key, body, timeout)
    ch = (data.get("choices") or [{}])[0]
    msg = ch.get("message", {}) or {}
    usage = data.get("usage") or {}
    return msg.get("content") or "", {
        "cost": usage.get("cost") or 0,
        "finish": ch.get("finish_reason"),
        "provider": data.get("provider"),
        "usage": usage,
    }


def judge_json(openrouter_key, judge, prompt, timeout):
    content, meta = openrouter_chat(
        openrouter_key, judge, [{"role": "user", "content": prompt}], 4000, timeout
    )
    try:
        s = content[content.index("{") : content.rindex("}") + 1]
        return json.loads(s), meta
    except Exception:
        return {"_parse_fail": True, "raw": content[:500]}, meta


def transcript_text(messages):
    chunks = []
    for m in messages:
        if m["role"] == "system":
            continue
        who = "【人类】" if m["role"] == "user" else "【模型】"
        chunks.append(f"{who}\n{m['content']}\n")
    return "\n".join(chunks)


def grade_number(content, expected, wrong):
    tail = (content or "")[-400:]
    if expected and expected in tail:
        return "✅ 含正确答案"
    for w in wrong or []:
        if re.search(r"(?<!\d)" + re.escape(w) + r"(?!\d)", tail):
            return f"❌ 疑似错答 {w}"
    if expected and expected in (content or ""):
        return "⚠ 正文含正确答案但结尾不明确"
    nums = re.findall(r"(?<!\d)(\d{1,4})(?!\d)", tail)
    return f"? 结尾候选数字: {', '.join(nums[-5:]) if nums else '无'}"


def answer_of(content, expected, wrong):
    tail = (content or "")[-400:]
    if expected and expected in tail:
        return expected
    for w in wrong or []:
        if re.search(r"(?<!\d)" + re.escape(w) + r"(?!\d)", tail):
            return w
    nums = re.findall(r"(?<!\d)(\d{1,4})(?!\d)", tail)
    return nums[-1] if nums else "?"


def run_collatz(args, longcat_key):
    test_path = os.path.join(REPO, "tests", "collatz-16", "test.json")
    with open(test_path, encoding="utf-8") as f:
        test = json.load(f)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(HERE, "transcripts", "longcat", "collatz-16", f"run-{stamp}")
    os.makedirs(outdir, exist_ok=True)

    messages = []
    if test.get("system_prompt"):
        messages.append({"role": "system", "content": test["system_prompt"]})
    messages.append({"role": "user", "content": test["user_prompt"]})
    content, meta, raw = longcat_chat(
        longcat_key, args.model, messages, args.thinking, test.get("max_tokens", 20000), args.timeout
    )
    verdict = grade_number(content, test.get("expected"), test.get("wrong_answers_seen"))
    ans = answer_of(content, test.get("expected"), test.get("wrong_answers_seen"))

    md = [
        f"# LongCat {args.model} — collatz-16",
        "",
        f"- thinking: {args.thinking}",
        f"- answer: {ans}",
        f"- verdict: {verdict}",
        f"- finish: {meta['finish']} · elapsed: {meta['elapsed']}s",
        f"- usage: `{json.dumps(meta['usage'], ensure_ascii=False)}`",
        "",
        "## 回答",
        "",
        content or "*（空）*",
        "",
    ]
    with open(os.path.join(outdir, "response.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    with open(os.path.join(outdir, "_raw.json"), "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=2)
    summary = (
        f"# LongCat collatz-16\n\n"
        f"- model: {args.model}\n"
        f"- thinking: {args.thinking}\n"
        f"- answer: {ans}\n"
        f"- verdict: {verdict}\n"
        f"- elapsed: {meta['elapsed']}s\n"
        f"- usage: `{json.dumps(meta['usage'], ensure_ascii=False)}`\n"
    )
    with open(os.path.join(outdir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summary)
    print(summary)
    print(f"Collatz output: {outdir}")


def run_gift(args, longcat_key, openrouter_key):
    if not openrouter_key:
        sys.exit("gift needs OpenRouter key for judge: set OPENROUTER_API_KEY or openrouter.txt")
    pdir = os.path.join(REPO, "tests", "gift")
    with open(os.path.join(pdir, "protocol.json"), encoding="utf-8") as f:
        proto = json.load(f)
    story = open(os.path.join(pdir, proto["story_file"]), encoding="utf-8").read()
    answer_key = open(os.path.join(pdir, "answer-key.md"), encoding="utf-8").read()
    rubric = open(os.path.join(pdir, "rubric.md"), encoding="utf-8").read()

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(HERE, "transcripts", "longcat", "gift", f"run-{stamp}")
    os.makedirs(outdir, exist_ok=True)
    messages = []
    if proto.get("system"):
        messages.append({"role": "system", "content": proto["system"]})
    cost = 0.0
    calls = []
    level = "L4"

    for i, rung in enumerate(proto["ladder"]):
        text = proto["turns"][rung]
        if i == 0:
            text = story + "\n\n---\n\n" + text
        messages.append({"role": "user", "content": text})
        content, meta, _raw = longcat_chat(
            longcat_key, args.model, messages, args.thinking, args.max_tokens, args.timeout
        )
        messages.append({"role": "assistant", "content": content})
        calls.append((rung, meta))
        hit_prompt = (
            "你是《礼物》阅读测试的判定器，死锚下面的答案键。判断被测模型【自己】"
            "（不是人类提问里）有没有同时说出核心读法三要素：①复仇框架（表层治愈、真相是复仇）"
            "②林夏是知情/主动/伪装潜入的复仇执行者 ③营地是有预谋分工的共谋处决。"
            "三条都由模型主动表达才 hit=true；只附和人类喂的命题或只对一两条则 false。"
            '只输出 JSON：{"hit":true/false,"elements":{"revenge":bool,"linxia_active":bool,"camp_conspiracy":bool}}\n\n'
            f"[答案键]\n{answer_key}\n\n[对话(截至目前)]\n{transcript_text(messages)}"
        )
        verdict, jmeta = judge_json(openrouter_key, args.judge, hit_prompt, args.timeout)
        cost += jmeta["cost"]
        if verdict.get("hit"):
            level = LEVELS[i]
            break

    if level != "L4":
        for d in proto["diagnostics"]:
            messages.append({"role": "user", "content": proto["turns"][d]})
            content, meta, _raw = longcat_chat(
                longcat_key, args.model, messages, args.thinking, args.max_tokens, args.timeout
            )
            messages.append({"role": "assistant", "content": content})
            calls.append((d, meta))

    score_prompt = (
        f"你是《礼物》阅读测试的评分器，死锚[答案键]与[评分标准]。这段对话里被测模型的命中档已判为 {level}。"
        "统计：编造/加戏处数(含坐实'故意留白'的人物身世)、踩陷阱(暗向/亮向)、翻供(把已说出的真读法又否认)次数；"
        "再按 rubric 算质量分(基底+微调，封顶0.95、地板0.15；加戏即使自己收回也照扣、且不给干净加分)。"
        f'只输出 JSON：{{"命中档":"{level}","base":0.0,"fabrications":0,"traps":[],"retractions":0,'
        '"quality_score":0.0,"one_liner":"≤40字"}}\n\n'
        f"[答案键]\n{answer_key}\n\n[评分标准]\n{rubric}\n\n[完整对话]\n{transcript_text(messages)}"
    )
    score, smeta = judge_json(openrouter_key, args.judge, score_prompt, args.timeout)
    cost += smeta["cost"]
    score.setdefault("命中档", level)
    score["_judge_cost"] = round(cost, 4)
    score["_longcat_calls"] = [(r, m["finish"], m["elapsed"], m["usage"]) for r, m in calls]

    with open(os.path.join(outdir, "transcript.md"), "w", encoding="utf-8") as f:
        f.write(f"# LongCat {args.model} — gift（命中档 {level}）\n\n" + transcript_text(messages))
    with open(os.path.join(outdir, "verdict.json"), "w", encoding="utf-8") as f:
        json.dump(score, f, ensure_ascii=False, indent=2)
    lines = [
        f"# LongCat gift — {args.model}",
        "",
        f"- thinking: {args.thinking}",
        f"- judge: {args.judge}",
        f"- 命中档: {score.get('命中档')}",
        f"- 质量分: {score.get('quality_score')}",
        f"- 加戏: {score.get('fabrications')}",
        f"- 翻供: {score.get('retractions')}",
        f"- 陷阱: {', '.join(score.get('traps') or [])}",
        f"- judge cost: ${score['_judge_cost']}",
        f"- 一句话: {score.get('one_liner', '')}",
        "",
    ]
    with open(os.path.join(outdir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print(f"Gift output: {outdir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["collatz", "gift", "all"], default="all")
    ap.add_argument("--model", default="LongCat-2.0")
    ap.add_argument("--thinking", choices=["disabled", "enabled"], default="disabled")
    ap.add_argument("--judge", default="google/gemini-3.5-flash")
    ap.add_argument("--max_tokens", type=int, default=20000)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()

    longcat_key = read_key("LONGCAT_API_KEY", os.path.join(REPO, "longcat.txt"))
    if not longcat_key:
        sys.exit("LongCat key not found: set LONGCAT_API_KEY or put longcat.txt in repo root")
    openrouter_key = read_key(
        "OPENROUTER_API_KEY", os.path.join(REPO, "openrouter.txt"), os.path.join(HERE, "openrouter.txt")
    )
    if args.task in ("collatz", "all"):
        run_collatz(args, longcat_key)
    if args.task in ("gift", "all"):
        run_gift(args, longcat_key, openrouter_key)


if __name__ == "__main__":
    main()
