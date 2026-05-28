#!/usr/bin/env python3
"""多轮对话助手：把一次对话的历史持久化到磁盘，每次调用发一条消息、返回模型回复。

设计意图：让 subagent 逐轮驱动多轮实验——subagent 负责"判断到没到位/要不要升级/打分"，
本脚本只管两件机械事：调 OpenRouter、维护对话历史。台词用 --turn 从协议里逐字取，
subagent 改不了措辞，保证所有模型台词一致。

用法：
  py convo.py --convo <对话id> --model <slug> --protocol gift --turn R0 [--provider P] [--reasoning default|off|on]
  py convo.py --convo <对话id> --model <slug> --message "自由文本"        # 不走协议时
首次对该 convo 发言、且协议里有 story_file 时，会自动把小说全文作为第一条消息的前缀。
历史与元信息存到 results/<protocol>/_convos/<convo>.json。
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def load_key():
    if os.environ.get("OPENROUTER_API_KEY"):
        return os.environ["OPENROUTER_API_KEY"].strip()
    for p in (os.path.join(HERE, os.pardir, "openrouter.txt"), os.path.join(HERE, "openrouter.txt")):
        if os.path.exists(p):
            return open(p, encoding="utf-8").read().strip()
    sys.exit("找不到 API key（OPENROUTER_API_KEY 或 ../openrouter.txt）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--convo", required=True, help="对话 id（同 id 续上下文，新 id 开新对话）")
    ap.add_argument("--model", required=True)
    ap.add_argument("--protocol", default=None, help="protocols/<x>.json，用于 --turn 取台词和 story")
    ap.add_argument("--turn", default=None, help="协议里 turns 的 key，如 R0/R2/D1")
    ap.add_argument("--message", default=None, help="自由文本（不走协议时用）")
    ap.add_argument("--provider", default=None, help="锁定上游，如 Google/OpenAI")
    ap.add_argument("--reasoning", default="default", choices=["default", "off", "on"])
    ap.add_argument("--max_tokens", type=int, default=20000)
    ap.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args()
    key = load_key()

    proto = None
    proto_dir = None
    if args.protocol:
        proto_dir = os.path.join(HERE, os.pardir, "tests", args.protocol)
        with open(os.path.join(proto_dir, "protocol.json"), encoding="utf-8") as f:
            proto = json.load(f)

    # 取本轮要发的文本
    if args.turn:
        if not proto:
            sys.exit("--turn 需要配 --protocol")
        text = proto["turns"][args.turn]
    elif args.message is not None:
        text = args.message
    else:
        sys.exit("需要 --turn 或 --message")

    pid = args.protocol or "adhoc"
    convo_dir = os.path.join(HERE, os.pardir, "results", pid, "_convos")
    os.makedirs(convo_dir, exist_ok=True)
    path = os.path.join(convo_dir, args.convo + ".json")

    if os.path.exists(path):
        state = json.load(open(path, encoding="utf-8"))
        msgs = state["messages"]
    else:
        msgs = []
        sysp = (proto or {}).get("system") or ""
        if sysp:
            msgs.append({"role": "system", "content": sysp})
        state = {"convo": args.convo, "model": args.model, "messages": msgs, "meta": []}

    # 首条 user 消息 + 协议里有 story → 前置全文
    first_user = not any(m["role"] == "user" for m in msgs)
    user_content = text
    if first_user and proto and proto.get("story_file"):
        story_path = os.path.join(proto_dir, proto["story_file"])
        story = open(story_path, encoding="utf-8").read()
        user_content = story + "\n\n---\n\n" + text
    msgs.append({"role": "user", "content": user_content})

    payload = {"model": args.model, "messages": msgs, "max_tokens": args.max_tokens}
    if args.reasoning == "off":
        payload["reasoning"] = {"enabled": False}
    elif args.reasoning == "on":
        payload["reasoning"] = {"enabled": True}
    if args.provider:
        payload["provider"] = {"order": [args.provider], "allow_fallbacks": False}

    def post(body):
        req = urllib.request.Request(
            API_URL, data=json.dumps(body).encode(), method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=args.timeout) as r:
            return json.loads(r.read().decode())

    t0 = time.time()
    try:
        data = post(payload)
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "ignore")
        if e.code == 400 and "reasoning" in payload and "reasoning" in err.lower():
            payload.pop("reasoning", None)
            try:
                data = post(payload)
            except Exception as e2:
                print(f"[ERROR] HTTP {e.code} 去掉 reasoning 重试仍失败: {e2}\n{err[:300]}"); sys.exit(1)
        else:
            print(f"[ERROR] HTTP {e.code}: {err[:400]}"); sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}"); sys.exit(1)

    ch = (data.get("choices") or [{}])[0]
    m = ch.get("message", {}) or {}
    content = m.get("content") or ""
    u = data.get("usage") or {}
    rtok = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
    msgs.append({"role": "assistant", "content": content})
    state["meta"].append({"turn": args.turn or "(free)", "finish": ch.get("finish_reason"),
                          "reasoning_tokens": rtok, "cost": u.get("cost"),
                          "provider": data.get("provider"), "elapsed": round(time.time() - t0, 1)})
    json.dump(state, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    n = sum(1 for x in msgs if x["role"] == "assistant")
    print(f"=== [{args.turn or 'msg'}] 模型回复 (第 {n} 轮) ===")
    print(content if content else "[空回复]")
    print(f"\n--- meta: finish={ch.get('finish_reason')} reasoning_tokens={rtok} "
          f"cost=${u.get('cost')} provider={data.get('provider')} elapsed={round(time.time() - t0, 1)}s ---")


if __name__ == "__main__":
    main()
