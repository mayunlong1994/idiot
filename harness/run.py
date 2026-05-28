#!/usr/bin/env python3
"""OpenRouter 模型测评跑分器（内容与脚本解耦）。

用法:
    py run.py --test collatz-16
    py run.py --test collatz-16 --modes off          # 只跑禁推理组
    py run.py --test collatz-16 --models models.json --workers 6

约定:
    models.json         待测模型名单 [{name, slug}, ...]
    tests/<id>.json     题目 {id,title,system_prompt,user_prompt,reasoning_modes,...}
    results/<id>/run-<时间戳>/   输出目录（每模型每模式一个 .md + 原始 jsonl + summary）

Key 读取顺序: 环境变量 OPENROUTER_API_KEY  ->  ../openrouter.txt  ->  ./openrouter.txt
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def load_key():
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"].strip()
    for p in (os.path.join(HERE, os.pardir, "openrouter.txt"),
              os.path.join(HERE, "openrouter.txt")):
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return f.read().strip()
    sys.exit("找不到 API key：设环境变量 OPENROUTER_API_KEY 或放一个 openrouter.txt")


def sanitize(slug):
    return slug.replace("/", "__").replace(":", "_")


def call(key, model, system_prompt, user_prompt, mode, temperature, max_tokens, timeout):
    """单次调用。mode: 'off'=禁推理, 'on'=开推理, 'default'=不传 reasoning 参数。"""
    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.append({"role": "user", "content": user_prompt})
    payload = {"model": model, "messages": msgs, "max_tokens": max_tokens}
    if temperature is not None:
        payload["temperature"] = temperature
    if mode == "off":
        payload["reasoning"] = {"enabled": False}
    elif mode == "on":
        payload["reasoning"] = {"enabled": True}

    def _post(body):
        req = urllib.request.Request(
            API_URL, data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://localhost/bench",
                     "X-Title": "model-bench"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    t0 = time.time()
    try:
        data = _post(payload)
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "ignore")
        # reasoning 参数不被支持时，去掉再试一次
        if e.code == 400 and "reasoning" in payload and "reasoning" in err.lower():
            payload.pop("reasoning", None)
            try:
                data = _post(payload)
                data["_note"] = "reasoning 参数被拒，已去掉重试（该模型可能不支持开关推理）"
            except Exception as e2:
                return {"error": f"HTTP {e.code} then {e2}", "raw_error": err[:500], "elapsed": time.time() - t0}
        else:
            return {"error": f"HTTP {e.code}", "raw_error": err[:500], "elapsed": time.time() - t0}
    except Exception as e:
        return {"error": str(e), "elapsed": time.time() - t0}

    data["elapsed"] = time.time() - t0
    return data


def extract(data):
    """从响应里取出 content / reasoning / 元信息。"""
    out = {"content": "", "reasoning": "", "finish": "", "tokens": {}, "cost": None,
           "provider": data.get("provider"), "elapsed": round(data.get("elapsed", 0), 1),
           "note": data.get("_note", "")}
    ch = (data.get("choices") or [{}])[0]
    msg = ch.get("message", {}) or {}
    out["content"] = msg.get("content") or ""
    out["reasoning"] = msg.get("reasoning") or ""
    out["finish"] = ch.get("finish_reason", "")
    u = data.get("usage") or {}
    out["tokens"] = {"prompt": u.get("prompt_tokens"), "completion": u.get("completion_tokens"),
                     "reasoning": (u.get("completion_tokens_details") or {}).get("reasoning_tokens")}
    out["cost"] = u.get("cost")
    return out


def grade(content, expected, wrong):
    """轻量判定：优先看结尾的最终答案区，避免把用户引文里的数字当成模型答案。仍需人工核对。"""
    txt = content or ""
    tail = txt[-400:]
    if expected and expected in tail:
        return "✅ 含正确答案"
    for w in (wrong or []):
        if re.search(r"(?<!\d)" + re.escape(w) + r"(?!\d)", tail):
            return f"❌ 疑似错答 {w}"
    if expected and expected in txt:
        return "⚠ 正文含正确答案但结尾不明确"
    nums = re.findall(r"(?<!\d)(\d{1,4})(?!\d)", tail)
    return f"? 结尾候选数字: {', '.join(nums[-5:]) if nums else '无'}"


def answer_of(content, expected, wrong):
    """提取这次回答最可能的最终数字，用于多次重复的稳定性聚合。"""
    txt = content or ""
    tail = txt[-400:]
    if expected and expected in tail:
        return expected
    for w in (wrong or []):
        if re.search(r"(?<!\d)" + re.escape(w) + r"(?!\d)", tail):
            return w
    nums = re.findall(r"(?<!\d)(\d{1,4})(?!\d)", tail)
    return nums[-1] if nums else "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True, help="tests/<id>.json 里的 id")
    ap.add_argument("--models", default=os.path.join(HERE, "models.json"))
    ap.add_argument("--modes", default=None, help="逗号分隔，覆盖题目里的 reasoning_modes，如 off 或 off,on")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--reps", type=int, default=1, help="每个 模型×模式 重复几次，用于看稳定性")
    args = ap.parse_args()

    key = load_key()
    with open(os.path.join(HERE, os.pardir, "tests", args.test, "test.json"), encoding="utf-8") as f:
        test = json.load(f)
    with open(args.models, encoding="utf-8") as f:
        models = json.load(f)

    modes = args.modes.split(",") if args.modes else test.get("reasoning_modes", ["default"])
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = os.path.join(HERE, os.pardir, "results", test["id"], f"run-{stamp}")
    os.makedirs(outdir, exist_ok=True)

    jobs = [(m, mode, r) for m in models for mode in modes for r in range(args.reps)]
    print(f"题目: {test['title']}  |  模型 {len(models)} × 模式 {modes} × 重复 {args.reps} = {len(jobs)} 次调用")
    print(f"输出: {outdir}\n")

    rawf = open(os.path.join(outdir, "_raw.jsonl"), "w", encoding="utf-8")
    rows = []

    def work(m, mode, r):
        data = call(key, m["slug"], test.get("system_prompt", ""), test["user_prompt"],
                    mode, test.get("temperature"), test.get("max_tokens", 8000), args.timeout)
        return m, mode, r, data

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(work, m, mode, r) for m, mode, r in jobs]
        for fut in as_completed(futs):
            m, mode, r, data = fut.result()
            suffix = f"__r{r + 1}" if args.reps > 1 else ""
            base = f"{sanitize(m['slug'])}__{mode}{suffix}"
            rawf.write(json.dumps({"model": m["slug"], "mode": mode, "rep": r + 1, "response": data}, ensure_ascii=False) + "\n")
            if "error" in data:
                print(f"  [ERR ] {m['name']:<22} {mode:<7} r{r + 1}  {data['error']}")
                rows.append((m, mode, r, None, data, "ERR"))
                with open(os.path.join(outdir, base + ".md"), "w", encoding="utf-8") as f:
                    f.write(f"# {m['name']} ({m['slug']}) — {mode} r{r + 1}\n\n**错误**: {data['error']}\n\n```\n{data.get('raw_error','')}\n```\n")
                continue
            e = extract(data)
            verdict = grade(e["content"], test.get("expected"), test.get("wrong_answers_seen"))
            ans = answer_of(e["content"], test.get("expected"), test.get("wrong_answers_seen"))
            rows.append((m, mode, r, e, verdict, ans))
            print(f"  [ok  ] {m['name']:<22} {mode:<7} r{r + 1}  ans={ans:<5} {verdict}  ({e['elapsed']}s, r-tok {e['tokens'].get('reasoning')})")
            with open(os.path.join(outdir, base + ".md"), "w", encoding="utf-8") as f:
                f.write(f"# {m['name']}  `{m['slug']}`\n\n")
                f.write(f"- 模式: **{mode}**  ·  rep: {r + 1}  ·  判定: {verdict}  ·  finish: {e['finish']}\n")
                f.write(f"- provider: {e['provider']}  ·  用时 {e['elapsed']}s  ·  tokens {e['tokens']}  ·  cost ${e['cost']}\n")
                if e["note"]:
                    f.write(f"- 注: {e['note']}\n")
                f.write("\n## 回答\n\n" + (e["content"] or "*（空）*") + "\n")
                if e["reasoning"]:
                    f.write("\n<details><summary>思维链 reasoning</summary>\n\n" + e["reasoning"] + "\n\n</details>\n")
    rawf.close()

    # summary
    from collections import Counter
    order = {m["slug"]: i for i, m in enumerate(models)}
    modeorder = {mode: i for i, mode in enumerate(modes)}
    rows.sort(key=lambda x: (order.get(x[0]["slug"], 99), modeorder.get(x[1], 99), x[2]))
    lines = [f"# {test['title']} — 结果汇总", "",
             f"运行: {stamp}  ·  正确答案: **{test.get('expected')}**  ·  重复 {args.reps} 次", ""]

    if args.reps > 1:
        # 稳定性聚合：每个 模型×模式 的答案分布
        lines += ["## 稳定性（每个 模型×模式 的答案分布）", "",
                  "| 模型 | 模式 | 命中正确 | 答案分布（值×次数） |", "|---|---|--:|---|"]
        agg = {}
        for m, mode, r, e, verdict, ans in rows:
            agg.setdefault((order.get(m["slug"], 99), m["name"], mode), []).append(ans)
        for key in sorted(agg):
            _, name, mode = key
            anslist = agg[key]
            cnt = Counter(anslist)
            hit = sum(1 for a in anslist if a == str(test.get("expected")))
            dist = "，".join(f"{v}×{n}" for v, n in cnt.most_common())
            lines.append(f"| {name} | {mode} | {hit}/{len(anslist)} | {dist} |")
        lines.append("")

    lines += ["## 逐次明细", "",
              "| 模型 | 模式 | rep | 答案 | 判定 | finish | 用时 | reason-tok | cost | provider |",
              "|---|---|--:|---|---|---|--:|--:|--:|---|"]
    for m, mode, r, e, verdict, ans in rows:
        if e is None:
            lines.append(f"| {m['name']} | {mode} | {r + 1} | ERR | {verdict.get('error','') if isinstance(verdict, dict) else verdict} | | | | | |")
        else:
            lines.append(f"| {m['name']} | {mode} | {r + 1} | {ans} | {verdict} | {e['finish']} | {e['elapsed']}s | "
                         f"{e['tokens'].get('reasoning')} | ${e['cost']} | {e['provider']} |")
    total_cost = sum((e["cost"] or 0) for _, _, _, e, _, _ in rows if e)
    lines += ["", f"**合计花费: ${round(total_cost, 4)}**  ·  共 {len(rows)} 次调用"]
    summary = "\n".join(lines) + "\n"
    with open(os.path.join(outdir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summary)
    print("\n" + summary)
    print(f"完成。明细见 {outdir}")


if __name__ == "__main__":
    main()
