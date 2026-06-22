# OpenRouter API 使用指南（给 agent 用）

> 一份自包含的上手文档。看完你就能调任意大模型、控推理、跑多轮对话、读懂返回。**所有结论都已在本项目实测过。** 配套工具见同目录 `run.py` 与 `../scoring/methodology.md`。

## 0. 一句话

OpenRouter 用**一个 key 通各家模型**，接口是 OpenAI-compatible 的 `POST /chat/completions`。换模型只换 `model` 字段（slug 形如 `openai/gpt-5.5`、`anthropic/claude-opus-4.7`）。

## 1. 鉴权与 Key

- Key 放在项目根的 `openrouter.txt`（脚本按 `OPENROUTER_API_KEY` 环境变量 → `../openrouter.txt` → `./openrouter.txt` 顺序找）。
- 请求头：`Authorization: Bearer <key>`。**别把 key 打印到日志或提交到 git。**

## 2. 最小请求

curl：
```bash
KEY=$(tr -d '\r\n' < openrouter.txt)
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-5.5","messages":[{"role":"user","content":"你好"}],"max_tokens":2000}'
```

Python（标准库 urllib，无需 pip）：
```python
import json, urllib.request
def chat(key, model, messages, **opts):
    body = {"model": model, "messages": messages, **opts}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())
```

## 3. 请求体字段

| 字段 | 说明 |
|---|---|
| `model` | 模型 slug（见 §8 取列表） |
| `messages` | `[{role, content}]`，role ∈ `system`/`user`/`assistant` |
| `max_tokens` | 给够；**推理模型很吃 token，不够会被截断**（见 §6） |
| `temperature` | **很多推理模型只接受 1，强行设 0 会报错**。不确定就不传，用各家默认 |
| `reasoning` | 推理控制，见 §4 |
| `provider` | 锁定上游，见 §7 |

## 4. 推理控制（核心）

`reasoning` 对象统一各家的"思考开关"：
```jsonc
"reasoning": {"enabled": false}      // 关推理（尝试）
"reasoning": {"enabled": true}       // 开
"reasoning": {"effort": "low"|"medium"|"high"}  // 控强度（部分模型）
"reasoning": {"max_tokens": 2000}    // 控思考预算（部分模型）
"reasoning": {"exclude": true}       // 仍思考但不在返回里给出思维链
```
不传该字段 = 用模型默认。

**两个坑必须知道：**
- **部分 provider 无视 `enabled:false`**（Gemini、MiniMax、某些 pro 模型照样思考）。判断它到底有没有思考，**看返回的 `usage…reasoning_tokens`，别信你传了什么**。
- 少数模型不支持 `reasoning` 参数，会返 400。稳妥做法：报 400 且错误信息含 "reasoning" 时，去掉该参数重试一次。

## 5. 多轮对话

无状态——**每轮把完整历史重发**。把模型上一轮的回复作为 `assistant` 追加，再加新的 `user`：
```python
msgs = [{"role":"user","content":"读这篇小说……"}]
r1 = chat(key, model, msgs)
a1 = r1["choices"][0]["message"]["content"]
msgs += [{"role":"assistant","content":a1},
         {"role":"user","content":"再想想，没那么简单？"}]
r2 = chat(key, model, msgs)
```
注意：上下文逐轮变长（长文每轮重发会涨 token、涨钱）。`reasoning` 字段**不要**回填进 `assistant` 历史，只回填 `content`。

## 6. 响应结构

```jsonc
{
  "provider": "OpenAI",                    // 实际服务的上游
  "choices": [{
    "finish_reason": "stop",               // "length"=被 max_tokens 截断（危险信号）
    "message": {
      "content": "最终回答",
      "reasoning": "思维链（若有）",         // 统一字段，见下
      "reasoning_details": [...]
    }
  }],
  "usage": {
    "prompt_tokens": 227, "completion_tokens": 353,
    "cost": 0.0117,                         // 美元，直接可用
    "completion_tokens_details": {"reasoning_tokens": 0}  // 真正花了多少思考 token
  }
}
```
取值：`content = choices[0].message.content`，`reasoning = choices[0].message.reasoning`。

- **DeepSeek 归一化**：DeepSeek 原生把思维链放单独字段（`reasoning_content`），走 OpenRouter 后被归一化进 `message.reasoning`，**所以对所有模型统一抓 `content`+`reasoning` 即可，无需特判**。
- **`reasoning_tokens` 是金标准**：判断模型"到底有没有真思考"，看这个数，不看你传的开关。
- **`finish_reason=="length"` + `content` 空**：模型"推理到死"，撞 max_tokens 还没给答案（混元 hy3、MiMo 出现过）。调大 `max_tokens` 重试或记为 DNF。

## 7. 锁定 provider（可复现性）

同一 slug，OpenRouter 可能路由到不同上游（Azure / OpenAI / Novita / SiliconFlow…），**速度、价格、甚至行为都可能不同**（实测同一模型不同上游答案不一样）。要复现就锁定：
```jsonc
"provider": {"order": ["OpenAI"], "allow_fallbacks": false}
```
（已实测：`order:["Alibaba"], allow_fallbacks:false` → 返回 provider 确为 Alibaba。）做对照实验时建议锁定，避免上游漂移混进结果。

## 8. 取模型列表

公开、免鉴权：
```bash
curl -s https://openrouter.ai/api/v1/models -o models.json
```
每条含 `id`(slug)、`name`、`supported_parameters`（看是否支持 `reasoning` 等）、定价、context 长度。用 `supported_parameters` 里有没有 `reasoning` 来预判能不能控推理。

## 9. 并发、超时、稳定性

- 并发：线程池 6–8 个 worker 一般没问题，再高可能被限流。
- 超时：推理模型可能跑 100–200 秒，`timeout` 设 300。
- 偶发 `IncompleteRead` / JSON 解析失败（流被截断），重试一次通常就好。

## 10. 成本量级（心里有数）

非推理调用 ~$0.01；轻推理 ~$0.02–0.06；重推理 / pro 系列单次可达 $0.2–0.5。本项目 Collatz 全程约 $4.4。**pro 系列别开大 reps；多轮 + 长文每轮重发会显著推高成本。**

## 11. Windows 注意

- 用 `py -X utf8`，并设 `PYTHONUTF8=1`（PowerShell：`$env:PYTHONUTF8=1`）；否则中文/特殊字符在打印或写文件时会崩。
- 别用 `python3`（可能是 Microsoft Store 的 stub，会挂）。
- 读 key 时去掉行尾 `\r\n`（Windows 换行）。
