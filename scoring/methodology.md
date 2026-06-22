# 大模型跑分 · 方法论 + 工具

一套"测试内容与脚本解耦"的小工具，用来拿同一道题问一圈模型、控变量、看结果。Collatz-16 是第一个用例，以后换题只加一个文件。

## 为什么用 API，不用网页

网页/App 对话框测不干净，至少这些你控不了：是否默认开 thinking、推理预算多大、有没有鼓励"详细分析"的隐藏系统提示、是否自动调工具/搜索、温度采样、同题多次是否走缓存或路由到不同版本。
API（这里走 OpenRouter，一个 key 通各家）能统一 prompt / 温度 / max_tokens，并用 `reasoning` 参数显式控制推理开关——这才谈得上"对照实验"。

## 工具结构（解耦）

```
IDIOT/
  harness/
    run.py                单轮跑分器：读 models + 一个 test，调 API，存结果
    run_convo.py          多轮自适应跑法（内置 API 裁判，给《礼物》这类多轮题用）
    convo.py              多轮底层助手（手动逐轮）
    models.json           待测模型名单 [{name, slug}, ...]
  tests/<id>/test.json    一道单轮题（题面/系统提示/标准答案/默认模式）
  tests/<id>/protocol.json 一道多轮题（台词/阶梯/诊断）
  results/<id>/...        输出（summary.md + 明细 + _raw.jsonl）
  openrouter.txt          API key（脚本自动读，已 .gitignore）
```

换新题 = 往 `tests/` 丢个 json；换/加模型 = 改 `models.json`。脚本不动。

### tests/<id>/test.json 字段

| 字段 | 说明 |
|---|---|
| `id` | 与文件名一致 |
| `system_prompt` | 系统提示，可空 |
| `user_prompt` | 题面（`\n` 换行） |
| `expected` | 标准答案（判分用，字符串） |
| `wrong_answers_seen` | 已知错答列表，判分时优先标红 |
| `reasoning_modes` | 默认跑哪些模式，如 `["off","on"]`，可被 `--modes` 覆盖 |
| `temperature` | `null` = 不传（用各家默认，避免推理模型拒绝非 1 温度） |
| `max_tokens` | 给够，推理模型会吃很多；不够会被截断（finish=length） |

## 怎么跑

```bash
# Windows 上用 py，并开 UTF-8（否则中文/特殊字符会崩）
set PYTHONUTF8=1            # 或 PowerShell: $env:PYTHONUTF8=1
py -X utf8 run.py --test collatz-16 --modes off,on --reps 8 --workers 8
```

常用参数：`--test`（必填，题 id）、`--models`（默认 models.json）、`--modes`（覆盖题里的）、`--reps`（每格重复几次）、`--workers`（并发）、`--timeout`（秒，推理模型设大点）。

输出看 `results/<id>/run-<时间戳>/summary.md`：`--reps>1` 时顶部有"稳定性表"（每个 模型×模式 的答案分布 + 命中率），下面是逐次明细；每次调用另存一个 `.md`（含回答正文 + 折叠的思维链）。原始响应在 `_raw.jsonl`。

## 关键旋钮：推理控制

OpenRouter 统一用 `reasoning` 参数：
- `mode=off` → `reasoning:{enabled:false}` 尝试关掉推理
- `mode=on` → `reasoning:{enabled:true}` 开
- `mode=default` → 不传该参数，用各家默认

脚本对所有模型统一抓 `message.content` + `message.reasoning` 两个字段——**DeepSeek 那种把思维链放单独字段的，被 OpenRouter 归一化进 `message.reasoning`，所以不用特殊处理**。`usage.completion_tokens_details.reasoning_tokens` 是判断"它到底有没有真思考"的关键指标。
（若某模型不支持 `reasoning` 参数返 400，脚本会自动去掉该参数重试一次。）

## 踩过的坑（方法论教训）

1. **单次采样会骗人。** 同一格 N=1 可能抽到离群值（GPT-5.5 关推理我们见过一次 920，重复 8 次其实 8/8）。**要给模型定性，必须 `--reps` 多跑看分布**，别拿一次结果下结论。
2. **"嘴上禁思考" ≠ "API 关推理"，是两个不同的干预。** prompt 里写"凭直觉别深想"，模型可能照样偷偷推理；`reasoning:{enabled:false}` 才是真把通道关死。两者效果差很多，别混为一谈（这正是 Collatz-16 里 codex 之谜的关键）。要测"被告知用直觉"就写进 prompt，要测"无思考能力"就用参数。
3. **部分 provider 无视 `enabled:false`。** Gemini、MiniMax、某些 pro 模型关不掉推理，reasoning_tokens 仍 >0。看结果时先核对 token，别把"没关成功"的当"关了"。
4. **判分器只是粗筛，必须看原文。** `grade()` 只看回答结尾 400 字里有没有标准答案/已知错答；模型不给干净数字时会抓个邻近数字充数。最终结论要打开 `.md` 逐个核。
5. **"推理到死" / 截断。** 有的模型（混元 hy3、MiMo Pro）会一直推理到撞 `max_tokens`（finish=length）都不给答案；有的（某 provider 上的 DeepSeek Flash）在正文里狂列枚举、自相矛盾、被截断。这些是真实的失败模式，summary 里会体现为 DNF/无答案。
6. **provider 路由会变。** 同一 slug，OpenRouter 可能路由到不同上游（Azure/OpenAI/Novita/SiliconFlow…），速度、价格、甚至行为都可能不同。summary 里记了 `provider`，异常时先看是不是换了家。
7. **温度默认不传。** 很多推理模型只接受 temperature=1，强行设 0 会报错；所以默认 `temperature:null`（不传）。要控温在题里显式设。

## 成本

Collatz-16 全程（19 模型广撒网 + GPT 深挖 96 次 + 零碎重试/预热）总共约 **$4.4**。单次：非推理调用 ~$0.01、轻推理 ~$0.02–0.06、重推理/pro 可飙到 $0.2–0.5。跑前心里有数，pro 系列别开大 reps。

## 复用：加一道新题

1. 写 `tests/<新id>/test.json`（题面 + 标准答案 + 已知错答）。
2. 需要的话调 `models.json`。
3. `py -X utf8 run.py --test <新id> --reps N`。
4. 看 `results/<新id>/.../summary.md`。

下一个项目（礼物 / 小说赏析）就可以用同一套：把"赏析题"写成一个 test，模型名单复用，区别只在那种主观题没有唯一 `expected`，判分要靠人读——但收集、控变量、存档这套流程照搬。
